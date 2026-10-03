from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from time import perf_counter
from typing import Any, Dict, List, Optional

from backend.connectors.base import JobSource
from backend.connectors.registry import JobSourceRegistry


# ============================================================
# HELPERS
# ============================================================


def _utc_now() -> str:
    """
    Return the current UTC timestamp in ISO-8601 format.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# PROVIDER HEALTH STATE
# ============================================================


@dataclass
class ProviderHealthStatus:
    """
    Runtime reliability state for one provider.
    """

    source: str

    display_name: str

    healthy: bool = False

    state: str = "unknown"

    status_code: Optional[int] = None

    message: str = ""

    latency_ms: Optional[float] = None

    total_checks: int = 0

    successful_checks: int = 0

    failed_checks: int = 0

    consecutive_failures: int = 0

    total_searches: int = 0

    successful_searches: int = 0

    failed_searches: int = 0

    consecutive_search_failures: int = 0

    total_jobs_returned: int = 0

    last_checked_at: Optional[str] = None

    last_success_at: Optional[str] = None

    last_failure_at: Optional[str] = None

    last_search_at: Optional[str] = None

    last_search_success_at: Optional[str] = None

    last_search_failure_at: Optional[str] = None

    updated_at: Optional[str] = None

    recent_errors: List[str] = field(
        default_factory=list
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================
# PROVIDER HEALTH SERVICE
# ============================================================


class ProviderHealthService:
    """
    Centralized reliability and health service for all
    CareerPilot job providers.

    Responsibilities:

        - live provider health checks
        - search success/failure tracking
        - latency tracking
        - consecutive failure tracking
        - provider state classification
        - recent error retention
        - registry-wide health summaries

    State model:

        unknown
            ↓
        healthy
            ↓
        degraded
            ↓
        unhealthy

    A provider may also become healthy again automatically
    after a successful operation.
    """

    MAX_RECENT_ERRORS = 10

    DEGRADED_LATENCY_MS = 5000.0

    FAILURE_THRESHOLD = 3

    def __init__(
        self,
        registry: JobSourceRegistry,
    ) -> None:

        if not isinstance(
            registry,
            JobSourceRegistry,
        ):
            raise TypeError(
                "registry must be an instance "
                "of JobSourceRegistry."
            )

        self.registry = registry

        self._statuses: Dict[
            str,
            ProviderHealthStatus,
        ] = {}

        self._lock = Lock()

        self._initialize_registered_providers()

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def _initialize_registered_providers(
        self,
    ) -> None:
        """
        Create an initial status object for every registered
        provider.
        """

        with self._lock:

            for source in self.registry.all():

                self._ensure_status_locked(
                    source
                )

    def _ensure_status_locked(
        self,
        source: JobSource,
    ) -> ProviderHealthStatus:
        """
        Return an existing status object or create it.
        """

        if source.name not in self._statuses:

            self._statuses[
                source.name
            ] = ProviderHealthStatus(
                source=source.name,
                display_name=(
                    source.display_name
                ),
            )

        return self._statuses[
            source.name
        ]

    # ========================================================
    # PROVIDER LOOKUP
    # ========================================================

    def get(
        self,
        source_name: str,
    ) -> ProviderHealthStatus:
        """
        Return the current health state for one provider.
        """

        normalized_name = (
            str(source_name)
            .strip()
            .lower()
        )

        source = (
            self.registry.get(
                normalized_name
            )
        )

        with self._lock:

            status = (
                self._ensure_status_locked(
                    source
                )
            )

            return ProviderHealthStatus(
                **status.to_dict()
            )

    def get_optional(
        self,
        source_name: str,
    ) -> Optional[
        ProviderHealthStatus
    ]:
        """
        Safe health lookup.
        """

        normalized_name = (
            str(source_name)
            .strip()
            .lower()
        )

        if not self.registry.contains(
            normalized_name
        ):
            return None

        return self.get(
            normalized_name
        )

    # ========================================================
    # STATE CLASSIFICATION
    # ========================================================

    def _classify_state(
        self,
        *,
        healthy: bool,
        latency_ms: Optional[float],
        consecutive_failures: int,
    ) -> str:
        """
        Convert raw health metrics into a simple operational
        state.
        """

        if not healthy:

            if (
                consecutive_failures
                >= self.FAILURE_THRESHOLD
            ):
                return "unhealthy"

            return "degraded"

        if (
            latency_ms is not None
            and latency_ms
            > self.DEGRADED_LATENCY_MS
        ):
            return "degraded"

        return "healthy"

    # ========================================================
    # LIVE HEALTH CHECK
    # ========================================================

    def check(
        self,
        source_name: str,
    ) -> ProviderHealthStatus:
        """
        Execute a live provider health check.

        The provider itself owns the actual health-check
        request. This service owns measurement and state.
        """

        source = self.registry.get(
            source_name
        )

        started = perf_counter()

        status_code: Optional[int] = None
        message = ""
        healthy = False

        try:
            result = (
                source.health_check()
            )

            elapsed_ms = (
                perf_counter()
                - started
            ) * 1000.0

            if not isinstance(
                result,
                dict,
            ):
                raise RuntimeError(
                    "Provider health_check() "
                    "must return a dictionary."
                )

            healthy = bool(
                result.get(
                    "healthy",
                    False,
                )
            )

            raw_status_code = result.get(
                "status_code"
            )

            if raw_status_code is not None:

                try:
                    status_code = int(
                        raw_status_code
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    status_code = None

            message = str(
                result.get(
                    "message",
                    "",
                )
                or ""
            )

            return self._record_health_result(
                source=source,
                healthy=healthy,
                latency_ms=elapsed_ms,
                status_code=status_code,
                message=message,
            )

        except Exception as exc:

            elapsed_ms = (
                perf_counter()
                - started
            ) * 1000.0

            return self._record_health_result(
                source=source,
                healthy=False,
                latency_ms=elapsed_ms,
                status_code=status_code,
                message=str(exc),
            )

    def check_all(
        self,
    ) -> List[
        ProviderHealthStatus
    ]:
        """
        Run health checks for every registered provider.

        Providers are checked independently. One failure does
        not prevent the remaining providers from being checked.
        """

        results: List[
            ProviderHealthStatus
        ] = []

        for source in self.registry.all():

            results.append(
                self.check(
                    source.name
                )
            )

        return results

    def _record_health_result(
        self,
        *,
        source: JobSource,
        healthy: bool,
        latency_ms: float,
        status_code: Optional[int],
        message: str,
    ) -> ProviderHealthStatus:
        """
        Persist one health-check result.
        """

        now = _utc_now()

        with self._lock:

            status = (
                self._ensure_status_locked(
                    source
                )
            )

            status.healthy = healthy

            status.status_code = (
                status_code
            )

            status.message = message

            status.latency_ms = round(
                latency_ms,
                2,
            )

            status.total_checks += 1

            status.last_checked_at = now

            status.updated_at = now

            if healthy:

                status.successful_checks += 1

                status.consecutive_failures = 0

                status.last_success_at = now

            else:

                status.failed_checks += 1

                status.consecutive_failures += 1

                status.last_failure_at = now

                self._record_error(
                    status,
                    message,
                )

            status.state = (
                self._classify_state(
                    healthy=healthy,
                    latency_ms=(
                        status.latency_ms
                    ),
                    consecutive_failures=(
                        status.consecutive_failures
                    ),
                )
            )

            return ProviderHealthStatus(
                **status.to_dict()
            )

    # ========================================================
    # SEARCH TELEMETRY
    # ========================================================

    def record_search_success(
        self,
        source_name: str,
        *,
        jobs_returned: int,
        latency_ms: Optional[float] = None,
    ) -> ProviderHealthStatus:
        """
        Record a successful provider search.
        """

        source = self.registry.get(
            source_name
        )

        now = _utc_now()

        with self._lock:

            status = (
                self._ensure_status_locked(
                    source
                )
            )

            status.total_searches += 1

            status.successful_searches += 1

            status.consecutive_search_failures = 0

            status.total_jobs_returned += max(
                0,
                int(jobs_returned),
            )

            status.last_search_at = now

            status.last_search_success_at = now

            status.updated_at = now

            status.healthy = True

            status.last_success_at = now

            if latency_ms is not None:

                status.latency_ms = round(
                    float(latency_ms),
                    2,
                )

            status.state = (
                self._classify_state(
                    healthy=True,
                    latency_ms=(
                        status.latency_ms
                    ),
                    consecutive_failures=(
                        status.consecutive_failures
                    ),
                )
            )

            return ProviderHealthStatus(
                **status.to_dict()
            )

    def record_search_failure(
        self,
        source_name: str,
        *,
        error: str,
        latency_ms: Optional[float] = None,
    ) -> ProviderHealthStatus:
        """
        Record a failed provider search without raising.

        The aggregator decides whether to continue searching
        other providers.
        """

        source = self.registry.get(
            source_name
        )

        now = _utc_now()

        with self._lock:

            status = (
                self._ensure_status_locked(
                    source
                )
            )

            status.total_searches += 1

            status.failed_searches += 1

            status.consecutive_search_failures += 1

            status.last_search_at = now

            status.last_search_failure_at = now

            status.last_failure_at = now

            status.updated_at = now

            status.healthy = False

            if latency_ms is not None:

                status.latency_ms = round(
                    float(latency_ms),
                    2,
                )

            error_message = str(
                error
            )

            status.message = (
                error_message
            )

            self._record_error(
                status,
                error_message,
            )

            status.state = (
                self._classify_state(
                    healthy=False,
                    latency_ms=(
                        status.latency_ms
                    ),
                    consecutive_failures=(
                        max(
                            status.consecutive_failures,
                            status.consecutive_search_failures,
                        )
                    ),
                )
            )

            return ProviderHealthStatus(
                **status.to_dict()
            )

    # ========================================================
    # ERROR HISTORY
    # ========================================================

    def _record_error(
        self,
        status: ProviderHealthStatus,
        error: str,
    ) -> None:
        """
        Keep a bounded recent error history.
        """

        message = str(
            error
            or "Unknown provider error."
        ).strip()

        if not message:
            message = (
                "Unknown provider error."
            )

        status.recent_errors.append(
            message
        )

        if (
            len(status.recent_errors)
            > self.MAX_RECENT_ERRORS
        ):
            status.recent_errors = (
                status.recent_errors[
                    -self.MAX_RECENT_ERRORS:
                ]
            )

    # ========================================================
    # REGISTRY-WIDE STATUS
    # ========================================================

    def all(
        self,
    ) -> List[
        ProviderHealthStatus
    ]:
        """
        Return current state for every registered provider.
        """

        # Ensure newly registered providers are represented.
        self._initialize_registered_providers()

        with self._lock:

            return [
                ProviderHealthStatus(
                    **status.to_dict()
                )
                for status
                in self._statuses.values()
            ]

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return a registry-wide health summary.
        """

        statuses = self.all()

        healthy = [
            status
            for status in statuses
            if status.state == "healthy"
        ]

        degraded = [
            status
            for status in statuses
            if status.state == "degraded"
        ]

        unhealthy = [
            status
            for status in statuses
            if status.state == "unhealthy"
        ]

        unknown = [
            status
            for status in statuses
            if status.state == "unknown"
        ]

        return {
            "provider_count": len(
                statuses
            ),
            "healthy_count": len(
                healthy
            ),
            "degraded_count": len(
                degraded
            ),
            "unhealthy_count": len(
                unhealthy
            ),
            "unknown_count": len(
                unknown
            ),
            "healthy_sources": [
                status.source
                for status in healthy
            ],
            "degraded_sources": [
                status.source
                for status in degraded
            ],
            "unhealthy_sources": [
                status.source
                for status in unhealthy
            ],
            "unknown_sources": [
                status.source
                for status in unknown
            ],
        }

    # ========================================================
    # OPERATIONAL HELPERS
    # ========================================================

    def available_sources(
        self,
    ) -> List[JobSource]:
        """
        Return providers that are currently healthy or have
        not yet accumulated enough evidence to be considered
        unhealthy.

        This allows the aggregator to avoid repeatedly
        hammering providers that are clearly down.
        """

        available: List[
            JobSource
        ] = []

        for source in self.registry.all():

            status = self.get(
                source.name
            )

            if status.state != "unhealthy":
                available.append(
                    source
                )

        return available

    def unhealthy_sources(
        self,
    ) -> List[JobSource]:
        """
        Return providers currently classified as unhealthy.
        """

        unhealthy: List[
            JobSource
        ] = []

        for source in self.registry.all():

            status = self.get(
                source.name
            )

            if status.state == "unhealthy":

                unhealthy.append(
                    source
                )

        return unhealthy

    def reset(
        self,
        source_name: Optional[str] = None,
    ) -> None:
        """
        Reset health state for one provider or all providers.

        This is useful for recovery workflows and tests.
        """

        with self._lock:

            if source_name is None:

                self._statuses.clear()

                for source in (
                    self.registry.all()
                ):
                    self._ensure_status_locked(
                        source
                    )

                return

            normalized_name = (
                str(source_name)
                .strip()
                .lower()
            )

            source = (
                self.registry.get(
                    normalized_name
                )
            )

            self._statuses[
                normalized_name
            ] = ProviderHealthStatus(
                source=source.name,
                display_name=(
                    source.display_name
                ),
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        summary = self.summary()

        return (
            "ProviderHealthService("
            f"providers="
            f"{summary['provider_count']}, "
            f"healthy="
            f"{summary['healthy_count']}, "
            f"degraded="
            f"{summary['degraded_count']}, "
            f"unhealthy="
            f"{summary['unhealthy_count']}"
            ")"
        )