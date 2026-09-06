from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set

from backend.schemas.resume import StructuredResume
from backend.services.resume_rewrite_engine import RewriteSuggestion


@dataclass
class LLMRewriteCandidate:
    source_text: str
    rewritten_text: str
    section: str
    target_requirement: str
    evidence: List[str] = field(default_factory=list)
    confidence: int = 0
    validation_status: str = "PENDING"
    validation_issues: List[str] = field(default_factory=list)


@dataclass
class LLMResumeReasoningResult:
    provider: str
    model: str
    candidates: List[LLMRewriteCandidate]
    accepted_count: int
    rejected_count: int
    summary: str
    safety_notes: List[str]


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider cannot generate output."""


class LLMResumeReasoner:
    """
    Evidence-constrained LLM reasoning layer for resume rewrites.

    Production pipeline:

        Structured Resume
               ↓
        Deterministic RewriteSuggestion
               ↓
        Evidence-rich LLM prompt
               ↓
        Ollama / Qwen3.5 9B
               ↓
        Output normalization
               ↓
        Evidence / hallucination validator
               ↓
        ACCEPTED / REJECTED

    Provider modes:

        LLM_PROVIDER=ollama
            Uses the local Ollama server.

        LLM_PROVIDER=none
            Explicit deterministic mode for tests/fallback workflows.

    Default production configuration:

        provider = ollama
        model    = qwen3.5:9b
    """

    DEFAULT_PROVIDER = "ollama"
    DEFAULT_MODEL = "qwen3.5:9b"
    DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
    DEFAULT_TIMEOUT = 180
    DEFAULT_TEMPERATURE = 0.2
    DEFAULT_NUM_PREDICT = 220
    DEFAULT_MAX_CANDIDATES = 3

    KNOWN_TECHNICAL_TERMS = {
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
        "fastapi",
        "flask",
        "django",
        "spring",
        "spring boot",
        "node",
        "node.js",
        "express",
        "react",
        "react.js",
        "reactjs",
        "next.js",
        "nextjs",
        "angular",
        "vue",
        "html",
        "css",
        "tailwind",
        "graphql",
        "rest api",
        "rest",
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "mongodb",
        "redis",
        "sqlite",
        "oracle",
        "dynamodb",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "sklearn",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "ai",
        "llm",
        "llms",
        "generative ai",
        "genai",
        "nlp",
        "computer vision",
        "langchain",
        "langgraph",
        "git",
        "github",
        "terraform",
        "linux",
        "ci/cd",
        "github actions",
        "figma",
        "photoshop",
        "adobe photoshop",
        "illustrator",
        "adobe illustrator",
        "tableau",
        "power bi",
        "excel",
    }

    IMPACT_WORDS = {
        "reduced",
        "increased",
        "improved",
        "optimized",
        "scaled",
        "accelerated",
        "saved",
        "grew",
        "boosted",
    }

    SAFE_IMPACT_WORDS = {
        "optimized",
        "improved",
    }

    STOPWORDS = {
        "the",
        "and",
        "for",
        "with",
        "using",
        "use",
        "worked",
        "work",
        "helped",
        "help",
        "assist",
        "assisted",
        "handled",
        "used",
        "made",
        "did",
        "involved",
        "participated",
        "built",
        "developed",
        "designed",
        "implemented",
        "created",
        "engineered",
        "on",
        "in",
        "to",
        "of",
        "a",
        "an",
        "is",
        "was",
        "were",
        "be",
        "this",
        "that",
        "by",
    }

    TECH_ALIASES = {
        "llm": {
            "llm",
            "llms",
            "large language model",
            "large language models",
        },
        "llms": {
            "llm",
            "llms",
            "large language model",
            "large language models",
        },
        "react": {
            "react",
            "react.js",
            "reactjs",
        },
        "react.js": {
            "react",
            "react.js",
            "reactjs",
        },
        "reactjs": {
            "react",
            "react.js",
            "reactjs",
        },
        "postgres": {
            "postgres",
            "postgresql",
        },
        "postgresql": {
            "postgres",
            "postgresql",
        },
        "golang": {
            "go",
            "golang",
        },
        "go": {
            "go",
            "golang",
        },
        "sklearn": {
            "sklearn",
            "scikit-learn",
        },
        "scikit-learn": {
            "sklearn",
            "scikit-learn",
        },
        "genai": {
            "genai",
            "generative ai",
        },
        "generative ai": {
            "genai",
            "generative ai",
        },
        "photoshop": {
            "photoshop",
            "adobe photoshop",
        },
        "adobe photoshop": {
            "photoshop",
            "adobe photoshop",
        },
        "illustrator": {
            "illustrator",
            "adobe illustrator",
        },
        "adobe illustrator": {
            "illustrator",
            "adobe illustrator",
        },
    }

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.provider = (
            provider
            or os.getenv(
                "LLM_PROVIDER",
                self.DEFAULT_PROVIDER,
            )
        ).strip().lower()

        self.model = (
            model
            or os.getenv(
                "LLM_MODEL",
                self.DEFAULT_MODEL,
            )
        ).strip()

        self.ollama_url = os.getenv(
            "OLLAMA_URL",
            self.DEFAULT_OLLAMA_URL,
        ).strip()

        self.timeout = self._read_int_env(
            "LLM_TIMEOUT",
            self.DEFAULT_TIMEOUT,
            minimum=10,
            maximum=600,
        )

        self.temperature = self._read_float_env(
            "LLM_TEMPERATURE",
            self.DEFAULT_TEMPERATURE,
            minimum=0.0,
            maximum=1.0,
        )

        self.num_predict = self._read_int_env(
            "LLM_NUM_PREDICT",
            self.DEFAULT_NUM_PREDICT,
            minimum=32,
            maximum=1024,
        )

        self.max_candidates = self._read_int_env(
            "LLM_MAX_CANDIDATES",
            self.DEFAULT_MAX_CANDIDATES,
            minimum=1,
            maximum=20,
        )

    # ============================================================
    # ENVIRONMENT HELPERS
    # ============================================================

    @staticmethod
    def _read_int_env(
        name: str,
        default: int,
        *,
        minimum: int,
        maximum: int,
    ) -> int:
        raw = os.getenv(name)

        if raw is None:
            return default

        try:
            value = int(raw)
        except ValueError:
            return default

        return max(
            minimum,
            min(maximum, value),
        )

    @staticmethod
    def _read_float_env(
        name: str,
        default: float,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        raw = os.getenv(name)

        if raw is None:
            return default

        try:
            value = float(raw)
        except ValueError:
            return default

        return max(
            minimum,
            min(maximum, value),
        )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def analyze(
        self,
        resume: StructuredResume,
        rewrite_suggestions: List[RewriteSuggestion],
    ) -> LLMResumeReasoningResult:
        if not rewrite_suggestions:
            return LLMResumeReasoningResult(
                provider=self.provider,
                model=self.model,
                candidates=[],
                accepted_count=0,
                rejected_count=0,
                summary=(
                    "No rewrite candidates were supplied "
                    "to the reasoning layer."
                ),
                safety_notes=self._safety_notes(),
            )

        candidates: List[LLMRewriteCandidate] = []

        selected_suggestions = rewrite_suggestions[
            : self.max_candidates
        ]

        for suggestion in selected_suggestions:
            try:
                candidate = self._generate_candidate(
                    resume=resume,
                    suggestion=suggestion,
                )

                validation = self.validate_candidate(
                    resume=resume,
                    source_suggestion=suggestion,
                    generated_text=candidate.rewritten_text,
                )

                candidate.validation_status = (
                    validation["status"]
                )

                candidate.validation_issues = list(
                    validation["issues"]
                )

            except LLMProviderError as exc:
                candidate = LLMRewriteCandidate(
                    source_text=suggestion.source_text,
                    rewritten_text="",
                    section=suggestion.section,
                    target_requirement=suggestion.target_requirement,
                    evidence=list(
                        suggestion.available_evidence
                    ),
                    confidence=0,
                    validation_status="REJECTED",
                    validation_issues=[
                        f"LLM generation failed: {exc}"
                    ],
                )

            candidate.confidence = max(
                0,
                min(
                    95,
                    suggestion.confidence,
                ),
            )

            if candidate.validation_status == "REJECTED":
                candidate.confidence = min(
                    candidate.confidence,
                    30,
                )

            candidates.append(candidate)

        accepted_count = sum(
            candidate.validation_status == "ACCEPTED"
            for candidate in candidates
        )

        rejected_count = len(candidates) - accepted_count

        skipped_count = max(
            0,
            len(rewrite_suggestions) - len(selected_suggestions),
        )

        summary = (
            f"AI reasoning evaluated "
            f"{len(candidates)} rewrite candidates. "
            f"{accepted_count} passed evidence validation "
            f"and {rejected_count} were rejected."
        )

        if skipped_count:
            summary += (
                f" {skipped_count} additional deterministic "
                f"candidates were not sent to the local LLM."
            )

        return LLMResumeReasoningResult(
            provider=self.provider,
            model=self.model,
            candidates=candidates,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            summary=summary,
            safety_notes=self._safety_notes(),
        )

    # ============================================================
    # GENERATION
    # ============================================================

    def _generate_candidate(
        self,
        resume: StructuredResume,
        suggestion: RewriteSuggestion,
    ) -> LLMRewriteCandidate:
        deterministic_text = (
            suggestion.suggested_rewrite
            or ""
        ).strip()

        if self.provider in {
            "",
            "none",
            "disabled",
        }:
            text = deterministic_text
        elif self.provider == "ollama":
            text = self._provider_generate(
                resume=resume,
                suggestion=suggestion,
            ).strip()
        else:
            raise LLMProviderError(
                f"Unsupported LLM provider '{self.provider}'. "
                f"Supported providers: ollama, none."
            )

        return LLMRewriteCandidate(
            source_text=suggestion.source_text,
            rewritten_text=text,
            section=suggestion.section,
            target_requirement=suggestion.target_requirement,
            evidence=list(
                suggestion.available_evidence
            ),
            confidence=max(
                0,
                min(
                    95,
                    suggestion.confidence,
                ),
            ),
        )

    def _provider_generate(
        self,
        resume: StructuredResume,
        suggestion: RewriteSuggestion,
    ) -> str:
        prompt = self._build_ollama_prompt(
            resume=resume,
            suggestion=suggestion,
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            },
        }

        request_data = json.dumps(
            payload
        ).encode("utf-8")

        request = urllib.request.Request(
            self.ollama_url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                raw_body = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

        except urllib.error.HTTPError as exc:
            body = ""

            try:
                body = exc.read().decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                pass

            message = (
                f"Ollama returned HTTP {exc.code}."
            )

            if body:
                message += f" {body[:500]}"

            raise LLMProviderError(
                message
            ) from exc

        except urllib.error.URLError as exc:
            raise LLMProviderError(
                "Could not connect to Ollama at "
                f"{self.ollama_url}. "
                "Make sure Ollama is running."
            ) from exc

        except TimeoutError as exc:
            raise LLMProviderError(
                f"Ollama generation timed out after "
                f"{self.timeout} seconds."
            ) from exc

        except OSError as exc:
            raise LLMProviderError(
                f"Unable to reach Ollama: {exc}"
            ) from exc

        try:
            result = json.loads(
                raw_body
            )
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                "Ollama returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise LLMProviderError(
                "Ollama returned an unexpected response shape."
            )

        generated_text = str(
            result.get("response")
            or ""
        ).strip()

        if not generated_text:
            generated_text = str(
                result.get("thinking")
                or ""
            ).strip()

        cleaned = self._clean_model_output(
            generated_text
        )

        if not cleaned:
            raise LLMProviderError(
                "Ollama returned an empty generation."
            )

        return cleaned

    def _build_ollama_prompt(
        self,
        resume: StructuredResume,
        suggestion: RewriteSuggestion,
    ) -> str:
        resume_text = self._resume_text(
            resume
        )

        evidence = [
            item.strip()
            for item in (
                suggestion.available_evidence
                or []
            )
            if item and item.strip()
        ]

        evidence_block = "\n".join(
            f"- {item}"
            for item in evidence
        )

        return f"""
