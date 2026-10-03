from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import requests

from backend.services.integration_store import get_connection, save_connection


@dataclass(frozen=True)
class OAuthConfig:
    provider: str
    client_id_env: str
    client_secret_env: str
    authorize_url: str
    token_url: str
    scopes: tuple[str, ...]
    redirect_path: str
    supports_pkce: bool = False
    extra_authorize: tuple[tuple[str, str], ...] = ()


CONFIGS: dict[str, OAuthConfig] = {
    "notion": OAuthConfig(
        provider="notion",
        client_id_env="NOTION_CLIENT_ID",
        client_secret_env="NOTION_CLIENT_SECRET",
        authorize_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        scopes=(),
        redirect_path="/integrations/oauth/notion/callback",
    ),
    "google": OAuthConfig(
        provider="google",
        client_id_env="GOOGLE_CLIENT_ID",
        client_secret_env="GOOGLE_CLIENT_SECRET",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=(
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
            "https://www.googleapis.com/auth/contacts.readonly",
        ),
        redirect_path="/integrations/oauth/google/callback",
        supports_pkce=True,
        extra_authorize=(("access_type", "offline"), ("prompt", "consent")),
    ),
    "microsoft": OAuthConfig(
        provider="microsoft",
        client_id_env="MICROSOFT_CLIENT_ID",
        client_secret_env="MICROSOFT_CLIENT_SECRET",
        authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scopes=(
            "openid",
            "profile",
            "email",
            "offline_access",
            "User.Read",
            "Mail.Read",
            "Calendars.Read",
            "Files.Read",
            "Contacts.Read",
        ),
        redirect_path="/integrations/oauth/microsoft/callback",
        supports_pkce=True,
    ),
    "github": OAuthConfig(
        provider="github",
        client_id_env="GITHUB_OAUTH_CLIENT_ID",
        client_secret_env="GITHUB_OAUTH_CLIENT_SECRET",
        authorize_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scopes=("read:user", "user:email"),
        redirect_path="/integrations/oauth/github/callback",
    ),
    "gitlab": OAuthConfig(
        provider="gitlab",
        client_id_env="GITLAB_CLIENT_ID",
        client_secret_env="GITLAB_CLIENT_SECRET",
        authorize_url="https://gitlab.com/oauth/authorize",
        token_url="https://gitlab.com/oauth/token",
        scopes=("read_user", "read_api", "read_repository"),
        redirect_path="/integrations/oauth/gitlab/callback",
    ),
}


def public_api_url() -> str:
    return os.getenv("CAREERPILOT_API_PUBLIC_URL", "http://localhost:8000").rstrip("/")


def public_frontend_url() -> str:
    return os.getenv("CAREERPILOT_FRONTEND_PUBLIC_URL", "http://localhost:3000").rstrip("/")


def redirect_uri(provider: str) -> str:
    return public_api_url() + CONFIGS[provider].redirect_path


def configured(provider: str) -> bool:
    config = CONFIGS[provider]
    return bool(os.getenv(config.client_id_env) and os.getenv(config.client_secret_env))


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


def authorization_url(provider: str, *, state: str, code_verifier: str | None = None) -> str:
    config = CONFIGS[provider]
    client_id = os.getenv(config.client_id_env, "").strip()
    if not client_id:
        raise RuntimeError(f"{config.client_id_env} is not configured.")
    params: dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri(provider),
        "response_type": "code",
        "state": state,
    }
    if config.scopes:
        params["scope"] = " ".join(config.scopes)
    for key, value in config.extra_authorize:
        params[key] = value
    if provider == "notion":
        params["owner"] = "user"
    if config.supports_pkce and code_verifier:
        _, challenge = base64_pkce(code_verifier)
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
    return f"{config.authorize_url}?{urlencode(params)}"


def base64_pkce(verifier: str) -> tuple[str, str]:
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _extract_expires_at(expires_in: Any) -> str | None:
    try:
        seconds = int(float(expires_in))
    except (TypeError, ValueError):
        return None
    return (datetime.now(timezone.utc) + timedelta(seconds=max(0, seconds))).isoformat()


def _exchange_oauth_code(provider: str, code: str, *, code_verifier: str | None) -> dict[str, Any]:
    config = CONFIGS[provider]
    client_id = os.getenv(config.client_id_env, "").strip()
    client_secret = os.getenv(config.client_secret_env, "").strip()
    if not client_id or not client_secret:
        raise RuntimeError(f"{config.client_id_env} / {config.client_secret_env} are not configured.")

    redirect = redirect_uri(provider)
    if provider == "notion":
        payload = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect}
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
        response = requests.post(
            config.token_url,
            json=payload,
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/json"},
            timeout=20,
        )
    elif provider in {"google", "microsoft"}:
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect,
            "grant_type": "authorization_code",
        }
        if provider == "microsoft":
            payload["scope"] = " ".join(config.scopes)
        if code_verifier:
            payload["code_verifier"] = code_verifier
        response = requests.post(config.token_url, data=payload, timeout=20)
    else:
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect,
        }
        headers = {"Accept": "application/json"}
        if provider == "gitlab":
            payload["grant_type"] = "authorization_code"
        response = requests.post(config.token_url, data=payload, headers=headers, timeout=20)

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:1000]
        raise RuntimeError(f"{provider} OAuth token exchange failed: {detail}") from exc
    data = response.json()
    if not isinstance(data, dict) or not data.get("access_token"):
        raise RuntimeError(f"{provider} OAuth response did not contain an access token.")
    return data


