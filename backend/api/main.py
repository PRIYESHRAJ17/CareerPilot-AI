from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (
    JobSearchRequest,
    JobSearchResponse,
)

from backend.schemas.candidate import (
    CandidateProfile,
    CareerGoal,
)

from backend.services.search_service import (
    CareerSearchService,
)


app = FastAPI(
    title="CareerPilot AI API",
    description=(
        "Agentic Career Intelligence API "
        "for job discovery and matching."
    ),
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


search_service = (
    CareerSearchService()
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "careerpilot-api",
        "version": "0.3.0",
    }


@app.post(
    "/jobs/search",
    response_model=JobSearchResponse,
)
def search_jobs(
    request: JobSearchRequest,
):
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

        results = (
            search_service.search(
                candidate=candidate,
                query=request.role,
                location=request.location,
            )
        )

        salary_summary = (
            search_service
            .build_salary_summary(
                results=results,
                minimum_salary_lpa=(
                    request.minimum_salary_lpa
                ),
            )
        )

        source_summary = (
            search_service
            .build_source_summary(
                results=results,
            )
        )

        return JobSearchResponse(
            query=request.role,
            location=request.location,
            result_count=len(results),
            results=results,
            salary_summary=salary_summary,
            source_summary=source_summary,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc