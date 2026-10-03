from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from backend.schemas.candidate import CandidateProfile, CareerGoal
from backend.schemas.job import Experience, Job, Salary
from backend.services.requirements_extractor import (
    JobRequirementsExtractor,
)
from backend.services.search_service import CareerSearchService


# ============================================================
# SERVICES
# ============================================================

search_service = CareerSearchService()
requirements_extractor = JobRequirementsExtractor()


# ============================================================
# SERIALIZATION
# ============================================================

def _serialize(value: Any) -> Any:
    """
    Convert CareerPilot domain objects into JSON-compatible data.
    """

    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _serialize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ============================================================
# INPUT BUILDERS
# ============================================================

def _build_candidate_profile(
    candidate_data: Dict[str, Any],
) -> CandidateProfile:
    """
    Build the existing CandidateProfile domain object from
    tool input without changing the Week 1-3 schema.
    """

    career_goal_data = candidate_data.get(
        "career_goal",
        {},
    ) or {}

    career_goal = CareerGoal(
        target_roles=list(
            career_goal_data.get(
                "target_roles",
                [],
            )
            or []
        ),
        target_industries=list(
            career_goal_data.get(
                "target_industries",
                [],
            )
            or []
        ),
        target_locations=list(
            career_goal_data.get(
                "target_locations",
                [],
            )
            or []
        ),
        minimum_salary_lpa=career_goal_data.get(
            "minimum_salary_lpa"
        ),
        preferred_work_modes=list(
            career_goal_data.get(
                "preferred_work_modes",
                [],
            )
            or []
        ),
    )

    skills = list(
        candidate_data.get(
            "skills",
            [],
        )
        or []
    )

    technical_skills = list(
        candidate_data.get(
            "technical_skills",
            skills,
        )
        or []
    )

    candidate = CandidateProfile(
        candidate_id=str(
            candidate_data.get(
                "candidate_id",
                "tool-user",
            )
        ),
        name=str(
            candidate_data.get(
                "name",
                "",
            )
        ),
        headline=str(
            candidate_data.get(
                "headline",
                "",
            )
        ),
        skills=skills,
        technical_skills=technical_skills,
        projects=list(
            candidate_data.get(
                "projects",
                [],
            )
            or []
        ),
        experience=list(
            candidate_data.get(
                "experience",
                [],
            )
            or []
        ),
        years_of_experience=candidate_data.get(
            "years_of_experience"
        ),
        preferred_locations=list(
            candidate_data.get(
                "preferred_locations",
                [],
            )
            or []
        ),
        preferred_work_modes=list(
            candidate_data.get(
                "preferred_work_modes",
                [],
            )
            or []
        ),
        career_goal=career_goal,
    )

    return candidate


def _build_job(
    job_data: Dict[str, Any],
) -> Job:
    """
    Build the canonical Job dataclass from tool input.
    """

    experience_data = (
        job_data.get("experience", {})
        or {}
    )

    salary_data = (
        job_data.get("salary", {})
        or {}
    )

    return Job(
        source=str(
            job_data.get(
                "source",
                "tool",
            )
        ),
        source_job_id=str(
            job_data.get(
                "source_job_id",
                "",
            )
        ),
        title=str(
            job_data.get(
                "title",
                "",
            )
        ),
        company=str(
            job_data.get(
                "company",
                "",
            )
        ),
        location=list(
            job_data.get(
                "location",
                [],
            )
            or []
        ),
        remote=bool(
            job_data.get(
                "remote",
                False,
            )
        ),
        employment_type=job_data.get(
            "employment_type"
        ),
        experience=Experience(
            min_years=experience_data.get(
                "min_years"
            ),
            max_years=experience_data.get(
                "max_years"
            ),
        ),
        salary=Salary(
            min_lpa=salary_data.get(
                "min_lpa"
            ),
            max_lpa=salary_data.get(
                "max_lpa"
            ),
            currency=str(
                salary_data.get(
                    "currency",
                    "INR",
                )
            ),
        ),
        skills=list(
            job_data.get(
                "skills",
                [],
            )
            or []
        ),
        description=str(
            job_data.get(
                "description",
                "",
            )
        ),
        apply_url=str(
            job_data.get(
                "apply_url",
                "",
            )
        ),
        source_url=str(
            job_data.get(
                "source_url",
                "",
            )
        ),
        posted_at=job_data.get(
            "posted_at"
        ),
        metadata=dict(
            job_data.get(
                "metadata",
                {},
            )
            or {}
        ),
        sources=list(
            job_data.get(
                "sources",
                [],
            )
            or []
        ),
        source_records=list(
            job_data.get(
                "source_records",
                [],
            )
            or []
        ),
    )


