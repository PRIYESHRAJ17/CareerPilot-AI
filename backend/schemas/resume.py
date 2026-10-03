from typing import List, Optional

from pydantic import BaseModel, Field


# ==========================================================
# CONTACT INFORMATION
# ==========================================================

class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


# ==========================================================
# EXPERIENCE
# ==========================================================

class ResumeExperience(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    description: str = ""

    achievements: List[str] = Field(
        default_factory=list
    )

    technologies: List[str] = Field(
        default_factory=list
    )


# ==========================================================
# EDUCATION
# ==========================================================

class ResumeEducation(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    field_of_study: Optional[str] = None

    grade: Optional[str] = None


# ==========================================================
# PROJECTS
# ==========================================================

class ResumeProject(BaseModel):
    name: Optional[str] = None

    description: str = ""

    technologies: List[str] = Field(
        default_factory=list
    )

    url: Optional[str] = None

    achievements: List[str] = Field(
        default_factory=list
    )


# ==========================================================
# CERTIFICATIONS
# ==========================================================

class ResumeCertification(BaseModel):
    name: str

    issuer: Optional[str] = None

    issue_date: Optional[str] = None

    expiry_date: Optional[str] = None

    credential_id: Optional[str] = None

    credential_url: Optional[str] = None


# ==========================================================
# ACHIEVEMENTS
# ==========================================================

class ResumeAchievement(BaseModel):
    title: str

    description: str = ""

    date: Optional[str] = None


# ==========================================================
# COMPLETE STRUCTURED RESUME
# ==========================================================

class StructuredResume(BaseModel):
    """
    Canonical structured representation of a resume.

    This becomes the shared resume data model for:

    - Resume Analyzer
    - ATS Analyzer
    - Job Matching
    - Resume Rewriter
    - Career Intelligence
    - Future Resume Builder
    """

    contact: ResumeContact = Field(
        default_factory=ResumeContact
    )

    headline: Optional[str] = None

    summary: str = ""

    experience: List[ResumeExperience] = Field(
        default_factory=list
    )

    education: List[ResumeEducation] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    technical_skills: List[str] = Field(
        default_factory=list
    )

    soft_skills: List[str] = Field(
        default_factory=list
    )

    projects: List[ResumeProject] = Field(
        default_factory=list
    )

    certifications: List[ResumeCertification] = Field(
        default_factory=list
    )

    achievements: List[ResumeAchievement] = Field(
        default_factory=list
    )

    languages: List[str] = Field(
        default_factory=list
    )

    raw_text: str = ""

    page_count: int = 0