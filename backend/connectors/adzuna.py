import os
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class AdzunaConnector(JobSource):
    """
    Adzuna job-source connector.

    Credentials are loaded from environment variables:
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
        """Ensure required Adzuna credentials are available."""
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Missing ADZUNA_APP_ID or ADZUNA_APP_KEY "
                "environment variables."
            )

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """Search Adzuna and return normalized CareerPilot Job objects."""

        self._validate_credentials()

        url = (
            f"https://api.adzuna.com/v1/api/jobs/"
            f"{self.country}/search/{page}"
        )

        params: Dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": query,
        }

        if location:
            params["where"] = location

        supported_filters = (
            "what",
            "where",
            "salary_min",
            "salary_max",
            "full_time",
            "part_time",
            "permanent",
            "contract",
            "sort_by",
            "max_days_old",
        )

        for key in supported_filters:
            if key in filters and filters[key] is not None:
                params[key] = filters[key]

        try:
            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Adzuna request failed: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Adzuna returned an invalid JSON response."
            ) from exc

        results = data.get("results", [])

        return [
            self.normalize(raw_job)
            for raw_job in results
            if isinstance(raw_job, dict)
        ]

    def health_check(self) -> Dict[str, Any]:
        """Check whether Adzuna is reachable and credentials are valid."""

        try:
            self._validate_credentials()

            url = (
                f"https://api.adzuna.com/v1/api/jobs/"
                f"{self.country}/search/1"
            )

            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": 1,
                "what": "software engineer",
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            return {
                "source": self.name,
                "healthy": response.ok,
                "status_code": response.status_code,
                "message": (
                    "Adzuna API is reachable."
                    if response.ok
                    else f"Adzuna returned HTTP {response.status_code}."
                ),
            }

        except Exception as exc:
            return {
                "source": self.name,
                "healthy": False,
                "status_code": None,
                "message": str(exc),
            }

    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        """Convert one Adzuna listing to CareerPilot's Job schema."""

        location_data = raw_job.get("location") or {}
        company_data = raw_job.get("company") or {}

        salary_min = self._safe_float(raw_job.get("salary_min"))
        salary_max = self._safe_float(raw_job.get("salary_max"))

        # Keep salary fields empty until we have verified the source unit.
        # Raw values are preserved in metadata so we do not fabricate LPA.
        salary = Salary(
            min_lpa=None,
            max_lpa=None,
            currency="INR",
        )

        experience = Experience()

        return Job(
            source=self.name,
            source_job_id=str(raw_job.get("id", "")),
            title=str(raw_job.get("title", "")).strip(),
            company=str(
                company_data.get("display_name", "Unknown")
            ).strip(),
            location=self._extract_locations(location_data),
            remote=self._detect_remote(raw_job),
            employment_type=self._extract_employment_type(raw_job),
            experience=experience,
            salary=salary,
            skills=self._extract_skills(raw_job),
            description=str(
                raw_job.get("description", "")
            ).strip(),
            apply_url=str(
                raw_job.get("redirect_url", "")
            ),
            source_url=str(
                raw_job.get("redirect_url", "")
            ),
            posted_at=raw_job.get("created"),
            metadata={
                "category": raw_job.get("category", {}),
                "contract_type": raw_job.get("contract_type"),
                "contract_time": raw_job.get("contract_time"),
                "salary_min_raw": salary_min,
                "salary_max_raw": salary_max,
                "salary_is_predicted": raw_job.get(
                    "salary_is_predicted"
                ),
                "original_adzuna_id": raw_job.get("id"),
            },
        )

    @staticmethod
    def _extract_locations(
        location_data: Dict[str, Any],
    ) -> List[str]:
        """
        Extract clean location components.

        Adzuna can return overlapping values such as:
            India, Karnataka, Bangalore, Bangalore, Karnataka

        We flatten comma-separated values and remove duplicates while
        preserving the original geographic order.
        """

        raw_values: List[str] = []

        area = location_data.get("area") or []
        display_name = location_data.get("display_name")

        raw_values.extend(area)

        if display_name:
            raw_values.append(display_name)

        normalized: List[str] = []
        seen = set()

        for value in raw_values:
            parts = str(value).split(",")

            for part in parts:
                cleaned = part.strip()

                if not cleaned:
                    continue

                comparison_key = cleaned.casefold()

                if comparison_key not in seen:
                    seen.add(comparison_key)
                    normalized.append(cleaned)

        return normalized

    @staticmethod
    def _extract_employment_type(
        raw_job: Dict[str, Any],
    ) -> Optional[str]:
        """Convert Adzuna contract fields into one label."""

        contract_time = raw_job.get("contract_time")
        contract_type = raw_job.get("contract_type")

        if contract_time and contract_type:
            return f"{contract_time}_{contract_type}"

        return contract_time or contract_type

    @staticmethod
    def _extract_skills(
        raw_job: Dict[str, Any],
    ) -> List[str]:
        """
        Extract only explicitly available skill-like information.

        We deliberately do not infer technical skills from descriptions yet.
        That will be handled later by the CareerPilot enrichment engine.
        """

        skills: List[str] = []

        category = raw_job.get("category") or {}
        label = category.get("label")

        if label:
            skills.append(str(label).strip())

        return list(
            dict.fromkeys(
                skill for skill in skills if skill
            )
        )

    @staticmethod
    def _detect_remote(
        raw_job: Dict[str, Any],
    ) -> bool:
        """
        Conservative remote detection from title/description text.
        """

        title = str(raw_job.get("title", "")).lower()
        description = str(
            raw_job.get("description", "")
        ).lower()

        remote_terms = (
            "remote",
            "work from home",
            "wfh",
            "work-from-home",
        )

        return any(
            term in title or term in description
            for term in remote_terms
        )

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert a value to float."""

        if value is None or value == "":
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None