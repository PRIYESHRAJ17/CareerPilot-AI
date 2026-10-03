from typing import Dict, List, Optional

from backend.connectors.base import (
    JobSource,
    ProviderMetadata,
)


class JobSourceRegistry:
    """
    Central provider registry for CareerPilot.

    Responsibilities:

        1. Register providers
        2. Prevent accidental duplicate registrations
        3. Retrieve providers by name
        4. List providers
        5. Expose provider metadata
        6. Filter providers by country/category
        7. Provide registry-wide counts

    The registry is intentionally independent from the
    search pipeline so 2 providers and 100+ providers use
    exactly the same architecture.
    """

    def __init__(
        self,
        allow_replace: bool = False,
    ) -> None:
        self._sources: Dict[str, JobSource] = {}
        self.allow_replace = allow_replace

    # =========================================================
    # REGISTRATION
    # =========================================================

    def register(
        self,
        source: JobSource,
        *,
        replace: Optional[bool] = None,
    ) -> JobSource:
        """
        Register one provider.

        By default, duplicate provider names are rejected.
        Replacement can be explicitly enabled either globally
        or for this individual registration.
        """

        if not isinstance(
            source,
            JobSource,
        ):
            raise TypeError(
                "source must be an instance of JobSource."
            )

        name = str(
            source.name
        ).strip().lower()

        if not name:
            raise ValueError(
                "Job source name cannot be empty."
            )

        should_replace = (
            self.allow_replace
            if replace is None
            else replace
        )

        if (
            name in self._sources
            and not should_replace
        ):
            raise ValueError(
                f"Job source '{name}' is already "
                "registered."
            )

        self._sources[name] = source

        return source

    def register_many(
        self,
        sources: List[JobSource],
        *,
        replace: Optional[bool] = None,
    ) -> List[JobSource]:
        """
        Register multiple providers in deterministic order.
        """

        registered: List[JobSource] = []

        for source in sources:
            registered.append(
                self.register(
                    source,
                    replace=replace,
                )
            )

        return registered

    # =========================================================
    # LOOKUP
    # =========================================================

    def get(
        self,
        name: str,
    ) -> JobSource:
        """
        Retrieve a provider by canonical name.
        """

        normalized_name = (
            str(name)
            .strip()
            .lower()
        )

        if normalized_name not in self._sources:
            raise KeyError(
                f"Job source '{normalized_name}' "
                "is not registered."
            )

        return self._sources[
            normalized_name
        ]

    def get_optional(
        self,
        name: str,
    ) -> Optional[JobSource]:
        """
        Safe lookup that returns None when missing.
        """

        normalized_name = (
            str(name)
            .strip()
            .lower()
        )

        return self._sources.get(
            normalized_name
        )

    # =========================================================
    # COLLECTIONS
    # =========================================================

    def all(self) -> List[JobSource]:
        """
        Return all registered providers.

        Registration order is preserved.
        """

        return list(
            self._sources.values()
        )

    def names(self) -> List[str]:
        """
        Return canonical provider names.
        """

        return list(
            self._sources.keys()
        )

    def metadata(
        self,
    ) -> List[ProviderMetadata]:
        """
        Return metadata for every registered provider.
        """

        return [
            source.metadata
            for source in self.all()
        ]

    def metadata_dicts(
        self,
    ) -> List[dict]:
        """
        Return serializable provider metadata.
        """

        return [
            source.metadata_dict()
            for source in self.all()
        ]

    # =========================================================
    # FILTERING
    # =========================================================

    def by_country(
        self,
        country: str,
    ) -> List[JobSource]:
        """
        Return providers covering a country.

        Matching is case-insensitive.
        """

        normalized_country = (
            str(country)
            .strip()
            .upper()
        )

        if not normalized_country:
            return []

        return [
            source
            for source in self.all()
            if normalized_country
            in {
                value.strip().upper()
                for value in source.countries
            }
        ]

    def by_category(
        self,
        category: str,
    ) -> List[JobSource]:
        """
        Return providers belonging to a category.
        """

        normalized_category = (
            str(category)
            .strip()
            .lower()
        )

        if not normalized_category:
            return []

        return [
            source
            for source in self.all()
            if (
                str(source.category)
                .strip()
                .lower()
                == normalized_category
            )
        ]

    # =========================================================
    # STATUS / COUNTS
    # =========================================================

    def contains(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a provider is registered.
        """

        normalized_name = (
            str(name)
            .strip()
            .lower()
        )

        return (
            normalized_name
            in self._sources
        )

    def count(self) -> int:
        """
        Return total number of registered providers.
        """

        return len(
            self._sources
        )

    def is_empty(self) -> bool:
        """
        Return True when no providers are registered.
        """

        return not self._sources

    def summary(self) -> dict:
        """
        Return a compact registry summary.

        Useful for health endpoints and observability.
        """

        providers = self.all()

        return {
            "provider_count": len(
                providers
            ),
            "provider_names": [
                source.name
                for source in providers
            ],
            "categories": sorted(
                {
                    source.category
                    for source in providers
                }
            ),
            "countries": sorted(
                {
                    country
                    for source in providers
                    for country
                    in source.countries
                }
            ),
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    def validate(self) -> List[str]:
        """
        Validate the registry configuration.

        Returns a list of validation errors.
        An empty list means the registry is valid.
        """

        errors: List[str] = []

        for source in self.all():

            name = str(
                source.name
            ).strip()

            if not name:
                errors.append(
                    "A registered provider has "
                    "an empty name."
                )

            if (
                not isinstance(
                    source.display_name,
                    str,
                )
                or not source.display_name.strip()
            ):
                errors.append(
                    f"Provider '{name}' has "
                    "an invalid display_name."
                )

            if (
                not isinstance(
                    source.category,
                    str,
                )
                or not source.category.strip()
            ):
                errors.append(
                    f"Provider '{name}' has "
                    "an invalid category."
                )

            duplicate_name = (
                [
                    other.name
                    for other in self.all()
                    if other is not source
                    and other.name == source.name
                ]
            )

            if duplicate_name:
                errors.append(
                    f"Duplicate provider name: "
                    f"'{name}'."
                )

        return errors

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __len__(self) -> int:
        return self.count()

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.contains(name)

    def __repr__(self) -> str:
        return (
            "JobSourceRegistry("
            f"count={self.count()}, "
            f"providers={self.names()!r}"
            ")"
        )