# ============================================================
# LOW-LEVEL TOOL HELPERS
# ============================================================

def search_jobs_for_candidate(
    candidate_data: Dict[str, Any],
    query: str,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the existing CareerSearchService pipeline for a
    candidate.

    Existing pipeline:

        Discovery
            ↓
        Deduplication
            ↓
        Salary intelligence
            ↓
        Hard filtering
            ↓
        Requirements extraction
            ↓
        Hybrid matching
            ↓
        Ranking
    """

    if not query or not query.strip():
        raise ValueError(
            "Job search query cannot be empty."
        )

    candidate = _build_candidate_profile(
        candidate_data
    )

    results = search_service.search(
        candidate=candidate,
        query=query.strip(),
        location=(
            location.strip()
            if location
            else None
        ),
    )

    return {
        "query": query.strip(),
        "location": location,
        "count": len(results),
        "results": [
            _serialize(result)
            for result in results
        ],
    }


def extract_job_requirements(
    job_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministically extract structured requirements from
    a canonical job.
    """

    job = _build_job(job_data)

    requirements = (
        requirements_extractor.extract(job)
    )

    return _serialize(requirements)


# ============================================================
# LANGCHAIN TOOLS
# ============================================================

@tool
def search_jobs(
    candidate_data: Dict[str, Any],
    query: str,
    location: str = "",
) -> Dict[str, Any]:
    """
    Search and rank jobs for a candidate.

    Use this tool when the agent needs real opportunity
    discovery, filtering, matching, salary intelligence,
    and ranked job results.
    """

    return search_jobs_for_candidate(
        candidate_data=candidate_data,
        query=query,
        location=location or None,
    )


@tool
def extract_job_requirements(
    job: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract deterministic job requirements from a job.

    Returns required skills, preferred skills, experience,
    education, responsibilities, seniority, hard and soft
    requirements, technologies, domain, and keywords.
    """

    return extract_job_requirements(
        job_data=job
    )


@tool
def analyze_job_description(
    job_description: str,
    job_title: str = "",
) -> Dict[str, Any]:
    """
    Analyze a raw job description by wrapping it inside the
    canonical Job schema and using the existing deterministic
    requirements extractor.
    """

    if not job_description or not job_description.strip():
        raise ValueError(
            "Job description cannot be empty."
        )

    job = Job(
        source="job-description-tool",
        source_job_id="tool-job",
        title=job_title or "Unknown Role",
        company="Unknown Company",
        description=job_description.strip(),
    )

    requirements = (
        requirements_extractor.extract(job)
    )

    return {
        "job_title": job.title,
        "requirements": _serialize(
            requirements
        ),
    }


# ============================================================
# CONVENIENCE PIPELINE
# ============================================================

def run_job_intelligence_pipeline(
    candidate_data: Dict[str, Any],
    query: str,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the deterministic job-intelligence workflow as one
    reusable capability for future agents.

    This does not replace CareerSearchService. It wraps it.
    """

    search_result = search_jobs_for_candidate(
        candidate_data=candidate_data,
        query=query,
        location=location,
    )

    return {
        "search": search_result,
        "jobs_found": search_result["count"],
    }


@tool
def run_job_search_pipeline(
    candidate_data: Dict[str, Any],
    query: str,
    location: str = "",
) -> Dict[str, Any]:
    """
    Run the complete deterministic job-search intelligence
    pipeline for an agent.
    """

    return run_job_intelligence_pipeline(
        candidate_data=candidate_data,
        query=query,
        location=location or None,
    )