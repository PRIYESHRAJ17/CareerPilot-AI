from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import backend.services.oauth_integrations as oauth


def test_all_external_oauth_configs_have_required_routes_and_scopes() -> None:
    assert set(oauth.CONFIGS) == {"notion", "google", "microsoft", "github", "gitlab"}
    assert "https://www.googleapis.com/auth/drive.metadata.readonly" in oauth.CONFIGS["google"].scopes
    assert "Mail.Read" in oauth.CONFIGS["microsoft"].scopes
    assert "read_api" in oauth.CONFIGS["gitlab"].scopes


def test_notion_authorization_url_is_csrf_bound_and_user_owned() -> None:
    with patch.dict("os.environ", {"NOTION_CLIENT_ID": "cid"}):
        url = oauth.authorization_url("notion", state="abc123")
    assert "state=abc123" in url
    assert "owner=user" in url
    assert "response_type=code" in url


def test_notion_refresh_rotates_tokens() -> None:
    connection = {
        "candidate_id": "candidate-1",
        "refresh_token": "refresh-old",
        "access_token": "access-old",
    }
    response = Mock()
    response.json.return_value = {"access_token": "access-new", "refresh_token": "refresh-new", "expires_in": 3600}
    response.raise_for_status.return_value = None
    with patch.dict("os.environ", {"NOTION_CLIENT_ID": "cid", "NOTION_CLIENT_SECRET": "secret"}), patch(
        "backend.services.oauth_integrations.requests.post", return_value=response
    ) as post, patch(
        "backend.services.oauth_integrations.save_connection"
    ) as save, patch(
        "backend.services.oauth_integrations.get_connection", return_value={**connection, "access_token": "access-new", "refresh_token": "refresh-new"}
    ):
        result = oauth._refresh_notion(connection)
    assert result["access_token"] == "access-new"
    assert result["refresh_token"] == "refresh-new"
    post.assert_called_once()
    save.assert_called_once()


def test_gitlab_refresh_rotates_tokens() -> None:
    connection = {
        "candidate_id": "candidate-1",
        "refresh_token": "refresh-old",
        "access_token": "access-old",
    }
    response = Mock()
    response.json.return_value = {"access_token": "access-new", "refresh_token": "refresh-new", "expires_in": 7200}
    response.raise_for_status.return_value = None
    with patch.dict("os.environ", {"GITLAB_CLIENT_ID": "cid", "GITLAB_CLIENT_SECRET": "secret"}), patch(
        "backend.services.oauth_integrations.requests.post", return_value=response
    ) as post, patch(
        "backend.services.oauth_integrations.save_connection"
    ) as save, patch(
        "backend.services.oauth_integrations.get_connection", return_value={**connection, "access_token": "access-new", "refresh_token": "refresh-new"}
    ):
        result = oauth._refresh_gitlab(connection)
    assert result["access_token"] == "access-new"
    assert result["refresh_token"] == "refresh-new"
    post.assert_called_once()
    save.assert_called_once()
