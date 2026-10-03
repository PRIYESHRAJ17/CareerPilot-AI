from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class TheMuseConnector(JobSource):
    name = "the_muse"
    display_name = "The Muse"
    category = "official_job_api"
    countries = ["GLOBAL"]
    requires_credentials = False
    credential_env_vars = []
    supports_paging = True
    supports_remote_filter = False
    supports_salary_filter = False
    website = "https://www.themuse.com/"
    api_url = "https://www.themuse.com/api/public/jobs"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = max(1, int(timeout))
        self.api_key = os.getenv("THEMUSE_API_KEY", "").strip()

    def _request(self, page: int, query: str, location: Optional[str]) -> dict[str, Any]:
        params: dict[str, Any] = {"page": max(0, int(page) - 1), "descending": "true"}
        if query:
            params["category"] = query
        if location:
            params["location"] = location
        if self.api_key:
            params["api_key"] = self.api_key
        response = requests.get(self.api_url, params=params, headers={"Accept": "application/json", "User-Agent": "CareerPilot-AI/Week7"}, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("The Muse returned an unexpected payload.")
        return data

    def search(self, query: str, location: Optional[str] = None, page: int = 1, limit: int = 20, **filters: Any) -> List[Job]:
        data = self._request(page, query, location)
        results = list(data.get("results") or [])[: max(1, int(limit))]
        return [self.normalize_and_enrich(item) for item in results if isinstance(item, dict)]

    def health_check(self) -> Dict[str, Any]:
        try:
            jobs = self.search("software", limit=1)
            return {"source": self.name, "healthy": bool(jobs), "status_code": 200, "jobs_returned": len(jobs), "message": "The Muse public Jobs API reachable."}
        except Exception as exc:
            return {"source": self.name, "healthy": False, "status_code": None, "jobs_returned": 0, "message": str(exc)}

    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        locations = [str(item.get("name") or "").strip() for item in (raw_job.get("locations") or []) if isinstance(item, dict) and str(item.get("name") or "").strip()]
        company = raw_job.get("company") or {}
        return Job(
            source=self.name,
            source_job_id=str(raw_job.get("id") or raw_job.get("refs", {}).get("landing_page") or "unknown"),
            title=str(raw_job.get("name") or "Untitled role").strip(),
            company=str(company.get("name") or "The Muse listing").strip(),
            location=locations,
            remote=any("remote" in location.casefold() for location in locations),
            employment_type=None,
            experience=Experience(),
            salary=Salary(currency="USD"),
            skills=[],
            description=str(raw_job.get("contents") or "").strip(),
            apply_url=str(raw_job.get("refs", {}).get("landing_page") or "").strip(),
            source_url=str(raw_job.get("refs", {}).get("landing_page") or "").strip(),
            posted_at=str(raw_job.get("publication_date") or "").strip() or None,
            metadata={"provider_family": "The Muse", "registered_api_key": bool(self.api_key)},
        )
