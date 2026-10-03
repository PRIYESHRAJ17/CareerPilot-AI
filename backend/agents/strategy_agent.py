from __future__ import annotations

from typing import Any, Dict

from backend.tools.strategy_tools import (
    create_career_strategy,
    summarize_career_strategy,
    run_career_strategy_pipeline,
)


class StrategyAgent:
    """
    Specialist agent responsible for career strategy.

    Flow:

        candidate_intelligence
                ↓
          Strategy Agent
                ↓
        strategy tools
                ↓
          career_strategy
                ↓
        Shared CareerPilot State

    The agent does not duplicate the deterministic Week 3
    career-strategy engine.
    """

    name = "strategy"

    def __init__(self) -> None:
        self.tools = {
            "create_career_strategy": (
                create_career_strategy
            ),
            "summarize_career_strategy": (
                summarize_career_strategy
            ),
            "run_career_strategy_pipeline": (
                run_career_strategy_pipeline
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
        Execute Strategy Agent against shared workflow state.

        Required:
            candidate_intelligence

        Produced:
            career_strategy
            strategy_summary
            strategy_actions
            traces
        """

        if not isinstance(state, dict):
            raise TypeError(
                "StrategyAgent state must be a dictionary."
            )

        candidate_intelligence = state.get(
            "candidate_intelligence"
        )

        if candidate_intelligence is None:
            raise ValueError(
                "Strategy Agent requires "
                "'candidate_intelligence' in shared state."
            )

        intelligence_data = self._serialize(
            candidate_intelligence
        )

        if not isinstance(
            intelligence_data,
            dict,
        ):
            raise TypeError(
                "candidate_intelligence must serialize "
                "to a dictionary."
            )

        # --------------------------------------------------------
        # Run complete deterministic strategy capability
        # --------------------------------------------------------

        result = self.tools[
            "run_career_strategy_pipeline"
        ].invoke(
            {
                "candidate_intelligence": (
                    intelligence_data
                )
            }
        )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "Career strategy pipeline returned "
                "an unexpected result type."
            )

        updated_state = dict(state)

        # --------------------------------------------------------
        # Strategy state
        # --------------------------------------------------------

        strategy = result.get(
            "strategy"
        )

        summary = result.get(
            "summary"
        )

        if strategy is not None:
            updated_state[
                "career_strategy"
            ] = strategy

        if summary is not None:
            updated_state[
                "strategy_summary"
            ] = summary

        # --------------------------------------------------------
        # IMPORTANT:
        # Keep strategy's raw recommended actions separate from
        # the structured recommendations produced by the
        # Recommendation Agent.
        # --------------------------------------------------------

        if isinstance(
            strategy,
            dict,
        ):
            updated_state[
                "strategy_actions"
            ] = list(
                strategy.get(
                    "recommended_actions",
                    [],
                )
                or []
            )

        return self._record_execution(
            state=updated_state,
            tools_used=[
                "run_career_strategy_pipeline"
            ],
            action="run_career_strategy_pipeline",
            decision="career_strategy_complete",
        )

    # ============================================================
    # OPTIONAL RE-SUMMARIZATION
    # ============================================================

    def summarize(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Rebuild the presentation-ready strategy summary from
        existing shared-state strategy data.
        """

        if not isinstance(state, dict):
            raise TypeError(
                "StrategyAgent state must be a dictionary."
            )

        strategy = state.get(
            "career_strategy"
        )

        if strategy is None:
            raise ValueError(
                "No career_strategy exists in shared state."
            )

        strategy_data = self._serialize(
            strategy
        )

        result = self.tools[
            "summarize_career_strategy"
        ].invoke(
            {
                "strategy": strategy_data,
            }
        )

        updated_state = dict(state)

        updated_state[
            "strategy_summary"
        ] = result

        return self._record_execution(
            state=updated_state,
            tools_used=[
                "summarize_career_strategy"
            ],
            action="summarize_career_strategy",
            decision="career_strategy_summary_complete",
        )

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
                "Strategy Agent generated career strategy "
                "from candidate intelligence using the "
                "deterministic strategy tools."
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
                    "Strategy Agent invoked the career "
                    "strategy capability."
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
                str(key): StrategyAgent._serialize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (list, tuple, set),
        ):
            return [
                StrategyAgent._serialize(
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

strategy_agent = StrategyAgent()


def run_strategy_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    return strategy_agent.run(
        state
    )