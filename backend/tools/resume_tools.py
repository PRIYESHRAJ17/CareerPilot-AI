from __future__ import annotations

import base64
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from backend.schemas.resume import StructuredResume
from backend.services.ats_analyzer import ATSAnalyzer
from backend.services.job_resume_analyzer import JobResumeAnalyzer
from backend.services.llm_resume_reasoner import LLMResumeReasoner
from backend.services.resume_intelligence import ResumeIntelligenceEngine
from backend.services.resume_parser import ResumeParser
from backend.services.resume_rewrite_engine import ResumeRewriteEngine
from backend.services.resume_structurer import ResumeStructurer


# ============================================================
# EXISTING WEEK 3 SERVICES
# ============================================================

resume_parser = ResumeParser()
resume_structurer = ResumeStructurer()
resume_intelligence_engine = ResumeIntelligenceEngine()
ats_analyzer = ATSAnalyzer()
job_resume_analyzer = JobResumeAnalyzer()
resume_rewrite_engine = ResumeRewriteEngine()
llm_resume_reasoner = LLMResumeReasoner()


# ============================================================
# SERIALIZATION HELPERS
# ============================================================


def _serialize(value: Any) -> Any:
    """
    Convert CareerPilot domain objects into JSON-compatible data.

    Supports:
    - Pydantic models
    - dataclasses
    - dictionaries
    - lists / tuples
    - primitive values
    """

    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if is_dataclass(value):
        return asdict(value)

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _serialize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ============================================================
# RESUME INPUT
# ============================================================


def _decode_resume_bytes(
    resume_base64: str,
) -> bytes:
    """
    Decode a base64-encoded PDF payload.
    """

    if not resume_base64 or not resume_base64.strip():
        raise ValueError(
            "resume_base64 must not be empty."
        )

    try:
        resume_bytes = base64.b64decode(
            resume_base64,
            validate=True,
        )
    except Exception as exc:
        raise ValueError(
            "resume_base64 is not valid base64."
        ) from exc

    if not resume_bytes:
        raise ValueError(
            "Decoded resume content is empty."
        )

    return resume_bytes


# ============================================================
# PARSE RESUME
# ============================================================


def parse_resume_bytes(
    resume_bytes: bytes,
) -> Dict[str, Any]:
    """
    Parse PDF resume bytes using the existing Week 3 parser.
    """

    parsed = resume_parser.parse(
        resume_bytes
    )

    return {
        "text": parsed.text,
        "pages": parsed.pages,
        "page_count": parsed.page_count,
        "sections": parsed.sections,
    }


@tool
def parse_resume(
    resume_base64: str,
) -> Dict[str, Any]:
    """
    Parse a base64-encoded PDF resume.

    Use this when the workflow needs raw resume text,
    page information, or detected resume sections.
    """

    resume_bytes = _decode_resume_bytes(
        resume_base64
    )

    return parse_resume_bytes(
        resume_bytes
    )


# ============================================================
# STRUCTURE RESUME
# ============================================================


def structure_resume_bytes(
    resume_bytes: bytes,
) -> Dict[str, Any]:
    """
    Parse and structure a PDF resume into CareerPilot's
    canonical StructuredResume model.
    """

    parsed = resume_parser.parse(
        resume_bytes
    )

    structured = resume_structurer.structure(
        parsed
    )

    return _serialize(
        structured
    )


@tool
def structure_resume(
    resume_base64: str,
) -> Dict[str, Any]:
    """
    Parse and convert a PDF resume into the canonical
    CareerPilot StructuredResume representation.
    """

    resume_bytes = _decode_resume_bytes(
        resume_base64
    )

    return structure_resume_bytes(
        resume_bytes
    )


# ============================================================
# RESUME INTELLIGENCE
# ============================================================


def analyze_structured_resume(
    resume: StructuredResume,
) -> Dict[str, Any]:
    """
    Run deterministic Week 3 resume intelligence.
    """

    result = resume_intelligence_engine.analyze(
        resume
    )

    return _serialize(
        result
    )


