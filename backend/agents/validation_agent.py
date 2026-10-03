from __future__ import annotations

from typing import Any, Dict, List

from backend.tools.validation_tools import (
    validate_agent_output,
    validate_resume_rewrites,
)


class ValidationAgent:
    """
    Specialist agent responsible for final workflow validation.

    Responsibilities:

        Shared CareerPilot State
                ↓
          Validation Agent
                ↓
        validation tools
                ↓
        valid / invalid decision
                ↓
        Shared CareerPilot State

    The agent validates:
        - required final workflow fields
        - generated resume rewrites
        - recommendation presence
        - final readiness for downstream completion

    It does not invent or rewrite content itself.
    """

    name = "validation"

    def __init__(self) -> None:
        self.tools = {
            "validate_agent_output": validate_agent_output,
            "validate_resume_rewrites": validate_resume_rewrites,
        }

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate the current shared workflow state.

        Produces:

            validation_results
            final_validation
            current_agent
            last_decision
            traces
        """

        if not isinstance(state, dict):
            raise TypeError(
                "ValidationAgent state must be a dictionary."
            )

        updated_state = dict(state)

        validation_results: List[Dict[str, Any]] = []

        # ========================================================
        # 1. FINAL STATE FIELD VALIDATION
        # ========================================================

        required_fields = self._required_fields(
            state
        )

        output_payload = {
            field_name: state.get(
                field_name
            )
            for field_name in required_fields
        }

        output_validation = self.tools[
            "validate_agent_output"
        ].invoke(
            {
                "payload": output_payload,
                "required_fields": required_fields,
            }
        )

        validation_results.append(
            {
                "check": "required_workflow_fields",
                "status": (
                    "PASS"
                    if output_validation.get(
                        "valid"
                    )
                    else "FAIL"
                ),
                "result": output_validation,
            }
        )

        # ========================================================
        # 2. RESUME REWRITE VALIDATION
        # ========================================================

        rewrite_validation = self._validate_rewrites(
            state
        )

        if rewrite_validation is not None:
            validation_results.append(
                {
                    "check": "resume_rewrites",
                    "status": (
                        "PASS"
                        if rewrite_validation.get(
                            "rejected_count",
                            0,
                        )
                        == 0
                        else "FAIL"
                    ),
                    "result": rewrite_validation,
                }
            )

        # ========================================================
        # 3. RECOMMENDATION VALIDATION
        # ========================================================

        recommendation_validation = (
            self._validate_recommendations(
                state
            )
        )

        validation_results.append(
            {
                "check": "recommendations",
                "status": (
                    "PASS"
                    if recommendation_validation["valid"]
                    else "FAIL"
                ),
                "result": recommendation_validation,
            }
        )

        knowledge_evidence = state.get("career_knowledge_evidence") or []
        knowledge_valid = bool(knowledge_evidence)
        knowledge_check = {
            "valid": knowledge_valid,
            "evidence_count": len(knowledge_evidence),
            "source_count": len({x.get("source_id") for x in knowledge_evidence if isinstance(x, dict) and x.get("source_id")}),
            "issues": [] if knowledge_valid else ["No career knowledge evidence was retrieved."],
        }
        validation_results.append({
            "check": "career_knowledge_evidence",
            "status": "PASS" if knowledge_valid else "FAIL",
            "result": knowledge_check,
        })

        # ========================================================
        # 4. OVERALL DECISION
        # ========================================================

        failed_checks = [
            item
            for item in validation_results
            if item.get("status") == "FAIL"
        ]

        overall_valid = (
            len(failed_checks) == 0
        )

        final_validation = {
            "valid": overall_valid,
            "status": (
                "VALID"
                if overall_valid
                else "INVALID"
            ),
            "checks": validation_results,
            "failed_checks": len(
                failed_checks
            ),
            "message": (
                "Workflow output passed all validation checks."
                if overall_valid
                else (
                    "Workflow output failed one or more "
                    "validation checks and requires recovery."
                )
            ),
        }

        updated_state[
            "validation_results"
        ] = validation_results

        updated_state[
            "final_validation"
        ] = final_validation

        # ========================================================
        # 5. NEXT WORKFLOW STATUS
        # ========================================================

        if overall_valid:
            updated_state[
                "validation_status"
            ] = "VALID"

            updated_state[
                "workflow_validation_passed"
            ] = True
        else:
            updated_state[
                "validation_status"
            ] = "INVALID"

            updated_state[
                "workflow_validation_passed"
            ] = False

        return self._record_execution(
            state=updated_state,
            valid=overall_valid,
        )

    # ============================================================
    # REQUIRED WORKFLOW FIELDS
    # ============================================================

    @staticmethod
    def _required_fields(
        state: Dict[str, Any],
    ) -> List[str]:
        """
        Determine which fields must exist for the workflow to
        produce a useful final result.

        We deliberately require only fields that the current
        specialist architecture can reasonably produce.
        """

        required = [
            "candidate_intelligence",
            "career_strategy",
            "recommendations",
            "next_action",
        ]

        # Resume intelligence is required only when the workflow
        # actually received a resume.
        if (
            state.get("resume") is not None
            or state.get("resume_base64") is not None
        ):
            required.append(
                "resume_intelligence"
            )

        # Job requirements are required only when job-specific
        # analysis was requested.
        if (
            state.get("job_description")
            or state.get("job") is not None
            or state.get("job_query")
        ):
            if (
                state.get("job_requirements")
                is not None
                or state.get("job_search_results")
                is not None
                or state.get("job_results")
                is not None
            ):
                required.append(
                    (
                        "job_requirements"
                        if state.get(
                            "job_requirements"
                        )
                        is not None
                        else "job_results"
                    )
                )

        return required

    # ============================================================
    # RESUME REWRITE VALIDATION
    # ============================================================

    def _validate_rewrites(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """
        Validate LLM-generated resume rewrite candidates when they
        are available.
        """

        resume = state.get(
            "resume"
        )

        llm_reasoning = state.get(
            "llm_reasoning"
        )

        if (
            resume is None
            or not isinstance(
                llm_reasoning,
                dict,
            )
        ):
            return None

        candidates = llm_reasoning.get(
            "candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ) or not candidates:
            return None

        normalized_candidates = []

        for candidate in candidates:
            if not isinstance(
                candidate,
                dict,
            ):
                continue

            normalized_candidates.append(
                {
                    "source_text": candidate.get(
                        "source_text",
                        "",
                    ),
                    "rewritten_text": candidate.get(
                        "rewritten_text",
                        "",
                    ),
                    "section": candidate.get(
                        "section",
                        "",
                    ),
                    "target_requirement": candidate.get(
                        "target_requirement",
                        "",
                    ),
                    "evidence": candidate.get(
                        "evidence",
                        [],
                    ),
                    "confidence": candidate.get(
                        "confidence",
                        0,
                    ),
                }
            )

        if not normalized_candidates:
            return {
                "candidates": [],
                "accepted_count": 0,
                "rejected_count": 0,
                "total_count": 0,
            }

        resume_data = self._serialize(
            resume
        )

        return self.tools[
            "validate_resume_rewrites"
        ].invoke(
            {
                "resume": resume_data,
                "candidates": normalized_candidates,
            }
        )

    # ============================================================
    # RECOMMENDATION VALIDATION
    # ============================================================

    @staticmethod
    def _validate_recommendations(
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        recommendations = state.get(
            "recommendations"
        )

        next_action = state.get(
            "next_action"
        )

        issues: List[str] = []

        if not isinstance(
            recommendations,
            list,
        ) or not recommendations:
            issues.append(
                "No recommendations were produced."
            )

        if not isinstance(
            next_action,
            dict,
        ) or not next_action.get(
            "action"
        ):
            issues.append(
                "No actionable next action was produced."
            )

        for index, recommendation in enumerate(
            recommendations
            if isinstance(
                recommendations,
                list,
            )
            else []
        ):
            if not isinstance(
                recommendation,
                dict,
            ):
                issues.append(
                    f"Recommendation {index + 1} "
                    "has an invalid structure."
                )
                continue

            if not str(
                recommendation.get(
                    "action",
                    "",
                )
                or ""
            ).strip():
                issues.append(
                    f"Recommendation {index + 1} "
                    "has no actionable text."
                )

            if not str(
                recommendation.get(
                    "reason",
                    "",
                )
                or ""
            ).strip():
                issues.append(
                    f"Recommendation {index + 1} "
                    "has no evidence/reason."
                )

        return {
            "valid": not issues,
            "issues": issues,
            "recommendation_count": (
                len(
                    recommendations
                )
                if isinstance(
                    recommendations,
                    list,
                )
                else 0
            ),
        }

    # ============================================================
    # EXECUTION TRACE
    # ============================================================

    def _record_execution(
        self,
        state: Dict[str, Any],
        valid: bool,
    ) -> Dict[str, Any]:
        updated_state = dict(state)

        updated_state[
            "current_agent"
        ] = self.name

        updated_state[
            "last_decision"
        ] = {
            "agent": self.name,
            "decision": (
                "validation_passed"
                if valid
                else "validation_failed"
            ),
            "reasoning": (
                "Validation Agent completed deterministic "
                "workflow safety and completeness checks."
            ),
            "next_step": (
                "final"
                if valid
                else "recovery"
            ),
        }

        # --------------------------------------------------------
        # Agent usage
        # --------------------------------------------------------

        agents_used = list(
            updated_state.get(
                "agents_used",
                [],
            )
            or []
        )

        if self.name not in agents_used:
            agents_used.append(
                self.name
            )

        updated_state[
            "agents_used"
        ] = agents_used

        # --------------------------------------------------------
        # Tool usage
        # --------------------------------------------------------

        tools_used = list(
            updated_state.get(
                "tools_used",
                [],
            )
            or []
        )

        for tool_name in (
            "validate_agent_output",
            "validate_resume_rewrites",
        ):
            if tool_name not in tools_used:
                tools_used.append(
                    tool_name
                )

        updated_state[
            "tools_used"
        ] = tools_used

        # --------------------------------------------------------
        # Agent trace
        # --------------------------------------------------------

        agent_trace = list(
            updated_state.get(
                "agent_trace",
                [],
            )
            or []
        )

        agent_trace.append(
            {
                "agent": self.name,
                "action": "validate_workflow",
                "status": (
                    "completed"
                    if valid
                    else "failed"
                ),
                "reasoning": (
                    "Validated workflow completeness, "
                    "recommendations, and available resume "
                    "rewrite candidates."
                ),
            }
        )

        updated_state[
            "agent_trace"
        ] = agent_trace

        # --------------------------------------------------------
        # Tool trace
        # --------------------------------------------------------

        tool_trace = list(
            updated_state.get(
                "tool_trace",
                [],
            )
            or []
        )

        tool_trace.append(
            {
                "tool": "validate_agent_output",
                "agent": self.name,
                "status": "completed",
            }
        )

        if (
            state.get("resume") is not None
            and isinstance(
                state.get("llm_reasoning"),
                dict,
            )
            and state.get(
                "llm_reasoning",
            ).get(
                "candidates"
            )
        ):
            tool_trace.append(
                {
                    "tool": "validate_resume_rewrites",
                    "agent": self.name,
                    "status": "completed",
                }
            )

        updated_state[
            "tool_trace"
        ] = tool_trace

        return updated_state

    # ============================================================
    # SERIALIZATION
    # ============================================================

    @staticmethod
    def _serialize(
        value: Any,
    ) -> Any:
        if value is None:
            return None

        if hasattr(
            value,
            "model_dump",
        ):
            return value.model_dump()

        if hasattr(
            value,
            "dict",
        ) and callable(
            value.dict
        ):
            return value.dict()

        if hasattr(
            value,
            "__dataclass_fields__",
        ):
            from dataclasses import asdict

            return asdict(value)

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): ValidationAgent._serialize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                ValidationAgent._serialize(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        return str(value)

    # ============================================================
    # UNIFORM EXECUTION ALIAS
    # ============================================================

    def execute(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.run(
            state
        )


# ============================================================
# MODULE-LEVEL INSTANCE
# ============================================================

validation_agent = ValidationAgent()


def run_validation_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return validation_agent.run(
        state
    )