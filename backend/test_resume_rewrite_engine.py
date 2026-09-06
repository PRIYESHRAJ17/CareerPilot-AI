from backend.schemas.resume import (
    ResumeContact,
    ResumeExperience,
    ResumeProject,
    StructuredResume,
)
from backend.services.resume_rewrite_engine import (
    ResumeRewriteEngine,
)


def test_resume_rewrite_engine():
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
                    "Worked on backend APIs using Python and FastAPI. "
                    "Designed database services with PostgreSQL."
                ),
                achievements=[
                    "Worked on AI-powered services using Python and LLMs.",
                    "Helped with Docker containerization.",
                    "Built backend APIs.",
                ],
                technologies=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Docker",
                ],
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
                    "Built an AI-powered career platform "
                    "for job matching and resume analysis."
                ),
                technologies=[
                    "Python",
                    "FastAPI",
                    "LLM",
                    "PostgreSQL",
                ],
                achievements=[
                    "Worked on job intelligence features."
                ],
            )
        ],
    )

    target_requirements = [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "LLM applications",
        "REST APIs",
    ]

    engine = ResumeRewriteEngine()

    result = engine.analyze(
        resume=resume,
        target_requirements=target_requirements,
    )

    print("\nRESUME REWRITE ENGINE")
    print("=" * 60)

    print(
        "Rewrite Readiness:",
        result.overall_readiness_score,
    )

    print("\nSUMMARY")
    print(result.summary)

    print("\nSUGGESTIONS")

    for suggestion in result.suggestions:
        print("\nSection:", suggestion.section)
        print("Original:", suggestion.source_text)
        print("Issue:", suggestion.issue)
        print(
            "Target Requirement:",
            suggestion.target_requirement,
        )
        print(
            "Evidence:",
            suggestion.available_evidence,
        )
        print(
            "Suggested Rewrite:",
            suggestion.suggested_rewrite,
        )
        print(
            "Confidence:",
            suggestion.confidence,
        )
        print(
            "Evidence Status:",
            suggestion.evidence_status,
        )

    print("\nPRIORITY ACTIONS")

    for action in result.priority_actions:
        print("-", action)

    print("\nSAFETY NOTES")

    for note in result.safety_notes:
        print("-", note)

    # ----------------------------------------------------------
    # Core validation
    # ----------------------------------------------------------

    assert 0 <= result.overall_readiness_score <= 100

    assert result.summary.strip()

    assert len(result.suggestions) > 0

    assert len(result.priority_actions) > 0

    assert len(result.safety_notes) >= 3

    # ----------------------------------------------------------
    # Evidence safety
    # ----------------------------------------------------------

    for suggestion in result.suggestions:
        assert suggestion.source_text.strip()

        assert 0 <= suggestion.confidence <= 100

        assert suggestion.evidence_status in {
            "SUPPORTED",
            "LIMITED_EVIDENCE",
        }

        # Rewrites must contain something meaningful.
        assert suggestion.suggested_rewrite.strip()

    # ----------------------------------------------------------
    # Weak bullets must be detected.
    # ----------------------------------------------------------

    assert any(
        "weak or generic"
        in suggestion.issue.lower()
        for suggestion in result.suggestions
    )

    # ----------------------------------------------------------
    # The engine must recognize the actual supported
    # technology evidence.
    # ----------------------------------------------------------

    assert any(
        any(
            "python" in evidence.lower()
            or "fastapi" in evidence.lower()
            or "docker" in evidence.lower()
            for evidence in suggestion.available_evidence
        )
        for suggestion in result.suggestions
    )

    # ----------------------------------------------------------
    # Safety language must explicitly prohibit fabrication.
    # ----------------------------------------------------------

    assert any(
        "fabricate" in note.lower()
        for note in result.safety_notes
    )

    assert any(
        "invent" in note.lower()
        for note in result.safety_notes
    )