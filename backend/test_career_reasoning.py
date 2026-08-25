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

from backend.services.career_reasoning import (
    CareerReasoningEngine,
)


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

    # Step 1:
    # Calculate objective match evidence.
    matcher = MatchEngine()

    match = matcher.score(
        candidate=candidate,
        job=job,
    )

    # Step 2:
    # Convert objective evidence into an action.
    reasoning_engine = CareerReasoningEngine()

    recommendation = reasoning_engine.analyze(
        candidate=candidate,
        job=job,
        match=match,
    )

    print("\n=== CareerPilot Recommendation ===\n")

    print(
        f"Decision:    {recommendation.decision}"
    )

    print(
        f"Confidence:  {recommendation.confidence}"
    )

    print(
        f"\nSummary:\n{recommendation.summary}"
    )

    print("\nStrengths:")

    for strength in recommendation.strengths:
        print(f"  ✓ {strength}")

    print("\nGaps:")

    for gap in recommendation.gaps:
        print(f"  △ {gap}")

    print("\nReasons:")

    for reason in recommendation.reasons:
        print(f"  • {reason}")


if __name__ == "__main__":
    main()