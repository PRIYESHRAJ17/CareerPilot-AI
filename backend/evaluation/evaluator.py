from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .test_cases import EVALUATION_CASES, EvaluationCase


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_TIMEOUT = 180


@dataclass
class CaseResult:
    case_id: str
    name: str
    category: str
    weight: float
    score: float
    weighted_score: float
    latency_seconds: float
    output: str
    notes: list[str]
    success: bool
    error: str | None = None


def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[str, float]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 512,
        },
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_body = response.read().decode("utf-8")

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_URL}: {exc}"
        ) from exc

    elapsed = time.perf_counter() - started

    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Ollama returned invalid JSON: {response_body[:500]}"
        ) from exc

    output = payload.get("response", "")

    if not isinstance(output, str):
        output = str(output)

    # Newer Ollama versions/models can return reasoning separately.
    if not output.strip():
        thinking = payload.get("thinking", "")
        if isinstance(thinking, str) and thinking.strip():
            output = thinking

    return output.strip(), elapsed


def run_case(
    case: EvaluationCase,
    model: str,
    index: int,
    total: int,
) -> CaseResult:
    print(
        f"\n[{index}/{total}] Running "
        f"{case.case_id}: {case.name}...",
        flush=True,
    )

    started = time.perf_counter()

    try:
        output, latency = call_ollama(
            case.prompt,
            model=model,
        )

        if not output:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        score, notes = case.validator(output)

        weighted_score = score * case.weight / 100.0

        result = CaseResult(
            case_id=case.case_id,
            name=case.name,
            category=case.category,
            weight=case.weight,
            score=round(score, 2),
            weighted_score=round(weighted_score, 2),
            latency_seconds=round(latency, 3),
            output=output,
            notes=notes,
            success=True,
        )

        print(
            f"[{index}/{total}] COMPLETE "
            f"| score={result.score:.2f}/100 "
            f"| contribution={result.weighted_score:.2f} "
            f"| time={result.latency_seconds:.2f}s",
            flush=True,
        )

        return result

    except TimeoutError:
        elapsed = time.perf_counter() - started

        print(
            f"[{index}/{total}] TIMEOUT "
            f"after {elapsed:.1f}s",
            flush=True,
        )

        return CaseResult(
            case_id=case.case_id,
            name=case.name,
            category=case.category,
            weight=case.weight,
            score=0.0,
            weighted_score=0.0,
            latency_seconds=round(elapsed, 3),
            output="",
            notes=[],
            success=False,
            error=f"Timed out after {DEFAULT_TIMEOUT} seconds.",
        )

    except Exception as exc:
        elapsed = time.perf_counter() - started

        print(
            f"[{index}/{total}] FAILED: {exc}",
            flush=True,
        )

        return CaseResult(
            case_id=case.case_id,
            name=case.name,
            category=case.category,
            weight=case.weight,
            score=0.0,
            weighted_score=0.0,
            latency_seconds=round(elapsed, 3),
            output="",
            notes=[],
            success=False,
            error=str(exc),
        )


def run_evaluation(
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    results: list[CaseResult] = []

    total = len(EVALUATION_CASES)

    total_weight = sum(
        case.weight
        for case in EVALUATION_CASES
    )

    print()
    print("=" * 68)
    print("CareerPilot AI — Evaluation v2")
    print("=" * 68)
    print(f"Model: {model}")
    print(f"Cases: {total}")
    print(f"Total weight: {total_weight:.0f}")
    print("Thinking: disabled")
    print("=" * 68)

    for index, case in enumerate(
        EVALUATION_CASES,
        start=1,
    ):
        results.append(
            run_case(
                case=case,
                model=model,
                index=index,
                total=total,
            )
        )

    successful = [
        result
        for result in results
        if result.success
    ]

    overall = sum(
        result.weighted_score
        for result in successful
    )

    category_scores: dict[str, list[tuple[float, float]]] = {}

    for result in successful:
        category_scores.setdefault(
            result.category,
            [],
        ).append(
            (
                result.score,
                result.weight,
            )
        )

    category_averages: dict[str, float] = {}

    for category, values in category_scores.items():
        total_category_weight = sum(
            weight
            for _, weight in values
        )

        weighted_average = sum(
            score * weight
            for score, weight in values
        ) / total_category_weight

        category_averages[category] = round(
            weighted_average,
            2,
        )

    return {
        "evaluation_version": "2.0",
        "model": model,
        "overall_score": round(overall, 2),
        "cases_total": total,
        "cases_completed": len(successful),
        "cases_failed": total - len(successful),
        "category_scores": category_averages,
        "cases": [
            {
                "case_id": result.case_id,
                "name": result.name,
                "category": result.category,
                "weight": result.weight,
                "score": result.score,
                "weighted_score": result.weighted_score,
                "latency_seconds": result.latency_seconds,
                "success": result.success,
                "output": result.output,
                "notes": result.notes,
                "error": result.error,
            }
            for result in results
        ],
    }