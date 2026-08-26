import os
import time
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class AdzunaConnector(JobSource):
    """
    Adzuna job-source connector for India.

    Credentials:
        ADZUNA_APP_ID
        ADZUNA_APP_KEY
    """

    name = "adzuna"

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

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
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "Missing ADZUNA_APP_ID or ADZUNA_APP_KEY "
                "environment variables."
            )

    def _build_search_url(
        self,
        page: int,
    ) -> str:
        return (
            "https://api.adzuna.com/v1/api/jobs/"
            f"{self.country}/search/{page}"
        )

    def _build_params(
        self,
        query: str,
        location: Optional[str],
        limit: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:

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
            if (
                key in filters
                and filters[key] is not None
            ):
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

        self._validate_credentials()

        url = self._build_search_url(page)

        params = self._build_params(
            query=query,
            location=location,
            limit=limit,
            filters=filters,
        )

        response: Optional[
            requests.Response
        ] = None

        backoff_seconds = [1, 3, 7]

        for attempt in range(
            self.max_retries
        ):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                )

                if (
                    response.status_code
                    in self.RETRYABLE_STATUS_CODES
                ):
                    if attempt < (
                        self.max_retries - 1
                    ):
                        wait_time = (
                            backoff_seconds[
                                min(
                                    attempt,
                                    len(backoff_seconds) - 1,
                                )
                            ]
                        )

                        print(
                            f"[Adzuna] HTTP "
                            f"{response.status_code}. "
                            f"Retrying in "
                            f"{wait_time}s..."
                        )

                        time.sleep(
                            wait_time
                        )
                        continue

                response.raise_for_status()
                break

            except requests.RequestException as exc:

                if attempt < (
                    self.max_retries - 1
                ):
                    wait_time = (
                        backoff_seconds[
                            min(
                                attempt,
                                len(backoff_seconds) - 1,
                            )
                        ]
                    )

                    print(
                        "[Adzuna] Request failed. "
                        f"Retrying in "
                        f"{wait_time}s..."
                    )

                    time.sleep(
                        wait_time
                    )
                    continue

                raise RuntimeError(
                    "Adzuna request failed after "
                    f"{self.max_retries} attempts: "
                    f"{exc}"
                ) from exc

        if response is None:
            raise RuntimeError(
                "Adzuna request failed without "
                "a response."
            )

        if not response.ok:
            raise RuntimeError(
                "Adzuna returned HTTP "
                f"{response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Adzuna returned invalid JSON."
            ) from exc

        results = data.get(
            "results",
            [],
        )

        return [
            self.normalize(raw_job)
            for raw_job in results
            if isinstance(
                raw_job,
                dict,
            )
        ]

    def health_check(
        self,
    ) -> Dict[str, Any]:

        try:
            self._validate_credentials()

            response = requests.get(
                self._build_search_url(1),
                params={
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "results_per_page": 1,
                    "what": "software engineer",
                },
                timeout=self.timeout,
            )

            return {
                "source": self.name,
                "healthy": response.ok,
                "status_code": response.status_code,
                "message": (
                    "Adzuna API is reachable."
                    if response.ok
                    else (
                        "Adzuna returned HTTP "
                        f"{response.status_code}."
                    )
                ),
            }

        except Exception as exc:
            return {
                "source": self.name,
                "healthy": False,
                "status_code": None,
                "message": str(exc),
            }

    def normalize(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:

        location_data = (
            raw_job.get("location")
            or {}
        )

        company_data = (
            raw_job.get("company")
            or {}
        )

        salary_min_raw = (
            self._safe_float(
                raw_job.get(
                    "salary_min"
                )
            )
        )

        salary_max_raw = (
            self._safe_float(
                raw_job.get(
                    "salary_max"
                )
            )
        )

        # Adzuna's India endpoint returns
        # annual salary values.
        #
        # Convert INR annual salary into LPA.
        salary = Salary(
            min_lpa=(
                round(
                    salary_min_raw / 100000,
                    2,
                )
                if salary_min_raw is not None
                else None
            ),
            max_lpa=(
                round(
                    salary_max_raw / 100000,
                    2,
                )
                if salary_max_raw is not None
                else None
            ),
            currency="INR",
        )

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

            employment_type=(
                self._extract_employment_type(
                    raw_job
                )
            ),

            experience=Experience(),

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
                "category": (
                    raw_job.get(
                        "category",
                        {},
                    )
                ),

                "contract_type": (
                    raw_job.get(
                        "contract_type"
                    )
                ),

                "contract_time": (
                    raw_job.get(
                        "contract_time"
                    )
                ),

                "salary_min_raw": (
                    salary_min_raw
                ),

                "salary_max_raw": (
                    salary_max_raw
                ),

                "salary_is_predicted": (
                    raw_job.get(
                        "salary_is_predicted"
                    )
                ),

                "original_adzuna_id": (
                    raw_job.get("id")
                ),
            },
        )

    @staticmethod
    def _extract_locations(
        location_data: Dict[str, Any],
    ) -> List[str]:

        raw_values: List[str] = []

        raw_values.extend(
            location_data.get("area")
            or []
        )

        display_name = (
            location_data.get(
                "display_name"
            )
        )

        if display_name:
            raw_values.append(
                display_name
            )

        normalized: List[str] = []
        seen = set()

        for value in raw_values:

            for part in str(value).split(","):

                cleaned = part.strip()

                if not cleaned:
                    continue

                key = cleaned.casefold()

                if key in seen:
                    continue

                seen.add(key)
                normalized.append(
                    cleaned
                )

        return normalized

    @staticmethod
    def _extract_employment_type(
        raw_job: Dict[str, Any],
    ) -> Optional[str]:

        contract_time = (
            raw_job.get(
                "contract_time"
            )
        )

        contract_type = (
            raw_job.get(
                "contract_type"
            )
        )

        if (
            contract_time
            and contract_type
        ):
            return (
                f"{contract_time}_"
                f"{contract_type}"
            )

        return (
            contract_time
            or contract_type
        )

    @staticmethod
    def _extract_skills(
        raw_job: Dict[str, Any],
    ) -> List[str]:

        category = (
            raw_job.get(
                "category"
            )
            or {}
        )

        label = category.get(
            "label"
        )

        if not label:
            return []

        return [
            str(label).strip()
        ]

    @staticmethod
    def _detect_remote(
        raw_job: Dict[str, Any],
    ) -> bool:

        text = (
            f"{raw_job.get('title', '')} "
            f"{raw_job.get('description', '')}"
        ).lower()

        remote_terms = (
            "remote",
            "work from home",
            "wfh",
            "work-from-home",
        )

        return any(
            term in text
            for term in remote_terms
        )

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> Optional[float]:

        if value is None or value == "":
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None