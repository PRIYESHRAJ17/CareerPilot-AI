import os
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary


class JoobleConnector(JobSource):
    """
    Jooble REST API connector.

    Credential:
        JOOBLE_API_KEY

    Uses the India Jooble API endpoint.
    """

    name = "jooble"

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
    ) -> None:
        self.api_key = os.getenv("JOOBLE_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries

    def _validate_credentials(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "Missing JOOBLE_API_KEY environment variable."
            )

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """
        Search Jooble and normalize the returned jobs.
        """

        self._validate_credentials()

        url = f"https://in.jooble.org/api/{self.api_key}"

        payload: Dict[str, Any] = {
            "keywords": query,
            "location": location or "India",
            "page": str(page),
            "ResultOnPage": str(limit),
        }

        if "salary" in filters and filters["salary"] is not None:
            payload["salary"] = filters["salary"]

        response: Optional[requests.Response] = None
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout,
                )

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    if attempt < self.max_retries - 1:
                        wait_time = [1, 3, 7][
                            min(attempt, 2)
                        ]

                        print(
                            f"[Jooble] HTTP "
                            f"{response.status_code}. "
                            f"Retrying in {wait_time}s..."
                        )

                        import time
                        time.sleep(wait_time)
                        continue

                response.raise_for_status()
                break

            except requests.RequestException as exc:
                last_error = exc

                if attempt < self.max_retries - 1:
                    wait_time = [1, 3, 7][
                        min(attempt, 2)
                    ]

                    print(
                        f"[Jooble] Request failed. "
                        f"Retrying in {wait_time}s..."
                    )

                    import time
                    time.sleep(wait_time)
                    continue

                raise RuntimeError(
                    f"Jooble request failed after "
                    f"{self.max_retries} attempts: {exc}"
                ) from exc

        if response is None:
            raise RuntimeError(
                "Jooble request failed without a response."
            )

        if not response.ok:
            raise RuntimeError(
                f"Jooble returned HTTP "
                f"{response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Jooble returned invalid JSON."
            ) from exc

        results = data.get("jobs", [])

        return [
            self.normalize(job)
            for job in results
            if isinstance(job, dict)
        ]

    def health_check(self) -> Dict[str, Any]:
        """
        Check Jooble API availability and credentials.
        """

        try:
            self._validate_credentials()

            url = f"https://in.jooble.org/api/{self.api_key}"

            response = requests.post(
                url,
                json={
                    "keywords": "software engineer",
                    "location": "Bangalore",
                    "page": "1",
                    "ResultOnPage": "1",
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=self.timeout,
            )

            return {
                "source": self.name,
                "healthy": response.ok,
                "status_code": response.status_code,
                "message": (
                    "Jooble API is reachable."
                    if response.ok
                    else (
                        f"Jooble returned HTTP "
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
        """
        Convert Jooble's job format into CareerPilot's Job schema.
        """

        location = str(
            raw_job.get("location", "")
        ).strip()

        return Job(
            source=self.name,
            source_job_id=str(
                raw_job.get("id", "")
            ),
            title=str(
                raw_job.get("title", "")
            ).strip(),
            company=str(
                raw_job.get("company", "Unknown")
            ).strip(),
            location=self._normalize_location(
                location
            ),
            remote=self._detect_remote(
                raw_job
            ),
            employment_type=raw_job.get(
                "type"
            ),
            experience=Experience(),
            salary=Salary(
                min_lpa=None,
                max_lpa=None,
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
            posted_at=raw_job.get(
                "updated"
            ),
            metadata={
                "source_name": raw_job.get(
                    "source"
                ),
                "salary_raw": raw_job.get(
                    "salary"
                ),
                "jooble_id": raw_job.get(
                    "id"
                ),
            },
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

            if key not in seen:
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