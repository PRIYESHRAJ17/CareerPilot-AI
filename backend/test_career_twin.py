from backend.services.career_twin import (
    get_or_create,
    update_from_candidate,
)


def test_career_twin_create_and_update():

    candidate_id = (
        "week6-test-user"
    )

    twin = get_or_create(
        candidate_id
    )

    assert (
        twin.candidate_id
        == candidate_id
    )

    updated = (
        update_from_candidate(
            candidate={
                "candidate_id":
                    candidate_id,

                "name":
                    "Test User",

                "skills": [
                    "Python",
                    "FastAPI",
                ],

                "technical_skills": [
                    "SQL"
                ],

                "career_goal": {

                    "target_roles": [
                        "AI Engineer"
                    ],

                    "target_locations": [
                        "Bengaluru"
                    ],
                },
            },

            candidate_intelligence={

                "readiness_score":
                    72,

                "readiness_level":
                    "NEAR_READY",

                "strengths": [
                    "Backend development"
                ],

                "career_direction": [
                    "AI / ML Engineering"
                ],
            },

            recommendations=[
                {
                    "action":
                        "Build an AI project"
                }
            ],
        )
    )

    assert (
        "Python"
        in updated.profile.skills
    )

    assert (
        "AI Engineer"
        in updated.profile.target_roles
    )

    assert (
        updated.derived.readiness_score
        == 72
    )

    assert updated.memory


def test_career_twin_persists():

    candidate_id = (
        "week6-persistence-test"
    )

    update_from_candidate(
        candidate={
            "candidate_id":
                candidate_id,

            "skills": [
                "Docker"
            ],
        }
    )

    loaded = get_or_create(
        candidate_id
    )

    assert (
        "Docker"
        in loaded.profile.skills
    )


def test_career_twin_merges_historical_skills():

    candidate_id = (
        "week6-merge-test"
    )

    update_from_candidate(
        candidate={
            "candidate_id":
                candidate_id,

            "skills": [
                "Python"
            ],

            "career_goal": {
                "target_roles": [
                    "Backend Engineer"
                ]
            },
        }
    )

    from backend.services.career_twin import (
        merge_twin_into_candidate_profile,
    )

    twin = get_or_create(
        candidate_id
    )

    merged = (
        merge_twin_into_candidate_profile(
            {
                "candidate_id":
                    candidate_id,

                "skills": [
                    "Docker"
                ],

                "career_goal": {
                    "target_roles": [
                        "AI Engineer"
                    ]
                },
            },
            twin,
        )
    )

    assert "Python" in (
        merged["skills"]
    )

    assert "Docker" in (
        merged["skills"]
    )

    assert "Backend Engineer" in (
        merged["career_goal"][
            "target_roles"
        ]
    )

    assert "AI Engineer" in (
        merged["career_goal"][
            "target_roles"
        ]
    )