@tool
def analyze_resume(
    structured_resume: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze a structured resume using deterministic
    resume intelligence.
    """

    resume = StructuredResume.model_validate(
        structured_resume
    )

    return analyze_structured_resume(
        resume
    )


# ============================================================
# ATS ANALYSIS
# ============================================================


def analyze_ats_resume(
    resume: StructuredResume,
    job_description: str,
) -> Dict[str, Any]:
    """
    Run deterministic ATS analysis.
    """

    if not job_description or not job_description.strip():
        raise ValueError(
            "job_description must not be empty."
        )

    result = ats_analyzer.analyze(
        resume=resume,
        job_description=job_description,
    )

    return _serialize(
        result
    )


@tool
def analyze_ats(
    structured_resume: Dict[str, Any],
    job_description: str,
) -> Dict[str, Any]:
    """
    Compare a structured resume against a job description
    using the deterministic ATS analyzer.
    """

    resume = StructuredResume.model_validate(
        structured_resume
    )

    return analyze_ats_resume(
        resume,
        job_description,
    )


# ============================================================
# JOB-SPECIFIC RESUME ANALYSIS
# ============================================================


def analyze_resume_for_job(
    resume: StructuredResume,
    job_description: str,
) -> Dict[str, Any]:
    """
    Run the deterministic job-specific resume analyzer.
    """

    if not job_description or not job_description.strip():
        raise ValueError(
            "job_description must not be empty."
        )

    result = job_resume_analyzer.analyze(
        resume=resume,
        job_description=job_description,
    )

    return _serialize(
        result
    )


@tool
def analyze_job_fit(
    structured_resume: Dict[str, Any],
    job_description: str,
) -> Dict[str, Any]:
    """
    Analyze how well the candidate's resume fits a
    specific job using evidence-based deterministic logic.
    """

    resume = StructuredResume.model_validate(
        structured_resume
    )

    return analyze_resume_for_job(
        resume,
        job_description,
    )


# ============================================================
# EVIDENCE-FIRST REWRITE
# ============================================================


def generate_rewrite_analysis(
    resume: StructuredResume,
    target_requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate deterministic evidence-first rewrite suggestions.
    """

    result = resume_rewrite_engine.analyze(
        resume=resume,
        target_requirements=target_requirements or [],
    )

    return _serialize(
        result
    )


@tool
def generate_resume_rewrites(
    structured_resume: Dict[str, Any],
    target_requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate evidence-first resume rewrite candidates.

    Rewrites are based only on information already present
    in the candidate's resume.
    """

    resume = StructuredResume.model_validate(
        structured_resume
    )

    return generate_rewrite_analysis(
        resume,
        target_requirements,
    )


# ============================================================
# LLM RESUME REASONING
# ============================================================


def run_llm_resume_reasoning(
    resume: StructuredResume,
    rewrite_suggestions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run the existing Week 3 evidence-constrained LLM reasoner.
    """

    from backend.services.resume_rewrite_engine import (
        RewriteSuggestion,
    )

    suggestions = []

    for item in rewrite_suggestions:
        if not isinstance(item, dict):
            raise TypeError(
                "Each rewrite suggestion must be a dictionary."
            )

        suggestions.append(
            RewriteSuggestion(
                section=str(
                    item.get(
                        "section",
                        "",
                    )
                ),
                source_text=str(
                    item.get(
                        "source_text",
                        "",
                    )
                ),
                issue=str(
                    item.get(
                        "issue",
                        "",
                    )
                ),
                target_requirement=str(
                    item.get(
                        "target_requirement",
                        "",
                    )
                ),
                available_evidence=list(
                    item.get(
                        "available_evidence",
                        [],
                    )
                    or []
                ),
                suggested_rewrite=str(
                    item.get(
                        "suggested_rewrite",
                        "",
                    )
                ),
                confidence=int(
                    item.get(
                        "confidence",
                        0,
                    )
                    or 0
                ),
                evidence_status=str(
                    item.get(
                        "evidence_status",
                        "SUPPORTED",
                    )
                ),
            )
        )

    result = llm_resume_reasoner.analyze(
        resume=resume,
        rewrite_suggestions=suggestions,
    )

    return _serialize(
        result
    )


@tool
def reason_over_resume_rewrites(
    structured_resume: Dict[str, Any],
    rewrite_suggestions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Use the configured local LLM to reason over deterministic
    evidence-first rewrite candidates.
    """

    resume = StructuredResume.model_validate(
        structured_resume
    )

    return run_llm_resume_reasoning(
        resume=resume,
        rewrite_suggestions=rewrite_suggestions,
    )


# ============================================================
# COMPLETE RESUME PIPELINE
# ============================================================


def run_resume_pipeline(
    resume_bytes: bytes,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete deterministic + LLM resume intelligence
    pipeline using the existing Week 3 services.

    Pipeline:

        PDF
         ↓
        Parsing
         ↓
        Structuring
         ↓
        Resume Intelligence
         ↓
        Optional ATS Analysis
         ↓
        Optional Job Fit Analysis
         ↓
        Optional Evidence-First Rewrite
         ↓
        Optional LLM Reasoning
    """

    parsed = resume_parser.parse(
        resume_bytes
    )

    structured = resume_structurer.structure(
        parsed
    )

    resume_intelligence = (
        resume_intelligence_engine.analyze(
            structured
        )
    )

    result: Dict[str, Any] = {
        "parsed_resume": _serialize(
            parsed
        ),
        "structured_resume": _serialize(
            structured
        ),
        "resume_intelligence": _serialize(
            resume_intelligence
        ),
    }

    if job_description:
        ats_result = ats_analyzer.analyze(
            resume=structured,
            job_description=job_description,
        )

        job_fit_result = job_resume_analyzer.analyze(
            resume=structured,
            job_description=job_description,
        )

        requirements = []

        for requirement in (
            getattr(
                ats_result,
                "requirements",
                [],
            )
            or []
        ):
            text = getattr(
                requirement,
                "text",
                "",
            )

            if text:
                requirements.append(
                    str(text)
                )

        rewrite_result = resume_rewrite_engine.analyze(
            resume=structured,
            target_requirements=requirements,
        )

        rewrite_suggestions = [
            _serialize(item)
            for item in (
                rewrite_result.suggestions
                or []
            )
        ]

        llm_result = llm_resume_reasoner.analyze(
            resume=structured,
            rewrite_suggestions=[
                type(
                    "RewriteSuggestionProxy",
                    (),
                    {
                        "section": item.get(
                            "section",
                            "",
                        ),
                        "source_text": item.get(
                            "source_text",
                            "",
                        ),
                        "issue": item.get(
                            "issue",
                            "",
                        ),
                        "target_requirement": item.get(
                            "target_requirement",
                            "",
                        ),
                        "available_evidence": item.get(
                            "available_evidence",
                            [],
                        ),
                        "suggested_rewrite": item.get(
                            "suggested_rewrite",
                            "",
                        ),
                        "confidence": item.get(
                            "confidence",
                            0,
                        ),
                        "evidence_status": item.get(
                            "evidence_status",
                            "SUPPORTED",
                        ),
                    },
                )()
                for item in rewrite_suggestions
            ],
        )

        result.update(
            {
                "ats_analysis": _serialize(
                    ats_result
                ),
                "job_fit_analysis": _serialize(
                    job_fit_result
                ),
                "rewrite_analysis": _serialize(
                    rewrite_result
                ),
                "llm_reasoning": _serialize(
                    llm_result
                ),
            }
        )

    return result


@tool
def run_resume_intelligence_pipeline(
    resume_base64: str,
    job_description: str = "",
) -> Dict[str, Any]:
    """
    Run the complete CareerPilot resume intelligence pipeline.

    This is the high-level resume capability intended for
    agentic orchestration.
    """

    resume_bytes = _decode_resume_bytes(
        resume_base64
    )

    return run_resume_pipeline(
        resume_bytes=resume_bytes,
        job_description=job_description or None,
    )