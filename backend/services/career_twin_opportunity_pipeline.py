from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements
from backend.services.career_twin import (
    get_or_create,
)
from backend.services.career_twin_job_intelligence import (
    CareerTwinJobIntelligence,
)
from backend.services.career_twin_matcher import (
    CareerTwinMatcher,
)
from backend.services.final_matcher import (
    FinalMatch,
)


class CareerTwinOpportunityPipeline:
    """
    Production bridge between the persistent Career Twin and the
    existing opportunity-matching pipeline.

    Responsibilities:

        Job + Requirements
                ↓
        Career Twin intelligence
                ↓
        Existing FinalMatch
                ↓
        Career Twin personalization
                ↓
        Unified opportunity intelligence

    The service is deliberately isolated from discovery. It cannot
    alter provider behavior, pagination, filtering, or deduplication.
    """

    def __init__(self) -> None:
        self.job_intelligence = (
            CareerTwinJobIntelligence()
        )
        self.matcher = CareerTwinMatcher()

    def enrich(
        self,
        candidate: CandidateProfile,
        job: Job,
        requirements: JobRequirements,
        base_match: FinalMatch,
    ) -> Dict[str, Any]:
        """
        Enrich one opportunity using the persistent Career Twin.
        """

        candidate_id = str(
            getattr(
                candidate,
                "candidate_id",
                "",
            )
            or "agentic-user"
        )

        career_twin = get_or_create(
            candidate_id
        )

        career_twin_analysis = (
            self.job_intelligence.analyze(
                job=job,
                career_twin=career_twin,
                requirements=requirements,
            )
        )

        personalized = (
            self.matcher.personalize(
                base_match=base_match,
                career_twin_analysis=(
                    career_twin_analysis
                ),
            )
        )

        return {
            "career_twin_analysis": (
                career_twin_analysis
            ),

            "personalized_match": (
                self._serialize(
                    personalized
                )
            ),

            "career_twin_id": candidate_id,

            "career_twin_version": (
                self._get_version(
                    career_twin
                )
            ),
        }

    @staticmethod
    def _get_version(
        career_twin: Any,
    ) -> Optional[int]:

        if career_twin is None:
            return None

        if isinstance(
            career_twin,
            dict,
        ):
            value = career_twin.get(
                "version"
            )
        else:
            value = getattr(
                career_twin,
                "version",
                None,
            )

        try:
            return (
                int(value)
                if value is not None
                else None
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _serialize(
        value: Any,
    ) -> Any:

        if value is None:
            return None

        if hasattr(
            value,
            "model_dump",
        ):
            return value.model_dump(
                mode="json"
            )

        if is_dataclass(value):
            return asdict(value)

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): (
                    CareerTwinOpportunityPipeline
                    ._serialize(item)
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                CareerTwinOpportunityPipeline._serialize(
                    item
                )
                for item in value
            ]

        return value