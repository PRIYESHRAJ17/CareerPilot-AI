from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.api.session import get_candidate_id
from backend.services.external_integrations import (
    github_profile,
    gitlab_profile,
    google_contacts,
    google_gmail_career_messages,
    google_summary,
    microsoft_contacts,
    microsoft_career_messages,
    microsoft_summary,
    notion_create_note,
    notion_search,
)
from backend.services.integration_status import setup_status, status_for_candidate
from backend.services.integration_store import (
    create_clipper_token,
    create_oauth_state,
    delete_connection,
    get_connection,
    revoke_clipper_tokens,
    verify_clipper_token,
)
from backend.services.oauth_integrations import (
    CONFIGS,
    authorization_url,
    complete_oauth,
    public_frontend_url,
)
from backend.services.workspace_store import append_event, upsert_record

router = APIRouter(prefix="/integrations", tags=["External Integrations"])


class NotionNoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    markdown: str = Field(min_length=1, max_length=20_000)
    parent_page_id: str = Field(min_length=10, max_length=80)


class ClipperJobRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2_000)
    title: str = Field(default="Captured opportunity", max_length=300)
    company: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=8_000)
    location: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=5_000)


@router.get("/status")
def integration_status(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    return {"integrations": status_for_candidate(candidate_id), "setup": setup_status()}


@router.get("/connect/{provider}")
def connect(provider: str, request: Request, candidate_id: str = Depends(get_candidate_id)) -> RedirectResponse:
    provider = provider.strip().lower()
    if provider not in CONFIGS:
        raise HTTPException(status_code=404, detail="Unsupported integration provider.")
    config = CONFIGS[provider]
    if not (os.getenv(config.client_id_env) and os.getenv(config.client_secret_env)):
        raise HTTPException(status_code=503, detail=f"{config.display if hasattr(config, 'display') else provider} OAuth credentials are not configured on the server.")
    code_verifier = None
    if config.supports_pkce:
        import secrets
        code_verifier = secrets.token_urlsafe(48)
    state = create_oauth_state(candidate_id, provider, code_verifier=code_verifier)
    url = authorization_url(provider, state=state, code_verifier=code_verifier)
    return RedirectResponse(url=url, status_code=302)


@router.get("/oauth/{provider}/callback")
def oauth_callback(provider: str, request: Request) -> RedirectResponse:
    provider = provider.strip().lower()
    if provider not in CONFIGS:
        return RedirectResponse(f"{public_frontend_url()}/integrations?error=unsupported_provider", status_code=302)
    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    candidate_id_hint = request.cookies.get("careerpilot_session")
    # The OAuth state is bound to the candidate. We cannot trust a cookie value
    # by itself; consume_oauth_state requires the signed session ID. Decode via
    # the same session helper without weakening the session contract.
    from backend.api.session import _verify  # intentional internal reuse
    candidate_id = _verify(candidate_id_hint)
    if not candidate_id or not state:
        return RedirectResponse(f"{public_frontend_url()}/integrations?error=oauth_state", status_code=302)
    from backend.services.integration_store import consume_oauth_state
    state_record = consume_oauth_state(state, provider, candidate_id)
    if not state_record or not code:
        return RedirectResponse(f"{public_frontend_url()}/integrations?error=oauth_state", status_code=302)
    try:
        result = complete_oauth(provider, candidate_id, code, state_record.get("code_verifier"))
        append_event(candidate_id, "integration.connected", f"Connected {provider}.", {"provider": provider})
        return RedirectResponse(f"{public_frontend_url()}/integrations?connected={quote(provider)}", status_code=302)
    except Exception as exc:
        return RedirectResponse(f"{public_frontend_url()}/integrations?error={quote(str(exc)[:180])}", status_code=302)


@router.delete("/{provider}")
def disconnect(provider: str, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    provider = provider.strip().lower()
    if provider not in CONFIGS:
        raise HTTPException(status_code=404, detail="Unsupported integration provider.")
    deleted = delete_connection(candidate_id, provider)
    append_event(candidate_id, "integration.disconnected", f"Disconnected {provider}.", {"provider": provider})
    return {"provider": provider, "disconnected": deleted or True}


@router.post("/notion/note")
def save_notion_note(payload: NotionNoteRequest, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        result = notion_create_note(candidate_id, title=payload.title, markdown=payload.markdown, parent_page_id=payload.parent_page_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    append_event(candidate_id, "notion.note_saved", f"Saved {payload.title} to Notion.", {"page_id": result.get("id")})
    return {"saved": True, "page": result}


@router.get("/notion/search")
def search_notion(query: str, candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        return {"results": notion_search(candidate_id, query)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/google/sync")
def sync_google(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        summary = google_summary(candidate_id)
        for event in summary.get("upcoming_events", []):
            upsert_record(candidate_id, "interviews", {"id": f"google:{event.get('id')}", "source": "google", "event": event}, record_id=f"google:{event.get('id')}")
        for item in summary.get("recent_files", []):
            upsert_record(candidate_id, "documents", {"id": f"google-drive:{item.get('id')}", "source": "google", "file": item}, record_id=f"google-drive:{item.get('id')}")
        return summary
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/google/network")
def sync_google_contacts(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        contacts = google_contacts(candidate_id)
        for contact in contacts:
            key = str(contact.get("resourceName") or contact.get("etag") or "")
            if not key:
                continue
            upsert_record(candidate_id, "networking", {"id": f"google:{key}", "source": "google", "contact": contact}, record_id=f"google:{key}")
        return {"imported": len(contacts), "contacts": contacts}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/microsoft/sync")
def sync_microsoft(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        summary = microsoft_summary(candidate_id)
        for event in summary.get("upcoming_events", []):
            key = f"microsoft:{event.get('id')}"
            upsert_record(candidate_id, "interviews", {"id": key, "source": "microsoft", "event": event}, record_id=key)
        for item in summary.get("recent_files", []):
            key = f"microsoft-drive:{item.get('id')}"
            upsert_record(candidate_id, "documents", {"id": key, "source": "microsoft", "file": item}, record_id=key)
        return summary
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/microsoft/network")
def sync_microsoft_contacts(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        contacts = microsoft_contacts(candidate_id)
        for contact in contacts:
            key = str(contact.get("id") or "")
            if not key:
                continue
            upsert_record(candidate_id, "networking", {"id": f"microsoft:{key}", "source": "microsoft", "contact": contact}, record_id=f"microsoft:{key}")
        return {"imported": len(contacts), "contacts": contacts}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/google/inbox-preview")
def google_inbox_preview(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        return {"items": google_gmail_career_messages(candidate_id)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/microsoft/inbox-preview")
def microsoft_inbox_preview(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        return {"items": microsoft_career_messages(candidate_id)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/github/sync")
def sync_github(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        result = github_profile(candidate_id)
        profile = result.get("profile") or {}
        upsert_record(candidate_id, "documents", {"id": "github-profile", "source": "github", "profile": profile}, record_id="github-profile")
        for repo in result.get("repositories") or []:
            repo_id = str(repo.get("id"))
            if repo_id:
                upsert_record(candidate_id, "documents", {"id": f"github-repo:{repo_id}", "source": "github", "repository": repo}, record_id=f"github-repo:{repo_id}")
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/gitlab/sync")
def sync_gitlab(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    try:
        result = gitlab_profile(candidate_id)
        profile = result.get("profile") or {}
        upsert_record(candidate_id, "documents", {"id": "gitlab-profile", "source": "gitlab", "profile": profile}, record_id="gitlab-profile")
        for project in result.get("projects") or []:
            project_id = str(project.get("id"))
            if project_id:
                upsert_record(candidate_id, "documents", {"id": f"gitlab-project:{project_id}", "source": "gitlab", "project": project}, record_id=f"gitlab-project:{project_id}")
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/clipper/token")
def new_clipper_token(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    revoke_clipper_tokens(candidate_id)
    token = create_clipper_token(candidate_id)
    return {"token": token, "warning": "Save this token now. It is shown only once."}


@router.post("/clipper/revoke")
def revoke_clipper(candidate_id: str = Depends(get_candidate_id)) -> dict[str, Any]:
    count = revoke_clipper_tokens(candidate_id)
    return {"revoked": count}


@router.post("/clipper/jobs")
def clipper_job(payload: ClipperJobRequest, request: Request) -> dict[str, Any]:
    token = request.headers.get("x-careerpilot-clipper-token", "")
    candidate_id = verify_clipper_token(token)
    if not candidate_id:
        raise HTTPException(status_code=401, detail="Invalid or revoked CareerPilot clipper token.")
    from urllib.parse import urlparse
    parsed = urlparse(payload.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Clip URL must be a valid HTTP(S) URL.")
    record = upsert_record(candidate_id, "saved-jobs", {
        "title": payload.title.strip() or "Captured opportunity",
        "company": payload.company.strip(),
        "description": payload.description.strip(),
        "location": payload.location.strip(),
        "notes": payload.notes.strip(),
        "apply_url": payload.url,
        "source_url": payload.url,
        "capture_type": "careerpilot-browser-extension",
        "saved_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    })
    append_event(candidate_id, "saved-job.clipped", f"Captured {payload.title or 'job opportunity'} from browser.", {"record_id": record["id"], "url": payload.url})
    return record
