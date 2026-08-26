from dataclasses import dataclass
from typing import List

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements

from backend.services.match_engine import (
    MatchBreakdown,
    MatchEngine,
)

from backend.services.semantic_matcher import (
    SemanticMatch,
    SemanticMatcher,
)


@dataclass
class FinalMatch:
    """
    Complete CareerPilot match result.

    Contains:
        - deterministic evidence
        - semantic evidence
        - final score
        - decision
        - confidence
        - detailed score breakdown
        - matched skills
        - skill gaps
        - explanation
    """

    deterministic_score: float
    semantic_score: float
    final_score: float

    decision: str
    confidence: float

    # Detailed deterministic dimensions.
    role_fit: float
    skill_fit: float
    experience_fit: float
    location_fit: float
    salary_fit: float
    career_goal_fit: float

    # Skills.
    matched_skills: List[str]
    skill_gaps: List[str]

    # Explainability.
    strengths: List[str]
    explanation: str


class FinalMatchEngine:
    """
    Combines deterministic and semantic evidence.

    Deterministic evidence remains the objective foundation.
    Semantic similarity enriches the result without blindly
    overriding hard evidence.
    """

    DETERMINISTIC_WEIGHT = 0.60
    SEMANTIC_WEIGHT = 0.40

    def __init__(self) -> None:
        self.match_engine = MatchEngine()
        self.semantic_matcher = SemanticMatcher()

    def evaluate(
        self,
        candidate: CandidateProfile,
        job: Job,
        requirements: JobRequirements,
    ) -> FinalMatch:

        # --------------------------------------------------
        # 1. Deterministic evidence
        # --------------------------------------------------

        deterministic: MatchBreakdown = (
            self.match_engine.score(
                candidate=candidate,
                job=job,
            )
        )

        # --------------------------------------------------
        # 2. Semantic evidence
        # --------------------------------------------------

        semantic: SemanticMatch = (
            self.semantic_matcher.compare(
                candidate=candidate,
                job=job,
                requirements=requirements,
            )
        )

        # --------------------------------------------------
        # 3. Final hybrid score
        # --------------------------------------------------

        final_score = round(
            (
                deterministic.overall_score
                * self.DETERMINISTIC_WEIGHT
                + semantic.overall_similarity
                * self.SEMANTIC_WEIGHT
            ),
            2,
        )

        # --------------------------------------------------
        # 4. Decision
        # --------------------------------------------------

        decision = self._decision(
            final_score
        )

        # --------------------------------------------------
        # 5. Confidence
        # --------------------------------------------------

        confidence = self._confidence(
            deterministic,
            semantic,
        )

        # --------------------------------------------------
        # 6. Strengths
        # --------------------------------------------------

        strengths = self._strengths(
            deterministic,
            semantic,
        )

        # --------------------------------------------------
        # 7. Skill evidence
        # --------------------------------------------------

        matched_skills = list(
            deterministic.matched_skills
        )

        skill_gaps = list(
            deterministic.missing_skills
        )

        # --------------------------------------------------
        # 8. Explanation
        # --------------------------------------------------

        explanation = self._explanation(
            deterministic=deterministic,
            semantic=semantic,
            final_score=final_score,
            decision=decision,
        )

        # --------------------------------------------------
        # 9. Complete result
        # --------------------------------------------------

        return FinalMatch(
            deterministic_score=(
                deterministic.overall_score
            ),

            semantic_score=(
                semantic.overall_similarity
            ),

            final_score=final_score,

            decision=decision,

            confidence=confidence,

            role_fit=(
                deterministic.role_fit
            ),

            skill_fit=(
                deterministic.skill_fit
            ),

            experience_fit=(
                deterministic.experience_fit
            ),

            location_fit=(
                deterministic.location_fit
            ),

            salary_fit=(
                deterministic.salary_fit
            ),

            career_goal_fit=(
                deterministic.career_goal_fit
            ),

            matched_skills=matched_skills,

            skill_gaps=skill_gaps,

            strengths=strengths,

            explanation=explanation,
        )

    @staticmethod
    def _decision(
        score: float,
    ) -> str:

        if score >= 85:
            return "APPLY_NOW"

        if score >= 70:
            return "GOOD_MATCH"

        if score >= 55:
            return "STRETCH"

        return "LOW_PRIORITY"

    @staticmethod
    def _confidence(
        deterministic: MatchBreakdown,
        semantic: SemanticMatch,
    ) -> float:

        agreement = (
            100
            - abs(
                deterministic.overall_score
                - semantic.overall_similarity
            )
        )

        return round(
            max(
                50.0,
                min(
                    95.0,
                    agreement,
                ),
            ),
            2,
        )

    @staticmethod
    def _strengths(
        deterministic: MatchBreakdown,
        semantic: SemanticMatch,
    ) -> List[str]:

        strengths: List[str] = []

        if deterministic.role_fit >= 85:
            strengths.append(
                "Strong role alignment"
            )

        if deterministic.skill_fit >= 75:
            strengths.append(
                "Strong skill alignment"
            )

        if deterministic.experience_fit >= 90:
            strengths.append(
                "Strong experience alignment"
            )

        if deterministic.location_fit >= 90:
            strengths.append(
                "Strong location alignment"
            )

        if deterministic.salary_fit >= 90:
            strengths.append(
                "Salary target alignment"
            )

        if deterministic.career_goal_fit >= 90:
            strengths.append(
                "Strong career goal alignment"
            )

        if semantic.skill_similarity >= 85:
            strengths.append(
                "Strong semantic skill compatibility"
            )

        if semantic.requirement_similarity >= 85:
            strengths.append(
                "Strong requirement compatibility"
            )

        return list(
            dict.fromkeys(
                strengths
            )
        )

    @staticmethod
    def _explanation(
        deterministic: MatchBreakdown,
        semantic: SemanticMatch,
        final_score: float,
        decision: str,
    ) -> str:

        return (
            f"CareerPilot calculated a final compatibility "
            f"score of {final_score}/100 using "
            f"{deterministic.overall_score}/100 deterministic "
            f"evidence and "
            f"{semantic.overall_similarity}/100 semantic "
            f"compatibility. "
            f"Role fit was "
            f"{deterministic.role_fit}/100, "
            f"skill fit was "
            f"{deterministic.skill_fit}/100, "
            f"experience fit was "
            f"{deterministic.experience_fit}/100, "
            f"location fit was "
            f"{deterministic.location_fit}/100, "
            f"salary fit was "
            f"{deterministic.salary_fit}/100, "
            f"and career-goal fit was "
            f"{deterministic.career_goal_fit}/100. "
            f"The recommended action is "
            f"{decision}."
        )