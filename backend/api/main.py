from dataclasses import asdict

from dotenv import load_dotenv

load_dotenv()

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import (
    CandidateIntelligenceResponse,
    CareerStrategyResponse,
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

from backend.services.candidate_intelligence import (
    CandidateIntelligenceEngine,
)

from backend.career_strategy import (
    generate_career_strategy,
)

from backend.services.resume_parser import (
    ResumeParser,
)

from backend.services.resume_structurer import (
    ResumeStructurer,
)

from backend.services.resume_intelligence import (
    ResumeIntelligenceEngine,
)

from backend.services.ats_analyzer import (
    ATSAnalyzer,
)

from backend.services.job_resume_analyzer import (
    JobResumeAnalyzer,
)

from backend.services.resume_rewrite_engine import (
    ResumeRewriteEngine,
)

from backend.services.llm_resume_reasoner import (
    LLMResumeReasoner,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="CareerPilot AI API",
    description=(
        "AI-powered career development, job search, "
        "candidate intelligence, resume intelligence, "
        "ATS analysis, job-specific resume analysis, "
        "evidence-based resume rewriting, and "
        "LLM-powered rewrite validation."
    ),
    version="0.6.0",
)


# ============================================================
# CORS
# ============================================================

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


# ============================================================
# SERVICES
# ============================================================

search_service = CareerSearchService()

candidate_intelligence_engine = (
    CandidateIntelligenceEngine()
)

resume_parser = ResumeParser()

resume_structurer = ResumeStructurer()

resume_intelligence_engine = (
    ResumeIntelligenceEngine()
)

ats_analyzer = ATSAnalyzer()

job_resume_analyzer = JobResumeAnalyzer()

resume_rewrite_engine = ResumeRewriteEngine()

llm_resume_reasoner = LLMResumeReasoner()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "CareerPilot AI API",
        "version": "0.6.0",
        "status": "running",
        "features": [
            "job-search",
            "candidate-intelligence",
            "career-strategy",
            "resume-analysis",
            "ats-analysis",
            "job-specific-resume-analysis",
            "resume-rewrite-engine",
            "evidence-based-rewriting",
            "llm-resume-reasoning",
            "rewrite-validation",
        ],
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "careerpilot-api",
        "version": "0.6.0",
    }


# ============================================================
# JOB SEARCH
# ============================================================

