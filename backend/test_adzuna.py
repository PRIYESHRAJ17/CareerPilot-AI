from dotenv import load_dotenv

from backend.connectors.adzuna import AdzunaConnector


def main() -> None:
    load_dotenv()

    connector = AdzunaConnector(country="in")

    jobs = connector.search(
        query="software engineer",
        location="Bangalore",
        limit=5,
    )

    print(f"\nFound {len(jobs)} jobs\n")

    for index, job in enumerate(jobs, start=1):
        print("=" * 70)
        print(f"#{index}")
        print(f"Source:   {job.source}")
        print(f"Company:  {job.company}")
        print(f"Title:    {job.title}")
        print(f"Location: {', '.join(job.location)}")
        print(f"Salary:   {job.salary.min_lpa} - {job.salary.max_lpa} LPA")
        print(f"URL:      {job.apply_url}")


if __name__ == "__main__":
    main()