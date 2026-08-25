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
    deterministic_score: float
    semantic_score: float
    final_score: float

    decision: str
    confidence: float

    strengths: List[str]
    skill_gaps: List[str]

    explanation: str


class FinalMatchEngine:
    """
    Combines deterministic evidence and semantic evidence.

    Hard constraints stay deterministic.
    Semantic similarity enriches, but does not blindly override,
    objective evidence.
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

        deterministic: MatchBreakdown = (
            self.match_engine.score(
                candidate=candidate,
                job=job,
            )
        )

        semantic: SemanticMatch = (
            self.semantic_matcher.compare(
                candidate=candidate,
                job=job,
                requirements=requirements,
            )
        )

        final_score = round(
            (
                deterministic.overall_score
                * self.DETERMINISTIC_WEIGHT
                + semantic.overall_similarity
                * self.SEMANTIC_WEIGHT
            ),
            2,
        )

        decision = self._decision(
            final_score
        )

        confidence = self._confidence(
            deterministic,
            semantic,
        )

        strengths = self._strengths(
            deterministic,
            semantic,
        )

        skill_gaps = list(
            deterministic.missing_skills
        )

        explanation = self._explanation(
            deterministic,
            semantic,
            final_score,
            decision,
        )

        return FinalMatch(
            deterministic_score=deterministic.overall_score,
            semantic_score=semantic.overall_similarity,
            final_score=final_score,
            decision=decision,
            confidence=confidence,
            strengths=strengths,
            skill_gaps=skill_gaps,
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

        if deterministic.location_fit >= 90:
            strengths.append(
                "Strong location alignment"
            )

        if deterministic.salary_fit >= 90:
            strengths.append(
                "Salary target alignment"
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
            dict.fromkeys(strengths)
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
            f"evidence and {semantic.overall_similarity}/100 "
            f"semantic compatibility. "
            f"The recommended action is {decision}."
        )