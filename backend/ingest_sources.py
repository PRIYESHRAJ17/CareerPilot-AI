from backend.services.source_ingestion import (
    ingest_all_sources,
)


if __name__ == "__main__":

    manifest = ingest_all_sources(
        max_workers=8
    )

    print()
    print(
        "========================================"
    )
    print(
        "CareerPilot Week 5 Ingestion Complete"
    )
    print(
        "========================================"
    )

    print(
        "Expected sources :",
        manifest["expected_sources"],
    )

    print(
        "Successful        :",
        manifest["successful_sources"],
    )

    print(
        "Failed            :",
        manifest["failed_sources"],
    )

    print(
        "Total chunks      :",
        manifest["total_chunks"],
    )