@app.post(
    "/jobs/search",
    response_model=JobSearchResponse,
)
def search_jobs(
    request: JobSearchRequest,
):
    """
    Search jobs and generate candidate intelligence
    and career strategy for the same candidate.

    Pipeline:

        Search Request
              ↓
        Candidate Profile
           ↙         ↘
          ↓           ↓
    Candidate      Job Search
    Intelligence     Engine
          ↓             ↓
    Career          Ranked
    Strategy          Jobs
           ↘         ↙
            Unified Response
    """

    try:
        # ----------------------------------------------------
        # 1. BUILD CANDIDATE PROFILE
        # ----------------------------------------------------

        career_goal = CareerGoal(
            target_roles=[
                request.role
            ],
            target_industries=(
                request.target_industries
            ),
            target_locations=(
                [request.location]
                if request.location
                else []
            ),
            minimum_salary_lpa=(
                request.minimum_salary_lpa
            ),
            preferred_work_modes=(
                request.preferred_work_modes
            ),
        )

        candidate = CandidateProfile(
            candidate_id="api-user",
            name="CareerPilot User",
            headline=request.role,
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
            career_goal=career_goal,
        )

        # ----------------------------------------------------
        # 2. CANDIDATE INTELLIGENCE
        # ----------------------------------------------------

        intelligence = (
            candidate_intelligence_engine.analyze(
                candidate
            )
        )

        candidate_intelligence = (
            CandidateIntelligenceResponse(
                **asdict(intelligence)
            )
        )

        # ----------------------------------------------------
        # 3. CAREER STRATEGY
        # ----------------------------------------------------

        strategy = generate_career_strategy(
            intelligence
        )

        career_strategy = (
            CareerStrategyResponse(
                **asdict(strategy)
            )
        )

        # ----------------------------------------------------
        # 4. JOB SEARCH
        # ----------------------------------------------------

        results = search_service.search(
            candidate=candidate,
            query=request.role,
            location=request.location,
        )

        # ----------------------------------------------------
        # 5. SALARY INTELLIGENCE
        # ----------------------------------------------------

        salary_summary = (
            search_service.build_salary_summary(
                results=results,
                minimum_salary_lpa=(
                    request.minimum_salary_lpa
                ),
            )
        )

        # ----------------------------------------------------
        # 6. SOURCE INTELLIGENCE
        # ----------------------------------------------------

        source_summary = (
            search_service.build_source_summary(
                results=results,
            )
        )

        # ----------------------------------------------------
        # 7. UNIFIED RESPONSE
        # ----------------------------------------------------

        return JobSearchResponse(
            query=request.role,
            location=request.location,
            result_count=len(results),
            results=results,
            salary_summary=salary_summary,
            source_summary=source_summary,
            candidate_intelligence=(
                candidate_intelligence
            ),
            career_strategy=(
                career_strategy
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# RESUME ANALYSIS
# ============================================================

@app.post("/resume/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
):
    """
    Analyze a PDF resume.

    Pipeline:

        PDF
         ↓
        Parser
         ↓
        Structurer
         ↓
        Resume Intelligence
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume filename is missing.",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF resumes are currently "
                "supported."
            ),
        )

    try:
        # ----------------------------------------------------
        # 1. READ FILE
        # ----------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded resume file is empty."
                ),
            )

        # ----------------------------------------------------
        # 2. PARSE PDF
        # ----------------------------------------------------

        parsed_resume = (
            resume_parser.parse(
                file_bytes
            )
        )

        # ----------------------------------------------------
        # 3. STRUCTURE RESUME
        # ----------------------------------------------------

        structured_resume = (
            resume_structurer.structure(
                parsed_resume
            )
        )

        # ----------------------------------------------------
        # 4. RESUME INTELLIGENCE
        # ----------------------------------------------------

        intelligence = (
            resume_intelligence_engine.analyze(
                structured_resume
            )
        )

        # ----------------------------------------------------
        # 5. RESPONSE
        # ----------------------------------------------------

        return {
            "filename": file.filename,
            "page_count": (
                parsed_resume.page_count
            ),
            "resume": (
                structured_resume.model_dump()
            ),
            "intelligence": (
                intelligence.to_dict()
            ),
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to analyze the "
                "uploaded resume."
            ),
        ) from exc


# ============================================================
# RESUME ATS + JOB-SPECIFIC ANALYSIS
# + EVIDENCE-BASED REWRITE
# + LLM REASONING / VALIDATION
# ============================================================

@app.post("/resume/ats-analyze")
async def analyze_resume_for_job(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Perform a complete job-specific resume analysis.

    Pipeline:

        PDF
         ↓
        Parser
         ↓
        Structured Resume
         ↓
        ┌─────────────────────────────────┐
        │                                 │
        ↓                                 ↓
    ATS Analyzer                  Job Resume Analyzer
        │                                 │
        │                                 ↓
        │                           Requirements
        │                                 │
        └───────────────┬─────────────────┘
                        ↓
              Resume Rewrite Engine
                        ↓
              Evidence-backed
              Rewrite Suggestions
                        ↓
              LLM Resume Reasoner
                        ↓
              Evidence Validation
                        ↓
              ACCEPTED / REJECTED

    Important:
    The LLM reasoning layer never replaces the
    deterministic evidence checks. Generated
    candidates are validated before acceptance.
    """

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume filename is missing.",
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF resumes are currently "
                "supported."
            ),
        )

    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "Job description cannot be empty."
            ),
        )

    try:
        # ----------------------------------------------------
        # 1. READ PDF
        # ----------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded resume file is empty."
                ),
            )

        # ----------------------------------------------------
        # 2. PARSE RESUME
        # ----------------------------------------------------

        parsed_resume = (
            resume_parser.parse(
                file_bytes
            )
        )

        # ----------------------------------------------------
        # 3. STRUCTURE RESUME
        # ----------------------------------------------------

        structured_resume = (
            resume_structurer.structure(
                parsed_resume
            )
        )

        # ----------------------------------------------------
        # 4. ATS ANALYSIS
        # ----------------------------------------------------

        ats_result = (
            ats_analyzer.analyze(
                structured_resume,
                job_description,
            )
        )

        # ----------------------------------------------------
        # 5. JOB-SPECIFIC RESUME ANALYSIS
        # ----------------------------------------------------

        job_resume_result = (
            job_resume_analyzer.analyze(
                resume=structured_resume,
                job_description=job_description,
            )
        )

        # ----------------------------------------------------
        # 6. BUILD VERIFIED TARGET REQUIREMENTS
        # ----------------------------------------------------
        #
        # We intentionally do not treat the entire job
        # description as resume evidence.
        #
        # Requirements are first extracted and classified
        # by the job-specific analyzer.

        extracted_requirements = []

        for item in (
            job_resume_result.strong_matches
        ):
            extracted_requirements.append(
                item.requirement
            )

        for item in (
            job_resume_result.partial_matches
        ):
            extracted_requirements.append(
                item.requirement
            )

        for item in (
            job_resume_result.missing_requirements
        ):
            extracted_requirements.append(
                item.requirement
            )

        # ----------------------------------------------------
        # 7. DEDUPLICATE REQUIREMENTS
        # ----------------------------------------------------

        verified_requirements = []

        seen_requirements = set()

        for requirement in (
            extracted_requirements
        ):
            normalized = (
                requirement.strip().lower()
            )

            if not normalized:
                continue

            if normalized in seen_requirements:
                continue

            seen_requirements.add(
                normalized
            )

            verified_requirements.append(
                requirement
            )

        # ----------------------------------------------------
        # 8. DETERMINISTIC REWRITE ENGINE
        # ----------------------------------------------------

        rewrite_result = (
            resume_rewrite_engine.analyze(
                resume=structured_resume,
                target_requirements=(
                    verified_requirements
                ),
            )
        )

        # ----------------------------------------------------
        # 9. LLM RESUME REASONER
        # ----------------------------------------------------
        #
        # The reasoner receives only the rewrite
        # suggestions generated from resume evidence.
        #
        # provider=none currently means deterministic
        # fallback generation + real evidence validation.
        #
        # Once a provider is configured, this same pipeline
        # can perform actual LLM generation while retaining
        # the validator.

        llm_reasoning_result = (
            llm_resume_reasoner.analyze(
                resume=structured_resume,
                rewrite_suggestions=(
                    rewrite_result.suggestions
                ),
            )
        )

        # ----------------------------------------------------
        # 10. LLM REASONING SERIALIZATION
        # ----------------------------------------------------

        llm_reasoning = (
            llm_resume_reasoner.to_dict(
                llm_reasoning_result
            )
        )

        # ----------------------------------------------------
        # 11. RESPONSE
        # ----------------------------------------------------

        return {
            "filename": file.filename,

            "page_count": (
                parsed_resume.page_count
            ),

            # ------------------------------------------------
            # Structured Resume
            # ------------------------------------------------

            "resume": (
                structured_resume.model_dump()
            ),

            # ------------------------------------------------
            # ATS Analysis
            # ------------------------------------------------

            "ats_analysis": (
                ats_result.to_dict()
            ),

            # ------------------------------------------------
            # Job-Specific Analysis
            # ------------------------------------------------

            "job_resume_analysis": {
                "overall_fit_score": (
                    job_resume_result.overall_fit_score
                ),

                "evidence_score": (
                    job_resume_result.evidence_score
                ),

                "keyword_alignment_score": (
                    job_resume_result.keyword_alignment_score
                ),

                "experience_alignment_score": (
                    job_resume_result.experience_alignment_score
                ),

                "section_relevance_score": (
                    job_resume_result.section_relevance_score
                ),

                "strong_matches": [
                    asdict(item)
                    for item
                    in job_resume_result.strong_matches
                ],

                "partial_matches": [
                    asdict(item)
                    for item
                    in job_resume_result.partial_matches
                ],

                "missing_requirements": [
                    asdict(item)
                    for item
                    in job_resume_result.missing_requirements
                ],

                "top_priorities": (
                    job_resume_result.top_priorities
                ),

                "recommendations": (
                    job_resume_result.recommendations
                ),

                "target_role": (
                    job_resume_result.target_role
                ),

                "summary": (
                    job_resume_result.summary
                ),
            },

            # ------------------------------------------------
            # Deterministic Rewrite Analysis
            # ------------------------------------------------

            "rewrite_analysis": {
                "overall_readiness_score": (
                    rewrite_result.overall_readiness_score
                ),

                "suggestions": [
                    asdict(item)
                    for item
                    in rewrite_result.suggestions
                ],

                "priority_actions": (
                    rewrite_result.priority_actions
                ),

                "safety_notes": (
                    rewrite_result.safety_notes
                ),

                "summary": (
                    rewrite_result.summary
                ),
            },

            # ------------------------------------------------
            # NEW: LLM Reasoning
            # ------------------------------------------------

            "llm_reasoning": llm_reasoning,

            # ------------------------------------------------
            # Pipeline Metadata
            # ------------------------------------------------

            "rewrite_pipeline": {
                "requirements_used": (
                    verified_requirements
                ),

                "evidence_first": True,

                "hallucination_protection": True,

                "llm_reasoning_enabled": True,

                "llm_provider": (
                    llm_reasoning_result.provider
                ),

                "llm_model": (
                    llm_reasoning_result.model
                ),

                "accepted_rewrites": (
                    llm_reasoning_result.accepted_count
                ),

                "rejected_rewrites": (
                    llm_reasoning_result.rejected_count
                ),
            },
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to analyze the resume "
                "for the target job."
            ),
        ) from exc