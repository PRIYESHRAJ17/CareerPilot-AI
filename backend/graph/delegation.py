from __future__ import annotations

from typing import Any, Callable, Dict


# ============================================================
# DELEGATION REGISTRY
# ============================================================

def _load_agent_runner(
    agent_name: str,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Lazily resolve a specialist agent runner.

    Lazy imports keep the graph/delegation layer lightweight and
    avoid importing the heavier job-search stack until the Job
    Agent is actually delegated to.
    """

    if agent_name == "candidate":
        from backend.agents.candidate_agent import (
            run_candidate_agent,
        )

        return run_candidate_agent

    if agent_name == "resume":
        from backend.agents.resume_agent import (
            run_resume_agent,
        )

        return run_resume_agent

    if agent_name == "job":
        from backend.agents.job_agent import (
            run_job_agent,
        )

        return run_job_agent

    if agent_name == "strategy":
        from backend.agents.strategy_agent import (
            run_strategy_agent,
        )

        return run_strategy_agent

    if agent_name == "recommendation":
        from backend.agents.recommendation_agent import (
            run_recommendation_agent,
        )

        return run_recommendation_agent

    if agent_name == "validation":
        from backend.agents.validation_agent import (
            run_validation_agent,
        )

        return run_validation_agent

    raise ValueError(
        f"Unknown delegatable agent '{agent_name}'."
    )


# ============================================================
# VALID AGENTS
# ============================================================

DELEGATABLE_AGENTS = {
    "candidate",
    "resume",
    "job",
    "strategy",
    "recommendation",
    "validation",
}


# ============================================================
# DELEGATION
# ============================================================

def delegate(
    state: Dict[str, Any],
    agent_name: str,
) -> Dict[str, Any]:
    """
    Delegate shared workflow state to one specialist agent.

    The delegation is real:
        Supervisor decision
              ↓
        delegate()
              ↓
        specialist agent
              ↓
        actual deterministic tool calls
              ↓
        updated shared state
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Delegation state must be a dictionary."
        )

    normalized_agent = str(
        agent_name
    ).strip().lower()

    if normalized_agent not in DELEGATABLE_AGENTS:
        raise ValueError(
            f"Agent '{normalized_agent}' is not delegatable. "
            f"Valid agents: {sorted(DELEGATABLE_AGENTS)}"
        )

    runner = _load_agent_runner(
        normalized_agent
    )

    delegated_state = dict(state)

    # --------------------------------------------------------
    # Record delegation before execution
    # --------------------------------------------------------

    delegation_trace = list(
        delegated_state.get(
            "delegation_trace",
            [],
        )
        or []
    )

    delegation_trace.append(
        {
            "from_agent": (
                delegated_state.get(
                    "current_agent"
                )
                or "supervisor"
            ),
            "to_agent": normalized_agent,
            "status": "started",
        }
    )

    delegated_state[
        "delegation_trace"
    ] = delegation_trace

    # --------------------------------------------------------
    # Execute real specialist
    # --------------------------------------------------------

    try:
        result = runner(
            delegated_state
        )
    except Exception as exc:
        delegation_trace = list(
            delegated_state.get(
                "delegation_trace",
                [],
            )
            or []
        )

        delegation_trace.append(
            {
                "from_agent": (
                    delegated_state.get(
                        "current_agent"
                    )
                    or "supervisor"
                ),
                "to_agent": normalized_agent,
                "status": "failed",
                "error": str(exc),
            }
        )

        failed_state = dict(
            delegated_state
        )

        failed_state[
            "delegation_trace"
        ] = delegation_trace

        errors = list(
            failed_state.get(
                "errors",
                [],
            )
            or []
        )

        errors.append(
            {
                "source": (
                    f"delegation:{normalized_agent}"
                ),
                "message": str(exc),
            }
        )

        failed_state[
            "errors"
        ] = errors

        raise

    if not isinstance(
        result,
        dict,
    ):
        raise TypeError(
            f"Delegated agent '{normalized_agent}' "
            "returned a non-dictionary state."
        )

    # --------------------------------------------------------
    # Record successful completion
    # --------------------------------------------------------

    result_state = dict(
        result
    )

    delegation_trace = list(
        result_state.get(
            "delegation_trace",
            delegated_state.get(
                "delegation_trace",
                [],
            ),
        )
        or []
    )

    delegation_trace.append(
        {
            "from_agent": (
                delegated_state.get(
                    "current_agent"
                )
                or "supervisor"
            ),
            "to_agent": normalized_agent,
            "status": "completed",
        }
    )

    result_state[
        "delegation_trace"
    ] = delegation_trace

    return result_state


# ============================================================
# SUPERVISOR-DRIVEN DELEGATION
# ============================================================

def delegate_from_supervisor(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Delegate based directly on the Supervisor's latest decision.

    Expected:
        state["supervisor_decision"]["next_agent"]
    """

    if not isinstance(
        state,
        dict,
    ):
        raise TypeError(
            "Delegation state must be a dictionary."
        )

    decision = state.get(
        "supervisor_decision"
    )

    if not isinstance(
        decision,
        dict,
    ):
        raise ValueError(
            "Missing Supervisor decision in shared state."
        )

    next_agent = str(
        decision.get(
            "next_agent",
            "",
        )
        or ""
    ).strip().lower()

    if next_agent in {
        "",
        "final",
        "recovery",
        "user",
        "end",
    }:
        raise ValueError(
            f"Supervisor route '{next_agent}' "
            "is not a specialist delegation target."
        )

    return delegate(
        state=state,
        agent_name=next_agent,
    )


# ============================================================
# TRACE HELPERS
# ============================================================

def delegation_summary(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return compact delegation metrics for API/frontend tracing.
    """

    trace = state.get(
        "delegation_trace",
        [],
    )

    if not isinstance(
        trace,
        list,
    ):
        trace = []

    completed = sum(
        1
        for item in trace
        if isinstance(
            item,
            dict,
        )
        and item.get(
            "status"
        ) == "completed"
    )

    failed = sum(
        1
        for item in trace
        if isinstance(
            item,
            dict,
        )
        and item.get(
            "status"
        ) == "failed"
    )

    started = sum(
        1
        for item in trace
        if isinstance(
            item,
            dict,
        )
        and item.get(
            "status"
        ) == "started"
    )

    return {
        "total_events": len(trace),
        "started": started,
        "completed": completed,
        "failed": failed,
        "trace": trace,
    }