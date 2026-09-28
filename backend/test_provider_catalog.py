from __future__ import annotations

from backend.data.provider_catalog import (
    CATALOG_TARGET,
    build_provider_catalog,
    catalog_summary,
)


def _dump(definition):
    if hasattr(definition, "model_dump"):
        return definition.model_dump(
            mode="json"
        )

    if hasattr(definition, "dict"):
        return definition.dict()

    return definition.__dict__


def test_catalog_reaches_target():
    definitions = build_provider_catalog(
        CATALOG_TARGET
    )

    assert len(definitions) == CATALOG_TARGET


def test_catalog_names_are_unique():
    definitions = build_provider_catalog(
        CATALOG_TARGET
    )

    names = [
        _dump(definition)["name"]
        for definition in definitions
    ]

    assert len(names) == len(set(names))


def test_catalog_contains_multiple_ats():
    summary = catalog_summary(
        CATALOG_TARGET
    )

    counts = summary["platform_counts"]

    assert "greenhouse" in counts
    assert "lever" in counts
    assert "ashby" in counts

    assert counts["greenhouse"] > 0
    assert counts["lever"] > 0
    assert counts["ashby"] > 0


def test_catalog_definitions_use_public_ats_adapter():
    definitions = build_provider_catalog(
        CATALOG_TARGET
    )

    for definition in definitions:
        data = _dump(definition)

        assert data["adapter_type"] == "ats_public"

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