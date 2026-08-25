from typing import List, Optional

from pydantic import BaseModel, Field


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


class JobResult(BaseModel):
    source: str
    source_job_id: str

    company: str
    title: str
    location: List[str]

    remote: bool
    employment_type: Optional[str]

    match_score: Optional[float] = None
    decision: Optional[str] = None
    confidence: Optional[float] = None

    strengths: List[str] = Field(
        default_factory=list,
    )

    skill_gaps: List[str] = Field(
        default_factory=list,
    )

    apply_url: str = ""