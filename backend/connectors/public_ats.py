"""
CareerPilot AI - Public ATS Job Source Connector.

Supported public ATS platforms:

    - Greenhouse
    - Lever
    - Ashby

These connectors use public employer job-board endpoints and therefore do not
require API credentials.

A ProviderDefinition supplies the company/board identifier through:

    adapter_config = {
        "platform": "greenhouse" | "lever" | "ashby",
        "board": "<public board slug>",
        ...
    }

Important:
    Public does not mean every provider endpoint is guaranteed to be alive.
    Runtime health verification remains authoritative.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary
from backend.schemas.provider_fleet import ProviderDefinition


class PublicAtsJobSource(JobSource):
    """
    Shared adapter for public ATS job-board APIs.

    Supported:
        greenhouse
        lever
        ashby

    Credentials:
        None.

    ProviderDefinition must contain:
        adapter_type="ats_public"

        adapter_config={
            "platform": "...",
            "board": "..."
        }
    """

    # ------------------------------------------------------------------
    # IMPORTANT
    # ------------------------------------------------------------------
    # Explicit class-level values prevent the base JobSource's credential
    # defaults from incorrectly classifying this public connector as a
    # credentialed provider.
    # ------------------------------------------------------------------

    requires_credentials = False
    credential_env_vars: List[str] = []

    RETRYABLE_STATUS_CODES = {
        408,
        425,
        429,
        500,
        502,
        503,
        504,
    }

    SUPPORTED_PLATFORMS = {
        "greenhouse",
        "lever",
        "ashby",
    }

    def __init__(
        self,
        definition: ProviderDefinition,
        timeout: int = 20,
        max_retries: int = 3,
    ) -> None:
        if definition.adapter_type != "ats_public":
            raise ValueError(
                "PublicAtsJobSource requires "
                "adapter_type='ats_public'."
            )

        self.definition = definition

        adapter_config = (
            definition.adapter_config
            if isinstance(
                definition.adapter_config,
                dict,
            )
            else {}
        )

        self.platform = str(
            adapter_config.get(
                "platform",
                "",
            )
        ).strip().lower()

        if self.platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(
                "Unsupported public ATS platform: "
                f"{self.platform}"
            )

        self.board_name = str(
            adapter_config.get(
                "board",
                "",
            )
        ).strip()

        if not self.board_name:
            raise ValueError(
                f"Provider '{definition.name}' "
                "requires adapter_config['board']."
            )

        self.region = str(
            adapter_config.get(
                "region",
                "global",
            )
            or "global"
        ).strip().lower()

        self.name = str(
            definition.name
        )

        self.display_name = str(
            definition.display_name
        )

        self.category = str(
            definition.category
        )

        self.countries = list(
            definition.countries
            or []
        )

        # --------------------------------------------------------------
        # Explicitly public / credential-free
        # --------------------------------------------------------------
        self.requires_credentials = False
        self.credential_env_vars = []

        self.supports_paging = bool(
            definition.supports_paging
        )

        self.supports_remote_filter = bool(
            definition.supports_remote_filter
        )

        self.supports_salary_filter = bool(
            definition.supports_salary_filter
        )

        self.website = definition.website
        self.api_url = definition.api_url

        self.timeout = max(
            1,
            int(timeout),
        )

        self.max_retries = max(
            1,
            int(max_retries),
        )

    # ================================================================
    # CONFIGURATION
    # ================================================================

    def validate_configuration(self) -> bool:
        """
        Validate only the structural configuration required by this public
        connector.

        This intentionally overrides JobSource.validate_configuration().

        Greenhouse, Lever, and Ashby public job-board endpoints do not require
        an API key for the public job-posting data used here. The provider
        therefore must never be blocked by credential environment variables.
        """

        return (
            self.platform in self.SUPPORTED_PLATFORMS
            and bool(self.board_name)
        )

    # ================================================================
    # METADATA
    # ================================================================

    @property
    def metadata(self):
        """
        Preserve the standard JobSource metadata contract while ensuring the
        runtime platform/board identity is available.
        """
        try:
            return super().metadata
        except Exception:
            return {
                "name": self.name,
                "display_name": self.display_name,
                "category": self.category,
                "countries": self.countries,
                "requires_credentials": False,
                "credential_env_vars": [],
                "supports_paging": self.supports_paging,
                "supports_remote_filter": (
                    self.supports_remote_filter
                ),
                "supports_salary_filter": (
                    self.supports_salary_filter
                ),
                "website": self.website,
                "api_url": self.api_url,
            }

    # ================================================================
    # ENDPOINT
    # ================================================================

    def _endpoint(self) -> str:
        if self.platform == "greenhouse":
            return (
                "https://boards-api.greenhouse.io/"
                "v1/boards/"
                f"{self.board_name}/jobs"
            )

        if self.platform == "lever":
            if self.region == "eu":
                base = (
                    "https://api.eu.lever.co/"
                    "v0/postings/"
                )
            else:
                base = (
                    "https://api.lever.co/"
                    "v0/postings/"
                )

            return (
                f"{base}{self.board_name}"
            )

        return (
            "https://api.ashbyhq.com/"
            "posting-api/job-board/"
            f"{self.board_name}"
        )

    # ================================================================
    # REQUEST
    # ================================================================

    def _request(self) -> Any:
        endpoint = self._endpoint()

        params: Dict[str, Any] = {}

        headers = {
            "Accept": "application/json",
            "User-Agent": (
                "CareerPilot-AI/"
                "provider-fleet"
            ),
        }

        if self.platform == "greenhouse":
            params["content"] = "true"

        elif self.platform == "lever":
            params["mode"] = "json"

        elif self.platform == "ashby":
            params["includeCompensation"] = "true"

        backoff = (
            1,
            3,
            7,
        )

        last_error: Optional[
            Exception
        ] = None

        for attempt in range(
            self.max_retries
        ):
            try:
                response = requests.get(
                    endpoint,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

                if (
                    response.status_code
                    in self.RETRYABLE_STATUS_CODES
                ):
                    if attempt < (
                        self.max_retries - 1
                    ):
                        time.sleep(
                            backoff[
                                min(
                                    attempt,
                                    len(backoff) - 1,
                                )
                            ]
                        )
                        continue

                response.raise_for_status()

                try:
                    return response.json()

                except ValueError as exc:
                    raise RuntimeError(
                        f"{self.name} returned "
                        "invalid JSON."
                    ) from exc

            except (
                requests.RequestException,
                RuntimeError,
            ) as exc:
                last_error = exc

                if attempt < (
                    self.max_retries - 1
                ):
                    time.sleep(
                        backoff[
                            min(
                                attempt,
                                len(backoff) - 1,
                            )
                        ]
                    )
                    continue

                raise RuntimeError(
                    f"{self.name} request failed "
                    f"after {self.max_retries} attempts: "
                    f"{exc}"
                ) from exc

        raise RuntimeError(
            f"{self.name} request failed: "
            f"{last_error}"
        )

    # ================================================================
    # EXTRACT JOB LIST
    # ================================================================

    def _jobs(
        self,
        data: Any,
    ) -> List[Dict[str, Any]]:
        if self.platform == "lever":
            if isinstance(
                data,
                list,
            ):
                return [
                    item
                    for item in data
                    if isinstance(
                        item,
                        dict,
                    )
                ]

            return []

        if isinstance(
            data,
            dict,
        ):
            jobs = data.get(
                "jobs",
                [],
            )

            if isinstance(
                jobs,
                list,
            ):
                return [
                    item
                    for item in jobs
                    if isinstance(
                        item,
                        dict,
                    )
                ]

        return []

    # ================================================================
    # SEARCH
    # ================================================================

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        del filters

        data = self._request()

        raw_jobs = self._jobs(
            data
        )

        normalized: List[Job] = []

        for raw_job in raw_jobs:
            try:
                normalized.append(
                    self.normalize_and_enrich(
                        raw_job
                    )
                )
            except Exception:
                # One malformed posting must never eliminate the whole
                # provider result.
                continue

        matched = [
            job
            for job in normalized
            if self._matches(
                job,
                query=query,
                location=location,
            )
        ]

        safe_page = max(
            1,
            int(page),
        )

        safe_limit = max(
            1,
            int(limit),
        )

        start = (
            safe_page - 1
        ) * safe_limit

        end = (
            start
            + safe_limit
        )

        return matched[
            start:end
        ]

    # ================================================================
    # MATCHING
    # ================================================================

    @staticmethod
    def _matches(
        job: Job,
        query: str,
        location: Optional[str],
    ) -> bool:
        haystack = " ".join(
            [
                str(job.title or ""),
                str(job.company or ""),
                str(job.description or ""),
                " ".join(
                    str(skill)
                    for skill in (
                        job.skills or []
                    )
                ),
                " ".join(
                    str(value)
                    for value in (
                        job.location or []
                    )
                ),
            ]
        ).lower()

        if query:
            tokens = [
                token
                for token in re.findall(
                    r"[a-z0-9]+",
                    query.lower(),
                )
                if len(token) >= 2
            ]

            if tokens and not all(
                token in haystack
                for token in tokens
            ):
                return False

        if location:
            requested = (
                str(location)
                .strip()
                .lower()
            )

            if requested:
                location_text = " ".join(
                    str(value)
                    for value in (
                        job.location or []
                    )
                ).lower()

                if (
                    requested not in haystack
                    and requested not in location_text
                ):
                    return False

        return True

    # ================================================================
    # HEALTH
    # ================================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:
        started = time.perf_counter()

        try:
            data = self._request()

            jobs = self._jobs(
                data
            )

            latency_ms = round(
                (
                    time.perf_counter()
                    - started
                )
                * 1000.0,
                2,
            )

            return {
                "source": self.name,
                "healthy": isinstance(
                    jobs,
                    list,
                ),
                "status_code": 200,
                "latency_ms": latency_ms,
                "jobs_available": len(
                    jobs
                ),
                "message": (
                    f"{self.platform} public "
                    "job-board endpoint reachable."
                ),
            }

        except Exception as exc:
            latency_ms = round(
                (
                    time.perf_counter()
                    - started
                )
                * 1000.0,
                2,
            )

            return {
                "source": self.name,
                "healthy": False,
                "status_code": None,
                "latency_ms": latency_ms,
                "jobs_available": 0,
                "message": str(exc),
            }

    # ================================================================
    # NORMALIZATION
    # ================================================================

    def normalize(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        if self.platform == "greenhouse":
            return self._normalize_greenhouse(
                raw_job
            )

        if self.platform == "lever":
            return self._normalize_lever(
                raw_job
            )

        return self._normalize_ashby(
            raw_job
        )

    # ================================================================
    # GREENHOUSE
    # ================================================================

    def _normalize_greenhouse(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        location: List[str] = []

        raw_location = (
            raw_job.get(
                "location"
            )
            or {}
        )

        if isinstance(
            raw_location,
            dict,
        ):
            name = raw_location.get(
                "name"
            )

            if name:
                location.append(
                    str(name)
                )

        departments = (
            raw_job.get(
                "departments"
            )
            or []
        )

        skills: List[str] = []

        if isinstance(
            departments,
            list,
        ):
            for department in departments:
                if isinstance(
                    department,
                    dict,
                ):
                    name = department.get(
                        "name"
                    )

                    if name:
                        skills.append(
                            str(name)
                        )

        absolute_url = str(
            raw_job.get(
                "absolute_url",
                "",
            )
            or ""
        ).strip()

        posted_at = (
            raw_job.get(
                "updated_at"
            )
            or raw_job.get(
                "created_at"
            )
        )

        return Job(
            source=self.name,

            source_job_id=str(
                raw_job.get(
                    "id",
                    "",
                )
                or ""
            ),

            title=str(
                raw_job.get(
                    "title",
                    "",
                )
                or ""
            ).strip(),

            company=self.board_name,

            location=location,

            remote=self._detect_remote(
                raw_job
            ),

            employment_type=None,

            experience=Experience(),

            salary=Salary(
                currency="USD"
            ),

            skills=skills,

            description=str(
                raw_job.get(
                    "content",
                    "",
                )
                or ""
            ).strip(),

            apply_url=absolute_url,

            source_url=absolute_url,

            posted_at=posted_at,

            metadata={
                "fleet_adapter": (
                    "ats_public"
                ),
                "ats_platform": (
                    "greenhouse"
                ),
                "ats_board": (
                    self.board_name
                ),
            },
        )

    # ================================================================
    # LEVER
    # ================================================================

    def _normalize_lever(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        categories = (
            raw_job.get(
                "categories"
            )
            or {}
        )

        if not isinstance(
            categories,
            dict,
        ):
            categories = {}

        locations: List[str] = []

        all_locations = (
            categories.get(
                "allLocations"
            )
            or []
        )

        if isinstance(
            all_locations,
            list,
        ):
            locations.extend(
                str(value)
                for value in all_locations
                if value
            )

        primary_location = (
            categories.get(
                "location"
            )
        )

        if (
            primary_location
            and str(primary_location)
            not in locations
        ):
            locations.append(
                str(primary_location)
            )

        workplace = str(
            raw_job.get(
                "workplaceType",
                "",
            )
            or ""
        ).lower()

        salary = (
            raw_job.get(
                "salaryRange"
            )
            or {}
        )

        if not isinstance(
            salary,
            dict,
        ):
            salary = {}

        description = str(
            raw_job.get(
                "descriptionPlain",
                "",
            )
            or ""
        ).strip()

        apply_url = str(
            raw_job.get(
                "applyUrl",
                "",
            )
            or ""
        ).strip()

        hosted_url = str(
            raw_job.get(
                "hostedUrl",
                "",
            )
            or ""
        ).strip()

        posted_at = self._first_value(
            raw_job,
            (
                "createdAt",
                "updatedAt",
                "created_at",
                "updated_at",
                "date",
                "postedAt",
            ),
        )

        return Job(
            source=self.name,

            source_job_id=str(
                raw_job.get(
                    "id",
                    "",
                )
                or ""
            ),

            title=str(
                raw_job.get(
                    "text",
                    "",
                )
                or ""
            ).strip(),

            company=self.board_name,

            location=locations,

            remote=(
                workplace == "remote"
                or "remote" in " ".join(
                    locations
                ).lower()
                or "remote" in description.lower()
            ),

            employment_type=(
                categories.get(
                    "commitment"
                )
            ),

            experience=Experience(),

            salary=Salary(
                min_lpa=self._number(
                    salary.get(
                        "min"
                    )
                ),

                max_lpa=self._number(
                    salary.get(
                        "max"
                    )
                ),

                currency=str(
                    salary.get(
                        "currency",
                        "USD",
                    )
                    or "USD"
                ).upper(),
            ),

            skills=[
                str(value)
                for value in (
                    categories.get(
                        "team"
                    ),
                    categories.get(
                        "department"
                    ),
                    categories.get(
                        "level"
                    ),
                )
                if value
            ],

            description=description,

            apply_url=apply_url,

            source_url=(
                hosted_url
                or apply_url
            ),

            posted_at=posted_at,

            metadata={
                "fleet_adapter": (
                    "ats_public"
                ),
                "ats_platform": (
                    "lever"
                ),
                "ats_board": (
                    self.board_name
                ),
            },
        )

    # ================================================================
    # ASHBY
    # ================================================================

    def _normalize_ashby(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        locations: List[str] = []

        primary_location = (
            raw_job.get(
                "location"
            )
        )

        if primary_location:
            locations.append(
                str(primary_location)
            )

        secondary = (
            raw_job.get(
                "secondaryLocations"
            )
            or []
        )

        if isinstance(
            secondary,
            list,
        ):
            for item in secondary:
                if isinstance(
                    item,
                    dict,
                ):
                    value = (
                        item.get(
                            "location"
                        )
                        or item.get(
                            "name"
                        )
                    )

                    if value:
                        locations.append(
                            str(value)
                        )

                elif item:
                    locations.append(
                        str(item)
                    )

        compensation = (
            raw_job.get(
                "compensation"
            )
            or {}
        )

        if not isinstance(
            compensation,
            dict,
        ):
            compensation = {}

        description = str(
            raw_job.get(
                "descriptionPlain",
                raw_job.get(
                    "description",
                    "",
                ),
            )
            or ""
        ).strip()

        job_url = str(
            raw_job.get(
                "jobUrl",
                raw_job.get(
                    "applyUrl",
                    "",
                ),
            )
            or ""
        ).strip()

        apply_url = str(
            raw_job.get(
                "applyUrl",
                raw_job.get(
                    "jobUrl",
                    "",
                ),
            )
            or ""
        ).strip()

        posted_at = self._first_value(
            raw_job,
            (
                "publishedAt",
                "published_at",
                "createdAt",
                "created_at",
                "updatedAt",
                "updated_at",
                "datePosted",
                "date_posted",
            ),
        )

        return Job(
            source=self.name,

            source_job_id=str(
                raw_job.get(
                    "jobUrl",
                    "",
                )
                or raw_job.get(
                    "applyUrl",
                    "",
                )
                or raw_job.get(
                    "id",
                    "",
                )
                or ""
            ),

            title=str(
                raw_job.get(
                    "title",
                    "",
                )
                or ""
            ).strip(),

            company=self.board_name,

            location=locations,

            remote=self._detect_remote(
                raw_job
            ),

            employment_type=None,

            experience=Experience(),

            salary=Salary(
                min_lpa=self._number(
                    compensation.get(
                        "min"
                    )
                ),

                max_lpa=self._number(
                    compensation.get(
                        "max"
                    )
                ),

                currency=str(
                    compensation.get(
                        "currency",
                        "USD",
                    )
                    or "USD"
                ).upper(),
            ),

            skills=[],

            description=description,

            apply_url=apply_url,

            source_url=(
                job_url
                or apply_url
            ),

            posted_at=posted_at,

            metadata={
                "fleet_adapter": (
                    "ats_public"
                ),
                "ats_platform": (
                    "ashby"
                ),
                "ats_board": (
                    self.board_name
                ),
            },
        )

    # ================================================================
    # HELPERS
    # ================================================================

    @staticmethod
    def _first_value(
        data: Dict[str, Any],
        keys: tuple[str, ...],
    ) -> Any:
        for key in keys:
            value = data.get(
                key
            )

            if value not in (
                None,
                "",
            ):
                return value

        return None

    @staticmethod
    def _number(
        value: Any,
    ) -> Optional[float]:
        if value is None:
            return None

        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return (
            number
            if number > 0
            else None
        )

    @staticmethod
    def _detect_remote(
        raw_job: Dict[str, Any],
    ) -> bool:
        values: List[str] = []

        for key in (
            "title",
            "location",
            "workplaceType",
            "description",
            "descriptionPlain",
            "content",
            "employment",
        ):
            value = raw_job.get(
                key
            )

            if isinstance(
                value,
                list,
            ):
                values.extend(
                    str(item)
                    for item in value
                    if item
                )

            elif isinstance(
                value,
                dict,
            ):
                values.extend(
                    str(item)
                    for item in value.values()
                    if item
                )

            elif value:
                values.append(
                    str(value)
                )

        text = " ".join(
            values
        ).lower()

        return any(
            marker in text
            for marker in (
                "remote",
                "work from home",
                "wfh",
                "distributed",
            )
        )


__all__ = [
    "PublicAtsJobSource",
]