from backend.schemas.candidate import CandidateProfile, CareerGoal
from backend.schemas.job import Job, Salary
from backend.services.job_filter import JobFilter


def main() -> None:
    candidate = CandidateProfile(
        candidate_id="demo-user",
        skills=["Python", "SQL", "DSA"],
        preferred_locations=["Bangalore"],
        preferred_work_modes=["remote", "hybrid"],
        career_goal=CareerGoal(
            target_roles=["Software Engineer"],
            minimum_salary_lpa=6,
        ),
    )

    jobs = [
        Job(
            source="test",
            source_job_id="1",
            title="Software Engineer",
            company="Company A",
            location=["Bangalore"],
            remote=True,
            salary=Salary(
                min_lpa=7,
                max_lpa=10,
                currency="INR",
            ),
        ),
        Job(
            source="test",
            source_job_id="2",
            title="Software Engineer",
            company="Company B",
            location=["Delhi"],
            remote=False,
            salary=Salary(
                min_lpa=8,
                max_lpa=12,
                currency="INR",
            ),
        ),
        Job(
            source="test",
            source_job_id="3",
            title="Software Engineer",
            company="Company C",
            location=["Bangalore"],
            remote=False,
            salary=Salary(
                min_lpa=5,
                max_lpa=6,
                currency="INR",
            ),
        ),
    ]

    job_filter = JobFilter()
    filtered = job_filter.filter(
        jobs=jobs,
        candidate=candidate,
    )

    print(f"\nInput jobs:    {len(jobs)}")
    print(f"Filtered jobs: {len(filtered)}\n")

    for job in filtered:
        print(
            f"{job.company} — "
            f"{job.title} — "
            f"{', '.join(job.location)}"
        )


if __name__ == "__main__":
    main()