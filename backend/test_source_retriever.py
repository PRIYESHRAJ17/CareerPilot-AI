from backend.services.source_retriever import (
    CareerSourceRetriever,
)


def test_week5_has_98_sources():

    registry = (
        CareerSourceRetriever()
    )

    assert registry.count() == 98


def test_week5_source_ids_are_unique():

    registry = (
        CareerSourceRetriever()
    )

    ids = [
        source["id"]
        for source in registry.sources
    ]

    assert len(ids) == 98
    assert len(ids) == len(set(ids))


def test_week5_source_urls_are_unique():

    registry = (
        CareerSourceRetriever()
    )

    urls = [
        source["url"]
        for source in registry.sources
    ]

    assert len(urls) == 98
    assert len(urls) == len(set(urls))


def test_source_search():

    registry = (
        CareerSourceRetriever()
    )

    results = registry.search(
        "software engineering interview",
        top_k=5,
    )

    assert len(results) > 0