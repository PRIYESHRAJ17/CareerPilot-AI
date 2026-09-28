from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Set

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.services.career_twin import (
    get_or_create,
    update_from_candidate,
)
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)


class CareerTwinMarketIntelligence:
    """
    Converts a live opportunity pool into persistent Career Twin
    intelligence.

    Flow:

        Live jobs
            ↓
        Requirement extraction
            ↓
        Market demand aggregation
            ↓
        Candidate-vs-market gap analysis
            ↓
        Priority skill gaps
            ↓
        Career actions
            ↓
        Persistent Career Twin update
    """

    def __init__(
        self,
        requirements_extractor: Optional[
            JobRequirementsExtractor
        ] = None,
    ) -> None:
        self.requirements_extractor = (
            requirements_extractor
            or JobRequirementsExtractor()
        )

    # ============================================================
    # PUBLIC ANALYSIS
    # ============================================================

    def analyze(
        self,
        candidate: CandidateProfile,
        jobs: Iterable[Job],
        career_twin: Any = None,
    ) -> Dict[str, Any]:
        jobs = list(jobs)

        twin = self._to_dict(
            career_twin
        )

        candidate_skills = self._skill_set(
            candidate.skills,
            candidate.technical_skills,
            twin.get("current_skills"),
            twin.get("skills"),
            twin.get("technical_skills"),
            twin.get("strengths"),
            (twin.get("derived") or {}).get(
                "strengths"
            ),
        )

        target_roles = self._string_list(
            candidate.career_goal.target_roles,
            twin.get("target_roles"),
            twin.get("career_goals"),
            (twin.get("derived") or {}).get(
                "career_directions"
            ),
        )

        technology_counts: Counter[str] = Counter()
        required_counts: Counter[str] = Counter()
        preferred_counts: Counter[str] = Counter()
        role_counts: Counter[str] = Counter()
        domain_counts: Counter[str] = Counter()

        analyzed_jobs = 0

        for job in jobs:
            requirements = (
                self.requirements_extractor.extract(
                    job
                )
            )

            analyzed_jobs += 1

            for skill in requirements.technologies:
                normalized = self._normalize(
                    skill
                )
                if normalized:
                    technology_counts[
                        normalized
                    ] += 1

            for skill in requirements.required_skills:
                normalized = self._normalize(
                    skill
                )
                if normalized:
                    required_counts[
                        normalized
                    ] += 1

            for skill in requirements.preferred_skills:
                normalized = self._normalize(
                    skill
                )
                if normalized:
                    preferred_counts[
                        normalized
                    ] += 1

            role = self._normalize(
                self._infer_role(job)
            )

            if role:
                role_counts[role] += 1

            if requirements.domain:
                domain = self._normalize(
                    requirements.domain
                )

                if domain:
                    domain_counts[
                        domain
                    ] += 1

        # --------------------------------------------------------
        # Market gap calculation
        # --------------------------------------------------------

        market_skills = set(
            technology_counts
        )

        missing_market_skills = (
            market_skills
            - candidate_skills
        )

        prioritized_gaps = []

        for skill in missing_market_skills:
            required_frequency = (
                required_counts.get(
                    skill,
                    0,
                )
            )

            preferred_frequency = (
                preferred_counts.get(
                    skill,
                    0,
                )
            )

            total_frequency = (
                technology_counts.get(
                    skill,
                    0,
                )
            )

            if required_frequency > 0:
                priority = "HIGH"
            elif total_frequency >= 5:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            prioritized_gaps.append(
                {
                    "skill": skill,
                    "priority": priority,
                    "market_frequency": (
                        total_frequency
                    ),
                    "required_frequency": (
                        required_frequency
                    ),
                    "preferred_frequency": (
                        preferred_frequency
                    ),
                    "market_coverage": round(
                        (
                            total_frequency
                            / analyzed_jobs
                            * 100
                        )
                        if analyzed_jobs
                        else 0.0,
                        2,
                    ),
                }
            )

        priority_order = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        prioritized_gaps.sort(
            key=lambda item: (
                priority_order.get(
                    item["priority"],
                    99,
                ),
                -item["required_frequency"],
                -item["market_frequency"],
                item["skill"],
            )
        )

        # --------------------------------------------------------
        # Career directions
        # --------------------------------------------------------

        market_roles = [
            {
                "role": role,
                "count": count,
            }
            for role, count
            in role_counts.most_common(15)
        ]

        # --------------------------------------------------------
        # Recommendations
        # --------------------------------------------------------

        recommendations = (
            self._build_recommendations(
                prioritized_gaps,
                target_roles,
            )
        )

        market_summary = (
            self._build_market_summary(
                analyzed_jobs=analyzed_jobs,
                technology_counts=(
                    technology_counts
                ),
                required_counts=(
                    required_counts
                ),
                market_roles=market_roles,
                target_roles=target_roles,
            )
        )

        return {
            "jobs_analyzed": analyzed_jobs,

            "market_summary": (
                market_summary
            ),

            "top_market_skills": (
                self._top_counter(
                    technology_counts
                )
            ),

            "top_required_skills": (
                self._top_counter(
                    required_counts
                )
            ),

            "top_preferred_skills": (
                self._top_counter(
                    preferred_counts
                )
            ),

            "market_roles": market_roles,

            "market_domains": {
                key: count
                for key, count
                in domain_counts.most_common(
                    15
                )
            },

            "candidate_skill_count": len(
                candidate_skills
            ),

            "market_skill_count": len(
                market_skills
            ),

            "market_skill_gaps": (
                prioritized_gaps[:20]
            ),

            "priority_skill_gaps": [
                item["skill"]
                for item
                in prioritized_gaps[:10]
            ],

            "recommendations": (
                recommendations
            ),

            "target_roles": (
                target_roles
            ),

            "evidence": {
                "source": (
                    "live_opportunity_pool"
                ),
                "jobs_analyzed": (
                    analyzed_jobs
                ),
                "requirement_extractor": (
                    "deterministic"
                ),
            },
        }

    # ============================================================
    # PERSISTENCE
    # ============================================================

    def sync_to_career_twin(
        self,
        candidate: CandidateProfile,
        candidate_intelligence: Optional[
            Dict[str, Any]
        ],
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Persist market-derived intelligence through the existing
        Career Twin update engine.
        """

        candidate_id = str(
            getattr(
                candidate,
                "candidate_id",
                "",
            )
            or "agentic-user"
        )

        existing_twin = get_or_create(
            candidate_id
        )

        base_intelligence = dict(
            candidate_intelligence
            or {}
        )

        base_intelligence[
            "market_intelligence"
        ] = analysis

        market_gap_items = (
            analysis.get(
                "market_skill_gaps",
                [],
            )
            or []
        )

        market_skill_gaps = [
            item.get("skill")
            for item
            in market_gap_items
            if (
                isinstance(
                    item,
                    dict,
                )
                and item.get("skill")
            )
        ]

        recommendations = list(
            analysis.get(
                "recommendations",
                [],
            )
            or []
        )

        try:
            updated_twin = (
                update_from_candidate(
                    candidate=candidate,
                    candidate_intelligence=(
                        base_intelligence
                    ),
                    skill_gaps=(
                        market_skill_gaps
                    ),
                    recommendations=(
                        recommendations
                    ),
                )
            )
        except Exception:
            # Preserve a useful result even if an older Career Twin
            # implementation does not accept one of the richer inputs.
            updated_twin = existing_twin

        return {
            "candidate_id": candidate_id,
            "career_twin": self._serialize(
                updated_twin
            ),
            "market_intelligence": analysis,
        }

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    @staticmethod
    def _build_recommendations(
        gaps: List[Dict[str, Any]],
        target_roles: List[str],
    ) -> List[Dict[str, Any]]:
        recommendations: List[
            Dict[str, Any]
        ] = []

        for index, gap in enumerate(
            gaps[:5],
            start=1,
        ):
            skill = str(
                gap["skill"]
            )

            priority = str(
                gap["priority"]
            )

            action = (
                f"Build practical evidence in {skill} "
                "through a focused project, production-style "
                "implementation, or targeted preparation."
            )

            if priority == "HIGH":
                reason = (
                    f"{skill} appears as a required skill in "
                    f"{gap['required_frequency']} observed "
                    "opportunities."
                )
            else:
                reason = (
                    f"{skill} appears across "
                    f"{gap['market_frequency']} observed "
                    "opportunities and represents a recurring "
                    "market requirement."
                )

            recommendations.append(
                {
                    "type": "market_skill_gap",
                    "priority": priority,
                    "rank": index,
                    "skill": skill,
                    "title": (
                        f"Develop market-relevant skill: "
                        f"{skill}"
                    ),
                    "action": action,
                    "reason": reason,
                    "target_roles": (
                        target_roles[:5]
                    ),
                    "evidence_source": (
                        "live_opportunity_pool"
                    ),
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "type": "market_scan",
                    "priority": "LOW",
                    "rank": 1,
                    "skill": None,
                    "title": (
                        "Continue monitoring the target market"
                    ),
                    "action": (
                        "Continue collecting live opportunities "
                        "and review recurring requirements as "
                        "the market changes."
                    ),
                    "reason": (
                        "The current opportunity pool did not "
                        "produce a strong missing-skill signal."
                    ),
                    "target_roles": (
                        target_roles[:5]
                    ),
                    "evidence_source": (
                        "live_opportunity_pool"
                    ),
                }
            )

        return recommendations

    # ============================================================
    # MARKET SUMMARY
    # ============================================================

    @staticmethod
    def _build_market_summary(
        analyzed_jobs: int,
        technology_counts: Counter[str],
        required_counts: Counter[str],
        market_roles: List[Dict[str, Any]],
        target_roles: List[str],
    ) -> Dict[str, Any]:

        role_alignment = 0.0

        if target_roles and market_roles:
            target_set = {
                role.casefold()
                for role in target_roles
            }

            matching_count = sum(
                item["count"]
                for item in market_roles
                if any(
                    target in item["role"]
                    or item["role"] in target
                    for target in target_set
                )
            )

            role_alignment = round(
                (
                    matching_count
                    / analyzed_jobs
                    * 100
                )
                if analyzed_jobs
                else 0.0,
                2,
            )

        return {
            "jobs_analyzed": (
                analyzed_jobs
            ),
            "unique_market_skills": len(
                technology_counts
            ),
            "unique_required_skills": len(
                required_counts
            ),
            "role_alignment_to_target": (
                role_alignment
            ),
            "market_depth": (
                "HIGH"
                if analyzed_jobs >= 200
                else (
                    "MEDIUM"
                    if analyzed_jobs >= 50
                    else "LOW"
                )
            ),
        }

    # ============================================================
    # HELPERS
    # ============================================================

    @classmethod
    def _skill_set(
        cls,
        *values: Any,
    ) -> Set[str]:
        output: Set[str] = set()

        for value in values:
            if value is None:
                continue

            if isinstance(
                value,
                str,
            ):
                normalized = cls._normalize(
                    value
                )

                if normalized:
                    output.add(
                        normalized
                    )

                continue

            if isinstance(
                value,
                dict,
            ):
                output.update(
                    cls._skill_set(
                        *value.values()
                    )
                )

                continue

            if isinstance(
                value,
                (list, tuple, set),
            ):
                for item in value:
                    normalized = cls._normalize(
                        item
                    )

                    if normalized:
                        output.add(
                            normalized
                        )

        return output

    @classmethod
    def _string_list(
        cls,
        *values: Any,
    ) -> List[str]:
        result: List[str] = []
        seen: Set[str] = set()

        for value in values:
            if value is None:
                continue

            if isinstance(
                value,
                str,
            ):
                items = [value]

            elif isinstance(
                value,
                (list, tuple, set),
            ):
                items = list(value)

            else:
                continue

            for item in items:
                normalized = cls._normalize(
                    item
                )

                if (
                    normalized
                    and normalized not in seen
                ):
                    seen.add(
                        normalized
                    )

                    result.append(
                        normalized
                    )

        return result

    @classmethod
    def _normalize(
        cls,
        value: Any,
    ) -> str:
        return " ".join(
            str(value or "")
            .casefold()
            .strip()
            .split()
        )

    @staticmethod
    def _infer_role(
        job: Job,
    ) -> str:
        title = str(
            job.title or ""
        ).strip()

        return title or "unknown"

    @staticmethod
    def _top_counter(
        counter: Counter[str],
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "value": value,
                "count": count,
            }
            for value, count
            in counter.most_common(
                limit
            )
        ]

    @staticmethod
    def _to_dict(
        value: Any,
    ) -> Dict[str, Any]:
        if value is None:
            return {}

        if hasattr(
            value,
            "model_dump",
        ):
            return value.model_dump(
                mode="python"
            )

        if is_dataclass(value):
            return asdict(value)

        if isinstance(
            value,
            dict,
        ):
            return value

        if hasattr(
            value,
            "__dict__",
        ):
            return dict(
                value.__dict__
            )

        return {}

    @classmethod
    def _serialize(
        cls,
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
                str(key): cls._serialize(
                    item
                )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                cls._serialize(
                    item
                )
                for item
                in value
            ]

        return value