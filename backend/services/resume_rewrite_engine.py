from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from backend.schemas.resume import (
    ResumeExperience,
    ResumeProject,
    StructuredResume,
)


@dataclass
class RewriteSuggestion:
    section: str
    source_text: str
    issue: str
    target_requirement: str
    available_evidence: List[str] = field(default_factory=list)
    suggested_rewrite: str = ""
    confidence: int = 0
    evidence_status: str = "SUPPORTED"


@dataclass
class ResumeRewriteAnalysis:
    overall_readiness_score: float
    suggestions: List[RewriteSuggestion]
    priority_actions: List[str]
    safety_notes: List[str]
    summary: str


class ResumeRewriteEngine:
    """
    Evidence-first resume rewrite planner.

    The engine improves clarity, action orientation, and job alignment
    using ONLY information already supported by the resume.

    It must never invent:
    - skills
    - technologies
    - metrics
    - achievements
    - employers
    - job titles
    - qualifications
    - responsibilities
    """

    WEAK_STARTERS = {
        "worked on",
        "worked with",
        "helped with",
        "helped",
        "assisted with",
        "responsible for",
        "involved in",
        "participated in",
        "handled",
        "did",
        "made",
        "used",
    }

    STRONG_ACTION_VERBS = {
        "built",
        "developed",
        "designed",
        "implemented",
        "engineered",
        "created",
        "automated",
        "optimized",
        "deployed",
        "integrated",
        "architected",
        "analyzed",
        "led",
        "delivered",
        "improved",
        "launched",
        "configured",
        "maintained",
        "tested",
        "researched",
    }

    METRIC_PATTERN = (
        r"\b(?:"
        r"\d+(?:\.\d+)?%"
        r"|"
        r"\d+(?:\.\d+)?[KMB]"
        r"|"
        r"\d+\+"
        r"|"
        r"\d+(?:\.\d+)?"
        r")\b"
    )

    def analyze(
        self,
        resume: StructuredResume,
        target_requirements: List[str] | None = None,
    ) -> ResumeRewriteAnalysis:
        requirements = self._clean_requirements(
            target_requirements or []
        )

        suggestions: List[RewriteSuggestion] = []

        # ----------------------------------------------------------
        # EXPERIENCE
        # ----------------------------------------------------------

        for experience in resume.experience:
            for bullet in experience.achievements:
                suggestion = self._analyze_bullet(
                    bullet=bullet,
                    section="experience",
                    requirements=requirements,
                    technologies=experience.technologies,
                    contextual_evidence=self._experience_context(
                        experience
                    ),
                )

                if suggestion:
                    suggestions.append(suggestion)

            if experience.description:
                for sentence in self._split_sentences(
                    experience.description
                ):
                    suggestion = self._analyze_bullet(
                        bullet=sentence,
                        section="experience",
                        requirements=requirements,
                        technologies=experience.technologies,
                        contextual_evidence=self._experience_context(
                            experience
                        ),
                    )

                    if suggestion:
                        suggestions.append(suggestion)

        # ----------------------------------------------------------
        # PROJECTS
        # ----------------------------------------------------------

        for project in resume.projects:
            for bullet in project.achievements:
                suggestion = self._analyze_bullet(
                    bullet=bullet,
                    section="projects",
                    requirements=requirements,
                    technologies=project.technologies,
                    contextual_evidence=self._project_context(
                        project
                    ),
                )

                if suggestion:
                    suggestions.append(suggestion)

            if project.description:
                for sentence in self._split_sentences(
                    project.description
                ):
                    suggestion = self._analyze_bullet(
                        bullet=sentence,
                        section="projects",
                        requirements=requirements,
                        technologies=project.technologies,
                        contextual_evidence=self._project_context(
                            project
                        ),
                    )

                    if suggestion:
                        suggestions.append(suggestion)

        suggestions = self._deduplicate_suggestions(
            suggestions
        )

        readiness = self._calculate_readiness(
            resume,
            suggestions,
        )

        priority_actions = self._build_priority_actions(
            resume,
            suggestions,
            requirements,
        )

        safety_notes = [
            "Never add a technology unless it is genuinely supported by the candidate.",
            "Never fabricate or invent metrics, scale, ownership, achievements, qualifications, or responsibilities.",
            "Every rewrite must remain traceable to evidence already present in the resume.",
            "A stronger action verb is acceptable only when it accurately describes the original work.",
            "Missing evidence must be surfaced as a gap, not disguised through stronger wording.",
        ]

        summary = self._build_summary(
            readiness,
            suggestions,
        )

        return ResumeRewriteAnalysis(
            overall_readiness_score=round(
                readiness,
                1,
            ),
            suggestions=suggestions,
            priority_actions=priority_actions,
            safety_notes=safety_notes,
            summary=summary,
        )

    # ==============================================================
    # BULLET ANALYSIS
    # ==============================================================

    def _analyze_bullet(
        self,
        bullet: str,
        section: str,
        requirements: List[str],
        technologies: List[str],
        contextual_evidence: List[str],
    ) -> RewriteSuggestion | None:
        text = self._clean_text(bullet)

        if not text:
            return None

        normalized = self._normalize(text)

        issues: List[str] = []

        if self._has_weak_starter(normalized):
            issues.append(
                "Weak or generic opening verb"
            )

        if not self._has_action_verb(normalized):
            issues.append(
                "Action is not clearly expressed"
            )

        if len(text.split()) < 7:
            issues.append(
                "Bullet is too short to communicate strong evidence"
            )

        if self._has_generic_language(normalized):
            issues.append(
                "Language is generic rather than outcome-focused"
            )

        target_requirement = self._best_requirement(
            text,
            requirements,
        )

        if not issues and target_requirement:
            issues.append(
                "Relevant evidence could be aligned more explicitly "
                "with the target role"
            )

        if not issues:
            return None

        evidence = self._build_evidence(
            bullet=text,
            technologies=technologies,
            contextual_evidence=contextual_evidence,
        )

        suggested_rewrite = self._build_safe_rewrite(
            text=text,
            target_requirement=target_requirement,
            technologies=technologies,
        )

        confidence = self._calculate_confidence(
            text=text,
            evidence=evidence,
            target_requirement=target_requirement,
        )

        return RewriteSuggestion(
            section=section,
            source_text=text,
            issue="; ".join(issues),
            target_requirement=target_requirement,
            available_evidence=evidence,
            suggested_rewrite=suggested_rewrite,
            confidence=confidence,
            evidence_status=(
                "SUPPORTED"
                if evidence
                else "LIMITED_EVIDENCE"
            ),
        )

    # ==============================================================
    # SAFE REWRITE
    # ==============================================================

    def _build_safe_rewrite(
        self,
        text: str,
        target_requirement: str,
        technologies: List[str],
    ) -> str:
        original = self._clean_text(text)

        body = self._remove_weak_prefix(
            original
        )

        first_word = (
            body.split()[0].lower()
            if body.split()
            else ""
        )

        # Never produce things like:
        # "Developed built backend APIs."
        if first_word in self.STRONG_ACTION_VERBS:
            rewritten = body
        else:
            verb = self._choose_safe_action_verb(
                original
            )

            rewritten = (
                f"{verb} {self._lowercase_first_word(body)}"
            )

        # Add a supported technology only if it is explicitly present
        # in the original bullet and isn't already in the rewrite.
        supported_technologies = [
            technology
            for technology in technologies
            if technology
            and self._contains_concept(
                original,
                technology,
            )
        ]

        missing_supported_technologies = [
            technology
            for technology in supported_technologies
            if not self._contains_concept(
                rewritten,
                technology,
            )
        ]

        if missing_supported_technologies:
            technology_text = ", ".join(
                missing_supported_technologies[:3]
            )

            rewritten = (
                f"{rewritten.rstrip('.')} "
                f"using {technology_text}"
            )

        # Only connect a target requirement where the original bullet
        # already contains meaningful evidence for it.
        if (
            target_requirement
            and self._can_safely_add_requirement(
                target_requirement,
                original,
            )
            and not self._contains_concept(
                rewritten,
                target_requirement,
            )
        ):
            rewritten = (
                f"{rewritten.rstrip('.')} "
                f"for {target_requirement}"
            )

        rewritten = self._fix_grammar(
            rewritten
        )

        return (
            rewritten.rstrip(" .")
            + "."
        )

    def _remove_weak_prefix(
        self,
        text: str,
    ) -> str:
        normalized = self._normalize(text)

        weak_prefixes = [
            "worked on ",
            "worked with ",
            "helped with ",
            "helped ",
            "assisted with ",
            "responsible for ",
            "involved in ",
            "participated in ",
            "handled ",
            "did ",
            "made ",
            "used ",
        ]

        for prefix in weak_prefixes:
            if normalized.startswith(prefix):
                return text[len(prefix):].strip()

        return text.strip()

    def _choose_safe_action_verb(
        self,
        original: str,
    ) -> str:
        text = self._normalize(original)

        if any(
            marker in text
            for marker in (
                "api",
                "backend",
                "service",
                "application",
            )
        ):
            return "Developed"

        if any(
            marker in text
            for marker in (
                "design",
                "designed",
                "architecture",
            )
        ):
            return "Designed"

        if "autom" in text:
            return "Automated"

        if "integrat" in text:
            return "Integrated"

        if any(
            marker in text
            for marker in (
                "deploy",
                "container",
                "docker",
            )
        ):
            return "Deployed"

        if any(
            marker in text
            for marker in (
                "test",
                "debug",
            )
        ):
            return "Tested"

        if any(
            marker in text
            for marker in (
                "analy",
                "research",
            )
        ):
            return "Analyzed"

        if any(
            marker in text
            for marker in (
                "database",
                "sql",
                "postgres",
                "mysql",
            )
        ):
            return "Designed"

        return "Implemented"

    def _lowercase_first_word(
        self,
        text: str,
    ) -> str:
        if not text:
            return text

        return (
            text[0].lower()
            + text[1:]
        )

    def _fix_grammar(
        self,
        text: str,
    ) -> str:
        replacements = {
            "aI": "AI",
            "aI-powered": "AI-powered",
            "A i": "AI",
            "lLm": "LLM",
            "docker": "Docker",
            "python": "Python",
            "fastapi": "FastAPI",
            "postgresql": "PostgreSQL",
        }

        result = text

        for old, new in replacements.items():
            result = result.replace(
                old,
                new,
            )

        # Normalize duplicate "using" phrases.
        result = re.sub(
            r"\busing\s+([^,.]+)\s+using\s+\1\b",
            r"using \1",
            result,
            flags=re.IGNORECASE,
        )

        # Normalize accidental verb duplication.
        result = re.sub(
            r"^(Developed|Designed|Implemented|Deployed|"
            r"Analyzed|Tested)\s+"
            r"(built|developed|designed|implemented|"
            r"deployed|analyzed|tested)\b\s*",
            lambda match: f"{match.group(1)} ",
            result,
            flags=re.IGNORECASE,
        )

        result = re.sub(
            r"\s+",
            " ",
            result,
        )

        return result.strip()

    # ==============================================================
    # EVIDENCE
    # ==============================================================

    def _build_evidence(
        self,
        bullet: str,
        technologies: List[str],
        contextual_evidence: List[str],
    ) -> List[str]:
        evidence: List[str] = []

        if bullet:
            evidence.append(
                f"Original resume statement: {bullet}"
            )

        for technology in technologies:
            if self._contains_concept(
                bullet,
                technology,
            ):
                evidence.append(
                    f"Technology explicitly supported: {technology}"
                )

        for item in contextual_evidence:
            if item:
                evidence.append(
                    f"Context from resume: {item}"
                )

        return self._deduplicate(
            evidence
        )[:6]

    def _calculate_confidence(
        self,
        text: str,
        evidence: List[str],
        target_requirement: str,
    ) -> int:
        score = 45

        if evidence:
            score += 20

        if self._has_action_verb(
            self._normalize(text)
        ):
            score += 10

        if self._has_metric(text):
            score += 10

        if target_requirement:
            score += 10

        return min(
            95,
            score,
        )

    # ==============================================================
    # REQUIREMENT MATCHING
    # ==============================================================

    def _best_requirement(
        self,
        text: str,
        requirements: List[str],
    ) -> str:
        if not requirements:
            return ""

        text_tokens = set(
            self._tokens(text)
        )

        best_requirement = ""
        best_score = 0.0

        for requirement in requirements:
            requirement_tokens = set(
                self._tokens(requirement)
            )

            if not requirement_tokens:
                continue

            overlap = (
                text_tokens
                & requirement_tokens
            )

            score = (
                len(overlap)
                / len(requirement_tokens)
            )

            if score > best_score:
                best_score = score
                best_requirement = requirement

        return (
            best_requirement
            if best_score >= 0.25
            else ""
        )

    def _can_safely_add_requirement(
        self,
        requirement: str,
        text: str,
    ) -> bool:
        requirement_tokens = set(
            self._tokens(requirement)
        )

        text_tokens = set(
            self._tokens(text)
        )

        return bool(
            requirement_tokens
            & text_tokens
        )

    # ==============================================================
    # READINESS
    # ==============================================================

    def _calculate_readiness(
        self,
        resume: StructuredResume,
        suggestions: List[RewriteSuggestion],
    ) -> float:
        score = 100.0

        weak_count = sum(
            "Weak or generic opening verb"
            in item.issue
            for item in suggestions
        )

        short_count = sum(
            "too short"
            in item.issue.lower()
            for item in suggestions
        )

        limited_count = sum(
            item.evidence_status
            == "LIMITED_EVIDENCE"
            for item in suggestions
        )

        score -= min(
            25,
            weak_count * 4,
        )

        score -= min(
            20,
            short_count * 3,
        )

        score -= min(
            15,
            limited_count * 2,
        )

        if not resume.summary:
            score -= 10

        if not resume.experience:
            score -= 15

        if not (
            resume.skills
            or resume.technical_skills
        ):
            score -= 15

        if not resume.projects:
            score -= 5

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    # ==============================================================
    # PRIORITIES
    # ==============================================================

    def _build_priority_actions(
        self,
        resume: StructuredResume,
        suggestions: List[RewriteSuggestion],
        requirements: List[str],
    ) -> List[str]:
        priorities: List[str] = []

        if any(
            "Weak or generic opening verb"
            in item.issue
            for item in suggestions
        ):
            priorities.append(
                "Rewrite generic experience and project bullets "
                "with stronger, truthful action verbs."
            )

        if any(
            "too short"
            in item.issue.lower()
            for item in suggestions
        ):
            priorities.append(
                "Expand short bullets with the real task, "
                "technology, and outcome already supported by the resume."
            )

        if any(
            item.evidence_status
            == "LIMITED_EVIDENCE"
            for item in suggestions
        ):
            priorities.append(
                "Strengthen missing evidence before rewriting; "
                "do not compensate for gaps by inventing claims."
            )

        if requirements:
            priorities.append(
                "Align the strongest verified resume evidence "
                "with the requirements of the target job."
            )

        if not resume.summary:
            priorities.append(
                "Add a concise professional summary based on "
                "verified experience and skills."
            )

        if not resume.projects:
            priorities.append(
                "Consider adding genuinely relevant projects "
                "supported by real work."
            )

        return self._deduplicate(
            priorities
        )[:8]

    # ==============================================================
    # CONTEXT
    # ==============================================================

    def _experience_context(
        self,
        experience: ResumeExperience,
    ) -> List[str]:
        context: List[str] = []

        if experience.job_title:
            context.append(
                f"Role: {experience.job_title}"
            )

        if experience.company:
            context.append(
                f"Company: {experience.company}"
            )

        if experience.technologies:
            context.append(
                "Technologies: "
                + ", ".join(
                    experience.technologies
                )
            )

        return context

    def _project_context(
        self,
        project: ResumeProject,
    ) -> List[str]:
        context: List[str] = []

        if project.name:
            context.append(
                f"Project: {project.name}"
            )

        if project.technologies:
            context.append(
                "Technologies: "
                + ", ".join(
                    project.technologies
                )
            )

        return context

    # ==============================================================
    # TEXT HELPERS
    # ==============================================================

    def _contains_concept(
        self,
        text: str,
        concept: str,
    ) -> bool:
        """
        Case-insensitive concept matching.

        Handles:
        - normal phrases: "machine learning"
        - punctuation: "C++"
        - common spacing variations
        """

        text_normalized = self._normalize(text)
        concept_normalized = self._normalize(concept)

        if not concept_normalized:
            return False

        # First try an exact normalized phrase.
        if concept_normalized in text_normalized:
            return True

        # Then use token overlap for punctuation-heavy concepts.
        concept_tokens = set(
            self._tokens(concept_normalized)
        )

        text_tokens = set(
            self._tokens(text_normalized)
        )

        if not concept_tokens:
            return False

        return concept_tokens.issubset(
            text_tokens
        )

    def _has_weak_starter(
        self,
        text: str,
    ) -> bool:
        return any(
            text.startswith(prefix)
            for prefix in self.WEAK_STARTERS
        )

    def _has_action_verb(
        self,
        text: str,
    ) -> bool:
        words = text.split()

        if not words:
            return False

        return (
            words[0].lower()
            in self.STRONG_ACTION_VERBS
        )

    def _has_generic_language(
        self,
        text: str,
    ) -> bool:
        generic_terms = {
            "various",
            "things",
            "multiple tasks",
            "different tasks",
            "helped",
            "worked on",
            "responsible",
        }

        return any(
            term in text
            for term in generic_terms
        )

    def _has_metric(
        self,
        text: str,
    ) -> bool:
        return re.search(
            self.METRIC_PATTERN,
            text,
        ) is not None

    def _split_sentences(
        self,
        text: str,
    ) -> List[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        return [
            sentence.strip(" -•")
            for sentence in sentences
            if sentence.strip()
        ]

    def _tokens(
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
        ]

    def _normalize(
        self,
        text: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.lower(),
        ).strip()

    def _clean_text(
        self,
        text: str,
    ) -> str:
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip(
            " -•\t\r\n"
        )

    def _clean_requirements(
        self,
        requirements: List[str],
    ) -> List[str]:
        result = []

        for requirement in requirements:
            cleaned = self._clean_text(
                requirement
            )

            if cleaned:
                result.append(
                    cleaned
                )

        return self._deduplicate(
            result
        )

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

    def _deduplicate_suggestions(
        self,
        suggestions: List[RewriteSuggestion],
    ) -> List[RewriteSuggestion]:
        seen = set()
        result = []

        for suggestion in suggestions:
            key = (
                suggestion.section.lower(),
                suggestion.source_text.lower(),
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(suggestion)

        return result

    def _build_summary(
        self,
        readiness: float,
        suggestions: List[RewriteSuggestion],
    ) -> str:
        limited = sum(
            item.evidence_status
            == "LIMITED_EVIDENCE"
            for item in suggestions
        )

        return (
            f"The resume has a rewrite readiness score of "
            f"{readiness:.1f}/100 with "
            f"{len(suggestions)} candidate improvements identified. "
            f"{limited} suggestions have limited evidence. "
            "The engine prioritizes truthful improvement over "
            "keyword stuffing or invented achievements."
        )