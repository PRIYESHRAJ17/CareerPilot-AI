from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class CareerGapIntelligence:
    """
    Persistent career-gap history.

    Stores market-derived gap snapshots independently from the main
    Career Twin document so historical changes can be compared.
    """

    DATA_FILE = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "career_gap_history.jsonl"
    )

    def __init__(self) -> None:
        self.DATA_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def record_snapshot(
        self,
        candidate_id: str,
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:

        gaps = list(
            analysis.get(
                "market_skill_gaps",
                [],
            )
            or []
        )

        record = {
            "candidate_id": str(
                candidate_id
            ),
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "jobs_analyzed": (
                analysis.get(
                    "jobs_analyzed",
                    0,
                )
            ),
            "priority_skill_gaps": list(
                analysis.get(
                    "priority_skill_gaps",
                    [],
                )
                or []
            ),
            "market_skill_gaps": gaps,
            "recommendations": list(
                analysis.get(
                    "recommendations",
                    [],
                )
                or []
            ),
        }

        with self.DATA_FILE.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        return record

    def get_history(
        self,
        candidate_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:

        if not self.DATA_FILE.exists():
            return []

        rows: List[
            Dict[str, Any]
        ] = []

        with self.DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as handle:

            for line in handle:

                line = line.strip()

                if not line:
                    continue

                try:
                    row = json.loads(
                        line
                    )
                except json.JSONDecodeError:
                    continue

                if str(
                    row.get(
                        "candidate_id",
                        "",
                    )
                ) != str(
                    candidate_id
                ):
                    continue

                rows.append(
                    row
                )

        return rows[-limit:]

    def build_current_gap_state(
        self,
        candidate_id: str,
    ) -> Dict[str, Any]:

        history = self.get_history(
            candidate_id,
            limit=20,
        )

        if not history:
            return {
                "candidate_id": str(
                    candidate_id
                ),
                "history_count": 0,
                "current_gaps": [],
                "previous_gaps": [],
                "new_gaps": [],
                "resolved_gaps": [],
                "persistent_gaps": [],
            }

        current = set(
            history[-1].get(
                "priority_skill_gaps",
                [],
            )
            or []
        )

        previous = set()

        if len(history) >= 2:
            previous = set(
                history[-2].get(
                    "priority_skill_gaps",
                    [],
                )
                or []
            )

        return {
            "candidate_id": str(
                candidate_id
            ),
            "history_count": len(
                history
            ),
            "current_gaps": sorted(
                current
            ),
            "previous_gaps": sorted(
                previous
            ),
            "new_gaps": sorted(
                current
                - previous
            ),
            "resolved_gaps": sorted(
                previous
                - current
            ),
            "persistent_gaps": sorted(
                current
                & previous
            ),
        }