import os
import time
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

    # HTTP statuses that commonly indicate a temporary failure.
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        country: str = "in",
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.country = country
        self.timeout = timeout
        self.max_retries = max_retries

    def _validate_credentials(self) -> None:
        """Ensure required Adzuna credentials are available."""

        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Missing ADZUNA_APP_ID or ADZUNA_APP_KEY "
                "environment variables."
            )

    def _build_search_url(self, page: int) -> str:
        """Build the Adzuna search endpoint."""

        return (
            f"https://api.adzuna.com/v1/api/jobs/"
            f"{self.country}/search/{page}"
        )

    def _build_params(
        self,
        query: str,
        location: Optional[str],
        limit: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build query parameters for Adzuna."""

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

        return params

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """
        Search Adzuna with retry/backoff and return normalized jobs.

        Retries are only applied to temporary server/rate-limit failures.
        """

        self._validate_credentials()

        url = self._build_search_url(page)
        params = self._build_params(
            query=query,
            location=location,
            limit=limit,
            filters=filters,
        )

        response: Optional[requests.Response] = None
        last_error: Optional[Exception] = None

        # Exponential-style backoff.
        backoff_seconds = [1, 3, 7]

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                if response.status_code in self.RETRYABLE_STATUS_CODES:
                    if attempt < self.max_retries - 1:
                        wait_time = backoff_seconds[
                            min(attempt, len(backoff_seconds) - 1)
                        ]

                        print(
                            f"[Adzuna] HTTP {response.status_code}. "
                            f"Retrying in {wait_time}s "
                            f"({attempt + 1}/{self.max_retries})..."
                        )

                        time.sleep(wait_time)
                        continue

                response.raise_for_status()
                break

            except requests.RequestException as exc:
                last_error = exc

                if attempt < self.max_retries - 1:
                    wait_time = backoff_seconds[
                        min(attempt, len(backoff_seconds) - 1)
                    ]

                    print(
                        f"[Adzuna] Request error. "
                        f"Retrying in {wait_time}s "
                        f"({attempt + 1}/{self.max_retries})..."
                    )

                    time.sleep(wait_time)
                    continue

                raise RuntimeError(
                    f"Adzuna request failed after "
                    f"{self.max_retries} attempts: {exc}"
                ) from exc

        if response is None:
            raise RuntimeError(
                "Adzuna request failed without receiving a response."
            )

        if not response.ok:
            if last_error:
                raise RuntimeError(
                    f"Adzuna request failed after "
                    f"{self.max_retries} attempts: {last_error}"
                ) from last_error

            raise RuntimeError(
                f"Adzuna returned HTTP {response.status_code}."
            )

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
        """
        Check whether Adzuna is reachable and credentials are valid.

        This deliberately performs a very small request.
        """

        try:
            self._validate_credentials()

            url = self._build_search_url(1)

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

            if response.ok:
                return {
                    "source": self.name,
                    "healthy": True,
                    "status_code": response.status_code,
                    "message": "Adzuna API is reachable.",
                }

            return {
                "source": self.name,
                "healthy": False,
                "status_code": response.status_code,
                "message": (
                    f"Adzuna returned HTTP "
                    f"{response.status_code}."
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
        """
        Convert one Adzuna listing into CareerPilot's canonical Job schema.
        """

        location_data = raw_job.get("location") or {}
        company_data = raw_job.get("company") or {}

        salary_min = self._safe_float(
            raw_job.get("salary_min")
        )
        salary_max = self._safe_float(
            raw_job.get("salary_max")
        )

        # Do not convert unknown salary units into LPA.
        # Raw source values are preserved in metadata.
        salary = Salary(
            min_lpa=None,
            max_lpa=None,
            currency="INR",
        )

        experience = Experience()

        return Job(
            source=self.name,
            source_job_id=str(
                raw_job.get("id", "")
            ),
            title=str(
                raw_job.get("title", "")
            ).strip(),
            company=str(
                company_data.get(
                    "display_name",
                    "Unknown",
                )
            ).strip(),
            location=self._extract_locations(
                location_data
            ),
            remote=self._detect_remote(
                raw_job
            ),
            employment_type=self._extract_employment_type(
                raw_job
            ),
            experience=experience,
            salary=salary,
            skills=self._extract_skills(
                raw_job
            ),
            description=str(
                raw_job.get(
                    "description",
                    "",
                )
            ).strip(),
            apply_url=str(
                raw_job.get(
                    "redirect_url",
                    "",
                )
            ),
            source_url=str(
                raw_job.get(
                    "redirect_url",
                    "",
                )
            ),
            posted_at=raw_job.get(
                "created"
            ),
            metadata={
                "category": raw_job.get(
                    "category",
                    {},
                ),
                "contract_type": raw_job.get(
                    "contract_type"
                ),
                "contract_time": raw_job.get(
                    "contract_time"
                ),
                "salary_min_raw": salary_min,
                "salary_max_raw": salary_max,
                "salary_is_predicted": raw_job.get(
                    "salary_is_predicted"
                ),
                "original_adzuna_id": raw_job.get(
                    "id"
                ),
            },
        )

    @staticmethod
    def _extract_locations(
        location_data: Dict[str, Any],
    ) -> List[str]:
        """
        Extract clean location components.

        Example raw data:
            India, Karnataka, Bangalore,
            Bangalore, Karnataka

        Result:
            India, Karnataka, Bangalore
        """

        raw_values: List[str] = []

        area = location_data.get("area") or []
        display_name = location_data.get(
            "display_name"
        )

        raw_values.extend(area)

        if display_name:
            raw_values.append(
                display_name
            )

        normalized: List[str] = []
        seen = set()

        for value in raw_values:
            parts = str(value).split(",")

            for part in parts:
                cleaned = part.strip()

                if not cleaned:
                    continue

                comparison_key = cleaned.casefold()

                if comparison_key in seen:
                    continue

                seen.add(comparison_key)
                normalized.append(cleaned)

        return normalized

    @staticmethod
    def _extract_employment_type(
        raw_job: Dict[str, Any],
    ) -> Optional[str]:
        """Convert Adzuna contract fields into one label."""

        contract_time = raw_job.get(
            "contract_time"
        )
        contract_type = raw_job.get(
            "contract_type"
        )

        if contract_time and contract_type:
            return (
                f"{contract_time}_{contract_type}"
            )

        return (
            contract_time
            or contract_type
        )

    @staticmethod
    def _extract_skills(
        raw_job: Dict[str, Any],
    ) -> List[str]:
        """
        Extract only explicitly available skill-like
        information.

        We deliberately do not infer technical skills
        here. The future CareerPilot enrichment layer
        will extract skills from descriptions using NLP.
        """

        skills: List[str] = []

        category = raw_job.get(
            "category"
        ) or {}

        label = category.get(
            "label"
        )

        if label:
            skills.append(
                str(label).strip()
            )

        return list(
            dict.fromkeys(
                skill
                for skill in skills
                if skill
            )
        )

    @staticmethod
    def _detect_remote(
        raw_job: Dict[str, Any],
    ) -> bool:
        """
        Conservative remote detection from title
        and description text.
        """

        title = str(
            raw_job.get(
                "title",
                "",
            )
        ).lower()

        description = str(
            raw_job.get(
                "description",
                "",
            )
        ).lower()

        remote_terms = (
            "remote",
            "work from home",
            "wfh",
            "work-from-home",
        )

        return any(
            term in title
            or term in description
            for term in remote_terms
        )

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> Optional[float]:
        """Safely convert a value to float."""

        if value is None or value == "":
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None