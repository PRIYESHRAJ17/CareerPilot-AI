from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END


# ============================================================
# ROUTE TARGETS
# ============================================================

ROUTE_TARGETS = {
    "candidate": "candidate",
    "resume": "resume",
    "job": "job",
    "strategy": "strategy",
    "recommendation": "recommendation",
    "validation": "validation",
    "recovery": "recovery",
    "final": "final",
    "user": END,
    "end": END,
}


# ============================================================
# SUPERVISOR ROUTING
# ============================================================

def route_after_supervisor(
    state: Dict[str, Any],
) -> str:
    """
    Convert the Supervisor's routing decision into a LangGraph
    node name.

    Expected Supervisor output:

        state["supervisor_decision"]["next_agent"]

    Examples:

        candidate
        resume
        job
        strategy
        recommendation
        validation
        recovery
        final
        user
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Routing state must be a dictionary."
        )

    decision = state.get(
        "supervisor_decision"
    )

    if not isinstance(
        decision,
        dict,
    ):
        raise ValueError(
            "Missing or invalid 'supervisor_decision' "
            "in shared state."
        )

    next_agent = str(
        decision.get(
            "next_agent",
            "",
        )
        or ""
    ).strip().lower()

    if not next_agent:
        raise ValueError(
            "Supervisor decision does not contain "
            "'next_agent'."
        )

    if next_agent not in ROUTE_TARGETS:
        raise ValueError(
            f"Unknown Supervisor route '{next_agent}'. "
            f"Valid routes: "
            f"{sorted(ROUTE_TARGETS.keys())}"
        )

    return ROUTE_TARGETS[
        next_agent
    ]


# ============================================================
# GENERIC ROUTER
# ============================================================

def route_from_decision(
    state: Dict[str, Any],
) -> str:
    """
    Generic routing helper for workflow nodes that write:

        state["last_decision"]["next_step"]

    This gives later workflow/recovery nodes a common routing
    interface.
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Routing state must be a dictionary."
        )

    decision = state.get(
        "last_decision"
    )

    if not isinstance(
        decision,
        dict,
    ):
        raise ValueError(
            "Missing or invalid 'last_decision' "
            "in shared state."
        )

    next_step = str(
        decision.get(
            "next_step",
            "",
        )
        or ""
    ).strip().lower()

    if not next_step:
        raise ValueError(
            "Decision does not contain 'next_step'."
        )

    if next_step not in ROUTE_TARGETS:
        raise ValueError(
            f"Unknown workflow route '{next_step}'. "
            f"Valid routes: "
            f"{sorted(ROUTE_TARGETS.keys())}"
        )

    return ROUTE_TARGETS[
        next_step
    ]


# ============================================================
# SPECIALIST → SUPERVISOR
# ============================================================

def route_after_specialist(
    state: Dict[str, Any],
) -> str:
    """
    All successful specialist agents return control to the
    Supervisor so it can inspect the updated shared state and
    decide the next step.

    This is intentionally centralized instead of hard-coding
    specialist-to-specialist edges.
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Routing state must be a dictionary."
        )

    return "supervisor"


# ============================================================
# VALIDATION ROUTING
# ============================================================

def route_after_validation(
    state: Dict[str, Any],
) -> str:
    """
    Route Validation Agent output:

        VALID
          ↓
        final

        INVALID
          ↓
        recovery
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Routing state must be a dictionary."
        )

    final_validation = state.get(
        "final_validation"
    )

    if not isinstance(
        final_validation,
        dict,
    ):
        raise ValueError(
            "Validation state is missing "
            "'final_validation'."
        )

    status = str(
        final_validation.get(
            "status",
            "",
        )
        or ""
    ).strip().upper()

    if status == "VALID":
        return "final"

    if status == "INVALID":
        return "recovery"

    # Do not silently finalize unknown validation states.
    raise ValueError(
        f"Unknown validation status '{status}'. "
        "Expected VALID or INVALID."
    )


# ============================================================
# RECOVERY ROUTING
# ============================================================

def route_after_recovery(
    state: Dict[str, Any],
) -> str:
    """
    Recovery currently sends the workflow to the user when it
    explicitly requires clarification.

    Future Level 8 recovery logic can route repairable failures
    back to a specialist or Supervisor.
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Routing state must be a dictionary."
        )

    if bool(
        state.get(
            "needs_user_input",
            False,
        )
    ):
        return "user"

    # Safe fallback: return to Supervisor rather than silently
    # continuing with potentially invalid state.
    return "supervisor"


# ============================================================
# ROUTING MAPS
# ============================================================

SUPERVISOR_CONDITIONAL_MAP = {
    "candidate": "candidate",
    "resume": "resume",
    "job": "job",
    "strategy": "strategy",
    "recommendation": "recommendation",
    "validation": "validation",
    "recovery": "recovery",
    "final": "final",
    "user": END,
}


VALIDATION_CONDITIONAL_MAP = {
    "final": "final",
    "recovery": "recovery",
}


RECOVERY_CONDITIONAL_MAP = {
    "user": END,
    "supervisor": "supervisor",
}