You are CareerPilot's evidence-constrained resume rewriting engine.

Your job is to rewrite ONE resume statement professionally using ONLY
facts supported by the supplied candidate evidence.

NON-NEGOTIABLE RULES:
1. Never invent facts.
2. Never invent metrics or percentages.
3. Never invent technologies.
4. Never invent ownership, scale, leadership, responsibilities, employers,
   customers, deployments, achievements, or outcomes.
5. Never infer a technology merely because another technology is related.
6. Never convert a target job requirement into candidate experience.
7. Preserve the original meaning.
8. You may improve grammar, clarity, concision and action wording.
9. Return ONLY the rewritten resume statement.
10. Do not return explanations, bullets, labels, Markdown, or quotation marks.

TARGET REQUIREMENT:
{suggestion.target_requirement or "General resume quality"}

ORIGINAL RESUME STATEMENT:
{suggestion.source_text}

VERIFIED EVIDENCE:
{evidence_block or "- No additional evidence supplied."}

STRUCTURED RESUME CONTEXT:
{resume_text[:8000]}

DETERMINISTIC SAFE DRAFT:
{suggestion.suggested_rewrite}

Produce ONE concise professional resume statement using only verified evidence.
""".strip()

    @staticmethod
    def _clean_model_output(
        text: str,
    ) -> str:
        cleaned = str(
            text or ""
        ).strip()

        # Remove common Qwen thinking wrappers.
        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()

        cleaned = re.sub(
            r"^<think>.*$",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()

        cleaned = re.sub(
            r"^</think>\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Remove accidental Markdown code fences.
        cleaned = re.sub(
            r"^```(?:text|markdown)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Remove accidental surrounding quotes.
        if (
            len(cleaned) >= 2
            and cleaned[0] == '"'
            and cleaned[-1] == '"'
        ):
            cleaned = cleaned[1:-1].strip()

        # Avoid multi-paragraph explanations.
        lines = [
            line.strip()
            for line in cleaned.splitlines()
            if line.strip()
        ]

        if len(lines) > 1:
            cleaned = " ".join(lines)

        return cleaned

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_candidate(
        self,
        resume: StructuredResume,
        source_suggestion: RewriteSuggestion,
        generated_text: str,
    ) -> Dict[str, Any]:
        issues: List[str] = []

        original = self._normalize(
            source_suggestion.source_text
        )

        generated = self._normalize(
            generated_text
        )

        # --------------------------------------------------------
        # 1. OUTPUT VALIDITY
        # --------------------------------------------------------

        if not generated:
            return {
                "status": "REJECTED",
                "issues": [
                    "Generated rewrite is empty."
                ],
            }

        if len(generated.split()) < 3:
            return {
                "status": "REJECTED",
                "issues": [
                    "Generated rewrite is too short "
                    "to be useful."
                ],
            }

        if not source_suggestion.available_evidence:
            issues.append(
                "No source evidence was supplied "
                "for the rewrite."
            )

        # --------------------------------------------------------
        # 2. SEMANTIC OVERLAP
        # --------------------------------------------------------

        original_tokens = set(
            self._meaningful_tokens(
                original
            )
        )

        generated_tokens = set(
            self._meaningful_tokens(
                generated
            )
        )

        if original_tokens:
            overlap = (
                len(
                    original_tokens
                    & generated_tokens
                )
                / len(original_tokens)
            )

            if overlap < 0.40:
                issues.append(
                    "Generated rewrite changes too much "
                    "of the original meaning."
                )

        # --------------------------------------------------------
        # 3. NUMERIC CLAIM PROTECTION
        # --------------------------------------------------------

        original_numbers = set(
            self._extract_numbers(
                original
            )
        )

        generated_numbers = set(
            self._extract_numbers(
                generated
            )
        )

        new_numbers = (
            generated_numbers
            - original_numbers
        )

        if new_numbers:
            issues.append(
                "Generated rewrite introduces "
                "unsupported numeric claims: "
                + ", ".join(
                    sorted(
                        new_numbers
                    )
                )
            )

        # --------------------------------------------------------
        # 4. TECHNOLOGY PROTECTION
        # --------------------------------------------------------

        resume_text = self._resume_text(
            resume
        )

        evidence_text = " ".join(
            source_suggestion.available_evidence
            or []
        )

        support_text = " ".join(
            [
                resume_text,
                original,
                self._normalize(
                    evidence_text
                ),
            ]
        )

        generated_terms = set(
            self._extract_known_technical_terms(
                generated
            )
        )

        unsupported_terms = sorted(
            term
            for term in generated_terms
            if not self._concept_is_supported(
                generated_term=term,
                support_text=support_text,
                resume=resume,
            )
        )

        if unsupported_terms:
            issues.append(
                "Generated rewrite introduces "
                "unsupported technical terms: "
                + ", ".join(
                    unsupported_terms
                )
            )

        # --------------------------------------------------------
        # 5. IMPACT CLAIM PROTECTION
        # --------------------------------------------------------

        issues.extend(
            self._detect_unsupported_impact_claims(
                original=original,
                generated=generated,
            )
        )

        # --------------------------------------------------------
        # 6. EXPLANATION LEAK PROTECTION
        # --------------------------------------------------------

        explanation_markers = [
            "the candidate",
            "according to the evidence",
            "this rewrite",
            "i cannot",
            "i can",
            "because the",
            "note:",
            "explanation:",
        ]

        if any(
            marker in generated
            for marker in explanation_markers
        ):
            issues.append(
                "Generated output contains explanation-like "
                "content instead of only the resume rewrite."
            )

        # --------------------------------------------------------
        # 7. FINAL RESULT
        # --------------------------------------------------------

        unique_issues = list(
            dict.fromkeys(
                issues
            )
        )

        return {
            "status": (
                "ACCEPTED"
                if not unique_issues
                else "REJECTED"
            ),
            "issues": unique_issues,
        }

    # ============================================================
    # TECHNOLOGY SUPPORT
    # ============================================================

    def _concept_is_supported(
        self,
        generated_term: str,
        support_text: str,
        resume: StructuredResume,
    ) -> bool:
        normalized_term = self._normalize(
            generated_term
        )

        possible_terms = self.TECH_ALIASES.get(
            normalized_term,
            {
                normalized_term
            },
        )

        for candidate in possible_terms:
            if self._contains_concept(
                support_text,
                candidate,
            ):
                return True

        for concept in self._verified_resume_concepts(
            resume
        ):
            if normalized_term == concept:
                return True

            if concept in possible_terms:
                return True

        return False

    def _extract_known_technical_terms(
        self,
        text: str,
    ) -> List[str]:
        found: List[str] = []

        for term in sorted(
            self.KNOWN_TECHNICAL_TERMS,
            key=len,
            reverse=True,
        ):
            if self._contains_concept(
                text,
                term,
            ):
                found.append(term)

        return found

    def _verified_resume_concepts(
        self,
        resume: StructuredResume,
    ) -> Set[str]:
        values: List[str] = []

        values.extend(
            resume.skills
            or []
        )

        values.extend(
            resume.technical_skills
            or []
        )

        for experience in (
            resume.experience
            or []
        ):
            values.extend(
                experience.technologies
                or []
            )

        for project in (
            resume.projects
            or []
        ):
            values.extend(
                project.technologies
                or []
            )

        return {
            self._normalize(value)
            for value in values
            if value
        }

    # ============================================================
    # IMPACT PROTECTION
    # ============================================================

    def _detect_unsupported_impact_claims(
        self,
        original: str,
        generated: str,
    ) -> List[str]:
        original_impacts = {
            word
            for word in self.IMPACT_WORDS
            if re.search(
                rf"\b{re.escape(word)}\b",
                original,
            )
        }

        generated_impacts = {
            word
            for word in self.IMPACT_WORDS
            if re.search(
                rf"\b{re.escape(word)}\b",
                generated,
            )
        }

        newly_added = (
            generated_impacts
            - original_impacts
        )

        issues: List[str] = []

        for impact in sorted(
            newly_added
        ):
            if impact in self.SAFE_IMPACT_WORDS:
                continue

            issues.append(
                "Generated rewrite introduces "
                "a stronger impact claim without "
                f"matching source evidence: {impact}"
            )

        return issues

    # ============================================================
    # TEXT MATCHING
    # ============================================================

    def _contains_concept(
        self,
        text: str,
        concept: str,
    ) -> bool:
        text = self._normalize(
            text
        )

        concept = self._normalize(
            concept
        )

        if not concept:
            return False

        escaped = re.escape(
            concept
        )

        if re.search(
            rf"(?<![a-z0-9+#])"
            rf"{escaped}"
            rf"(?![a-z0-9+#])",
            text,
        ):
            return True

        if len(concept) <= 2:
            return False

        concept_tokens = set(
            self._meaningful_tokens(
                concept
            )
        )

        text_tokens = set(
            self._meaningful_tokens(
                text
            )
        )

        return bool(
            concept_tokens
            and concept_tokens.issubset(
                text_tokens
            )
        )

    def _meaningful_tokens(
        self,
        text: str,
    ) -> List[str]:
        tokens = re.findall(
            r"[a-zA-Z0-9+#.-]+",
            self._normalize(
                text
            ),
        )

        return [
            token
            for token in tokens
            if len(token) >= 3
            and token not in self.STOPWORDS
        ]

    def _extract_numbers(
        self,
        text: str,
    ) -> List[str]:
        return re.findall(
            r"\b\d+(?:\.\d+)?%?\b",
            text,
        )

    def _normalize(
        self,
        text: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            str(text or "").lower(),
        ).strip()

    # ============================================================
    # RESUME TEXT
    # ============================================================

    def _resume_text(
        self,
        resume: StructuredResume,
    ) -> str:
        parts: List[str] = []

        parts.append(
            resume.headline
            or ""
        )

        parts.append(
            resume.summary
            or ""
        )

        parts.extend(
            resume.skills
            or []
        )

        parts.extend(
            resume.technical_skills
            or []
        )

        parts.extend(
            resume.soft_skills
            or []
        )

        for experience in (
            resume.experience
            or []
        ):
            parts.extend(
                [
                    experience.job_title
                    or "",
                    experience.company
                    or "",
                    experience.location
                    or "",
                    experience.description
                    or "",
                ]
            )

            parts.extend(
                experience.achievements
                or []
            )

            parts.extend(
                experience.technologies
                or []
            )

        for project in (
            resume.projects
            or []
        ):
            parts.extend(
                [
                    project.name
                    or "",
                    project.description
                    or "",
                ]
            )

            parts.extend(
                project.technologies
                or []
            )

            parts.extend(
                project.achievements
                or []
            )

        for education in (
            resume.education
            or []
        ):
            parts.extend(
                [
                    education.degree
                    or "",
                    education.institution
                    or "",
                    education.field_of_study
                    or "",
                ]
            )

        return self._normalize(
            " ".join(parts)
        )

    # ============================================================
    # SAFETY
    # ============================================================

    def _safety_notes(
        self,
    ) -> List[str]:
        provider_note = (
            f"Local LLM provider: {self.provider}."
        )

        if self.provider == "ollama":
            provider_note += (
                f" Model: {self.model}."
            )

        return [
            provider_note,
            "Generated rewrites must remain grounded in verified resume evidence.",
            "Unsupported metrics and achievements are rejected.",
            "Unsupported technologies are rejected.",
            "Major semantic drift from the original evidence is rejected.",
            "Polished wording never authorizes fabrication of experience.",
            "Failed local LLM generations are rejected rather than silently accepted.",
        ]

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(
        self,
        result: LLMResumeReasoningResult,
    ) -> Dict[str, Any]:
        return asdict(
            result
        )


llm_resume_reasoner = LLMResumeReasoner()