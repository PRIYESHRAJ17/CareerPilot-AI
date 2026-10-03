from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Set

from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)


class CareerTwinJobIntelligence:
    """
    Career Twin-aware intelligence layer for job analysis.

    Design principles:

    1. Hard evidence remains authoritative.
    2. Career Twin context enriches matching rather than blindly
       overriding deterministic job evidence.
    3. Every conclusion is explainable.
    4. Missing skills are separated into:
       - immediate requirements
       - useful growth opportunities
       - non-critical gaps
    5. The output is JSON-friendly so it can be persisted, returned
       by APIs, and consumed by agents without another translation
       layer.
    """

    ROLE_WEIGHT = 0.25
    SKILL_WEIGHT = 0.35
    GOAL_WEIGHT = 0.15
    GROWTH_WEIGHT = 0.15
    LOCATION_WEIGHT = 0.10

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
    # PUBLIC API
    # ============================================================

    def analyze(
        self,
        job: Job,
        career_twin: Any,
        requirements: Optional[JobRequirements] = None,
    ) -> Dict[str, Any]:
        """
        Produce a Career Twin-aware interpretation of one job.
        """

        requirements = requirements or (
            self.requirements_extractor.extract(job)
        )

        twin = self._to_dict(career_twin)

        current_skills = self._skill_set(
            twin.get("current_skills"),
            twin.get("skills"),
            twin.get("technical_skills"),
            twin.get("profile", {}).get("skills"),
            twin.get("profile", {}).get(
                "technical_skills"
            ),
        )

        derived = twin.get("derived") or {}

        strengths = self._skill_set(
            twin.get("strengths"),
            derived.get("strengths"),
        )

        skill_gaps = self._skill_set(
            twin.get("skill_gaps"),
            derived.get("skill_gaps"),
            derived.get("gaps"),
        )

        target_roles = self._string_list(
            twin.get("target_roles"),
            twin.get("career_goals"),
            twin.get("target_career_directions"),
            derived.get("career_directions"),
        )

        target_industries = self._string_list(
            twin.get("target_industries"),
            twin.get("industries"),
        )

        preferred_locations = self._string_list(
            twin.get("preferred_locations"),
            twin.get("locations"),
        )

        preferred_work_modes = self._string_list(
            twin.get("preferred_work_modes"),
            twin.get("work_modes"),
        )

        required_skills = {
            self._normalize(skill)
            for skill in (
                requirements.required_skills
                + requirements.preferred_skills
                + requirements.technologies
            )
            if self._normalize(skill)
        }

        matched_skills = sorted(
            required_skills.intersection(
                current_skills | strengths
            )
        )

        missing_skills = sorted(
            required_skills.difference(
                current_skills | strengths
            )
        )

        career_gap_matches = sorted(
            set(missing_skills).intersection(
                skill_gaps
            )
        )

        role_alignment = self._role_alignment(
            job=job,
            target_roles=target_roles,
        )

        skill_alignment = self._skill_alignment(
            required_skills=required_skills,
            available_skills=(
                current_skills | strengths
            ),
        )

        goal_alignment = self._goal_alignment(
            job=job,
            target_industries=target_industries,
        )

        growth_relevance = self._growth_relevance(
            missing_skills=missing_skills,
            career_gap_matches=career_gap_matches,
        )

        location_alignment = self._location_alignment(
            job=job,
            preferred_locations=preferred_locations,
            preferred_work_modes=preferred_work_modes,
        )

        score = round(
            (
                role_alignment * self.ROLE_WEIGHT
                + skill_alignment * self.SKILL_WEIGHT
                + goal_alignment * self.GOAL_WEIGHT
                + growth_relevance * self.GROWTH_WEIGHT
                + location_alignment * self.LOCATION_WEIGHT
            ),
            2,
        )

        risks = self._build_risks(
            job=job,
            requirements=requirements,
            missing_skills=missing_skills,
            career_gap_matches=career_gap_matches,
            role_alignment=role_alignment,
            location_alignment=location_alignment,
        )

        evidence = self._build_evidence(
            job=job,
            requirements=requirements,
            matched_skills=matched_skills,
            career_gap_matches=career_gap_matches,
            target_roles=target_roles,
            target_industries=target_industries,
        )

        reasoning = self._build_reasoning(
            job=job,
            score=score,
            role_alignment=role_alignment,
            skill_alignment=skill_alignment,
            goal_alignment=goal_alignment,
            growth_relevance=growth_relevance,
            location_alignment=location_alignment,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            career_gap_matches=career_gap_matches,
        )

        confidence = self._confidence(
            twin=twin,
            requirements=requirements,
            required_skills=required_skills,
        )

        return {
            "career_twin_match_score": score,
            "career_twin_confidence": confidence,
            "career_twin_role_alignment": round(
                role_alignment,
                2,
            ),
            "career_twin_skill_alignment": round(
                skill_alignment,
                2,
            ),
            "career_twin_goal_alignment": round(
                goal_alignment,
                2,
            ),
            "career_twin_growth_relevance": round(
                growth_relevance,
                2,
            ),
            "career_twin_location_alignment": round(
                location_alignment,
                2,
            ),
            "career_twin_matched_skills": matched_skills,
            "career_twin_missing_skills": missing_skills,
            "career_twin_gap_matches": career_gap_matches,
            "career_twin_evidence": evidence,
            "career_twin_risks": risks,
            "career_twin_reasoning": reasoning,
            "job_requirement_count": len(
                required_skills
            ),
            "career_twin_skill_count": len(
                current_skills | strengths
            ),
        }

    def aggregate_requirements(
        self,
        jobs: Iterable[Job],
    ) -> Dict[str, Any]:
        """
        Aggregate requirements across a discovered opportunity set.

        This is intentionally deterministic so the same opportunity
        pool always produces the same career-gap signals.
        """

        jobs = list(jobs)

        skill_counter: Counter[str] = Counter()
        required_skill_counter: Counter[str] = Counter()
        preferred_skill_counter: Counter[str] = Counter()
        seniority_counter: Counter[str] = Counter()
        domain_counter: Counter[str] = Counter()
        experience_values: List[float] = []

        analyzed_jobs = 0

        for job in jobs:
            requirements = (
                self.requirements_extractor.extract(job)
            )

            analyzed_jobs += 1

            for skill in requirements.technologies:
                normalized = self._normalize(skill)
                if normalized:
                    skill_counter[normalized] += 1

            for skill in requirements.required_skills:
                normalized = self._normalize(skill)
                if normalized:
                    required_skill_counter[
                        normalized
                    ] += 1

            for skill in requirements.preferred_skills:
                normalized = self._normalize(skill)
                if normalized:
                    preferred_skill_counter[
                        normalized
                    ] += 1

            if requirements.seniority:
                seniority_counter[
                    requirements.seniority
                ] += 1

            if requirements.domain:
                domain_counter[
                    requirements.domain
                ] += 1

            if (
                requirements.years_experience_min
                is not None
            ):
                experience_values.append(
                    requirements.years_experience_min
                )

        return {
            "jobs_analyzed": analyzed_jobs,
            "unique_technologies": len(
                skill_counter
            ),
            "top_technologies": self._top_counter(
                skill_counter
            ),
            "top_required_skills": self._top_counter(
                required_skill_counter
            ),
            "top_preferred_skills": self._top_counter(
                preferred_skill_counter
            ),
            "seniority_distribution": dict(
                seniority_counter.most_common()
            ),
            "domain_distribution": dict(
                domain_counter.most_common()
            ),
            "average_min_experience": (
                round(
                    sum(experience_values)
                    / len(experience_values),
                    2,
                )
                if experience_values
                else None
            ),
            "max_observed_min_experience": (
                max(experience_values)
                if experience_values
                else None
            ),
        }

    # ============================================================
    # MATCHING DIMENSIONS
    # ============================================================

    def _role_alignment(
        self,
        job: Job,
        target_roles: List[str],
    ) -> float:
        if not target_roles:
            return 70.0

        title = self._normalize(job.title)

        best = 35.0

        for target in target_roles:
            target_normalized = self._normalize(
                target
            )

            if not target_normalized:
                continue

            if (
                target_normalized == title
            ):
                best = max(best, 100.0)
                continue

            if (
                target_normalized in title
                or title in target_normalized
            ):
                best = max(best, 90.0)
                continue

            target_words = {
                word
                for word in target_normalized.split()
                if len(word) > 2
            }

            title_words = {
                word
                for word in title.split()
                if len(word) > 2
            }

            if target_words:
                overlap = len(
                    target_words.intersection(
                        title_words
                    )
                ) / len(target_words)

                if overlap >= 0.75:
                    best = max(best, 85.0)
                elif overlap >= 0.50:
                    best = max(best, 75.0)
                elif overlap >= 0.25:
                    best = max(best, 60.0)

        return best

    @staticmethod
    def _skill_alignment(
        required_skills: Set[str],
        available_skills: Set[str],
    ) -> float:
        if not required_skills:
            return 70.0

        matched = len(
            required_skills.intersection(
                available_skills
            )
        )

        return round(
            (
                matched
                / len(required_skills)
            )
            * 100,
            2,
        )

    def _goal_alignment(
        self,
        job: Job,
        target_industries: List[str],
    ) -> float:
        if not target_industries:
            return 70.0

        haystack = " ".join(
            [
                job.title,
                job.company,
                job.description,
                str(job.metadata),
            ]
        ).casefold()

        matches = [
            industry
            for industry in target_industries
            if self._normalize(industry)
            and self._normalize(industry)
            in haystack
        ]

        if matches:
            return 100.0

        return 50.0

    @staticmethod
    def _growth_relevance(
        missing_skills: List[str],
        career_gap_matches: List[str],
    ) -> float:
        if not missing_skills:
            return 100.0

        if not career_gap_matches:
            return 45.0

        ratio = (
            len(career_gap_matches)
            / len(missing_skills)
        )

        return round(
            55.0 + (ratio * 45.0),
            2,
        )

    def _location_alignment(
        self,
        job: Job,
        preferred_locations: List[str],
        preferred_work_modes: List[str],
    ) -> float:
        if (
            not preferred_locations
            and not preferred_work_modes
        ):
            return 70.0

        location_score = 70.0
        work_mode_score = 70.0

        normalized_job_locations = {
            self._normalize(location)
            for location in job.location
            if self._normalize(location)
        }

        normalized_preferences = {
            self._normalize(location)
            for location in preferred_locations
            if self._normalize(location)
        }

        if normalized_preferences:
            if normalized_job_locations.intersection(
                normalized_preferences
            ):
                location_score = 100.0
            elif job.remote:
                location_score = 90.0
            else:
                location_score = 30.0

        normalized_modes = {
            self._normalize(mode)
            for mode in preferred_work_modes
        }

        if normalized_modes:
            if job.remote and any(
                mode in {"remote", "remote-first"}
                for mode in normalized_modes
            ):
                work_mode_score = 100.0
            elif (
                any(
                    mode
                    in {
                        "hybrid",
                        "onsite",
                        "on-site",
                        "office",
                    }
                    for mode in normalized_modes
                )
                and not job.remote
            ):
                work_mode_score = 90.0
            else:
                work_mode_score = 50.0

        return round(
            (
                location_score
                + work_mode_score
            )
            / 2,
            2,
        )

    # ============================================================
    # EVIDENCE / EXPLANATION
    # ============================================================

    def _build_evidence(
        self,
        job: Job,
        requirements: JobRequirements,
        matched_skills: List[str],
        career_gap_matches: List[str],
        target_roles: List[str],
        target_industries: List[str],
    ) -> List[Dict[str, Any]]:
        evidence: List[Dict[str, Any]] = []

        if matched_skills:
            evidence.append(
                {
                    "type": "skill_alignment",
                    "strength": "positive",
                    "details": (
                        f"{len(matched_skills)} job "
                        "requirements overlap with "
                        "Career Twin skills."
                    ),
                    "skills": matched_skills[:20],
                }
            )

        if career_gap_matches:
            evidence.append(
                {
                    "type": "career_gap_relevance",
                    "strength": "positive",
                    "details": (
                        "This opportunity requires skills "
                        "that are already present in the "
                        "Career Twin's tracked development gaps."
                    ),
                    "skills": career_gap_matches[:20],
                }
            )

        if target_roles:
            evidence.append(
                {
                    "type": "career_direction",
                    "strength": "context",
                    "details": (
                        "Job was evaluated against the "
                        "Career Twin target directions."
                    ),
                    "target_roles": target_roles[:10],
                }
            )

        if target_industries:
            evidence.append(
                {
                    "type": "industry_goal",
                    "strength": "context",
                    "details": (
                        "Job was checked against the "
                        "Career Twin target industries."
                    ),
                    "target_industries": (
                        target_industries[:10]
                    ),
                }
            )

        if requirements.years_experience_min is not None:
            evidence.append(
                {
                    "type": "experience_requirement",
                    "strength": "neutral",
                    "minimum_years": (
                        requirements.years_experience_min
                    ),
                    "maximum_years": (
                        requirements.years_experience_max
                    ),
                }
            )

        return evidence

    @staticmethod
    def _build_risks(
        job: Job,
        requirements: JobRequirements,
        missing_skills: List[str],
        career_gap_matches: List[str],
        role_alignment: float,
        location_alignment: float,
    ) -> List[Dict[str, Any]]:
        risks: List[Dict[str, Any]] = []

        hard_missing = set(
            requirements.required_skills
        ).intersection(
            set(missing_skills)
        )

        if hard_missing:
            risks.append(
                {
                    "type": "required_skill_gap",
                    "severity": "high",
                    "skills": sorted(
                        hard_missing
                    )[:20],
                }
            )

        if (
            career_gap_matches
            and not hard_missing
        ):
            risks.append(
                {
                    "type": "development_opportunity",
                    "severity": "medium",
                    "skills": career_gap_matches[:20],
                }
            )

        if role_alignment < 50:
            risks.append(
                {
                    "type": "role_misalignment",
                    "severity": "high",
                    "job_title": job.title,
                }
            )

        if location_alignment < 50:
            risks.append(
                {
                    "type": "location_misalignment",
                    "severity": "medium",
                    "locations": list(
                        job.location
                    ),
                }
            )

        return risks

    @staticmethod
    def _build_reasoning(
        job: Job,
        score: float,
        role_alignment: float,
        skill_alignment: float,
        goal_alignment: float,
        growth_relevance: float,
        location_alignment: float,
        matched_skills: List[str],
        missing_skills: List[str],
        career_gap_matches: List[str],
    ) -> str:
        parts = [
            (
                f"Career Twin compatibility for "
                f"'{job.title}' is {score}/100."
            ),
            (
                f"Role alignment: {role_alignment}/100."
            ),
            (
                f"Skill alignment: {skill_alignment}/100."
            ),
            (
                f"Career-goal alignment: "
                f"{goal_alignment}/100."
            ),
            (
                f"Growth relevance: "
                f"{growth_relevance}/100."
            ),
            (
                f"Location/work-mode alignment: "
                f"{location_alignment}/100."
            ),
        ]

        if matched_skills:
            parts.append(
                "Matched skills: "
                + ", ".join(
                    matched_skills[:8]
                )
                + "."
            )

        if missing_skills:
            parts.append(
                "Missing tracked requirements: "
                + ", ".join(
                    missing_skills[:8]
                )
                + "."
            )

        if career_gap_matches:
            parts.append(
                "The opportunity also overlaps with "
                "tracked career-development gaps: "
                + ", ".join(
                    career_gap_matches[:8]
                )
                + "."
            )

        return " ".join(parts)

    @staticmethod
    def _confidence(
        twin: Dict[str, Any],
        requirements: JobRequirements,
        required_skills: Set[str],
    ) -> float:
        evidence_points = 0

        if twin:
            evidence_points += 1

        if required_skills:
            evidence_points += 1

        if requirements.required_skills:
            evidence_points += 1

        if requirements.seniority:
            evidence_points += 1

        if requirements.years_experience_min is not None:
            evidence_points += 1

        if requirements.domain:
            evidence_points += 1

        if not evidence_points:
            return 50.0

        return round(
            min(
                95.0,
                55.0
                + (
                    evidence_points * 7.5
                ),
            ),
            2,
        )

    # ============================================================
    # AGGREGATION HELPERS
    # ============================================================

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
            for value, count in counter.most_common(
                limit
            )
        ]

    # ============================================================
    # DATA NORMALIZATION
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

            if isinstance(value, str):
                normalized = cls._normalize(value)
                if normalized:
                    output.add(normalized)
                continue

            if isinstance(value, dict):
                output.update(
                    cls._skill_set(
                        *value.values()
                    )
                )
                continue

            if isinstance(value, (list, tuple, set)):
                for item in value:
                    normalized = cls._normalize(
                        str(item)
                    )
                    if normalized:
                        output.add(normalized)
                continue

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

            if isinstance(value, str):
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
                    str(item)
                )

                if (
                    normalized
                    and normalized not in seen
                ):
                    seen.add(normalized)
                    result.append(
                        str(item).strip()
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

    @classmethod
    def _to_dict(
        cls,
        value: Any,
    ) -> Dict[str, Any]:
        if value is None:
            return {}

        if hasattr(value, "model_dump"):
            return value.model_dump(
                mode="python"
            )

        if is_dataclass(value):
            return asdict(value)

        if isinstance(value, dict):
            return value

        if hasattr(value, "__dict__"):
            return dict(value.__dict__)

        return {}