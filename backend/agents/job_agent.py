from __future__ import annotations

from typing import Any, Dict

from backend.tools.job_tools import (
    analyze_job_description,
    extract_job_requirements,
    run_job_search_pipeline,
    search_jobs,
)


class JobAgent:
    """
    Specialist agent responsible for opportunity intelligence.

    Responsibilities:

        Shared CareerPilot State
                ↓
            Job Agent
                ↓
        deterministic job tools
                ↓
        job search / requirements /
        opportunity intelligence
                ↓
        Shared CareerPilot State

    The agent does not duplicate Week 1-3 job intelligence logic.
    """

    name = "job"

    def __init__(self) -> None:
        self.tools = {
            "search_jobs": search_jobs,
            "analyze_job_description": analyze_job_description,
            "extract_job_requirements": extract_job_requirements,
            "run_job_search_pipeline": run_job_search_pipeline,
        }

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute Job Agent against shared workflow state.

        Supported paths:

        1. Candidate + search query
           → full job search pipeline

        2. Raw job description
           → deterministic requirement analysis

        3. Canonical job object
           → deterministic requirement extraction
        """

        if not isinstance(state, dict):
            raise TypeError(
                "JobAgent state must be a dictionary."
            )

        updated_state = dict(state)

        candidate_profile = state.get(
            "candidate_profile"
        )

        query = str(
            state.get(
                "job_query",
                "",
            )
            or ""
        ).strip()

        location = str(
            state.get(
                "job_location",
                "",
            )
            or ""
        ).strip()

        job_description = str(
            state.get(
                "job_description",
                "",
            )
            or ""
        ).strip()

        job = state.get(
            "job"
        )

        tools_used: list[str] = []
        action = ""
        decision = ""

        # ========================================================
        # PATH 1 — JOB SEARCH
        # ========================================================

        if candidate_profile is not None and query:
            candidate_data = self._serialize(
                candidate_profile
            )

            if not isinstance(
                candidate_data,
                dict,
            ):
                raise TypeError(
                    "candidate_profile must serialize "
                    "to a dictionary."
                )

            result = self.tools[
                "run_job_search_pipeline"
            ].invoke(
                {
                    "candidate_data": candidate_data,
                    "query": query,
                    "location": location,
                }
            )

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "Job search pipeline returned "
                    "an unexpected result type."
                )

            updated_state[
                "job_search_results"
            ] = result.get(
                "search",
                result,
            )

            updated_state[
                "job_results"
            ] = result.get(
                "search",
                result,
            )

            updated_state[
                "jobs_found"
            ] = result.get(
                "jobs_found",
                result.get(
                    "count",
                    0,
                ),
            )

            tools_used.append(
                "run_job_search_pipeline"
            )

            action = "job_search"
            decision = "job_search_complete"

        # ========================================================
        # PATH 2 — RAW JOB DESCRIPTION
        # ========================================================

        elif job_description:
            result = self.tools[
                "analyze_job_description"
            ].invoke(
                {
                    "job_description": job_description,
                    "job_title": str(
                        state.get(
                            "job_title",
                            "",
                        )
                        or ""
                    ),
                }
            )

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "Job description analysis returned "
                    "an unexpected result type."
                )

            updated_state[
                "job_requirements"
            ] = result.get(
                "requirements",
                result,
            )

            tools_used.append(
                "analyze_job_description"
            )

            action = "analyze_job_description"
            decision = "job_requirements_extracted"

        # ========================================================
        # PATH 3 — CANONICAL JOB
        # ========================================================

        elif job is not None:
            job_data = self._serialize(
                job
            )

            if not isinstance(
                job_data,
                dict,
            ):
                raise TypeError(
                    "job must serialize to a dictionary."
                )

            result = self.tools[
                "extract_job_requirements"
            ].invoke(
                {
                    "job": job_data,
                }
            )

            if not isinstance(
                result,
                dict,
            ):
                raise TypeError(
                    "Job requirements tool returned "
                    "an unexpected result type."
                )

            updated_state[
                "job_requirements"
            ] = result

            tools_used.append(
                "extract_job_requirements"
            )

            action = "extract_job_requirements"
            decision = "job_requirements_extracted"

        # ========================================================
        # NO USABLE INPUT
        # ========================================================

        else:
            raise ValueError(
                "Job Agent requires one of: "
                "'candidate_profile' + 'job_query', "
                "'job_description', or 'job'."
            )

        # ========================================================
        # DERIVE SKILL GAPS WHEN POSSIBLE
        # ========================================================

        updated_state = self._derive_skill_gaps(
            updated_state
        )

        # ========================================================
        # RECORD EXECUTION
        # ========================================================

        return self._record_execution(
            state=updated_state,
            tools_used=tools_used,
            action=action,
            decision=decision,
        )

    # ============================================================
    # SKILL-GAP DERIVATION
    # ============================================================

    @staticmethod
    def _derive_skill_gaps(
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Derive a simple deterministic skill-gap view when both
        candidate skills and job requirements are available.

        This does not replace the existing matching engine.
        """

        updated_state = dict(state)

        candidate_profile = state.get(
            "candidate_profile"
        )

        requirements = state.get(
            "job_requirements"
        )

        if (
            candidate_profile is None
            or not isinstance(
                requirements,
                dict,
            )
        ):
            return updated_state

        candidate_data = JobAgent._serialize(
            candidate_profile
        )

        if not isinstance(
            candidate_data,
            dict,
        ):
            return updated_state

        candidate_skills = {
            str(skill).strip().casefold()
            for skill in (
                candidate_data.get(
                    "skills",
                    [],
                )
                or []
            )
        }

        candidate_skills.update(
            str(skill).strip().casefold()
            for skill in (
                candidate_data.get(
                    "technical_skills",
                    [],
                )
                or []
            )
        )

        required_skills = {
            str(skill).strip().casefold()
            for skill in (
                requirements.get(
                    "required_skills",
                    [],
                )
                or []
            )
        }

        preferred_skills = {
            str(skill).strip().casefold()
            for skill in (
                requirements.get(
                    "preferred_skills",
                    [],
                )
                or []
            )
        }

        missing_required = sorted(
            required_skills
            - candidate_skills
        )

        missing_preferred = sorted(
            preferred_skills
            - candidate_skills
        )

        updated_state[
            "skill_gaps"
        ] = {
            "required": missing_required,
            "preferred": missing_preferred,
            "all": sorted(
                set(
                    missing_required
                    + missing_preferred
                )
            ),
        }

        return updated_state

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

        updated_state[
            "current_agent"
        ] = self.name

        updated_state[
            "last_decision"
        ] = {
            "agent": self.name,
            "decision": decision,
            "reasoning": (
                "Job Agent selected and executed the appropriate "
                "deterministic opportunity-intelligence capability."
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
                    "Job Agent executed the required "
                    "opportunity-intelligence capability."
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
                str(key): JobAgent._serialize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                JobAgent._serialize(
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

job_agent = JobAgent()


def run_job_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return job_agent.run(
        state
    )