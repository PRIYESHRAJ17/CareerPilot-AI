from typing import List

from backend.api.models import (
    JobResult,
    MatchBreakdown,
    SalarySummary,
    SourceRecord,
    SourceSummary,
)

from backend.connectors.adzuna import AdzunaConnector
from backend.connectors.jooble import JoobleConnector

from backend.schemas.candidate import CandidateProfile

from backend.services.deduplication import JobDeduplicator
from backend.services.final_matcher import FinalMatchEngine
from backend.services.job_aggregator import JobAggregator
from backend.services.job_filter import JobFilter
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)
from backend.services.salary_intelligence import (
    SalaryIntelligence,
)


class CareerSearchService:
    """
    Complete CareerPilot opportunity pipeline.

    Discovery
        ↓
    Deduplication
        ↓
    Salary intelligence
        ↓
    Hard filtering
        ↓
    Requirements extraction
        ↓
    Hybrid matching
        ↓
    Source-aware API response
        ↓
    Ranking
    """

    def __init__(self) -> None:
        self.aggregator = JobAggregator(
            sources=[
                AdzunaConnector(country="in"),
                JoobleConnector(),
            ]
        )

        self.deduplicator = JobDeduplicator()
        self.salary_intelligence = SalaryIntelligence()
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

        # --------------------------------------------------
        # 1. Broad discovery
        # --------------------------------------------------

        raw_jobs = self.aggregator.search(
            query=query,
            location=location,
            limit_per_source=30,
        )

        # --------------------------------------------------
        # 2. Canonical opportunities
        # --------------------------------------------------

        canonical_jobs = (
            self.deduplicator.deduplicate(
                raw_jobs
            )
        )

        # --------------------------------------------------
        # 3. Salary intelligence
        # --------------------------------------------------

        enriched_jobs = [
            self.salary_intelligence.enrich(job)
            for job in canonical_jobs
        ]

        # --------------------------------------------------
        # 4. Hard filtering
        # --------------------------------------------------

        filtered_jobs = self.filter.filter(
            enriched_jobs,
            candidate,
        )

        results: List[JobResult] = []

        # --------------------------------------------------
        # 5. Matching + response construction
        # --------------------------------------------------

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

            # ----------------------------------------------
            # Sources
            # ----------------------------------------------

            sources = (
                job.sources
                if job.sources
                else [job.source]
            )

            source_count = (
                job.source_count
                if job.sources
                else 1
            )

            source_records: List[
                SourceRecord
            ] = []

            for raw_record in (
                job.source_records
                or []
            ):
                source_records.append(
                    SourceRecord(
                        source=str(
                            raw_record.get(
                                "source",
                                "",
                            )
                        ),

                        source_job_id=str(
                            raw_record.get(
                                "source_job_id",
                                "",
                            )
                        ),

                        company=str(
                            raw_record.get(
                                "company",
                                job.company,
                            )
                        ),

                        title=str(
                            raw_record.get(
                                "title",
                                job.title,
                            )
                        ),

                        location=list(
                            raw_record.get(
                                "location",
                                job.location,
                            )
                            or []
                        ),

                        remote=bool(
                            raw_record.get(
                                "remote",
                                False,
                            )
                        ),

                        employment_type=(
                            raw_record.get(
                                "employment_type"
                            )
                        ),

                        apply_url=str(
                            raw_record.get(
                                "apply_url",
                                "",
                            )
                        ),

                        source_url=str(
                            raw_record.get(
                                "source_url",
                                "",
                            )
                        ),

                        salary_min_lpa=(
                            raw_record.get(
                                "salary_min_lpa"
                            )
                        ),

                        salary_max_lpa=(
                            raw_record.get(
                                "salary_max_lpa"
                            )
                        ),

                        salary_currency=str(
                            raw_record.get(
                                "salary_currency",
                                "INR",
                            )
                        ),

                        salary_status=str(
                            raw_record.get(
                                "salary_status",
                                "UNDISCLOSED",
                            )
                        ),

                        salary_confidence=float(
                            raw_record.get(
                                "salary_confidence",
                                0.0,
                            )
                            or 0.0
                        ),

                        salary_evidence=(
                            raw_record.get(
                                "salary_evidence"
                            )
                        ),

                        posted_at=(
                            raw_record.get(
                                "posted_at"
                            )
                        ),
                    )
                )

            # ----------------------------------------------
            # Fallback source record
            # ----------------------------------------------

            if not source_records:
                source_records.append(
                    SourceRecord(
                        source=job.source,
                        source_job_id=(
                            job.source_job_id
                        ),
                        company=job.company,
                        title=job.title,
                        location=job.location,
                        remote=job.remote,
                        employment_type=(
                            job.employment_type
                        ),
                        apply_url=(
                            job.apply_url
                        ),
                        source_url=(
                            job.source_url
                        ),
                        salary_min_lpa=(
                            job.salary.min_lpa
                        ),
                        salary_max_lpa=(
                            job.salary.max_lpa
                        ),
                        salary_currency=(
                            job.salary.currency
                        ),
                        salary_status=str(
                            job.metadata.get(
                                "salary_status",
                                "UNDISCLOSED",
                            )
                        ),
                        salary_confidence=float(
                            job.metadata.get(
                                "salary_confidence",
                                0.0,
                            )
                            or 0.0
                        ),
                        salary_evidence=(
                            job.metadata.get(
                                "salary_evidence"
                            )
                        ),
                        posted_at=(
                            job.posted_at
                        ),
                    )
                )

            # ----------------------------------------------
            # Salary
            # ----------------------------------------------

            salary_min = job.salary.min_lpa
            salary_max = job.salary.max_lpa

            salary_disclosed = (
                salary_min is not None
                or salary_max is not None
            )

            salary_confidence = float(
                job.metadata.get(
                    "salary_confidence",
                    0.0,
                )
                or 0.0
            )

            salary_evidence = (
                job.metadata.get(
                    "salary_evidence"
                )
            )

            candidate_minimum = (
                candidate
                .career_goal
                .minimum_salary_lpa
            )

            if not salary_disclosed:
                salary_status = "UNDISCLOSED"

            elif candidate_minimum is None:
                salary_status = "MEETS_TARGET"

            elif (
                salary_min is not None
                and salary_min >= candidate_minimum
            ):
                salary_status = "MEETS_TARGET"

            elif (
                salary_min is None
                and salary_max is not None
                and salary_max >= candidate_minimum
            ):
                salary_status = "MEETS_TARGET"

            else:
                salary_status = "BELOW_TARGET"

            # ----------------------------------------------
            # Match breakdown
            # ----------------------------------------------

            match_breakdown = MatchBreakdown(
                overall_score=(
                    match.final_score
                ),

                role_fit=match.role_fit,
                skill_fit=match.skill_fit,
                experience_fit=(
                    match.experience_fit
                ),
                location_fit=(
                    match.location_fit
                ),
                salary_fit=match.salary_fit,
                career_goal_fit=(
                    match.career_goal_fit
                ),

                semantic_score=(
                    match.semantic_score
                ),

                deterministic_score=(
                    match.deterministic_score
                ),
            )

            # ----------------------------------------------
            # Result
            # ----------------------------------------------

            results.append(
                JobResult(
                    source=job.source,

                    source_job_id=(
                        job.source_job_id
                    ),

                    sources=sources,

                    source_count=source_count,

                    source_records=(
                        source_records
                    ),

                    company=job.company,

                    title=job.title,

                    location=job.location,

                    remote=job.remote,

                    employment_type=(
                        job.employment_type
                    ),

                    match_score=(
                        match.final_score
                    ),

                    decision=match.decision,

                    confidence=(
                        match.confidence
                    ),

                    strengths=(
                        match.strengths
                    ),

                    skill_gaps=(
                        match.skill_gaps
                    ),

                    matched_skills=(
                        match.matched_skills
                    ),

                    explanation=(
                        match.explanation
                    ),

                    match_breakdown=(
                        match_breakdown
                    ),

                    salary_min_lpa=(
                        salary_min
                    ),

                    salary_max_lpa=(
                        salary_max
                    ),

                    salary_disclosed=(
                        salary_disclosed
                    ),

                    salary_status=(
                        salary_status
                    ),

                    salary_confidence=(
                        salary_confidence
                    ),

                    salary_evidence=(
                        salary_evidence
                    ),

                    apply_url=(
                        job.apply_url
                    ),
                )
            )

        # --------------------------------------------------
        # 6. Ranking
        # --------------------------------------------------

        results.sort(
            key=lambda result: (
                result.match_score
                if result.match_score is not None
                else 0
            ),
            reverse=True,
        )

        return results

    def build_salary_summary(
        self,
        results: List[JobResult],
        minimum_salary_lpa: float | None,
    ) -> SalarySummary:

        salary_verified = sum(
            1
            for result in results
            if (
                result.salary_status
                == "MEETS_TARGET"
                and result.salary_disclosed
            )
        )

        salary_undisclosed = sum(
            1
            for result in results
            if result.salary_status
            == "UNDISCLOSED"
        )

        return SalarySummary(
            minimum_salary_lpa=(
                minimum_salary_lpa
            ),
            opportunities_found=len(
                results
            ),
            salary_verified=(
                salary_verified
            ),
            salary_undisclosed=(
                salary_undisclosed
            ),
        )

    def build_source_summary(
        self,
        results: List[JobResult],
    ) -> SourceSummary:

        configured_sources = [
            source.name
            for source in self.aggregator.sources
        ]

        contributing_sources = set()

        for result in results:
            contributing_sources.update(
                result.sources
                if result.sources
                else [result.source]
            )

        return SourceSummary(
            connected=len(
                configured_sources
            ),
            contributing=len(
                contributing_sources
            ),
            sources=configured_sources,
        )