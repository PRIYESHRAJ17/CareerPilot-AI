from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List

from langchain_core.tools import tool

from backend.schemas.resume import StructuredResume
from backend.services.llm_resume_reasoner import (
    LLMResumeReasoner,
)
from backend.services.resume_rewrite_engine import (
    RewriteSuggestion,
)


# ============================================================
# SERVICES
# ============================================================

llm_resume_reasoner = LLMResumeReasoner()


# ============================================================
# SERIALIZATION
# ============================================================

def _serialize(value: Any) -> Any:
    """
    Convert CareerPilot domain objects into JSON-compatible data.
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

    if isinstance(value, (list, tuple, set)):
        return [
            _serialize(item)
            for item in value
        ]

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


# ============================================================
# INPUT BUILDERS
# ============================================================

def _build_rewrite_suggestion(
    suggestion_data: Dict[str, Any],
) -> RewriteSuggestion:
    """
    Reconstruct the canonical Week 3 RewriteSuggestion object
    from serialized workflow state.
    """

    if not isinstance(
        suggestion_data,
        dict,
    ):
        raise TypeError(
            "suggestion must be a dictionary."
        )

    return RewriteSuggestion(
        section=str(
            suggestion_data.get(
                "section",
                "",
            )
        ),
        source_text=str(
            suggestion_data.get(
                "source_text",
                "",
            )
        ),
        issue=str(
            suggestion_data.get(
                "issue",
                "",
            )
        ),
        target_requirement=str(
            suggestion_data.get(
                "target_requirement",
                "",
            )
        ),
        available_evidence=list(
            suggestion_data.get(
                "available_evidence",
                [],
            )
            or []
        ),
        suggested_rewrite=str(
            suggestion_data.get(
                "suggested_rewrite",
                "",
            )
        ),
        confidence=int(
            suggestion_data.get(
                "confidence",
                0,
            )
            or 0
        ),
        evidence_status=str(
            suggestion_data.get(
                "evidence_status",
                "SUPPORTED",
            )
        ),
    )


def _build_structured_resume(
    resume_data: Dict[str, Any],
) -> StructuredResume:
    """
    Reconstruct StructuredResume from serialized workflow state.
    """

    if not isinstance(
        resume_data,
        dict,
    ):
        raise TypeError(
            "resume must be a dictionary."
        )

    return StructuredResume.model_validate(
        resume_data
    )


# ============================================================
# LOW-LEVEL VALIDATION CAPABILITY
# ============================================================

def validate_rewrite(
    resume_data: Dict[str, Any],
    suggestion_data: Dict[str, Any],
    generated_text: str,
) -> Dict[str, Any]:
    """
    Validate one generated resume rewrite against the original
    resume and deterministic source suggestion.
    """

    if not isinstance(
        generated_text,
        str,
    ):
        raise TypeError(
            "generated_text must be a string."
        )

    resume = _build_structured_resume(
        resume_data
    )

    suggestion = _build_rewrite_suggestion(
        suggestion_data
    )

    result = llm_resume_reasoner.validate_candidate(
        resume=resume,
        source_suggestion=suggestion,
        generated_text=generated_text,
    )

    return _serialize(result)


def validate_rewrite_batch(
    resume_data: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate multiple generated rewrite candidates.

    Each candidate must contain:
        source_text
        rewritten_text
        section
        target_requirement
        evidence
        confidence

    The function reconstructs the source RewriteSuggestion from
    each candidate and validates the generated text independently.
    """

    if not isinstance(
        candidates,
        list,
    ):
        raise TypeError(
            "candidates must be a list."
        )

    validated_candidates = []

    accepted_count = 0
    rejected_count = 0

    for candidate in candidates:
        if not isinstance(
            candidate,
            dict,
        ):
            raise TypeError(
                "Each candidate must be a dictionary."
            )

        suggestion_data = {
            "section": candidate.get(
                "section",
                "",
            ),
            "source_text": candidate.get(
                "source_text",
                "",
            ),
            "issue": candidate.get(
                "issue",
                "",
            ),
            "target_requirement": candidate.get(
                "target_requirement",
                "",
            ),
            "available_evidence": candidate.get(
                "evidence",
                candidate.get(
                    "available_evidence",
                    [],
                ),
            ),
            "suggested_rewrite": candidate.get(
                "suggested_rewrite",
                "",
            ),
            "confidence": candidate.get(
                "confidence",
                0,
            ),
            "evidence_status": candidate.get(
                "evidence_status",
                "SUPPORTED",
            ),
        }

        validation = validate_rewrite(
            resume_data=resume_data,
            suggestion_data=suggestion_data,
            generated_text=str(
                candidate.get(
                    "rewritten_text",
                    "",
                )
            ),
        )

        accepted = (
            validation.get("status")
            == "ACCEPTED"
        )

        if accepted:
            accepted_count += 1
        else:
            rejected_count += 1

        validated_candidates.append(
            {
                "source_text": candidate.get(
                    "source_text",
                    "",
                ),
                "rewritten_text": candidate.get(
                    "rewritten_text",
                    "",
                ),
                "section": candidate.get(
                    "section",
                    "",
                ),
                "target_requirement": candidate.get(
                    "target_requirement",
                    "",
                ),
                "confidence": candidate.get(
                    "confidence",
                    0,
                ),
                "validation_status": validation.get(
                    "status"
                ),
                "validation_issues": validation.get(
                    "issues",
                    [],
                ),
            }
        )

    return {
        "candidates": validated_candidates,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "total_count": len(
            validated_candidates
        ),
    }


