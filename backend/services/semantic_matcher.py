from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements


@dataclass
class SemanticMatch:
    """
    Semantic similarity evidence between a candidate and a job.

    The matcher prefers local embedding similarity when the optional
    embedding stack is available. When the native dependency chain is
    unavailable, it falls back to a deterministic lexical similarity
    method rather than making the entire CareerPilot pipeline fail.

    The fallback is explicitly reported through `backend`.
    """

    profile_similarity: float
    skill_similarity: float
    requirement_similarity: float
    overall_similarity: float

    matched_concepts: List[str]
    reasoning_context: str


class SemanticMatcher:
    """
    CareerPilot semantic matching engine.

    Primary backend:
        sentence-transformers / all-MiniLM-L6-v2

    Resilient fallback:
        deterministic token Jaccard similarity

    The fallback exists for operational resilience only. It does not
    silently pretend to be an embedding model.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        self.model_name = model_name
        self.model = None

        self.backend = "lexical_fallback"
        self.backend_error = None

        try:
            from sentence_transformers import (
                SentenceTransformer,
            )

            self.model = SentenceTransformer(
                model_name
            )

            self.backend = "sentence_transformers"

        except Exception as exc:
            self.model = None
            self.backend = "lexical_fallback"
            self.backend_error = (
                f"{type(exc).__name__}: {exc}"
            )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def compare(
        self,
        candidate: CandidateProfile,
        job: Job,
        requirements: JobRequirements,
    ) -> SemanticMatch:

        candidate_profile_text = self._candidate_text(
            candidate
        )

        job_profile_text = self._job_text(
            job
        )

        candidate_skills_text = self._skills_text(
            candidate
        )

        job_requirements_text = (
            self._requirements_text(
                requirements
            )
        )

        profile_similarity = self._similarity(
            candidate_profile_text,
            job_profile_text,
        )

        skill_similarity = self._similarity(
            candidate_skills_text,
            job_requirements_text,
        )

        requirement_similarity = self._similarity(
            candidate_profile_text,
            job_requirements_text,
        )

        overall_similarity = round(
            (
                profile_similarity * 0.35
                + skill_similarity * 0.40
                + requirement_similarity * 0.25
            ),
            2,
        )

        matched_concepts = self._matched_concepts(
            candidate,
            requirements,
        )

        backend_label = (
            "embedding"
            if self.backend
            == "sentence_transformers"
            else "deterministic lexical fallback"
        )

        reasoning_context = (
            f"Semantic similarity is "
            f"{overall_similarity:.2f}/100. "
            f"The comparison considers the candidate profile, "
            f"skills, and extracted job requirements using the "
            f"{backend_label} backend."
        )

        if (
            self.backend
            != "sentence_transformers"
            and self.backend_error
        ):
            reasoning_context += (
                " The embedding backend was unavailable, "
                "so CareerPilot used its deterministic "
                "fallback to preserve workflow availability."
            )

        return SemanticMatch(
            profile_similarity=profile_similarity,
            skill_similarity=skill_similarity,
            requirement_similarity=(
                requirement_similarity
            ),
            overall_similarity=overall_similarity,
            matched_concepts=matched_concepts,
            reasoning_context=reasoning_context,
        )

    # ============================================================
    # SIMILARITY
    # ============================================================

    def _similarity(
        self,
        left: str,
        right: str,
    ) -> float:
        """
        Use embeddings when available.

        Otherwise use deterministic token Jaccard similarity.
        """

        left = str(left or "").strip()
        right = str(right or "").strip()

        if not left and not right:
            return 100.0

        if not left or not right:
            return 0.0

        if self.model is not None:
            try:
                embeddings = self.model.encode(
                    [
                        left,
                        right,
                    ],
                    normalize_embeddings=True,
                )

                similarity = float(
                    embeddings[0] @ embeddings[1]
                )

                score = (
                    (similarity + 1.0)
                    / 2.0
                ) * 100.0

                return round(
                    max(
                        0.0,
                        min(
                            100.0,
                            score,
                        ),
                    ),
                    2,
                )

            except Exception as exc:
                self.backend = (
                    "lexical_fallback"
                )

                self.backend_error = (
                    f"{type(exc).__name__}: {exc}"
                )

                self.model = None

        return self._lexical_similarity(
            left,
            right,
        )

    @classmethod
    def _lexical_similarity(
        cls,
        left: str,
        right: str,
    ) -> float:
        left_tokens = set(
            cls._tokenize(left)
        )

        right_tokens = set(
            cls._tokenize(right)
        )

        if not left_tokens and not right_tokens:
            return 100.0

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = (
            left_tokens.intersection(
                right_tokens
            )
        )

        union = (
            left_tokens.union(
                right_tokens
            )
        )

        score = (
            len(intersection)
            / len(union)
        ) * 100.0

        return round(
            max(
                0.0,
                min(
                    100.0,
                    score,
                ),
            ),
            2,
        )

    @staticmethod
    def _tokenize(
        text: str,
    ) -> Sequence[str]:
        return re.findall(
            r"[a-z0-9+#.-]+",
            str(text or "").casefold(),
        )

    # ============================================================
    # CANDIDATE REPRESENTATION
    # ============================================================

    @staticmethod
    def _candidate_text(
        candidate: CandidateProfile,
    ) -> str:

        return " ".join(
            [
                candidate.headline or "",
                " ".join(candidate.skills),
                " ".join(candidate.technical_skills),
                " ".join(candidate.soft_skills),
                " ".join(candidate.education),
                " ".join(candidate.certifications),
                " ".join(candidate.projects),
                " ".join(
                    candidate.career_goal.target_roles
                ),
                " ".join(
                    candidate.career_goal.target_industries
                ),
            ]
        )

    @staticmethod
    def _skills_text(
        candidate: CandidateProfile,
    ) -> str:

        return " ".join(
            candidate.skills
            + candidate.technical_skills
        )

    @staticmethod
    def _job_text(
        job: Job,
    ) -> str:

        return " ".join(
            [
                job.title,
                job.company,
                job.description,
                " ".join(job.skills),
                " ".join(job.location),
            ]
        )

    @staticmethod
    def _requirements_text(
        requirements: JobRequirements,
    ) -> str:

        return " ".join(
            [
                " ".join(
                    requirements.required_skills
                ),
                " ".join(
                    requirements.preferred_skills
                ),
                " ".join(
                    requirements.technologies
                ),
                " ".join(
                    requirements.responsibilities
                ),
                " ".join(
                    requirements.hard_requirements
                ),
                " ".join(
                    requirements.soft_requirements
                ),
                " ".join(
                    requirements.keywords
                ),
            ]
        )

    # ============================================================
    # CONCEPT MATCHING
    # ============================================================

    @staticmethod
    def _matched_concepts(
        candidate: CandidateProfile,
        requirements: JobRequirements,
    ) -> List[str]:

        candidate_values = {
            value.casefold()
            for value in (
                candidate.skills
                + candidate.technical_skills
            )
        }

        requirement_values = {
            value.casefold()
            for value in (
                requirements.required_skills
                + requirements.preferred_skills
                + requirements.technologies
            )
        }

        return sorted(
            candidate_values.intersection(
                requirement_values
            )
        )