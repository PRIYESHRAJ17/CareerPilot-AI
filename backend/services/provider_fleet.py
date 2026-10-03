from typing import Dict, Iterable, List

from backend.connectors.base import JobSource
from backend.connectors.generic_json import (
    GenericJsonJobSource,
)
from backend.connectors.generic_rss import (
    GenericRssJobSource,
)
from backend.connectors.public_ats import (
    PublicAtsJobSource,
)
from backend.connectors.registry import (
    JobSourceRegistry,
)
from backend.schemas.provider_fleet import (
    ProviderDefinition,
)


class ProviderFleet:
    """
    Central builder and manager for the CareerPilot provider
    fleet.

    Supported adapter families:

        json
        rss
        ats_public
    """

    SUPPORTED_ADAPTERS = {
        "json",
        "rss",
        "ats_public",
    }

    def __init__(
        self,
        definitions: Iterable[
            ProviderDefinition
        ],
    ) -> None:

        self.definitions: Dict[
            str,
            ProviderDefinition,
        ] = {}

        for definition in definitions:

            self.add_definition(
                definition
            )

        self.registry = (
            JobSourceRegistry()
        )

    # =========================================================
    # DEFINITIONS
    # =========================================================

    def add_definition(
        self,
        definition: ProviderDefinition,
    ) -> None:

        name = (
            definition.name
            .strip()
            .lower()
        )

        if not name:
            raise ValueError(
                "Provider definition name "
                "cannot be empty."
            )

        if name in self.definitions:

            raise ValueError(
                f"Provider definition '{name}' "
                "already exists."
            )

        if (
            definition.adapter_type
            not in self.SUPPORTED_ADAPTERS
        ):

            raise ValueError(
                f"Unsupported adapter type "
                f"'{definition.adapter_type}' "
                f"for provider '{name}'."
            )

        self.definitions[
            name
        ] = definition

    def get_definition(
        self,
        name: str,
    ) -> ProviderDefinition:

        normalized_name = (
            name.strip().lower()
        )

        if (
            normalized_name
            not in self.definitions
        ):

            raise KeyError(
                f"Provider definition "
                f"'{normalized_name}' "
                "does not exist."
            )

        return self.definitions[
            normalized_name
        ]

    def definitions_list(
        self,
    ) -> List[
        ProviderDefinition
    ]:

        return list(
            self.definitions.values()
        )

    # =========================================================
    # ADAPTER FACTORY
    # =========================================================

    def build_source(
        self,
        definition: ProviderDefinition,
    ) -> JobSource:

        if (
            definition.adapter_type
            == "json"
        ):

            return GenericJsonJobSource(
                definition
            )

        if (
            definition.adapter_type
            == "rss"
        ):

            return GenericRssJobSource(
                definition
            )

        if (
            definition.adapter_type
            == "ats_public"
        ):

            return PublicAtsJobSource(
                definition
            )

        raise ValueError(
            f"Unsupported adapter type: "
            f"{definition.adapter_type}"
        )

    # =========================================================
    # BUILD
    # =========================================================

    def build_all(
        self,
    ) -> List[JobSource]:

        sources: List[
            JobSource
        ] = []

        for definition in (
            self.definitions_list()
        ):

            if not definition.enabled:
                continue

            sources.append(
                self.build_source(
                    definition
                )
            )

        return sources

    # =========================================================
    # REGISTRATION
    # =========================================================

    def register_enabled(
        self,
    ) -> JobSourceRegistry:

        sources = (
            self.build_all()
        )

        self.registry.register_many(
            sources
        )

        return self.registry

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(
        self,
    ) -> dict:

        definitions = (
            self.definitions_list()
        )

        enabled = [
            definition
            for definition in definitions
            if definition.enabled
        ]

        return {
            "total_definitions": len(
                definitions
            ),

            "enabled_definitions": len(
                enabled
            ),

            "adapter_types": sorted(
                {
                    definition.adapter_type
                    for definition
                    in enabled
                }
            ),

            "credentialed": sum(
                1
                for definition
                in enabled
                if definition.requires_credentials
            ),

            "public": sum(
                1
                for definition
                in enabled
                if not definition.requires_credentials
            ),

            "attribution_required": sum(
                1
                for definition
                in enabled
                if definition.attribution_required
            ),

            "redistribution_restricted": sum(
                1
                for definition
                in enabled
                if definition.redistribution_restricted
            ),
        }