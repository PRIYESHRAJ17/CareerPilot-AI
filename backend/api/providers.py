from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends

from backend.api.session import get_candidate_id
from backend.data.provider_catalog import build_provider_catalog, CATALOG_TARGET
from backend.services.workspace_store import list_records, upsert_record

router = APIRouter(prefix="/providers", tags=["Provider Control Center"])
VERIFICATION = Path(__file__).resolve().parents[1] / "data" / "provider_verification.json"


@router.get("/catalog")
def catalog(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    definitions = build_provider_catalog(target=CATALOG_TARGET)
    verification: dict[str, Any] = {}
    if VERIFICATION.exists():
        try:
            verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
        except Exception:
            verification = {}
    by_name = {str(item.get("name")): item for item in verification.get("results", []) if isinstance(item, dict)}
    preferences = {str(item.get("id")): item for item in list_records(candidate_id, "settings")}
    pref = (preferences.get("providers") or {}).get("providers") or {}
    providers = []
    for definition in definitions:
        name = str(getattr(definition, "name", ""))
        metadata = getattr(definition, "metadata", {}) or {}
        result = by_name.get(name, {})
        providers.append({
            "name": name,
            "display_name": str(getattr(definition, "display_name", None) or name),
            "platform": str((getattr(definition, "adapter_config", {}) or {}).get("platform", "unknown")),
            "state": result.get("state", "UNVERIFIED"),
            "health_ok": result.get("health_ok"),
            "search_ok": result.get("search_ok"),
            "jobs_returned": result.get("jobs_returned", 0),
            "checked_at": result.get("checked_at"),
            "enabled": bool(pref.get(name, {}).get("enabled", True)),
            "metadata": metadata,
        })
    return {"target": CATALOG_TARGET, "providers": providers, "source": "persisted verification manifest + canonical catalog"}


@router.post("/preferences")
def provider_preference(payload: dict[str, Any], candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    name = str(payload.get("provider") or "").strip()
    enabled = bool(payload.get("enabled", True))
    current = next((item for item in list_records(candidate_id, "settings") if item.get("id") == "providers"), {})
    providers = dict(current.get("providers") or {})
    providers[name] = {"enabled": enabled}
    return upsert_record(candidate_id, "settings", {"id": "providers", "providers": providers})
