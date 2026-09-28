from __future__ import annotations

from dataclasses import (
    asdict,
    is_dataclass,
)
from typing import (
    Any,
    Dict,
)

from backend.tools.candidate_tools import (
    analyze_candidate,
)


class CandidateAgent:
    """
    Specialist agent responsible for
    candidate intelligence.

    Week 6 enhancement:

        Career Twin
              ↓
        Candidate Agent
              ↓
        Candidate Intelligence

    The Career Twin provides historical
    candidate context while the deterministic
    candidate intelligence engine remains
    the computation authority.
    """

    name = "candidate"

    def __init__(self) -> None:

        self.tools = {
            "analyze_candidate":
                analyze_candidate,
        }

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            state,
            dict,
        ):

            raise TypeError(
                "CandidateAgent state "
                "must be a dictionary."
            )

        candidate_profile = (
            state.get(
                "candidate_profile"
            )
        )

        if candidate_profile is None:

            raise ValueError(
                "Candidate Agent requires "
                "'candidate_profile' "
                "in shared state."
            )

        # --------------------------------------------------------
        # ACTIVE CANDIDATE
        # --------------------------------------------------------

        candidate_data = (
            self._serialize(
                candidate_profile
            )
        )

        if not isinstance(
            candidate_data,
            dict,
        ):

            raise TypeError(
                "candidate_profile must "
                "serialize to a dictionary."
            )

        # ========================================================
        # WEEK 6 — CAREER TWIN CONTEXT
        # ========================================================

        career_twin = (
            state.get(
                "career_twin"
            )
            or {}
        )

        twin_profile = (
            career_twin.get(
                "profile"
            )
            or {}
        )

        if twin_profile:

            # ----------------------------------------------------
            # Merge historical skills / evidence
            # ----------------------------------------------------

            for field in (
                "skills",
                "technical_skills",
                "soft_skills",
                "education",
                "certifications",
                "projects",
                "experience",
            ):

                current_values = list(
                    candidate_data.get(
                        field
                    )
                    or []
                )

                historical_values = list(
                    twin_profile.get(
                        field
                    )
                    or []
                )

                candidate_data[
                    field
                ] = list(
                    dict.fromkeys(
                        current_values
                        + historical_values
                    )
                )

            # ----------------------------------------------------
            # Merge career goals
            # ----------------------------------------------------

            career_goal = dict(
                candidate_data.get(
                    "career_goal"
                )
                or {}
            )

            for field in (
                "target_roles",
                "target_industries",
                "target_locations",
            ):

                current_values = list(
                    career_goal.get(
                        field
                    )
                    or []
                )

                historical_values = list(
                    twin_profile.get(
                        field
                    )
                    or []
                )

                career_goal[
                    field
                ] = list(
                    dict.fromkeys(
                        current_values
                        + historical_values
                    )
                )

            # ----------------------------------------------------
            # Preserve persistent preferences
            # ----------------------------------------------------

            if (
                not career_goal.get(
                    "minimum_salary_lpa"
                )
            ):

                career_goal[
                    "minimum_salary_lpa"
                ] = twin_profile.get(
                    "minimum_salary_lpa"
                )

            if (
                not career_goal.get(
                    "target_timeline_months"
                )
            ):

                career_goal[
                    "target_timeline_months"
                ] = twin_profile.get(
                    "timeline_months"
                )

            candidate_data[
                "career_goal"
            ] = career_goal

        # ========================================================
        # DETERMINISTIC CANDIDATE INTELLIGENCE
        # ========================================================

        result = self.tools[
            "analyze_candidate"
        ].invoke(
            {
                "candidate_data":
                    candidate_data,
            }
        )

        if not isinstance(
            result,
            dict,
        ):

            raise TypeError(
                "analyze_candidate tool "
                "returned an unexpected "
                "result type."
            )

        updated_state = dict(
            state
        )

        # --------------------------------------------------------
        # Candidate intelligence
        # --------------------------------------------------------

        updated_state[
            "candidate_intelligence"
        ] = result

        # --------------------------------------------------------
        # Workflow metadata
        # --------------------------------------------------------

        updated_state[
            "current_agent"
        ] = self.name

        updated_state[
            "last_decision"
        ] = {

            "agent":
                self.name,

            "decision":
                "candidate_analysis_complete",

            "reasoning": (
                "Candidate profile and "
                "persistent Career Twin "
                "context were analyzed using "
                "the deterministic "
                "candidate-intelligence tool."
            ),

            "next_step":
                "strategy",
        }

        # ========================================================
        # AGENT USAGE
        # ========================================================

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

        # ========================================================
        # TOOL USAGE
        # ========================================================

        tools_used = list(
            updated_state.get(
                "tools_used",
                [],
            )
            or []
        )

        if (
            "analyze_candidate"
            not in tools_used
        ):

            tools_used.append(
                "analyze_candidate"
            )

        updated_state[
            "tools_used"
        ] = tools_used

        # ========================================================
        # AGENT TRACE
        # ========================================================

        agent_trace = list(
            updated_state.get(
                "agent_trace",
                [],
            )
            or []
        )

        agent_trace.append(
            {

                "agent":
                    self.name,

                "action":
                    "analyze_candidate",

                "status":
                    "completed",

                "reasoning": (
                    "Candidate Agent merged "
                    "persistent Career Twin "
                    "context and invoked the "
                    "deterministic candidate "
                    "intelligence engine."
                ),
            }
        )

        updated_state[
            "agent_trace"
        ] = agent_trace

        # ========================================================
        # TOOL TRACE
        # ========================================================

        tool_trace = list(
            updated_state.get(
                "tool_trace",
                [],
            )
            or []
        )

        tool_trace.append(
            {

                "tool":
                    "analyze_candidate",

                "agent":
                    self.name,

                "status":
                    "completed",
            }
        )

        updated_state[
            "tool_trace"
        ] = tool_trace

        return updated_state

    # ============================================================
    # ALIAS
    # ============================================================

    def execute(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.run(
            state
        )

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

            return value.model_dump(
                mode="json"
            )

        if is_dataclass(
            value
        ):

            return asdict(
                value
            )

        if isinstance(
            value,
            dict,
        ):

            return {
                str(key):
                CandidateAgent._serialize(
                    item
                )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            return [
                CandidateAgent._serialize(
                    item
                )
                for item
                in value
            ]

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            return value

        return str(
            value
        )


# ============================================================
# MODULE-LEVEL INSTANCE
# ============================================================

candidate_agent = (
    CandidateAgent()
)


def run_candidate_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:

    return candidate_agent.run(
        state
    )