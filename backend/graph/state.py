from __future__ import annotations

from typing import Any, TypedDict

from backend.schemas.agentic import (
    AgentDecision,
    AgentTraceEntry,
    CareerPilotFinalResponse,
    ToolTraceEntry,
    ValidationResult,
    WorkflowError,
    WorkflowMetadata,
)


class CareerPilotState(
    TypedDict,
    total=False,
):
    # ============================================================
    # REQUEST / WORKFLOW
    # ============================================================

    request_id: str
    thread_id: str
    user_goal: str

    conversation_context: list[
        dict[str, Any]
    ]

    messages: list[
        dict[str, Any]
    ]

    workflow: WorkflowMetadata
    workflow_status: str
    current_agent: str
    step_count: int
    retry_count: int

    # ============================================================
    # SUPERVISOR
    # ============================================================

    supervisor_decision: AgentDecision
    last_decision: AgentDecision

    # ============================================================
    # CANDIDATE
    # ============================================================

    candidate_profile: dict[
        str,
        Any,
    ]

    candidate_intelligence: Any

    # ============================================================
    # CAREER TWIN
    # ============================================================

    career_twin: Any

    career_memory_events: list[Any]

    market_intelligence: Any

    career_gap_intelligence: Any

    career_timeline: Any

    career_twin_sync: Any

    # ============================================================
    # RESUME
    # ============================================================

    resume_base64: str
    resume: Any
    resume_evidence: Any
    resume_intelligence: Any
    ats_analysis: Any
    job_fit_analysis: Any
    rewrite_analysis: Any
    rewrite_candidates: list[Any]
    validated_rewrites: list[Any]
    validation_results: list[Any]

    # ============================================================
    # JOB
    # ============================================================

    job_description: str
    job_query: str
    job: Any
    job_requirements: Any
    job_search_results: Any
    job_results: Any
    skill_gaps: list[Any]

    # ============================================================
    # STRATEGY / RECOMMENDATIONS
    # ============================================================

    career_strategy: Any
    recommendations: list[Any]
    next_action: Any

    # ============================================================
    # VALIDATION / RESPONSE
    # ============================================================

    final_validation: (
        ValidationResult
        | dict[str, Any]
        | None
    )

    final_response: (
        CareerPilotFinalResponse
        | dict[str, Any]
        | None
    )

    # ============================================================
    # OBSERVABILITY
    # ============================================================

    agents_used: list[str]
    tools_used: list[str]

    agent_trace: list[
        AgentTraceEntry
    ]

    tool_trace: list[
        ToolTraceEntry
    ]

    career_knowledge_evidence: list[
        dict[str, Any]
    ]

    delegation_trace: list[
        dict[str, Any]
    ]

    # ============================================================
    # USER
    # ============================================================

    needs_user_input: bool
    user_question: str

    # ============================================================
    # ERRORS
    # ============================================================

    errors: list[
        WorkflowError
    ]


def create_initial_state(
    *,
    request_id: str,
    user_goal: str,
    thread_id: str | None = None,
    conversation_context: (
        list[dict[str, Any]]
        | None
    ) = None,
) -> CareerPilotState:

    resolved_thread_id = (
        thread_id
        or request_id
    )

    workflow = WorkflowMetadata(
        workflow_id=request_id,
        thread_id=resolved_thread_id,
    )

    return CareerPilotState(
        request_id=request_id,
        thread_id=resolved_thread_id,
        user_goal=user_goal,
        conversation_context=(
            conversation_context
            or []
        ),
        messages=[],
        workflow=workflow,
        workflow_status="PENDING",
        current_agent="supervisor",
        step_count=0,
        retry_count=0,
        supervisor_decision=None,
        last_decision=None,
        candidate_profile={},
        career_twin={},
        career_memory_events=[],
        market_intelligence={},
        career_gap_intelligence={},
        career_timeline={},
        career_twin_sync={},
        agents_used=[],
        tools_used=[],
        agent_trace=[],
        tool_trace=[],
        career_knowledge_evidence=[],
        delegation_trace=[],
        needs_user_input=False,
        user_question="",
        errors=[],
        recommendations=[],
        skill_gaps=[],
        rewrite_candidates=[],
        validated_rewrites=[],
        validation_results=[],
    )