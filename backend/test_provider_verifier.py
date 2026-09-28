from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from backend.schemas.job import (
    Experience,
    Job,
    Salary,
)
from backend.services.provider_verifier import (
    ProviderFleetVerifier,
    ProviderVerificationState,
)


def make_definition():
    return SimpleNamespace(
        name="fake_live",
        display_name="Fake Live",
        adapter_type="json",
    )


class FakeSource:
    name = "fake_live"
    display_name = "Fake Live"
    category = "test"

    requires_credentials = False
    credential_env_vars = []

    def validate_configuration(self):
        return True

    def health_check(self):
        return {
            "healthy": True,
            "status": "healthy",
        }

    def search(
        self,
        query,
        location,
        limit=5,
    ):
        now = datetime.now(
            timezone.utc
        ).isoformat()

        return [
            {
                "title": "Software Engineer",
                "company": "CareerPilot Test",
                "location": location,
                "url": (
                    "https://example.com/jobs/1"
                ),
                "posted_at": now,
                "metadata": {
                    "provider_name": (
                        "fake_live"
                    ),
                },
            }
        ]

    def normalize(self, item):
        return item


class CanonicalJobSource(FakeSource):
    def search(
        self,
        query,
        location,
        limit=5,
    ):
        now = datetime.now(
            timezone.utc
        )

        return [
            Job(
                source="fake_live",
                source_job_id="canonical-1",
                title="Software Engineer",
                company="CareerPilot Test",
                location=[location],
                remote=True,
                employment_type=None,
                experience=Experience(),
                salary=Salary(
                    currency="USD"
                ),
                skills=[
                    "backend"
                ],
                description=(
                    "Software engineer "
                    "backend position"
                ),
                apply_url=(
                    "https://example.com/"
                    "jobs/canonical-1"
                ),
                source_url=(
                    "https://example.com/"
                    "jobs/canonical-1"
                ),
                posted_at=now,
                metadata={
                    "provider_name": (
                        "fake_live"
                    )
                },
            )
        ]

    def normalize(self, item):
        raise AssertionError(
            "Canonical Job was incorrectly "
            "passed to normalize()."
        )


class EmptySource(FakeSource):
    def search(
        self,
        query,
        location,
        limit=5,
    ):
        return []


class NoProvenanceSource(FakeSource):
    def search(
        self,
        query,
        location,
        limit=5,
    ):
        now = datetime.now(
            timezone.utc
        ).isoformat()

        return [
            {
                "title": "Software Engineer",
                "company": "CareerPilot Test",
                "location": location,
                "url": (
                    "https://example.com/jobs/2"
                ),
                "posted_at": now,
                "metadata": {},
            }
        ]


class StaleSource(FakeSource):
    def search(
        self,
        query,
        location,
        limit=5,
    ):
        stale = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=500
            )
        ).isoformat()

        return [
            {
                "title": "Software Engineer",
                "company": "CareerPilot Test",
                "location": location,
                "url": (
                    "https://example.com/jobs/3"
                ),
                "posted_at": stale,
                "metadata": {
                    "provider_name": (
                        "fake_live"
                    ),
                },
            }
        ]


class FakeFleet:
    def __init__(self, source):
        self.source = source

    def build_source(
        self,
        definition,
    ):
        return self.source

    def list_definitions(self):
        return [
            make_definition()
        ]


def test_live_provider_requires_real_job_and_evidence():
    verifier = ProviderFleetVerifier(
        FakeFleet(
            FakeSource()
        ),
        query="software engineer",
        location="remote",
    )

    result = verifier.verify(
        make_definition()
    )

    assert (
        result.state
        is ProviderVerificationState.LIVE
    )

    assert result.configuration_ok is True
    assert result.health_ok is True
    assert result.search_ok is True

    assert result.jobs_returned == 1
    assert result.jobs_normalized == 1
    assert result.jobs_with_provenance == 1
    assert result.jobs_with_url == 1
    assert result.fresh_jobs == 1


def test_canonical_jobs_are_not_normalized_twice():
    verifier = ProviderFleetVerifier(
        FakeFleet(
            CanonicalJobSource()
        ),
        query="software engineer",
        location="remote",
    )

    result = verifier.verify(
        make_definition()
    )

    assert (
        result.state
        is ProviderVerificationState.LIVE
    )

    assert result.jobs_returned == 1
    assert result.jobs_normalized == 1

    normalization = (
        result.evidence[
            "normalization"
        ]
    )

    assert (
        normalization[
            "canonical_jobs_reused"
        ]
        == 1
    )

    assert (
        normalization["errors"]
        == 0
    )


def test_empty_provider_is_not_live():
    verifier = ProviderFleetVerifier(
        FakeFleet(
            EmptySource()
        )
    )

    result = verifier.verify(
        make_definition()
    )

    assert (
        result.state
        is ProviderVerificationState.DEGRADED
    )

    assert result.jobs_returned == 0
    assert result.jobs_normalized == 0


def test_missing_provenance_rejects_provider():
    verifier = ProviderFleetVerifier(
        FakeFleet(
            NoProvenanceSource()
        )
    )

    result = verifier.verify(
        make_definition()
    )

    assert (
        result.state
        is ProviderVerificationState.REJECTED
    )

    assert result.jobs_normalized == 1
    assert result.jobs_with_provenance == 0


def test_stale_provider_is_degraded():
    verifier = ProviderFleetVerifier(
        FakeFleet(
            StaleSource()
        ),
        freshness_days=180,
    )

    result = verifier.verify(
        make_definition()
    )

    assert (
        result.state
        is ProviderVerificationState.DEGRADED
    )

    assert result.fresh_jobs == 0