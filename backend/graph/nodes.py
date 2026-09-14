from __future__ import annotations

from typing import Any

from backend.graph.safety import evaluate_workflow_safety
from backend.graph.state import CareerPilotState
from backend.schemas.agentic import (
    AgentName,
    WorkflowStatus,
)


def _normalise_workflow_metadata(
    state: CareerPilotState,
) -> CareerPilotState:
    """
    Keep the Pydantic WorkflowMetadata object internally consistent.

    LangGraph state may contain ordinary strings such as "supervisor"
    or "COMPLETED". WorkflowMetadata expects AgentName / WorkflowStatus
    enum values, so we normalize them before the state is checkpointed
    or serialized.
    """

    updated = dict(state)

    workflow = updated.get("workflow")

    if workflow is None:
        return updated

    current_agent = updated.get("current_agent")

    if current_agent:
        try:
            current_agent_value = (
                current_agent.value
                if isinstance(current_agent, AgentName)
                else str(current_agent)
            )

            if current_agent_value in {
                member.value
                for member in AgentName
            }:
                workflow.current_agent = AgentName(
                    current_agent_value
                )
            else:
                # "final" is a graph terminal state, not a specialist
                # agent, so it is intentionally not stored as AgentName.
                workflow.current_agent = None
        except Exception:
            pass

    workflow_status = updated.get(
        "workflow_status"
    )

    if workflow_status:
        try:
            workflow.status = WorkflowStatus(
                workflow_status.value
                if isinstance(
                    workflow_status,
                    WorkflowStatus,
                )
                else str(workflow_status)
            )
        except Exception:
            pass

    try:
        workflow_agents = []

        for agent in (
            workflow.agents_used or []
        ):
            try:
                workflow_agents.append(
                    agent
                    if isinstance(agent, AgentName)
                    else AgentName(str(agent))
                )
            except Exception:
                continue

        workflow.agents_used = workflow_agents
    except Exception:
        pass

    updated["workflow"] = workflow

    return updated


def supervisor_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.supervisor_agent import (
        run_supervisor_agent,
    )

    updated = run_supervisor_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def candidate_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.candidate_agent import (
        run_candidate_agent,
    )

    updated = run_candidate_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def resume_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.resume_agent import (
        run_resume_agent,
    )

    updated = run_resume_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def job_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.job_agent import (
        run_job_agent,
    )

    updated = run_job_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def strategy_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.strategy_agent import (
        run_strategy_agent,
    )

    updated = run_strategy_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def recommendation_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.recommendation_agent import (
        run_recommendation_agent,
    )

    updated = run_recommendation_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def validation_node(
    state: CareerPilotState,
) -> CareerPilotState:
    from backend.agents.validation_agent import (
        run_validation_agent,
    )

    updated = run_validation_agent(state)

    return _normalise_workflow_metadata(
        updated
    )


def recovery_node(
    state: CareerPilotState,
) -> CareerPilotState:
    """
    Deterministic recovery controller.

    Recovery:
      1. increments retry_count,
      2. records the recovery attempt,
      3. checks safety limits,
      4. sends the workflow back to Supervisor when safe,
      5. otherwise asks for user input / safely terminates.
    """

    current_retry = int(
        state.get("retry_count", 0) or 0
    )

    next_retry = current_retry + 1

    updated = dict(state)

    updated["retry_count"] = next_retry
    updated["current_agent"] = "recovery"

    errors = list(
        state.get("errors") or []
    )

    recovery_entry = {
        "agent": "recovery",
        "attempt": next_retry,
        "reason": "workflow_validation_failed",
    }

    agent_trace = list(
        state.get("agent_trace") or []
    )

    agent_trace.append(
        recovery_entry
    )

    updated["agent_trace"] = agent_trace

    safety = evaluate_workflow_safety(
        updated
    )

    if safety["safe_to_continue"]:
        updated["needs_user_input"] = False
        updated["user_question"] = ""

        updated["last_decision"] = {
            "agent": "recovery",
            "decision": "retry",
            "reasoning": (
                "Validation failed. Recovery permits another "
                "bounded workflow attempt."
            ),
            "next_step": "supervisor",
        }

        return _normalise_workflow_metadata(
            updated
        )

    updated["needs_user_input"] = True

    updated["user_question"] = (
        "CareerPilot could not safely complete the workflow "
        "after bounded recovery attempts. Please review the "
        "provided input or clarify the request."
    )

    errors.append(
        {
            "code": "RECOVERY_LIMIT_REACHED",
            "message": "; ".join(
                safety["reasons"]
            ),
            "agent": "recovery",
            "recoverable": False,
        }
    )

    updated["errors"] = errors

    updated["last_decision"] = {
        "agent": "recovery",
        "decision": "stop_safely",
        "reasoning": (
            "Safety limits prevent another automatic "
            "recovery attempt."
        ),
        "next_step": "user",
    }

    return _normalise_workflow_metadata(
        updated
    )


def final_node(
    state: CareerPilotState,
) -> CareerPilotState:
    """
    Mark the workflow complete and build the final response envelope.
    """

    updated = dict(state)

    # "final" is a terminal graph state rather than one of the
    # seven specialist AgentName enum members.
    updated["current_agent"] = "final"

    workflow = updated.get("workflow")

    if workflow is not None:
        try:
            workflow.status = WorkflowStatus.COMPLETED
        except Exception:
            pass

        # Final is not a specialist agent, so don't store it as
        # WorkflowMetadata.current_agent.
        try:
            workflow.current_agent = None
        except Exception:
            pass

    updated["workflow_status"] = (
        WorkflowStatus.COMPLETED
    )

    final_response: dict[str, Any] = {
        "status": "COMPLETED",
        "message": (
            "CareerPilot workflow completed successfully."
        ),
        "recommendations": (
            updated.get("recommendations") or []
        ),
        "next_action": (
            updated.get("next_action")
        ),
        "validation": (
            updated.get("final_validation")
        ),
        "agents_used": (
            updated.get("agents_used") or []
        ),
        "delegation_trace": (
            updated.get("delegation_trace") or []
        ),
    }

    updated["final_response"] = final_response

    return _normalise_workflow_metadata(
        updated
    )