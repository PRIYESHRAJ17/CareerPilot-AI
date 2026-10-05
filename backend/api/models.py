from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ==========================================================
# SEARCH REQUEST
# ==========================================================

class JobSearchRequest(BaseModel):
    role: str = Field(
        ...,
        min_length=1,
    )

    location: Optional[str] = None

    experience_years: float = Field(
        default=0,
        ge=0,
    )

    minimum_salary_lpa: Optional[float] = Field(
        default=None,
        ge=0,
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

    @field_validator(
        "preferred_work_modes",
        "skills",
        "target_industries",
    )
    @classmethod
    def normalize_lists(
        cls,
        values: List[str],
    ) -> List[str]:
        cleaned: List[str] = []
        seen: set[str] = set()

        for value in values:
            item = value.strip()

            if not item:
                continue

            key = item.casefold()

            if key in seen:
                continue

            seen.add(key)
            cleaned.append(item)

        return cleaned


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

    @field_validator("posted_at", mode="before")
    @classmethod
    def normalize_posted_at(cls, value):
        """
        Normalize provider-specific posted_at formats into
        an ISO-8601 string.

        Supported inputs include:
        - ISO/date strings
        - datetime objects
        - Unix timestamps in seconds
        - Unix timestamps in milliseconds
        - numeric timestamp strings
        """

        if value is None:
            return None

        # Already a datetime object
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)

            return value.isoformat()

        # Numeric Unix timestamp
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                timestamp = float(value)

                # Millisecond timestamps are much larger than
                # normal Unix-second timestamps.
                if abs(timestamp) >= 10_000_000_000:
                    timestamp /= 1000.0

                return datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc,
                ).isoformat()

            except (OverflowError, OSError, ValueError):
                return str(value)

        # Numeric timestamp represented as a string
        if isinstance(value, str):
            cleaned = value.strip()

            if not cleaned:
                return None

            try:
                numeric_value = float(cleaned)

                if abs(numeric_value) >= 10_000_000_000:
                    numeric_value /= 1000.0

                return datetime.fromtimestamp(
                    numeric_value,
                    tz=timezone.utc,
                ).isoformat()

            except (ValueError, OverflowError, OSError):
                return cleaned

        # Final defensive fallback
        return str(value)


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
# CAREER INTELLIGENCE
# ==========================================================

class CandidateIntelligenceResponse(BaseModel):
    """
    Structured intelligence about the candidate generated
    from the candidate profile.
    """

    profile_completeness: float = 0.0

    normalized_skills: List[str] = Field(
        default_factory=list,
    )

    skill_categories: dict[str, List[str]] = Field(
        default_factory=dict,
    )

    strengths: List[str] = Field(
        default_factory=list,
    )

    missing_information: List[str] = Field(
        default_factory=list,
    )

    career_direction: List[str] = Field(
        default_factory=list,
    )

    target_roles: List[str] = Field(
        default_factory=list,
    )

    target_industries: List[str] = Field(
        default_factory=list,
    )

    readiness_level: str = "EARLY_STAGE"

    readiness_score: float = 0.0

    recommendations: List[str] = Field(
        default_factory=list,
    )


# ==========================================================
# CAREER STRATEGY
# ==========================================================

class CareerStrategyResponse(BaseModel):
    """
    Personalized career strategy derived from candidate
    intelligence.
    """

    primary_role: str

    career_directions: List[str] = Field(
        default_factory=list,
    )

    priority_skills: List[str] = Field(
        default_factory=list,
    )

    improvement_areas: List[str] = Field(
        default_factory=list,
    )

    recommended_actions: List[str] = Field(
        default_factory=list,
    )

    strategy_summary: str = ""


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

    # ------------------------------------------------------
    # Career Intelligence
    # ------------------------------------------------------

    candidate_intelligence: CandidateIntelligenceResponse

    # ------------------------------------------------------
    # Career Strategy
    # ------------------------------------------------------

    career_strategy: CareerStrategyResponse