from backend.schemas.resume import (
    ResumeContact,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    StructuredResume,
)
from backend.services.job_resume_analyzer import (
    JobResumeAnalyzer,
)


def test_job_resume_analyzer():
    resume = StructuredResume(
        contact=ResumeContact(
            name="Priyesh Raj",
            email="priyesh@example.com",
            phone="+91 9999999999",
            location="Bangalore",
        ),
        headline="AI Backend Developer",
        summary=(
            "AI-focused backend developer building "
            "production APIs and intelligent applications."
        ),
        experience=[
            ResumeExperience(
                job_title="Backend Developer",
                company="Example Technologies",
                start_date="2023",
                end_date="2026",
                description=(
                    "Built backend APIs using Python and FastAPI. "
                    "Designed database services with PostgreSQL."
                ),
                achievements=[
                    "Built AI-powered services using Python and LLMs.",
                    "Containerized services with Docker.",
                ],
                technologies=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Docker",
                ],
            )
        ],
        education=[
            ResumeEducation(
                degree="B.Tech",
                institution="Example University",
                field_of_study="Computer Science",
                start_date="2020",
                end_date="2024",
            )
        ],
        skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
            "LLM",
        ],
        technical_skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
            "LLM",
        ],
        projects=[
            ResumeProject(
                name="CareerPilot AI",
                description=(
                    "AI-powered career platform for job matching "
                    "and resume analysis."
                ),
                technologies=[
                    "Python",
                    "FastAPI",
                    "LLM",
                    "PostgreSQL",
                ],
                achievements=[
                    "Built a complete job intelligence pipeline."
                ],
            )
        ],
    )

    job_description = """
    Senior AI Backend Engineer

    We are looking for a backend engineer with 3+ years
    of professional experience.

    Required skills:
    Python
    FastAPI
    PostgreSQL
    Docker
    LangChain

    Experience with LLM applications and REST APIs is strongly preferred.

    A bachelor's degree in computer science or engineering is preferred.
    """

    analyzer = JobResumeAnalyzer()

    result = analyzer.analyze(
        resume=resume,
        job_description=job_description,
    )

    print("\nJOB-SPECIFIC RESUME ANALYSIS")
    print("=" * 60)

    print("Target Role:", result.target_role)
    print("Overall Fit:", result.overall_fit_score)
    print("Evidence Score:", result.evidence_score)
    print(
        "Keyword Alignment:",
        result.keyword_alignment_score,
    )
    print(
        "Experience Alignment:",
        result.experience_alignment_score,
    )
    print(
        "Section Relevance:",
        result.section_relevance_score,
    )

    print("\nSUMMARY")
    print(result.summary)

    print("\nSTRONG MATCHES")
    for item in result.strong_matches:
        print(
            "-",
            item.requirement,
            "|",
            item.category,
            "|",
            item.evidence,
        )

    print("\nPARTIAL MATCHES")
    for item in result.partial_matches:
        print(
            "-",
            item.requirement,
            "|",
            item.category,
            "|",
            item.evidence,
        )

    print("\nMISSING")
    for item in result.missing_requirements:
        print(
            "-",
            item.requirement,
            "|",
            item.category,
        )

    print("\nTOP PRIORITIES")
    for item in result.top_priorities:
        print("-", item)

    print("\nRECOMMENDATIONS")
    for item in result.recommendations:
        print("-", item)

    # ------------------------------------------------------------
    # Score validation
    # ------------------------------------------------------------

    assert 0 <= result.overall_fit_score <= 100
    assert 0 <= result.evidence_score <= 100
    assert 0 <= result.keyword_alignment_score <= 100
    assert 0 <= result.experience_alignment_score <= 100
    assert 0 <= result.section_relevance_score <= 100

    # ------------------------------------------------------------
    # Match validation
    # ------------------------------------------------------------

    assert len(result.strong_matches) > 0

    # LangChain is deliberately absent from the resume.
    assert any(
        item.requirement.lower() == "langchain"
        for item in result.missing_requirements
    )

    # The highest-priority recommendations should mention
    # the missing LangChain requirement.
    assert any(
        "langchain" in item.lower()
        for item in result.top_priorities
    )

    # The analyzer should identify the target role.
    assert (
        result.target_role
        == "Senior AI Backend Engineer"
    )

    # The analyzer should produce an actual explanation.
    assert result.summary.strip()

    # There should be actionable recommendations.
    assert len(result.recommendations) > 0