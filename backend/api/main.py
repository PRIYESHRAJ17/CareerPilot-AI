from dotenv import load_dotenv

# Load local environment variables before any connector is created.
load_dotenv()

from fastapi import FastAPI, HTTPException

from backend.api.models import JobSearchRequest
from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)
from backend.services.search_service import CareerSearchService


app = FastAPI(
    title="CareerPilot AI API",
    description=(
        "Agentic Career Intelligence API "
        "for job discovery and matching."
    ),
    version="0.2.0",
)


# Create the search service only after .env has been loaded.
search_service = CareerSearchService()


@app.get("/health")
def health():
    """Basic API health endpoint."""

    return {
        "status": "healthy",
        "service": "careerpilot-api",
        "version": "0.2.0",
    }


@app.post("/jobs/search")
def search_jobs(
    request: JobSearchRequest,
):
    """
    Search live job sources and return ranked CareerPilot matches.
    """

    try:
        candidate = CandidateProfile(
            candidate_id="api-user",

            skills=request.skills,

            technical_skills=request.skills,

            years_of_experience=(
                request.experience_years
            ),

            preferred_locations=(
                [request.location]
                if request.location
                else []
            ),

            preferred_work_modes=(
                request.preferred_work_modes
            ),

            career_goal=CareerGoal(
                target_roles=[
                    request.role
                ],

                target_industries=(
                    request.target_industries
                ),

                minimum_salary_lpa=(
                    request.minimum_salary_lpa
                ),
            ),
        )

        results = search_service.search(
            candidate=candidate,
            query=request.role,
            location=request.location,
        )

        return {
            "query": request.role,
            "location": request.location,
            "result_count": len(results),
            "results": results,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc