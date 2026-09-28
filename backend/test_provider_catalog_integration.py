from __future__ import annotations

from typing import Any

from backend.data.provider_catalog import (
    build_provider_catalog,
)
from backend.services.provider_verifier import (
    ProviderFleetVerifier,
)


class DummyFleet:
    def build_source(self, definition):
        raise RuntimeError(
            "Not used in catalog construction test."
        )

    def list_definitions(self):
        return []


def model_to_dict(value: Any) -> dict[str, Any]:
    """
    Convert a Pydantic model to a dictionary.

    CareerPilot currently uses Pydantic v2, but this helper keeps the test
    resilient to a future schema-library change.
    """
    model_dump = getattr(
        value,
        "model_dump",
        None,
    )

    if callable(model_dump):
        result = model_dump(
            mode="json"
        )

        if isinstance(result, dict):
            return result

    legacy_dict = getattr(
        value,
        "dict",
        None,
    )

    if callable(legacy_dict):
        result = legacy_dict()

        if isinstance(result, dict):
            return result

    if hasattr(
        value,
        "__dict__",
    ):
        return dict(
            value.__dict__
        )

    raise TypeError(
        f"Cannot convert {type(value).__name__} "
        "to a dictionary."
    )


def test_catalog_definitions_are_accepted_by_verifier():
    definitions = build_provider_catalog(
        128
    )

    verifier = ProviderFleetVerifier(
        DummyFleet()
    )

    assert len(definitions) == 128

    for definition in definitions:
        verifier._validate_definition_identity(
            definition
        )


def test_catalog_endpoint_metadata_is_complete():
    definitions = build_provider_catalog(
        128
    )

    assert len(definitions) == 128

    for definition in definitions:
        data = model_to_dict(
            definition
        )

        assert data["name"]
        assert data["display_name"]
        assert data["adapter_type"] == (
            "ats_public"
        )
        assert data["endpoint"]
        assert data["website"]

        adapter_config = data.get(
            "adapter_config"
        )

        assert isinstance(
            adapter_config,
            dict,
        )

        assert adapter_config["platform"] in {
            "greenhouse",
            "lever",
            "ashby",
        }

        assert str(
            adapter_config["board"]
        ).strip()


def test_catalog_contains_no_duplicate_endpoints():
    definitions = build_provider_catalog(
        128
    )

    endpoints = [
        definition.endpoint
        for definition in definitions
    ]

    assert len(endpoints) == len(
        set(endpoints)
    )