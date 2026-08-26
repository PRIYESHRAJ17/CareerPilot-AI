from typing import List, Optional

from pydantic import BaseModel, Field


# ==========================================================
# SEARCH REQUEST
# ==========================================================

class JobSearchRequest(BaseModel):
    role: str = Field(
        ...,
        min_length=1,
        description="Target job role or search query.",
    )

    location: Optional[str] = Field(
        default=None,
        description="Preferred job location.",
    )

    experience_years: float = Field(
        default=0,
        ge=0,
        description="Candidate experience in years.",
    )

    minimum_salary_lpa: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum acceptable salary in LPA.",
    )

    preferred_work_modes: List[str] = Field(
        default_factory=list,
    )

    skills: List[str] = Field(
        default_factory=list,
    )

    target_industries: List[str] = Field(
        default_factory=list,
    )


# ==========================================================
# MATCH INTELLIGENCE
# ==========================================================

class MatchBreakdown(BaseModel):
    overall_score: float = 0.0

    role_fit: float = 0.0
    skill_fit: float = 0.0
    experience_fit: float = 0.0
    location_fit: float = 0.0
    salary_fit: float = 0.0
    career_goal_fit: float = 0.0

    semantic_score: Optional[float] = None
    deterministic_score: Optional[float] = None


# ==========================================================
# SOURCE-LEVEL PROVENANCE
# ==========================================================

class SourceRecord(BaseModel):
    """
    One source-specific representation of a canonical
    CareerPilot opportunity.

    This allows one canonical job to retain every source
    where it was discovered.
    """

    source: str

    source_job_id: str

    company: str

    title: str

    location: List[str] = Field(
        default_factory=list,
    )

    remote: bool = False

    employment_type: Optional[str] = None

    apply_url: str = ""

    source_url: str = ""

    salary_min_lpa: Optional[float] = None

    salary_max_lpa: Optional[float] = None

    salary_currency: str = "INR"

    salary_status: str = "UNDISCLOSED"

    salary_confidence: float = 0.0

    salary_evidence: Optional[str] = None

    posted_at: Optional[str] = None


# ==========================================================
# JOB RESULT
# ==========================================================

class JobResult(BaseModel):
    """
    Canonical CareerPilot opportunity.

    One result may represent the same opportunity found
    across multiple independent job sources.
    """

    source: str

    source_job_id: str

    # ------------------------------------------------------
    # Cross-source identity
    # ------------------------------------------------------

    sources: List[str] = Field(
        default_factory=list,
    )

    source_count: int = Field(
        default=1,
        ge=0,
    )

    source_records: List[SourceRecord] = Field(
        default_factory=list,
    )

    # ------------------------------------------------------
    # Core opportunity
    # ------------------------------------------------------

    company: str

    title: str

    location: List[str] = Field(
        default_factory=list,
    )

    remote: bool = False

    employment_type: Optional[str] = None

    # ------------------------------------------------------
    # Match intelligence
    # ------------------------------------------------------

    match_score: Optional[float] = None

    decision: Optional[str] = None

    confidence: Optional[float] = None

    strengths: List[str] = Field(
        default_factory=list,
    )

    skill_gaps: List[str] = Field(
        default_factory=list,
    )

    matched_skills: List[str] = Field(
        default_factory=list,
    )

    explanation: str = ""

    match_breakdown: Optional[
        MatchBreakdown
    ] = None

    # ------------------------------------------------------
    # Salary intelligence
    # ------------------------------------------------------

    salary_min_lpa: Optional[float] = None

    salary_max_lpa: Optional[float] = None

    salary_disclosed: bool = False

    salary_status: str = "UNDISCLOSED"

    salary_confidence: float = 0.0

    salary_evidence: Optional[str] = None

    # ------------------------------------------------------
    # Primary application link
    # ------------------------------------------------------

    apply_url: str = ""


# ==========================================================
# SALARY SUMMARY
# ==========================================================

class SalarySummary(BaseModel):
    minimum_salary_lpa: Optional[float] = None

    opportunities_found: int = 0

    salary_verified: int = 0

    salary_undisclosed: int = 0


# ==========================================================
# SOURCE SUMMARY
# ==========================================================

class SourceSummary(BaseModel):
    """
    Summary of configured and contributing job sources.
    """

    connected: int = 0

    contributing: int = 0

    sources: List[str] = Field(
        default_factory=list,
    )


# ==========================================================
# SEARCH RESPONSE
# ==========================================================

class JobSearchResponse(BaseModel):
    query: str

    location: Optional[str] = None

    result_count: int

    results: List[JobResult]

    salary_summary: SalarySummary

    source_summary: SourceSummary