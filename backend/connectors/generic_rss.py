import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from backend.connectors.base import JobSource
from backend.schemas.job import Experience, Job, Salary
from backend.schemas.provider_fleet import (
    ProviderDefinition,
)


class GenericRssJobSource(JobSource):
    """
    Generic RSS/Atom job-feed adapter.

    Designed for sources that expose published job listings
    through RSS or Atom without requiring a custom parser.

    The feed is fetched from the configured endpoint and
    filtered locally by query/location when necessary.
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

        if definition.adapter_type != "rss":
            raise ValueError(
                "GenericRssJobSource requires "
                "adapter_type='rss'."
            )

        self.definition = definition

        self.name = definition.name

        self.display_name = (
            definition.display_name
        )

        self.category = (
            definition.category
        )

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
    # REQUEST
    # =========================================================

    def _fetch_feed(
        self,
    ) -> str:

        headers = dict(
            self.definition.headers
        )

        headers.setdefault(
            "Accept",
            (
                "application/rss+xml,"
                " application/atom+xml,"
                " application/xml,"
                " text/xml"
            ),
        )

        headers.setdefault(
            "User-Agent",
            (
                "CareerPilot-AI/"
                "provider-fleet"
            ),
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

                response = requests.get(
                    self.definition.endpoint,
                    params=dict(
                        self.definition.static_params
                    ),
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
                                    len(
                                        backoff
                                    ) - 1,
                                )
                            ]
                        )

                        continue

                response.raise_for_status()

                return response.text

            except requests.RequestException as exc:

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
                    f"{self.name} RSS request failed "
                    f"after {self.max_retries} attempts: "
                    f"{exc}"
                ) from exc

        raise RuntimeError(
            f"{self.name} RSS request failed: "
            f"{last_error}"
        )

    # =========================================================
    # XML HELPERS
    # =========================================================

    @staticmethod
    def _local_name(
        tag: str,
    ) -> str:

        if "}" in tag:
            return tag.rsplit(
                "}",
                1,
            )[-1].lower()

        return tag.lower()

    @classmethod
    def _child_text(
        cls,
        element: ET.Element,
        *names: str,
    ) -> str:

        wanted = {
            name.lower()
            for name in names
        }

        for child in list(
            element
        ):

            name = cls._local_name(
                child.tag
            )

            if name not in wanted:
                continue

            text = (
                "".join(
                    child.itertext()
                )
                .strip()
            )

            if text:
                return text

        return ""

    @classmethod
    def _child_link(
        cls,
        element: ET.Element,
    ) -> str:

        for child in list(
            element
        ):

            if (
                cls._local_name(
                    child.tag
                )
                != "link"
            ):
                continue

            href = (
                child.attrib.get(
                    "href"
                )
            )

            if href:
                return href.strip()

            text = (
                "".join(
                    child.itertext()
                )
                .strip()
            )

            if text:
                return text

        return ""

    @classmethod
    def _items(
        cls,
        root: ET.Element,
    ) -> List[ET.Element]:

        items = [
            element
            for element in root.iter()
            if cls._local_name(
                element.tag
            )
            in {
                "item",
                "entry",
            }
        ]

        return items

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

        del filters

        self.validate_configuration()

        xml_text = self._fetch_feed()

        try:

            root = ET.fromstring(
                xml_text
            )

        except ET.ParseError as exc:

            raise RuntimeError(
                f"{self.name} returned invalid "
                "RSS/Atom XML."
            ) from exc

        candidates: List[
            Job
        ] = []

        for element in self._items(
            root
        ):

            raw_job = {
                "title": self._child_text(
                    element,
                    "title",
                ),

                "description": self._child_text(
                    element,
                    "description",
                    "summary",
                    "content",
                ),

                "link": self._child_link(
                    element
                ),

                "guid": self._child_text(
                    element,
                    "guid",
                    "id",
                ),

                "published": self._child_text(
                    element,
                    "pubdate",
                    "published",
                    "updated",
                ),

                "author": self._child_text(
                    element,
                    "author",
                    "creator",
                ),

                "category": self._child_text(
                    element,
                    "category",
                ),
            }

            job = self.normalize_and_enrich(
                raw_job
            )

            if not self._matches(
                job,
                query=query,
                location=location,
            ):
                continue

            candidates.append(
                job
            )

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

        return candidates[
            start:end
        ]

    # =========================================================
    # MATCHING
    # =========================================================

    @staticmethod
    def _matches(
        job: Job,
        query: str,
        location: Optional[str],
    ) -> bool:

        haystack = " ".join(
            [
                job.title,
                job.company,
                job.description,
                " ".join(
                    job.skills
                ),
            ]
        ).lower()

        if query:

            query_tokens = [
                token
                for token
                in re.findall(
                    r"[a-z0-9]+",
                    query.lower(),
                )
                if len(token) >= 2
            ]

            if query_tokens and not all(
                token in haystack
                for token
                in query_tokens
            ):
                return False

        if location:

            requested = (
                location.lower()
            )

            job_locations = " ".join(
                job.location
            ).lower()

            if (
                requested not in haystack
                and requested
                not in job_locations
            ):
                return False

        return True

    # =========================================================
    # HEALTH
    # =========================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        try:

            xml_text = self._fetch_feed()

            root = ET.fromstring(
                xml_text
            )

            items = self._items(
                root
            )

            return {
                "source": self.name,
                "healthy": True,
                "status_code": 200,
                "message": (
                    "RSS/Atom feed reachable; "
                    f"{len(items)} items discovered."
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

        title = str(
            raw_job.get(
                "title",
                "",
            )
        ).strip()

        description = str(
            raw_job.get(
                "description",
                "",
            )
        ).strip()

        link = str(
            raw_job.get(
                "link",
                "",
            )
        ).strip()

        guid = str(
            raw_job.get(
                "guid",
                "",
            )
        ).strip()

        author = str(
            raw_job.get(
                "author",
                "",
            )
        ).strip()

        category = str(
            raw_job.get(
                "category",
                "",
            )
        ).strip()

        company = (
            self._extract_company(
                author,
                description,
            )
        )

        locations = (
            self._extract_locations(
                description
            )
        )

        posted_at = (
            self._normalize_date(
                raw_job.get(
                    "published"
                )
            )
        )

        salary_min, salary_max, currency = (
            self._extract_salary(
                description
            )
        )

        skills = []

        if category:
            skills.append(
                category
            )

        return Job(
            source=self.name,

            source_job_id=(
                guid
                or link
                or (
                    f"{company}-"
                    f"{title}"
                )
            ),

            title=title,

            company=company,

            location=locations,

            remote=(
                self.definition.remote_default
                or self._detect_remote(
                    title,
                    description,
                )
            ),

            employment_type=None,

            experience=Experience(),

            salary=Salary(
                min_lpa=salary_min,
                max_lpa=salary_max,
                currency=currency,
            ),

            skills=skills,

            description=description,

            apply_url=link,

            source_url=link,

            posted_at=posted_at,

            metadata={
                "fleet_adapter": "rss",
                "provider_definition": (
                    self.definition.name
                ),
                "feed_author": author,
                "feed_category": category,
            },
        )

    # =========================================================
    # HEURISTICS
    # =========================================================

    @staticmethod
    def _extract_company(
        author: str,
        description: str,
    ) -> str:

        if author:
            return author

        patterns = [
            r"(?:company|employer)\s*:\s*([^\n|]+)",
            r"(?:at|@)\s+([A-Z][A-Za-z0-9&.\- ]{2,60})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                description,
                flags=re.IGNORECASE,
            )

            if match:

                company = (
                    match.group(
                        1
                    )
                    .strip()
                )

                if company:
                    return company

        return "Unknown"

    @staticmethod
    def _extract_locations(
        text: str,
    ) -> List[str]:

        locations = []

        patterns = [
            r"(?:location|locations?)\s*:\s*([^\n|]+)",
            r"(?:based in)\s*:\s*([^\n|]+)",
        ]

        for pattern in patterns:

            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            for match in matches:

                for part in re.split(
                    r",|/|\|",
                    match,
                ):

                    cleaned = (
                        part.strip()
                    )

                    if (
                        cleaned
                        and cleaned.casefold()
                        not in {
                            location.casefold()
                            for location
                            in locations
                        }
                    ):
                        locations.append(
                            cleaned
                        )

        return locations

    @staticmethod
    def _extract_salary(
        text: str,
    ) -> tuple[
        Optional[float],
        Optional[float],
        str,
    ]:

        currency = "USD"

        lowered = text.lower()

        if "inr" in lowered or "₹" in text:
            currency = "INR"
        elif "eur" in lowered or "€" in text:
            currency = "EUR"
        elif "gbp" in lowered or "£" in text:
            currency = "GBP"

        matches = re.findall(
            r"(?:[$€£₹]\s*)?"
            r"(\d[\d,]*(?:\.\d+)?)"
            r"(?:\s*(?:-|to)\s*"
            r"(?:[$€£₹]\s*)?"
            r"(\d[\d,]*(?:\.\d+)?))?"
            r"\s*(?:k|K)?",
            text,
        )

        if not matches:
            return None, None, currency

        # Deliberately conservative: use only a clearly useful
        # range from text containing salary-related wording.
        salary_context = any(
            marker in lowered
            for marker in (
                "salary",
                "compensation",
                "pay",
                "usd",
                "eur",
                "gbp",
                "inr",
                "$",
                "€",
                "£",
                "₹",
            )
        )

        if not salary_context:
            return None, None, currency

        for low, high in matches:

            if not low:
                continue

            minimum = float(
                low.replace(
                    ",",
                    "",
                )
            )

            maximum = (
                float(
                    high.replace(
                        ",",
                        "",
                    )
                )
                if high
                else None
            )

            return (
                minimum,
                maximum,
                currency,
            )

        return None, None, currency

    @staticmethod
    def _detect_remote(
        title: str,
        description: str,
    ) -> bool:

        text = (
            f"{title} "
            f"{description}"
        ).lower()

        return any(
            token in text
            for token in (
                "remote",
                "work from home",
                "wfh",
                "work-from-home",
            )
        )

    @staticmethod
    def _normalize_date(
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return None

        try:

            parsed = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )

            return parsed.isoformat()

        except ValueError:

            return text