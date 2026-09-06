from dataclasses import dataclass, field
from typing import List, Dict

from backend.schemas.candidate import CandidateProfile


@dataclass
class CandidateIntelligence:
    """
    Derived intelligence about a candidate.

    This layer does not modify the original candidate profile.
    It converts raw profile data into useful career signals.
    """

    profile_completeness: float

    normalized_skills: List[str] = field(default_factory=list)
    skill_categories: Dict[str, List[str]] = field(
        default_factory=dict
    )

    strengths: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)

    career_direction: List[str] = field(default_factory=list)

    target_roles: List[str] = field(default_factory=list)
    target_industries: List[str] = field(default_factory=list)

    readiness_level: str = "EARLY_STAGE"
    readiness_score: float = 0.0

    recommendations: List[str] = field(default_factory=list)


class CandidateIntelligenceEngine:
    """
    Converts a CandidateProfile into higher-level
    career intelligence.

    This is intentionally deterministic in Week 3.
    LLM reasoning can be added later without replacing
    the underlying evidence.
    """

    SKILL_CATEGORIES = {
        "programming": {
            "python",
            "java",
            "c++",
            "c",
            "javascript",
            "typescript",
            "go",
            "rust",
        },
        "backend": {
            "fastapi",
            "django",
            "flask",
            "node.js",
            "node",
            "express",
            "rest",
            "rest api",
            "api",
        },
        "frontend": {
            "react",
            "next.js",
            "nextjs",
            "html",
            "css",
            "tailwind",
            "vue",
            "angular",
        },
        "ai_ml": {
            "machine learning",
            "deep learning",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "llm",
            "generative ai",
            "genai",
            "nlp",
            "artificial intelligence",
        },
        "data": {
            "sql",
            "mysql",
            "postgresql",
            "mongodb",
            "pandas",
            "numpy",
            "data analysis",
        },
        "devops": {
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "ci/cd",
            "linux",
        },
        "engineering": {
            "git",
            "github",
            "testing",
            "unit testing",
            "system design",
            "data structures",
            "algorithms",
        },
    }

    def analyze(
        self,
        candidate: CandidateProfile,
    ) -> CandidateIntelligence:

        normalized_skills = self._normalize_skills(candidate)

        skill_categories = self._categorize_skills(
            normalized_skills
        )

        completeness = self._profile_completeness(
            candidate
        )

        strengths = self._identify_strengths(
            candidate,
            skill_categories,
        )

        missing_information = (
            self._identify_missing_information(candidate)
        )

        career_direction = self._infer_career_direction(
            candidate,
            skill_categories,
        )

        readiness_score = self._readiness_score(
            candidate,
            completeness,
            skill_categories,
        )

        readiness_level = self._readiness_level(
            readiness_score
        )

        recommendations = (
            self._generate_recommendations(
                candidate,
                skill_categories,
                missing_information,
                readiness_level,
            )
        )

        return CandidateIntelligence(
            profile_completeness=round(
                completeness,
                2,
            ),
            normalized_skills=normalized_skills,
            skill_categories=skill_categories,
            strengths=strengths,
            missing_information=missing_information,
            career_direction=career_direction,
            target_roles=list(
                candidate.career_goal.target_roles
            ),
            target_industries=list(
                candidate.career_goal.target_industries
            ),
            readiness_level=readiness_level,
            readiness_score=round(
                readiness_score,
                2,
            ),
            recommendations=recommendations,
        )

    # ------------------------------------------------------
    # Skill normalization
    # ------------------------------------------------------

    @staticmethod
    def _normalize_skills(
        candidate: CandidateProfile,
    ) -> List[str]:

        skills = (
            candidate.skills
            + candidate.technical_skills
        )

        normalized = {
            skill.casefold().strip()
            for skill in skills
            if skill and skill.strip()
        }

        return sorted(normalized)

    # ------------------------------------------------------
    # Skill categorization
    # ------------------------------------------------------

    def _categorize_skills(
        self,
        skills: List[str],
    ) -> Dict[str, List[str]]:

        categories = {}

        for category, known_skills in (
            self.SKILL_CATEGORIES.items()
        ):
            matches = sorted(
                skill
                for skill in skills
                if skill in known_skills
            )

            if matches:
                categories[category] = matches

        return categories

    # ------------------------------------------------------
    # Profile completeness
    # ------------------------------------------------------

    @staticmethod
    def _profile_completeness(
        candidate: CandidateProfile,
    ) -> float:

        checks = [
            bool(candidate.skills),
            bool(candidate.technical_skills),
            bool(candidate.education),
            bool(candidate.projects),
            bool(candidate.career_goal.target_roles),
            bool(candidate.preferred_locations),
            bool(candidate.preferred_work_modes),
        ]

        completed = sum(checks)

        return (
            completed / len(checks)
        ) * 100

    # ------------------------------------------------------
    # Strength detection
    # ------------------------------------------------------

    @staticmethod
    def _identify_strengths(
        candidate: CandidateProfile,
        categories: Dict[str, List[str]],
    ) -> List[str]:

        strengths = []

        if categories.get("programming"):
            strengths.append(
                "Programming foundation"
            )

        if categories.get("backend"):
            strengths.append(
                "Backend development"
            )

        if categories.get("frontend"):
            strengths.append(
                "Frontend development"
            )

        if categories.get("ai_ml"):
            strengths.append(
                "AI/ML capability"
            )

        if categories.get("data"):
            strengths.append(
                "Data and database capability"
            )

        if categories.get("devops"):
            strengths.append(
                "Deployment and infrastructure exposure"
            )

        if candidate.projects:
            strengths.append(
                "Hands-on project experience"
            )

        return strengths

    # ------------------------------------------------------
    # Missing information
    # ------------------------------------------------------

    @staticmethod
    def _identify_missing_information(
        candidate: CandidateProfile,
    ) -> List[str]:

        missing = []

        if not candidate.education:
            missing.append("education")

        if not candidate.projects:
            missing.append("projects")

        if not candidate.certifications:
            missing.append("certifications")

        if candidate.notice_period_days is None:
            missing.append("notice period")

        if not candidate.career_goal.target_roles:
            missing.append("target roles")

        if not candidate.preferred_locations:
            missing.append("preferred locations")

        return missing

    # ------------------------------------------------------
    # Career direction
    # ------------------------------------------------------

    @staticmethod
    def _infer_career_direction(
        candidate: CandidateProfile,
        categories: Dict[str, List[str]],
    ) -> List[str]:

        directions = []

        roles = [
            role.casefold()
            for role in candidate.career_goal.target_roles
        ]

        role_text = " ".join(roles)

        if (
            "ai" in role_text
            or "machine learning" in role_text
            or "ml" in role_text
        ):
            directions.append("AI / ML Engineering")

        if (
            "backend" in role_text
            or categories.get("backend")
        ):
            directions.append("Backend Engineering")

        if (
            "frontend" in role_text
            or categories.get("frontend")
        ):
            directions.append("Frontend Engineering")

        if (
            "data" in role_text
            or categories.get("data")
        ):
            directions.append("Data Engineering / Analytics")

        if not directions:
            directions.append(
                "General Software Engineering"
            )

        return directions

    # ------------------------------------------------------
    # Readiness
    # ------------------------------------------------------

    @staticmethod
    def _readiness_score(
        candidate: CandidateProfile,
        completeness: float,
        categories: Dict[str, List[str]],
    ) -> float:

        score = completeness * 0.40

        skill_count = len(
            candidate.skills
            + candidate.technical_skills
        )

        score += min(
            skill_count * 5,
            25,
        )

        if candidate.projects:
            score += 15

        if categories:
            score += min(
                len(categories) * 3,
                15,
            )

        if candidate.career_goal.target_roles:
            score += 5

        return min(score, 100)

    @staticmethod
    def _readiness_level(
        score: float,
    ) -> str:

        if score >= 80:
            return "JOB_READY"

        if score >= 60:
            return "NEAR_READY"

        if score >= 40:
            return "DEVELOPING"

        return "EARLY_STAGE"

    # ------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------

    @staticmethod
    def _generate_recommendations(
        candidate: CandidateProfile,
        categories: Dict[str, List[str]],
        missing_information: List[str],
        readiness_level: str,
    ) -> List[str]:

        recommendations = []

        if "backend" in categories:
            recommendations.append(
                "Strengthen production backend skills "
                "with APIs, databases and deployment."
            )

        if "ai_ml" in categories:
            recommendations.append(
                "Build practical AI projects and "
                "demonstrate measurable outcomes."
            )

        if not candidate.projects:
            recommendations.append(
                "Add at least one strong production-style "
                "project to the candidate profile."
            )

        if "projects" in missing_information:
            recommendations.append(
                "Document projects with technologies, "
                "responsibilities and measurable results."
            )

        if readiness_level in {
            "EARLY_STAGE",
            "DEVELOPING",
        }:
            recommendations.append(
                "Prioritize high-impact skill development "
                "before targeting highly competitive roles."
            )

        return recommendations