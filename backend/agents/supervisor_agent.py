from __future__ import annotations

from typing import Any, Dict, List


class SupervisorAgent:
    """
    Supervisor / orchestrator decision layer.

    The Supervisor does NOT directly execute specialist agents.

    It examines shared CareerPilot state and decides:

        - which specialist should run next
        - whether validation should run
        - whether recovery is required
        - whether the workflow can finish

    LangGraph will later use this decision to actually route
    execution between specialist nodes.
    """

    name = "supervisor"

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze shared state and produce the next routing decision.
        """

        if not isinstance(
            state,
            dict,
        ):
            raise TypeError(
                "SupervisorAgent state must be a dictionary."
            )

        decision = self.decide(
            state
        )

        updated_state = dict(state)

        # --------------------------------------------------------
        # Supervisor state
        # --------------------------------------------------------

        updated_state[
            "current_agent"
        ] = self.name

        updated_state[
            "last_decision"
        ] = {
            "agent": self.name,
            "decision": decision["decision"],
            "reasoning": decision["reasoning"],
            "next_step": decision["next_agent"],
        }

        updated_state[
            "supervisor_decision"
        ] = decision

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
                "action": "route_workflow",
                "status": "completed",
                "reasoning": decision[
                    "reasoning"
                ],
                "decision": decision[
                    "decision"
                ],
                "next_agent": decision[
                    "next_agent"
                ],
            }
        )

        updated_state[
            "agent_trace"
        ] = agent_trace

        # --------------------------------------------------------
        # Step count
        # --------------------------------------------------------

        workflow = updated_state.get(
            "workflow"
        )

        if workflow is not None:
            self._increment_workflow_step(
                updated_state
            )
        elif "step_count" in updated_state:
            updated_state[
                "step_count"
            ] = int(
                updated_state.get(
                    "step_count",
                    0,
                )
                or 0
            ) + 1
        else:
            updated_state[
                "step_count"
            ] = 1

        return updated_state

    # ============================================================
    # DECISION ENGINE
    # ============================================================

    def decide(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Determine the next required workflow step.

        Routing priority:

        1. invalid validation → recovery
        2. explicit user input needed → user
        3. missing candidate intelligence → candidate
        4. missing resume intelligence → resume
        5. missing job intelligence → job
        6. missing career strategy → strategy
        7. missing recommendations → recommendation
        8. missing validation → validation
        9. valid workflow → final
        """

        # ========================================================
        # 1. VALIDATION FAILURE
        # ========================================================

        final_validation = state.get(
            "final_validation"
        )

        if isinstance(
            final_validation,
            dict,
        ):
            validation_status = str(
                final_validation.get(
                    "status",
                    "",
                )
                or ""
            ).upper()

            if validation_status == "INVALID":
                return self._decision(
                    decision="recover",
                    next_agent="recovery",
                    reasoning=(
                        "The previous validation pass failed. "
                        "The workflow requires recovery before "
                        "another finalization attempt."
                    ),
                    priority=1,
                )

            if validation_status == "VALID":
                return self._decision(
                    decision="finish",
                    next_agent="final",
                    reasoning=(
                        "Validation passed and the workflow "
                        "contains an acceptable final result."
                    ),
                    priority=9,
                )

        # ========================================================
        # 2. USER INPUT REQUIRED
        # ========================================================

        if bool(
            state.get(
                "needs_user_input",
                False,
            )
        ):
            return self._decision(
                decision="request_user_input",
                next_agent="user",
                reasoning=(
                    "The current workflow state explicitly "
                    "requires additional user information."
                ),
                priority=2,
            )

        # ========================================================
        # 3. CANDIDATE INTELLIGENCE
        # ========================================================

        if not self._has_meaningful_value(
            state.get(
                "candidate_intelligence"
            )
        ):
            if self._has_candidate_profile(
                state
            ):
                return self._decision(
                    decision="delegate_candidate",
                    next_agent="candidate",
                    reasoning=(
                        "Candidate profile information is available "
                        "but candidate intelligence has not yet been "
                        "produced."
                    ),
                    priority=3,
                )

        # ========================================================
        # 4. RESUME INTELLIGENCE
        # ========================================================

        has_resume_input = (
            self._has_meaningful_value(
                state.get(
                    "resume"
                )
            )
            or self._has_meaningful_value(
                state.get(
                    "resume_base64"
                )
            )
        )

        if (
            has_resume_input
            and not self._has_meaningful_value(
                state.get(
                    "resume_intelligence"
                )
            )
        ):
            return self._decision(
                decision="delegate_resume",
                next_agent="resume",
                reasoning=(
                    "Resume input is available but resume "
                    "intelligence has not yet been produced."
                ),
                priority=4,
            )

        # ========================================================
        # 5. JOB INTELLIGENCE
        # ========================================================

        has_job_request = (
            self._has_meaningful_value(
                state.get(
                    "job_query"
                )
            )
            or self._has_meaningful_value(
                state.get(
                    "job_description"
                )
            )
            or self._has_meaningful_value(
                state.get(
                    "job"
                )
            )
        )

        has_job_output = (
            self._has_meaningful_value(
                state.get(
                    "job_requirements"
                )
            )
            or self._has_meaningful_value(
                state.get(
                    "job_results"
                )
            )
            or self._has_meaningful_value(
                state.get(
                    "job_search_results"
                )
            )
        )

        if (
            has_job_request
            and not has_job_output
        ):
            return self._decision(
                decision="delegate_job",
                next_agent="job",
                reasoning=(
                    "A job request is present but job/opportunity "
                    "intelligence has not yet been generated."
                ),
                priority=5,
            )

        # ========================================================
        # 6. CAREER STRATEGY
        # ========================================================

        if (
            self._has_meaningful_value(
                state.get(
                    "candidate_intelligence"
                )
            )
            and not self._has_meaningful_value(
                state.get(
                    "career_strategy"
                )
            )
        ):
            return self._decision(
                decision="delegate_strategy",
                next_agent="strategy",
                reasoning=(
                    "Candidate intelligence is available but "
                    "a career strategy has not yet been generated."
                ),
                priority=6,
            )

        # ========================================================
        # 7. RECOMMENDATIONS
        # ========================================================

        recommendations = state.get(
            "recommendations"
        )

        if not self._has_nonempty_list(
            recommendations
        ):
            has_strategy_or_intelligence = (
                self._has_meaningful_value(
                    state.get(
                        "career_strategy"
                    )
                )
                or self._has_meaningful_value(
                    state.get(
                        "candidate_intelligence"
                    )
                )
                or self._has_meaningful_value(
                    state.get(
                        "job_requirements"
                    )
                )
                or self._has_meaningful_value(
                    state.get(
                        "resume_intelligence"
                    )
                )
            )

            if has_strategy_or_intelligence:
                return self._decision(
                    decision="delegate_recommendation",
                    next_agent="recommendation",
                    reasoning=(
                        "Sufficient candidate intelligence exists, "
                        "but personalized recommendations have not "
                        "yet been synthesized."
                    ),
                    priority=7,
                )

        # ========================================================
        # 8. VALIDATION
        # ========================================================

        if not self._has_meaningful_value(
            state.get(
                "final_validation"
            )
        ):
            return self._decision(
                decision="delegate_validation",
                next_agent="validation",
                reasoning=(
                    "The required specialist outputs are present. "
                    "The workflow must pass through the validation "
                    "gate before finalization."
                ),
                priority=8,
            )

        # ========================================================
        # 9. FALLBACK
        # ========================================================

        return self._decision(
            decision="finish",
            next_agent="final",
            reasoning=(
                "No further specialist work is required "
                "for the current shared workflow state."
            ),
            priority=9,
        )

    # ============================================================
    # DECISION BUILDER
    # ============================================================

    @staticmethod
    def _decision(
        decision: str,
        next_agent: str,
        reasoning: str,
        priority: int,
    ) -> Dict[str, Any]:
        return {
            "decision": decision,
            "next_agent": next_agent,
            "reasoning": reasoning,
            "priority": priority,
        }

    # ============================================================
    # STATE HELPERS
    # ============================================================

    @staticmethod
    def _has_candidate_profile(
        state: Dict[str, Any],
    ) -> bool:
        return (
            SupervisorAgent._has_meaningful_value(
                state.get(
                    "candidate_profile"
                )
            )
        )

    @staticmethod
    def _has_meaningful_value(
        value: Any,
    ) -> bool:
        if value is None:
            return False

        if isinstance(
            value,
            str,
        ):
            return bool(
                value.strip()
            )

        if isinstance(
            value,
            (list, tuple, set, dict),
        ):
            return bool(value)

        return True

    @staticmethod
    def _has_nonempty_list(
        value: Any,
    ) -> bool:
        return (
            isinstance(
                value,
                list,
            )
            and len(value) > 0
        )

    # ============================================================
    # WORKFLOW METADATA SUPPORT
    # ============================================================

    @staticmethod
    def _increment_workflow_step(
        state: Dict[str, Any],
    ) -> None:
        """
        Safely update WorkflowMetadata when the shared state uses
        the Level 2 dataclass structure.
        """

        workflow = state.get(
            "workflow"
        )

        if workflow is None:
            return

        if hasattr(
            workflow,
            "step_count",
        ):
            workflow.step_count = int(
                workflow.step_count
            ) + 1

        if hasattr(
            workflow,
            "current_agent",
        ):
            workflow.current_agent = (
                "supervisor"
            )

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

supervisor_agent = SupervisorAgent()


def run_supervisor_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return supervisor_agent.run(
        state
    )