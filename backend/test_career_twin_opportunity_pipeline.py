from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)
from backend.schemas.job import (
    Job,
)
from backend.schemas.requirements import (
    JobRequirements,
)
from backend.services.career_twin_opportunity_pipeline import (
    CareerTwinOpportunityPipeline,
)
from backend.services.final_matcher import (
    FinalMatch,
)


def _candidate() -> CandidateProfile:
    return CandidateProfile(
        candidate_id="pipeline-test-user",
        name="Pipeline Test",
        headline="Software Engineer",
        skills=[
            "Python",
            "SQL",
        ],
        technical_skills=[
            "Python",
            "SQL",
        ],
        career_goal=CareerGoal(
            target_roles=[
                "Software Engineer",
            ],
        ),
        preferred_locations=[
            "Bangalore",
        ],
    )


def _job() -> Job:
    return Job(
        source="test",
        source_job_id="pipeline-job-1",
        title="Software Engineer",
        company="CareerPilot Labs",
        location=[
            "Bangalore",
        ],
        remote=False,
        skills=[
            "Python",
            "SQL",
            "FastAPI",
        ],
        description=(
            "Build backend services using Python "
            "and FastAPI."
        ),
        apply_url=(
            "https://example.com/pipeline-job-1"
        ),
        source_url=(
            "https://example.com/pipeline-job-1"
        ),
    )


def _requirements() -> JobRequirements:
    return JobRequirements(
        required_skills=[
            "python",
            "sql",
        ],
        preferred_skills=[
            "fastapi",
        ],
        technologies=[
            "python",
            "sql",
            "fastapi",
        ],
    )


def _match() -> FinalMatch:
    return FinalMatch(
        deterministic_score=80.0,
        semantic_score=82.0,
        final_score=80.8,
        decision="GOOD_MATCH",
        confidence=88.0,
        role_fit=100.0,
        skill_fit=75.0,
        experience_fit=70.0,
        location_fit=100.0,
        salary_fit=70.0,
        career_goal_fit=90.0,
        matched_skills=[
            "python",
            "sql",
        ],
        skill_gaps=[
            "fastapi",
        ],
        strengths=[
            "Strong role alignment",
            "Strong location alignment",
        ],
        explanation=(
            "Base match for pipeline test."
        ),
    )


def test_pipeline_enriches_opportunity():
    pipeline = (
        CareerTwinOpportunityPipeline()
    )

    result = pipeline.enrich(
        candidate=_candidate(),
        job=_job(),
        requirements=_requirements(),
        base_match=_match(),
    )

    assert (
        result["career_twin_id"]
        == "pipeline-test-user"
    )

    assert (
        "career_twin_analysis"
        in result
    )

    assert (
        "personalized_match"
        in result
    )

    personalized = (
        result["personalized_match"]
    )

    assert (
        0
        <= personalized[
            "personalized_score"
        ]
        <= 100
    )


def test_pipeline_preserves_base_match():
    pipeline = (
        CareerTwinOpportunityPipeline()
    )

    base = _match()

    result = pipeline.enrich(
        candidate=_candidate(),
        job=_job(),
        requirements=_requirements(),
        base_match=base,
    )

    personalized = (
        result["personalized_match"]
    )

    assert (
        personalized["base_score"]
        == base.final_score
    )

    assert (
        personalized["base_confidence"]
        == base.confidence
    )


def test_pipeline_produces_career_twin_evidence():
    pipeline = (
        CareerTwinOpportunityPipeline()
    )

    result = pipeline.enrich(
        candidate=_candidate(),
        job=_job(),
        requirements=_requirements(),
        base_match=_match(),
    )

    analysis = (
        result["career_twin_analysis"]
    )

    assert isinstance(
        analysis[
            "career_twin_evidence"
        ],
        list,
    )

    assert isinstance(
        analysis[
            "career_twin_reasoning"
        ],
        str,
    )