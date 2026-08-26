from backend.schemas.job import Job, Salary
from backend.services.salary_intelligence import (
    SalaryIntelligence,
)


def make_job(
    description: str,
) -> Job:
    return Job(
        source="test",
        source_job_id="1",
        title="Software Engineer",
        company="Test Company",
        description=description,
        salary=Salary(),
    )


def main() -> None:
    intelligence = SalaryIntelligence()

    examples = [
        "Compensation: ₹8–12 LPA",
        "Salary range: 10 to 15 LPA",
        "Package: 20 LPA",
        "Annual compensation: INR 1200000 - 1800000",
        "Competitive compensation ₹80,000 per month",
        "Salary ₹1 lakh per year",
        "Package of 6-10 lakhs per annum",
        "Salary information is not disclosed.",
    ]

    print(
        "\n=== CareerPilot Salary Intelligence ===\n"
    )

    for text in examples:
        job = make_job(text)

        enriched = intelligence.enrich(
            job
        )

        print(
            f"Input:      {text}"
        )

        print(
            f"Salary:     "
            f"{enriched.salary.min_lpa} - "
            f"{enriched.salary.max_lpa} LPA"
        )

        print(
            "Status:     "
            f"{enriched.metadata.get('salary_status')}"
        )

        print(
            "Confidence: "
            f"{enriched.metadata.get('salary_confidence')}"
        )

        print(
            "Evidence:   "
            f"{enriched.metadata.get('salary_evidence')}"
        )

        print("-" * 70)


if __name__ == "__main__":
    main()