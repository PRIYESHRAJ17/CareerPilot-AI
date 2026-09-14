from dataclasses import asdict, is_dataclass
from typing import Any, Dict

from langchain_core.tools import tool

from backend.career_strategy import (
    CareerStrategy,
    generate_career_strategy,
)
from backend.services.candidate_intelligence import (
    CandidateIntelligence,
)


# ============================================================
# SERIALIZATION
# ============================================================

def _serialize(value: Any) -> Any:
    """
    Convert CareerPilot domain objects into JSON-compatible data.
    """

    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _serialize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ============================================================
# INPUT BUILDER
# ============================================================

def _build_candidate_intelligence(
    intelligence_data: Dict[str, Any],
) -> CandidateIntelligence:
    """
    Reconstruct the existing CandidateIntelligence object
    from serialized workflow/tool state.

    This exactly follows the Week 3 CandidateIntelligence
    dataclass rather than introducing additional fields.
    """

    if not isinstance(
        intelligence_data,
        dict,
    ):
        raise TypeError(
            "candidate_intelligence must be a dictionary."
        )

    return CandidateIntelligence(
        profile_completeness=float(
            intelligence_data.get(
                "profile_completeness",
                0.0,
            )
            or 0.0
        ),
        normalized_skills=list(
            intelligence_data.get(
                "normalized_skills",
                [],
            )
            or []
        ),
        skill_categories=dict(
            intelligence_data.get(
                "skill_categories",
                {},
            )
            or {}
        ),
        strengths=list(
            intelligence_data.get(
                "strengths",
                [],
            )
            or []
        ),
        missing_information=list(
            intelligence_data.get(
                "missing_information",
                [],
            )
            or []
        ),
        career_direction=list(
            intelligence_data.get(
                "career_direction",
                [],
            )
            or []
        ),
        target_roles=list(
            intelligence_data.get(
                "target_roles",
                [],
            )
            or []
        ),
        target_industries=list(
            intelligence_data.get(
                "target_industries",
                [],
            )
            or []
        ),
        readiness_level=str(
            intelligence_data.get(
                "readiness_level",
                "EARLY_STAGE",
            )
        ),
        readiness_score=float(
            intelligence_data.get(
                "readiness_score",
                0.0,
            )
            or 0.0
        ),
        recommendations=list(
            intelligence_data.get(
                "recommendations",
                [],
            )
            or []
        ),
    )


# ============================================================
# LOW-LEVEL STRATEGY CAPABILITY
# ============================================================

def generate_strategy(
    intelligence_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate an actionable career strategy using the existing
    deterministic Week 3 strategy engine.
    """

    intelligence = _build_candidate_intelligence(
        intelligence_data
    )

    strategy = generate_career_strategy(
        intelligence
    )

    return _serialize(strategy)


def build_strategy_summary(
    strategy_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce a compact strategy summary from an existing
    CareerStrategy object/state.
    """

    if not isinstance(
        strategy_data,
        dict,
    ):
        raise TypeError(
            "strategy_data must be a dictionary."
        )

    strategy = CareerStrategy(
        primary_role=str(
            strategy_data.get(
                "primary_role",
                "",
            )
        ),
        career_directions=list(
            strategy_data.get(
                "career_directions",
                [],
            )
            or []
        ),
        priority_skills=list(
            strategy_data.get(
                "priority_skills",
                [],
            )
            or []
        ),
        improvement_areas=list(
            strategy_data.get(
                "improvement_areas",
                [],
            )
            or []
        ),
        recommended_actions=list(
            strategy_data.get(
                "recommended_actions",
                [],
            )
            or []
        ),
        strategy_summary=str(
            strategy_data.get(
                "strategy_summary",
                "",
            )
        ),
    )

    return {
        "primary_role": strategy.primary_role,
        "career_directions": strategy.career_directions,
        "priority_skills": strategy.priority_skills,
        "improvement_areas": strategy.improvement_areas,
        "recommended_actions": strategy.recommended_actions,
        "strategy_summary": strategy.strategy_summary,
    }


# ============================================================
# LANGCHAIN TOOLS
# ============================================================

@tool
def create_career_strategy(
    candidate_intelligence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a deterministic career strategy from candidate
    intelligence.
    """

    return generate_strategy(
        intelligence_data=candidate_intelligence
    )


@tool
def summarize_career_strategy(
    strategy: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return a normalized, presentation-ready career strategy
    summary from the shared workflow state.
    """

    return build_strategy_summary(
        strategy_data=strategy
    )


# ============================================================
# CONVENIENCE PIPELINE
# ============================================================

def run_strategy_pipeline(
    intelligence_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the complete deterministic career-strategy capability.
    """

    strategy = generate_strategy(
        intelligence_data=intelligence_data
    )

    summary = build_strategy_summary(
        strategy_data=strategy
    )

    return {
        "strategy": strategy,
        "summary": summary,
    }


@tool
def run_career_strategy_pipeline(
    candidate_intelligence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the complete career strategy pipeline for an agent.
    """

    return run_strategy_pipeline(
        intelligence_data=candidate_intelligence
    )