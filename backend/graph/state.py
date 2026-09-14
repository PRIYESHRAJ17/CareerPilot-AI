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


class CareerPilotState(TypedDict, total=False):
    # ============================================================
    # REQUEST / WORKFLOW IDENTITY
    # ============================================================

    request_id: str
    thread_id: str

    user_goal: str

    conversation_context: list[dict[str, Any]]

    messages: list[dict[str, Any]]

    # ============================================================
    # WORKFLOW
    # ============================================================

    workflow: WorkflowMetadata

    workflow_status: str

    current_agent: str

    step_count: int

    retry_count: int

    # ============================================================
    # SUPERVISOR / ROUTING
    # ============================================================

    supervisor_decision: AgentDecision

    last_decision: AgentDecision

    # ============================================================
    # CANDIDATE
    # ============================================================

    candidate_profile: dict[str, Any]

    candidate_intelligence: Any

    # ============================================================
    # RESUME INPUTS
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
    # JOB INPUTS
    # ============================================================

    job_description: str

    job_query: str

    job: Any

    job_requirements: Any

    skill_gaps: list[Any]

    # ============================================================
    # CAREER STRATEGY
    # ============================================================

    career_strategy: Any

    recommendations: list[Any]

    next_action: Any

    # ============================================================
    # FINAL VALIDATION / RESPONSE
    # ============================================================

    final_validation: ValidationResult | dict[str, Any] | None

    final_response: CareerPilotFinalResponse | dict[str, Any] | None

    # ============================================================
    # OBSERVABILITY
    # ============================================================

    agents_used: list[str]

    tools_used: list[str]

    agent_trace: list[AgentTraceEntry]

    tool_trace: list[ToolTraceEntry]

    delegation_trace: list[dict[str, Any]]

    # ============================================================
    # USER INTERACTION
    # ============================================================

    needs_user_input: bool

    user_question: str

    # ============================================================
    # ERRORS
    # ============================================================

    errors: list[WorkflowError]


def create_initial_state(
    *,
    request_id: str,
    user_goal: str,
    thread_id: str | None = None,
    conversation_context: list[dict[str, Any]] | None = None,
) -> CareerPilotState:
    """
    Create the initial shared state for a CareerPilot workflow.
    """

    resolved_thread_id = (
        thread_id
        or request_id
    )

    workflow = WorkflowMetadata(
        workflow_id=request_id,
        thread_id=resolved_thread_id,
    )

    return CareerPilotState(
        # --------------------------------------------------------
        # Identity
        # --------------------------------------------------------

        request_id=request_id,

        thread_id=resolved_thread_id,

        user_goal=user_goal,

        conversation_context=(
            conversation_context
            or []
        ),

        messages=[],

        # --------------------------------------------------------
        # Workflow
        # --------------------------------------------------------

        workflow=workflow,

        workflow_status="PENDING",

        current_agent="supervisor",

        step_count=0,

        retry_count=0,

        # --------------------------------------------------------
        # Supervisor
        # --------------------------------------------------------

        supervisor_decision=None,

        last_decision=None,

        # --------------------------------------------------------
        # Candidate
        # --------------------------------------------------------

        candidate_profile={},

        # --------------------------------------------------------
        # Observability
        # --------------------------------------------------------

        agents_used=[],

        tools_used=[],

        agent_trace=[],

        tool_trace=[],

        delegation_trace=[],

        # --------------------------------------------------------
        # User interaction
        # --------------------------------------------------------

        needs_user_input=False,

        user_question="",

        # --------------------------------------------------------
        # Errors
        # --------------------------------------------------------

        errors=[],

        # --------------------------------------------------------
        # Workflow collections
        # --------------------------------------------------------

        recommendations=[],

        skill_gaps=[],

        rewrite_candidates=[],

        validated_rewrites=[],

        validation_results=[],
    )