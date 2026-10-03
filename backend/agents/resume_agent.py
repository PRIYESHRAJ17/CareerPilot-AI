from __future__ import annotations

from typing import Any, Dict, Optional

from backend.tools.resume_tools import (
    analyze_ats,
    analyze_job_fit,
    analyze_resume,
    generate_resume_rewrites,
    reason_over_resume_rewrites,
    run_resume_intelligence_pipeline,
)


class ResumeAgent:
    """
    Specialist agent responsible for resume intelligence.

    Responsibilities:
        Resume input
            ↓
        Resume Agent
            ↓
        Resume tools
            ↓
        Resume intelligence / ATS / job fit /
        evidence-based rewrites / LLM reasoning
            ↓
        Shared CareerPilot State

    The agent does not duplicate Week 3 resume logic.
    """

    name = "resume"

    def __init__(self) -> None:
        self.tools = {
            "analyze_resume": analyze_resume,
            "analyze_ats": analyze_ats,
            "analyze_job_fit": analyze_job_fit,
            "generate_resume_rewrites": generate_resume_rewrites,
            "reason_over_resume_rewrites": (
                reason_over_resume_rewrites
            ),
            "run_resume_intelligence_pipeline": (
                run_resume_intelligence_pipeline
            ),
        }

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Resume Agent against shared workflow state.

        Preferred input:
            resume_base64

        Optional:
            job_description

        The complete resume intelligence pipeline is used when
        resume_base64 is available.
        """

        if not isinstance(state, dict):
            raise TypeError(
                "ResumeAgent state must be a dictionary."
            )

        resume_base64 = state.get(
            "resume_base64"
        )

        job_description = str(
            state.get(
                "job_description",
                "",
            )
            or ""
        ).strip()

        # --------------------------------------------------------
        # Primary path: complete resume pipeline
        # --------------------------------------------------------

        if resume_base64:
            result = self.tools[
                "run_resume_intelligence_pipeline"
            ].invoke(
                {
                    "resume_base64": resume_base64,
                    "job_description": job_description,
                }
            )

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "Resume intelligence pipeline returned "
                    "an unexpected result type."
                )

            updated_state = self._apply_pipeline_result(
                state=state,
                result=result,
            )

            return self._record_execution(
                state=updated_state,
                tools_used=[
                    "run_resume_intelligence_pipeline"
                ],
                action="run_resume_intelligence_pipeline",
                decision="resume_analysis_complete",
            )

        # --------------------------------------------------------
        # Secondary path: existing structured resume
        # --------------------------------------------------------

        resume = state.get(
            "resume"
        )

        if resume is None:
            raise ValueError(
                "Resume Agent requires either "
                "'resume_base64' or 'resume' in shared state."
            )

        resume_data = self._serialize(
            resume
        )

        if not isinstance(
            resume_data,
            dict,
        ):
            raise TypeError(
                "resume must serialize to a dictionary."
            )

        updated_state = dict(state)

        # Resume intelligence
        intelligence = self.tools[
            "analyze_resume"
        ].invoke(
            {
                "structured_resume": resume_data,
            }
        )

        updated_state[
            "resume_intelligence"
        ] = intelligence

        tools_used = [
            "analyze_resume"
        ]

        # --------------------------------------------------------
        # Job-specific resume intelligence
        # --------------------------------------------------------

        if job_description:
            ats_result = self.tools[
                "analyze_ats"
            ].invoke(
                {
                    "structured_resume": resume_data,
                    "job_description": job_description,
                }
            )

            job_fit_result = self.tools[
                "analyze_job_fit"
            ].invoke(
                {
                    "structured_resume": resume_data,
                    "job_description": job_description,
                }
            )

            rewrite_result = self.tools[
                "generate_resume_rewrites"
            ].invoke(
                {
                    "structured_resume": resume_data,
                }
            )

            updated_state[
                "ats_analysis"
            ] = ats_result

            updated_state[
                "job_fit_analysis"
            ] = job_fit_result

            updated_state[
                "rewrite_analysis"
            ] = rewrite_result

            tools_used.extend(
                [
                    "analyze_ats",
                    "analyze_job_fit",
                    "generate_resume_rewrites",
                ]
            )

            rewrite_suggestions = (
                self._extract_rewrite_suggestions(
                    rewrite_result
                )
            )

            if rewrite_suggestions:
                reasoning_result = self.tools[
                    "reason_over_resume_rewrites"
                ].invoke(
                    {
                        "structured_resume": resume_data,
                        "rewrite_suggestions": (
                            rewrite_suggestions
                        ),
                    }
                )

                updated_state[
                    "llm_reasoning"
                ] = reasoning_result

                tools_used.append(
                    "reason_over_resume_rewrites"
                )

        return self._record_execution(
            state=updated_state,
            tools_used=tools_used,
            action="resume_intelligence",
            decision="resume_analysis_complete",
        )

    # ============================================================
    # PIPELINE RESULT MAPPING
    # ============================================================

    def _apply_pipeline_result(
        self,
        state: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Map pipeline output into the shared CareerPilot state.

        Keys are only written when the corresponding result exists.
        """

        updated_state = dict(state)

        mapping = {
            "resume": "resume",
            "resume_intelligence": (
                "resume_intelligence"
            ),
            "ats_analysis": "ats_analysis",
            "job_fit_analysis": (
                "job_fit_analysis"
            ),
            "rewrite_analysis": (
                "rewrite_analysis"
            ),
            "llm_reasoning": "llm_reasoning",
        }

        for result_key, state_key in mapping.items():
            if result_key in result:
                updated_state[
                    state_key
                ] = result[result_key]

        return updated_state

    # ============================================================
    # REWRITE EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_rewrite_suggestions(
        rewrite_result: Any,
    ) -> list[Dict[str, Any]]:
        """
        Extract rewrite suggestions in the shape expected by
        the LLM resume reasoning tool.
        """

        if not isinstance(
            rewrite_result,
            dict,
        ):
            return []

        suggestions = rewrite_result.get(
            "suggestions",
            [],
        )

        if not isinstance(
            suggestions,
            list,
        ):
            return []

        normalized = []

        for suggestion in suggestions:
            if isinstance(
                suggestion,
                dict,
            ):
                normalized.append(
                    suggestion
                )

        return normalized

    # ============================================================
    # EXECUTION TRACE
    # ============================================================

    def _record_execution(
        self,
        state: Dict[str, Any],
        tools_used: list[str],
        action: str,
        decision: str,
    ) -> Dict[str, Any]:
        updated_state = dict(state)

        # --------------------------------------------------------
        # Current agent
        # --------------------------------------------------------

        updated_state[
            "current_agent"
        ] = self.name

        # --------------------------------------------------------
        # Decision
        # --------------------------------------------------------

        updated_state[
            "last_decision"
        ] = {
            "agent": self.name,
            "decision": decision,
            "reasoning": (
                "Resume Agent completed resume intelligence "
                "using the available deterministic resume tools."
            ),
            "next_step": "supervisor",
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

        existing_tools = list(
            updated_state.get(
                "tools_used",
                [],
            )
            or []
        )

        for tool_name in tools_used:
            if tool_name not in existing_tools:
                existing_tools.append(
                    tool_name
                )

        updated_state[
            "tools_used"
        ] = existing_tools

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
                "action": action,
                "status": "completed",
                "reasoning": (
                    "Resume Agent selected and executed "
                    "resume-intelligence capabilities."
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

        for tool_name in tools_used:
            tool_trace.append(
                {
                    "tool": tool_name,
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
                str(key): ResumeAgent._serialize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                ResumeAgent._serialize(
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

resume_agent = ResumeAgent()


def run_resume_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return resume_agent.run(
        state
    )