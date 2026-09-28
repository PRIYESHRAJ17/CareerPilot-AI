import os
import time
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary
from backend.schemas.provider_fleet import (
    ProviderDefinition,
)


class GenericJsonJobSource(JobSource):
    """
    Generic JSON job provider.

    One implementation can service many providers whose APIs
    differ mainly in endpoint, parameters and JSON field paths.

    Supported:

        GET / POST
        query parameter mapping
        location parameter mapping
        pagination
        credentials
        nested JSON response extraction
        universal Job normalization
        provider provenance
    """

    RETRYABLE_STATUS_CODES = {
        408,
        425,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        definition: ProviderDefinition,
        timeout: int = 20,
        max_retries: int = 3,
    ) -> None:

        if definition.adapter_type != "json":
            raise ValueError(
                "GenericJsonJobSource requires "
                "adapter_type='json'."
            )

        self.definition = definition

        self.name = definition.name
        self.display_name = (
            definition.display_name
        )
        self.category = definition.category
        self.countries = list(
            definition.countries
        )

        self.requires_credentials = (
            definition.requires_credentials
        )

        self.credential_env_vars = list(
            definition.credential_env_vars
        )

        self.supports_paging = (
            definition.supports_paging
        )

        self.supports_remote_filter = (
            definition.supports_remote_filter
        )

        self.supports_salary_filter = (
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

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def validate_configuration(
        self,
    ) -> None:

        if not self.requires_credentials:
            return

        missing = [
            variable
            for variable
            in self.credential_env_vars
            if not os.getenv(variable)
        ]

        if missing:
            raise RuntimeError(
                f"Missing credentials for provider "
                f"'{self.name}': "
                f"{', '.join(missing)}"
            )

    # =========================================================
    # REQUEST BUILDING
    # =========================================================

    def _headers(self) -> Dict[str, str]:

        headers = dict(
            self.definition.headers
        )

        headers.setdefault(
            "Accept",
            "application/json",
        )

        headers.setdefault(
            "User-Agent",
            "CareerPilot-AI/"
            "provider-fleet",
        )

        return headers

    def _params(
        self,
        query: str,
        location: Optional[str],
        page: int,
        limit: int,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:

        params = dict(
            self.definition.static_params
        )

        if (
            self.definition.query_parameter
            and query
        ):

            params[
                self.definition.query_parameter
            ] = query

        if (
            self.definition.location_parameter
            and location
        ):

            params[
                self.definition.location_parameter
            ] = location

        if (
            self.definition.limit_parameter
        ):

            params[
                self.definition.limit_parameter
            ] = limit

        if (
            self.definition.page_parameter
        ):

            params[
                self.definition.page_parameter
            ] = page

        # Provider-specific optional filters.
        params.update(
            {
                key: value
                for key, value
                in filters.items()
                if value is not None
            }
        )

        return params

    # =========================================================
    # REQUEST
    # =========================================================

    def _request(
        self,
        *,
        params: Dict[str, Any],
    ) -> Any:

        method = (
            self.definition.method
            .strip()
            .upper()
        )

        backoff = [
            1,
            3,
            7,
        ]

        last_error: Optional[
            Exception
        ] = None

        for attempt in range(
            self.max_retries
        ):

            try:

                if method == "POST":

                    response = requests.post(
                        self.definition.endpoint,
                        params=None,
                        json=params,
                        headers=self._headers(),
                        timeout=self.timeout,
                    )

                else:

                    response = requests.get(
                        self.definition.endpoint,
                        params=params,
                        headers=self._headers(),
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
                                    len(
                                        backoff
                                    ) - 1,
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
                                len(
                                    backoff
                                ) - 1,
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

    # =========================================================
    # RESPONSE PATH
    # =========================================================

    @staticmethod
    def _get_path(
        value: Any,
        path: Optional[str],
    ) -> Any:

        if path is None or not path:
            return value

        current = value

        for token in path.split("."):

            token = token.strip()

            if not token:
                continue

            if isinstance(
                current,
                dict,
            ):

                current = current.get(
                    token
                )

            elif isinstance(
                current,
                list,
            ):

                try:

                    current = current[
                        int(token)
                    ]

                except (
                    ValueError,
                    IndexError,
                ):

                    return None

            else:

                return None

        return current

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:

        self.validate_configuration()

        data = self._request(
            params=self._params(
                query=query,
                location=location,
                page=page,
                limit=limit,
                filters=filters,
            )
        )

        jobs = self._get_path(
            data,
            self.definition.response_jobs_path,
        )

        if isinstance(
            jobs,
            dict,
        ):

            jobs = [
                jobs
            ]

        if not isinstance(
            jobs,
            list,
        ):

            return []

        return [
            self.normalize_and_enrich(
                raw_job
            )
            for raw_job in jobs
            if isinstance(
                raw_job,
                dict,
            )
        ]

    # =========================================================
    # HEALTH
    # =========================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        try:

            self.validate_configuration()

            data = self._request(
                params=self._params(
                    query="software engineer",
                    location=None,
                    page=1,
                    limit=1,
                    filters={},
                )
            )

            jobs = self._get_path(
                data,
                self.definition.response_jobs_path,
            )

            healthy = isinstance(
                jobs,
                list,
            )

            return {
                "source": self.name,
                "healthy": healthy,
                "status_code": 200,
                "message": (
                    "Provider API reachable."
                    if healthy
                    else (
                        "Provider returned an "
                        "unexpected jobs structure."
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

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def normalize(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:

        fields = (
            self.definition.field_paths
        )

        def value(
            key: str,
            default: Any = None,
        ) -> Any:

            path = fields.get(
                key
            )

            result = self._get_path(
                raw_job,
                path,
            )

            return (
                default
                if result is None
                else result
            )

        title = str(
            value(
                "title",
                "",
            )
        ).strip()

        company = str(
            value(
                "company",
                "Unknown",
            )
        ).strip()

        location_value = value(
            "location",
            [],
        )

        locations = (
            self._normalize_locations(
                location_value
            )
        )

        description = str(
            value(
                "description",
                "",
            )
        ).strip()

        apply_url = str(
            value(
                "apply_url",
                "",
            )
        ).strip()

        source_url = str(
            value(
                "source_url",
                apply_url,
            )
        ).strip()

        source_job_id = str(
            value(
                "source_job_id",
                "",
            )
        ).strip()

        remote = value(
            "remote",
            self.definition.remote_default,
        )

        salary_min = self._number(
            value(
                "salary_min"
            )
        )

        salary_max = self._number(
            value(
                "salary_max"
            )
        )

        salary_currency = str(
            value(
                "salary_currency",
                self.definition.salary_currency
                or "USD",
            )
        ).upper()

        employment_type = value(
            "employment_type"
        )

        posted_at = value(
            "posted_at"
        )

        skills_value = value(
            "skills",
            [],
        )

        skills = self._normalize_skills(
            skills_value
        )

        return Job(
            source=self.name,

            source_job_id=(
                source_job_id
                or apply_url
                or (
                    f"{company}-"
                    f"{title}"
                )
            ),

            title=title,

            company=company,

            location=locations,

            remote=bool(
                remote
            ),

            employment_type=(
                str(
                    employment_type
                ).strip()
                if employment_type
                else None
            ),

            experience=Experience(),

            salary=Salary(
                min_lpa=salary_min,
                max_lpa=salary_max,
                currency=salary_currency,
            ),

            skills=skills,

            description=description,

            apply_url=apply_url,

            source_url=source_url,

            posted_at=(
                str(posted_at)
                if posted_at is not None
                else None
            ),

            metadata={
                "fleet_adapter": "generic_json",
                "provider_definition": (
                    self.definition.name
                ),
            },
        )

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> Optional[float]:

        if value is None:
            return None

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

        return (
            result
            if result > 0
            else None
        )

    @staticmethod
    def _normalize_locations(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):

            values = value

        else:

            values = str(
                value
            ).split(",")

        result: List[str] = []

        seen = set()

        for item in values:

            if isinstance(
                item,
                dict,
            ):
                item = (
                    item.get(
                        "name"
                    )
                    or item.get(
                        "location"
                    )
                    or ""
                )

            cleaned = str(
                item
            ).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)

            result.append(
                cleaned
            )

        return result

    @staticmethod
    def _normalize_skills(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):

            values = [
                item.strip()
                for item in value.split(
                    ","
                )
            ]

        elif isinstance(
            value,
            list,
        ):

            values = value

        else:

            return []

        result: List[str] = []

        seen = set()

        for item in values:

            if isinstance(
                item,
                dict,
            ):

                item = (
                    item.get(
                        "name"
                    )
                    or item.get(
                        "label"
                    )
                    or ""
                )

            cleaned = str(
                item
            ).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)

            result.append(
                cleaned
            )

        return result