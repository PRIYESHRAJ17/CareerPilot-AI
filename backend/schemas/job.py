from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Salary:
    min_lpa: Optional[float] = None
    max_lpa: Optional[float] = None
    currency: str = "INR"


@dataclass
class Experience:
    min_years: Optional[float] = None
    max_years: Optional[float] = None


@dataclass
class Job:
    source: str
    source_job_id: str
    title: str
    company: str
    location: List[str] = field(default_factory=list)

    remote: bool = False
    employment_type: Optional[str] = None

    experience: Experience = field(default_factory=Experience)
    salary: Salary = field(default_factory=Salary)

    skills: List[str] = field(default_factory=list)
    description: str = ""

    apply_url: str = ""
    source_url: str = ""
    posted_at: Optional[str] = None

    metadata: dict = field(default_factory=dict)
