from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict

from backend.tools.candidate_tools import analyze_candidate


class CandidateAgent:
    """
    Specialist agent responsible for candidate intelligence.

    Responsibility:
        Shared CareerPilot State
                    ↓
              Candidate Agent
                    ↓
          analyze_candidate tool
                    ↓
          candidate_intelligence
                    ↓
          Shared CareerPilot State

    The agent does not duplicate candidate-intelligence logic.
    Deterministic computation remains inside the tool/service layer.
    """

    name = "candidate"

    def __init__(self) -> None:
        self.tools = {
            "analyze_candidate": analyze_candidate,
        }

    # ============================================================
    # PUBLIC ENTRYPOINT
    # ============================================================

    def run(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the Candidate Agent against shared workflow state.

        Required state:
            candidate_profile

        Produced state:
            candidate_intelligence
            current_agent
            last_decision
            agents_used
            tools_used
            agent_trace
            tool_trace
        """

        if not isinstance(state, dict):
            raise TypeError(
                "CandidateAgent state must be a dictionary."
            )

        candidate_profile = state.get(
            "candidate_profile"
        )

        if candidate_profile is None:
            raise ValueError(
                "Candidate Agent requires "
                "'candidate_profile' in shared state."
            )

        candidate_data = self._serialize(
            candidate_profile
        )

        if not isinstance(
            candidate_data,
            dict,
        ):
            raise TypeError(
                "candidate_profile must serialize to a dictionary."
            )

        result = self.tools[
            "analyze_candidate"
        ].invoke(
            {
                "candidate_data": candidate_data,
            }
        )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "analyze_candidate tool returned "
                "an unexpected result type."
            )

        updated_state = dict(state)

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
            "agent": self.name,
            "decision": "candidate_analysis_complete",
            "reasoning": (
                "Candidate profile was analyzed using "
                "the deterministic candidate-intelligence tool."
            ),
            "next_step": "strategy",
        }

        # --------------------------------------------------------
        # Agent / tool usage tracking
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

        tools_used = list(
            updated_state.get(
                "tools_used",
                [],
            )
            or []
        )

        if "analyze_candidate" not in tools_used:
            tools_used.append(
                "analyze_candidate"
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
                "action": "analyze_candidate",
                "status": "completed",
                "reasoning": (
                    "Candidate Agent invoked the "
                    "candidate intelligence tool."
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
                "tool": "analyze_candidate",
                "agent": self.name,
                "status": "completed",
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
        """
        Alias for run(), useful when agents are invoked uniformly
        by the future supervisor/orchestrator.
        """

        return self.run(state)

    # ============================================================
    # SERIALIZATION
    # ============================================================

    @staticmethod
    def _serialize(
        value: Any,
    ) -> Any:
        """
        Convert domain objects into JSON-compatible structures.
        """

        if value is None:
            return None

        if hasattr(
            value,
            "model_dump",
        ):
            return value.model_dump()

        if is_dataclass(value):
            return asdict(value)

        if isinstance(
            value,
            dict,
        ):
            return {
                str(key): CandidateAgent._serialize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                CandidateAgent._serialize(
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
# MODULE-LEVEL INSTANCE
# ============================================================

candidate_agent = CandidateAgent()


def run_candidate_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience entrypoint for LangGraph node wiring.
    """

    return candidate_agent.run(
        state
    )