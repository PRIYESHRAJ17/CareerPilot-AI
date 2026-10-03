from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.api.session import get_candidate_id
from backend.services.learning_hub import LEARNING_PROVIDERS, recommendations
from backend.services.workspace_store import list_records, upsert_record

router = APIRouter(prefix="/learning", tags=["Learning Hub"])


@router.get("/providers")
def providers(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {"providers": list(LEARNING_PROVIDERS)}


@router.get("/recommendations")
def learning_recommendations(skills: str = Query(default=""), candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    values = [item.strip() for item in skills.split(",") if item.strip()]
    return {"recommendations": recommendations(values, limit=30)}


@router.get("/progress")
def progress(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {"items": list_records(candidate_id, "learning")}


@router.post("/progress")
def save_progress(payload: dict[str, Any], candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return upsert_record(candidate_id, "learning", payload, record_id=str(payload.get("id") or ""))
