from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid

from backend.schemas.career_twin import (
    CareerMemoryEvent,
    CareerTwin,
    CareerTwinDerived,
    CareerTwinProfile,
)


DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
)

STORE_PATH = DATA_DIR / "career_twins.json"
EVENTS_PATH = DATA_DIR / "career_memory_events.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unique(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()

    for value in values:
        if value is None:
            continue

        key = json.dumps(
            value,
            sort_keys=True,
            default=str,
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _load_store() -> dict[str, Any]:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not STORE_PATH.exists():
        return {}

    try:
        payload = json.loads(
            STORE_PATH.read_text(
                encoding="utf-8"
            )
        )

        return (
            payload
            if isinstance(payload, dict)
            else {}
        )

    except (OSError, json.JSONDecodeError):
        return {}


def _save_store(
    store: dict[str, Any],
) -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = STORE_PATH.with_suffix(
        ".tmp"
    )

    temp_path.write_text(
        json.dumps(
            store,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp_path.replace(STORE_PATH)


def get_or_create(
    candidate_id: str,
) -> CareerTwin:
    store = _load_store()

    existing = store.get(candidate_id)

    if existing:
        return CareerTwin.model_validate(
            existing
        )

    twin = CareerTwin(
        candidate_id=candidate_id
    )

    store[candidate_id] = twin.model_dump(
        mode="json"
    )

    _save_store(store)

    return twin


def save(
    twin: CareerTwin,
) -> CareerTwin:
    store = _load_store()

    twin.updated_at = _now()

    store[twin.candidate_id] = (
        twin.model_dump(
            mode="json"
        )
    )

    _save_store(store)

    return twin


def record_event(
    candidate_id: str,
    event_type: str,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> CareerMemoryEvent:

    event = CareerMemoryEvent(
        event_id=f"evt-{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        summary=summary,
        timestamp=_now(),
        payload=payload or {},
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with EVENTS_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                event.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
            )
            + "\n"
        )

    twin = get_or_create(
        candidate_id
    )

    twin.memory = (
        twin.memory + [event]
    )[-100:]

    save(twin)

    return event


def update_from_candidate(
    candidate: dict[str, Any],
    candidate_intelligence: dict[str, Any] | None = None,
    skill_gaps: Any = None,
    recommendations: list[Any] | None = None,
    candidate_id: str | None = None,
) -> CareerTwin:

    resolved_candidate_id = str(
        candidate_id
        or candidate.get("candidate_id")
        or "agentic-user"
    )

    twin = get_or_create(
        resolved_candidate_id
    )

    current = twin.profile

    career_goal = (
        candidate.get(
            "career_goal"
        )
        or {}
    )

    incoming_profile = CareerTwinProfile(
        name=candidate.get("name"),
        headline=candidate.get("headline"),
        skills=list(
            candidate.get("skills")
            or []
        ),
        technical_skills=list(
            candidate.get(
                "technical_skills"
            )
            or []
        ),
        soft_skills=list(
            candidate.get(
                "soft_skills"
            )
            or []
        ),
        education=list(
            candidate.get(
                "education"
            )
            or []
        ),
        certifications=list(
            candidate.get(
                "certifications"
            )
            or []
        ),
        projects=list(
            candidate.get(
                "projects"
            )
            or []
        ),
        experience=list(
            candidate.get(
                "experience"
            )
            or []
        ),
        target_roles=list(
            career_goal.get(
                "target_roles"
            )
            or []
        ),
        target_industries=list(
            career_goal.get(
                "target_industries"
            )
            or []
        ),
        target_locations=list(
            career_goal.get(
                "target_locations"
            )
            or candidate.get(
                "preferred_locations"
            )
            or []
        ),
        preferred_work_modes=list(
            career_goal.get(
                "preferred_work_modes"
            )
            or candidate.get(
                "preferred_work_modes"
            )
            or []
        ),
        minimum_salary_lpa=career_goal.get(
            "minimum_salary_lpa"
        ),
        timeline_months=career_goal.get(
            "target_timeline_months"
        ),
    )

    twin.profile = CareerTwinProfile(
        name=(
            incoming_profile.name
            or current.name
        ),
        headline=(
            incoming_profile.headline
            or current.headline
        ),
        skills=_unique(
            current.skills
            + incoming_profile.skills
        ),
        technical_skills=_unique(
            current.technical_skills
            + incoming_profile.technical_skills
        ),
        soft_skills=_unique(
            current.soft_skills
            + incoming_profile.soft_skills
        ),
        education=_unique(
            current.education
            + incoming_profile.education
        ),
        certifications=_unique(
            current.certifications
            + incoming_profile.certifications
        ),
        projects=_unique(
            current.projects
            + incoming_profile.projects
        ),
        experience=_unique(
            current.experience
            + incoming_profile.experience
        ),
        target_roles=_unique(
            current.target_roles
            + incoming_profile.target_roles
        ),
        target_industries=_unique(
            current.target_industries
            + incoming_profile.target_industries
        ),
        target_locations=_unique(
            current.target_locations
            + incoming_profile.target_locations
        ),
        preferred_work_modes=_unique(
            current.preferred_work_modes
            + incoming_profile.preferred_work_modes
        ),
        minimum_salary_lpa=(
            incoming_profile.minimum_salary_lpa
            if incoming_profile.minimum_salary_lpa
            is not None
            else current.minimum_salary_lpa
        ),
        timeline_months=(
            incoming_profile.timeline_months
            if incoming_profile.timeline_months
            is not None
            else current.timeline_months
        ),
    )

    intelligence = (
        candidate_intelligence
        or {}
    )

    derived: CareerTwinDerived = (
        twin.derived.model_copy(
            deep=True
        )
    )

    derived.strengths = _unique(
        derived.strengths
        + list(
            intelligence.get(
                "strengths"
            )
            or []
        )
    )

    derived.career_directions = _unique(
        derived.career_directions
        + list(
            intelligence.get(
                "career_direction"
            )
            or []
        )
    )

    if intelligence.get(
        "readiness_score"
    ) is not None:
        derived.readiness_score = float(
            intelligence["readiness_score"]
        )

    if intelligence.get(
        "readiness_level"
    ):
        derived.readiness_level = str(
            intelligence[
                "readiness_level"
            ]
        )

    gaps: list[str] = []

    if isinstance(
        skill_gaps,
        dict,
    ):
        for key in (
            "required",
            "preferred",
            "missing",
        ):
            gaps.extend(
                str(item)
                for item in (
                    skill_gaps.get(
                        key
                    )
                    or []
                )
            )

    elif isinstance(
        skill_gaps,
        list,
    ):
        gaps.extend(
            str(item)
            for item in skill_gaps
        )

    derived.skill_gaps = _unique(
        derived.skill_gaps
        + gaps
    )

    twin.derived = derived

    twin.version += 1

    save(twin)

    record_event(
        candidate_id=candidate_id,
        event_type="profile_sync",
        summary=(
            "Career Twin synchronized "
            "from the active CareerPilot workflow."
        ),
        payload={
            "skills": twin.profile.skills,
            "target_roles": twin.profile.target_roles,
            "readiness_score": (
                twin.derived.readiness_score
            ),
            "recommendation_count": len(
                recommendations or []
            ),
        },
    )

    return get_or_create(
        candidate_id
    )


def merge_twin_into_candidate_profile(
    candidate: dict[str, Any],
    twin: CareerTwin,
) -> dict[str, Any]:

    merged = dict(
        candidate or {}
    )

    profile = twin.profile

    for field in (
        "skills",
        "technical_skills",
        "soft_skills",
        "education",
        "certifications",
        "projects",
        "experience",
    ):
        merged[field] = _unique(
            list(
                merged.get(
                    field
                )
                or []
            )
            + list(
                getattr(
                    profile,
                    field,
                )
                or []
            )
        )

    career_goal = dict(
        merged.get(
            "career_goal"
        )
        or {}
    )

    career_goal[
        "target_roles"
    ] = _unique(
        list(
            career_goal.get(
                "target_roles"
            )
            or []
        )
        + profile.target_roles
    )

    career_goal[
        "target_industries"
    ] = _unique(
        list(
            career_goal.get(
                "target_industries"
            )
            or []
        )
        + profile.target_industries
    )

    career_goal[
        "target_locations"
    ] = _unique(
        list(
            career_goal.get(
                "target_locations"
            )
            or []
        )
        + profile.target_locations
    )

    if (
        career_goal.get(
            "minimum_salary_lpa"
        )
        is None
    ):
        career_goal[
            "minimum_salary_lpa"
        ] = profile.minimum_salary_lpa

    if (
        career_goal.get(
            "target_timeline_months"
        )
        is None
    ):
        career_goal[
            "target_timeline_months"
        ] = profile.timeline_months

    merged[
        "career_goal"
    ] = career_goal

    if not merged.get("name"):
        merged["name"] = profile.name

    if not merged.get("headline"):
        merged["headline"] = profile.headline

    return merged