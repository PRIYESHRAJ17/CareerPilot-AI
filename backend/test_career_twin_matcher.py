from backend.services.career_twin_matcher import (
    CareerTwinMatcher,
)
from backend.services.final_matcher import (
    FinalMatch,
)


def _base_match() -> FinalMatch:
    return FinalMatch(
        deterministic_score=72.0,
        semantic_score=78.0,
        final_score=74.4,
        decision="GOOD_MATCH",
        confidence=86.0,
        role_fit=85.0,
        skill_fit=75.0,
        experience_fit=90.0,
        location_fit=100.0,
        salary_fit=70.0,
        career_goal_fit=80.0,
        matched_skills=[
            "python",
            "sql",
        ],
        skill_gaps=[
            "docker",
        ],
        strengths=[
            "Strong role alignment",
        ],
        explanation=(
            "Base compatibility evidence."
        ),
    )


def test_career_twin_personalizes_score():
    matcher = CareerTwinMatcher()

    result = matcher.personalize(
        base_match=_base_match(),
        career_twin_analysis={
            "career_twin_match_score": 92.0,
            "career_twin_confidence": 90.0,
            "career_twin_matched_skills": [
                "python",
                "sql",
            ],
            "career_twin_gap_matches": [
                "docker",
            ],
            "career_twin_reasoning": (
                "Strong alignment with the "
                "candidate's tracked direction."
            ),
        },
    )

    assert result.base_score == 74.4
    assert result.career_twin_score == 92.0

    assert (
        result.personalized_score
        > result.base_score
    )

    assert 0 <= (
        result.personalized_score
    ) <= 100

    assert 0 <= (
        result.personalized_confidence
    ) <= 100

    assert (
        "Career Twin skill alignment"
        in result.strengths
    )

    assert (
        "Career development alignment"
        in result.strengths
    )


def test_career_twin_neutral_score_does_not_break_match():
    matcher = CareerTwinMatcher()

    result = matcher.personalize(
        base_match=_base_match(),
        career_twin_analysis={},
    )

    assert 0 <= (
        result.personalized_score
    ) <= 100

    assert result.decision in {
        "APPLY_NOW",
        "GOOD_MATCH",
        "STRETCH",
        "LOW_PRIORITY",
    }


def test_career_twin_score_is_clamped():
    matcher = CareerTwinMatcher()

    result = matcher.personalize(
        base_match=_base_match(),
        career_twin_analysis={
            "career_twin_match_score": 1000,
            "career_twin_confidence": -500,
        },
    )

    assert result.career_twin_score == 100.0
    assert result.career_twin_confidence == 0.0
    assert result.personalized_score <= 100.0