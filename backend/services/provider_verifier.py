"""
CareerPilot AI - Provider Verification Engine.

A provider is LIVE only after real-world verification succeeds:

    configuration
        -> health
        -> real search
        -> canonical jobs
        -> provenance
        -> usable URL
        -> freshness

Provider.search() normally returns canonical CareerPilot Job objects.
The verifier therefore reuses canonical Job objects and only calls
normalize() for raw provider payloads.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from backend.schemas.job import Job
from backend.schemas.provider_fleet import ProviderDefinition
from backend.services.provider_fleet import ProviderFleet


class ProviderVerificationState(str, Enum):
    LIVE = "LIVE"
    CONFIGURED = "CONFIGURED"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"


@dataclass(slots=True)
class ProviderVerificationResult:
    name: str
    display_name: str
    adapter_type: str
    state: ProviderVerificationState

    configuration_ok: bool = False
    health_ok: bool = False
    search_ok: bool = False

    jobs_returned: int = 0
    jobs_normalized: int = 0
    jobs_with_provenance: int = 0
    jobs_with_url: int = 0
    fresh_jobs: int = 0

    latency_ms: float = 0.0

    message: str = ""
    error_type: str | None = None
    error: str | None = None

    checked_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    evidence: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def is_live(self) -> bool:
        return (
            self.state
            is ProviderVerificationState.LIVE
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(slots=True)
class ProviderVerificationSummary:
    total: int
    live: int
    configured: int
    degraded: int
    offline: int
    unverified: int
    rejected: int

    jobs_returned: int
    jobs_normalized: int
    jobs_with_provenance: int
    jobs_with_url: int
    fresh_jobs: int

    results: list[ProviderVerificationResult] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "live": self.live,
            "configured": self.configured,
            "degraded": self.degraded,
            "offline": self.offline,
            "unverified": self.unverified,
            "rejected": self.rejected,
            "jobs_returned": self.jobs_returned,
            "jobs_normalized": self.jobs_normalized,
            "jobs_with_provenance": self.jobs_with_provenance,
            "jobs_with_url": self.jobs_with_url,
            "fresh_jobs": self.fresh_jobs,
            "live_percentage": round(
                self.live / self.total * 100.0,
                2,
            )
            if self.total
            else 0.0,
            "results": [
                result.to_dict()
                for result in self.results
            ],
        }


class ProviderFleetVerifier:
    """Verify one provider or an entire provider fleet."""

    def __init__(
        self,
        fleet: ProviderFleet,
        *,
        query: str = "software engineer",
        location: str = "remote",
        limit: int = 5,
        freshness_days: int = 180,
        concurrency: int = 8,
    ) -> None:
        self.fleet = fleet
        self.query = str(
            query or ""
        ).strip()
        self.location = str(
            location or ""
        ).strip()
        self.limit = max(
            1,
            min(
                int(limit),
                50,
            ),
        )
        self.freshness_days = max(
            1,
            int(freshness_days),
        )
        self.concurrency = max(
            1,
            min(
                int(concurrency),
                32,
            ),
        )

    # ================================================================
    # PUBLIC API
    # ================================================================

    async def verify_all_async(
        self,
        definitions: Sequence[ProviderDefinition] | None = None,
    ) -> ProviderVerificationSummary:
        items = list(
            definitions
            if definitions is not None
            else self.fleet.list_definitions()
        )

        semaphore = asyncio.Semaphore(
            self.concurrency
        )

        async def run(
            definition: ProviderDefinition,
        ) -> ProviderVerificationResult:
            async with semaphore:
                return await self.verify_async(
                    definition
                )

        results = await asyncio.gather(
            *(
                run(item)
                for item in items
            )
        )

        return self._build_summary(
            results
        )

    def verify_all(
        self,
        definitions: Sequence[ProviderDefinition] | None = None,
    ) -> ProviderVerificationSummary:
        return asyncio.run(
            self.verify_all_async(
                definitions
            )
        )

    async def verify_async(
        self,
        definition: ProviderDefinition,
    ) -> ProviderVerificationResult:
        started = time.perf_counter()

        result = ProviderVerificationResult(
            name=str(
                getattr(
                    definition,
                    "name",
                    "",
                )
                or ""
            ),
            display_name=str(
                getattr(
                    definition,
                    "display_name",
                    "",
                )
                or getattr(
                    definition,
                    "name",
                    "",
                )
                or "Unknown Provider"
            ),
            adapter_type=str(
                getattr(
                    definition,
                    "adapter_type",
                    "unknown",
                )
                or "unknown"
            ),
            state=ProviderVerificationState.UNVERIFIED,
        )

        # ------------------------------------------------------------
        # 1. Definition validation
        # ------------------------------------------------------------
        try:
            self._validate_definition_identity(
                definition
            )
        except Exception as exc:
            self._fail(
                result,
                ProviderVerificationState.REJECTED,
                "Provider definition is invalid.",
                exc,
                started,
            )
            return result

        # ------------------------------------------------------------
        # 2. Adapter construction
        # ------------------------------------------------------------
        try:
            source = self.fleet.build_source(
                definition
            )
        except Exception as exc:
            self._fail(
                result,
                ProviderVerificationState.CONFIGURED,
                (
                    "Definition exists but adapter "
                    "construction failed."
                ),
                exc,
                started,
            )
            return result

        # ------------------------------------------------------------
        # 3. Configuration
        # ------------------------------------------------------------
        try:
            result.configuration_ok = (
                await self._configuration_ok(
                    source
                )
            )
        except Exception as exc:
            self._fail(
                result,
                ProviderVerificationState.CONFIGURED,
                "Configuration validation failed.",
                exc,
                started,
            )
            return result

        if not result.configuration_ok:
            result.state = (
                ProviderVerificationState.CONFIGURED
            )
            result.message = (
                "Provider is configured but required "
                "configuration is unavailable."
            )
            result.latency_ms = (
                self._elapsed_ms(started)
            )
            return result

        # ------------------------------------------------------------
        # 4. Health
        # ------------------------------------------------------------
        try:
            (
                result.health_ok,
                health_evidence,
            ) = await self._health_check(
                source
            )

            result.evidence[
                "health"
            ] = health_evidence

        except Exception as exc:
            self._fail(
                result,
                ProviderVerificationState.OFFLINE,
                "Provider health check failed.",
                exc,
                started,
            )
            return result

        if not result.health_ok:
            result.state = (
                ProviderVerificationState.DEGRADED
            )
            result.message = (
                "Provider endpoint is reachable only "
                "partially or failed health validation."
            )
            result.latency_ms = (
                self._elapsed_ms(started)
            )
            return result

        # ------------------------------------------------------------
        # 5. Real provider search
        # ------------------------------------------------------------
        try:
            raw_result = await self._search(
                source
            )

            jobs = self._coerce_sequence(
                raw_result
            )

            result.search_ok = True
            result.jobs_returned = len(
                jobs
            )

            # --------------------------------------------------------
            # 6. Canonical-job-aware normalization
            # --------------------------------------------------------
            (
                normalized_jobs,
                normalization_errors,
                canonical_count,
                raw_count,
            ) = self._normalize_jobs(
                source,
                jobs,
            )

            result.jobs_normalized = len(
                normalized_jobs
            )

            result.evidence[
                "normalization"
            ] = {
                "returned": len(jobs),
                "canonical_jobs_reused": (
                    canonical_count
                ),
                "normalized_from_raw": (
                    raw_count
                ),
                "errors": len(
                    normalization_errors
                ),
                "error_samples": (
                    normalization_errors[:5]
                ),
            }

            provenance = sum(
                1
                for job in normalized_jobs
                if self._has_provenance(
                    job,
                    definition,
                )
            )

            urls = sum(
                1
                for job in normalized_jobs
                if self._extract_url(
                    job
                )
            )

            fresh = sum(
                1
                for job in normalized_jobs
                if self._is_fresh(
                    job
                )
            )

            result.jobs_with_provenance = provenance
            result.jobs_with_url = urls
            result.fresh_jobs = fresh

            result.evidence[
                "job_validation"
            ] = {
                "returned": (
                    result.jobs_returned
                ),
                "normalized": (
                    result.jobs_normalized
                ),
                "with_provenance": (
                    provenance
                ),
                "with_url": urls,
                "fresh": fresh,
                "freshness_days": (
                    self.freshness_days
                ),
            }

        except Exception as exc:
            self._fail(
                result,
                ProviderVerificationState.OFFLINE,
                "Real job retrieval failed.",
                exc,
                started,
            )
            return result

        # ------------------------------------------------------------
        # 7. Strict LIVE admission
        # ------------------------------------------------------------

        if result.jobs_returned <= 0:
            result.state = (
                ProviderVerificationState.DEGRADED
            )
            result.message = (
                "Search succeeded but returned no jobs."
            )

        elif result.jobs_normalized <= 0:
            result.state = (
                ProviderVerificationState.REJECTED
            )
            result.message = (
                "Provider returned data that could "
                "not be normalized."
            )

        elif result.jobs_with_provenance <= 0:
            result.state = (
                ProviderVerificationState.REJECTED
            )
            result.message = (
                "Normalized jobs have no valid "
                "provider provenance."
            )

        elif result.jobs_with_url <= 0:
            result.state = (
                ProviderVerificationState.REJECTED
            )
            result.message = (
                "Normalized jobs contain no usable "
                "job/application URLs."
            )

        elif result.fresh_jobs <= 0:
            result.state = (
                ProviderVerificationState.DEGRADED
            )
            result.message = (
                "Provider returned jobs but no recent "
                "freshness evidence was found within "
                f"{self.freshness_days} days."
            )

        else:
            result.state = (
                ProviderVerificationState.LIVE
            )
            result.message = (
                "Provider passed live verification."
            )

        result.latency_ms = (
            self._elapsed_ms(started)
        )

        return result

    def verify(
        self,
        definition: ProviderDefinition,
    ) -> ProviderVerificationResult:
        return asyncio.run(
            self.verify_async(
                definition
            )
        )

    # ================================================================
    # CONFIGURATION
    # ================================================================

    async def _configuration_ok(
        self,
        source: Any,
    ) -> bool:
        validator = getattr(
            source,
            "validate_configuration",
            None,
        )

        if validator is None:
            return True

        value = validator()

        if inspect.isawaitable(
            value
        ):
            value = await value

        return bool(value)

    # ================================================================
    # HEALTH
    # ================================================================

    async def _health_check(
        self,
        source: Any,
    ) -> tuple[
        bool,
        dict[str, Any],
    ]:
        health = getattr(
            source,
            "health_check",
            None,
        )

        if health is None:
            return (
                True,
                {
                    "available": False,
                    "assumed": True,
                },
            )

        value = health()

        if inspect.isawaitable(
            value
        ):
            value = await value

        if isinstance(
            value,
            Mapping,
        ):
            return (
                self._health_mapping_ok(
                    value
                ),
                dict(value),
            )

        if (
            isinstance(
                value,
                tuple,
            )
            and value
        ):
            return (
                bool(value[0]),
                {
                    "result": list(
                        value
                    )
                },
            )

        return (
            bool(value),
            {
                "result": value
            },
        )

    # ================================================================
    # SEARCH
    # ================================================================

    async def _search(
        self,
        source: Any,
    ) -> Any:
        search = getattr(
            source,
            "search",
            None,
        )

        if search is None:
            raise RuntimeError(
                "Provider source does not implement search()."
            )

        try:
            value = search(
                query=self.query,
                location=self.location,
                limit=self.limit,
            )
        except TypeError:
            try:
                value = search(
                    self.query,
                    self.location,
                    self.limit,
                )
            except TypeError:
                value = search(
                    self.query
                )

        if inspect.isawaitable(
            value
        ):
            return await value

        return value

    # ================================================================
    # CANONICAL JOB DETECTION
    # ================================================================

    @staticmethod
    def _is_canonical_job(
        value: Any,
    ) -> bool:
        """
        Detect CareerPilot's canonical Job model.

        This prevents an already-normalized Job from being passed through
        normalize() a second time.
        """

        if isinstance(
            value,
            Job,
        ):
            return True

        if value is None:
            return False

        mapping: Mapping[str, Any] | None = None

        if isinstance(
            value,
            Mapping,
        ):
            mapping = value

        elif hasattr(
            value,
            "model_dump",
        ):
            try:
                dumped = value.model_dump(
                    mode="json"
                )

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    mapping = dumped

            except Exception:
                mapping = None

        elif hasattr(
            value,
            "dict",
        ):
            try:
                dumped = value.dict()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    mapping = dumped

            except Exception:
                mapping = None

        if mapping is None:
            return False

        markers = (
            "source_job_id",
            "apply_url",
            "source_url",
            "metadata",
        )

        marker_count = sum(
            1
            for marker in markers
            if marker in mapping
        )

        return (
            marker_count >= 2
            and bool(
                mapping.get(
                    "title"
                )
            )
        )

    def _normalize_jobs(
        self,
        source: Any,
        jobs: Sequence[Any],
    ) -> tuple[
        list[Any],
        list[dict[str, str]],
        int,
        int,
    ]:
        normalized: list[Any] = []
        errors: list[dict[str, str]] = []

        canonical_count = 0
        raw_count = 0

        normalizer = getattr(
            source,
            "normalize",
            None,
        )

        for index, item in enumerate(
            jobs
        ):
            # Already canonical: DO NOT normalize again.
            if self._is_canonical_job(
                item
            ):
                normalized.append(
                    item
                )
                canonical_count += 1
                continue

            # No normalizer: accept the item as returned.
            if normalizer is None:
                normalized.append(
                    item
                )
                raw_count += 1
                continue

            try:
                try:
                    candidate = normalizer(
                        item
                    )
                except TypeError:
                    candidate = normalizer(
                        item,
                        source,
                    )

                if candidate is not None:
                    normalized.append(
                        candidate
                    )
                    raw_count += 1

            except Exception as exc:
                errors.append(
                    {
                        "index": str(
                            index
                        ),
                        "type": type(
                            exc
                        ).__name__,
                        "message": str(
                            exc
                        ),
                    }
                )

        return (
            normalized,
            errors,
            canonical_count,
            raw_count,
        )

    # ================================================================
    # PROVENANCE
    # ================================================================

    def _has_provenance(
        self,
        job: Any,
        definition: ProviderDefinition,
    ) -> bool:
        expected = str(
            getattr(
                definition,
                "name",
                "",
            )
            or ""
        ).strip().lower()

        if not expected:
            return False

        mapping = self._as_mapping(
            job
        )

        metadata = self._extract_metadata(
            job
        )

        provider_values = (
            metadata.get(
                "provider_name"
            ),
            metadata.get(
                "source"
            ),
            metadata.get(
                "source_name"
            ),
            metadata.get(
                "provider"
            ),
            mapping.get(
                "source"
            ),
        )

        return any(
            str(value or "")
            .strip()
            .lower()
            == expected
            for value in provider_values
        )

    # ================================================================
    # URL
    # ================================================================

    def _extract_url(
        self,
        job: Any,
    ) -> str | None:
        mapping = self._as_mapping(
            job
        )

        for key in (
            "url",
            "apply_url",
            "application_url",
            "job_url",
            "source_url",
            "link",
            "redirect_url",
        ):
            value = mapping.get(
                key
            )

            if value:
                return str(
                    value
                )

        metadata = self._extract_metadata(
            job
        )

        for key in (
            "url",
            "apply_url",
            "application_url",
            "job_url",
            "source_url",
            "link",
        ):
            value = metadata.get(
                key
            )

            if value:
                return str(
                    value
                )

        return None

    # ================================================================
    # FRESHNESS
    # ================================================================

    def _is_fresh(
        self,
        job: Any,
    ) -> bool:
        candidates = self._date_candidates(
            job
        )

        if not candidates:
            return False

        now = datetime.now(
            timezone.utc
        )

        for candidate in candidates:
            parsed = self._parse_datetime(
                candidate
            )

            if parsed is None:
                continue

            age_days = (
                (
                    now - parsed
                ).total_seconds()
                / 86400.0
            )

            if (
                age_days < 0
                or age_days <= self.freshness_days
            ):
                return True

        return False

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime | None:
        if isinstance(
            value,
            datetime,
        ):
            parsed = value

        elif isinstance(
            value,
            (int, float),
        ):
            try:
                timestamp = float(
                    value
                )

                if abs(
                    timestamp
                ) > 10_000_000_000:
                    timestamp /= 1000.0

                parsed = datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc,
                )

            except (
                OverflowError,
                OSError,
                ValueError,
            ):
                return None

        elif isinstance(
            value,
            str,
        ):
            text = value.strip()

            if not text:
                return None

            if text.endswith(
                "Z"
            ):
                text = (
                    text[:-1]
                    + "+00:00"
                )

            try:
                parsed = datetime.fromisoformat(
                    text
                )

            except ValueError:
                parsed = None

                for fmt in (
                    "%Y-%m-%d",
                    "%Y/%m/%d",
                    "%d-%m-%Y",
                    "%m/%d/%Y",
                    "%Y-%m-%d %H:%M:%S",
                ):
                    try:
                        parsed = datetime.strptime(
                            text[:19],
                            fmt,
                        )
                        break
                    except ValueError:
                        continue

                if parsed is None:
                    return None

        else:
            return None

        if parsed.tzinfo is None:
            return parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    def _date_candidates(
        self,
        job: Any,
    ) -> list[Any]:
        mapping = self._as_mapping(
            job
        )

        metadata = self._extract_metadata(
            job
        )

        keys = (
            "posted_at",
            "published_at",
            "created_at",
            "updated_at",
            "date_posted",
            "publication_date",
            "last_updated",
        )

        values: list[Any] = []

        for source in (
            mapping,
            metadata,
        ):
            for key in keys:
                value = source.get(
                    key
                )

                if value is not None:
                    values.append(
                        value
                    )

        return values

    # ================================================================
    # OBJECT HELPERS
    # ================================================================

    def _extract_metadata(
        self,
        job: Any,
    ) -> dict[str, Any]:
        mapping = self._as_mapping(
            job
        )

        metadata = mapping.get(
            "metadata"
        )

        if isinstance(
            metadata,
            Mapping,
        ):
            return dict(
                metadata
            )

        value = getattr(
            job,
            "metadata",
            None,
        )

        if isinstance(
            value,
            Mapping,
        ):
            return dict(
                value
            )

        return {}

    @staticmethod
    def _as_mapping(
        value: Any,
    ) -> dict[str, Any]:
        if isinstance(
            value,
            Mapping,
        ):
            return dict(
                value
            )

        if hasattr(
            value,
            "model_dump",
        ):
            try:
                dumped = value.model_dump(
                    mode="json"
                )

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(
                        dumped
                    )

            except Exception:
                pass

        if hasattr(
            value,
            "dict",
        ):
            try:
                dumped = value.dict()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(
                        dumped
                    )

            except Exception:
                pass

        output: dict[str, Any] = {}

        for key in (
            "source",
            "source_job_id",
            "title",
            "company",
            "company_name",
            "location",
            "url",
            "apply_url",
            "application_url",
            "job_url",
            "source_url",
            "description",
            "skills",
            "metadata",
            "posted_at",
            "published_at",
            "created_at",
            "updated_at",
        ):
            if hasattr(
                value,
                key,
            ):
                output[key] = getattr(
                    value,
                    key,
                )

        return output

    @staticmethod
    def _coerce_sequence(
        value: Any,
    ) -> list[Any]:
        if value is None:
            return []

        if isinstance(
            value,
            Mapping,
        ):
            for key in (
                "jobs",
                "results",
                "data",
                "items",
                "postings",
            ):
                candidate = value.get(
                    key
                )

                if (
                    isinstance(
                        candidate,
                        Sequence,
                    )
                    and not isinstance(
                        candidate,
                        (
                            str,
                            bytes,
                            bytearray,
                        ),
                    )
                ):
                    return list(
                        candidate
                    )

            return [value]

        if (
            isinstance(
                value,
                Sequence,
            )
            and not isinstance(
                value,
                (
                    str,
                    bytes,
                    bytearray,
                ),
            )
        ):
            return list(
                value
            )

        if (
            isinstance(
                value,
                Iterable,
            )
            and not isinstance(
                value,
                (
                    str,
                    bytes,
                    bytearray,
                ),
            )
        ):
            return list(
                value
            )

        return [value]

    # ================================================================
    # HEALTH / VALIDATION / SUMMARY
    # ================================================================

    @staticmethod
    def _health_mapping_ok(
        value: Mapping[str, Any],
    ) -> bool:
        for key in (
            "healthy",
            "ok",
            "success",
            "available",
        ):
            if key in value:
                return bool(
                    value[key]
                )

        status = str(
            value.get(
                "status",
                "",
            )
        ).lower()

        if status in {
            "healthy",
            "ok",
            "success",
            "available",
            "live",
        }:
            return True

        if status in {
            "unhealthy",
            "failed",
            "offline",
            "error",
        }:
            return False

        return True

    @staticmethod
    def _validate_definition_identity(
        definition: ProviderDefinition,
    ) -> None:
        name = str(
            getattr(
                definition,
                "name",
                "",
            )
            or ""
        ).strip()

        if not name:
            raise ValueError(
                "Provider definition requires a name."
            )

        adapter_type = str(
            getattr(
                definition,
                "adapter_type",
                "",
            )
            or ""
        ).strip()

        if not adapter_type:
            raise ValueError(
                f"Provider '{name}' "
                "is missing adapter_type."
            )

    @staticmethod
    def _elapsed_ms(
        started: float,
    ) -> float:
        return round(
            (
                time.perf_counter()
                - started
            )
            * 1000.0,
            2,
        )

    @staticmethod
    def _fail(
        result: ProviderVerificationResult,
        state: ProviderVerificationState,
        message: str,
        exc: Exception,
        started: float,
    ) -> None:
        result.state = state
        result.error_type = type(
            exc
        ).__name__
        result.error = str(
            exc
        )
        result.message = message
        result.latency_ms = (
            ProviderFleetVerifier._elapsed_ms(
                started
            )
        )

    def _build_summary(
        self,
        results: Sequence[
            ProviderVerificationResult
        ],
    ) -> ProviderVerificationSummary:
        counts = {
            state: 0
            for state
            in ProviderVerificationState
        }

        for result in results:
            counts[result.state] += 1

        return ProviderVerificationSummary(
            total=len(
                results
            ),
            live=counts[
                ProviderVerificationState.LIVE
            ],
            configured=counts[
                ProviderVerificationState.CONFIGURED
            ],
            degraded=counts[
                ProviderVerificationState.DEGRADED
            ],
            offline=counts[
                ProviderVerificationState.OFFLINE
            ],
            unverified=counts[
                ProviderVerificationState.UNVERIFIED
            ],
            rejected=counts[
                ProviderVerificationState.REJECTED
            ],
            jobs_returned=sum(
                result.jobs_returned
                for result in results
            ),
            jobs_normalized=sum(
                result.jobs_normalized
                for result in results
            ),
            jobs_with_provenance=sum(
                result.jobs_with_provenance
                for result in results
            ),
            jobs_with_url=sum(
                result.jobs_with_url
                for result in results
            ),
            fresh_jobs=sum(
                result.fresh_jobs
                for result in results
            ),
            results=list(
                results
            ),
        )


__all__ = [
    "ProviderVerificationState",
    "ProviderVerificationResult",
    "ProviderVerificationSummary",
    "ProviderFleetVerifier",
]