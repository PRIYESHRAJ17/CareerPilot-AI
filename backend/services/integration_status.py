from __future__ import annotations

import os
from typing import Any

from backend.services.integration_store import list_connections
from backend.services.oauth_integrations import CONFIGS, configured


def status_for_candidate(candidate_id: str) -> list[dict[str, Any]]:
    existing = {item["provider"]: item for item in list_connections(candidate_id)}
    result = []
    display = {
        "notion": "Notion",
        "google": "Google Workspace",
        "microsoft": "Microsoft 365",
        "github": "GitHub",
        "gitlab": "GitLab",
    }
    descriptions = {
        "notion": "Save jobs, research, notes and plans into the user's Notion workspace.",
        "google": "Gmail, Calendar, Drive and Contacts for career workflow automation.",
        "microsoft": "Outlook Mail, Calendar, OneDrive and Contacts through Microsoft Graph.",
        "github": "Career evidence from repositories, profile and technical activity.",
        "gitlab": "Career evidence from projects and GitLab profile activity.",
    }
    for provider in CONFIGS:
        result.append({
            "provider": provider,
            "display_name": display[provider],
            "description": descriptions[provider],
            "configured": configured(provider),
            "connected": provider in existing,
            "updated_at": existing.get(provider, {}).get("updated_at"),
            "scope": existing.get(provider, {}).get("scope"),
        })
    return result


def setup_status() -> dict[str, Any]:
    return {
        "api_public_url": os.getenv("CAREERPILOT_API_PUBLIC_URL", "http://localhost:8000"),
        "frontend_public_url": os.getenv("CAREERPILOT_FRONTEND_PUBLIC_URL", "http://localhost:3000"),
        "token_encryption_configured": bool(os.getenv("CAREERPILOT_TOKEN_ENCRYPTION_KEY")),
        "job_api_credentials": {
            "adzuna": bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY")),
            "jooble": bool(os.getenv("JOOBLE_API_KEY")),
            "usajobs": bool(os.getenv("USAJOBS_API_KEY") and os.getenv("USAJOBS_USER_AGENT")),
            "the_muse": True,
        },
    }
