from backend.connectors.generic_rss import (
    GenericRssJobSource,
)
from backend.connectors.public_ats import (
    PublicAtsJobSource,
)
from backend.schemas.provider_fleet import (
    ProviderDefinition,
)


def test_rss_adapter_metadata() -> None:
    definition = ProviderDefinition(
        name="test_rss",
        display_name="Test RSS",
        adapter_type="rss",
        endpoint="https://example.com/jobs.rss",
        category="remote_job_board",
        remote_default=True,
    )

    source = GenericRssJobSource(
        definition
    )

    metadata = source.metadata_dict()

    assert metadata["name"] == "test_rss"
    assert metadata["supports_paging"] is True


def test_rss_adapter_normalization() -> None:
    definition = ProviderDefinition(
        name="test_rss",
        display_name="Test RSS",
        adapter_type="rss",
        endpoint="https://example.com/jobs.rss",
        remote_default=True,
    )

    source = GenericRssJobSource(
        definition
    )

    job = source.normalize_and_enrich(
        {
            "title": "Backend Engineer",
            "description": (
                "Company: Example Technologies\n"
                "Location: Bangalore\n"
                "Remote backend role."
            ),
            "link": (
                "https://example.com/jobs/backend"
            ),
            "guid": "rss-001",
            "published": "2026-09-27T10:00:00Z",
            "author": "Example Technologies",
            "category": "Engineering",
        }
    )

    assert job.source == "test_rss"
    assert job.source_job_id == "rss-001"
    assert job.title == "Backend Engineer"
    assert job.company == "Example Technologies"
    assert job.remote is True

    assert job.metadata[
        "provider_name"
    ] == "test_rss"


def test_greenhouse_adapter_contract() -> None:
    definition = ProviderDefinition(
        name="greenhouse_example",
        display_name="Greenhouse Example",
        adapter_type="ats_public",
        endpoint="unused",
        adapter_config={
            "platform": "greenhouse",
            "board": "example",
        },
    )

    source = PublicAtsJobSource(
        definition
    )

    job = source.normalize(
        {
            "id": 123,
            "title": "Software Engineer",
            "location": {
                "name": "New York, NY"
            },
            "content": "Build systems.",
            "absolute_url": (
                "https://boards.greenhouse.io/"
                "example/jobs/123"
            ),
            "departments": [
                {
                    "name": "Engineering"
                }
            ],
        }
    )

    assert job.source == (
        "greenhouse_example"
    )

    assert job.source_job_id == "123"
    assert job.title == "Software Engineer"
    assert job.company == "example"

    assert job.location == [
        "New York, NY"
    ]

    assert job.apply_url.startswith(
        "https://boards.greenhouse.io/"
    )


def test_lever_adapter_contract() -> None:
    definition = ProviderDefinition(
        name="lever_example",
        display_name="Lever Example",
        adapter_type="ats_public",
        endpoint="unused",
        adapter_config={
            "platform": "lever",
            "board": "example",
        },
    )

    source = PublicAtsJobSource(
        definition
    )

    job = source.normalize(
        {
            "id": "lever-123",
            "text": "Backend Engineer",
            "categories": {
                "location": "Remote",
                "allLocations": [
                    "Remote",
                ],
                "commitment": "Fulltime",
                "team": "Engineering",
                "department": "Technology",
                "level": "Mid",
            },
            "workplaceType": "remote",
            "descriptionPlain": (
                "Build backend systems."
            ),
            "hostedUrl": (
                "https://jobs.lever.co/"
                "example/lever-123"
            ),
            "applyUrl": (
                "https://jobs.lever.co/"
                "example/lever-123/apply"
            ),
        }
    )

    assert job.source == (
        "lever_example"
    )

    assert job.title == "Backend Engineer"
    assert job.company == "example"
    assert job.remote is True

    assert job.location == [
        "Remote"
    ]


def test_ashby_adapter_contract() -> None:
    definition = ProviderDefinition(
        name="ashby_example",
        display_name="Ashby Example",
        adapter_type="ats_public",
        endpoint="unused",
        adapter_config={
            "platform": "ashby",
            "board": "example",
        },
    )

    source = PublicAtsJobSource(
        definition
    )

    job = source.normalize(
        {
            "title": "Platform Engineer",
            "location": "San Francisco, CA",
            "secondaryLocations": [
                {
                    "location": "Remote"
                }
            ],
            "jobUrl": (
                "https://jobs.ashbyhq.com/"
                "example/123"
            ),
            "descriptionPlain": (
                "Build platform infrastructure."
            ),
            "compensation": {
                "min": 120000,
                "max": 160000,
                "currency": "USD",
            },
        }
    )

    assert job.source == (
        "ashby_example"
    )

    assert job.title == (
        "Platform Engineer"
    )

    assert job.company == "example"

    assert job.location == [
        "San Francisco, CA",
        "Remote",
    ]

    assert job.salary.min_lpa == 120000
    assert job.salary.max_lpa == 160000