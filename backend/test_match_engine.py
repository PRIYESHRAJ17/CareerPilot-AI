from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)
from backend.schemas.job import (
    Experience,
    Job,
    Salary,
)
from backend.services.match_engine import MatchEngine


def main() -> None:
    candidate = CandidateProfile(
        candidate_id="demo-user",
        skills=[
            "Python",
            "SQL",
            "DSA",
            "Git",
        ],
        technical_skills=[
            "Python",
            "SQL",
            "DSA",
            "Git",
        ],
        years_of_experience=0,
        preferred_locations=[
            "Bangalore",
        ],
        preferred_work_modes=[
            "remote",
            "hybrid",
        ],
        career_goal=CareerGoal(
            target_roles=[
                "Software Engineer",
            ],
            target_industries=[
                "technology",
            ],
            minimum_salary_lpa=6,
        ),
    )

    job = Job(
        source="test",
        source_job_id="demo-001",
        title="Software Engineer",
        company="DemoTech",
        location=[
            "Bangalore",
        ],
        remote=True,
        experience=Experience(
            min_years=0,
            max_years=2,
        ),
        salary=Salary(
            min_lpa=6,
            max_lpa=9,
            currency="INR",
        ),
        skills=[
            "Python",
            "SQL",
            "DSA",
            "AWS",
            "Docker",
        ],
    )

    engine = MatchEngine()

    result = engine.score(
        candidate=candidate,
        job=job,
    )

    print("\n=== CareerPilot Match Analysis ===\n")

    print(
        f"Overall Score:       {result.overall_score}"
    )
    print(
        f"Role Fit:             {result.role_fit}"
    )
    print(
        f"Skill Fit:            {result.skill_fit}"
    )
    print(
        f"Experience Fit:       {result.experience_fit}"
    )
    print(
        f"Location Fit:         {result.location_fit}"
    )
    print(
        f"Salary Fit:           {result.salary_fit}"
    )
    print(
        f"Career Goal Fit:      {result.career_goal_fit}"
    )

    print(
        "\nMatched Skills:"
    )

    for skill in result.matched_skills:
        print(f"  ✓ {skill}")

    print(
        "\nMissing Skills:"
    )

    for skill in result.missing_skills:
        print(f"  △ {skill}")


if __name__ == "__main__":
    main()