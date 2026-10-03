from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class CareerTwinTimeline:
    """
    Persistent Career Twin event/timeline store.

    Timeline events are append-only JSONL records so that historical
    career evolution is never silently overwritten.
    """

    DATA_DIR = (
        Path(__file__).resolve().parents[1]
        / "data"
    )

    EVENTS_FILE = (
        DATA_DIR
        / "career_timeline.jsonl"
    )

    def __init__(self) -> None:
        self.DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def record(
        self,
        candidate_id: str,
        event_type: str,
        summary: str,
        source: str = "careerpilot",
        evidence: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        career_twin_version: Optional[int] = None,
    ) -> Dict[str, Any]:

        event = {
            "event_id": str(uuid4()),
            "candidate_id": str(
                candidate_id
            ),
            "event_type": str(
                event_type
            ),
            "timestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "source": str(source),
            "summary": str(summary),
            "evidence": list(
                evidence or []
            ),
            "metadata": dict(
                metadata or {}
            ),
            "career_twin_version": (
                career_twin_version
            ),
        }

        with self.EVENTS_FILE.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        return event

    def get_events(
        self,
        candidate_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:

        if not self.EVENTS_FILE.exists():
            return []

        events: List[
            Dict[str, Any]
        ] = []

        with self.EVENTS_FILE.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                try:
                    event = json.loads(
                        line
                    )
                except json.JSONDecodeError:
                    continue

                if str(
                    event.get(
                        "candidate_id",
                        "",
                    )
                ) != str(
                    candidate_id
                ):
                    continue

                events.append(
                    event
                )

        events.sort(
            key=lambda item: item.get(
                "timestamp",
                "",
            )
        )

        if limit is not None:
            return events[-int(limit):]

        return events

    def build_timeline(
        self,
        candidate_id: str,
        career_twin: Any = None,
        limit: int = 100,
    ) -> Dict[str, Any]:

        events = self.get_events(
            candidate_id,
            limit=limit,
        )

        twin_memory: List[Any] = []

        if career_twin is not None:

            if isinstance(
                career_twin,
                dict,
            ):
                twin_memory = list(
                    career_twin.get(
                        "memory",
                        [],
                    )
                    or []
                )

            else:
                twin_memory = list(
                    getattr(
                        career_twin,
                        "memory",
                        [],
                    )
                    or []
                )

        combined = []

        for item in twin_memory:
            if hasattr(
                item,
                "model_dump",
            ):
                combined.append(
                    item.model_dump(
                        mode="json"
                    )
                )
            elif hasattr(
                item,
                "__dict__",
            ):
                combined.append(
                    dict(
                        item.__dict__
                    )
                )
            else:
                combined.append(
                    item
                )

        combined.extend(
            events
        )

        combined.sort(
            key=lambda item: (
                str(
                    item.get(
                        "timestamp",
                        item.get(
                            "created_at",
                            "",
                        ),
                    )
                )
            )
        )

        return {
            "candidate_id": str(
                candidate_id
            ),
            "event_count": len(
                combined
            ),
            "events": combined[-limit:],
            "event_types": sorted(
                {
                    str(
                        item.get(
                            "event_type",
                            "UNKNOWN",
                        )
                    )
                    for item in combined
                }
            ),
        }

    def build_career_snapshot(
        self,
        candidate_id: str,
        career_twin: Any = None,
    ) -> Dict[str, Any]:

        timeline = self.build_timeline(
            candidate_id,
            career_twin,
        )

        events = timeline[
            "events"
        ]

        skill_events = [
            event
            for event in events
            if str(
                event.get(
                    "event_type",
                    "",
                )
            ).upper()
            in {
                "SKILL_ADDED",
                "SKILL_GAP_DETECTED",
                "MARKET_GAP_DETECTED",
            }
        ]

        goal_events = [
            event
            for event in events
            if str(
                event.get(
                    "event_type",
                    "",
                )
            ).upper()
            in {
                "GOAL_UPDATED",
                "CAREER_DIRECTION_CHANGED",
            }
        ]

        opportunity_events = [
            event
            for event in events
            if str(
                event.get(
                    "event_type",
                    "",
                )
            ).upper()
            == "JOB_MATCH_FOUND"
        ]

        return {
            "candidate_id": str(
                candidate_id
            ),
            "timeline": timeline,
            "skill_event_count": len(
                skill_events
            ),
            "goal_event_count": len(
                goal_events
            ),
            "opportunity_event_count": len(
                opportunity_events
            ),
            "latest_event": (
                events[-1]
                if events
                else None
            ),
        }