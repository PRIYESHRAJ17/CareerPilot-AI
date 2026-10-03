from __future__ import annotations

import re

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from email.utils import (
    parsedate_to_datetime,
)

from typing import (
    List,
    Optional,
    Set,
)

from backend.schemas.candidate import (
    CandidateProfile,
)

from backend.schemas.job import Job


class JobFilter:
    """
    Production CareerPilot opportunity-quality filter.

    The filter deliberately avoids over-filtering.

    It keeps:

    - jobs with undisclosed salary
    - remote opportunities
    - country-level locations
    - jobs with sparse provider metadata

    It rejects:

    - clearly stale jobs
    - impossible/future dates
    - clearly irrelevant roles
    - incompatible locations
    - incompatible salary floors
    - incompatible work modes

    Location matching is intentionally semantic rather
    than exact-string-only.
    """

    MAX_JOB_AGE_DAYS = 120

    FUTURE_GRACE_DAYS = 2

    GENERIC_ROLE_TERMS = {
        "engineer",
        "engineering",
        "developer",
        "development",
        "manager",
        "management",
        "analyst",
        "specialist",
        "scientist",
        "architect",
        "designer",
        "lead",
        "senior",
        "junior",
        "associate",
        "principal",
        "staff",
        "intern",
    }

    LOCATION_ALIASES = {
        "bangalore": {
            "bangalore",
            "bengaluru",
            "karnataka",
        },

        "bengaluru": {
            "bangalore",
            "bengaluru",
            "karnataka",
        },

        "mumbai": {
            "mumbai",
            "bombay",
            "maharashtra",
        },

        "delhi": {
            "delhi",
            "new delhi",
            "ncr",
            "national capital region",
        },

        "new delhi": {
            "delhi",
            "new delhi",
            "ncr",
            "national capital region",
        },

        "gurgaon": {
            "gurgaon",
            "gurugram",
            "haryana",
            "ncr",
        },

        "gurugram": {
            "gurgaon",
            "gurugram",
            "haryana",
            "ncr",
        },

        "noida": {
            "noida",
            "uttar pradesh",
            "ncr",
        },

        "hyderabad": {
            "hyderabad",
            "telangana",
        },

        "pune": {
            "pune",
            "maharashtra",
        },

        "chennai": {
            "chennai",
            "madras",
            "tamil nadu",
        },

        "kolkata": {
            "kolkata",
            "calcutta",
            "west bengal",
        },

        "ahmedabad": {
            "ahmedabad",
            "gujarat",
        },

        "jaipur": {
            "jaipur",
            "rajasthan",
        },

        "kochi": {
            "kochi",
            "cochin",
            "kerala",
        },
    }

    INDIA_TERMS = {
        "india",
        "indian",
        "remote india",
        "india remote",
    }

    def filter(
        self,
        jobs: List[Job],
        candidate: CandidateProfile,
    ) -> List[Job]:

        filtered: List[
            Job
        ] = []

        for job in jobs:

            if not self._freshness_match(
                job
            ):
                continue

            if not self._role_match(
                job,
                candidate,
            ):
                continue

            if not self._location_match(
                job,
                candidate,
            ):
                continue

            if not self._salary_match(
                job,
                candidate,
            ):
                continue

            if not self._work_mode_match(
                job,
                candidate,
            ):
                continue

            filtered.append(
                job
            )

        return filtered

    # ======================================================
    # FRESHNESS
    # ======================================================

    @classmethod
    def _freshness_match(
        cls,
        job: Job,
    ) -> bool:

        posted_at = (
            job.posted_at
        )

        # Missing dates are retained because many real
        # providers don't expose reliable timestamps.
        if not posted_at:
            return True

        parsed = cls._parse_datetime(
            posted_at
        )

        if parsed is None:
            return True

        now = datetime.now(
            timezone.utc
        )

        if parsed > (
            now
            + timedelta(
                days=cls.FUTURE_GRACE_DAYS
            )
        ):
            return False

        oldest = (
            now
            - timedelta(
                days=cls.MAX_JOB_AGE_DAYS
            )
        )

        return parsed >= oldest

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> Optional[
        datetime
    ]:

        if isinstance(
            value,
            datetime,
        ):

            dt = value

        elif isinstance(
            value,
            (int, float),
        ):

            numeric = float(
                value
            )

            if numeric > 10**11:
                numeric /= 1000.0

            try:

                dt = datetime.fromtimestamp(
                    numeric,
                    tz=timezone.utc,
                )

            except (
                ValueError,
                OverflowError,
            ):

                return None

        else:

            text = str(
                value
            ).strip()

            if not text:
                return None

            # ISO-8601
            try:

                dt = datetime.fromisoformat(
                    text.replace(
                        "Z",
                        "+00:00",
                    )
                )

            except ValueError:

                # RFC 2822 / RSS-style timestamps
                try:

                    dt = parsedate_to_datetime(
                        text
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    return None

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    # ======================================================
    # ROLE RELEVANCE
    # ======================================================

    @classmethod
    def _role_match(
        cls,
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

        roles = list(
            candidate.career_goal.target_roles
            or []
        )

        if not roles:

            if candidate.headline:
                roles = [
                    candidate.headline
                ]

        if not roles:
            return True

        title = cls._normalize_text(
            job.title
        )

        description = cls._normalize_text(
            job.description
        )

        skills = " ".join(
            cls._normalize_text(
                skill
            )
            for skill
            in (
                job.skills
                or []
            )
        )

        searchable = (
            f"{title} "
            f"{skills} "
            f"{description}"
        )

        for role in roles:

            normalized_role = (
                cls._normalize_text(
                    role
                )
            )

            if not normalized_role:
                continue

            # Direct phrase match.
            if normalized_role in title:

                return True

            terms = [
                token
                for token
                in normalized_role.split()
                if token
            ]

            if not terms:
                continue

            anchor_terms = [
                term
                for term
                in terms
                if term
                not in cls.GENERIC_ROLE_TERMS
            ]

            # If the role consists only of generic terms,
            # matching one generic term is sufficient.
            if not anchor_terms:

                if any(
                    term in title
                    for term
                    in terms
                ):
                    return True

                continue

            # At least one meaningful role anchor must
            # exist in the title/skills/description.
            if not any(
                cls._contains_token(
                    searchable,
                    term,
                )
                for term
                in anchor_terms
            ):
                continue

            # A generic role token in the title + a semantic
            # anchor somewhere in the listing is a strong
            # enough match.
            generic_in_title = any(
                cls._contains_token(
                    title,
                    term,
                )
                for term
                in cls.GENERIC_ROLE_TERMS
                if term in terms
            )

            anchor_in_title = any(
                cls._contains_token(
                    title,
                    term,
                )
                for term
                in anchor_terms
            )

            if (
                anchor_in_title
                or generic_in_title
            ):
                return True

            # Finally allow skill/description evidence when
            # the title is generic.
            if any(
                cls._contains_token(
                    searchable,
                    term,
                )
                for term
                in anchor_terms
            ):
                return True

        return False

    # ======================================================
    # LOCATION
    # ======================================================

    @classmethod
    def _location_match(
        cls,
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

        preferred = list(
            candidate.preferred_locations
            or []
        )

        if not preferred:
            return True

        # Explicit remote jobs are location-compatible.
        if job.remote:
            return True

        job_location_text = cls._normalize_text(
            " ".join(
                job.location
                or []
            )
        )

        # Missing provider location should not destroy a
        # potentially useful opportunity.
        if not job_location_text:

            return True

        job_terms = cls._expand_location_terms(
            job_location_text
        )

        for location in preferred:

            normalized = (
                cls._normalize_text(
                    location
                )
            )

            if not normalized:
                continue

            accepted_terms = (
                cls.LOCATION_ALIASES.get(
                    normalized,
                    {normalized},
                )
            )

            if job_terms.intersection(
                accepted_terms
            ):
                return True

            # Exact substring fallback.
            if normalized in (
                job_location_text
            ):
                return True

            # --------------------------------------------------
            # India-wide opportunities:
            #
            # A job explicitly scoped to India is retained for
            # an Indian city request because many providers
            # publish "India" while the actual role may support
            # remote/hybrid or multiple Indian offices.
            # --------------------------------------------------

            if (
                cls._is_indian_location(
                    normalized
                )
                and
                (
                    job_terms
                    & cls.INDIA_TERMS
                )
            ):
                return True

            if (
                cls._looks_like_indian_city(
                    normalized
                )
                and
                (
                    job_terms
                    & cls.INDIA_TERMS
                )
            ):
                return True

        return False

    @classmethod
    def _expand_location_terms(
        cls,
        text: str,
    ) -> Set[str]:

        terms = set()

        normalized = (
            cls._normalize_text(
                text
            )
        )

        if not normalized:
            return terms

        terms.add(
            normalized
        )

        # Add token-level forms.
        terms.update(
            normalized.split()
        )

        # Add all known aliases.
        for key, aliases in (
            cls.LOCATION_ALIASES.items()
        ):

            if (
                key in normalized
                or any(
                    alias
                    in normalized
                    for alias
                    in aliases
                )
            ):

                terms.update(
                    aliases
                )

        if any(
            token in normalized
            for token in cls.INDIA_TERMS
        ):

            terms.update(
                cls.INDIA_TERMS
            )

        return terms

    @classmethod
    def _is_indian_location(
        cls,
        value: str,
    ) -> bool:

        normalized = (
            cls._normalize_text(
                value
            )
        )

        if (
            normalized
            in cls.INDIA_TERMS
        ):
            return True

        return any(
            normalized
            in aliases
            for aliases
            in cls.LOCATION_ALIASES.values()
        )

    @classmethod
    def _looks_like_indian_city(
        cls,
        value: str,
    ) -> bool:

        normalized = (
            cls._normalize_text(
                value
            )
        )

        return any(
            normalized
            in aliases
            for aliases
            in cls.LOCATION_ALIASES.values()
        )

    # ======================================================
    # SALARY
    # ======================================================

    @staticmethod
    def _salary_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

        minimum = (
            candidate
            .career_goal
            .minimum_salary_lpa
        )

        if minimum is None:
            return True

        salary_min = (
            job.salary.min_lpa
        )

        salary_max = (
            job.salary.max_lpa
        )

        # Undisclosed salary remains eligible.
        if (
            salary_min is None
            and salary_max is None
        ):
            return True

        if salary_min is not None:

            return (
                salary_min
                >= minimum
            )

        if salary_max is not None:

            return (
                salary_max
                >= minimum
            )

        return True

    # ======================================================
    # WORK MODE
    # ======================================================

    @staticmethod
    def _work_mode_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

        preferred = {
            mode.casefold().strip()
            for mode
            in (
                candidate
                .preferred_work_modes
                or []
            )
        }

        if not preferred:
            return True

        if job.remote:

            return bool(
                preferred
                & {
                    "remote",
                    "work from home",
                    "wfh",
                }
            )

        # For non-remote jobs, treat missing explicit
        # provider mode as compatible with onsite/hybrid
        # preferences. Providers often don't classify
        # hybrid accurately.
        return bool(
            preferred
            & {
                "onsite",
                "on-site",
                "hybrid",
            }
        )

    # ======================================================
    # HELPERS
    # ======================================================

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        normalized = (
            str(value or "")
            .casefold()
            .strip()
        )

        normalized = re.sub(
            r"[^a-z0-9\s]+",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized.strip()

    @classmethod
    def _contains_token(
        cls,
        text: str,
        token: str,
    ) -> bool:

        normalized_text = (
            cls._normalize_text(
                text
            )
        )

        normalized_token = (
            cls._normalize_text(
                token
            )
        )

        if not normalized_token:
            return False

        if (
            " "
            in normalized_token
        ):

            return (
                normalized_token
                in normalized_text
            )

        return bool(
            re.search(
                rf"\b{re.escape(normalized_token)}\b",
                normalized_text,
            )
        )