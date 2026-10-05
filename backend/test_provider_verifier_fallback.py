from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from backend.services.provider_verifier import (
    ProviderFleetVerifier,
    ProviderVerificationState,
)


def make_definition():
    return SimpleNamespace(
        name="fallback_live",
        display_name="Fallback Live",
        adapter_type="json",
    )


class FallbackSource:
    name = "fallback_live"
    display_name = "Fallback Live"
    category = "test"
    requires_credentials = False
    credential_env_vars = []

    def validate_configuration(self):
        return True

    def health_check(self):
        return {"healthy": True, "status": "healthy"}

    def search(self, query, location, limit=5):
        if query == "software engineer" and location == "remote":
            return []
        return [{
            "title": "Engineer",
            "company": "CareerPilot Test",
            "location": ["New York"],
            "url": "https://example.com/jobs/fallback",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"provider_name": "fallback_live"},
        }]

    def normalize(self, item):
        return item


class FakeFleet:
    def build_source(self, definition):
        return FallbackSource()

    def list_definitions(self):
        return [make_definition()]


def test_verifier_uses_broader_search_when_primary_is_empty():
    verifier = ProviderFleetVerifier(
        FakeFleet(),
        query="software engineer",
        location="remote",
    )

    result = verifier.verify(make_definition())

    assert result.state is ProviderVerificationState.LIVE
    assert result.jobs_returned == 1
    assert result.evidence["search"]["query"] == "engineer"
    assert result.evidence["search"]["location"] == ""
    assert len(result.evidence["search"]["attempts"]) >= 2
