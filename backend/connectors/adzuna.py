import os
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class AdzunaConnector(JobSource):
    """
    Adzuna job-source connector.

    Credentials are read from environment variables:
    ADZUNA_APP_ID
    ADZUNA_APP_KEY
    """

    name = "adzuna"

    def __init__(self, country: str = "in", timeout: int = 15) -> None:
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = country
        self.timeout = timeout

    def _validate_credentials(self) -> None:
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Missing ADZUNA_APP_ID or ADZUNA_APP_KEY environment variables."
            )

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:

        self._validate_credentials()

        url = (
            f"https://api.adzuna.com/v1/api/jobs/"
            f"{self.country}/search/{page}"
        )

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": query,
        }

        if location:
            params["where"] = location

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        return [
            self.normalize(raw_job)
            for raw_job in data.get("results", [])
        ]

    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        location_data = raw_job.get("location") or {}
        company_data = raw_job.get("company") or {}

        salary = Salary(
            min_lpa=self._monthly_to_lpa(raw_job.get("salary_min")),
            max_lpa=self._monthly_to_lpa(raw_job.get("salary_max")),
            currency="INR",
        )

        experience = Experience()

        return Job(
            source=self.name,
            source_job_id=str(raw_job.get("id", "")),
            title=raw_job.get("title", "").strip(),
            company=company_data.get("display_name", "Unknown"),
            location=self._extract_locations(location_data),
            remote=False,
            employment_type=None,
            experience=experience,
            salary=salary,
            skills=[],
            description=raw_job.get("description", ""),
            apply_url=raw_job.get("redirect_url", ""),
            source_url=raw_job.get("redirect_url", ""),
            posted_at=raw_job.get("created"),
            metadata={
                "category": raw_job.get("category", {}),
                "contract_type": raw_job.get("contract_type"),
                "contract_time": raw_job.get("contract_time"),
            },
        )

    @staticmethod
    def _extract_locations(location_data: Dict[str, Any]) -> List[str]:
        area = location_data.get("area") or []
        display_name = location_data.get("display_name")

        locations = list(area)

        if display_name and display_name not in locations:
            locations.append(display_name)

        return locations

    @staticmethod
    def _monthly_to_lpa(value: Optional[float]) -> Optional[float]:
        """
        Adzuna salary values can be represented in annual/monthly forms
        depending on source data. This helper is intentionally conservative.

        For now, treat the received value as annual INR unless later
        source-level benchmarking shows a different representation.
        """
        if value is None:
            return None

        return round(float(value) / 100000, 2)
