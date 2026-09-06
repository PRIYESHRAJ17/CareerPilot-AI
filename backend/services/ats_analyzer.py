from dataclasses import dataclass, field
import re
from typing import Dict, List, Set

from backend.schemas.resume import StructuredResume


@dataclass
class ATSRequirement:
    """One requirement extracted from a target job description."""

    text: str
    category: str
    normalized: str
    importance: str = "preferred"


@dataclass
class ATSMatch:
    """Evidence showing how a job requirement is supported."""

    requirement: str
    category: str
    status: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class ATSAnalysisResult:
    """Structured deterministic ATS analysis."""

    overall_score: float
    keyword_coverage_score: float
    skill_match_score: float
    experience_alignment_score: float
    education_alignment_score: float
    section_coverage_score: float

    requirements: List[ATSRequirement]
    matches: List[ATSMatch]

    matched_keywords: List[str]
    missing_keywords: List[str]
    weak_keywords: List[str]

    supported_requirements: List[str]
    mentioned_only_requirements: List[str]
    missing_requirements: List[str]

    strengths: List[str]
    issues: List[str]
    recommendations: List[str]

    keyword_stuffing_risk: bool
    unsupported_claim_risk: bool

    summary: str

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "keyword_coverage_score": self.keyword_coverage_score,
            "skill_match_score": self.skill_match_score,
            "experience_alignment_score": self.experience_alignment_score,
            "education_alignment_score": self.education_alignment_score,
            "section_coverage_score": self.section_coverage_score,
            "requirements": [
                {
                    "text": item.text,
                    "category": item.category,
                    "normalized": item.normalized,
                    "importance": item.importance,
                }
                for item in self.requirements
            ],
            "matches": [
                {
                    "requirement": item.requirement,
                    "category": item.category,
                    "status": item.status,
                    "evidence": item.evidence,
                    "confidence": item.confidence,
                }
                for item in self.matches
            ],
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "weak_keywords": self.weak_keywords,
            "supported_requirements": self.supported_requirements,
            "mentioned_only_requirements": self.mentioned_only_requirements,
            "missing_requirements": self.missing_requirements,
            "strengths": self.strengths,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "keyword_stuffing_risk": self.keyword_stuffing_risk,
            "unsupported_claim_risk": self.unsupported_claim_risk,
            "summary": self.summary,
        }