def complete_oauth(
    provider: str,
    candidate_id: str,
    code: str,
    code_verifier: str | None,
) -> dict[str, Any]:
    token = _exchange_oauth_code(provider, code, code_verifier=code_verifier)
    expires_at = _extract_expires_at(token.get("expires_in"))
    metadata = {key: token.get(key) for key in ("workspace_name", "workspace_id", "bot_id", "owner", "scope", "refresh_token_expires_in") if token.get(key) is not None}
    save_connection(
        candidate_id,
        provider,
        access_token=str(token.get("access_token")),
        refresh_token=str(token.get("refresh_token")) if token.get("refresh_token") else None,
        expires_at=expires_at,
        scope=str(token.get("scope") or token.get("scopes") or " ".join(CONFIGS[provider].scopes)),
        metadata=metadata,
    )
    return {"provider": provider, "expires_at": expires_at, "metadata": metadata}


def _refresh_google(connection: dict[str, Any]) -> dict[str, Any]:
    refresh = connection.get("refresh_token")
    if not refresh:
        return connection
    config = CONFIGS["google"]
    response = requests.post(
        config.token_url,
        data={
            "client_id": os.getenv(config.client_id_env, ""),
            "client_secret": os.getenv(config.client_secret_env, ""),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    response.raise_for_status()
    token = response.json()
    access = token.get("access_token")
    if access:
        save_connection(
            connection["candidate_id"],
            "google",
            access_token=access,
            refresh_token=refresh,
            expires_at=_extract_expires_at(token.get("expires_in")),
            scope=connection.get("scope"),
            metadata=connection.get("metadata") or {},
        )
        return get_connection(connection["candidate_id"], "google") or connection
    return connection


def _refresh_notion(connection: dict[str, Any]) -> dict[str, Any]:
    refresh = connection.get("refresh_token")
    if not refresh:
        return connection
    config = CONFIGS["notion"]
    client_id = os.getenv(config.client_id_env, "")
    client_secret = os.getenv(config.client_secret_env, "")
    if not client_id or not client_secret:
        return connection
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    response = requests.post(
        config.token_url,
        json={"grant_type": "refresh_token", "refresh_token": refresh},
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    token = response.json()
    access = token.get("access_token")
    if access:
        save_connection(
            connection["candidate_id"],
            "notion",
            access_token=access,
            refresh_token=str(token.get("refresh_token") or refresh),
            expires_at=_extract_expires_at(token.get("expires_in")),
            scope=token.get("scope") or connection.get("scope"),
            metadata=connection.get("metadata") or {},
        )
        return get_connection(connection["candidate_id"], "notion") or connection
    return connection


def _refresh_gitlab(connection: dict[str, Any]) -> dict[str, Any]:
    refresh = connection.get("refresh_token")
    if not refresh:
        return connection
    config = CONFIGS["gitlab"]
    response = requests.post(
        config.token_url,
        data={
            "client_id": os.getenv(config.client_id_env, ""),
            "client_secret": os.getenv(config.client_secret_env, ""),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
            "redirect_uri": redirect_uri("gitlab"),
        },
        headers={"Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    token = response.json()
    access = token.get("access_token")
    if access:
        save_connection(
            connection["candidate_id"],
            "gitlab",
            access_token=access,
            refresh_token=str(token.get("refresh_token") or refresh),
            expires_at=_extract_expires_at(token.get("expires_in")),
            scope=token.get("scope") or connection.get("scope"),
            metadata=connection.get("metadata") or {},
        )
        return get_connection(connection["candidate_id"], "gitlab") or connection
    return connection


def _refresh_microsoft(connection: dict[str, Any]) -> dict[str, Any]:
    refresh = connection.get("refresh_token")
    if not refresh:
        return connection
    config = CONFIGS["microsoft"]
    response = requests.post(
        config.token_url,
        data={
            "client_id": os.getenv(config.client_id_env, ""),
            "client_secret": os.getenv(config.client_secret_env, ""),
            "refresh_token": refresh,
            "grant_type": "refresh_token",
            "scope": " ".join(config.scopes),
        },
        timeout=20,
    )
    response.raise_for_status()
    token = response.json()
    access = token.get("access_token")
    if access:
        save_connection(
            connection["candidate_id"],
            "microsoft",
            access_token=access,
            refresh_token=str(token.get("refresh_token") or refresh),
            expires_at=_extract_expires_at(token.get("expires_in")),
            scope=token.get("scope") or connection.get("scope"),
            metadata=connection.get("metadata") or {},
        )
        return get_connection(connection["candidate_id"], "microsoft") or connection
    return connection


def access_token(candidate_id: str, provider: str) -> str:
    connection = get_connection(candidate_id, provider)
    if not connection or not connection.get("access_token"):
        raise RuntimeError(f"{provider} is not connected for this CareerPilot account.")
    expires_at = connection.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(str(expires_at))
            if expiry <= datetime.now(timezone.utc) + timedelta(seconds=60):
                if provider == "notion":
                    connection = _refresh_notion(connection)
                elif provider == "google":
                    connection = _refresh_google(connection)
                elif provider == "microsoft":
                    connection = _refresh_microsoft(connection)
                elif provider == "gitlab":
                    connection = _refresh_gitlab(connection)
        except ValueError:
            pass
    token = connection.get("access_token")
    if not token:
        raise RuntimeError(f"{provider} access token is unavailable.")
    return str(token)
