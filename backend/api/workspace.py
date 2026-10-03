from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.api.session import get_candidate_id
from backend.services.workspace_store import (
    append_event,
    delete_record,
    get_record,
    list_events,
    list_records,
    upsert_record,
)

router = APIRouter(prefix="/workspace", tags=["CareerPilot Workspace"])

ALLOWED_ENTITIES = {
    "saved-jobs",
    "applications",
    "companies",
    "interviews",
    "career-plan",
    "networking",
    "alerts",
    "packets",
    "documents",
    "market",
    "agent-runs",
    "settings",
    "inbox",
    "learning",
}


class WorkspaceRecord(BaseModel):
    id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class BrowserClipRequest(BaseModel):
    url: str
    title: str = "Captured opportunity"
    company: str = ""
    notes: str = ""


class EventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=500)
    payload: dict[str, Any] = Field(default_factory=dict)


def _entity(entity: str) -> str:
    if entity not in ALLOWED_ENTITIES:
        raise HTTPException(status_code=404, detail="Workspace entity is not supported.")
    return entity


@router.get("/state")
def workspace_state(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "saved_jobs": list_records(candidate_id, "saved-jobs"),
        "applications": list_records(candidate_id, "applications"),
        "companies": list_records(candidate_id, "companies"),
        "interviews": list_records(candidate_id, "interviews"),
        "career_plan": list_records(candidate_id, "career-plan"),
        "networking": list_records(candidate_id, "networking"),
        "alerts": list_records(candidate_id, "alerts"),
        "packets": list_records(candidate_id, "packets"),
        "documents": list_records(candidate_id, "documents"),
        "market": list_records(candidate_id, "market", limit=50),
        "settings": list_records(candidate_id, "settings", limit=5),
        "agent_runs": list_records(candidate_id, "agent-runs", limit=50),
        "inbox": list_records(candidate_id, "inbox", limit=100),
        "learning": list_records(candidate_id, "learning", limit=100),
        "activity": list_events(candidate_id),
    }


@router.get("/activity")
def activity(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {"activity": list_events(candidate_id)}



@router.post("/events")
def create_event(event: EventRequest, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return append_event(candidate_id, event.event_type, event.summary, event.payload)


@router.post("/browser-clip")
def browser_clip(payload: BrowserClipRequest, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    parsed = urlparse(payload.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Clip URL must be a valid HTTP(S) URL.")
    record = upsert_record(
        candidate_id,
        "saved-jobs",
        {
            "title": payload.title,
            "company": payload.company,
            "apply_url": payload.url,
            "source_url": payload.url,
            "notes": payload.notes,
            "capture_type": "browser-clipper",
            "saved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        },
    )
    append_event(candidate_id, "saved-job.clipped", f"Captured {payload.title}.", {"record_id": record["id"], "url": payload.url})
    return record


@router.post("/{entity}")
def create_or_update(
    entity: str,
    record: WorkspaceRecord,
    candidate_id: str = Depends(get_candidate_id),
) -> dict[str, Any]:
    entity = _entity(entity)
    payload = dict(record.payload)
    stored = upsert_record(candidate_id, entity, payload, record_id=record.id)
    append_event(
        candidate_id,
        f"{entity}.updated",
        f"{entity.replace('-', ' ').title()} updated.",
        {"record_id": stored["id"]},
    )
    return stored


@router.get("/{entity}")
def list_entity(entity: str, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    entity = _entity(entity)
    return {"entity": entity, "items": list_records(candidate_id, entity)}


@router.get("/{entity}/{record_id}")
def get_entity(entity: str, record_id: str, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    entity = _entity(entity)
    item = get_record(candidate_id, entity, record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Workspace record not found.")
    return item


@router.delete("/{entity}/{record_id}")
def delete_entity(entity: str, record_id: str, candidate_id: str = Depends(get_candidate_id)) -> dict[str, bool]:
    entity = _entity(entity)
    deleted = delete_record(candidate_id, entity, record_id)
    if deleted:
        append_event(candidate_id, f"{entity}.deleted", f"{entity.replace('-', ' ').title()} removed.", {"record_id": record_id})
    return {"deleted": deleted}


