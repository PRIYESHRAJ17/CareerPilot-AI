from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .evaluator import DEFAULT_MODEL, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run CareerPilot local LLM evaluation."
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model name.",
    )

    args = parser.parse_args()

    report = run_evaluation(args.model)

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"llm_eval_{args.model.replace(':', '_')}_{timestamp}.json"

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("CareerPilot LLM Evaluation")
    print("=" * 60)
    print(f"Model: {report['model']}")
    print(f"Overall: {report['overall_score']}/100")
    print()

    for category, score in report["category_scores"].items():
        print(f"{category:24} {score:6.2f}/100")

    print()
    print(f"Report saved to: {report_path}")
    print()

    for case in report["cases"]:
        print(
            f"{case['case_id']} | "
            f"{case['name']:<28} | "
            f"{case['score']:6.2f}/100 | "
            f"{case['latency_seconds']:.2f}s"
        )


if __name__ == "__main__":
    main()