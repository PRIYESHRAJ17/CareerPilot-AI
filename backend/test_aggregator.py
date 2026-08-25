from dotenv import load_dotenv

from backend.connectors.adzuna import AdzunaConnector
from backend.services.job_aggregator import JobAggregator


def main() -> None:
    load_dotenv()

    adzuna = AdzunaConnector(country="in")

    aggregator = JobAggregator(
        sources=[adzuna]
    )

    jobs = aggregator.search(
        query="software engineer",
        location="Bangalore",
        limit_per_source=5,
    )

    print(f"\nUnified jobs: {len(jobs)}\n")

    for index, job in enumerate(jobs, start=1):
        print(
            f"{index}. "
            f"{job.company} — "
            f"{job.title} — "
            f"{', '.join(job.location)}"
        )


if __name__ == "__main__":
    main()
