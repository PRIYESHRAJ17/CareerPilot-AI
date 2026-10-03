from backend.schemas.resume import (
    ResumeContact,
    ResumeExperience,
    ResumeProject,
    StructuredResume,
)
from backend.services.llm_resume_reasoner import (
    LLMResumeReasoner,
)
from backend.services.resume_rewrite_engine import (
    RewriteSuggestion,
)


def build_resume() -> StructuredResume:
    return StructuredResume(
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
                    "Built backend APIs using Python and FastAPI."
                ),
                achievements=[
                    "Worked on AI-powered services using Python and LLMs.",
                    "Built backend APIs using FastAPI.",
                    "Containerized services using Docker.",
                ],
                technologies=[
                    "Python",
                    "FastAPI",
                    "LLM",
                    "Docker",
                ],
            )
        ],
        skills=[
            "Python",
            "FastAPI",
            "LLM",
            "Docker",
        ],
        technical_skills=[
            "Python",
            "FastAPI",
            "LLM",
            "Docker",
        ],
        projects=[
            ResumeProject(
                name="CareerPilot AI",
                description=(
                    "Built an AI-powered career platform "
                    "for job matching."
                ),
                technologies=[
                    "Python",
                    "FastAPI",
                    "LLM",
                ],
            )
        ],
    )


def test_llm_reasoner_accepts_evidence_based_rewrite():
    resume = build_resume()

    suggestion = RewriteSuggestion(
        section="experience",
        source_text=(
            "Worked on AI-powered services using Python and LLMs."
        ),
        issue="Weak or generic opening verb",
        target_requirement="LLM applications",
        available_evidence=[
            "Original resume statement: "
            "Worked on AI-powered services using Python and LLMs.",
            "Technology explicitly supported: Python",
            "Technology explicitly supported: LLM",
        ],
        suggested_rewrite=(
            "Developed AI-powered services using Python and LLMs."
        ),
        confidence=80,
        evidence_status="SUPPORTED",
    )

    reasoner = LLMResumeReasoner()

    result = reasoner.analyze(
        resume=resume,
        rewrite_suggestions=[
            suggestion
        ],
    )

    assert result.provider == "none"

    assert len(
        result.candidates
    ) == 1

    candidate = result.candidates[0]

    assert (
        candidate.validation_status
        == "ACCEPTED"
    )

    assert candidate.rewritten_text == (
        "Developed AI-powered services using Python and LLMs."
    )

    assert result.accepted_count == 1

    assert result.rejected_count == 0


def test_llm_reasoner_rejects_unsupported_metric():
    resume = build_resume()

    suggestion = RewriteSuggestion(
        section="experience",
        source_text=(
            "Worked on backend APIs using FastAPI."
        ),
        issue="Weak or generic opening verb",
        target_requirement="FastAPI",
        available_evidence=[
            "Original resume statement: "
            "Worked on backend APIs using FastAPI.",
            "Technology explicitly supported: FastAPI",
        ],
        suggested_rewrite=(
            "Developed backend APIs using FastAPI, "
            "reducing latency by 45%."
        ),
        confidence=85,
        evidence_status="SUPPORTED",
    )

    reasoner = LLMResumeReasoner()

    result = reasoner.analyze(
        resume=resume,
        rewrite_suggestions=[
            suggestion
        ],
    )

    assert len(
        result.candidates
    ) == 1

    candidate = result.candidates[0]

    assert (
        candidate.validation_status
        == "REJECTED"
    )

    assert result.accepted_count == 0

    assert result.rejected_count == 1

    assert any(
        "numeric"
        in issue.lower()
        or "claim"
        in issue.lower()
        for issue in candidate.validation_issues
    )


def test_llm_reasoner_rejects_unsupported_technology():
    resume = build_resume()

    suggestion = RewriteSuggestion(
        section="experience",
        source_text=(
            "Built backend APIs using FastAPI."
        ),
        issue="Improve job alignment",
        target_requirement="FastAPI",
        available_evidence=[
            "Original resume statement: "
            "Built backend APIs using FastAPI.",
            "Technology explicitly supported: FastAPI",
        ],
        suggested_rewrite=(
            "Built scalable backend APIs using FastAPI and Kubernetes."
        ),
        confidence=90,
        evidence_status="SUPPORTED",
    )

    reasoner = LLMResumeReasoner()

    result = reasoner.analyze(
        resume=resume,
        rewrite_suggestions=[
            suggestion
        ],
    )

    candidate = result.candidates[0]

    assert (
        candidate.validation_status
        == "REJECTED"
    )

    assert any(
        "technical"
        in issue.lower()
        or "unsupported"
        in issue.lower()
        for issue in candidate.validation_issues
    )


def test_validator_preserves_original_evidence():
    resume = build_resume()

    reasoner = LLMResumeReasoner()

    suggestion = RewriteSuggestion(
        section="experience",
        source_text=(
            "Containerized services using Docker."
        ),
        issue="Alignment improvement",
        target_requirement="Docker",
        available_evidence=[
            "Original resume statement: "
            "Containerized services using Docker.",
            "Technology explicitly supported: Docker",
        ],
        suggested_rewrite=(
            "Containerized services using Docker."
        ),
        confidence=80,
        evidence_status="SUPPORTED",
    )

    validation = reasoner.validate_candidate(
        resume=resume,
        source_suggestion=suggestion,
        generated_text=(
            "Containerized services using Docker."
        ),
    )

    assert (
        validation["status"]
        == "ACCEPTED"
    )

    assert validation["issues"] == []


def test_empty_reasoning_input():
    resume = build_resume()

    reasoner = LLMResumeReasoner()

    result = reasoner.analyze(
        resume=resume,
        rewrite_suggestions=[],
    )

    assert result.candidates == []

    assert result.accepted_count == 0

    assert result.rejected_count == 0

    assert (
        "No rewrite candidates"
        in result.summary
    )