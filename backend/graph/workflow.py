from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.graph.checkpoints import (
    careerpilot_checkpointer,
    get_thread_id,
    workflow_config,
)
from backend.graph.delegation import delegate_from_supervisor
from backend.graph.nodes import (
    candidate_node,
    final_node,
    job_node,
    recommendation_node,
    recovery_node,
    resume_node,
    strategy_node,
    supervisor_node,
    validation_node,
)
from backend.graph.routing import (
    route_after_recovery,
    route_after_specialist,
    route_after_supervisor,
    route_after_validation,
)
from backend.graph.state import CareerPilotState


def delegation_node(state: CareerPilotState) -> CareerPilotState:
    """
    Execute the specialist selected by the Supervisor.
    """
    return delegate_from_supervisor(state)


def compile_careerpilot_graph():
    graph = StateGraph(CareerPilotState)

    # Orchestration
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("delegation", delegation_node)

    # Specialists
    graph.add_node("candidate", candidate_node)
    graph.add_node("resume", resume_node)
    graph.add_node("job", job_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("validation", validation_node)

    # Recovery / final
    graph.add_node("recovery", recovery_node)
    graph.add_node("final", final_node)

    # Entry
    graph.add_edge(START, "supervisor")

    # Supervisor routing
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "candidate": "delegation",
            "resume": "delegation",
            "job": "delegation",
            "strategy": "delegation",
            "recommendation": "delegation",
            "validation": "delegation",
            "recovery": "recovery",
            "final": "final",
            "user": END,
            "end": END,
        },
    )

    # Delegation returns control to Supervisor.
    graph.add_conditional_edges(
        "delegation",
        route_after_specialist,
        {
            "supervisor": "supervisor",
            "candidate": "supervisor",
            "resume": "supervisor",
            "job": "supervisor",
            "strategy": "supervisor",
            "recommendation": "supervisor",
            "validation": "supervisor",
            "recovery": "recovery",
            "final": "final",
            "user": END,
            "end": END,
        },
    )

    # Direct specialist paths
    for node_name in (
        "candidate",
        "resume",
        "job",
        "strategy",
        "recommendation",
    ):
        graph.add_conditional_edges(
            node_name,
            route_after_specialist,
            {
                "supervisor": "supervisor",
                "recovery": "recovery",
                "final": "final",
                "user": END,
                "end": END,
            },
        )

    # Validation
    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "final": "final",
            "recovery": "recovery",
            "supervisor": "supervisor",
            "user": END,
            "end": END,
        },
    )

    # Recovery
    graph.add_conditional_edges(
        "recovery",
        route_after_recovery,
        {
            "supervisor": "supervisor",
            "user": END,
            "end": END,
        },
    )

    # Terminal
    graph.add_edge("final", END)

    return graph.compile(
        checkpointer=careerpilot_checkpointer,
    )


careerpilot_graph = compile_careerpilot_graph()


def invoke_careerpilot(state: CareerPilotState) -> CareerPilotState:
    """
    Execute CareerPilot with native LangGraph checkpointing.

    Reusing the same thread_id allows subsequent invocations to address
    the same checkpointed workflow thread.
    """
    thread_id = get_thread_id(state)

    return careerpilot_graph.invoke(
        state,
        config=workflow_config(thread_id),
    )