class ATSAnalyzer:
    """
    Deterministic ATS analyzer.

    Input:
        StructuredResume + target job description

    Output:
        Evidence-based ATS analysis.

    Design principle:
        The analyzer distinguishes between:

            SUPPORTED
            MENTIONED_ONLY
            MISSING

        It never tells a candidate to claim experience they
        do not have.
    """

    COMMON_SKILLS = {
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c",
        "c#",
        "go",
        "rust",
        "sql",
        "html",
        "css",
        "react",
        "next.js",
        "node.js",
        "fastapi",
        "django",
        "flask",
        "spring",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "git",
        "github",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "langchain",
        "langgraph",
        "llm",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "rest api",
        "restful api",
        "microservices",
        "graphql",
        "ci/cd",
        "linux",
        "terraform",
        "jenkins",
        "spark",
        "pandas",
        "numpy",
    }

    DEGREE_TERMS = {
        "bachelor",
        "b.tech",
        "btech",
        "b.e",
        "be",
        "master",
        "m.tech",
        "mtech",
        "m.e",
        "me",
        "mba",
        "phd",
        "doctorate",
        "degree",
        "diploma",
    }

    EXPERIENCE_TERMS = {
        "experience",
        "years",
        "senior",
        "junior",
        "lead",
        "intern",
        "internship",
        "professional",
    }

    SECTION_TERMS = {
        "experience": {
            "experience",
            "work experience",
            "professional experience",
            "employment",
        },
        "education": {
            "education",
            "degree",
            "bachelor",
            "master",
            "phd",
        },
        "skills": {
            "skills",
            "technical skills",
            "technologies",
            "tools",
            "frameworks",
        },
        "projects": {
            "projects",
            "project experience",
        },
        "certifications": {
            "certification",
            "certifications",
        },
    }

    ACTION_WORDS = {
        "built",
        "developed",
        "designed",
        "implemented",
        "engineered",
        "created",
        "deployed",
        "automated",
        "optimized",
        "improved",
        "integrated",
        "led",
        "managed",
        "architected",
        "migrated",
        "analyzed",
        "delivered",
    }

    WEAK_TERMS = {
        "familiar with",
        "basic knowledge",
        "exposure to",
        "knowledge of",
        "understanding of",
    }

    STOPWORDS = {
        "and",
        "the",
        "with",
        "for",
        "from",
        "this",
        "that",
        "will",
        "your",
        "you",
        "our",
        "are",
        "have",
        "has",
        "into",
        "using",
        "use",
        "work",
        "role",
        "job",
        "team",
        "years",
        "year",
        "must",
        "should",
        "strong",
        "good",
        "ability",
        "skills",
        "skill",
        "experience",
        "required",
        "preferred",
        "including",
        "plus",
        "etc",
    }

    def analyze(
        self,
        resume: StructuredResume,
        job_description: str,
    ) -> ATSAnalysisResult:

        if not job_description or not job_description.strip():
            raise ValueError(
                "Job description cannot be empty."
            )

        normalized_job = self._normalize_text(
            job_description
        )

        requirements = self._extract_requirements(
            job_description
        )

        resume_text = self._build_resume_text(
            resume
        )

        matches = []

        for requirement in requirements:
            matches.append(
                self._match_requirement(
                    requirement,
                    resume,
                    resume_text,
                )
            )

        supported = [
            match.requirement
            for match in matches
            if match.status == "SUPPORTED"
        ]

        mentioned_only = [
            match.requirement
            for match in matches
            if match.status == "MENTIONED_ONLY"
        ]

        missing = [
            match.requirement
            for match in matches
            if match.status == "MISSING"
        ]

        matched_keywords = sorted(
            {
                match.requirement
                for match in matches
                if match.status
                in {
                    "SUPPORTED",
                    "MENTIONED_ONLY",
                }
            },
            key=str.lower,
        )

        missing_keywords = sorted(
            set(missing),
            key=str.lower,
        )

        weak_keywords = sorted(
            {
                match.requirement
                for match in matches
                if match.status == "MENTIONED_ONLY"
            },
            key=str.lower,
        )

        keyword_coverage_score = (
            self._calculate_keyword_coverage(
                matches
            )
        )

        skill_match_score = (
            self._calculate_category_score(
                matches,
                "skill",
            )
        )

        experience_alignment_score = (
            self._calculate_experience_alignment(
                resume,
                job_description,
                matches,
            )
        )

        education_alignment_score = (
            self._calculate_education_alignment(
                resume,
                matches,
            )
        )

        section_coverage_score = (
            self._calculate_section_coverage(
                resume
            )
        )

        overall_score = (
            keyword_coverage_score * 0.35
            + skill_match_score * 0.30
            + experience_alignment_score * 0.15
            + education_alignment_score * 0.10
            + section_coverage_score * 0.10
        )

        keyword_stuffing_risk = (
            self._detect_keyword_stuffing(
                resume,
                matches,
            )
        )

        unsupported_claim_risk = (
            self._detect_unsupported_claim_risk(
                matches
            )
        )

        strengths = self._generate_strengths(
            matches,
            section_coverage_score,
        )

        issues = self._generate_issues(
            matches,
            keyword_stuffing_risk,
            unsupported_claim_risk,
        )

        recommendations = self._generate_recommendations(
            matches,
            resume,
            keyword_stuffing_risk,
        )

        summary = self._generate_summary(
            overall_score,
            supported,
            mentioned_only,
            missing,
        )

        return ATSAnalysisResult(
            overall_score=round(
                overall_score,
                1,
            ),
            keyword_coverage_score=round(
                keyword_coverage_score,
                1,
            ),
            skill_match_score=round(
                skill_match_score,
                1,
            ),
            experience_alignment_score=round(
                experience_alignment_score,
                1,
            ),
            education_alignment_score=round(
                education_alignment_score,
                1,
            ),
            section_coverage_score=round(
                section_coverage_score,
                1,
            ),
            requirements=requirements,
            matches=matches,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            weak_keywords=weak_keywords,
            supported_requirements=supported,
            mentioned_only_requirements=mentioned_only,
            missing_requirements=missing,
            strengths=self._deduplicate(
                strengths
            ),
            issues=self._deduplicate(
                issues
            ),
            recommendations=self._deduplicate(
                recommendations
            ),
            keyword_stuffing_risk=keyword_stuffing_risk,
            unsupported_claim_risk=unsupported_claim_risk,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # REQUIREMENT EXTRACTION
    # ------------------------------------------------------------------

    def _extract_requirements(
        self,
        job_description: str,
    ) -> List[ATSRequirement]:

        lines = [
            line.strip(" •-*:\t")
            for line in job_description.splitlines()
            if line.strip()
        ]

        requirements = []

        # First identify explicit skill terms.
        explicit_skills = self._extract_job_skills(
            job_description
        )

        for skill in explicit_skills:
            importance = self._infer_importance(
                skill,
                job_description,
            )

            requirements.append(
                ATSRequirement(
                    text=skill,
                    category="skill",
                    normalized=self._normalize_term(
                        skill
                    ),
                    importance=importance,
                )
            )

        # Then pick up experience/education requirements.
        lowered = job_description.lower()

        if re.search(
            r"\b\d+\+?\s*(?:years?|yrs?)\b",
            lowered,
        ):
            requirements.append(
                ATSRequirement(
                    text="Relevant professional experience",
                    category="experience",
                    normalized="relevant professional experience",
                    importance="required",
                )
            )

        if any(
            term in lowered
            for term in self.DEGREE_TERMS
        ):
            requirements.append(
                ATSRequirement(
                    text="Relevant education or degree",
                    category="education",
                    normalized="relevant education or degree",
                    importance="preferred",
                )
            )

        # Extract high-value multi-word phrases from bullets.
        for line in lines:
            cleaned = self._normalize_text(line)

            if not cleaned:
                continue

            if len(cleaned.split()) > 10:
                continue

            if any(
                phrase in cleaned
                for phrase in (
                    "rest api",
                    "restful api",
                    "machine learning",
                    "deep learning",
                    "system design",
                    "microservices",
                    "data engineering",
                    "software engineering",
                    "cloud computing",
                    "ci/cd",
                )
            ):
                for phrase in (
                    "rest api",
                    "restful api",
                    "machine learning",
                    "deep learning",
                    "system design",
                    "microservices",
                    "data engineering",
                    "software engineering",
                    "cloud computing",
                    "ci/cd",
                ):
                    if phrase in cleaned:
                        requirements.append(
                            ATSRequirement(
                                text=phrase,
                                category="skill",
                                normalized=phrase,
                                importance="preferred",
                            )
                        )

        return self._deduplicate_requirements(
            requirements
        )

    def _extract_job_skills(
        self,
        text: str,
    ) -> List[str]:

        normalized = self._normalize_text(
            text
        )

        found = []

        for skill in sorted(
            self.COMMON_SKILLS,
            key=len,
            reverse=True,
        ):
            pattern = (
                r"(?<![a-z0-9+#.-])"
                + re.escape(skill.lower())
                + r"(?![a-z0-9+#.-])"
            )

            if re.search(
                pattern,
                normalized,
            ):
                found.append(skill)

        return self._deduplicate(
            found
        )

    # ------------------------------------------------------------------
    # MATCHING
    # ------------------------------------------------------------------

    def _match_requirement(
        self,
        requirement: ATSRequirement,
        resume: StructuredResume,
        resume_text: str,
    ) -> ATSMatch:

        term = requirement.normalized

        if requirement.category == "skill":
            skill_evidence = self._find_skill_evidence(
                term,
                resume,
            )

            contextual_evidence = (
                self._find_contextual_evidence(
                    term,
                    resume,
                )
            )

            if contextual_evidence:
                return ATSMatch(
                    requirement=requirement.text,
                    category=requirement.category,
                    status="SUPPORTED",
                    evidence=contextual_evidence,
                    confidence=0.95,
                )

            if skill_evidence:
                return ATSMatch(
                    requirement=requirement.text,
                    category=requirement.category,
                    status="MENTIONED_ONLY",
                    evidence=skill_evidence,
                    confidence=0.65,
                )

            return ATSMatch(
                requirement=requirement.text,
                category=requirement.category,
                status="MISSING",
                evidence=[],
                confidence=0.95,
            )

        if requirement.category == "experience":
            if resume.experience:
                return ATSMatch(
                    requirement=requirement.text,
                    category=requirement.category,
                    status="SUPPORTED",
                    evidence=[
                        f"{len(resume.experience)} experience entr{'y' if len(resume.experience) == 1 else 'ies'} detected."
                    ],
                    confidence=0.85,
                )

            return ATSMatch(
                requirement=requirement.text,
                category=requirement.category,
                status="MISSING",
                evidence=[],
                confidence=0.9,
            )

        if requirement.category == "education":
            if resume.education:
                return ATSMatch(
                    requirement=requirement.text,
                    category=requirement.category,
                    status="SUPPORTED",
                    evidence=[
                        "Education entry detected."
                    ],
                    confidence=0.8,
                )

            return ATSMatch(
                requirement=requirement.text,
                category=requirement.category,
                status="MISSING",
                evidence=[],
                confidence=0.9,
            )

        if term in resume_text:
            return ATSMatch(
                requirement=requirement.text,
                category=requirement.category,
                status="MENTIONED_ONLY",
                evidence=[
                    "Term appears in resume text."
                ],
                confidence=0.6,
            )

        return ATSMatch(
            requirement=requirement.text,
            category=requirement.category,
            status="MISSING",
            evidence=[],
            confidence=0.9,
        )

    def _find_skill_evidence(
        self,
        skill: str,
        resume: StructuredResume,
    ) -> List[str]:

        evidence = []

        all_skills = (
            resume.skills
            + resume.technical_skills
            + resume.soft_skills
        )

        for listed_skill in all_skills:
            if self._terms_match(
                skill,
                listed_skill,
            ):
                evidence.append(
                    f"Listed skill: {listed_skill}"
                )

        return evidence

    def _find_contextual_evidence(
        self,
        skill: str,
        resume: StructuredResume,
    ) -> List[str]:

        evidence = []

        for experience in resume.experience:

            text = (
                experience.description
                or ""
            )

            for bullet in experience.achievements:
                text += " " + bullet

            if self._text_contains_term(
                text,
                skill,
            ):
                evidence.append(
                    f"Experience: {experience.job_title or 'Role'}"
                )

        for project in resume.projects:

            text = project.description

            for achievement in project.achievements:
                text += " " + achievement

            if self._text_contains_term(
                text,
                skill,
            ):
                evidence.append(
                    f"Project: {project.name or 'Project'}"
                )

        if resume.summary and self._text_contains_term(
            resume.summary,
            skill,
        ):
            evidence.append(
                "Professional summary"
            )

        return evidence

    # ------------------------------------------------------------------
    # SCORING
    # ------------------------------------------------------------------

    def _calculate_keyword_coverage(
        self,
        matches: List[ATSMatch],
    ) -> float:

        if not matches:
            return 0.0

        total_weight = 0.0
        earned = 0.0

        for match in matches:

            weight = (
                2.0
                if match.category == "skill"
                else 1.0
            )

            total_weight += weight

            if match.status == "SUPPORTED":
                earned += weight

            elif match.status == "MENTIONED_ONLY":
                earned += weight * 0.55

        return (
            earned
            / total_weight
            * 100
            if total_weight
            else 0.0
        )

    def _calculate_category_score(
        self,
        matches: List[ATSMatch],
        category: str,
    ) -> float:

        selected = [
            match
            for match in matches
            if match.category == category
        ]

        if not selected:
            return 100.0

        total = len(selected)
        earned = 0.0

        for match in selected:

            if match.status == "SUPPORTED":
                earned += 1.0

            elif match.status == "MENTIONED_ONLY":
                earned += 0.5

        return earned / total * 100

    def _calculate_experience_alignment(
        self,
        resume: StructuredResume,
        job_description: str,
        matches: List[ATSMatch],
    ) -> float:

        experience_matches = [
            match
            for match in matches
            if match.category == "experience"
        ]

        if not experience_matches:
            return 100.0 if resume.experience else 40.0

        if not resume.experience:
            return 0.0

        lowered = job_description.lower()

        year_match = re.search(
            r"\b(\d+)\+?\s*(?:years?|yrs?)\b",
            lowered,
        )

        candidate_years = 0.0

        for experience in resume.experience:
            candidate_years += self._estimate_experience_years(
                experience.start_date,
                experience.end_date,
            )

        if not year_match:
            return 75.0

        required_years = float(
            year_match.group(1)
        )

        if candidate_years <= 0:
            return 55.0

        if candidate_years >= required_years:
            return 100.0

        ratio = candidate_years / required_years

        return max(
            20.0,
            min(
                100.0,
                ratio * 100,
            ),
        )

    def _calculate_education_alignment(
        self,
        resume: StructuredResume,
        matches: List[ATSMatch],
    ) -> float:

        education_matches = [
            match
            for match in matches
            if match.category == "education"
        ]

        if not education_matches:
            return 100.0 if resume.education else 60.0

        if resume.education:
            return 100.0

        return 0.0

    def _calculate_section_coverage(
        self,
        resume: StructuredResume,
    ) -> float:

        checks = [
            bool(resume.summary),
            bool(resume.experience),
            bool(resume.education),
            bool(
                resume.skills
                or resume.technical_skills
            ),
            bool(resume.projects),
        ]

        return (
            sum(checks)
            / len(checks)
            * 100
        )

    # ------------------------------------------------------------------
    # RISK DETECTION
    # ------------------------------------------------------------------

    def _detect_keyword_stuffing(
        self,
        resume: StructuredResume,
        matches: List[ATSMatch],
    ) -> bool:

        skills = self._normalize_list(
            resume.skills
            + resume.technical_skills
        )

        if not skills:
            return False

        unique_skills = set(skills)

        duplicate_ratio = (
            1
            - len(unique_skills)
            / len(skills)
        )

        if duplicate_ratio > 0.20:
            return True

        long_skill_line = any(
            len(skill.split()) > 6
            for skill in skills
        )

        return long_skill_line

    def _detect_unsupported_claim_risk(
        self,
        matches: List[ATSMatch],
    ) -> bool:

        return any(
            match.status == "MENTIONED_ONLY"
            and match.category == "skill"
            and match.confidence < 0.7
            for match in matches
        )

    # ------------------------------------------------------------------
    # RECOMMENDATIONS
    # ------------------------------------------------------------------

    def _generate_strengths(
        self,
        matches: List[ATSMatch],
        section_coverage_score: float,
    ) -> List[str]:

        strengths = []

        supported = sum(
            match.status == "SUPPORTED"
            for match in matches
        )

        if supported:
            strengths.append(
                f"{supported} job requirement(s) are supported by resume evidence."
            )

        if section_coverage_score >= 80:
            strengths.append(
                "Core resume sections are present."
            )

        if any(
            match.category == "skill"
            and match.status == "SUPPORTED"
            for match in matches
        ):
            strengths.append(
                "Several target skills are supported by contextual experience or project evidence."
            )

        return strengths

    def _generate_issues(
        self,
        matches: List[ATSMatch],
        keyword_stuffing_risk: bool,
        unsupported_claim_risk: bool,
    ) -> List[str]:

        issues = []

        missing = sum(
            match.status == "MISSING"
            for match in matches
        )

        mentioned_only = sum(
            match.status == "MENTIONED_ONLY"
            for match in matches
        )

        if missing:
            issues.append(
                f"{missing} job requirement(s) are not currently represented."
            )

        if mentioned_only:
            issues.append(
                f"{mentioned_only} requirement(s) appear without strong contextual evidence."
            )

        if keyword_stuffing_risk:
            issues.append(
                "The resume may contain redundant or overly dense keyword usage."
            )

        if unsupported_claim_risk:
            issues.append(
                "Some matched keywords may be listed without enough evidence of practical use."
            )

        return issues

    def _generate_recommendations(
        self,
        matches: List[ATSMatch],
        resume: StructuredResume,
        keyword_stuffing_risk: bool,
    ) -> List[str]:

        recommendations = []

        missing_skills = [
            match.requirement
            for match in matches
            if match.category == "skill"
            and match.status == "MISSING"
        ]

        weak_skills = [
            match.requirement
            for match in matches
            if match.category == "skill"
            and match.status == "MENTIONED_ONLY"
        ]

        if missing_skills:
            recommendations.append(
                "Add missing job-specific skills only when they are genuinely supported by your background."
            )

        if weak_skills:
            recommendations.append(
                "Strengthen contextual evidence for skills that are currently only listed in the skills section."
            )

        if any(
            match.category == "experience"
            and match.status == "SUPPORTED"
            for match in matches
        ):
            recommendations.append(
                "Align experience bullets with the responsibilities and outcomes emphasized by the target role."
            )

        if keyword_stuffing_risk:
            recommendations.append(
                "Normalize duplicate skills and avoid repeating the same keyword without additional evidence."
            )

        if not resume.projects:
            recommendations.append(
                "Consider adding relevant projects when they provide genuine evidence for target-job requirements."
            )

        return recommendations

    def _generate_summary(
        self,
        score: float,
        supported: List[str],
        mentioned_only: List[str],
        missing: List[str],
    ) -> str:

        if score >= 85:
            level = "strong"
        elif score >= 70:
            level = "good"
        elif score >= 50:
            level = "moderate"
        else:
            level = "weak"

        return (
            f"The resume shows a {level} ATS alignment with the target job, "
            f"scoring {round(score, 1)}/100. "
            f"{len(supported)} requirements are supported, "
            f"{len(mentioned_only)} are mentioned without strong contextual evidence, "
            f"and {len(missing)} are currently missing."
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _build_resume_text(
        self,
        resume: StructuredResume,
    ) -> str:

        parts = [
            resume.headline or "",
            resume.summary,
            *resume.skills,
            *resume.technical_skills,
            *resume.soft_skills,
        ]

        for experience in resume.experience:
            parts.extend(
                [
                    experience.job_title or "",
                    experience.company or "",
                    experience.description,
                    *experience.achievements,
                    *experience.technologies,
                ]
            )

        for education in resume.education:
            parts.extend(
                [
                    education.degree or "",
                    education.institution or "",
                    education.field_of_study or "",
                ]
            )

        for project in resume.projects:
            parts.extend(
                [
                    project.name or "",
                    project.description,
                    *project.technologies,
                    *project.achievements,
                ]
            )

        return self._normalize_text(
            " ".join(parts)
        )

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        value = text.lower()

        value = value.replace(
            "&",
            " and ",
        )

        value = re.sub(
            r"[^a-z0-9+#./% -]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    def _normalize_term(
        self,
        term: str,
    ) -> str:

        return self._normalize_text(
            term
        )

    def _text_contains_term(
        self,
        text: str,
        term: str,
    ) -> bool:

        normalized_text = self._normalize_text(
            text
        )

        normalized_term = self._normalize_term(
            term
        )

        return bool(
            re.search(
                r"(?<![a-z0-9+#.-])"
                + re.escape(normalized_term)
                + r"(?![a-z0-9+#.-])",
                normalized_text,
            )
        )

    def _terms_match(
        self,
        left: str,
        right: str,
    ) -> bool:

        normalized_left = self._normalize_term(
            left
        )

        normalized_right = self._normalize_term(
            right
        )

        if normalized_left == normalized_right:
            return True

        aliases = {
            "restful api": "rest api",
            "node": "node.js",
            "node js": "node.js",
            "postgres": "postgresql",
            "postgres sql": "postgresql",
            "ml": "machine learning",
            "ai": "artificial intelligence",
        }

        left_alias = aliases.get(
            normalized_left,
            normalized_left,
        )

        right_alias = aliases.get(
            normalized_right,
            normalized_right,
        )

        return left_alias == right_alias

    def _infer_importance(
        self,
        skill: str,
        job_description: str,
    ) -> str:

        lowered = job_description.lower()

        patterns = [
            f"required {skill.lower()}",
            f"{skill.lower()} required",
            f"must have {skill.lower()}",
            f"must know {skill.lower()}",
            f"mandatory {skill.lower()}",
        ]

        if any(
            pattern in lowered
            for pattern in patterns
        ):
            return "required"

        return "preferred"

    def _estimate_experience_years(
        self,
        start_date: str | None,
        end_date: str | None,
    ) -> float:

        if not start_date:
            return 0.0

        start = self._extract_year(
            start_date
        )

        if not start:
            return 0.0

        end = self._extract_year(
            end_date or ""
        )

        if not end:
            from datetime import datetime

            end = datetime.now().year

        return max(
            0.0,
            float(end - start),
        )

    def _extract_year(
        self,
        value: str,
    ) -> int | None:

        match = re.search(
            r"\b(19|20)\d{2}\b",
            value or "",
        )

        if not match:
            return None

        return int(
            match.group(0)
        )

    def _deduplicate_requirements(
        self,
        requirements: List[ATSRequirement],
    ) -> List[ATSRequirement]:

        seen = set()
        result = []

        for requirement in requirements:

            key = (
                requirement.category,
                requirement.normalized,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(requirement)

        return result

    def _normalize_list(
        self,
        values: List[str],
    ) -> List[str]:

        normalized = []

        for value in values:
            cleaned = self._normalize_text(
                value
            )

            if cleaned:
                normalized.append(
                    cleaned
                )

        return normalized

    def _deduplicate(
        self,
        values: List[str],
    ) -> List[str]:

        return list(
            dict.fromkeys(
                value
                for value in values
                if value
            )
        )