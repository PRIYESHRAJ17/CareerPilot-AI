from __future__ import annotations

import re
from typing import Any

import requests

from backend.services.oauth_integrations import access_token


class IntegrationApiError(RuntimeError):
    pass


def _request(provider: str, candidate_id: str, url: str, *, params: dict[str, Any] | None = None, method: str = "GET", json: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    token = access_token(candidate_id, provider)
    final_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if headers:
        final_headers.update(headers)
    response = requests.request(method, url, params=params, json=json, headers=final_headers, timeout=25)
    if not response.ok:
        raise IntegrationApiError(f"{provider} API returned HTTP {response.status_code}: {response.text[:1000]}")
    try:
        data = response.json()
    except ValueError as exc:
        raise IntegrationApiError(f"{provider} API returned invalid JSON.") from exc
    return data if isinstance(data, dict) else {"data": data}


def notion_create_note(candidate_id: str, *, title: str, markdown: str, parent_page_id: str) -> dict[str, Any]:
    """Create a simple Notion child page then append paragraph blocks."""
    api_version = "2022-06-28"
    token = access_token(candidate_id, "notion")
    rich_title = [{"type": "text", "text": {"content": title[:200]}}]
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": api_version, "Content-Type": "application/json"},
        json={"parent": {"page_id": parent_page_id}, "properties": {"title": {"title": rich_title}}},
        timeout=25,
    )
    if not response.ok:
        raise IntegrationApiError(f"Notion create page failed: HTTP {response.status_code}: {response.text[:1000]}")
    page = response.json()
    page_id = str(page.get("id", ""))
    if page_id and markdown.strip():
        blocks = []
        for raw in markdown.splitlines():
            text = raw.strip()
            if not text:
                continue
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:1900]}}]}})
        if blocks:
            append = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers={"Authorization": f"Bearer {token}", "Notion-Version": api_version, "Content-Type": "application/json"},
                json={"children": blocks[:100]},
                timeout=25,
            )
            if not append.ok:
                raise IntegrationApiError(f"Notion append blocks failed: HTTP {append.status_code}: {append.text[:1000]}")
    return page


def notion_search(candidate_id: str, query: str) -> list[dict[str, Any]]:
    token = access_token(candidate_id, "notion")
    response = requests.post(
        "https://api.notion.com/v1/search",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
        json={"query": query[:100], "page_size": 25},
        timeout=25,
    )
    if not response.ok:
        raise IntegrationApiError(f"Notion search failed: HTTP {response.status_code}: {response.text[:1000]}")
    data = response.json()
    return list(data.get("results") or [])


def google_summary(candidate_id: str) -> dict[str, Any]:
    token = access_token(candidate_id, "google")
    headers = {"Authorization": f"Bearer {token}"}
    me = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers, timeout=20)
    me.raise_for_status()
    profile = me.json()
    calendar = requests.get("https://www.googleapis.com/calendar/v3/calendars/primary/events", headers=headers, params={"maxResults": 10, "singleEvents": "true", "orderBy": "startTime", "timeMin": "1970-01-01T00:00:00Z"}, timeout=20)
    calendar.raise_for_status()
    drive = requests.get("https://www.googleapis.com/drive/v3/files", headers=headers, params={"pageSize": 10, "fields": "files(id,name,mimeType,modifiedTime,webViewLink)", "orderBy": "modifiedTime desc"}, timeout=20)
    drive.raise_for_status()
    return {"profile": profile, "upcoming_events": calendar.json().get("items", []), "recent_files": drive.json().get("files", [])}


def google_gmail_career_messages(candidate_id: str, max_results: int = 20) -> list[dict[str, Any]]:
    token = access_token(candidate_id, "google")
    headers = {"Authorization": f"Bearer {token}"}
    params = {"userId": "me", "maxResults": max_results, "q": '(interview OR recruiter OR "application" OR "next round" OR "offer" OR "rejection") newer_than:180d'}
    listing = requests.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", headers=headers, params=params, timeout=25)
    listing.raise_for_status()
    results: list[dict[str, Any]] = []
    for item in (listing.json().get("messages") or [])[:max_results]:
        detail = requests.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", headers=headers, params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]}, timeout=25)
        detail.raise_for_status()
        payload = detail.json().get("payload", {})
        headers_map = {str(h.get("name", "")).lower(): str(h.get("value", "")) for h in payload.get("headers", []) if isinstance(h, dict)}
        results.append({"id": item["id"], "thread_id": detail.json().get("threadId"), "subject": headers_map.get("subject", ""), "from": headers_map.get("from", ""), "date": headers_map.get("date", "")})
    return results


