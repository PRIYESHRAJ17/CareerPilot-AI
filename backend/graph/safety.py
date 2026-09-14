from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SafetyPolicy:
    """
    Deterministic workflow safety limits.

    These limits prevent invalid agent outputs from causing
    unbounded orchestration loops.
    """

    max_retries: int = 2
    max_workflow_steps: int = 25
    max_errors: int = 5


DEFAULT_SAFETY_POLICY = SafetyPolicy()


def evaluate_workflow_safety(
    state: dict[str, Any],
    policy: SafetyPolicy = DEFAULT_SAFETY_POLICY,
) -> dict[str, Any]:
    """
    Evaluate whether the current workflow may safely continue.
    """

    retry_count = int(state.get("retry_count", 0) or 0)
    step_count = int(state.get("step_count", 0) or 0)
    errors = state.get("errors") or []

    reasons: list[str] = []

    if retry_count >= policy.max_retries:
        reasons.append(
            f"Maximum recovery retries reached ({policy.max_retries})."
        )

    if step_count >= policy.max_workflow_steps:
        reasons.append(
            f"Maximum workflow steps reached ({policy.max_workflow_steps})."
        )

    if len(errors) >= policy.max_errors:
        reasons.append(
            f"Maximum accumulated errors reached ({policy.max_errors})."
        )

    return {
        "safe_to_continue": not reasons,
        "retry_count": retry_count,
        "step_count": step_count,
        "error_count": len(errors),
        "reasons": reasons,
    }


def can_retry(
    state: dict[str, Any],
    policy: SafetyPolicy = DEFAULT_SAFETY_POLICY,
) -> bool:
    """
    Return True only when another recovery attempt is permitted.
    """

    result = evaluate_workflow_safety(state, policy)
    return bool(result["safe_to_continue"])