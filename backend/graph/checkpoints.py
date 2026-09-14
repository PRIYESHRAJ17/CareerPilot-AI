from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver


# Native LangGraph checkpointer.
#
# This keeps workflow checkpoints available throughout the running
# application process and allows a workflow to be resumed by thread_id.
careerpilot_checkpointer = MemorySaver()


def workflow_config(thread_id: str) -> dict[str, Any]:
    """
    Build the LangGraph configuration used for checkpointing.

    The same thread_id must be reused to resume the same workflow thread.
    """
    if not thread_id:
        raise ValueError("thread_id is required for checkpointed execution.")

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def get_thread_id(state: dict[str, Any]) -> str:
    """
    Resolve the checkpoint thread identifier from shared state.
    """
    workflow = state.get("workflow")

    if workflow is not None:
        thread_id = getattr(workflow, "thread_id", None)

        if thread_id:
            return str(thread_id)

    thread_id = state.get("thread_id")

    if thread_id:
        return str(thread_id)

    request_id = state.get("request_id")

    if request_id:
        return str(request_id)

    raise ValueError(
        "Unable to determine thread_id from CareerPilot state."
    )