# ============================================================
# LANGCHAIN TOOLS
# ============================================================

@tool
def validate_resume_rewrite(
    resume: Dict[str, Any],
    suggestion: Dict[str, Any],
    generated_text: str,
) -> Dict[str, Any]:
    """
    Validate one resume rewrite against verified resume evidence.

    Use this tool before a generated rewrite is accepted into
    the final CareerPilot response.
    """

    return validate_rewrite(
        resume_data=resume,
        suggestion_data=suggestion,
        generated_text=generated_text,
    )


@tool
def validate_resume_rewrites(
    resume: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate multiple generated resume rewrites and return
    accepted/rejected counts plus per-candidate issues.
    """

    return validate_rewrite_batch(
        resume_data=resume,
        candidates=candidates,
    )


# ============================================================
# GENERIC OUTPUT VALIDATION
# ============================================================

def validate_required_fields(
    payload: Dict[str, Any],
    required_fields: List[str],
) -> Dict[str, Any]:
    """
    Deterministically verify that an agent/tool payload contains
    all required non-empty fields.

    This is useful for validating shared-state objects before
    downstream agents consume them.
    """

    if not isinstance(
        payload,
        dict,
    ):
        return {
            "valid": False,
            "missing_fields": [
                "payload"
            ],
            "message": (
                "Payload must be a dictionary."
            ),
        }

    missing_fields = []

    for field_name in required_fields:
        value = payload.get(
            field_name
        )

        if value is None:
            missing_fields.append(
                field_name
            )
            continue

        if isinstance(
            value,
            str,
        ) and not value.strip():
            missing_fields.append(
                field_name
            )
            continue

        if isinstance(
            value,
            (list, dict),
        ) and not value:
            missing_fields.append(
                field_name
            )

    return {
        "valid": not missing_fields,
        "missing_fields": missing_fields,
        "message": (
            "All required fields are present."
            if not missing_fields
            else (
                "Required fields are missing: "
                + ", ".join(missing_fields)
            )
        ),
    }


@tool
def validate_agent_output(
    payload: Dict[str, Any],
    required_fields: List[str],
) -> Dict[str, Any]:
    """
    Check whether an agent output contains all required fields
    before it is written into shared workflow state.
    """

    return validate_required_fields(
        payload=payload,
        required_fields=required_fields,
    )