from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class CareerTwinProfile(BaseModel):
    name: str | None = None
    headline: str | None = None

    skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)

    education: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)

    experience: list[dict[str, Any]] = Field(
        default_factory=list
    )

    target_roles: list[str] = Field(
        default_factory=list
    )

    target_industries: list[str] = Field(
        default_factory=list
    )

    target_locations: list[str] = Field(
        default_factory=list
    )

    preferred_work_modes: list[str] = Field(
        default_factory=list
    )

    minimum_salary_lpa: float | None = None

    timeline_months: int | None = None


class CareerTwinDerived(BaseModel):
    strengths: list[str] = Field(
        default_factory=list
    )

    skill_gaps: list[str] = Field(
        default_factory=list
    )

    readiness_score: float = 0.0

    readiness_level: str = "EARLY_STAGE"

    career_directions: list[str] = Field(
        default_factory=list
    )


class CareerMemoryEvent(BaseModel):
    event_id: str

    event_type: str

    summary: str

    timestamp: str

    payload: dict[str, Any] = Field(
        default_factory=dict
    )


class CareerTwin(BaseModel):
    candidate_id: str

    version: int = 1

    profile: CareerTwinProfile = Field(
        default_factory=CareerTwinProfile
    )

    derived: CareerTwinDerived = Field(
        default_factory=CareerTwinDerived
    )

    memory: list[CareerMemoryEvent] = Field(
        default_factory=list
    )

    created_at: str = Field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )

    updated_at: str = Field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )