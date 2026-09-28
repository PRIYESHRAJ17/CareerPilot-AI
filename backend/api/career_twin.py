from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.services.career_twin import (
    get_or_create,
    record_event,
    update_from_candidate,
)


router = APIRouter(
    prefix="/career-twin",
    tags=["Career Twin"],
)


@router.get("/{candidate_id}")
def get_career_twin(
    candidate_id: str,
) -> dict[str, Any]:

    twin = get_or_create(
        candidate_id
    )

    return twin.model_dump(
        mode="json"
    )


@router.post("/{candidate_id}/sync")
def sync_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:

    candidate = dict(
        payload.get(
            "candidate_profile"
        )
        or {}
    )

    candidate[
        "candidate_id"
    ] = candidate_id

    twin = update_from_candidate(
        candidate=candidate,
        candidate_intelligence=(
            payload.get(
                "candidate_intelligence"
            )
        ),
        skill_gaps=(
            payload.get(
                "skill_gaps"
            )
        ),
        recommendations=(
            payload.get(
                "recommendations"
            )
            or []
        ),
    )

    return twin.model_dump(
        mode="json"
    )


@router.patch("/{candidate_id}")
def update_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:

    twin = get_or_create(
        candidate_id
    )

    profile = twin.profile.model_copy(
        deep=True
    )

    incoming = dict(
        payload.get(
            "profile"
        )
        or {}
    )

    for field, value in incoming.items():

        if hasattr(
            profile,
            field,
        ):
            setattr(
                profile,
                field,
                value,
            )

    twin.profile = profile

    twin.version += 1

    from backend.services.career_twin import save

    save(twin)

    record_event(
        candidate_id=candidate_id,
        event_type="manual_update",
        summary=(
            "Career Twin profile manually "
            "updated by the user."
        ),
        payload={
            "fields": sorted(
                incoming.keys()
            )
        },
    )

    return get_or_create(
        candidate_id
    ).model_dump(
        mode="json"
    )


@router.post("/{candidate_id}/events")
def add_career_event(
    candidate_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:

    event = record_event(
        candidate_id=candidate_id,
        event_type=str(
            payload.get(
                "event_type"
            )
            or "custom"
        ),
        summary=str(
            payload.get(
                "summary"
            )
            or "Career event recorded."
        ),
        payload=dict(
            payload.get(
                "payload"
            )
            or {}
        ),
    )

    return {
        "event": event.model_dump(
            mode="json"
        ),
        "career_twin": (
            get_or_create(
                candidate_id
            ).model_dump(
                mode="json"
            )
        ),
    }