from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from backend.schemas.resume import StructuredResume


@dataclass
class JobResumeRequirement:
    requirement: str
    category: str
    importance: str
    status: str
    evidence: List[str] = field(default_factory=list)
    evidence_strength: int = 0


@dataclass
class JobResumeAnalysis:
    overall_fit_score: float
    evidence_score: float
    keyword_alignment_score: float
    experience_alignment_score: float
    section_relevance_score: float

    strong_matches: List[JobResumeRequirement]
    partial_matches: List[JobResumeRequirement]
    missing_requirements: List[JobResumeRequirement]

    top_priorities: List[str]
    recommendations: List[str]

    target_role: str = ""
    summary: str = ""


class JobResumeAnalyzer:
    """
    Deterministic, evidence-based analysis of how well a structured resume
    is positioned for a specific target job.

    This analyzer intentionally does NOT invent experience, skills,
    technologies, employers, projects, or achievements.
    """

    COMMON_SKILLS = {
        # Programming
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "go",
        "golang",
        "rust",
        "php",
        "ruby",
        "kotlin",
        "swift",

        # Backend / APIs
        "fastapi",
        "flask",
        "django",
        "spring",
        "spring boot",
        "node",
        "node.js",
        "express",
        "rest api",
        "rest",
        "graphql",
        "microservices",

        # Frontend
        "react",
        "react.js",
        "next.js",
        "nextjs",
        "angular",
        "vue",
        "html",
        "css",
        "tailwind",
        "bootstrap",

        # Databases
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "mongodb",
        "redis",
        "sqlite",
        "oracle",
        "dynamodb",

        # AI / ML
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "ai",
        "llm",
        "generative ai",
        "genai",
        "nlp",
        "computer vision",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "langchain",
        "langgraph",

        # DevOps / Cloud
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "ci/cd",
        "github actions",
        "terraform",
        "linux",

        # Engineering
        "git",
        "github",
        "testing",
        "unit testing",
        "system design",
        "data structures",
        "algorithms",

        # Design / Analytics
        "figma",
        "adobe photoshop",
        "photoshop",
        "adobe illustrator",
        "illustrator",
        "tableau",
        "power bi",
        "excel",
    }

    ROLE_STOPWORDS = {
        "and",
        "or",
        "the",
        "a",
        "an",
        "for",
        "with",
        "of",
        "to",
        "in",
        "on",
        "engineer",
        "developer",
        "designer",
        "analyst",
        "specialist",
        "senior",
        "junior",
        "lead",
        "manager",
        "software",
        "technology",
        "technologies",
    }

    ACTION_TERMS = {
        "build",
        "develop",
        "design",
        "implement",
        "create",
        "maintain",
        "optimize",
        "automate",
        "analyze",
        "lead",
        "collaborate",
        "deploy",
        "integrate",
        "test",
        "debug",
        "research",
        "architect",
        "manage",
    }

    def analyze(
        self,
        resume: StructuredResume,
        job_description: str,
    ) -> JobResumeAnalysis:
        if not job_description or not job_description.strip():
            raise ValueError("job_description must not be empty")

        job_text = self._normalize(job_description)

        target_role = self._extract_target_role(job_description)
        requirements = self._extract_requirements(job_description)

        resume_text = self._resume_search_text(resume)

        evaluated: List[JobResumeRequirement] = []

        for requirement, category, importance in requirements:
            status, evidence, strength = self._evaluate_requirement(
                requirement=requirement,
                category=category,
                resume=resume,
                resume_text=resume_text,
                job_text=job_text,
            )

            evaluated.append(
                JobResumeRequirement(
                    requirement=requirement,
                    category=category,
                    importance=importance,
                    status=status,
                    evidence=evidence,
                    evidence_strength=strength,
                )
            )

        strong_matches = [
            item for item in evaluated if item.status == "STRONG_MATCH"
        ]

        partial_matches = [
            item for item in evaluated if item.status == "PARTIAL_MATCH"
        ]

        missing_requirements = [
            item for item in evaluated if item.status == "MISSING"
        ]

        keyword_alignment_score = self._score_keyword_alignment(
            evaluated
        )

        evidence_score = self._score_evidence(evaluated)

        experience_alignment_score = self._score_experience_alignment(
            resume,
            job_description,
        )

        section_relevance_score = self._score_section_relevance(
            resume,
            job_description,
        )

        overall_fit_score = round(
            (
                keyword_alignment_score * 0.30
                + evidence_score * 0.35
                + experience_alignment_score * 0.20
                + section_relevance_score * 0.15
            ),
            1,
        )

        top_priorities = self._build_priorities(
            missing_requirements=missing_requirements,
            partial_matches=partial_matches,
            resume=resume,
        )

        recommendations = self._build_recommendations(
            missing_requirements=missing_requirements,
            partial_matches=partial_matches,
            resume=resume,
            job_description=job_description,
        )

        summary = self._build_summary(
            target_role=target_role,
            overall_fit_score=overall_fit_score,
            strong_count=len(strong_matches),
            partial_count=len(partial_matches),
            missing_count=len(missing_requirements),
        )

        return JobResumeAnalysis(
            overall_fit_score=overall_fit_score,
            evidence_score=round(evidence_score, 1),
            keyword_alignment_score=round(keyword_alignment_score, 1),
            experience_alignment_score=round(
                experience_alignment_score,
                1,
            ),
            section_relevance_score=round(
                section_relevance_score,
                1,
            ),
            strong_matches=strong_matches,
            partial_matches=partial_matches,
            missing_requirements=missing_requirements,
            top_priorities=top_priorities,
            recommendations=recommendations,
            target_role=target_role,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Requirement extraction
    # ------------------------------------------------------------------

    def _extract_requirements(
        self,
        job_description: str,
    ) -> List[Tuple[str, str, str]]:
        """
        Returns:
            (requirement, category, importance)
        """

        requirements: List[Tuple[str, str, str]] = []
        seen = set()

        text = self._normalize(job_description)

        # 1. Explicit skill requirements
        for skill in sorted(
            self.COMMON_SKILLS,
            key=len,
            reverse=True,
        ):
            if self._contains_skill(text, skill):
                category = self._skill_category(skill)

                importance = (
                    "HIGH"
                    if self._is_high_importance_skill(
                        text,
                        skill,
                    )
                    else "MEDIUM"
                )

                key = (skill, category)

                if key not in seen:
                    requirements.append(
                        (skill, category, importance)
                    )
                    seen.add(key)

        # 2. Experience requirement
        experience_match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*years?"
            r"(?:\s+of)?\s+(?:relevant\s+)?"
            r"(?:professional\s+)?experience",
            text,
        )

        if experience_match:
            years = experience_match.group(1)

            requirement = (
                f"{years}+ years relevant experience"
            )

            requirements.append(
                (
                    requirement,
                    "experience",
                    "HIGH",
                )
            )

        # 3. Education
        education_keywords = [
            "bachelor",
            "b.tech",
            "btech",
            "master",
            "m.tech",
            "mtech",
            "degree",
            "computer science",
            "engineering degree",
            "bachelor's degree",
            "master's degree",
        ]

        matched_education = [
            item
            for item in education_keywords
            if item in text
        ]

        if matched_education:
            requirement = "Relevant educational qualification"

            requirements.append(
                (
                    requirement,
                    "education",
                    "MEDIUM",
                )
            )

        # 4. Important responsibility phrases
        responsibility_patterns = [
            r"design and develop ([^.]{10,120})",
            r"build and maintain ([^.]{10,120})",
            r"responsible for ([^.]{10,120})",
            r"experience with ([^.]{10,120})",
            r"hands[- ]on experience with ([^.]{10,120})",
            r"strong understanding of ([^.]{10,120})",
        ]

        for pattern in responsibility_patterns:
            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                phrase = self._clean_requirement(match.group(1))

                if self._is_useful_requirement(phrase):
                    key = phrase.lower()

                    if key not in seen:
                        requirements.append(
                            (
                                phrase,
                                "responsibility",
                                "MEDIUM",
                            )
                        )
                        seen.add(key)

        # Prevent excessive noise.
        return requirements[:40]

    # ------------------------------------------------------------------
    # Requirement evaluation
    # ------------------------------------------------------------------

    def _evaluate_requirement(
        self,
        requirement: str,
        category: str,
        resume: StructuredResume,
        resume_text: str,
        job_text: str,
    ) -> Tuple[str, List[str], int]:
        normalized_requirement = self._normalize(requirement)

        # Skills
        if category == "skill":
            return self._evaluate_skill(
                requirement,
                resume,
                resume_text,
            )

        # Experience
        if category == "experience":
            return self._evaluate_experience(
                requirement,
                resume,
            )

        # Education
        if category == "education":
            return self._evaluate_education(
                requirement,
                resume,
            )

        # Responsibilities
        if category == "responsibility":
            return self._evaluate_responsibility(
                requirement,
                resume,
                resume_text,
                normalized_requirement,
            )

        return (
            "MISSING",
            [],
            0,
        )

    def _evaluate_skill(
        self,
        requirement: str,
        resume: StructuredResume,
        resume_text: str,
    ) -> Tuple[str, List[str], int]:
        normalized = self._normalize(requirement)

        exact_matches = []

        for skill in (
            resume.skills
            + resume.technical_skills
        ):
            if self._normalize(skill) == normalized:
                exact_matches.append(skill)

        if exact_matches:
            return (
                "STRONG_MATCH",
                [
                    f"Listed skill: {skill}"
                    for skill in exact_matches[:3]
                ],
                100,
            )

        # Resume may prove the skill through experience/projects
        contextual_evidence = self._find_contextual_evidence(
            requirement,
            resume,
        )

        if contextual_evidence:
            return (
                "PARTIAL_MATCH",
                contextual_evidence[:3],
                70,
            )

        # Normalize known aliases.
        aliases = self._skill_aliases(requirement)

        for alias in aliases:
            if self._contains_skill(resume_text, alias):
                return (
                    "PARTIAL_MATCH",
                    [
                        f"Referenced in resume text as: {alias}"
                    ],
                    65,
                )

        return (
            "MISSING",
            [],
            0,
        )

    def _evaluate_experience(
        self,
        requirement: str,
        resume: StructuredResume,
    ) -> Tuple[str, List[str], int]:
        requested_years = self._extract_year_count(
            requirement
        )

        if requested_years is None:
            return (
                "PARTIAL_MATCH",
                [],
                50,
            )

        resume_years = self._estimate_resume_years(
            resume
        )

        if resume_years >= requested_years:
            return (
                "STRONG_MATCH",
                [
                    (
                        f"Estimated resume experience: "
                        f"{resume_years:.1f} years"
                    )
                ],
                100,
            )

        if resume_years >= requested_years * 0.7:
            return (
                "PARTIAL_MATCH",
                [
                    (
                        f"Estimated resume experience: "
                        f"{resume_years:.1f} years; "
                        f"job requests {requested_years:.0f}+ years"
                    )
                ],
                60,
            )

        return (
            "MISSING",
            [
                (
                    f"Estimated resume experience: "
                    f"{resume_years:.1f} years; "
                    f"job requests {requested_years:.0f}+ years"
                )
            ],
            20,
        )

    def _evaluate_education(
        self,
        requirement: str,
        resume: StructuredResume,
    ) -> Tuple[str, List[str], int]:
        if not resume.education:
            return (
                "MISSING",
                [],
                0,
            )

        evidence = []

        for education in resume.education:
            values = [
                education.degree,
                education.institution,
                education.field_of_study,
            ]

            clean_values = [
                value
                for value in values
                if value
            ]

            if clean_values:
                evidence.append(
                    "Education: "
                    + ", ".join(clean_values)
                )

        if evidence:
            return (
                "STRONG_MATCH",
                evidence[:3],
                100,
            )

        return (
            "PARTIAL_MATCH",
            [],
            50,
        )

    def _evaluate_responsibility(
        self,
        requirement: str,
        resume: StructuredResume,
        resume_text: str,
        normalized_requirement: str,
    ) -> Tuple[str, List[str], int]:
        requirement_tokens = {
            token
            for token in re.findall(
                r"[a-zA-Z0-9+#.]+",
                normalized_requirement,
            )
            if len(token) >= 4
        }

        if not requirement_tokens:
            return (
                "MISSING",
                [],
                0,
            )

        evidence = []

        searchable_blocks = self._resume_evidence_blocks(
            resume
        )

        for block in searchable_blocks:
            block_normalized = self._normalize(block)

            block_tokens = set(
                re.findall(
                    r"[a-zA-Z0-9+#.]+",
                    block_normalized,
                )
            )

            overlap = requirement_tokens.intersection(
                block_tokens
            )

            coverage = (
                len(overlap)
                / max(len(requirement_tokens), 1)
            )

            if coverage >= 0.75:
                evidence.append(block.strip())

            elif coverage >= 0.45:
                evidence.append(block.strip())

        if evidence:
            best_coverage = self._best_requirement_coverage(
                requirement_tokens,
                evidence,
            )

            if best_coverage >= 0.75:
                return (
                    "STRONG_MATCH",
                    evidence[:3],
                    90,
                )

            return (
                "PARTIAL_MATCH",
                evidence[:3],
                65,
            )

        # A broad textual check can still establish weak evidence.
        if self._contains_phrase_tokens(
            resume_text,
            requirement_tokens,
        ):
            return (
                "PARTIAL_MATCH",
                [
                    "Related terminology appears in "
                    "the resume."
                ],
                55,
            )

        return (
            "MISSING",
            [],
            0,
        )

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_keyword_alignment(
        self,
        requirements: List[JobResumeRequirement],
    ) -> float:
        if not requirements:
            return 0.0

        weights = {
            "HIGH": 1.5,
            "MEDIUM": 1.0,
            "LOW": 0.5,
        }

        earned = 0.0
        possible = 0.0

        for item in requirements:
            weight = weights.get(
                item.importance,
                1.0,
            )

            possible += 100 * weight

            if item.status == "STRONG_MATCH":
                earned += 100 * weight

            elif item.status == "PARTIAL_MATCH":
                earned += 65 * weight

        return min(
            100.0,
            (earned / possible) * 100
            if possible
            else 0.0,
        )

    def _score_evidence(
        self,
        requirements: List[JobResumeRequirement],
    ) -> float:
        if not requirements:
            return 0.0

        total = sum(
            item.evidence_strength
            for item in requirements
        )

        return total / len(requirements)

    def _score_experience_alignment(
        self,
        resume: StructuredResume,
        job_description: str,
    ) -> float:
        requested_years = self._extract_year_count(
            self._normalize(job_description)
        )

        actual_years = self._estimate_resume_years(
            resume
        )

        score = 60.0

        if requested_years is not None:
            if actual_years >= requested_years:
                score = 100.0
            elif actual_years >= requested_years * 0.8:
                score = 80.0
            elif actual_years >= requested_years * 0.5:
                score = 55.0
            else:
                score = 25.0

        if resume.experience:
            score += 5

        return min(
            100.0,
            score,
        )

    def _score_section_relevance(
        self,
        resume: StructuredResume,
        job_description: str,
    ) -> float:
        text = self._normalize(
            job_description
        )

        score = 0.0
        possible = 0.0

        sections = {
            "summary": bool(resume.summary),
            "experience": bool(resume.experience),
            "skills": bool(
                resume.skills
                or resume.technical_skills
            ),
            "projects": bool(resume.projects),
            "education": bool(resume.education),
        }

        relevance_weights = {
            "summary": 1.0,
            "experience": 2.0,
            "skills": 2.0,
            "projects": 1.5,
            "education": 0.75,
        }

        technical_job = self._looks_technical(text)

        for section, present in sections.items():
            weight = relevance_weights[section]

            if technical_job and section == "projects":
                weight = 2.0

            possible += weight

            if present:
                score += weight

        if possible == 0:
            return 0.0

        return (score / possible) * 100

    # ------------------------------------------------------------------
    # Recommendations / priorities
    # ------------------------------------------------------------------

    def _build_priorities(
        self,
        missing_requirements: List[JobResumeRequirement],
        partial_matches: List[JobResumeRequirement],
        resume: StructuredResume,
    ) -> List[str]:
        priorities: List[str] = []

        high_missing = [
            item
            for item in missing_requirements
            if item.importance == "HIGH"
        ]

        for item in high_missing[:5]:
            priorities.append(
                f"Address missing high-priority requirement: "
                f"{item.requirement}"
            )

        for item in partial_matches[:5]:
            priorities.append(
                f"Strengthen evidence for: "
                f"{item.requirement}"
            )

        if not resume.projects:
            priorities.append(
                "Add relevant projects to demonstrate "
                "job-specific practical evidence."
            )

        if not resume.summary:
            priorities.append(
                "Add a targeted professional summary "
                "aligned with this role."
            )

        return self._deduplicate(
            priorities
        )[:8]

    def _build_recommendations(
        self,
        missing_requirements: List[JobResumeRequirement],
        partial_matches: List[JobResumeRequirement],
        resume: StructuredResume,
        job_description: str,
    ) -> List[str]:
        recommendations: List[str] = []

        high_missing = [
            item
            for item in missing_requirements
            if item.importance == "HIGH"
        ]

        for item in high_missing[:4]:
            if item.category == "skill":
                recommendations.append(
                    f"Add {item.requirement} only when "
                    f"you genuinely have the skill and can support it "
                    f"with experience, coursework, or a project."
                )

            elif item.category == "experience":
                recommendations.append(
                    "Do not fabricate years of experience. "
                    "Instead, emphasize the most relevant experience "
                    "and projects that demonstrate equivalent capability."
                )

            else:
                recommendations.append(
                    f"Address the job requirement '{item.requirement}' "
                    "through truthful resume evidence."
                )

        for item in partial_matches[:4]:
            if item.category == "skill":
                recommendations.append(
                    f"Make {item.requirement} more explicit in "
                    "the Skills section and in a relevant experience "
                    "or project bullet where supported."
                )

            elif item.category == "responsibility":
                recommendations.append(
                    f"Rewrite relevant bullets to directly demonstrate "
                    f"the responsibility '{item.requirement}', "
                    "without adding unsupported claims."
                )

        if resume.experience:
            recommendations.append(
                "Prioritize measurable outcomes, scale, ownership, "
                "and technologies in experience bullets that directly "
                "match this job."
            )

        if resume.projects:
            recommendations.append(
                "Move the most relevant project evidence toward "
                "the sections receiving the most attention from the target role."
            )

        if not resume.projects:
            recommendations.append(
                "Consider adding one genuinely relevant project "
                "that demonstrates the target role's core requirements."
            )

        return self._deduplicate(
            recommendations
        )[:10]

    def _build_summary(
        self,
        target_role: str,
        overall_fit_score: float,
        strong_count: int,
        partial_count: int,
        missing_count: int,
    ) -> str:
        role_text = (
            target_role
            if target_role
            else "the target role"
        )

        return (
            f"The resume shows a {overall_fit_score:.1f}/100 "
            f"job-specific fit for {role_text}. "
            f"It has {strong_count} strong matches, "
            f"{partial_count} partial matches, and "
            f"{missing_count} missing requirements. "
            "The score reflects evidence present in the resume, "
            "not predicted hiring probability."
        )

    # ------------------------------------------------------------------
    # Resume evidence helpers
    # ------------------------------------------------------------------

    def _resume_search_text(
        self,
        resume: StructuredResume,
    ) -> str:
        parts: List[str] = [
            resume.headline or "",
            resume.summary or "",
            *resume.skills,
            *resume.technical_skills,
            *resume.soft_skills,
        ]

        for item in resume.experience:
            parts.extend(
                [
                    item.job_title or "",
                    item.company or "",
                    item.location or "",
                    item.description,
                    *item.achievements,
                    *item.technologies,
                ]
            )

        for item in resume.projects:
            parts.extend(
                [
                    item.name or "",
                    item.description,
                    *item.technologies,
                    *item.achievements,
                ]
            )

        for item in resume.education:
            parts.extend(
                [
                    item.degree or "",
                    item.institution or "",
                    item.field_of_study or "",
                ]
            )

        return self._normalize(
            " ".join(parts)
        )

    def _resume_evidence_blocks(
        self,
        resume: StructuredResume,
    ) -> List[str]:
        blocks: List[str] = []

        if resume.summary:
            blocks.append(
                resume.summary
            )

        for experience in resume.experience:
            if experience.description:
                blocks.append(
                    experience.description
                )

            blocks.extend(
                experience.achievements
            )

        for project in resume.projects:
            if project.description:
                blocks.append(
                    project.description
                )

            blocks.extend(
                project.achievements
            )

        return [
            block
            for block in blocks
            if block and block.strip()
        ]

    def _find_contextual_evidence(
        self,
        requirement: str,
        resume: StructuredResume,
    ) -> List[str]:
        requirement_tokens = set(
            self._tokenize(requirement)
        )

        evidence = []

        for block in self._resume_evidence_blocks(
            resume
        ):
            tokens = set(
                self._tokenize(block)
            )

            overlap = requirement_tokens.intersection(
                tokens
            )

            if overlap:
                evidence.append(
                    block
                )

        return evidence

    def _best_requirement_coverage(
        self,
        requirement_tokens: set[str],
        evidence: List[str],
    ) -> float:
        best = 0.0

        for item in evidence:
            tokens = set(
                self._tokenize(item)
            )

            coverage = (
                len(requirement_tokens.intersection(tokens))
                / max(len(requirement_tokens), 1)
            )

            best = max(
                best,
                coverage,
            )

        return best

    # ------------------------------------------------------------------
    # Role / experience helpers
    # ------------------------------------------------------------------

    def _extract_target_role(
        self,
        job_description: str,
    ) -> str:
        lines = [
            line.strip()
            for line in job_description.splitlines()
            if line.strip()
        ]

        if not lines:
            return ""

        first_line = lines[0]

        cleaned = re.sub(
            r"^(job title|position|role)\s*:\s*",
            "",
            first_line,
            flags=re.IGNORECASE,
        )

        if len(cleaned) <= 120:
            return cleaned

        return ""

    def _extract_year_count(
        self,
        text: str,
    ) -> float | None:
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return float(
            match.group(1)
        )

    def _estimate_resume_years(
        self,
        resume: StructuredResume,
    ) -> float:
        ranges = []

        for item in resume.experience:
            start = self._parse_year(
                item.start_date
            )
            end = self._parse_year(
                item.end_date
            )

            if start is None:
                continue

            if end is None:
                end = 2026

            if end >= start:
                ranges.append(
                    (start, end)
                )

        if not ranges:
            return 0.0

        # Merge overlapping employment periods.
        ranges.sort()

        merged = [ranges[0]]

        for start, end in ranges[1:]:
            previous_start, previous_end = merged[-1]

            if start <= previous_end:
                merged[-1] = (
                    previous_start,
                    max(previous_end, end),
                )
            else:
                merged.append(
                    (start, end)
                )

        total_years = sum(
            end - start
            for start, end in merged
        )

        return max(
            0.0,
            float(total_years),
        )

    def _parse_year(
        self,
        value: str | None,
    ) -> int | None:
        if not value:
            return None

        if "present" in value.lower():
            return 2026

        match = re.search(
            r"(19|20)\d{2}",
            value,
        )

        if not match:
            return None

        return int(
            match.group(0)
        )

    # ------------------------------------------------------------------
    # Skill helpers
    # ------------------------------------------------------------------

    def _skill_category(
        self,
        skill: str,
    ) -> str:
        s = self._normalize(skill)

        if s in {
            "python",
            "java",
            "javascript",
            "typescript",
            "c",
            "c++",
            "c#",
            "go",
            "golang",
            "rust",
            "php",
            "ruby",
            "kotlin",
            "swift",
        }:
            return "skill"

        return "skill"

    def _skill_aliases(
        self,
        skill: str,
    ) -> List[str]:
        normalized = self._normalize(
            skill
        )

        aliases = {
            "react": [
                "react",
                "react.js",
                "reactjs",
            ],
            "next.js": [
                "next.js",
                "nextjs",
            ],
            "postgresql": [
                "postgresql",
                "postgres",
            ],
            "golang": [
                "golang",
                "go",
            ],
            "scikit-learn": [
                "scikit-learn",
                "sklearn",
            ],
            "generative ai": [
                "generative ai",
                "genai",
            ],
        }

        return aliases.get(
            normalized,
            [normalized],
        )

    def _is_high_importance_skill(
        self,
        text: str,
        skill: str,
    ) -> bool:
        patterns = [
            f"required.*{re.escape(skill)}",
            f"{re.escape(skill)}.*required",
            f"must.*{re.escape(skill)}",
            f"{re.escape(skill)}.*must",
            f"strong.*{re.escape(skill)}",
        ]

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    # ------------------------------------------------------------------
    # General text helpers
    # ------------------------------------------------------------------

    def _contains_skill(
        self,
        text: str,
        skill: str,
    ) -> bool:
        normalized_skill = self._normalize(
            skill
        )

        if " " in normalized_skill:
            return normalized_skill in text

        pattern = rf"(?<![a-z0-9+#.]){re.escape(normalized_skill)}(?![a-z0-9+#.])"

        return re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ) is not None

    def _contains_phrase_tokens(
        self,
        text: str,
        tokens: set[str],
    ) -> bool:
        text_tokens = set(
            self._tokenize(text)
        )

        if not tokens:
            return False

        coverage = len(
            text_tokens.intersection(tokens)
        ) / len(tokens)

        return coverage >= 0.7

    def _tokenize(
        self,
        text: str,
    ) -> List[str]:
        return [
            token.lower()
            for token in re.findall(
                r"[a-zA-Z0-9+#.]+",
                self._normalize(text),
            )
            if len(token) >= 3
            and token not in self.ROLE_STOPWORDS
        ]

    def _normalize(
        self,
        text: str,
    ) -> str:
        text = text.lower()

        text = text.replace(
            "\u2013",
            "-",
        ).replace(
            "\u2014",
            "-",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _clean_requirement(
        self,
        text: str,
    ) -> str:
        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip(
            " ,;:-"
        )

        if len(text) > 120:
            text = text[:120].rstrip() + "..."

        return text

    def _is_useful_requirement(
        self,
        text: str,
    ) -> bool:
        if len(text) < 8:
            return False

        if len(text.split()) < 2:
            return False

        return not all(
            token in self.ROLE_STOPWORDS
            for token in text.lower().split()
        )

    def _looks_technical(
        self,
        text: str,
    ) -> bool:
        technical_markers = [
            "software",
            "developer",
            "engineer",
            "programming",
            "api",
            "database",
            "python",
            "java",
            "javascript",
            "machine learning",
            "cloud",
        ]

        return sum(
            marker in text
            for marker in technical_markers
        ) >= 2

    def _deduplicate(
        self,
        values: List[str],
    ) -> List[str]:
        seen = set()
        result = []

        for value in values:
            key = value.lower().strip()

            if key in seen:
                continue

            seen.add(key)
            result.append(value)

        return result


job_resume_analyzer = JobResumeAnalyzer()