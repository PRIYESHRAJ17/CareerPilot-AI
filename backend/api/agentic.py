from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.graph.state import create_initial_state
from backend.graph.workflow import invoke_careerpilot
from backend.schemas.agentic import (
    AgenticHealthResponse,
    AgenticRunRequest,
    AgenticRunResponse,
)


router = APIRouter(
    prefix="/agentic",
    tags=["Agentic CareerPilot"],
)


def _serialize(value: Any) -> Any:
    """
    Convert CareerPilot/Pydantic/LangGraph values into JSON-safe data.
    """

    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

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

    return value


def _build_response(
    state: dict[str, Any],
) -> AgenticRunResponse:
    workflow = state.get("workflow")

    request_id = str(
        state.get("request_id")
        or getattr(workflow, "workflow_id", "")
    )

    thread_id = str(
        state.get("thread_id")
        or getattr(workflow, "thread_id", "")
    )

    status = (
        getattr(workflow, "status", None)
        or state.get("workflow_status")
        or "UNKNOWN"
    )

    current_agent = (
        getattr(workflow, "current_agent", None)
        or state.get("current_agent")
    )

    current_agent = _serialize(current_agent)

    status = _serialize(status)

    return AgenticRunResponse(
        request_id=request_id,

        thread_id=thread_id,

        status=status,

        current_agent=current_agent,

        agents_used=_serialize(
            state.get("agents_used") or []
        ),

        tools_used=_serialize(
            state.get("tools_used") or []
        ),

        delegation_trace=_serialize(
            state.get("delegation_trace") or []
        ),

        candidate_intelligence=_serialize(
            state.get("candidate_intelligence")
        ),

        resume_intelligence=_serialize(
            state.get("resume_intelligence")
        ),

        ats_analysis=_serialize(
            state.get("ats_analysis")
        ),

        job_fit_analysis=_serialize(
            state.get("job_fit_analysis")
        ),

        rewrite_analysis=_serialize(
            state.get("rewrite_analysis")
        ),

        rewrite_candidates=_serialize(
            state.get("rewrite_candidates") or []
        ),

        validated_rewrites=_serialize(
            state.get("validated_rewrites") or []
        ),

        job=_serialize(
            state.get("job")
        ),

        job_requirements=_serialize(
            state.get("job_requirements")
        ),

        skill_gaps=_serialize(
            state.get("skill_gaps") or []
        ),

        career_strategy=_serialize(
            state.get("career_strategy")
        ),

        recommendations=_serialize(
            state.get("recommendations") or []
        ),

        next_action=_serialize(
            state.get("next_action")
        ),

        final_validation=_serialize(
            state.get("final_validation")
        ),

        final_response=_serialize(
            state.get("final_response")
        ),

        retry_count=int(
            state.get("retry_count", 0) or 0
        ),

        errors=_serialize(
            state.get("errors") or []
        ),
    )


@router.get(
    "/health",
    response_model=AgenticHealthResponse,
)
def agentic_health():
    return AgenticHealthResponse(
        status="healthy",
        service="careerpilot-agentic",
        orchestration="langgraph",
        checkpointing="enabled",
    )


@router.post(
    "/run",
    response_model=AgenticRunResponse,
)
def run_agentic_workflow(
    request: AgenticRunRequest,
):
    """
    Run the complete CareerPilot agentic workflow.

    Existing deterministic APIs remain untouched.

    This endpoint creates shared CareerPilot state, seeds the
    supplied user/candidate/job/resume context, executes LangGraph,
    and returns the structured agentic result.
    """

    try:
        request_id = (
            request.request_id
            or f"agentic-{id(request)}"
        )

        thread_id = (
            request.thread_id
            or request_id
        )

        state = create_initial_state(
            request_id=request_id,
            user_goal=request.user_goal,
            thread_id=thread_id,
            conversation_context=(
                request.conversation_context
            ),
        )

        if request.candidate_profile is not None:
            state["candidate_profile"] = (
                request.candidate_profile
            )

        if request.resume_base64:
            state["resume_base64"] = (
                request.resume_base64
            )

        if request.job_description:
            state["job_description"] = (
                request.job_description
            )

        if request.job_query:
            state["job_query"] = (
                request.job_query
            )

        state = invoke_careerpilot(state)

        return _build_response(state)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agentic workflow failed: {exc}",
        ) from exc