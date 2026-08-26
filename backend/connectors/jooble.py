import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class JoobleConnector(JobSource):
    """
    Jooble REST API connector.

    Credential:
        JOOBLE_API_KEY
    """

    name = "jooble"

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.api_key = os.getenv(
            "JOOBLE_API_KEY"
        )

        self.timeout = timeout
        self.max_retries = max_retries

    def _validate_credentials(self) -> None:

        if not self.api_key:
            raise RuntimeError(
                "Missing JOOBLE_API_KEY "
                "environment variable."
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
            "https://in.jooble.org/api/"
            f"{self.api_key}"
        )

        payload: Dict[str, Any] = {
            "keywords": query,
            "location": (
                location
                or "India"
            ),
            "page": str(page),
            "ResultOnPage": str(limit),
        }

        # IMPORTANT:
        # Do not pass candidate salary into Jooble
        # here. CareerPilot applies salary locally
        # after building the broad market pool.

        response: Optional[
            requests.Response
        ] = None

        last_error: Optional[
            Exception
        ] = None

        backoff_seconds = [
            1,
            3,
            7,
        ]

        for attempt in range(
            self.max_retries
        ):

            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type":
                            "application/json"
                    },
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
                                    2,
                                )
                            ]
                        )

                        print(
                            "[Jooble] HTTP "
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

                last_error = exc

                if attempt < (
                    self.max_retries - 1
                ):

                    wait_time = (
                        backoff_seconds[
                            min(
                                attempt,
                                2,
                            )
                        ]
                    )

                    print(
                        "[Jooble] Request failed. "
                        f"Retrying in "
                        f"{wait_time}s..."
                    )

                    time.sleep(
                        wait_time
                    )
                    continue

                raise RuntimeError(
                    "Jooble request failed after "
                    f"{self.max_retries} attempts: "
                    f"{exc}"
                ) from exc

        if response is None:
            raise RuntimeError(
                "Jooble request failed without "
                "a response."
            )

        if not response.ok:

            if last_error:
                raise RuntimeError(
                    "Jooble request failed after "
                    f"{self.max_retries} attempts: "
                    f"{last_error}"
                ) from last_error

            raise RuntimeError(
                "Jooble returned HTTP "
                f"{response.status_code}."
            )

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "Jooble returned invalid JSON."
            ) from exc

        results = data.get(
            "jobs",
            [],
        )

        return [
            self.normalize(job)
            for job in results
            if isinstance(
                job,
                dict,
            )
        ]

    def health_check(
        self,
    ) -> Dict[str, Any]:

        try:
            self._validate_credentials()

            response = requests.post(
                (
                    "https://in.jooble.org/api/"
                    f"{self.api_key}"
                ),
                json={
                    "keywords":
                        "software engineer",

                    "location":
                        "Bangalore",

                    "page":
                        "1",

                    "ResultOnPage":
                        "1",
                },
                headers={
                    "Content-Type":
                        "application/json"
                },
                timeout=self.timeout,
            )

            return {
                "source": self.name,
                "healthy": response.ok,
                "status_code": (
                    response.status_code
                ),
                "message": (
                    "Jooble API is reachable."
                    if response.ok
                    else (
                        "Jooble returned HTTP "
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

        location = str(
            raw_job.get(
                "location",
                "",
            )
        ).strip()

        salary_min, salary_max = (
            self._parse_salary(
                raw_job.get(
                    "salary"
                )
            )
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
                raw_job.get(
                    "company",
                    "Unknown",
                )
            ).strip(),

            location=(
                self._normalize_location(
                    location
                )
            ),

            remote=self._detect_remote(
                raw_job
            ),

            employment_type=(
                raw_job.get(
                    "type"
                )
            ),

            experience=Experience(),

            salary=Salary(
                min_lpa=salary_min,
                max_lpa=salary_max,
                currency="INR",
            ),

            skills=[],

            description=str(
                raw_job.get(
                    "snippet",
                    "",
                )
            ).strip(),

            apply_url=str(
                raw_job.get(
                    "link",
                    "",
                )
            ),

            source_url=str(
                raw_job.get(
                    "link",
                    "",
                )
            ),

            posted_at=(
                raw_job.get(
                    "updated"
                )
            ),

            metadata={
                "source_name": (
                    raw_job.get(
                        "source"
                    )
                ),

                "salary_raw": (
                    raw_job.get(
                        "salary"
                    )
                ),

                "salary_min_lpa": (
                    salary_min
                ),

                "salary_max_lpa": (
                    salary_max
                ),

                "jooble_id": (
                    raw_job.get(
                        "id"
                    )
                ),
            },
        )

    @staticmethod
    def _parse_salary(
        value: Any,
    ) -> Tuple[
        Optional[float],
        Optional[float],
    ]:
        """
        Parse Jooble salary text into INR LPA.

        Handles formats such as:

            8,00,000 - 12,00,000 INR
            800000 - 1200000 INR
            1200000 INR
            8 - 12 LPA

        Unknown salary formats remain unknown.
        """

        if value is None:
            return None, None

        text = str(value).strip()

        if not text:
            return None, None

        lowered = text.lower()

        # --------------------------------------------------
        # Case 1: salary already expressed in LPA
        # --------------------------------------------------

        if "lpa" in lowered:

            numbers = re.findall(
                r"\d+(?:\.\d+)?",
                text,
            )

            if not numbers:
                return None, None

            values = [
                float(number)
                for number in numbers
            ]

            if len(values) == 1:
                return (
                    values[0],
                    None,
                )

            return (
                values[0],
                values[1],
            )

        # --------------------------------------------------
        # Case 2: annual INR values
        # --------------------------------------------------

        numbers = re.findall(
            r"\d+(?:,\d{3})*(?:\.\d+)?",
            text,
        )

        if not numbers:
            return None, None

        values: List[float] = []

        for number in numbers:

            try:
                values.append(
                    float(
                        number.replace(
                            ",",
                            "",
                        )
                    )
                )

            except ValueError:
                continue

        if not values:
            return None, None

        # Convert annual INR → LPA.
        if len(values) == 1:

            return (
                round(
                    values[0] / 100000,
                    2,
                ),
                None,
            )

        return (
            round(
                values[0] / 100000,
                2,
            ),
            round(
                values[1] / 100000,
                2,
            ),
        )

    @staticmethod
    def _normalize_location(
        value: str,
    ) -> List[str]:

        if not value:
            return []

        parts = [
            part.strip()
            for part in value.split(",")
            if part.strip()
        ]

        result: List[str] = []
        seen = set()

        for part in parts:

            key = part.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(part)

        return result

    @staticmethod
    def _detect_remote(
        raw_job: Dict[str, Any],
    ) -> bool:

        text = (
            f"{raw_job.get('title', '')} "
            f"{raw_job.get('snippet', '')}"
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