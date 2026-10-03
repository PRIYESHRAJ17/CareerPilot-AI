from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)
from backend.schemas.job import (
    Experience,
    Job,
)
from backend.services.career_twin_job_intelligence import (
    CareerTwinJobIntelligence,
)


def _job() -> Job:
    return Job(
        source="test",
        source_job_id="job-1",
        title="Software Engineer",
        company="CareerPilot Labs",
        location=["Bangalore"],
        remote=False,
        experience=Experience(
            min_years=1,
            max_years=4,
        ),
        skills=[
            "Python",
            "FastAPI",
            "SQL",
            "Docker",
        ],
        description=(
            "Required: Python, FastAPI, SQL. "
            "Docker experience is preferred."
        ),
        apply_url="https://example.com/job-1",
        source_url="https://example.com/job-1",
    )


def _twin():
    return {
        "current_skills": [
            "Python",
            "SQL",
        ],
        "strengths": [
            "Python",
        ],
        "skill_gaps": [
            "FastAPI",
            "Docker",
        ],
        "target_roles": [
            "Software Engineer",
        ],
        "target_industries": [
            "SaaS",
        ],
        "preferred_locations": [
            "Bangalore",
        ],
        "preferred_work_modes": [
            "onsite",
        ],
        "derived": {
            "strengths": [
                "Python",
            ],
            "skill_gaps": [
                "FastAPI",
                "Docker",
            ],
            "career_directions": [
                "Software Engineer",
            ],
        },
    }


def test_career_twin_job_analysis():
    engine = CareerTwinJobIntelligence()

    result = engine.analyze(
        job=_job(),
        career_twin=_twin(),
    )

    assert 0 <= result[
        "career_twin_match_score"
    ] <= 100

    assert 0 <= result[
        "career_twin_confidence"
    ] <= 100

    assert (
        "python"
        in result[
            "career_twin_matched_skills"
        ]
    )

    assert (
        "fastapi"
        in result[
            "career_twin_missing_skills"
        ]
    )

    assert (
        "fastapi"
        in result[
            "career_twin_gap_matches"
        ]
    )


def test_requirement_aggregation():
    engine = CareerTwinJobIntelligence()

    jobs = [
        _job(),
        _job(),
    ]

    aggregate = (
        engine.aggregate_requirements(
            jobs
        )
    )

    assert aggregate[
        "jobs_analyzed"
    ] == 2

    technology_names = {
        item["value"]
        for item in aggregate[
            "top_technologies"
        ]
    }

    assert "python" in technology_names
    assert (
        aggregate[
            "unique_technologies"
        ]
        >= 3
    )


def test_career_twin_with_empty_profile():
    engine = CareerTwinJobIntelligence()

    result = engine.analyze(
        job=_job(),
        career_twin={},
    )

    assert 0 <= result[
        "career_twin_match_score"
    ] <= 100

    assert isinstance(
        result[
            "career_twin_evidence"
        ],
        list,
    )

    assert isinstance(
        result[
            "career_twin_risks"
        ],
        list,
    )