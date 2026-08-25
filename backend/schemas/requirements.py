from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobRequirements:
    """
    Structured representation of requirements extracted from a
    job description.
    """

    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)

    years_experience_min: Optional[float] = None
    years_experience_max: Optional[float] = None

    education_requirements: List[str] = field(
        default_factory=list
    )

    responsibilities: List[str] = field(
        default_factory=list
    )

    seniority: Optional[str] = None

    hard_requirements: List[str] = field(
        default_factory=list
    )

    soft_requirements: List[str] = field(
        default_factory=list
    )

    technologies: List[str] = field(
        default_factory=list
    )

    domain: Optional[str] = None

    keywords: List[str] = field(
        default_factory=list
    )