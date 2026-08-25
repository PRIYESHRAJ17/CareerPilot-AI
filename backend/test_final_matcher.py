from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.schemas.job import Job

from backend.schemas.requirements import (
    JobRequirements,
)

from backend.services.final_matcher import (
    FinalMatchEngine,
)


def main() -> None:

    candidate = CandidateProfile(
        candidate_id="final-demo",

        headline="Backend Software Engineer",

        skills=[
            "Python",
            "SQL",
            "REST APIs",
            "Git",
        ],

        technical_skills=[
            "Python",
            "PostgreSQL",
            "Docker",
        ],

        projects=[
            "Built a REST API backend",
            "Developed a scalable database application",
        ],

        career_goal=CareerGoal(
            target_roles=[
                "Software Engineer",
                "Backend Engineer",
            ],
            target_industries=[
                "technology",
            ],
            minimum_salary_lpa=6,
        ),

        preferred_locations=[
            "Bangalore",
        ],

        years_of_experience=0,
    )

    job = Job(
        source="test",
        source_job_id="final-001",
        title="Software Development Engineer",
        company="CareerPilot Demo",
        location=[
            "Bangalore",
        ],
        remote=True,

        description=(
            "Build backend services and APIs using Python. "
            "Work with relational databases and containerized "
            "applications. Collaborate with engineering teams."
        ),

        skills=[
            "Python",
            "REST APIs",
            "Docker",
            "PostgreSQL",
        ],
    )

    requirements = JobRequirements(
        required_skills=[
            "python",
            "rest apis",
        ],

        preferred_skills=[
            "docker",
            "postgresql",
        ],

        technologies=[
            "python",
            "rest apis",
            "docker",
            "postgresql",
        ],

        responsibilities=[
            "build backend services",
            "develop APIs",
            "work with relational databases",
            "collaborate with engineering teams",
        ],
    )

    engine = FinalMatchEngine()

    result = engine.evaluate(
        candidate=candidate,
        job=job,
        requirements=requirements,
    )

    print("\n=== CareerPilot Final Match ===\n")

    print(
        f"Deterministic Score: {result.deterministic_score}"
    )

    print(
        f"Semantic Score:      {result.semantic_score}"
    )

    print(
        f"Final Score:         {result.final_score}"
    )

    print(
        f"Decision:            {result.decision}"
    )

    print(
        f"Confidence:          {result.confidence}"
    )

    print("\nStrengths:")

    for strength in result.strengths:
        print(f"  ✓ {strength}")

    print("\nSkill Gaps:")

    for gap in result.skill_gaps:
        print(f"  △ {gap}")

    print(
        f"\nExplanation:\n{result.explanation}"
    )


if __name__ == "__main__":
    main()