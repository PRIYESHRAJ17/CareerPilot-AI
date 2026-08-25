from typing import List

from backend.connectors.adzuna import AdzunaConnector
from backend.connectors.jooble import JoobleConnector

from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.schemas.requirements import (
    JobRequirements,
)

from backend.services.deduplication import (
    JobDeduplicator,
)

from backend.services.final_matcher import (
    FinalMatchEngine,
)

from backend.services.job_aggregator import (
    JobAggregator,
)

from backend.services.job_filter import (
    JobFilter,
)

from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)

from backend.api.models import (
    JobResult,
)


class CareerSearchService:
    """
    Orchestrates the Week-2 CareerPilot search pipeline.
    """

    def __init__(self) -> None:
        self.aggregator = JobAggregator(
            sources=[
                AdzunaConnector(country="in"),
                JoobleConnector(),
            ]
        )

        self.deduplicator = JobDeduplicator()
        self.filter = JobFilter()
        self.requirements_extractor = (
            JobRequirementsExtractor()
        )
        self.match_engine = FinalMatchEngine()

    def search(
        self,
        candidate: CandidateProfile,
        query: str,
        location: str | None = None,
    ) -> List[JobResult]:

        raw_jobs = self.aggregator.search(
            query=query,
            location=location,
            limit_per_source=10,
        )

        canonical_jobs = (
            self.deduplicator.deduplicate(
                raw_jobs
            )
        )

        filtered_jobs = self.filter.filter(
            canonical_jobs,
            candidate,
        )

        results: List[JobResult] = []

        for job in filtered_jobs:

            requirements = (
                self.requirements_extractor.extract(
                    job
                )
            )

            match = self.match_engine.evaluate(
                candidate=candidate,
                job=job,
                requirements=requirements,
            )

            results.append(
                JobResult(
                    source=job.source,
                    source_job_id=job.source_job_id,
                    company=job.company,
                    title=job.title,
                    location=job.location,
                    remote=job.remote,
                    employment_type=job.employment_type,
                    match_score=match.final_score,
                    decision=match.decision,
                    confidence=match.confidence,
                    strengths=match.strengths,
                    skill_gaps=match.skill_gaps,
                    apply_url=job.apply_url,
                )
            )

        results.sort(
            key=lambda result: (
                result.match_score or 0
            ),
            reverse=True,
        )

        return results