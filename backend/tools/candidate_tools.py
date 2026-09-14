from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.services.candidate_intelligence import (
    CandidateIntelligenceEngine,
)


candidate_intelligence_engine = CandidateIntelligenceEngine()


def _build_candidate_profile(
    candidate_data: Dict[str, Any],
) -> CandidateProfile:
    """
    Convert a JSON-compatible candidate payload into the
    existing CareerPilot CandidateProfile model.
    """

    career_goal_data = candidate_data.get(
        "career_goal",
        {},
    ) or {}

    career_goal = CareerGoal(
        target_roles=list(
            career_goal_data.get(
                "target_roles",
                [],
            )
        ),
        target_industries=list(
            career_goal_data.get(
                "target_industries",
                [],
            )
        ),
        target_locations=list(
            career_goal_data.get(
                "target_locations",
                [],
            )
        ),
        minimum_salary_lpa=career_goal_data.get(
            "minimum_salary_lpa"
        ),
        preferred_work_modes=list(
            career_goal_data.get(
                "preferred_work_modes",
                [],
            )
        ),
        target_timeline_months=career_goal_data.get(
            "target_timeline_months"
        ),
    )

    return CandidateProfile(
        candidate_id=str(
            candidate_data.get(
                "candidate_id",
                "agentic-user",
            )
        ),
        name=candidate_data.get("name"),
        headline=candidate_data.get("headline"),
        skills=list(
            candidate_data.get(
                "skills",
                [],
            )
        ),
        technical_skills=list(
            candidate_data.get(
                "technical_skills",
                [],
            )
        ),
        soft_skills=list(
            candidate_data.get(
                "soft_skills",
                [],
            )
        ),
        years_of_experience=float(
            candidate_data.get(
                "years_of_experience",
                0.0,
            )
            or 0.0
        ),
        notice_period_days=candidate_data.get(
            "notice_period_days"
        ),
        education=list(
            candidate_data.get(
                "education",
                [],
            )
        ),
        certifications=list(
            candidate_data.get(
                "certifications",
                [],
            )
        ),
        projects=list(
            candidate_data.get(
                "projects",
                [],
            )
        ),
        career_goal=career_goal,
        preferred_locations=list(
            candidate_data.get(
                "preferred_locations",
                [],
            )
        ),
        preferred_work_modes=list(
            candidate_data.get(
                "preferred_work_modes",
                [],
            )
        ),
        metadata=dict(
            candidate_data.get(
                "metadata",
                {},
            )
        ),
    )


def analyze_candidate_profile(
    candidate_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministically analyze candidate intelligence.

    This helper is used both by the LangGraph nodes and by
    the LLM-facing tool wrapper.
    """

    candidate = _build_candidate_profile(
        candidate_data
    )

    intelligence = (
        candidate_intelligence_engine.analyze(
            candidate
        )
    )

    return {
        "profile_completeness": (
            intelligence.profile_completeness
        ),
        "normalized_skills": (
            intelligence.normalized_skills
        ),
        "skill_categories": (
            intelligence.skill_categories
        ),
        "strengths": intelligence.strengths,
        "missing_information": (
            intelligence.missing_information
        ),
        "career_direction": (
            intelligence.career_direction
        ),
        "target_roles": (
            intelligence.target_roles
        ),
        "target_industries": (
            intelligence.target_industries
        ),
        "readiness_level": (
            intelligence.readiness_level
        ),
        "readiness_score": (
            intelligence.readiness_score
        ),
        "recommendations": (
            intelligence.recommendations
        ),
    }


@tool
def analyze_candidate(
    candidate_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze a candidate profile using CareerPilot's
    deterministic candidate intelligence engine.

    Use this tool when candidate-level career intelligence
    is required.
    """

    if not isinstance(
        candidate_data,
        dict,
    ):
        raise TypeError(
            "candidate_data must be a dictionary"
        )

    return analyze_candidate_profile(
        candidate_data
    )