from dataclasses import dataclass
from typing import List

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.services.match_engine import MatchBreakdown


@dataclass
class CareerRecommendation:
    """
    Actionable recommendation generated from objective
    candidate-vs-job evidence.
    """

    decision: str
    confidence: float
    summary: str

    strengths: List[str]
    gaps: List[str]
    reasons: List[str]


class CareerReasoningEngine:
    """
    Converts the deterministic match breakdown into
    an actionable recommendation.

    Important:
    - It does not invent the match score.
    - It does not override objective evidence.
    - LLM-based semantic reasoning will be added later.
    """

    def analyze(
        self,
        candidate: CandidateProfile,
        job: Job,
        match: MatchBreakdown,
    ) -> CareerRecommendation:

        strengths: List[str] = []
        gaps: List[str] = []
        reasons: List[str] = []

        # -------------------------
        # Role alignment
        # -------------------------

        if match.role_fit >= 90:
            strengths.append(
                "Strong role alignment"
            )
        elif match.role_fit >= 70:
            strengths.append(
                "Reasonable role alignment"
            )
        else:
            gaps.append(
                "Weak role alignment"
            )

        # -------------------------
        # Skill alignment
        # -------------------------

        if match.skill_fit >= 85:
            strengths.append(
                "Strong skill alignment"
            )
        elif match.skill_fit >= 60:
            strengths.append(
                "Moderate skill alignment"
            )
        else:
            gaps.append(
                "Significant skill gaps"
            )

        # -------------------------
        # Experience
        # -------------------------

        if match.experience_fit >= 85:
            strengths.append(
                "Experience level is compatible"
            )
        elif match.experience_fit < 60:
            gaps.append(
                "Experience mismatch"
            )

        # -------------------------
        # Location
        # -------------------------

        if match.location_fit >= 90:
            strengths.append(
                "Location preference matches"
            )
        elif match.location_fit < 50:
            gaps.append(
                "Location preference does not match"
            )

        # -------------------------
        # Salary
        # -------------------------

        if match.salary_fit >= 90:
            strengths.append(
                "Salary target appears compatible"
            )
        elif match.salary_fit < 60:
            gaps.append(
                "Salary may not meet the target"
            )

        # -------------------------
        # Explicit missing skills
        # -------------------------

        for skill in match.missing_skills:
            gaps.append(
                f"Missing skill: {skill}"
            )

        # -------------------------
        # Decision
        # -------------------------

        score = match.overall_score

        if score >= 85:
            decision = "APPLY_NOW"
            confidence = min(95.0, score + 5)

        elif score >= 70:
            decision = "GOOD_MATCH"
            confidence = score

        elif score >= 55:
            decision = "STRETCH"
            confidence = score

        else:
            decision = "LOW_PRIORITY"
            confidence = score

        # -------------------------
        # Human-readable summary
        # -------------------------

        if decision == "APPLY_NOW":
            summary = (
                "This opportunity is strongly aligned with "
                "the candidate profile and is worth applying to."
            )

        elif decision == "GOOD_MATCH":
            summary = (
                "This opportunity is a good match with some "
                "areas that should be reviewed before applying."
            )

        elif decision == "STRETCH":
            summary = (
                "This opportunity is achievable but has "
                "meaningful gaps that may reduce competitiveness."
            )

        else:
            summary = (
                "This opportunity currently has limited "
                "alignment with the candidate profile."
            )

        # -------------------------
        # Reason list
        # -------------------------

        reasons.extend(strengths[:3])

        if gaps:
            reasons.append(
                f"{len(gaps)} improvement or gap signal(s) identified."
            )

        return CareerRecommendation(
            decision=decision,
            confidence=round(confidence, 2),
            summary=summary,
            strengths=strengths,
            gaps=gaps,
            reasons=reasons,
        )