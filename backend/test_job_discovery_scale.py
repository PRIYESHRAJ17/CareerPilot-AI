from datetime import (
    datetime,
    timedelta,
    timezone,
)

from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.schemas.job import (
    Job,
)

from backend.services.job_filter import (
    JobFilter,
)


def _candidate(
    role: str = "Software Engineer",
    location: str = "Bangalore",
) -> CandidateProfile:

    return CandidateProfile(
        candidate_id="scale-test",

        name="Scale Test",

        skills=[
            "Python",
            "Java",
            "SQL",
        ],

        career_goal=CareerGoal(
            target_roles=[
                role
            ],
        ),

        preferred_locations=[
            location
        ],
    )


def test_bangalore_alias_matches() -> None:

    job = Job(
        source="test",
        source_job_id="1",
        title="Software Engineer",
        company="Example",
        location=[
            "Bengaluru"
        ],
        description=(
            "Build backend software "
            "using Python."
        ),
        posted_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(),
    )

    assert len(result) == 1


def test_india_scoped_job_is_retained() -> None:

    job = Job(
        source="test",
        source_job_id="2",
        title="Software Engineer",
        company="Example",
        location=[
            "India"
        ],
        description=(
            "Software engineering "
            "role for India."
        ),
        posted_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(),
    )

    assert len(result) == 1


def test_remote_job_matches_location() -> None:

    job = Job(
        source="test",
        source_job_id="3",
        title="Software Engineer",
        company="RemoteCo",
        location=[],
        remote=True,
        description=(
            "Remote software engineering "
            "role using Python."
        ),
        posted_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(),
    )

    assert len(result) == 1


def test_stale_job_is_rejected() -> None:

    stale_date = (
        datetime.now(
            timezone.utc
        )
        - timedelta(
            days=180
        )
    )

    job = Job(
        source="test",
        source_job_id="4",
        title="Software Engineer",
        company="OldCo",
        location=[
            "Bangalore"
        ],
        description=(
            "Software engineering "
            "role using Python."
        ),
        posted_at=(
            stale_date.isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(),
    )

    assert len(result) == 0


def test_irrelevant_role_is_rejected() -> None:

    job = Job(
        source="test",
        source_job_id="5",
        title="Hardware Integration Engineer",
        company="HardwareCo",
        location=[
            "Bangalore"
        ],
        description=(
            "Design mechanical "
            "and hardware systems."
        ),
        posted_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(
            role="Software Engineer"
        ),
    )

    assert len(result) == 0


def test_relevant_software_role_is_kept() -> None:

    job = Job(
        source="test",
        source_job_id="6",
        title="Backend Software Engineer",
        company="SoftwareCo",
        location=[
            "Bangalore"
        ],
        skills=[
            "Python",
            "SQL",
        ],
        description=(
            "Build backend software "
            "services and APIs."
        ),
        posted_at=(
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    )

    result = JobFilter().filter(
        [job],
        _candidate(),
    )

    assert len(result) == 1