from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.api.session import get_candidate_id
from backend.graph.state import create_initial_state
from backend.graph.workflow import invoke_careerpilot

from backend.services.career_twin import (
    get_or_create,
    merge_twin_into_candidate_profile,
    update_from_candidate,
)

from backend.services.workspace_store import append_event, upsert_record

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
    Convert CareerPilot/Pydantic/LangGraph values
    into JSON-safe data.
    """

    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if hasattr(value, "model_dump"):
        return value.model_dump(
            mode="json"
        )

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            _serialize(item)
            for item in value
        ]

    return value


def _build_response(
    state: dict[str, Any],
) -> AgenticRunResponse:

    workflow = state.get(
        "workflow"
    )

    request_id = str(
        state.get(
            "request_id"
        )
        or getattr(
            workflow,
            "workflow_id",
            "",
        )
    )

    thread_id = str(
        state.get(
            "thread_id"
        )
        or getattr(
            workflow,
            "thread_id",
            "",
        )
    )

    status = (
        getattr(
            workflow,
            "status",
            None,
        )
        or state.get(
            "workflow_status"
        )
        or "UNKNOWN"
    )

    current_agent = (
        getattr(
            workflow,
            "current_agent",
            None,
        )
        or state.get(
            "current_agent"
        )
    )

    return AgenticRunResponse(
        request_id=request_id,

        thread_id=thread_id,

        status=_serialize(
            status
        ),

        current_agent=_serialize(
            current_agent
        ),

        agents_used=_serialize(
            state.get(
                "agents_used"
            )
            or []
        ),

        tools_used=_serialize(
            state.get(
                "tools_used"
            )
            or []
        ),

        career_knowledge_evidence=_serialize(
            state.get(
                "career_knowledge_evidence"
            )
            or []
        ),

        # ----------------------------------------------------
        # WEEK 6 — CAREER TWIN
        # ----------------------------------------------------

        career_twin=_serialize(
            state.get(
                "career_twin"
            )
            or {}
        ),

        career_memory_events=_serialize(
            state.get(
                "career_memory_events"
            )
            or []
        ),

        # ----------------------------------------------------
        # EXISTING INTELLIGENCE
        # ----------------------------------------------------

        delegation_trace=_serialize(
            state.get(
                "delegation_trace"
            )
            or []
        ),

        candidate_intelligence=_serialize(
            state.get(
                "candidate_intelligence"
            )
        ),

        resume_intelligence=_serialize(
            state.get(
                "resume_intelligence"
            )
        ),

        ats_analysis=_serialize(
            state.get(
                "ats_analysis"
            )
        ),

        job_fit_analysis=_serialize(
            state.get(
                "job_fit_analysis"
            )
        ),

        rewrite_analysis=_serialize(
            state.get(
                "rewrite_analysis"
            )
        ),

        rewrite_candidates=_serialize(
            state.get(
                "rewrite_candidates"
            )
            or []
        ),

        validated_rewrites=_serialize(
            state.get(
                "validated_rewrites"
            )
            or []
        ),

        job=_serialize(
            state.get(
                "job"
            )
        ),

        job_requirements=_serialize(
            state.get(
                "job_requirements"
            )
        ),

        skill_gaps=_serialize(
            state.get(
                "skill_gaps"
            )
            or []
        ),

        career_strategy=_serialize(
            state.get(
                "career_strategy"
            )
        ),

        recommendations=_serialize(
            state.get(
                "recommendations"
            )
            or []
        ),

        next_action=_serialize(
            state.get(
                "next_action"
            )
        ),

        final_validation=_serialize(
            state.get(
                "final_validation"
            )
        ),

        final_response=_serialize(
            state.get(
                "final_response"
            )
        ),

        retry_count=int(
            state.get(
                "retry_count",
                0,
            )
            or 0
        ),

        errors=_serialize(
            state.get(
                "errors"
            )
            or []
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
    http_request: Request,
):

    """
    Run the complete CareerPilot
    agentic workflow.

    Week 6 enhancement:

        Request
           ↓
        Career Twin hydration
           ↓
        Agentic workflow
           ↓
        Career Twin persistence
           ↓
        Response
    """

    try:

        request_id = (
            request.request_id
            or str(__import__("uuid").uuid4())
        )

        thread_id = request_id

        # ----------------------------------------------------
        # CREATE SHARED STATE
        # ----------------------------------------------------

        state = create_initial_state(
            request_id=request_id,
            user_goal=request.user_goal,
            thread_id=thread_id,
            conversation_context=(
                request.conversation_context
            ),
        )

        # ----------------------------------------------------
        # CANDIDATE PROFILE
        # ----------------------------------------------------

        if (
            request.candidate_profile
            is not None
        ):

            state[
                "candidate_profile"
            ] = (
                request.candidate_profile
            )

        else:

            # Bare career question still receives
            # a valid minimal candidate context.

            state[
                "candidate_profile"
            ] = {

                "candidate_id":
                    get_candidate_id(
                        http_request
                    ),

                "name":
                    "CareerPilot User",

                "headline":
                    request.user_goal,

                "skills": [],

                "technical_skills": [],

                "soft_skills": [],

                "years_of_experience":
                    0.0,

                "education": [],

                "certifications": [],

                "projects": [],

                "preferred_locations": [],

                "preferred_work_modes": [],

                "metadata": {},

                "career_goal": {

                    "target_roles": [
                        request.user_goal
                    ],

                    "target_industries": [],

                    "target_locations": [],

                    "minimum_salary_lpa":
                        None,

                    "preferred_work_modes": [],

                    "target_timeline_months":
                        None,
                },
            }

        # ====================================================
        # WEEK 6 — CAREER TWIN HYDRATION
        # ====================================================

        candidate_id = get_candidate_id(
            http_request
        )

        career_twin = get_or_create(
            candidate_id
        )

        state[
            "career_twin"
        ] = career_twin.model_dump(
            mode="json"
        )

        # Historical Career Twin state is merged into
        # the active candidate context before agents run.

        state[
            "candidate_profile"
        ] = (
            merge_twin_into_candidate_profile(
                state[
                    "candidate_profile"
                ],
                career_twin,
            )
        )

        # ----------------------------------------------------
        # OPTIONAL INPUTS
        # ----------------------------------------------------

        if request.resume_base64:

            state[
                "resume_base64"
            ] = (
                request.resume_base64
            )

        if request.job_description:

            state[
                "job_description"
            ] = (
                request.job_description
            )

        if request.job_query:

            state[
                "job_query"
            ] = (
                request.job_query
            )

        # ====================================================
        # RUN LANGGRAPH
        # ====================================================

        state = invoke_careerpilot(
            state
        )

        # ====================================================
        # WEEK 6 — PERSIST CAREER TWIN
        # ====================================================

        updated_twin = (
            update_from_candidate(
                candidate=(
                    state.get(
                        "candidate_profile"
                    )
                    or {}
                ),

                candidate_intelligence=(
                    state.get(
                        "candidate_intelligence"
                    )
                    or {}
                ),

                skill_gaps=(
                    state.get(
                        "skill_gaps"
                    )
                    or []
                ),

                recommendations=(
                    state.get(
                        "recommendations"
                    )
                    or []
                ),
            )
        )

        state[
            "career_twin"
        ] = updated_twin.model_dump(
            mode="json"
        )

        state[
            "career_memory_events"
        ] = [
            event.model_dump(
                mode="json"
            )
            for event in (
                updated_twin.memory[
                    -10:
                ]
            )
        ]

        response = _build_response(state)
        try:
            upsert_record(
                candidate_id,
                "agent-runs",
                {
                    "id": request_id,
                    "request_id": request_id,
                    "thread_id": thread_id,
                    "status": str(response.status),
                    "goal": request.user_goal,
                    "agents_used": response.agents_used,
                    "tools_used": response.tools_used,
                    "recommendations": [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in response.recommendations],
                    "next_action": response.next_action.model_dump(mode="json") if response.next_action else None,
                    "final_validation": response.final_validation.model_dump(mode="json") if response.final_validation else None,
                    "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                },
                record_id=request_id,
            )
            append_event(candidate_id, "agentic.completed", "Agentic CareerPilot workflow completed and persisted.", {"request_id": request_id, "status": str(response.status)})
        except Exception:
            # Persistence is a durability enhancement and must not make a completed workflow fail.
            pass
        return response

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Agentic workflow failed: "
                f"{exc}"
            ),
        ) from exc
