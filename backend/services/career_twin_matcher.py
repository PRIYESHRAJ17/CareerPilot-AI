from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from backend.services.final_matcher import FinalMatch


@dataclass
class PersonalizedMatch:
    """
    Final opportunity match after combining the existing hybrid
    matcher with Career Twin intelligence.

    The original FinalMatch remains the objective base evidence.
    Career Twin personalization influences the ranking score without
    destroying the underlying deterministic/semantic evidence.
    """

    base_score: float
    career_twin_score: float
    personalized_score: float

    base_confidence: float
    career_twin_confidence: float
    personalized_confidence: float

    decision: str

    strengths: List[str]
    explanation: str


class CareerTwinMatcher:
    """
    Personalizes an existing FinalMatch using persistent Career Twin
    intelligence.

    Architecture:

        deterministic evidence
                  +
        semantic evidence
                  ↓
             FinalMatch
                  +
          Career Twin evidence
                  ↓
         PersonalizedMatch

    The existing matcher remains authoritative for base compatibility.
    Career Twin acts as an additional personalization layer.
    """

    CAREER_TWIN_WEIGHT = 0.15
    BASE_MATCH_WEIGHT = 0.85

    CONFIDENCE_TWIN_WEIGHT = 0.20
    CONFIDENCE_BASE_WEIGHT = 0.80

    def personalize(
        self,
        base_match: FinalMatch,
        career_twin_analysis: Dict[str, Any],
    ) -> PersonalizedMatch:

        base_score = self._clamp(
            base_match.final_score
        )

        twin_score = self._number(
            career_twin_analysis.get(
                "career_twin_match_score",
                50.0,
            ),
            default=50.0,
        )

        twin_score = self._clamp(
            twin_score
        )

        personalized_score = round(
            (
                base_score
                * self.BASE_MATCH_WEIGHT
                + twin_score
                * self.CAREER_TWIN_WEIGHT
            ),
            2,
        )

        base_confidence = self._clamp(
            base_match.confidence
        )

        twin_confidence = self._clamp(
            self._number(
                career_twin_analysis.get(
                    "career_twin_confidence",
                    50.0,
                ),
                default=50.0,
            )
        )

        personalized_confidence = round(
            (
                base_confidence
                * self.CONFIDENCE_BASE_WEIGHT
                + twin_confidence
                * self.CONFIDENCE_TWIN_WEIGHT
            ),
            2,
        )

        decision = self._decision(
            personalized_score
        )

        strengths = list(
            base_match.strengths
        )

        twin_matched = self._string_list(
            career_twin_analysis.get(
                "career_twin_matched_skills"
            )
        )

        twin_gap_matches = self._string_list(
            career_twin_analysis.get(
                "career_twin_gap_matches"
            )
        )

        if twin_matched:
            strengths.append(
                "Career Twin skill alignment"
            )

        if twin_gap_matches:
            strengths.append(
                "Career development alignment"
            )

        strengths = list(
            dict.fromkeys(
                strengths
            )
        )

        twin_reasoning = str(
            career_twin_analysis.get(
                "career_twin_reasoning",
                "",
            )
            or ""
        ).strip()

        explanation = (
            f"{base_match.explanation} "
            f"Career Twin personalization produced "
            f"a {twin_score}/100 Career Twin fit and "
            f"a final personalized opportunity score of "
            f"{personalized_score}/100."
        )

        if twin_reasoning:
            explanation += (
                f" {twin_reasoning}"
            )

        return PersonalizedMatch(
            base_score=base_score,
            career_twin_score=twin_score,
            personalized_score=personalized_score,
            base_confidence=base_confidence,
            career_twin_confidence=twin_confidence,
            personalized_confidence=(
                personalized_confidence
            ),
            decision=decision,
            strengths=strengths,
            explanation=explanation,
        )

    # ============================================================
    # DECISION
    # ============================================================

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

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _number(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _clamp(
        value: Any,
    ) -> float:

        try:
            numeric = float(value)
        except (
            TypeError,
            ValueError,
        ):
            numeric = 0.0

        return max(
            0.0,
            min(
                100.0,
                numeric,
            ),
        )

    @staticmethod
    def _string_list(
        value: Any,
    ) -> List[str]:

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):
            value = [value]

        if not isinstance(
            value,
            (list, tuple, set),
        ):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]