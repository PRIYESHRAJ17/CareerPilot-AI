from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.schemas.job import Job


@dataclass(frozen=True)
class ProviderMetadata:
    """
    Static metadata describing one job provider.

    Provider identity and capabilities may be supplied either
    by a concrete connector class or by a runtime adapter
    instance created from a ProviderDefinition.
    """

    name: str

    display_name: str

    category: str = "job_board"

    countries: List[str] = field(
        default_factory=list
    )

    requires_credentials: bool = False

    credential_env_vars: List[str] = field(
        default_factory=list
    )

    supports_paging: bool = True

    supports_remote_filter: bool = False

    supports_salary_filter: bool = False

    website: Optional[str] = None

    api_url: Optional[str] = None

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert metadata into a stable serializable
        dictionary.
        """

        return {
            "name": self.name,

            "display_name": self.display_name,

            "category": self.category,

            "countries": list(
                self.countries
            ),

            "requires_credentials": bool(
                self.requires_credentials
            ),

            "credential_env_vars": list(
                self.credential_env_vars
            ),

            "supports_paging": bool(
                self.supports_paging
            ),

            "supports_remote_filter": bool(
                self.supports_remote_filter
            ),

            "supports_salary_filter": bool(
                self.supports_salary_filter
            ),

            "website": self.website,

            "api_url": self.api_url,
        }


class JobSource(ABC):
    """
    Universal CareerPilot job-source contract.

    Every provider exposes:

        metadata
        configuration validation
        search
        health_check
        normalize
        normalize_and_enrich

    The provider metadata is intentionally read from the
    runtime instance. This is essential for generic adapters,
    whose configuration is supplied through ProviderDefinition.
    """

    # =========================================================
    # DEFAULT IDENTITY
    # =========================================================

    name: str = "unknown"

    display_name: str = "Unknown Provider"

    category: str = "job_board"

    countries: List[str] = []

    # =========================================================
    # DEFAULT CAPABILITIES
    # =========================================================

    requires_credentials: bool = False

    credential_env_vars: List[str] = []

    supports_paging: bool = True

    supports_remote_filter: bool = False

    supports_salary_filter: bool = False

    # =========================================================
    # DEFAULT PUBLIC INFORMATION
    # =========================================================

    website: Optional[str] = None

    api_url: Optional[str] = None

    # =========================================================
    # METADATA
    # =========================================================

    @property
    def metadata(
        self,
    ) -> ProviderMetadata:
        """
        Build metadata from the concrete runtime instance.

        IMPORTANT:

        We intentionally read `self.<field>` instead of
        `type(self).<field>`.

        Generic fleet adapters configure their identity and
        capabilities at runtime, so class-level lookup would
        incorrectly return the base-class defaults.
        """

        return ProviderMetadata(
            name=str(
                self.name
            ),

            display_name=str(
                self.display_name
            ),

            category=str(
                self.category
            ),

            countries=list(
                self.countries
                or []
            ),

            requires_credentials=bool(
                self.requires_credentials
            ),

            credential_env_vars=list(
                self.credential_env_vars
                or []
            ),

            supports_paging=bool(
                self.supports_paging
            ),

            supports_remote_filter=bool(
                self.supports_remote_filter
            ),

            supports_salary_filter=bool(
                self.supports_salary_filter
            ),

            website=self.website,

            api_url=self.api_url,
        )

    def metadata_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return serializable provider metadata.
        """

        return self.metadata.to_dict()

    # =========================================================
    # CONFIGURATION
    # =========================================================

    def validate_configuration(
        self,
    ) -> None:
        """
        Validate provider configuration before live use.

        Credential-free providers pass automatically.
        Credentialed providers must have every declared
        environment variable present.
        """

        if not self.requires_credentials:
            return

        import os

        missing = [
            variable
            for variable in self.credential_env_vars
            if not os.getenv(variable)
        ]

        if missing:

            raise RuntimeError(
                f"Missing credentials for provider "
                f"'{self.name}': "
                f"{', '.join(missing)}"
            )

    # =========================================================
    # SEARCH
    # =========================================================

    @abstractmethod
    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """
        Search the provider and return canonical Job objects.
        """

        raise NotImplementedError

    # =========================================================
    # HEALTH
    # =========================================================

    @abstractmethod
    def health_check(
        self,
    ) -> Dict[str, Any]:
        """
        Perform a lightweight live provider health check.
        """

        raise NotImplementedError

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @abstractmethod
    def normalize(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        """
        Convert provider-specific job data into CareerPilot's
        canonical Job schema.
        """

        raise NotImplementedError

    # =========================================================
    # UNIVERSAL ENRICHMENT
    # =========================================================

    def enrich_job(
        self,
        job: Job,
    ) -> Job:
        """
        Attach universal provider provenance to a canonical job.
        """

        metadata = (
            dict(
                job.metadata
            )
            if isinstance(
                job.metadata,
                dict,
            )
            else {}
        )

        metadata.update(
            {
                "provider_name": self.name,

                "provider_display_name": (
                    self.display_name
                ),

                "provider_category": (
                    self.category
                ),

                "provider_countries": list(
                    self.countries
                    or []
                ),
            }
        )

        job.metadata = metadata

        return job

    def normalize_and_enrich(
        self,
        raw_job: Dict[str, Any],
    ) -> Job:
        """
        Universal provider processing pipeline:

            raw provider record
                    ↓
                normalize
                    ↓
                  enrich
                    ↓
              canonical Job
        """

        job = self.normalize(
            raw_job
        )

        return self.enrich_job(
            job
        )

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}"
            ")"
        )