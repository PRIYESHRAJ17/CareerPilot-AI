from __future__ import annotations

from backend.data.provider_catalog import build_provider_catalog
from backend.services.provider_fleet import ProviderFleet


def test_public_ats_catalog_requires_no_credentials():
    definitions = build_provider_catalog(128)

    fleet = ProviderFleet(definitions)

    for definition in definitions:
        source = fleet.build_source(definition)

        assert source.requires_credentials is False
        assert source.credential_env_vars == []
        assert source.validate_configuration() is True