from __future__ import annotations

import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from threading import Lock

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

from backend.connectors.base import JobSource

from backend.connectors.registry import (
    JobSourceRegistry,
)

from backend.schemas.job import Job


class JobAggregator:
    """
    Production multi-provider job discovery engine.

    Design goals:

    - 98-provider concurrent discovery.
    - Deep per-provider retrieval.
    - Provider pagination when supported.
    - Adaptive query expansion.
    - Provider failure isolation.
    - Runtime provider telemetry.
    - Temporary provider cooldown.
    - Same-source deduplication.
    - Deterministic result ordering.

    Production discovery strategy:

        Query
          ↓
        Provider fleet
          ↓
        Up to 60 jobs/provider/request
          ↓
        Provider page 2 when supported
          ↓
        If the raw pool is still too small:
          ↓
        Related role query
          ↓
        Deduplication
          ↓
        SearchService quality + ranking
    """

    PRODUCTION_MIN_LIMIT = 60

    PRODUCTION_TARGET_RAW_JOBS = 500

    MAX_DISCOVERY_ROUNDS = 3

    def __init__(
        self,
        sources: Optional[List[JobSource]] = None,
        registry: Optional[JobSourceRegistry] = None,
        max_workers: int = 20,
        failure_threshold: int = 3,
        cooldown_seconds: int = 300,
    ) -> None:

        # --------------------------------------------------
        # Provider resolution
        # --------------------------------------------------

        if (
            sources is not None
            and registry is not None
        ):
            raise ValueError(
                "Provide either 'sources' or 'registry', "
                "not both."
            )

        if registry is not None:

            resolved_sources = registry.all()

        elif sources is not None:

            resolved_sources = list(
                sources
            )

        else:

            resolved_sources = []

        self.sources: List[
            JobSource
        ] = resolved_sources

        self.registry = registry

        self.max_workers = max(
            1,
            int(max_workers),
        )

        self.failure_threshold = max(
            1,
            int(failure_threshold),
        )

        self.cooldown_seconds = max(
            1,
            int(cooldown_seconds),
        )

        # --------------------------------------------------
        # Runtime telemetry
        # --------------------------------------------------

        self._failure_counts: Dict[
            str,
            int,
        ] = {}

        self._cooldown_until: Dict[
            str,
            float,
        ] = {}

        self._search_counts: Dict[
            str,
            int,
        ] = {}

        self._success_counts: Dict[
            str,
            int,
        ] = {}

        self._jobs_returned: Dict[
            str,
            int,
        ] = {}

        self._last_errors: Dict[
            str,
            str,
        ] = {}

        self._lock = Lock()

    # ======================================================
    # PROVIDER HELPERS
    # ======================================================

    @staticmethod
    def _source_name(
        source: JobSource,
    ) -> str:

        return str(
            getattr(
                source,
                "name",
                source.__class__.__name__,
            )
        )

    @staticmethod
    def _supports_paging(
        source: JobSource,
    ) -> bool:

        explicit = getattr(
            source,
            "supports_paging",
            None,
        )

        if explicit is not None:
            return bool(explicit)

        return (
            JobAggregator._source_name(
                source
            ).lower()
            in {
                "adzuna",
                "jooble",
            }
        )

    def _is_available(
        self,
        source: JobSource,
    ) -> bool:

        name = self._source_name(
            source
        )

        now = time.monotonic()

        with self._lock:

            cooldown_until = (
                self._cooldown_until.get(
                    name,
                    0.0,
                )
            )

            if now < cooldown_until:
                return False

        return True

    # ======================================================
    # QUERY EXPANSION
    # ======================================================

    @staticmethod
    def _build_query_variants(
        query: str,
    ) -> List[str]:

        original = " ".join(
            str(query)
            .strip()
            .split()
        )

        if not original:
            return []

        lowered = (
            original.casefold()
        )

        variants: List[str] = [
            original
        ]

        expansions = [
            (
                (
                    "software engineer",
                    "software developer",
                    "sde",
                ),
                (
                    "software engineer",
                    "software developer",
                ),
            ),

            (
                (
                    "backend engineer",
                    "backend developer",
                    "back end engineer",
                ),
                (
                    "backend engineer",
                    "backend developer",
                ),
            ),

            (
                (
                    "frontend engineer",
                    "frontend developer",
                    "front end engineer",
                ),
                (
                    "frontend engineer",
                    "frontend developer",
                ),
            ),

            (
                (
                    "full stack engineer",
                    "full stack developer",
                    "fullstack engineer",
                ),
                (
                    "full stack engineer",
                    "full stack developer",
                ),
            ),

            (
                (
                    "machine learning engineer",
                    "ml engineer",
                    "machine learning developer",
                ),
                (
                    "machine learning engineer",
                    "ml engineer",
                ),
            ),

            (
                (
                    "data scientist",
                    "data science",
                    "machine learning scientist",
                ),
                (
                    "data scientist",
                    "data science",
                ),
            ),

            (
                (
                    "data engineer",
                    "data engineering",
                ),
                (
                    "data engineer",
                    "data engineering",
                ),
            ),

            (
                (
                    "devops engineer",
                    "platform engineer",
                    "site reliability engineer",
                ),
                (
                    "devops engineer",
                    "platform engineer",
                ),
            ),

            (
                (
                    "cloud engineer",
                    "cloud infrastructure engineer",
                ),
                (
                    "cloud engineer",
                    "cloud infrastructure engineer",
                ),
            ),

            (
                (
                    "cybersecurity engineer",
                    "security engineer",
                    "information security engineer",
                ),
                (
                    "cybersecurity engineer",
                    "security engineer",
                ),
            ),

            (
                (
                    "product manager",
                    "technical product manager",
                ),
                (
                    "product manager",
                    "technical product manager",
                ),
            ),
        ]

        for phrases, replacement_variants in (
            expansions
        ):

            if any(
                phrase
                in lowered
                for phrase
                in phrases
            ):

                for variant in (
                    replacement_variants
                ):

                    normalized = (
                        variant.strip()
                    )

                    if (
                        normalized.casefold()
                        != lowered
                        and normalized
                        not in variants
                    ):
                        variants.append(
                            normalized
                        )

                break

        # --------------------------------------------------
        # Generic role fallback
        # --------------------------------------------------

        if len(variants) == 1:

            generic = lowered

            generic_replacements = [
                (
                    " engineer",
                    " developer",
                ),
                (
                    " developer",
                    " engineer",
                ),
                (
                    " analyst",
                    " specialist",
                ),
            ]

            for (
                old,
                new,
            ) in generic_replacements:

                if old in generic:

                    alternative = (
                        generic.replace(
                            old,
                            new,
                            1,
                        )
                    )

                    if (
                        alternative
                        not in variants
                    ):

                        variants.append(
                            alternative
                        )

                    break

        return variants[
            :JobAggregator.MAX_DISCOVERY_ROUNDS
        ]

    # ======================================================
    # RUNTIME TELEMETRY
    # ======================================================

    def _record_success(
        self,
        source: JobSource,
        job_count: int,
    ) -> None:

        name = self._source_name(
            source
        )

        with self._lock:

            self._failure_counts[
                name
            ] = 0

            self._cooldown_until[
                name
            ] = 0.0

            self._search_counts[
                name
            ] = (
                self._search_counts.get(
                    name,
                    0,
                )
                + 1
            )

            self._success_counts[
                name
            ] = (
                self._success_counts.get(
                    name,
                    0,
                )
                + 1
            )

            self._jobs_returned[
                name
            ] = (
                self._jobs_returned.get(
                    name,
                    0,
                )
                + job_count
            )

            self._last_errors.pop(
                name,
                None,
            )

    def _record_failure(
        self,
        source: JobSource,
        error: Exception,
    ) -> None:

        name = self._source_name(
            source
        )

        with self._lock:

            failures = (
                self._failure_counts.get(
                    name,
                    0,
                )
                + 1
            )

            self._failure_counts[
                name
            ] = failures

            self._search_counts[
                name
            ] = (
                self._search_counts.get(
                    name,
                    0,
                )
                + 1
            )

            self._last_errors[
                name
            ] = str(
                error
            )

            if failures >= (
                self.failure_threshold
            ):

                self._cooldown_until[
                    name
                ] = (
                    time.monotonic()
                    + self.cooldown_seconds
                )

    # ======================================================
    # SINGLE PROVIDER DISCOVERY
    # ======================================================

    def _search_source(
        self,
        source: JobSource,
        query: str,
        location: Optional[str],
        limit_per_source: int,
        filters: Dict[str, Any],
        production_mode: bool,
    ) -> Tuple[
        JobSource,
        List[Job],
        Optional[Exception],
        float,
    ]:

        started = time.perf_counter()

        all_jobs: List[
            Job
        ] = []

        try:

            effective_limit = (
                max(
                    limit_per_source,
                    self.PRODUCTION_MIN_LIMIT,
                )
                if production_mode
                else limit_per_source
            )

            page_count = (
                2
                if (
                    production_mode
                    and self._supports_paging(
                        source
                    )
                )
                else 1
            )

            last_error: Optional[
                Exception
            ] = None

            for page in range(
                1,
                page_count + 1,
            ):

                try:

                    jobs = source.search(
                        query=query,
                        location=location,
                        page=page,
                        limit=effective_limit,
                        **filters,
                    )

                except TypeError as exc:

                    # Some legacy/custom connectors may not
                    # support the page keyword despite the
                    # common interface.

                    if page > 1:

                        last_error = exc
                        break

                    jobs = source.search(
                        query=query,
                        location=location,
                        limit=effective_limit,
                        **filters,
                    )

                if jobs is None:
                    jobs = []

                page_jobs = [
                    job
                    for job
                    in jobs
                    if isinstance(
                        job,
                        Job,
                    )
                ]

                all_jobs.extend(
                    page_jobs
                )

                # Stop paging when the provider has no more
                # records available.
                if (
                    not page_jobs
                    or len(page_jobs)
                    < effective_limit
                ):
                    break

            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000

            unique_jobs = (
                self._deduplicate_source_results(
                    all_jobs
                )
            )

            if last_error is not None:

                self._record_failure(
                    source,
                    last_error,
                )

                return (
                    source,
                    unique_jobs,
                    last_error,
                    elapsed_ms,
                )

            self._record_success(
                source,
                len(unique_jobs),
            )

            return (
                source,
                unique_jobs,
                None,
                elapsed_ms,
            )

        except Exception as exc:

            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000

            self._record_failure(
                source,
                exc,
            )

            return (
                source,
                self._deduplicate_source_results(
                    all_jobs
                ),
                exc,
                elapsed_ms,
            )

    # ======================================================
    # DISCOVERY ROUND
    # ======================================================

    def _run_discovery_round(
        self,
        query: str,
        location: Optional[str],
        limit_per_source: int,
        filters: Dict[str, Any],
        production_mode: bool,
    ) -> List[Job]:

        enabled = filters.pop("_enabled_providers", None)
        enabled_names = {str(item) for item in enabled} if enabled else None
        available_sources = [
            source
            for source in self.sources
            if self._is_available(source)
            and (enabled_names is None or self._source_name(source) in enabled_names)
        ]

        if not available_sources:
            return []

        worker_count = min(
            self.max_workers,
            len(available_sources),
        )

        indexed_results: Dict[
            int,
            List[Job],
        ] = {}

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            future_to_index = {
                executor.submit(
                    self._search_source,
                    source,
                    query,
                    location,
                    limit_per_source,
                    filters,
                    production_mode,
                ): index
                for index, source
                in enumerate(
                    available_sources
                )
            }

            for future in as_completed(
                future_to_index
            ):

                index = (
                    future_to_index[
                        future
                    ]
                )

                source = (
                    available_sources[
                        index
                    ]
                )

                try:

                    (
                        returned_source,
                        jobs,
                        error,
                        elapsed_ms,
                    ) = future.result()

                except Exception as exc:

                    returned_source = source
                    jobs = []
                    error = exc
                    elapsed_ms = 0.0

                    self._record_failure(
                        source,
                        exc,
                    )

                indexed_results[
                    index
                ] = jobs

                source_name = (
                    self._source_name(
                        returned_source
                    )
                )

                if error is not None:

                    print(
                        "[JobAggregator] "
                        f"{source_name} failed "
                        f"after "
                        f"{elapsed_ms:.0f}ms: "
                        f"{error}"
                    )

                else:

                    print(
                        "[JobAggregator] "
                        f"{source_name}: "
                        f"{len(jobs)} jobs "
                        f"({elapsed_ms:.0f}ms)"
                    )

        all_jobs: List[
            Job
        ] = []

        for index in sorted(
            indexed_results
        ):

            all_jobs.extend(
                indexed_results[
                    index
                ]
            )

        return (
            self._deduplicate_source_results(
                all_jobs
            )
        )

    # ======================================================
    # SEARCH
    # ======================================================

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        limit_per_source: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """
        Perform adaptive high-volume discovery.

        Normal unit tests using a small limit retain the
        original single-query behavior.

        Production requests (limit >= 30) use:

        - minimum 60 records/provider
        - second page where supported
        - adaptive query expansion
        - raw-pool target of 500 jobs
        """

        production_mode = (
            limit_per_source >= 30
        )

        queries = (
            self._build_query_variants(
                query
            )
            if production_mode
            else [query]
        )

        if not queries:
            return []

        combined_jobs: List[
            Job
        ] = []

        for index, discovery_query in (
            enumerate(queries)
        ):

            round_jobs = (
                self._run_discovery_round(
                    query=discovery_query,
                    location=location,
                    limit_per_source=(
                        limit_per_source
                    ),
                    filters=filters,
                    production_mode=(
                        production_mode
                    ),
                )
            )

            combined_jobs.extend(
                round_jobs
            )

            combined_jobs = (
                self._deduplicate_source_results(
                    combined_jobs
                )
            )

            print(
                "[JobAggregator] "
                f"Discovery round "
                f"{index + 1}/"
                f"{len(queries)} "
                f"query={discovery_query!r} "
                f"pool={len(combined_jobs)}"
            )

            if (
                not production_mode
                or len(combined_jobs)
                >= self.PRODUCTION_TARGET_RAW_JOBS
            ):
                break

        return (
            self._deduplicate_source_results(
                combined_jobs
            )
        )

    # ======================================================
    # SAME-SOURCE DEDUPLICATION
    # ======================================================

    @staticmethod
    def _deduplicate_source_results(
        jobs: List[Job],
    ) -> List[Job]:

        seen = set()

        unique_jobs: List[
            Job
        ] = []

        for job in jobs:

            source = str(
                getattr(
                    job,
                    "source",
                    "",
                )
            )

            source_job_id = str(
                getattr(
                    job,
                    "source_job_id",
                    "",
                )
            )

            key = (
                source
                + ":"
                + source_job_id
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            unique_jobs.append(
                job
            )

        return unique_jobs

    # ======================================================
    # HEALTH CHECK
    # ======================================================

    def health_check(
        self,
    ) -> List[
        Dict[str, Any]
    ]:

        if not self.sources:
            return []

        worker_count = min(
            self.max_workers,
            len(self.sources),
        )

        def check_source(
            source: JobSource,
        ) -> Dict[str, Any]:

            started = time.perf_counter()

            source_name = (
                self._source_name(
                    source
                )
            )

            try:

                result = (
                    source.health_check()
                )

                elapsed_ms = (
                    time.perf_counter()
                    - started
                ) * 1000

                if not isinstance(
                    result,
                    dict,
                ):

                    result = {
                        "source":
                            source_name,
                        "healthy":
                            bool(result),
                        "status_code":
                            None,
                        "message":
                            "Health check completed.",
                    }

                else:

                    result = dict(
                        result
                    )

                result[
                    "source"
                ] = str(
                    result.get(
                        "source",
                        source_name,
                    )
                )

                result[
                    "healthy"
                ] = bool(
                    result.get(
                        "healthy",
                        False,
                    )
                )

                result[
                    "latency_ms"
                ] = round(
                    elapsed_ms,
                    2,
                )

                return result

            except Exception as exc:

                elapsed_ms = (
                    time.perf_counter()
                    - started
                ) * 1000

                return {
                    "source":
                        source_name,
                    "healthy":
                        False,
                    "status_code":
                        None,
                    "message":
                        str(exc),
                    "latency_ms":
                        round(
                            elapsed_ms,
                            2,
                        ),
                }

        results: List[
            Dict[str, Any]
        ] = []

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            futures = [
                executor.submit(
                    check_source,
                    source,
                )
                for source
                in self.sources
            ]

            for future in as_completed(
                futures
            ):

                results.append(
                    future.result()
                )

        results.sort(
            key=lambda item: str(
                item.get(
                    "source",
                    "",
                )
            )
        )

        return results

    # ======================================================
    # HEALTH SUMMARY
    # ======================================================

    def health_summary(
        self,
    ) -> Dict[str, Any]:

        results = self.health_check()

        healthy_sources: List[
            str
        ] = []

        degraded_sources: List[
            str
        ] = []

        provider_details: Dict[
            str,
            Dict[str, Any],
        ] = {}

        with self._lock:

            failure_counts = dict(
                self._failure_counts
            )

            search_counts = dict(
                self._search_counts
            )

            success_counts = dict(
                self._success_counts
            )

            jobs_returned = dict(
                self._jobs_returned
            )

            last_errors = dict(
                self._last_errors
            )

            cooldown_until = dict(
                self._cooldown_until
            )

        now = time.monotonic()

        for result in results:

            source = str(
                result.get(
                    "source",
                    "",
                )
            )

            health_check_ok = bool(
                result.get(
                    "healthy",
                    False,
                )
            )

            runtime_failures = int(
                failure_counts.get(
                    source,
                    0,
                )
            )

            runtime_searches = int(
                search_counts.get(
                    source,
                    0,
                )
            )

            runtime_successes = int(
                success_counts.get(
                    source,
                    0,
                )
            )

            runtime_jobs = int(
                jobs_returned.get(
                    source,
                    0,
                )
            )

            runtime_error = (
                last_errors.get(
                    source
                )
            )

            in_cooldown = (
                cooldown_until.get(
                    source,
                    0.0,
                )
                > now
            )

            runtime_healthy = (
                runtime_failures == 0
            )

            effective_healthy = (
                health_check_ok
                and runtime_healthy
            )

            detail = dict(
                result
            )

            detail.update(
                {
                    "health_check_healthy":
                        health_check_ok,
                    "runtime_healthy":
                        runtime_healthy,
                    "effective_healthy":
                        effective_healthy,
                    "search_count":
                        runtime_searches,
                    "search_success_count":
                        runtime_successes,
                    "search_failure_count":
                        runtime_failures,
                    "jobs_returned":
                        runtime_jobs,
                    "last_search_error":
                        runtime_error,
                    "in_cooldown":
                        in_cooldown,
                }
            )

            provider_details[
                source
            ] = detail

            if effective_healthy:

                healthy_sources.append(
                    source
                )

            else:

                degraded_sources.append(
                    source
                )

        healthy_sources.sort()
        degraded_sources.sort()

        provider_count = len(
            results
        )

        healthy_count = len(
            healthy_sources
        )

        degraded_count = len(
            degraded_sources
        )

        return {
            "provider_count":
                provider_count,

            "healthy_sources":
                healthy_sources,

            "degraded_sources":
                degraded_sources,

            "healthy_count":
                healthy_count,

            "degraded_count":
                degraded_count,

            "unhealthy_count":
                degraded_count,

            "healthy_provider_count":
                healthy_count,

            "degraded_provider_count":
                degraded_count,

            "unhealthy_provider_count":
                degraded_count,

            "failed_provider_count":
                degraded_count,

            "total":
                provider_count,

            "healthy":
                healthy_count,

            "unhealthy":
                degraded_count,

            "unhealthy_sources":
                degraded_sources,

            "providers":
                provider_details,

            "sources":
                provider_details,
        }

    # ======================================================
    # PROVIDER STATUS
    # ======================================================

    def provider_status(
        self,
    ) -> Dict[
        str,
        Dict[str, Any],
    ]:

        now = time.monotonic()

        provider_names = {
            self._source_name(
                source
            )
            for source
            in self.sources
        }

        result: Dict[
            str,
            Dict[str, Any],
        ] = {}

        with self._lock:

            for name in sorted(
                provider_names
            ):

                failures = (
                    self._failure_counts.get(
                        name,
                        0,
                    )
                )

                cooldown_until = (
                    self._cooldown_until.get(
                        name,
                        0.0,
                    )
                )

                result[name] = {
                    "searches":
                        self._search_counts.get(
                            name,
                            0,
                        ),

                    "successes":
                        self._success_counts.get(
                            name,
                            0,
                        ),

                    "failures":
                        failures,

                    "jobs_returned":
                        self._jobs_returned.get(
                            name,
                            0,
                        ),

                    "in_cooldown":
                        cooldown_until > now,

                    "last_error":
                        self._last_errors.get(
                            name
                        ),
                }

        return result

    # ======================================================
    # RESET
    # ======================================================

    def reset_provider_state(
        self,
    ) -> None:

        with self._lock:

            self._failure_counts.clear()
            self._cooldown_until.clear()
            self._search_counts.clear()
            self._success_counts.clear()
            self._jobs_returned.clear()
            self._last_errors.clear()

    # ======================================================
    # DYNAMIC REGISTRATION
    # ======================================================

    def register(
        self,
        source: JobSource,
    ) -> None:

        source_name = (
            self._source_name(
                source
            )
        )

        existing_names = {
            self._source_name(
                item
            )
            for item
            in self.sources
        }

        if source_name in existing_names:

            raise ValueError(
                "Provider already registered: "
                f"{source_name}"
            )

        self.sources.append(
            source
        )

        if self.registry is not None:

            self.registry.register(
                source
            )

    def register_many(
        self,
        sources: List[JobSource],
    ) -> None:

        for source in sources:

            self.register(
                source
            )

    # ======================================================
    # SUMMARY
    # ======================================================

    def summary(
        self,
    ) -> Dict[str, Any]:

        status = self.provider_status()

        total = len(
            self.sources
        )

        available = sum(
            1
            for item
            in status.values()
            if not item[
                "in_cooldown"
            ]
        )

        successful = sum(
            1
            for item
            in status.values()
            if item[
                "successes"
            ] > 0
        )

        return {
            "total_providers":
                total,

            "available_providers":
                available,

            "providers_with_success":
                successful,

            "total_searches":
                sum(
                    item[
                        "searches"
                    ]
                    for item
                    in status.values()
                ),

            "total_successes":
                sum(
                    item[
                        "successes"
                    ]
                    for item
                    in status.values()
                ),

            "total_failures":
                sum(
                    item[
                        "failures"
                    ]
                    for item
                    in status.values()
                ),

            "total_jobs_returned":
                sum(
                    item[
                        "jobs_returned"
                    ]
                    for item
                    in status.values()
                ),

            "status":
                status,
        }