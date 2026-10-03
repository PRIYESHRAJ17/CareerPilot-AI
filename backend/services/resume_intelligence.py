from dataclasses import dataclass, field
from typing import Dict, List, Set

from backend.schemas.resume import StructuredResume


@dataclass
class ResumeSectionScore:
    """Score and evidence for one resume section."""

    score: float
    strengths: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ResumeIntelligenceResult:
    """
    Deterministic resume intelligence result.

    This layer intentionally does not use an LLM.
    It provides evidence that a future AI reasoning layer
    can safely reason over.
    """

    overall_score: float

    section_scores: Dict[str, ResumeSectionScore]

    strengths: List[str]
    issues: List[str]
    recommendations: List[str]

    missing_sections: List[str]

    keyword_quality: Dict[str, object]
    achievement_analysis: Dict[str, object]

    summary: str

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "section_scores": {
                name: {
                    "score": section.score,
                    "strengths": section.strengths,
                    "issues": section.issues,
                    "recommendations": section.recommendations,
                }
                for name, section in self.section_scores.items()
            },
            "strengths": self.strengths,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "missing_sections": self.missing_sections,
            "keyword_quality": self.keyword_quality,
            "achievement_analysis": self.achievement_analysis,
            "summary": self.summary,
        }


class ResumeIntelligenceEngine:
    """
    Deterministic Resume Intelligence Engine.

    Responsibilities:

    1. Evaluate resume completeness.
    2. Score important resume sections.
    3. Detect weak or vague content.
    4. Analyze achievement/impact evidence.
    5. Evaluate skill quality.
    6. Generate actionable recommendations.
    7. Produce structured evidence for future AI reasoning.

    Important:
    This engine NEVER invents achievements, metrics, technologies,
    employers, dates or qualifications.
    """

    SECTION_WEIGHTS = {
        "contact": 0.10,
        "summary": 0.10,
        "experience": 0.30,
        "education": 0.10,
        "skills": 0.15,
        "projects": 0.15,
        "certifications": 0.05,
        "achievements": 0.05,
    }

    WEAK_TERMS = {
        "responsible for",
        "worked on",
        "helped",
        "assisted",
        "participated",
        "involved in",
        "handled",
        "did",
        "worked with",
        "duties included",
    }

    ACTION_VERBS = {
        "built",
        "developed",
        "designed",
        "created",
        "implemented",
        "engineered",
        "automated",
        "optimized",
        "improved",
        "reduced",
        "increased",
        "launched",
        "led",
        "managed",
        "delivered",
        "deployed",
        "architected",
        "integrated",
        "analyzed",
        "developed",
        "migrated",
        "streamlined",
        "configured",
    }

    METRIC_PATTERN_TERMS = {
        "%",
        "percent",
        "x",
        "million",
        "thousand",
        "crore",
        "lakh",
        "₹",
        "$",
        "€",
        "users",
        "customers",
        "clients",
        "requests",
        "transactions",
        "projects",
        "hours",
        "days",
        "months",
    }

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
    }

    RECOMMENDED_SECTIONS = {
        "summary",
        "experience",
        "education",
        "skills",
        "projects",
        "certifications",
        "achievements",
    }

    def analyze(
        self,
        resume: StructuredResume,
    ) -> ResumeIntelligenceResult:

        section_scores = {
            "contact": self._score_contact(resume),
            "summary": self._score_summary(resume),
            "experience": self._score_experience(resume),
            "education": self._score_education(resume),
            "skills": self._score_skills(resume),
            "projects": self._score_projects(resume),
            "certifications": self._score_certifications(resume),
            "achievements": self._score_achievements(resume),
        }

        overall_score = self._calculate_overall_score(
            section_scores
        )

        missing_sections = self._find_missing_sections(
            resume
        )

        keyword_quality = self._analyze_keyword_quality(
            resume
        )

        achievement_analysis = (
            self._analyze_achievement_evidence(
                resume
            )
        )

        strengths = self._collect_strengths(
            section_scores
        )

        issues = self._collect_issues(
            section_scores
        )

        recommendations = self._collect_recommendations(
            section_scores
        )

        recommendations.extend(
            self._generate_global_recommendations(
                resume,
                missing_sections,
                keyword_quality,
                achievement_analysis,
            )
        )

        recommendations = self._deduplicate(
            recommendations
        )

        summary = self._generate_summary(
            overall_score,
            strengths,
            issues,
        )

        return ResumeIntelligenceResult(
            overall_score=round(
                overall_score,
                1,
            ),
            section_scores=section_scores,
            strengths=self._deduplicate(
                strengths
            ),
            issues=self._deduplicate(
                issues
            ),
            recommendations=recommendations,
            missing_sections=missing_sections,
            keyword_quality=keyword_quality,
            achievement_analysis=achievement_analysis,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # SECTION SCORING
    # ------------------------------------------------------------------

    def _score_contact(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        contact = resume.contact

        fields = [
            contact.name,
            contact.email,
            contact.phone,
            contact.location,
        ]

        optional_fields = [
            contact.website,
            contact.linkedin,
            contact.github,
        ]

        required_count = sum(
            bool(value)
            for value in fields
        )

        optional_count = sum(
            bool(value)
            for value in optional_fields
        )

        score = (
            required_count / len(fields)
        ) * 80

        score += (
            optional_count / len(optional_fields)
        ) * 20

        strengths = []
        issues = []
        recommendations = []

        if contact.email:
            strengths.append(
                "Professional email address is present."
            )
        else:
            issues.append(
                "Email address is missing."
            )

        if contact.phone:
            strengths.append(
                "Phone number is present."
            )
        else:
            issues.append(
                "Phone number is missing."
            )

        if contact.linkedin or contact.github:
            strengths.append(
                "Professional profile link is available."
            )
        else:
            recommendations.append(
                "Consider adding LinkedIn or GitHub when relevant."
            )

        return ResumeSectionScore(
            score=round(score, 1),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_summary(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        summary = resume.summary.strip()

        if not summary:
            return ResumeSectionScore(
                score=0,
                issues=[
                    "Professional summary is missing."
                ],
                recommendations=[
                    "Add a concise summary focused on role, expertise and value."
                ],
            )

        words = summary.split()

        score = 50.0
        strengths = []
        issues = []
        recommendations = []

        if 30 <= len(words) <= 120:
            score += 20
            strengths.append(
                "Summary has a reasonable length."
            )
        elif len(words) < 30:
            score -= 10
            issues.append(
                "Summary may be too short to communicate sufficient value."
            )
        else:
            score -= 5
            issues.append(
                "Summary may be longer than necessary."
            )

        lower = summary.lower()

        if any(
            verb in lower
            for verb in self.ACTION_VERBS
        ):
            score += 10
            strengths.append(
                "Summary contains action-oriented language."
            )

        if any(
            metric in lower
            for metric in self.METRIC_PATTERN_TERMS
        ):
            score += 10
            strengths.append(
                "Summary contains measurable evidence."
            )
        else:
            recommendations.append(
                "Where truthful, add measurable outcomes or scope."
            )

        if any(
            term in lower
            for term in self.WEAK_TERMS
        ):
            score -= 10
            issues.append(
                "Summary contains weak or generic wording."
            )

        if resume.headline:
            score += 10
            strengths.append(
                "A distinct professional headline is available."
            )

        return ResumeSectionScore(
            score=max(
                0,
                min(100, score),
            ),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_experience(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        if not resume.experience:
            return ResumeSectionScore(
                score=0,
                issues=[
                    "No work experience entries were detected."
                ],
                recommendations=[
                    "Add relevant professional, internship or practical experience."
                ],
            )

        score = 40.0
        strengths = []
        issues = []
        recommendations = []

        complete_entries = 0
        achievement_bullets = 0
        weak_bullets = 0
        metric_bullets = 0

        for experience in resume.experience:

            if (
                experience.job_title
                and experience.company
            ):
                complete_entries += 1

            bullets = (
                experience.achievements
                or self._split_lines(
                    experience.description
                )
            )

            for bullet in bullets:

                analysis = self._analyze_bullet(
                    bullet
                )

                if analysis["has_action_verb"]:
                    achievement_bullets += 1

                if analysis["has_metric"]:
                    metric_bullets += 1

                if analysis["weak_language"]:
                    weak_bullets += 1

        score += min(
            20,
            complete_entries
            / len(resume.experience)
            * 20,
        )

        total_bullets = (
            achievement_bullets
            if achievement_bullets
            else 0
        )

        if total_bullets:
            score += min(
                15,
                total_bullets * 3,
            )

        if metric_bullets:
            score += min(
                15,
                metric_bullets * 5,
            )

        if weak_bullets:
            score -= min(
                20,
                weak_bullets * 3,
            )

        if complete_entries == len(
            resume.experience
        ):
            strengths.append(
                "Experience entries contain recognizable role and company information."
            )
        else:
            issues.append(
                "Some experience entries appear incomplete."
            )

        if metric_bullets:
            strengths.append(
                f"{metric_bullets} experience bullet(s) contain measurable evidence."
            )
        else:
            issues.append(
                "Experience bullets contain little or no measurable impact evidence."
            )
            recommendations.append(
                "Add truthful metrics such as scale, time saved, users, revenue, performance or efficiency improvements."
            )

        if weak_bullets:
            issues.append(
                f"{weak_bullets} experience bullet(s) use weak or generic language."
            )
            recommendations.append(
                "Replace responsibility-focused wording with action + task + outcome statements."
            )

        return ResumeSectionScore(
            score=max(
                0,
                min(100, score),
            ),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_education(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        if not resume.education:
            return ResumeSectionScore(
                score=0,
                issues=[
                    "Education information was not detected."
                ],
                recommendations=[
                    "Add degree, institution and relevant academic details."
                ],
            )

        complete = 0

        for education in resume.education:
            if (
                education.degree
                and education.institution
            ):
                complete += 1

        score = (
            complete
            / len(resume.education)
        ) * 100

        strengths = []
        issues = []
        recommendations = []

        if complete == len(resume.education):
            strengths.append(
                "Education entries contain degree and institution information."
            )
        else:
            issues.append(
                "Some education entries are incomplete."
            )
            recommendations.append(
                "Verify degree, institution, field of study and dates."
            )

        return ResumeSectionScore(
            score=round(score, 1),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_skills(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        skills = self._normalize_skills(
            resume.skills
            + resume.technical_skills
            + resume.soft_skills
        )

        if not skills:
            return ResumeSectionScore(
                score=0,
                issues=[
                    "No recognizable skills were detected."
                ],
                recommendations=[
                    "Add role-relevant technical and professional skills."
                ],
            )

        score = 40.0
        strengths = []
        issues = []
        recommendations = []

        unique_skills = set(skills)

        if len(unique_skills) >= 5:
            score += 20

        if len(unique_skills) >= 10:
            score += 15

        recognized = unique_skills.intersection(
            self.COMMON_SKILLS
        )

        if recognized:
            score += 15
            strengths.append(
                f"{len(recognized)} recognizable technical/domain skill(s) detected."
            )

        if resume.technical_skills:
            score += 5
            strengths.append(
                "Technical skills are separated from general skills."
            )

        if resume.soft_skills:
            score += 5
            strengths.append(
                "Soft skills are explicitly represented."
            )

        if len(unique_skills) < 5:
            issues.append(
                "Skill coverage appears limited."
            )
            recommendations.append(
                "Add relevant technologies, tools, frameworks and domain skills supported by actual experience."
            )

        return ResumeSectionScore(
            score=max(
                0,
                min(100, score),
            ),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_projects(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        if not resume.projects:
            return ResumeSectionScore(
                score=0,
                issues=[
                    "No projects were detected."
                ],
                recommendations=[
                    "Add relevant projects, especially when professional experience is limited."
                ],
            )

        score = 50.0
        strengths = []
        issues = []
        recommendations = []

        projects_with_tech = 0
        projects_with_outcomes = 0

        for project in resume.projects:

            if project.technologies:
                projects_with_tech += 1

            if (
                project.achievements
                or self._contains_metric(
                    project.description
                )
            ):
                projects_with_outcomes += 1

        score += min(
            20,
            projects_with_tech * 5,
        )

        score += min(
            20,
            projects_with_outcomes * 5,
        )

        if projects_with_tech:
            strengths.append(
                "Projects include technology information."
            )

        if projects_with_outcomes:
            strengths.append(
                "Projects contain some outcome-oriented evidence."
            )
        else:
            issues.append(
                "Project descriptions lack measurable outcomes."
            )
            recommendations.append(
                "Describe project scale, technical contribution and measurable outcomes where truthful."
            )

        return ResumeSectionScore(
            score=max(
                0,
                min(100, score),
            ),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    def _score_certifications(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        if not resume.certifications:
            return ResumeSectionScore(
                score=50,
                recommendations=[
                    "Certifications are optional; add relevant credentials when they strengthen your target profile."
                ],
            )

        score = 70.0
        strengths = []
        recommendations = []

        if any(
            certification.issuer
            for certification in resume.certifications
        ):
            score += 15
            strengths.append(
                "Certification issuers are provided."
            )

        if any(
            certification.credential_url
            for certification in resume.certifications
        ):
            score += 15
            strengths.append(
                "Credential verification links are available."
            )

        return ResumeSectionScore(
            score=min(100, score),
            strengths=strengths,
            recommendations=recommendations,
        )

    def _score_achievements(
        self,
        resume: StructuredResume,
    ) -> ResumeSectionScore:

        if not resume.achievements:
            return ResumeSectionScore(
                score=40,
                recommendations=[
                    "Add meaningful awards, competitions, leadership outcomes or other verifiable achievements when applicable."
                ],
            )

        score = 60.0
        strengths = []
        issues = []
        recommendations = []

        quantified = 0

        for achievement in resume.achievements:

            if self._contains_metric(
                achievement.description
            ):
                quantified += 1

        if quantified:
            score += min(
                40,
                quantified * 10,
            )
            strengths.append(
                "Some achievements contain measurable evidence."
            )
        else:
            issues.append(
                "Achievements lack measurable evidence."
            )

        return ResumeSectionScore(
            score=min(100, score),
            strengths=strengths,
            issues=issues,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # ACHIEVEMENT / BULLET ANALYSIS
    # ------------------------------------------------------------------

    def _analyze_bullet(
        self,
        bullet: str,
    ) -> Dict[str, object]:

        text = bullet.strip()
        lower = text.lower()

        words = lower.split()

        first_word = (
            words[0].strip(".,:;")
            if words
            else ""
        )

        has_action_verb = (
            first_word in self.ACTION_VERBS
            or any(
                f" {verb} "
                in f" {lower} "
                for verb in self.ACTION_VERBS
            )
        )

        has_metric = self._contains_metric(
            text
        )

        weak_language = any(
            term in lower
            for term in self.WEAK_TERMS
        )

        has_technology = bool(
            self._extract_known_skills(
                text
            )
        )

        return {
            "text": text,
            "has_action_verb": has_action_verb,
            "has_metric": has_metric,
            "weak_language": weak_language,
            "has_technology": has_technology,
        }

    def _analyze_achievement_evidence(
        self,
        resume: StructuredResume,
    ) -> Dict[str, object]:

        bullets = []

        for experience in resume.experience:

            experience_bullets = (
                experience.achievements
                or self._split_lines(
                    experience.description
                )
            )

            bullets.extend(
                experience_bullets
            )

        for project in resume.projects:

            bullets.extend(
                project.achievements
            )

            if project.description:
                bullets.append(
                    project.description
                )

        total = len(bullets)

        if not total:
            return {
                "total_bullets": 0,
                "action_oriented": 0,
                "quantified": 0,
                "technology_supported": 0,
                "weak_language": 0,
                "impact_evidence_score": 0,
                "details": [],
            }

        details = []

        action_count = 0
        metric_count = 0
        technology_count = 0
        weak_count = 0

        for bullet in bullets:

            analysis = self._analyze_bullet(
                bullet
            )

            action_count += int(
                analysis["has_action_verb"]
            )

            metric_count += int(
                analysis["has_metric"]
            )

            technology_count += int(
                analysis["has_technology"]
            )

            weak_count += int(
                analysis["weak_language"]
            )

            details.append(
                analysis
            )

        action_ratio = (
            action_count / total
        )

        metric_ratio = (
            metric_count / total
        )

        technology_ratio = (
            technology_count / total
        )

        weak_ratio = (
            weak_count / total
        )

        impact_score = (
            action_ratio * 35
            + metric_ratio * 40
            + technology_ratio * 15
            - weak_ratio * 20
        )

        return {
            "total_bullets": total,
            "action_oriented": action_count,
            "quantified": metric_count,
            "technology_supported": technology_count,
            "weak_language": weak_count,
            "impact_evidence_score": round(
                max(
                    0,
                    min(100, impact_score),
                ),
                1,
            ),
            "details": details,
        }

    # ------------------------------------------------------------------
    # KEYWORD ANALYSIS
    # ------------------------------------------------------------------

    def _analyze_keyword_quality(
        self,
        resume: StructuredResume,
    ) -> Dict[str, object]:

        all_text = " ".join(
            [
                resume.headline or "",
                resume.summary,
                " ".join(resume.skills),
                " ".join(resume.technical_skills),
                " ".join(resume.soft_skills),
                *[
                    experience.description
                    for experience
                    in resume.experience
                ],
                *[
                    project.description
                    for project
                    in resume.projects
                ],
            ]
        ).lower()

        recognized = sorted(
            skill
            for skill in self.COMMON_SKILLS
            if skill in all_text
        )

        skill_list = self._normalize_skills(
            resume.skills
            + resume.technical_skills
        )

        duplicate_skills = self._find_duplicates(
            skill_list
        )

        return {
            "recognized_keywords": recognized,
            "recognized_keyword_count": len(
                recognized
            ),
            "listed_skill_count": len(
                set(skill_list)
            ),
            "duplicate_skills": duplicate_skills,
            "keyword_diversity": round(
                self._keyword_diversity(
                    recognized
                ),
                1,
            ),
        }

    # ------------------------------------------------------------------
    # GLOBAL ANALYSIS
    # ------------------------------------------------------------------

    def _find_missing_sections(
        self,
        resume: StructuredResume,
    ) -> List[str]:

        present = set()

        if resume.summary.strip():
            present.add("summary")

        if resume.experience:
            present.add("experience")

        if resume.education:
            present.add("education")

        if (
            resume.skills
            or resume.technical_skills
            or resume.soft_skills
        ):
            present.add("skills")

        if resume.projects:
            present.add("projects")

        if resume.certifications:
            present.add("certifications")

        if resume.achievements:
            present.add("achievements")

        return sorted(
            self.RECOMMENDED_SECTIONS - present
        )

    def _calculate_overall_score(
        self,
        section_scores: Dict[
            str,
            ResumeSectionScore,
        ],
    ) -> float:

        return sum(
            section_scores[name].score
            * weight
            for name, weight
            in self.SECTION_WEIGHTS.items()
        )

    def _collect_strengths(
        self,
        section_scores: Dict[
            str,
            ResumeSectionScore,
        ],
    ) -> List[str]:

        strengths = []

        for section in section_scores.values():
            strengths.extend(
                section.strengths
            )

        return self._deduplicate(
            strengths
        )

    def _collect_issues(
        self,
        section_scores: Dict[
            str,
            ResumeSectionScore,
        ],
    ) -> List[str]:

        issues = []

        for section in section_scores.values():
            issues.extend(
                section.issues
            )

        return self._deduplicate(
            issues
        )

    def _collect_recommendations(
        self,
        section_scores: Dict[
            str,
            ResumeSectionScore,
        ],
    ) -> List[str]:

        recommendations = []

        for section in section_scores.values():
            recommendations.extend(
                section.recommendations
            )

        return self._deduplicate(
            recommendations
        )

    def _generate_global_recommendations(
        self,
        resume: StructuredResume,
        missing_sections: List[str],
        keyword_quality: Dict[str, object],
        achievement_analysis: Dict[str, object],
    ) -> List[str]:

        recommendations = []

        if "projects" in missing_sections:
            recommendations.append(
                "Consider adding 1–3 highly relevant projects when they strengthen your target role."
            )

        if "achievements" in missing_sections:
            recommendations.append(
                "Add verifiable achievements or measurable outcomes where applicable."
            )

        if achievement_analysis[
            "total_bullets"
        ]:

            if (
                achievement_analysis[
                    "quantified"
                ]
                == 0
            ):
                recommendations.append(
                    "Increase quantified impact across experience and project bullets without inventing metrics."
                )

        if (
            keyword_quality[
                "recognized_keyword_count"
            ]
            < 3
        ):
            recommendations.append(
                "Ensure important role-relevant technologies and domain skills are explicitly represented where genuinely supported."
            )

        if keyword_quality[
            "duplicate_skills"
        ]:
            recommendations.append(
                "Remove duplicate skill entries and normalize equivalent skill names."
            )

        return recommendations

    def _generate_summary(
        self,
        score: float,
        strengths: List[str],
        issues: List[str],
    ) -> str:

        if score >= 85:
            level = "strong"
        elif score >= 70:
            level = "good"
        elif score >= 50:
            level = "developing"
        else:
            level = "needs significant improvement"

        if issues:
            focus = issues[0]
        elif strengths:
            focus = strengths[0]
        else:
            focus = "overall resume structure and content quality"

        return (
            f"The resume currently shows a {level} overall profile "
            f"with an evidence-based score of {round(score, 1)}/100. "
            f"The highest-priority observation is: {focus}"
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _contains_metric(
        self,
        text: str,
    ) -> bool:

        if not text:
            return False

        lower = text.lower()

        if any(
            term in lower
            for term in self.METRIC_PATTERN_TERMS
        ):
            return True

        return bool(
            __import__("re").search(
                r"\b\d+(?:\.\d+)?\s*(?:%|percent|x|k|m|b)\b",
                lower,
            )
        )

    def _extract_known_skills(
        self,
        text: str,
    ) -> Set[str]:

        lower = text.lower()

        return {
            skill
            for skill in self.COMMON_SKILLS
            if skill in lower
        }

    def _normalize_skills(
        self,
        skills: List[str],
    ) -> List[str]:

        normalized = []

        for skill in skills:

            value = " ".join(
                skill.lower().split()
            ).strip()

            if value:
                normalized.append(
                    value
                )

        return list(
            dict.fromkeys(
                normalized
            )
        )

    def _find_duplicates(
        self,
        values: List[str],
    ) -> List[str]:

        seen = set()
        duplicates = []

        for value in values:

            if value in seen:
                duplicates.append(
                    value
                )

            seen.add(value)

        return list(
            dict.fromkeys(
                duplicates
            )
        )

    def _keyword_diversity(
        self,
        keywords: List[str],
    ) -> float:

        if not keywords:
            return 0.0

        unique = len(
            set(keywords)
        )

        return (
            unique
            / len(keywords)
            * 100
        )

    def _split_lines(
        self,
        text: str,
    ) -> List[str]:

        if not text:
            return []

        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

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