from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.session import get_candidate_id
from backend.services.career_inbox import sync_career_inbox
from backend.services.workspace_store import list_records, upsert_record

router = APIRouter(prefix="/inbox", tags=["Career Inbox"])


class InboxItemRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source: str = Field(default="manual", max_length=50)
    kind: str = Field(default="career", max_length=50)
    content: str = Field(default="", max_length=20_000)
    url: str = Field(default="", max_length=2_000)


@router.get("/items")
def items(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {"items": list_records(candidate_id, "inbox")}


@router.post("/sync")
def sync(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return sync_career_inbox(candidate_id)


@router.post("/items")
def add_item(payload: InboxItemRequest, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    record = upsert_record(candidate_id, "inbox", payload.model_dump())
    return record