def google_contacts(candidate_id: str, page_size: int = 100) -> list[dict[str, Any]]:
    token = access_token(candidate_id, "google")
    response = requests.get("https://people.googleapis.com/v1/people/me/connections", headers={"Authorization": f"Bearer {token}"}, params={"pageSize": min(max(page_size, 1), 500), "personFields": "names,emailAddresses,organizations,urls"}, timeout=25)
    response.raise_for_status()
    return list(response.json().get("connections") or [])


def microsoft_summary(candidate_id: str) -> dict[str, Any]:
    token = access_token(candidate_id, "microsoft")
    headers = {"Authorization": f"Bearer {token}"}
    me = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers, params={"$select": "id,displayName,mail,userPrincipalName"}, timeout=20)
    me.raise_for_status()
    events = requests.get("https://graph.microsoft.com/v1.0/me/events", headers=headers, params={"$top": 10, "$orderby": "start/dateTime", "$select": "id,subject,start,end,webLink"}, timeout=20)
    events.raise_for_status()
    drive = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/children", headers=headers, params={"$top": 10, "$select": "id,name,lastModifiedDateTime,webUrl"}, timeout=20)
    drive.raise_for_status()
    return {"profile": me.json(), "upcoming_events": events.json().get("value", []), "recent_files": drive.json().get("value", [])}


def microsoft_career_messages(candidate_id: str, max_results: int = 20) -> list[dict[str, Any]]:
    token = access_token(candidate_id, "microsoft")
    response = requests.get("https://graph.microsoft.com/v1.0/me/messages", headers={"Authorization": f"Bearer {token}"}, params={"$top": max_results, "$orderby": "receivedDateTime desc", "$select": "id,subject,from,receivedDateTime,webLink,bodyPreview", "$filter": "receivedDateTime ge 1970-01-01T00:00:00Z"}, timeout=25)
    response.raise_for_status()
    items = []
    for message in response.json().get("value", []):
        text = f"{message.get('subject','')} {message.get('bodyPreview','')}".lower()
        if any(term in text for term in ("interview", "recruiter", "application", "next round", "offer", "rejection")):
            sender = (message.get("from") or {}).get("emailAddress") or {}
            items.append({"id": message.get("id"), "subject": message.get("subject", ""), "from": sender.get("address", ""), "date": message.get("receivedDateTime", ""), "web_link": message.get("webLink", ""), "preview": message.get("bodyPreview", "")[:500]})
    return items


def microsoft_contacts(candidate_id: str, max_results: int = 100) -> list[dict[str, Any]]:
    token = access_token(candidate_id, "microsoft")
    response = requests.get("https://graph.microsoft.com/v1.0/me/contacts", headers={"Authorization": f"Bearer {token}"}, params={"$top": min(max(max_results, 1), 1000), "$select": "id,displayName,emailAddresses,companyName,businessPhones"}, timeout=25)
    response.raise_for_status()
    return list(response.json().get("value") or [])


def github_profile(candidate_id: str) -> dict[str, Any]:
    token = access_token(candidate_id, "github")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2026-03-10"}
    me = requests.get("https://api.github.com/user", headers=headers, timeout=20)
    me.raise_for_status()
    repos = requests.get("https://api.github.com/user/repos", headers=headers, params={"per_page": 100, "sort": "updated", "direction": "desc"}, timeout=25)
    repos.raise_for_status()
    return {"profile": me.json(), "repositories": repos.json()}


def gitlab_profile(candidate_id: str) -> dict[str, Any]:
    token = access_token(candidate_id, "gitlab")
    headers = {"Authorization": f"Bearer {token}"}
    me = requests.get("https://gitlab.com/api/v4/user", headers=headers, timeout=20)
    me.raise_for_status()
    projects = requests.get("https://gitlab.com/api/v4/projects", headers=headers, params={"membership": "true", "per_page": 100, "simple": "true", "order_by": "last_activity_at"}, timeout=25)
    projects.raise_for_status()
    return {"profile": me.json(), "projects": projects.json()}


def normalize_message(item: dict[str, Any], source: str) -> dict[str, Any]:
    text = f"{item.get('subject', '')} {item.get('preview', '')}".casefold()
    if any(term in text for term in ("interview", "next round", "schedule")):
        kind = "interview"
    elif "offer" in text:
        kind = "offer"
    elif any(term in text for term in ("rejection", "not moving forward", "unfortunately")):
        kind = "rejection"
    elif any(term in text for term in ("application", "applied", "candidate")):
        kind = "application"
    elif "recruiter" in text:
        kind = "recruiter"
    else:
        kind = "career"
    return {**item, "source": source, "kind": kind}
