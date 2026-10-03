from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)

from backend.api.session import (
    ensure_session,
    get_candidate_id,
)

from backend.services.career_twin import (
    get_or_create,
    record_event,
    save,
    update_from_candidate,
)

router = APIRouter(
    prefix="/career-twin",
    tags=["Career Twin"],
)


@router.get("/session")
def session_career_twin(
    request: Request,
    response: Response,
) -> dict[str, Any]:
    candidate_id = ensure_session(
        request,
        response,
    )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.get("/{candidate_id}")
def get_career_twin(
    candidate_id: str,
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.post("/{candidate_id}/sync")
def sync_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    candidate = dict(
        payload.get(
            "candidate_profile",
        )
        or {},
    )

    candidate[
        "candidate_id"
    ] = candidate_id

    twin = update_from_candidate(
        candidate=candidate,
        candidate_intelligence=payload.get(
            "candidate_intelligence",
        ),
        skill_gaps=payload.get(
            "skill_gaps",
        ),
        recommendations=payload.get(
            "recommendations",
        )
        or [],
    )

    return twin.model_dump(
        mode="json",
    )


@router.patch("/{candidate_id}")
def update_career_twin(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    twin = get_or_create(
        candidate_id,
    )

    profile = twin.profile.model_copy(
        deep=True,
    )

    incoming = dict(
        payload.get(
            "profile",
        )
        or {},
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

    save(twin)

    record_event(
        candidate_id=candidate_id,
        event_type="manual_update",
        summary="Career Twin profile manually updated by the user.",
        payload={
            "fields": sorted(
                incoming.keys(),
            ),
        },
    )

    return get_or_create(
        candidate_id,
    ).model_dump(
        mode="json",
    )


@router.post("/{candidate_id}/events")
def add_career_event(
    candidate_id: str,
    payload: dict[str, Any],
    authenticated_candidate_id: str = Depends(
        get_candidate_id,
    ),
) -> dict[str, Any]:
    if (
        candidate_id !=
        authenticated_candidate_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Career session does not own this Career Twin.",
        )

    event = record_event(
        candidate_id=candidate_id,
        event_type=str(
            payload.get(
                "event_type",
            )
            or "custom",
        ),
        summary=str(
            payload.get(
                "summary",
            )
            or "Career event recorded.",
        ),
        payload=dict(
            payload.get(
                "payload",
            )
            or {},
        ),
    )

    return {
        "event": event.model_dump(
            mode="json",
        ),
        "career_twin": get_or_create(
            candidate_id,
        ).model_dump(
            mode="json",
        ),
    }
