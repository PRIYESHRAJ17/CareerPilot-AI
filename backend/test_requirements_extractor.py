from backend.schemas.job import Job
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)


def main() -> None:

    job = Job(
        source="test",
        source_job_id="req-001",
        title="Software Engineer",
        company="DemoTech",
        location=["Bangalore"],
        description="""
        We are looking for a Software Engineer to join our
        backend engineering team.

        Requirements:
        - 0-2 years of software development experience.
        - Strong experience with Python and SQL.
        - Experience building REST APIs.
        - Git knowledge is required.
        - Bachelor's degree in Computer Science or related field.

        Nice to have:
        - AWS
        - Docker
        - Kubernetes

        Responsibilities:
        - Build scalable backend services.
        - Design and maintain APIs.
        - Work with engineering teams to deliver features.
        - Write tests and improve system reliability.
        """,
    )

    extractor = JobRequirementsExtractor()

    requirements = extractor.extract(job)

    print("\n=== Job Intelligence ===\n")

    print("Required skills:")
    for skill in requirements.required_skills:
        print(f"  ✓ {skill}")

    print("\nPreferred skills:")
    for skill in requirements.preferred_skills:
        print(f"  + {skill}")

    print(
        f"\nExperience minimum: "
        f"{requirements.years_experience_min}"
    )

    print(
        f"Experience maximum: "
        f"{requirements.years_experience_max}"
    )

    print("\nEducation:")
    for education in requirements.education_requirements:
        print(f"  • {education}")

    print(
        f"\nSeniority: {requirements.seniority}"
    )

    print(
        f"Domain: {requirements.domain}"
    )

    print("\nHard requirements:")
    for item in requirements.hard_requirements:
        print(f"  ! {item}")

    print("\nSoft requirements:")
    for item in requirements.soft_requirements:
        print(f"  ~ {item}")

    print("\nResponsibilities:")
    for item in requirements.responsibilities:
        print(f"  → {item}")


if __name__ == "__main__":
    main()