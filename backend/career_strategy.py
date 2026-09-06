from dataclasses import dataclass
from typing import List

from backend.services.candidate_intelligence import CandidateIntelligence


@dataclass
class CareerStrategy:
    """
    Converts candidate intelligence into an actionable
    career strategy.
    """

    primary_role: str
    career_directions: List[str]
    priority_skills: List[str]
    improvement_areas: List[str]
    recommended_actions: List[str]
    strategy_summary: str


def generate_career_strategy(
    intelligence: CandidateIntelligence,
) -> CareerStrategy:
    """
    Generate a career strategy from CandidateIntelligence.
    """

    # ------------------------------------------------------
    # Primary role
    # ------------------------------------------------------

    if intelligence.target_roles:
        primary_role = intelligence.target_roles[0]
    else:
        primary_role = "AI / Backend Engineering"

    # ------------------------------------------------------
    # Career directions
    # ------------------------------------------------------

    career_directions = list(
        intelligence.career_direction
    )

    # ------------------------------------------------------
    # Priority skills
    # ------------------------------------------------------

    priority_skills = list(
        intelligence.normalized_skills
    )

    # ------------------------------------------------------
    # Improvement areas
    # ------------------------------------------------------

    improvement_areas = []

    if "certifications" in intelligence.missing_information:
        improvement_areas.append(
            "Certifications and professional credentials"
        )

    if "notice period" in intelligence.missing_information:
        improvement_areas.append(
            "Notice period and availability information"
        )

    if "AI / ML Engineering" in intelligence.career_direction:
        improvement_areas.append(
            "Production-grade AI/ML engineering"
        )

    if "Backend Engineering" in intelligence.career_direction:
        improvement_areas.append(
            "Scalable backend architecture and APIs"
        )

    if "Data Engineering / Analytics" in intelligence.career_direction:
        improvement_areas.append(
            "Data pipelines and analytics"
        )

    # Remove duplicates
    improvement_areas = list(
        dict.fromkeys(improvement_areas)
    )

    # ------------------------------------------------------
    # Recommended actions
    # ------------------------------------------------------

    recommended_actions = [
        (
            f"Target {primary_role} opportunities "
            "that match the candidate's strongest skills."
        ),
        (
            "Strengthen production-grade API, "
            "database and deployment skills."
        ),
        (
            "Build practical AI projects with "
            "measurable real-world outcomes."
        ),
        (
            "Practice system design and backend "
            "engineering fundamentals."
        ),
        (
            "Continuously evaluate skill gaps "
            "against target job requirements."
        ),
    ]

    # ------------------------------------------------------
    # Strategy summary
    # ------------------------------------------------------

    if priority_skills:
        skill_text = ", ".join(priority_skills)

        strategy_summary = (
            f"The candidate is currently positioned for "
            f"{primary_role}. The strongest technical "
            f"foundation is in {skill_text}. The next priority "
            f"is converting this foundation into stronger "
            f"production-ready experience, measurable project "
            f"outcomes and targeted career opportunities."
        )
    else:
        strategy_summary = (
            f"The candidate is currently positioned for "
            f"{primary_role}. The next priority is developing "
            f"role-relevant skills and practical experience."
        )

    return CareerStrategy(
        primary_role=primary_role,
        career_directions=career_directions,
        priority_skills=priority_skills,
        improvement_areas=improvement_areas,
        recommended_actions=recommended_actions,
        strategy_summary=strategy_summary,
    )