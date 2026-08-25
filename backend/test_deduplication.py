from dotenv import load_dotenv

from backend.connectors.adzuna import AdzunaConnector
from backend.connectors.jooble import JoobleConnector
from backend.services.job_aggregator import JobAggregator
from backend.services.deduplication import JobDeduplicator


def main() -> None:
    load_dotenv()

    aggregator = JobAggregator(
        sources=[
            AdzunaConnector(country="in"),
            JoobleConnector(),
        ]
    )

    jobs = aggregator.search(
        query="software engineer",
        location="Bangalore",
        limit_per_source=5,
    )

    print(f"\nBefore deduplication: {len(jobs)}")

    deduplicator = JobDeduplicator()
    canonical_jobs = deduplicator.deduplicate(jobs)

    print(
        f"After deduplication:  {len(canonical_jobs)}\n"
    )

    for index, job in enumerate(
        canonical_jobs,
        start=1,
    ):
        source_count = job.metadata.get(
            "source_count",
            1,
        )

        print(
            f"{index}. "
            f"{job.company} — "
            f"{job.title} "
            f"[{source_count} source(s)]"
        )


if __name__ == "__main__":
    main()