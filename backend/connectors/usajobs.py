from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class USAJobsConnector(JobSource):
    name = "usajobs"
    display_name = "USAJOBS"
    category = "official_job_api"
    countries = ["US"]
    requires_credentials = True
    credential_env_vars = ["USAJOBS_API_KEY", "USAJOBS_USER_AGENT"]
    supports_paging = True
    supports_remote_filter = False
    supports_salary_filter = False
    website = "https://www.usajobs.gov/"
    api_url = "https://data.usajobs.gov/api/Search"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = max(1, int(timeout))

    def validate_configuration(self) -> None:
        missing = [name for name in self.credential_env_vars if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing USAJOBS credentials: {', '.join(missing)}")

    def _request(self, **params: Any) -> dict[str, Any]:
        self.validate_configuration()
        response = requests.get(
            self.api_url,
            params=params,
            headers={
                "Host": "data.usajobs.gov",
                "User-Agent": os.getenv("USAJOBS_USER_AGENT", "careerpilot@example.com"),
                "Authorization-Key": os.getenv("USAJOBS_API_KEY", ""),
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("USAJOBS returned an unexpected payload.")
        return data

    def search(self, query: str, location: Optional[str] = None, page: int = 1, limit: int = 20, **filters: Any) -> List[Job]:
        data = self._request(
            Keyword=query,
            LocationName=location or None,
            Page=max(1, int(page)),
            ResultsPerPage=min(max(int(limit), 1), 500),
        )
        items = ((data.get("SearchResult") or {}).get("SearchResultItems") or [])
        return [self.normalize_and_enrich(item.get("MatchedObjectDescriptor", {})) for item in items if isinstance(item, dict)]

    def health_check(self) -> Dict[str, Any]:
        try:
            jobs = self.search("software engineer", limit=1)
            return {"source": self.name, "healthy": bool(jobs), "status_code": 200, "jobs_returned": len(jobs), "message": "USAJOBS search API reachable."}
        except Exception as exc:
            return {"source": self.name, "healthy": False, "status_code": None, "jobs_returned": 0, "message": str(exc)}

    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        locations = []
        for item in raw_job.get("PositionLocation", []) or []:
            if isinstance(item, dict):
                value = str(item.get("LocationName") or "").strip()
                if value:
                    locations.append(value)
        remuneration = raw_job.get("PositionRemuneration", []) or []
        salary_min = salary_max = None
        currency = "USD"
        if remuneration and isinstance(remuneration[0], dict):
            salary_min = _number(remuneration[0].get("MinimumRange"))
            salary_max = _number(remuneration[0].get("MaximumRange"))
        return Job(
            source=self.name,
            source_job_id=str(raw_job.get("PositionID") or raw_job.get("PositionURI") or raw_job.get("PositionTitle") or "unknown"),
            title=str(raw_job.get("PositionTitle") or "Untitled role").strip(),
            company=str((raw_job.get("OrganizationName") or raw_job.get("DepartmentName") or "US Federal Government")).strip(),
            location=locations,
            remote=False,
            employment_type=str(raw_job.get("PositionScheduleTypeName") or "").strip() or None,
            experience=Experience(),
            salary=Salary(min_lpa=salary_min, max_lpa=salary_max, currency=currency),
            skills=[],
            description=str(raw_job.get("UserArea", {}).get("Details", {}).get("JobSummary") or "").strip(),
            apply_url=str(raw_job.get("PositionURI") or "").strip(),
            source_url=str(raw_job.get("PositionURI") or "").strip(),
            posted_at=str(raw_job.get("PublicationStartDate") or "").strip() or None,
            metadata={"provider_family": "USAJOBS", "federal_job": True},
        )


def _number(value: Any) -> float | None:
    try:
        number = float(str(value).replace(",", ""))
        return number if number > 0 else None
    except (TypeError, ValueError):
        return None
