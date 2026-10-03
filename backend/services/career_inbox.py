from __future__ import annotations

from typing import Any

from backend.services.external_integrations import (
    google_gmail_career_messages,
    microsoft_career_messages,
    normalize_message,
)
from backend.services.integration_store import list_connections
from backend.services.workspace_store import list_records, upsert_record


def sync_career_inbox(candidate_id: str) -> dict[str, Any]:
    imported: list[dict[str, Any]] = []
    connected = {str(item.get("provider")) for item in list_connections(candidate_id)}
    errors: dict[str, str] = {}
    if "google" in connected:
        try:
            imported.extend(normalize_message(item, "google") for item in google_gmail_career_messages(candidate_id))
        except Exception as exc:
            errors["google"] = str(exc)
    if "microsoft" in connected:
        try:
            imported.extend(normalize_message(item, "microsoft") for item in microsoft_career_messages(candidate_id))
        except Exception as exc:
            errors["microsoft"] = str(exc)

    seen: set[str] = set()
    stored: list[dict[str, Any]] = []
    for item in imported:
        key = f"{item.get('source')}:{item.get('id')}"
        if key in seen:
            continue
        seen.add(key)
        payload = {**item, "id": key, "synced_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
        stored.append(upsert_record(candidate_id, "inbox", payload, record_id=key))
    return {"items": stored or list_records(candidate_id, "inbox"), "imported": len(stored), "errors": errors}
