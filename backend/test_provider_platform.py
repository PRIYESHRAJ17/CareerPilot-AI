from typing import Any, Dict, List, Optional

import pytest

from backend.connectors.base import JobSource
from backend.connectors.registry import JobSourceRegistry
from backend.schemas.job import Job, Salary
from backend.services.deduplication import JobDeduplicator
from backend.services.job_aggregator import JobAggregator
from backend.services.provider_health import ProviderHealthService


class FakeJobSource(JobSource):
    """
    Deterministic provider for provider-platform tests.

    No network calls.
    No credentials.
    No external dependencies.
    """

    name = "fake_provider"
    display_name = "Fake Provider"
    category = "test"

    countries = ["IN"]

    requires_credentials = False
    credential_env_vars: List[str] = []

    supports_paging = True
    supports_remote_filter = True

    # Explicitly override the base-provider default.
    supports_salary_filter = True

    website = "https://example.com"
    api_url = "https://example.com/api"

    def __init__(
        self,
        *,
        jobs: Optional[List[Job]] = None,
        fail_search: bool = False,
        health_ok: bool = True,
    ) -> None:
        self.jobs = (
            jobs
            if jobs is not None
            else [
                Job(
                    source="fake_provider",
                    source_job_id="fake-1",
                    title="Backend Engineer",
                    company="Example Technologies",
                    location=["Bangalore"],
                    remote=False,
                    salary=Salary(
                        min_lpa=8.0,
                        max_lpa=12.0,
                        currency="INR",
                    ),
                    description=(
                        "Backend engineering role."
                    ),
                    apply_url=(
                        "https://example.com/jobs/fake-1"
                    ),
                    source_url=(
                        "https://example.com/jobs/fake-1"
                    ),
                )
            ]
        )

        self.fail_search = fail_search
        self.health_ok = health_ok

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:

        if self.fail_search:
            raise RuntimeError(
                "fake provider search failure"
            )

        return list(
            self.jobs[
                :max(
                    1,
                    int(limit),
                )
            ]
        )

    def health_check(
        self,
    ) -> Dict[str, Any]:

        return {
            "source": self.name,
            "healthy": self.health_ok,
            "status_code": (
                200
                if self.health_ok
                else 503
            ),
            "message": (
                "Fake provider healthy"
                if self.health_ok
                else "Fake provider unavailable"
            ),
        }

    def normalize(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:

        return Job(
            source=self.name,
            source_job_id=str(
                raw_job.get(
                    "id",
                    "",
                )
            ),
            title=str(
                raw_job.get(
                    "title",
                    "",
                )
            ),
            company=str(
                raw_job.get(
                    "company",
                    "Unknown",
                )
            ),
            location=list(
                raw_job.get(
                    "location",
                    [],
                )
                or []
            ),
            description=str(
                raw_job.get(
                    "description",
                    "",
                )
            ),
            apply_url=str(
                raw_job.get(
                    "apply_url",
                    "",
                )
            ),
            source_url=str(
                raw_job.get(
                    "source_url",
                    "",
                )
            ),
        )


class FailingJobSource(FakeJobSource):
    """
    Provider that intentionally fails searches.
    """

    name = "failing_provider"
    display_name = "Failing Provider"

    def __init__(self) -> None:
        super().__init__(
            fail_search=True
        )

        self.name = "failing_provider"
        self.display_name = "Failing Provider"


# ============================================================
# PROVIDER CONTRACT
# ============================================================


def test_provider_metadata_contract() -> None:
    source = FakeJobSource()

    assert source.name == "fake_provider"
    assert source.display_name == "Fake Provider"
    assert source.category == "test"
    assert source.countries == ["IN"]

    assert source.requires_credentials is False
    assert source.supports_paging is True
    assert source.supports_remote_filter is True
    assert source.supports_salary_filter is True

    metadata = source.metadata_dict()

    assert metadata["name"] == "fake_provider"
    assert metadata["display_name"] == "Fake Provider"
    assert metadata["category"] == "test"
    assert metadata["countries"] == ["IN"]
    assert metadata["requires_credentials"] is False
    assert metadata["supports_paging"] is True
    assert metadata["supports_remote_filter"] is True

    # Verify the metadata contract uses the provider's
    # capability rather than blindly assuming the base default.
    assert metadata["supports_salary_filter"] == (
        source.supports_salary_filter
    )

    assert metadata["website"] == (
        "https://example.com"
    )

    assert metadata["api_url"] == (
        "https://example.com/api"
    )


def test_provider_configuration_contract() -> None:
    source = FakeJobSource()

    source.validate_configuration()


def test_provider_normalization_enrichment_contract() -> None:
    source = FakeJobSource()

    job = source.normalize_and_enrich(
        {
            "id": "normalized-1",
            "title": "Backend Engineer",
            "company": "Example Technologies",
            "location": ["Bangalore"],
            "description": "Build APIs.",
            "apply_url": (
                "https://example.com/jobs/1"
            ),
            "source_url": (
                "https://example.com/jobs/1"
            ),
        }
    )

    assert isinstance(
        job,
        Job,
    )

    assert job.source == "fake_provider"

    assert job.metadata[
        "provider_name"
    ] == "fake_provider"

    assert job.metadata[
        "provider_display_name"
    ] == "Fake Provider"

    assert job.metadata[
        "provider_category"
    ] == "test"

    assert job.metadata[
        "provider_countries"
    ] == ["IN"]


# ============================================================
# REGISTRY
# ============================================================


def test_registry_registration_and_lookup() -> None:
    registry = JobSourceRegistry()

    source = FakeJobSource()

    registered = registry.register(
        source
    )

    assert registered is source
    assert registry.count() == 1

    assert registry.contains(
        "fake_provider"
    )

    assert registry.get(
        "fake_provider"
    ) is source

    assert registry.names() == [
        "fake_provider"
    ]


def test_registry_duplicate_protection() -> None:
    registry = JobSourceRegistry()

    registry.register(
        FakeJobSource()
    )

    with pytest.raises(
        ValueError,
        match="already registered",
    ):
        registry.register(
            FakeJobSource()
        )


def test_registry_filtering_and_summary() -> None:
    registry = JobSourceRegistry()

    source = FakeJobSource()

    registry.register(
        source
    )

    assert registry.by_country(
        "in"
    ) == [source]

    assert registry.by_category(
        "TEST"
    ) == [source]

    summary = registry.summary()

    assert summary[
        "provider_count"
    ] == 1

    assert summary[
        "provider_names"
    ] == [
        "fake_provider"
    ]

    assert "test" in summary[
        "categories"
    ]

    assert "IN" in summary[
        "countries"
    ]


# ============================================================
# HEALTH
# ============================================================


def test_provider_health_service_live_check() -> None:
    registry = JobSourceRegistry()

    source = FakeJobSource()

    registry.register(
        source
    )

    health = ProviderHealthService(
        registry
    )

    result = health.check(
        "fake_provider"
    )

    assert result.healthy is True
    assert result.state == "healthy"
    assert result.total_checks == 1
    assert result.successful_checks == 1
    assert result.failed_checks == 0

    assert (
        result.consecutive_failures
        == 0
    )


def test_provider_health_service_failure_recovery() -> None:
    registry = JobSourceRegistry()

    source = FakeJobSource()

    registry.register(
        source
    )

    health = ProviderHealthService(
        registry
    )

    failed = health.record_search_failure(
        "fake_provider",
        error="temporary failure",
        latency_ms=125.0,
    )

    assert failed.failed_searches == 1

    assert (
        failed.consecutive_search_failures
        == 1
    )

    assert failed.state == "degraded"

    recovered = health.record_search_success(
        "fake_provider",
        jobs_returned=7,
        latency_ms=75.0,
    )

    assert recovered.successful_searches == 1

    assert (
        recovered.consecutive_search_failures
        == 0
    )

    assert recovered.total_jobs_returned == 7
    assert recovered.state == "healthy"


# ============================================================
# AGGREGATOR
# ============================================================


def test_aggregator_isolates_provider_failure() -> None:
    registry = JobSourceRegistry()

    healthy = FakeJobSource()
    failing = FailingJobSource()

    registry.register_many(
        [
            healthy,
            failing,
        ]
    )

    aggregator = JobAggregator(
        registry=registry
    )

    jobs = aggregator.search(
        query="backend engineer",
        location="Bangalore",
        limit_per_source=5,
    )

    assert len(jobs) == 1
    assert jobs[0].source == "fake_provider"

    summary = aggregator.health_summary()

    assert summary[
        "provider_count"
    ] == 2

    assert "fake_provider" in (
        summary[
            "healthy_sources"
        ]
    )

    assert "failing_provider" in (
        summary[
            "degraded_sources"
        ]
    )


def test_aggregator_same_source_deduplication() -> None:
    duplicate_a = Job(
        source="fake_provider",
        source_job_id="same-id",
        title="Backend Engineer",
        company="Example Technologies",
        location=["Bangalore"],
    )

    duplicate_b = Job(
        source="fake_provider",
        source_job_id="same-id",
        title="Backend Engineer",
        company="Example Technologies",
        location=["Bangalore"],
    )

    source = FakeJobSource(
        jobs=[
            duplicate_a,
            duplicate_b,
        ]
    )

    registry = JobSourceRegistry()

    registry.register(
        source
    )

    aggregator = JobAggregator(
        registry=registry
    )

    jobs = aggregator.search(
        query="backend engineer"
    )

    assert len(jobs) == 1


# ============================================================
# CROSS-SOURCE DEDUPLICATION
# ============================================================


def test_cross_source_deduplication_preserves_provenance() -> None:
    first = Job(
        source="fake_provider",
        source_job_id="a-1",
        title="Software Engineer",
        company="Acme Technologies Pvt Ltd",
        location=["Bengaluru"],
        description=(
            "Build backend systems and APIs."
        ),
        apply_url=(
            "https://example.com/jobs/backend"
        ),
        source_url=(
            "https://example.com/jobs/backend"
        ),
        salary=Salary(
            min_lpa=8.0,
            max_lpa=12.0,
        ),
    )

    second = Job(
        source="second_provider",
        source_job_id="b-1",
        title="Software Development Engineer",
        company="Acme Technologies",
        location=["Bangalore"],
        description=(
            "Develop backend systems."
        ),
        apply_url=(
            "https://example.com/jobs/backend"
            "?utm_source=jooble"
        ),
        source_url=(
            "https://example.com/jobs/backend"
            "?utm_source=jooble"
        ),
        salary=Salary(
            min_lpa=8.0,
            max_lpa=12.0,
        ),
    )

    deduplicator = JobDeduplicator()

    canonical = deduplicator.deduplicate(
        [
            first,
            second,
        ]
    )

    assert len(canonical) == 1

    job = canonical[0]

    assert job.metadata[
        "source_count"
    ] == 2

    assert set(
        job.sources
    ) == {
        "fake_provider",
        "second_provider",
    }

    assert len(
        job.source_records
    ) == 2

    assert job.metadata[
        "canonical_job_id"
    ].startswith(
        "job-"
    )