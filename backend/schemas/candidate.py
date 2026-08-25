from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CareerGoal:
    target_roles: List[str] = field(default_factory=list)
    target_industries: List[str] = field(default_factory=list)
    target_locations: List[str] = field(default_factory=list)

    minimum_salary_lpa: Optional[float] = None
    preferred_work_modes: List[str] = field(default_factory=list)

    target_timeline_months: Optional[int] = None


@dataclass
class CandidateProfile:
    candidate_id: str

    name: Optional[str] = None
    headline: Optional[str] = None

    skills: List[str] = field(default_factory=list)
    technical_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)

    years_of_experience: float = 0.0
    notice_period_days: Optional[int] = None

    education: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)

    career_goal: CareerGoal = field(default_factory=CareerGoal)

    preferred_locations: List[str] = field(default_factory=list)
    preferred_work_modes: List[str] = field(default_factory=list)

    metadata: dict = field(default_factory=dict)
