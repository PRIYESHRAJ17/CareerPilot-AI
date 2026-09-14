from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# WORKFLOW STATUS
# ============================================================


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================
# AGENT TYPES
# ============================================================


class AgentName(str, Enum):
    SUPERVISOR = "supervisor"
    CANDIDATE = "candidate"
    RESUME = "resume"
    JOB = "job"
    STRATEGY = "strategy"
    RECOMMENDATION = "recommendation"
    VALIDATION = "validation"


# ============================================================
# AGENT DECISION
# ============================================================


class AgentDecision(BaseModel):
    next_agent: Optional[AgentName] = None

    reason: str = ""

    required_information: List[str] = Field(
        default_factory=list
    )

    required_tools: List[str] = Field(
        default_factory=list
    )

    should_continue: bool = True

    workflow_complete: bool = False

    needs_user_input: bool = False

    user_question: Optional[str] = None


# ============================================================
# AGENT TRACE
# ============================================================


class AgentTraceEntry(BaseModel):
    agent: AgentName

    action: str = ""

    status: str = "COMPLETED"

    tools_used: List[str] = Field(
        default_factory=list
    )

    summary: str = ""

    error: Optional[str] = None


# ============================================================
# TOOL TRACE
# ============================================================


class ToolTraceEntry(BaseModel):
    tool_name: str

    agent: AgentName

    status: str = "COMPLETED"

    input_summary: str = ""

    output_summary: str = ""

    error: Optional[str] = None


# ============================================================
# VALIDATION RESULT
# ============================================================


class ValidationResult(BaseModel):
    valid: bool

    status: str = "VALID"

    issues: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )

    checked_by: Optional[AgentName] = None

    evidence_grounded: Optional[bool] = None

    semantic_drift_detected: Optional[bool] = None

    unsupported_claims: List[str] = Field(
        default_factory=list
    )


# ============================================================
# WORKFLOW ERROR
# ============================================================


class WorkflowError(BaseModel):
    stage: str

    message: str

    agent: Optional[AgentName] = None

    recoverable: bool = True


# ============================================================
# RECOMMENDATION
# ============================================================


class CareerRecommendation(BaseModel):
    title: str

    action: str

    priority: str = "MEDIUM"

    reason: str = ""

    evidence: List[str] = Field(
        default_factory=list
    )

    expected_impact: str = ""


# ============================================================
# NEXT ACTION
# ============================================================


class NextAction(BaseModel):
    title: str

    action: str

    reason: str = ""

    priority: str = "HIGH"


# ============================================================
# FINAL CAREERPILOT RESPONSE
# ============================================================


class CareerPilotFinalResponse(BaseModel):
    summary: str = ""

    job_fit_score: Optional[float] = None

    strong_matches: List[str] = Field(
        default_factory=list
    )

    partial_matches: List[str] = Field(
        default_factory=list
    )

    missing_requirements: List[str] = Field(
        default_factory=list
    )

    skill_gaps: List[str] = Field(
        default_factory=list
    )

    career_strategy: List[str] = Field(
        default_factory=list
    )

    recommendations: List[CareerRecommendation] = Field(
        default_factory=list
    )

    next_action: Optional[NextAction] = None

    validated: bool = False


# ============================================================
# WORKFLOW METADATA
# ============================================================


class WorkflowMetadata(BaseModel):
    workflow_id: str

    thread_id: Optional[str] = None

    status: WorkflowStatus = WorkflowStatus.PENDING

    current_agent: Optional[AgentName] = None

    agents_used: List[AgentName] = Field(
        default_factory=list
    )

    tools_used: List[str] = Field(
        default_factory=list
    )

    step_count: int = 0

    errors: List[WorkflowError] = Field(
        default_factory=list
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


# ============================================================
# LEVEL 10 — AGENTIC API
# ============================================================


class AgenticRunRequest(BaseModel):
    """
    Input to the CareerPilot agentic workflow.
    """

    request_id: Optional[str] = None

    thread_id: Optional[str] = None

    user_goal: str = Field(
        min_length=1,
        description="What the candidate wants CareerPilot to accomplish.",
    )

    candidate_profile: Optional[Dict[str, Any]] = None

    resume_base64: Optional[str] = None

    job_description: Optional[str] = None

    job_query: Optional[str] = None

    conversation_context: List[Dict[str, Any]] = Field(
        default_factory=list
    )


class AgenticRunResponse(BaseModel):
    """
    API-safe serialization of the completed/current workflow state.
    """

    request_id: str

    thread_id: str

    status: str

    current_agent: Optional[str] = None

    agents_used: List[str] = Field(
        default_factory=list
    )

    tools_used: List[str] = Field(
        default_factory=list
    )

    delegation_trace: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    candidate_intelligence: Any = None

    resume_intelligence: Any = None

    ats_analysis: Any = None

    job_fit_analysis: Any = None

    rewrite_analysis: Any = None

    rewrite_candidates: List[Any] = Field(
        default_factory=list
    )

    validated_rewrites: List[Any] = Field(
        default_factory=list
    )

    job: Any = None

    job_requirements: Any = None

    skill_gaps: List[Any] = Field(
        default_factory=list
    )

    career_strategy: Any = None

    recommendations: List[Any] = Field(
        default_factory=list
    )

    next_action: Any = None

    final_validation: Any = None

    final_response: Any = None

    retry_count: int = 0

    errors: List[Any] = Field(
        default_factory=list
    )


class AgenticHealthResponse(BaseModel):
    status: str

    service: str

    orchestration: str

    checkpointing: str