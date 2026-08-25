from dataclasses import dataclass
from typing import List

from sentence_transformers import SentenceTransformer

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements


@dataclass
class SemanticMatch:
    """
    Semantic similarity evidence between a candidate and a job.
    """

    profile_similarity: float
    skill_similarity: float
    requirement_similarity: float
    overall_similarity: float

    matched_concepts: List[str]
    reasoning_context: str


class SemanticMatcher:
    """
    Local embedding-based semantic matcher.

    The embedding model provides semantic similarity.
    It does not make the final career decision.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.model = SentenceTransformer(model_name)

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

        job_requirements_text = self._requirements_text(
            requirements
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

        reasoning_context = (
            f"Semantic similarity is "
            f"{overall_similarity:.2f}/100. "
            f"The comparison considers the candidate profile, "
            f"skills, and extracted job requirements."
        )

        return SemanticMatch(
            profile_similarity=profile_similarity,
            skill_similarity=skill_similarity,
            requirement_similarity=requirement_similarity,
            overall_similarity=overall_similarity,
            matched_concepts=matched_concepts,
            reasoning_context=reasoning_context,
        )

    def _similarity(
        self,
        left: str,
        right: str,
    ) -> float:

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
            max(0.0, min(100.0, score)),
            2,
        )

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