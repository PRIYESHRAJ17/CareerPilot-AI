import hashlib
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from backend.schemas.job import Job


class JobDeduplicator:
    """
    Canonical job deduplication engine.

    Goal:

        Many provider listings
                ↓
        One canonical opportunity
                ↓
        Preserve every source record

    Deduplication is deliberately conservative.

    Strong signals:
        - same canonical apply URL
        - same canonical source URL
        - same provider + source job ID

    Structured signals:
        - company
        - normalized title
        - location

    Fuzzy signals are only used when the structured signals
    are sufficiently compatible.

    A canonical opportunity preserves provenance from every
    contributing source.
    """

    TRACKING_QUERY_PARAMS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "ref",
        "referrer",
        "source",
        "src",
        "trk",
        "tracking",
    }

    COMPANY_SUFFIX_PATTERNS = (
        r"\bprivate limited\b",
        r"\bpvt limited\b",
        r"\bpvt ltd\b",
        r"\bprivate ltd\b",
        r"\blimited\b",
        r"\bltd\b",
        r"\bincorporated\b",
        r"\binc\b",
        r"\bcorporation\b",
        r"\bcorp\b",
        r"\bcompany\b",
        r"\bco\b",
        r"\bllc\b",
        r"\bl\.l\.c\b",
        r"\bplc\b",
    )

    TITLE_NOISE_PATTERNS = (
        r"\bfull[\s-]*time\b",
        r"\bpart[\s-]*time\b",
        r"\bcontract\b",
        r"\btemporary\b",
        r"\bremote\b",
        r"\bhybrid\b",
        r"\bon[\s-]*site\b",
        r"\bonsite\b",
    )

    TITLE_REPLACEMENTS = {
        "software development engineer": (
            "software engineer"
        ),
        "software dev engineer": (
            "software engineer"
        ),
        "software developer engineer": (
            "software engineer"
        ),
        "developer programmer": (
            "developer"
        ),
        "sde": "software engineer",
        "swe": "software engineer",
        "sr": "senior",
        "sr.": "senior",
        "jr": "junior",
        "jr.": "junior",
    }

    LOCATION_ALIASES = {
        "blr": "bangalore",
        "bengaluru": "bangalore",
        "bombay": "mumbai",
        "mum": "mumbai",
        "delhi ncr": "delhi",
        "new delhi": "delhi",
        "hyd": "hyderabad",
        "secunderabad": "hyderabad",
        "kolkata": "calcutta",
        "pune city": "pune",
        "remote": "remote",
        "work from home": "remote",
        "wfh": "remote",
    }

    def deduplicate(
        self,
        jobs: List[Job],
    ) -> List[Job]:
        """
        Deduplicate a collection of normalized jobs.
        """

        if not jobs:
            return []

        # -----------------------------------------------------
        # Step 1:
        # Remove exact provider-level duplicates.
        # -----------------------------------------------------

        unique_jobs = (
            self._remove_exact_source_duplicates(
                jobs
            )
        )

        # -----------------------------------------------------
        # Step 2:
        # Build canonical clusters.
        # -----------------------------------------------------

        clusters: List[
            List[Job]
        ] = []

        for job in unique_jobs:

            matched_cluster: Optional[
                List[Job]
            ] = None

            for cluster in clusters:

                if self._should_merge_with_cluster(
                    job,
                    cluster,
                ):
                    matched_cluster = cluster
                    break

            if matched_cluster is None:

                clusters.append(
                    [job]
                )

            else:

                matched_cluster.append(
                    job
                )

        # -----------------------------------------------------
        # Step 3:
        # Merge every cluster into one canonical job.
        # -----------------------------------------------------

        canonical_jobs = [
            self._merge_group(
                cluster
            )
            for cluster in clusters
        ]

        # -----------------------------------------------------
        # Step 4:
        # Stable output ordering.
        # -----------------------------------------------------

        canonical_jobs.sort(
            key=lambda job: (
                self._normalize_company(
                    job.company
                ),

                self._normalize_title(
                    job.title
                ),

                self._normalize_location(
                    job.location
                ),
            )
        )

        return canonical_jobs

    # =========================================================
    # SOURCE-LEVEL DEDUPLICATION
    # =========================================================

    def _remove_exact_source_duplicates(
        self,
        jobs: List[Job],
    ) -> List[Job]:

        seen = set()

        unique_jobs: List[
            Job
        ] = []

        for job in jobs:

            source = (
                str(
                    job.source
                    or ""
                )
                .strip()
                .lower()
            )

            source_job_id = (
                str(
                    job.source_job_id
                    or ""
                )
                .strip()
            )

            if source_job_id:

                key = (
                    "source_id",
                    source,
                    source_job_id,
                )

            else:

                key = (
                    "fallback",
                    source,
                    self._normalize_company(
                        job.company
                    ),
                    self._normalize_title(
                        job.title
                    ),
                    self._normalize_location(
                        job.location
                    ),
                    self._canonical_url(
                        job.apply_url
                    )
                    or self._canonical_url(
                        job.source_url
                    ),
                )

            if key in seen:
                continue

            seen.add(key)

            unique_jobs.append(
                job
            )

        return unique_jobs

    # =========================================================
    # CLUSTER MATCHING
    # =========================================================

    def _should_merge_with_cluster(
        self,
        job: Job,
        cluster: List[Job],
    ) -> bool:
        """
        Determine whether `job` belongs to an existing
        canonical opportunity cluster.

        Matching against any sufficiently strong member is
        enough. This supports cases where provider A and C
        agree even if provider B has slightly different data.
        """

        for existing in cluster:

            if self._is_same_source_record(
                job,
                existing,
            ):
                return True

            if self._same_canonical_url(
                job,
                existing,
            ):
                return True

            if self._structured_match(
                job,
                existing,
            ):
                return True

        return False

    @staticmethod
    def _is_same_source_record(
        left: Job,
        right: Job,
    ) -> bool:

        return (
            str(
                left.source
                or ""
            )
            .strip()
            .lower()
            == str(
                right.source
                or ""
            )
            .strip()
            .lower()
            and str(
                left.source_job_id
                or ""
            ).strip()
            != ""
            and str(
                left.source_job_id
                or ""
            ).strip()
            == str(
                right.source_job_id
                or ""
            ).strip()
        )

    def _same_canonical_url(
        self,
        left: Job,
        right: Job,
    ) -> bool:

        left_urls = {
            url
            for url in (
                self._canonical_url(
                    left.apply_url
                ),
                self._canonical_url(
                    left.source_url
                ),
            )
            if url
        }

        right_urls = {
            url
            for url in (
                self._canonical_url(
                    right.apply_url
                ),
                self._canonical_url(
                    right.source_url
                ),
            )
            if url
        }

        return bool(
            left_urls
            and right_urls
            and left_urls.intersection(
                right_urls
            )
        )

    # =========================================================
    # STRUCTURED MATCH
    # =========================================================

    def _structured_match(
        self,
        left: Job,
        right: Job,
    ) -> bool:

        left_company = (
            self._normalize_company(
                left.company
            )
        )

        right_company = (
            self._normalize_company(
                right.company
            )
        )

        if not left_company or not right_company:
            return False

        if left_company != right_company:
            return False

        left_title = (
            self._normalize_title(
                left.title
            )
        )

        right_title = (
            self._normalize_title(
                right.title
            )
        )

        if not left_title or not right_title:
            return False

        title_similarity = (
            self._title_similarity(
                left_title,
                right_title,
            )
        )

        if title_similarity < 0.82:
            return False

        left_locations = (
            self._location_tokens(
                left.location
            )
        )

        right_locations = (
            self._location_tokens(
                right.location
            )
        )

        # Both sources have location information.
        if (
            left_locations
            and right_locations
        ):

            if self._locations_compatible(
                left_locations,
                right_locations,
            ):
                return True

            return False

        # One provider omitted location.
        #
        # Because company + title already match strongly,
        # allow the merge.
        return True

    # =========================================================
    # URL CANONICALIZATION
    # =========================================================

    @classmethod
    def _canonical_url(
        cls,
        value: Optional[str],
    ) -> str:

        if not value:
            return ""

        raw = str(
            value
        ).strip()

        if not raw:
            return ""

        # Normalize protocol-less URLs.
        if "://" not in raw:
            raw = (
                "https://"
                + raw
            )

        try:

            parsed = urlsplit(
                raw
            )

        except ValueError:
            return raw.lower()

        scheme = (
            parsed.scheme
            or "https"
        ).lower()

        hostname = (
            parsed.hostname
            or ""
        ).lower()

        if not hostname:
            return raw.lower()

        # -----------------------------------------------------
        # Remove default ports.
        # -----------------------------------------------------

        netloc = hostname

        if parsed.port:

            default_port = (
                (
                    scheme == "http"
                    and parsed.port == 80
                )
                or (
                    scheme == "https"
                    and parsed.port == 443
                )
            )

            if not default_port:
                netloc = (
                    f"{hostname}:"
                    f"{parsed.port}"
                )

        # -----------------------------------------------------
        # Normalize path.
        # -----------------------------------------------------

        path = (
            parsed.path
            or "/"
        )

        path = re.sub(
            r"/+",
            "/",
            path,
        )

        if (
            path != "/"
            and path.endswith("/")
        ):
            path = path[:-1]

        # -----------------------------------------------------
        # Remove tracking parameters while keeping meaningful
        # query parameters.
        # -----------------------------------------------------

        query_pairs = []

        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):

            normalized_key = (
                key.strip().lower()
            )

            if normalized_key in (
                cls.TRACKING_QUERY_PARAMS
            ):
                continue

            query_pairs.append(
                (
                    normalized_key,
                    value.strip(),
                )
            )

        query_pairs.sort()

        query = urlencode(
            query_pairs
        )

        return urlunsplit(
            (
                scheme,
                netloc,
                path,
                query,
                "",
            )
        ).lower()

    # =========================================================
    # COMPANY NORMALIZATION
    # =========================================================

    @classmethod
    def _normalize_company(
        cls,
        value: str,
    ) -> str:

        normalized = (
            cls._normalize_text(
                value
            )
        )

        if not normalized:
            return ""

        # Remove legal/company suffixes.
        for pattern in (
            cls.COMPANY_SUFFIX_PATTERNS
        ):

            normalized = re.sub(
                pattern,
                " ",
                normalized,
            )

        # Common ampersand wording.
        normalized = (
            normalized.replace(
                " and ",
                " & ",
            )
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    # =========================================================
    # TITLE NORMALIZATION
    # =========================================================

    @classmethod
    def _normalize_title(
        cls,
        value: str,
    ) -> str:

        normalized = (
            cls._normalize_text(
                value
            )
        )

        if not normalized:
            return ""

        # -----------------------------------------------------
        # Normalize known equivalent phrases.
        # -----------------------------------------------------

        # Longest replacements first.
        replacements = sorted(
            cls.TITLE_REPLACEMENTS.items(),
            key=lambda item: len(
                item[0]
            ),
            reverse=True,
        )

        for old, new in replacements:

            normalized = re.sub(
                rf"\b{re.escape(old)}\b",
                new,
                normalized,
            )

        # -----------------------------------------------------
        # Remove marketplace noise.
        # -----------------------------------------------------

        for pattern in (
            cls.TITLE_NOISE_PATTERNS
        ):

            normalized = re.sub(
                pattern,
                " ",
                normalized,
            )

        # -----------------------------------------------------
        # Normalize punctuation and spacing.
        # -----------------------------------------------------

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    # =========================================================
    # GENERIC TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        normalized = (
            str(
                value
                or ""
            )
            .lower()
            .strip()
        )

        normalized = re.sub(
            r"[\u2010-\u2015]",
            "-",
            normalized,
        )

        normalized = re.sub(
            r"[^a-z0-9\s&+-]",
            " ",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return normalized

    # =========================================================
    # TITLE SIMILARITY
    # =========================================================

    @staticmethod
    def _title_similarity(
        left: str,
        right: str,
    ) -> float:

        if left == right:
            return 1.0

        left_tokens = set(
            left.split()
        )

        right_tokens = set(
            right.split()
        )

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = (
            left_tokens
            & right_tokens
        )

        union = (
            left_tokens
            | right_tokens
        )

        jaccard = (
            len(intersection)
            / len(union)
        )

        sequence = SequenceMatcher(
            None,
            left,
            right,
        ).ratio()

        # Stronger signal goes to token overlap because
        # provider titles frequently vary in word ordering.
        return (
            0.6 * jaccard
            + 0.4 * sequence
        )

    # =========================================================
    # LOCATION NORMALIZATION
    # =========================================================

    @classmethod
    def _normalize_location(
        cls,
        locations: List[str],
    ) -> str:

        tokens = (
            cls._location_tokens(
                locations
            )
        )

        return "|".join(
            sorted(tokens)
        )

    @classmethod
    def _location_tokens(
        cls,
        locations: List[str],
    ) -> set:

        normalized = set()

        for location in (
            locations or []
        ):

            cleaned = (
                cls._normalize_text(
                    location
                )
            )

            if not cleaned:
                continue

            # Split common composite locations.
            parts = re.split(
                r"[|,/]+",
                cleaned,
            )

            for part in parts:

                part = (
                    part
                    .strip()
                )

                if not part:
                    continue

                alias = (
                    cls.LOCATION_ALIASES.get(
                        part
                    )
                )

                normalized.add(
                    alias
                    or part
                )

        return normalized

    @staticmethod
    def _locations_compatible(
        left: set,
        right: set,
    ) -> bool:

        if not left or not right:
            return True

        # Explicit remote matches explicit remote.
        if (
            "remote" in left
            and "remote" in right
        ):
            return True

        # Direct intersection.
        if left.intersection(
            right
        ):
            return True

        # Global/India-level records can coexist with a
        # specific location when one provider is broad.
        broad_tokens = {
            "india",
            "global",
            "worldwide",
            "anywhere",
        }

        if (
            left.intersection(
                broad_tokens
            )
            or right.intersection(
                broad_tokens
            )
        ):
            return True

        return False

    # =========================================================
    # MERGING
    # =========================================================

    def _merge_group(
        self,
        group: List[Job],
    ) -> Job:

        if not group:
            raise ValueError(
                "Cannot merge an empty job group."
            )

        # -----------------------------------------------------
        # Choose strongest canonical record.
        # -----------------------------------------------------

        primary = max(
            group,
            key=self._completeness_score,
        )

        # Work on a metadata copy so we never mutate an
        # unrelated object accidentally.
        primary.metadata = dict(
            primary.metadata
            if isinstance(
                primary.metadata,
                dict,
            )
            else {}
        )

        # -----------------------------------------------------
        # Preserve every provider record.
        # -----------------------------------------------------

        source_records: List[
            dict
        ] = []

        seen_sources = set()

        for job in group:

            source_key = (
                str(
                    job.source
                    or ""
                )
                .strip()
                .lower(),

                str(
                    job.source_job_id
                    or ""
                ).strip(),
            )

            if (
                source_key
                in seen_sources
            ):
                continue

            seen_sources.add(
                source_key
            )

            source_records.append(
                self._source_record(
                    job
                )
            )

        # -----------------------------------------------------
        # Stable source ordering.
        # -----------------------------------------------------

        source_records.sort(
            key=lambda record: (
                str(
                    record.get(
                        "source",
                        "",
                    )
                ).lower(),

                str(
                    record.get(
                        "source_job_id",
                        "",
                    )
                ),
            )
        )

        source_names: List[
            str
        ] = []

        for record in source_records:

            source = str(
                record.get(
                    "source",
                    "",
                )
            )

            if source and source not in source_names:

                source_names.append(
                    source
                )

        source_names.sort(
            key=str.lower
        )

        # -----------------------------------------------------
        # Canonical provenance.
        # -----------------------------------------------------

        primary.sources = (
            source_names
        )

        primary.source_records = (
            source_records
        )

        canonical_id = (
            self._canonical_id(
                primary
            )
        )

        primary.metadata.update(
            {
                "canonical_job_id": (
                    canonical_id
                ),

                "source_count": (
                    len(source_names)
                ),

                "source_names": (
                    source_names
                ),

                "source_records": (
                    source_records
                ),

                "dedup_cluster_size": (
                    len(source_records)
                ),
            }
        )

        # -----------------------------------------------------
        # Strongest salary evidence.
        # -----------------------------------------------------

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
                    ] = (
                        best_metadata[key]
                    )

        # -----------------------------------------------------
        # Inherit the best useful URLs.
        # -----------------------------------------------------

        if not primary.apply_url:

            for record in source_records:

                if record.get(
                    "apply_url"
                ):

                    primary.apply_url = (
                        str(
                            record[
                                "apply_url"
                            ]
                        )
                    )

                    break

        if not primary.source_url:

            for record in source_records:

                if record.get(
                    "source_url"
                ):

                    primary.source_url = (
                        str(
                            record[
                                "source_url"
                            ]
                        )
                    )

                    break

        # -----------------------------------------------------
        # Prefer richer description / skills if the selected
        # primary record is weak.
        # -----------------------------------------------------

        if not primary.description:

            richest_description = max(
                group,
                key=lambda job: len(
                    str(
                        job.description
                        or ""
                    )
                ),
            )

            primary.description = (
                richest_description.description
            )

        if not primary.skills:

            richest_skills = max(
                group,
                key=lambda job: len(
                    job.skills or []
                ),
            )

            primary.skills = list(
                richest_skills.skills
                or []
            )

        return primary

    # =========================================================
    # CANONICAL ID
    # =========================================================

    def _canonical_id(
        self,
        job: Job,
    ) -> str:

        canonical_parts = (
            self._normalize_company(
                job.company
            ),

            self._normalize_title(
                job.title
            ),

            self._normalize_location(
                job.location
            ),
        )

        payload = "|".join(
            canonical_parts
        )

        return (
            "job-"
            + hashlib.sha256(
                payload.encode(
                    "utf-8"
                )
            ).hexdigest()[:20]
        )

    # =========================================================
    # SOURCE RECORD
    # =========================================================

    @staticmethod
    def _source_record(
        job: Job,
    ) -> dict:

        metadata = (
            job.metadata
            if isinstance(
                job.metadata,
                dict,
            )
            else {}
        )

        return {
            "source": (
                job.source
            ),

            "source_job_id": (
                job.source_job_id
            ),

            "company": (
                job.company
            ),

            "title": (
                job.title
            ),

            "location": list(
                job.location
                or []
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

            "provider_name": (
                metadata.get(
                    "provider_name",
                    job.source,
                )
            ),

            "provider_display_name": (
                metadata.get(
                    "provider_display_name"
                )
            ),
        }

    # =========================================================
    # COMPLETENESS
    # =========================================================

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
            score += min(
                4,
                len(
                    job.skills
                ),
            )

        if (
            job.salary.min_lpa
            is not None
            or job.salary.max_lpa
            is not None
        ):
            score += 3

        if job.remote:
            score += 1

        if job.posted_at:
            score += 1

        return score

    # =========================================================
    # BEST SALARY EVIDENCE
    # =========================================================

    @staticmethod
    def _best_salary_job(
        group: List[Job],
    ) -> Optional[Job]:
        """
        Select the strongest salary evidence.

        Priority:

            min + max salary
            min salary
            max salary
            no salary

        Within the same tier, salary confidence is preferred.
        """

        def salary_score(
            job: Job,
        ) -> Tuple[
            int,
            int,
            float,
        ]:

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

            try:

                confidence = float(
                    metadata.get(
                        "salary_confidence",
                        0.0,
                    )
                    or 0.0
                )

            except (
                TypeError,
                ValueError,
            ):

                confidence = 0.0

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

        selected = (
            candidates[0]
        )

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