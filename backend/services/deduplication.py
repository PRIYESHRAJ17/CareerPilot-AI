import re
from typing import Dict, List

from backend.schemas.job import Job


class JobDeduplicator:
    """
    Groups likely duplicate listings into canonical
    opportunities while preserving source-level provenance.

    A canonical opportunity can therefore represent:

        One opportunity
            ├── Adzuna listing
            ├── Jooble listing
            ├── Himalayas listing
            └── ...future sources

    Each source record retains its own identifiers,
    URLs and source-specific evidence.
    """

    def deduplicate(
        self,
        jobs: List[Job],
    ) -> List[Job]:

        groups: Dict[
            str,
            List[Job],
        ] = {}

        for job in jobs:
            fingerprint = (
                self._fingerprint(job)
            )

            groups.setdefault(
                fingerprint,
                [],
            ).append(job)

        return [
            self._merge_group(group)
            for group in groups.values()
        ]

    # ==================================================
    # Fingerprinting
    # ==================================================

    def _fingerprint(
        self,
        job: Job,
    ) -> str:

        company = self._normalize_company(
            job.company
        )

        title = self._normalize_title(
            job.title
        )

        location = self._normalize_location(
            job.location
        )

        return "|".join(
            [
                company,
                title,
                location,
            ]
        )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        value = (
            value or ""
        ).lower().strip()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    @classmethod
    def _normalize_company(
        cls,
        value: str,
    ) -> str:

        normalized = (
            cls._normalize_text(value)
        )

        # Common legal/company suffixes.
        normalized = re.sub(
            r"\b(private|pvt)\b",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\b(limited|ltd)\b",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\b(incorporated|inc)\b",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\b(corporation|corp)\b",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    @classmethod
    def _normalize_title(
        cls,
        value: str,
    ) -> str:

        normalized = (
            cls._normalize_text(value)
        )

        replacements = {
            "software development engineer":
                "software engineer",

            "software dev engineer":
                "software engineer",

            "sde":
                "software engineer",

            "swe":
                "software engineer",

            "sr":
                "senior",

            "jr":
                "junior",
        }

        for old, new in replacements.items():
            normalized = re.sub(
                rf"\b{re.escape(old)}\b",
                new,
                normalized,
            )

        # Remove common noise that often differs
        # between job-board versions.
        noise_patterns = [
            r"\bfull time\b",
            r"\bfulltime\b",
            r"\bpart time\b",
            r"\bcontract\b",
            r"\bremote\b",
            r"\bhybrid\b",
            r"\bonsite\b",
        ]

        for pattern in noise_patterns:
            normalized = re.sub(
                pattern,
                " ",
                normalized,
            )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    @classmethod
    def _normalize_location(
        cls,
        locations: List[str],
    ) -> str:

        normalized = [
            cls._normalize_text(
                location
            )
            for location in (
                locations or []
            )
        ]

        normalized = sorted(
            set(
                location
                for location in normalized
                if location
            )
        )

        return "|".join(
            normalized
        )

    # ==================================================
    # Source record creation
    # ==================================================

    @staticmethod
    def _source_record(
        job: Job,
    ) -> dict:
        """
        Create a durable source-level provenance record.

        This is intentionally richer than just
        source + source_job_id so a future detail panel
        can show each source independently.
        """

        metadata = (
            job.metadata
            if isinstance(
                job.metadata,
                dict,
            )
            else {}
        )

        return {
            "source": job.source,

            "source_job_id": (
                job.source_job_id
            ),

            "company": job.company,

            "title": job.title,

            "location": list(
                job.location or []
            ),

            "remote": bool(
                job.remote
            ),

            "employment_type": (
                job.employment_type
            ),

            "apply_url": (
                job.apply_url
            ),

            "source_url": (
                job.source_url
            ),

            "salary_min_lpa": (
                job.salary.min_lpa
            ),

            "salary_max_lpa": (
                job.salary.max_lpa
            ),

            "salary_currency": (
                job.salary.currency
            ),

            "salary_status": (
                metadata.get(
                    "salary_status"
                )
                or (
                    "VERIFIED"
                    if (
                        job.salary.min_lpa
                        is not None
                        or job.salary.max_lpa
                        is not None
                    )
                    else "UNDISCLOSED"
                )
            ),

            "salary_confidence": (
                metadata.get(
                    "salary_confidence",
                    0.0,
                )
                or 0.0
            ),

            "salary_evidence": (
                metadata.get(
                    "salary_evidence"
                )
            ),

            "posted_at": (
                job.posted_at
            ),
        }

    # ==================================================
    # Group merging
    # ==================================================

    def _merge_group(
        self,
        group: List[Job],
    ) -> Job:

        if not group:
            raise ValueError(
                "Cannot merge an empty job group."
            )

        # Prefer the most complete listing as
        # the canonical primary record.
        primary = max(
            group,
            key=self._completeness_score,
        )

        source_records: List[dict] = []

        seen_sources = set()

        # --------------------------------------------------
        # Preserve every distinct source.
        # --------------------------------------------------

        for job in group:

            source_key = (
                job.source,
                job.source_job_id,
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(
                source_key
            )

            source_records.append(
                self._source_record(
                    job
                )
            )

        source_names: List[str] = []

        for record in source_records:
            source = record[
                "source"
            ]

            if source not in source_names:
                source_names.append(
                    source
                )

        # Stable ordering gives us predictable
        # API and UI output.
        source_names.sort()

        source_records.sort(
            key=lambda record: (
                str(
                    record.get(
                        "source",
                        "",
                    )
                ).lower()
            )
        )

        # --------------------------------------------------
        # Attach provenance to canonical job.
        # --------------------------------------------------

        primary.sources = (
            source_names
        )

        primary.source_records = (
            source_records
        )

        primary.metadata = {
            **primary.metadata,

            "source_count": (
                len(source_names)
            ),

            "source_names": (
                source_names
            ),

            "source_records": (
                source_records
            ),
        }

        # --------------------------------------------------
        # Prefer the strongest salary evidence across
        # duplicate sources.
        # --------------------------------------------------

        best_salary_job = (
            self._best_salary_job(
                group
            )
        )

        if best_salary_job is not None:
            primary.salary = (
                best_salary_job.salary
            )

            best_metadata = (
                best_salary_job.metadata
                if isinstance(
                    best_salary_job.metadata,
                    dict,
                )
                else {}
            )

            for key in (
                "salary_status",
                "salary_source",
                "salary_confidence",
                "salary_evidence",
            ):
                if key in best_metadata:
                    primary.metadata[
                        key
                    ] = best_metadata[key]

        # --------------------------------------------------
        # If primary lacks URLs, inherit the first
        # useful source URL.
        # --------------------------------------------------

        if not primary.apply_url:

            for record in source_records:
                if record.get(
                    "apply_url"
                ):
                    primary.apply_url = (
                        record[
                            "apply_url"
                        ]
                    )
                    break

        if not primary.source_url:

            for record in source_records:
                if record.get(
                    "source_url"
                ):
                    primary.source_url = (
                        record[
                            "source_url"
                        ]
                    )
                    break

        return primary

    # ==================================================
    # Quality helpers
    # ==================================================

    @staticmethod
    def _completeness_score(
        job: Job,
    ) -> int:

        score = 0

        if job.company:
            score += 2

        if job.title:
            score += 2

        if job.location:
            score += 2

        if job.description:
            score += 3

        if job.apply_url:
            score += 2

        if job.source_url:
            score += 1

        if job.employment_type:
            score += 1

        if job.skills:
            score += 2

        if (
            job.salary.min_lpa
            is not None
            or job.salary.max_lpa
            is not None
        ):
            score += 3

        if job.remote:
            score += 1

        return score

    @staticmethod
    def _best_salary_job(
        group: List[Job],
    ) -> Job | None:
        """
        Choose the strongest salary evidence.

        Priority:

            valid min salary + max salary
            valid min salary
            valid max salary
            no salary
        """

        def salary_score(
            job: Job,
        ) -> tuple:

            minimum = (
                job.salary.min_lpa
            )

            maximum = (
                job.salary.max_lpa
            )

            has_min = (
                minimum is not None
                and minimum > 0
            )

            has_max = (
                maximum is not None
                and maximum > 0
            )

            metadata = (
                job.metadata
                if isinstance(
                    job.metadata,
                    dict,
                )
                else {}
            )

            confidence = float(
                metadata.get(
                    "salary_confidence",
                    0.0,
                )
                or 0.0
            )

            return (
                1 if has_min else 0,
                1 if has_max else 0,
                confidence,
            )

        candidates = sorted(
            group,
            key=salary_score,
            reverse=True,
        )

        if not candidates:
            return None

        selected = candidates[0]

        minimum = (
            selected.salary.min_lpa
        )

        maximum = (
            selected.salary.max_lpa
        )

        if (
            minimum is None
            and maximum is None
        ):
            return None

        return selected