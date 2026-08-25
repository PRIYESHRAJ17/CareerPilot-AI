from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.schemas.job import Job

from backend.schemas.requirements import (
    JobRequirements,
)

from backend.services.semantic_matcher import (
    SemanticMatcher,
)


def main() -> None:

    candidate = CandidateProfile(
        candidate_id="semantic-demo",

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
        ),
    )

    job = Job(
        source="test",
        source_job_id="semantic-001",
        title="Software Development Engineer",
        company="SemanticTech",
        location=[
            "Bangalore",
        ],
        description=(
            "Build backend services and APIs using Python. "
            "Work with relational databases and containerized "
            "applications. Collaborate with engineering teams."
        ),
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

    matcher = SemanticMatcher()

    result = matcher.compare(
        candidate=candidate,
        job=job,
        requirements=requirements,
    )

    print("\n=== CareerPilot Semantic Match ===\n")

    print(
        f"Profile Similarity:      "
        f"{result.profile_similarity}"
    )

    print(
        f"Skill Similarity:        "
        f"{result.skill_similarity}"
    )

    print(
        f"Requirement Similarity:  "
        f"{result.requirement_similarity}"
    )

    print(
        f"Overall Semantic Score:  "
        f"{result.overall_similarity}"
    )

    print("\nMatched Concepts:")

    for concept in result.matched_concepts:
        print(f"  ✓ {concept}")

    print(
        f"\n{result.reasoning_context}"
    )


if __name__ == "__main__":
    main()