from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)
from backend.schemas.job import Job

from backend.services.career_twin_market_intelligence import (
    CareerTwinMarketIntelligence,
)


def _candidate() -> CandidateProfile:
    return CandidateProfile(
        candidate_id="market-test-user",
        name="Market Test",
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


def _jobs():
    return [
        Job(
            source="test",
            source_job_id="1",
            title="Software Engineer",
            company="Company A",
            location=[
                "Bangalore",
            ],
            skills=[
                "Python",
                "FastAPI",
                "Docker",
            ],
            description=(
                "Required: Python, FastAPI, Docker."
            ),
        ),
        Job(
            source="test",
            source_job_id="2",
            title="Backend Engineer",
            company="Company B",
            location=[
                "Bangalore",
            ],
            skills=[
                "Python",
                "FastAPI",
                "Docker",
                "SQL",
            ],
            description=(
                "Required: Python, FastAPI, Docker, SQL."
            ),
        ),
        Job(
            source="test",
            source_job_id="3",
            title="Software Developer",
            company="Company C",
            location=[
                "Bangalore",
            ],
            skills=[
                "Python",
                "FastAPI",
                "SQL",
            ],
            description=(
                "Required: Python, FastAPI, SQL."
            ),
        ),
    ]


def test_market_analysis_detects_recurring_gap():
    engine = (
        CareerTwinMarketIntelligence()
    )

    result = engine.analyze(
        candidate=_candidate(),
        jobs=_jobs(),
        career_twin={
            "current_skills": [
                "Python",
                "SQL",
            ],
        },
    )

    assert (
        result["jobs_analyzed"]
        == 3
    )

    assert (
        "fastapi"
        in result["priority_skill_gaps"]
    )

    assert (
        result["market_summary"]["market_depth"]
        == "LOW"
    )

    assert result[
        "recommendations"
    ]


def test_market_analysis_preserves_candidate_skills():
    engine = (
        CareerTwinMarketIntelligence()
    )

    result = engine.analyze(
        candidate=_candidate(),
        jobs=_jobs(),
        career_twin={},
    )

    assert (
        result["candidate_skill_count"]
        >= 2
    )

    top_skills = {
        item["value"]
        for item
        in result[
            "top_market_skills"
        ]
    }

    assert "python" in top_skills


def test_market_recommendations_have_evidence():
    engine = (
        CareerTwinMarketIntelligence()
    )

    result = engine.analyze(
        candidate=_candidate(),
        jobs=_jobs(),
        career_twin={},
    )

    for recommendation in result[
        "recommendations"
    ]:
        assert (
            recommendation[
                "evidence_source"
            ]
            == "live_opportunity_pool"
        )

        assert (
            recommendation["action"]
        )


def test_market_sync_returns_twin_payload(
    monkeypatch,
):
    engine = (
        CareerTwinMarketIntelligence()
    )

    fake_twin = {
        "candidate_id": (
            "market-test-user"
        ),
        "version": 4,
    }

    def fake_get_or_create(
        candidate_id,
    ):
        assert (
            candidate_id
            == "market-test-user"
        )

        return fake_twin

    def fake_update_from_candidate(
        candidate,
        candidate_intelligence,
        skill_gaps,
        recommendations,
    ):
        assert (
            candidate.candidate_id
            == "market-test-user"
        )

        assert skill_gaps
        assert recommendations

        return {
            "candidate_id": (
                "market-test-user"
            ),
            "version": 5,
            "derived": {
                "skill_gaps": (
                    skill_gaps
                ),
            },
        }

    monkeypatch.setattr(
        (
            "backend.services."
            "career_twin_market_intelligence."
            "get_or_create"
        ),
        fake_get_or_create,
    )

    monkeypatch.setattr(
        (
            "backend.services."
            "career_twin_market_intelligence."
            "update_from_candidate"
        ),
        fake_update_from_candidate,
    )

    analysis = engine.analyze(
        candidate=_candidate(),
        jobs=_jobs(),
        career_twin=fake_twin,
    )

    result = engine.sync_to_career_twin(
        candidate=_candidate(),
        candidate_intelligence={},
        analysis=analysis,
    )

    assert (
        result["candidate_id"]
        == "market-test-user"
    )

    assert (
        result["career_twin"]["version"]
        == 5
    )