from __future__ import annotations

from unittest.mock import Mock

from backend.connectors.themuse import TheMuseConnector
from backend.connectors.usajobs import USAJobsConnector
from backend.services.learning_hub import recommendations
from backend.services.external_integrations import normalize_message


def test_the_muse_normalization() -> None:
    connector = TheMuseConnector()
    job = connector.normalize(
        {
            "id": 42,
            "name": "Software Engineer",
            "company": {"name": "Example"},
            "locations": [{"name": "Remote"}],
            "contents": "Build great systems.",
            "refs": {"landing_page": "https://www.themuse.com/jobs/42"},
            "publication_date": "2026-10-01T00:00:00Z",
        }
    )
    assert job.source == "the_muse"
    assert job.source_job_id == "42"
    assert job.company == "Example"
    assert job.remote is True
    assert job.apply_url.startswith("https://")


def test_usajobs_normalization() -> None:
    connector = USAJobsConnector()
    job = connector.normalize(
        {
            "PositionID": "USA-42",
            "PositionTitle": "Software Engineer",
            "OrganizationName": "Example Agency",
            "PositionLocation": [{"LocationName": "Washington"}],
            "PositionURI": "https://www.usajobs.gov/job/42",
            "PublicationStartDate": "2026-10-01",
            "PositionRemuneration": [{"MinimumRange": "100000", "MaximumRange": "150000"}],
            "UserArea": {"Details": {"JobSummary": "Build systems."}},
        }
    )
    assert job.source == "usajobs"
    assert job.source_job_id == "USA-42"
    assert job.salary.min_lpa == 100000
    assert job.salary.max_lpa == 150000
    assert job.apply_url.startswith("https://")


def test_learning_recommendations_are_real_destination_links() -> None:
    items = recommendations(["Kubernetes"], limit=7)
    assert len(items) == 7
    assert all(item["skill"] == "Kubernetes" for item in items)
    assert all(item["url"].startswith("https://") for item in items)


def test_career_message_classification() -> None:
    assert normalize_message({"subject": "Interview next round", "preview": "Schedule"}, "google")["kind"] == "interview"
    assert normalize_message({"subject": "Offer", "preview": "Congratulations"}, "google")["kind"] == "offer"
    assert normalize_message({"subject": "Application update", "preview": "Candidate"}, "microsoft")["kind"] == "application"
