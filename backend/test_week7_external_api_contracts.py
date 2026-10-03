from __future__ import annotations

from unittest.mock import Mock, patch

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
from backend.services.integration_store import create_clipper_token, revoke_clipper_tokens, verify_clipper_token


def response(payload: dict) -> Mock:
    r = Mock(); r.ok = True; r.status_code = 200; r.json.return_value = payload; r.text = ""; r.raise_for_status.return_value = None
    return r


def test_notion_create_and_search_contracts() -> None:
    create_response = response({"id": "page-1", "object": "page"})
    search_response = response({"results": [{"id": "page-1"}]})
    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.post", side_effect=[create_response, search_response]
    ) as post, patch("backend.services.external_integrations.requests.patch", return_value=response({})) as patch_call:
        page = notion_create_note("candidate", title="Career note", markdown="line one\nline two", parent_page_id="12345678123456781234567812345678")
        results = notion_search("candidate", "career")
    assert page["id"] == "page-1"
    assert results == [{"id": "page-1"}]
    assert post.call_count == 2
    patch_call.assert_called_once()


def test_google_contracts_are_scoped_to_read_sync() -> None:
    responses = [
        response({"sub": "u1"}),
        response({"items": [{"id": "event-1"}]}),
        response({"files": [{"id": "file-1"}]}),
    ]
    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", side_effect=responses
    ):
        summary = google_summary("candidate")
    assert summary["upcoming_events"][0]["id"] == "event-1"
    assert summary["recent_files"][0]["id"] == "file-1"

    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get",
        side_effect=[response({"messages": [{"id": "m1"}]}), response({"threadId": "t1", "payload": {"headers": [{"name": "Subject", "value": "Interview"}, {"name": "From", "value": "recruiter@example.com"}, {"name": "Date", "value": "today"}]}})],
    ):
        messages = google_gmail_career_messages("candidate")
    assert messages[0]["subject"] == "Interview"

    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", return_value=response({"connections": [{"resourceName": "people/1"}]})
    ):
        contacts = google_contacts("candidate")
    assert contacts[0]["resourceName"] == "people/1"


def test_microsoft_contracts() -> None:
    responses = [
        response({"id": "u1"}),
        response({"value": [{"id": "event-1"}]}),
        response({"value": [{"id": "file-1"}]}),
    ]
    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", side_effect=responses
    ):
        summary = microsoft_summary("candidate")
    assert summary["upcoming_events"][0]["id"] == "event-1"
    assert summary["recent_files"][0]["id"] == "file-1"

    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", return_value=response({"value": [{"id": "c1", "displayName": "A"}]})
    ):
        contacts = microsoft_contacts("candidate")
    assert contacts[0]["id"] == "c1"

    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", return_value=response({"value": [{"id": "m1", "subject": "Interview next round", "bodyPreview": "Schedule", "from": {"emailAddress": {"address": "r@example.com"}}, "receivedDateTime": "today", "webLink": "https://outlook.example/m1"}]})
    ):
        messages = microsoft_career_messages("candidate")
    assert messages[0]["id"] == "m1"


def test_github_gitlab_profile_contracts() -> None:
    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", side_effect=[response({"login": "user"}), response([{"id": 1, "name": "repo"}])]
    ):
        github = github_profile("candidate")
    assert github["profile"]["login"] == "user"
    assert github["repositories"][0]["id"] == 1

    with patch("backend.services.external_integrations.access_token", return_value="token"), patch(
        "backend.services.external_integrations.requests.get", side_effect=[response({"username": "user"}), response([{"id": 2, "name": "project"}])]
    ):
        gitlab = gitlab_profile("candidate")
    assert gitlab["profile"]["username"] == "user"
    assert gitlab["projects"][0]["id"] == 2


def test_browser_clipper_token_is_revocable() -> None:
    candidate = "00000000-0000-0000-0000-000000000001"
    revoke_clipper_tokens(candidate)
    token = create_clipper_token(candidate)
    assert verify_clipper_token(token) == candidate
    revoke_clipper_tokens(candidate)
    assert verify_clipper_token(token) is None
