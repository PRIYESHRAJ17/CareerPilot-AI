from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable


Validator = Callable[[str], tuple[float, list[str]]]


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    name: str
    category: str
    weight: float
    prompt: str
    validator: Validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def _has_explicit_negation(text: str, term: str) -> bool:
    lowered = text.lower()

    patterns = [
        f"not {term}",
        f"no {term}",
        f"{term} not provided",
        f"{term} not verified",
        f"{term} is not verified",
        f"{term} is not provided",
        f"{term} is unverified",
        f"no explicit evidence of {term}",
        f"no evidence of {term}",
        f"cannot confirm {term}",
        f"cannot verify {term}",
        f"{term} is not established",
        f"{term} not established",
        f"{term} is unsupported",
        f"{term} is absent",
        f"{term} explicitly absent",
        f"no mention of {term}",
        f"no {term} experience",
        f"{term} experience is absent",
        f"{term} experience is not verified",
        f"{term} experience not verified",
        f"no verified {term} experience",
        f"not listed: {term}",
        f"{term} not listed",
        f"{term} is not listed",
        f"does not mention {term}",
        f"doesn't mention {term}",
        f"no listed {term}",
    ]

    return any(pattern in lowered for pattern in patterns)


def _contains_section(text: str, phrases: list[str]) -> bool:
    return _contains_any(text, phrases)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def validate_job_fit(text: str) -> tuple[float, list[str]]:
    """
    CP-01 evaluates evidence-grounded job-fit reasoning.

    Scoring rewards:
    - correct evidence classification,
    - calibrated reasoning,
    - explicit gap identification,
    - concrete next actions.

    The validator intentionally accepts multiple natural-language ways
    of expressing "not verified" or "absent".
    """
    lowered = text.lower()
    score = 100.0
    notes: list[str] = []

    # ------------------------------------------------------------------
    # 1. Unsupported inference checks
    # ------------------------------------------------------------------

    forbidden_claims = [
        "b.tech proves dsa",
        "b.tech implies dsa",
        "b.tech demonstrates dsa",
        "b.tech proves strong programming fundamentals",
        "b.tech implies strong programming fundamentals",
        "b.tech demonstrates strong programming fundamentals",
        "almost certainly implemented",
        "almost certainly have",
        "proves they understand",
        "proves dsa",
        "proves production",
        "proves cloud",
        "fastapi proves cloud",
        "python proves cloud",
        "b.tech guarantees",
        "degree proves",
        "degree demonstrates dsa",
        "project proves production",
        "projects prove production",
        "project proves cloud",
        "projects prove cloud",
        "would likely succeed in an interview",
        "likely succeed in an interview",
        "will likely succeed in an interview",
        "guaranteed interview",
        "guaranteed to succeed",
        "certain to succeed",
        "definitely pass",
        "obvious hire",
        "ideal candidate",
        "perfect fit",
        "guaranteed fit",
    ]

    violations = 0

    for phrase in forbidden_claims:
        if phrase in lowered:
            violations += 1
            notes.append(
                f"Unsupported inference detected: '{phrase}'."
            )

    score -= min(violations * 15, 60)

    # ------------------------------------------------------------------
    # 2. Mandatory verified matches
    # ------------------------------------------------------------------

    if "python" in lowered:
        notes.append("Recognized Python as explicitly verified.")
    else:
        score -= 5
        notes.append("Python was not recognized.")

    if "c++" in lowered or "cpp" in lowered:
        notes.append("Recognized C++ as explicitly verified.")
    else:
        score -= 5
        notes.append("C++ was not recognized.")

    if "git" in lowered:
        if _has_explicit_negation(lowered, "git"):
            score -= 10
            notes.append("Git was incorrectly weakened or negated.")
        else:
            notes.append("Recognized Git as explicitly verified.")
    else:
        score -= 5
        notes.append("Git was not recognized.")

    # ------------------------------------------------------------------
    # 3. FastAPI / REST reasoning
    # ------------------------------------------------------------------

    fastapi_present = "fastapi" in lowered

    rest_present = _contains_any(
        lowered,
        [
            "rest api",
            "rest apis",
            "restful",
            "rest api exposure",
            "api exposure",
            "api development",
            "api capability",
            "api capabilities",
        ],
    )

    if fastapi_present:
        if rest_present:
            notes.append(
                "Correctly connects FastAPI to REST/API evidence."
            )
        else:
            score -= 3
            notes.append(
                "FastAPI was mentioned but its REST/API relevance was unclear."
            )
    else:
        score -= 5
        notes.append("FastAPI was not recognized.")

    # ------------------------------------------------------------------
    # 4. DSA must be NOT VERIFIED
    # ------------------------------------------------------------------

    dsa_present = _contains_any(
        lowered,
        [
            "dsa",
            "data structures and algorithms",
            "data structures",
            "algorithms",
        ],
    )

    if not dsa_present:
        score -= 15
        notes.append("Did not discuss DSA.")
    else:
        dsa_negative = _contains_any(
            lowered,
            [
                "not verified",
                "not explicitly listed",
                "not explicitly provided",
                "not provided",
                "unverified",
                "missing",
                "no explicit evidence",
                "no evidence",
                "cannot confirm",
                "cannot verify",
                "not established",
                "cannot infer",
                "cannot be inferred",
                "not proven",
            ],
        )

        if dsa_negative or _has_explicit_negation(
            lowered, "dsa"
        ):
            notes.append("Correctly treats DSA as NOT VERIFIED.")
        else:
            score -= 15
            notes.append(
                "DSA was discussed without clearly marking it unverified."
            )

    # ------------------------------------------------------------------
    # 5. Cloud must be NOT VERIFIED
    # ------------------------------------------------------------------

    cloud_present = _contains_any(
        lowered,
        [
            "cloud",
            "aws",
            "azure",
            "gcp",
        ],
    )

    if not cloud_present:
        score -= 10
        notes.append("Did not discuss cloud.")
    else:
        cloud_negative = _contains_any(
            lowered,
            [
                "cloud is not verified",
                "cloud not verified",
                "cloud is unverified",
                "cloud unverified",
                "cloud not provided",
                "cloud is not provided",
                "cloud missing",
                "cloud is missing",
                "no cloud experience",
                "no explicit evidence of cloud",
                "no evidence of cloud",
                "no mention of cloud",
                "cloud is not mentioned",
                "cloud not mentioned",
                "cloud is not listed",
                "cloud not listed",
                "cloud deployment is not listed",
                "no cloud deployment",
                "no cloud deployment is listed",
                "no cloud usage",
                "no cloud platform exposure",
                "no aws experience",
                "no azure experience",
                "no gcp experience",
                "aws not verified",
                "azure not verified",
                "gcp not verified",
                "aws is not verified",
                "azure is not verified",
                "gcp is not verified",
                "no aws evidence",
                "no azure evidence",
                "no gcp evidence",
                "no explicit evidence of aws",
                "no explicit evidence of azure",
                "no explicit evidence of gcp",
                "aws not listed",
                "azure not listed",
                "gcp not listed",
                "no mention of aws",
                "no mention of azure",
                "no mention of gcp",
                "does not mention aws",
                "does not mention azure",
                "does not mention gcp",
                "doesn't mention aws",
                "doesn't mention azure",
                "doesn't mention gcp",
                "python knowledge does not imply cloud",
                "python does not imply cloud",
                "fastapi does not imply cloud",
                "fastapi does not prove cloud",
                "cloud cannot be inferred",
            ],
        )

        natural_negation = (
            _has_explicit_negation(lowered, "cloud")
            or _has_explicit_negation(lowered, "aws")
            or _has_explicit_negation(lowered, "azure")
            or _has_explicit_negation(lowered, "gcp")
        )

        if cloud_negative or natural_negation:
            notes.append("Correctly treats cloud as NOT VERIFIED.")
        else:
            score -= 10
            notes.append(
                "Cloud was mentioned without clearly marking it unverified."
            )

    # ------------------------------------------------------------------
    # 6. Internship must be EXPLICITLY ABSENT
    # ------------------------------------------------------------------

    internship_present = "internship" in lowered

    if not internship_present:
        score -= 10
        notes.append("Did not discuss internship status.")
    else:
        internship_absent = _contains_any(
            lowered,
            [
                "no professional internship",
                "no internship experience",
                "internship is explicitly absent",
                "internship explicitly absent",
                "professional internship is absent",
                "professional internship experience is absent",
                "no professional internship experience",
                "no prior internship",
                "internship experience is absent",
                "internship experience: absent",
                "no internship history",
                "absence of internship",
            ],
        )

        natural_negation = _has_explicit_negation(
            lowered,
            "internship",
        )

        if internship_absent or natural_negation:
            notes.append(
                "Correctly treats internship as EXPLICITLY ABSENT."
            )
        else:
            score -= 10
            notes.append(
                "Internship was discussed without clearly identifying it as absent."
            )

    # ------------------------------------------------------------------
    # 7. Production-scale experience must be EXPLICITLY ABSENT
    # ------------------------------------------------------------------

    production_present = _contains_any(
        lowered,
        [
            "production-scale",
            "production scale",
            "production experience",
            "production-scale experience",
            "production environment",
            "at scale",
            "real-world production",
        ],
    )

    if not production_present:
        score -= 10
        notes.append(
            "Did not explicitly discuss production-scale experience."
        )
    else:
        production_negative = _contains_any(
            lowered,
            [
                "no verified production",
                "no production experience",
                "production experience is absent",
                "production-scale experience is absent",
                "production-scale experience is not verified",
                "production-scale is not verified",
                "production is not verified",
                "production not verified",
                "production-scale not verified",
                "not verified in production",
                "not verified at production scale",
                "no verified production-scale experience",
                "no production-scale experience",
                "production experience is not established",
                "production-scale experience is not established",
                "no evidence of production",
                "no explicit evidence of production",
                "projects do not prove production",
                "project does not prove production",
                "projects do not demonstrate production",
                "project does not demonstrate production",
                "having projects does not prove production",
            ],
        )

        natural_negation = _contains_any(
            lowered,
            [
                "does not prove production",
                "doesn't prove production",
                "cannot prove production",
                "cannot infer production",
                "cannot be inferred from projects",
                "projects do not establish production",
                "project does not establish production",
            ],
        )

        if production_negative or natural_negation:
            notes.append(
                "Correctly treats production-scale experience as EXPLICITLY ABSENT."
            )
        else:
            score -= 10
            notes.append(
                "Production was mentioned without clearly identifying the candidate's "
                "production-scale experience as absent."
            )

    # ------------------------------------------------------------------
    # 8. Required reasoning sections
    # ------------------------------------------------------------------

    required_sections = {
        "overall fit assessment": [
            "overall fit assessment",
            "overall assessment",
            "fit assessment",
        ],
        "verified matches": [
            "verified strong matches",
            "verified matches",
            "strong matches",
        ],
        "partially supported": [
            "partially supported",
            "partial matches",
            "partially supported matches",
        ],
        "not verified": [
            "not verified requirements",
            "not verified",
        ],
        "explicitly absent": [
            "explicitly absent requirements",
            "explicitly absent",
        ],
        "top three gaps": [
            "top three gaps",
            "top 3 gaps",
            "three gaps",
            "3 gaps",
        ],
        "next actions": [
            "three concrete next actions",
            "3 concrete next actions",
            "next actions",
            "next steps",
            "action plan",
        ],
    }

    for section_name, phrases in required_sections.items():
        if _contains_section(lowered, phrases):
            notes.append(
                f"Includes {section_name} reasoning."
            )
        else:
            score -= 5
            notes.append(
                f"Missing {section_name} section."
            )

    # ------------------------------------------------------------------
    # 9. Three concrete actions
    # ------------------------------------------------------------------

    numbered_action_hits = sum(
        1
        for pattern in [
            r"\n\s*1[\.\):\-]",
            r"\n\s*2[\.\):\-]",
            r"\n\s*3[\.\):\-]",
        ]
        if re.search(pattern, lowered)
    )

    action_keywords = [
        "solve",
        "complete",
        "practice",
        "build",
        "deploy",
        "containerize",
        "learn",
        "implement",
        "publish",
        "document",
        "contribute",
        "apply",
        "create",
        "add",
        "test",
    ]

    action_keyword_hits = sum(
        1
        for keyword in action_keywords
        if keyword in lowered
    )

    if numbered_action_hits >= 3:
        notes.append(
            "Provides at least three numbered actions."
        )
    elif action_keyword_hits >= 3:
        notes.append(
            "Provides multiple concrete action-oriented recommendations."
        )
    else:
        score -= 5
        notes.append(
            "Could not verify three concrete next actions."
        )

    # ------------------------------------------------------------------
    # 10. Fit calibration
    # ------------------------------------------------------------------

    optimistic_language = [
        "excellent fit",
        "perfect fit",
        "highly qualified",
        "fully qualified",
        "clearly qualifies",
        "definitely qualifies",
        "obvious hire",
        "ideal candidate",
        "guaranteed fit",
        "excellent candidate",
        "definitely succeed",
        "will definitely succeed",
    ]

    optimistic_hits = [
        phrase
        for phrase in optimistic_language
        if phrase in lowered
    ]

    if optimistic_hits:
        score -= min(len(optimistic_hits) * 5, 15)
        notes.append(
            "Overall fit language may be too strong for the available evidence: "
            + ", ".join(optimistic_hits)
        )

    material_gap_signals = [
        "dsa",
        "cloud",
        "internship",
        "production",
    ]

    material_gap_hits = sum(
        1
        for signal in material_gap_signals
        if signal in lowered
    )

    if material_gap_hits >= 4:
        notes.append(
            "Overall assessment acknowledges all major evidence gaps."
        )
    else:
        score -= 5
        notes.append(
            "Overall assessment does not clearly account for all major evidence gaps."
        )

    return max(0.0, min(100.0, score)), notes


def validate_evidence_rewrite(text: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    score = 100.0
    notes: list[str] = []

    forbidden_claims = [
        "47%",
        "50%",
        "kubernetes",
        "aws",
        "langchain",
        "azure",
        "gcp",
        "production-scale",
        "production scale",
        "production environment",
        "reduced latency",
        "improved latency",
        "increased performance",
        "decreased response time",
    ]

    for claim in forbidden_claims:
        if claim in lowered:
            score -= 25
            notes.append(
                f"Unsupported claim detected: {claim}"
            )

    supported = [
        "react",
        "fastapi",
        "python",
        "sql",
    ]

    if any(term in lowered for term in supported):
        notes.append(
            "Preserved verified technical evidence."
        )
    else:
        score -= 20
        notes.append(
            "Failed to preserve verified technical evidence."
        )

    word_count = len(text.strip().split())

    if word_count == 0:
        score = 0
        notes.append("Rewrite is empty.")
    elif word_count > 45:
        score -= 10
        notes.append(
            "Rewrite is unnecessarily long for a resume bullet."
        )

    line_count = len(
        [
            line
            for line in text.strip().splitlines()
            if line.strip()
        ]
    )

    if line_count > 3:
        score -= 5
        notes.append(
            "Rewrite contains too much surrounding explanation."
        )

    return max(0.0, score), notes


def validate_gap_analysis(text: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    score = 100.0
    notes: list[str] = []

    gaps = {
        "DSA": [
            "dsa",
            "data structures",
            "algorithms",
        ],
        "cloud": [
            "cloud",
            "aws",
            "azure",
            "gcp",
        ],
        "production": [
            "production",
            "production-scale",
        ],
        "internship": [
            "internship",
        ],
    }

    for label, terms in gaps.items():
        if not _contains_any(lowered, terms):
            score -= 15
            notes.append(
                f"Did not discuss {label}."
            )
            continue

        if _contains_any(
            lowered,
            [
                "not provided",
                "not verified",
                "not explicitly provided",
                "not established",
                "unverified",
                "missing evidence",
                "missing",
                "no explicit evidence",
                "no evidence",
                "cannot confirm",
                "cannot verify",
                "absent",
                "explicitly absent",
                "not proven",
                "cannot be inferred",
                "cannot infer",
            ],
        ) or any(
            _has_explicit_negation(lowered, term)
            for term in terms
        ):
            notes.append(
                f"Correctly treats {label} as a gap or unverified evidence."
            )
        else:
            score -= 10
            notes.append(
                f"{label} was mentioned without sufficient evidence qualification."
            )

    forbidden = [
        "b.tech proves",
        "b.tech implies",
        "almost certainly",
        "fastapi proves production",
        "python proves cloud",
        "project proves production",
        "projects prove production",
    ]

    for phrase in forbidden:
        if phrase in lowered:
            score -= 10
            notes.append(
                f"Unsupported inference detected: {phrase}"
            )

    if _contains_any(
        lowered,
        [
            "priority",
            "prioritized",
            "#1",
            "highest priority",
            "critical gap",
            "priority 1",
            "priority 2",
            "priority 3",
        ],
    ):
        notes.append(
            "Gaps are prioritized."
        )
    else:
        score -= 5
        notes.append(
            "Gap analysis lacks explicit prioritization."
        )

    evidence_language = [
        "evidence needed",
        "what evidence",
        "evidence required",
        "to verify",
        "to close the gap",
        "proof needed",
    ]

    if _contains_any(lowered, evidence_language):
        notes.append("Explains what evidence is needed.")
    else:
        score -= 5
        notes.append(
            "Does not clearly explain evidence needed."
        )

    return max(0.0, min(100.0, score)), notes


def validate_action_plan(text: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    score = 100.0
    notes: list[str] = []

    action_groups = [
        ["dsa", "data structures", "algorithms"],
        ["cloud", "aws", "azure", "gcp", "deploy", "deployment"],
        ["production", "production-like", "production scale"],
        ["testing", "pytest", "unit test", "tests"],
        ["internship", "apply", "open source", "professional experience"],
    ]

    hits = sum(
        1
        for group in action_groups
        if _contains_any(lowered, group)
    )

    if hits >= 4:
        notes.append(
            "Action plan addresses the major known gaps."
        )
    elif hits == 3:
        score -= 10
        notes.append(
            "Action plan covers most major gaps."
        )
    else:
        score -= 25
        notes.append(
            "Action plan misses several major gaps."
        )

    dangerous_claims = [
        "your aws experience",
        "your kubernetes experience",
        "your production experience",
        "your strong dsa skills",
        "your cloud experience",
        "your internship experience",
        "already have production",
        "already have aws",
        "already have kubernetes",
    ]

    for phrase in dangerous_claims:
        if phrase in lowered:
            score -= 15
            notes.append(
                f"Recommendation assumes unsupported evidence: {phrase}"
            )

    action_verbs = [
        "build",
        "complete",
        "solve",
        "deploy",
        "containerize",
        "implement",
        "publish",
        "document",
        "contribute",
        "apply",
        "practice",
        "learn",
        "add",
        "create",
        "test",
    ]

    action_hits = sum(
        1
        for verb in action_verbs
        if verb in lowered
    )

    if action_hits >= 3:
        notes.append(
            "Recommendations contain multiple concrete action verbs."
        )
    else:
        score -= 5
        notes.append(
            "Recommendations are not sufficiently action-oriented."
        )

    return max(0.0, min(100.0, score)), notes


def validate_json(text: str) -> tuple[float, list[str]]:
    cleaned = text.strip()

    if cleaned.startswith("</think>"):
        cleaned = cleaned[len("</think>") :].strip()

    if cleaned.startswith("```") or cleaned.endswith("```"):
        return 0.0, [
            "JSON was wrapped in Markdown code fences."
        ]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return 0.0, [
            f"Invalid JSON: {exc}"
        ]

    if not isinstance(parsed, dict):
        return 50.0, [
            "Top-level JSON value must be an object."
        ]

    expected_keys = {
        "fit_score",
        "strong_matches",
        "partial_matches",
        "missing_requirements",
        "next_actions",
    }

    if set(parsed.keys()) != expected_keys:
        return 50.0, [
            "JSON schema keys do not exactly match the required structure."
        ]

    if (
        not isinstance(parsed["fit_score"], int)
        or isinstance(parsed["fit_score"], bool)
        or not 0 <= parsed["fit_score"] <= 100
    ):
        return 70.0, [
            "fit_score must be an integer between 0 and 100."
        ]

    array_keys = [
        "strong_matches",
        "partial_matches",
        "missing_requirements",
        "next_actions",
    ]

    for key in array_keys:
        if not isinstance(parsed[key], list):
            return 70.0, [
                f"{key} must be an array."
            ]

        if not all(
            isinstance(item, str)
            for item in parsed[key]
        ):
            return 70.0, [
                f"All {key} elements must be strings."
            ]

    missing_text = " ".join(
        item.lower()
        for item in parsed["missing_requirements"]
    )

    required_missing = [
        "dsa",
        "cloud",
        "internship",
        "production",
    ]

    missing_hits = sum(
        1
        for term in required_missing
        if term in missing_text
    )

    if missing_hits < 3:
        return 85.0, [
            "JSON is valid, but important missing-evidence requirements were not preserved."
        ]

    positive_text = " ".join(
        [
            *parsed["strong_matches"],
            *parsed["partial_matches"],
        ]
    ).lower()

    unsafe_positive_claims = [
        "aws",
        "kubernetes",
        "production-scale",
        "production scale",
        "internship experience",
        "dsa experience",
    ]

    unsafe_hits = [
        term
        for term in unsafe_positive_claims
        if term in positive_text
    ]

    if unsafe_hits:
        return 90.0, [
            "JSON is structurally valid but places unsupported claims in positive-match fields: "
            + ", ".join(unsafe_hits)
        ]

    if len(parsed["next_actions"]) < 2:
        return 95.0, [
            "JSON is valid and evidence-safe but contains too few actionable next steps."
        ]

    return 100.0, [
        "Valid raw JSON with the exact schema and evidence-safe classification."
    ]


def validate_evidence_constraints(text: str) -> tuple[float, list[str]]:
    lowered = text.lower()
    score = 100.0
    notes: list[str] = []

    required_rejections = {
        "production": [
            "production",
            "production-scale",
            "production scale",
        ],
        "aws": [
            "aws",
        ],
        "kubernetes": [
            "kubernetes",
        ],
    }

    for label, terms in required_rejections.items():
        if not _contains_any(lowered, terms):
            score -= 10
            notes.append(
                f"Did not discuss {label}."
            )
            continue

        negative_patterns = [
            "not proven",
            "not verified",
            "not provided",
            "cannot be inferred",
            "unsupported",
            "not established",
            "cannot confirm",
            "cannot verify",
            "not demonstrated",
            "not shown",
            "no explicit evidence",
            "no evidence",
            "no mention",
            "not listed",
            "does not mention",
            "doesn't mention",
            "no experience",
        ]

        natural_negation = any(
            pattern in lowered
            for pattern in negative_patterns
        )

        if natural_negation:
            notes.append(
                f"Correctly rejects unsupported {label} experience."
            )
        else:
            score -= 20
            notes.append(
                f"{label} may have been treated as established."
            )

    if _contains_any(
        lowered,
        [
            "verified facts",
            "explicit evidence",
            "evidence status",
            "verified",
        ],
    ):
        notes.append(
            "Distinguishes explicit evidence from inference."
        )

    if _contains_any(
        lowered,
        [
            "unsupported assumptions",
            "cannot be inferred",
            "reasonable assumption",
            "unsupported inference",
        ],
    ):
        notes.append(
            "Explicitly discusses unsupported assumptions."
        )

    if _contains_any(
        lowered,
        [
            "what evidence would be needed",
            "evidence needed",
            "evidence required",
            "to verify",
        ],
    ):
        notes.append(
            "Explains what evidence would be required."
        )
    else:
        score -= 5
        notes.append(
            "Does not clearly explain evidence required for verification."
        )

    return max(0.0, min(100.0, score)), notes


# ---------------------------------------------------------------------------
# Evaluation cases
# ---------------------------------------------------------------------------


EVALUATION_CASES = [
    EvaluationCase(
        case_id="CP-01",
        name="Job Fit Reasoning",
        category="career_reasoning",
        weight=25.0,
        prompt="""
You are CareerPilot's evidence-grounded job-fit reasoning engine.

RULE:
Never turn assumptions into candidate evidence.

Use ONLY these evidence states:
- VERIFIED = explicitly stated in candidate evidence.
- PARTIALLY SUPPORTED = related evidence exists, but does not fully prove the requirement.
- NOT VERIFIED = no explicit candidate evidence proves it.
- EXPLICITLY ABSENT = candidate explicitly does not have it.

CANDIDATE EVIDENCE
- B.Tech Computer Science student
- Projects: CareerPilot AI, a full-stack AI career assistant; sentiment analysis web app
- Skills: Python, C++, JavaScript, React, FastAPI, SQL, Git
- No professional internship experience
- No verified production-scale experience
- Goal: software engineering / AI engineering internship

TARGET
Software Engineering Intern

REQUIREMENTS
- Strong programming fundamentals
- Python or C++
- Data structures and algorithms
- REST APIs
- Git
- Good problem-solving ability
- Cloud experience preferred but not required

MANDATORY CONCLUSIONS
- Python = VERIFIED
- C++ = VERIFIED
- Git = VERIFIED
- FastAPI = PARTIALLY SUPPORTED evidence relevant to REST APIs; do not claim it proves every REST requirement
- DSA = NOT VERIFIED
- Cloud = NOT VERIFIED
- Internship = EXPLICITLY ABSENT
- Production-scale experience = EXPLICITLY ABSENT
- Do NOT infer DSA from the B.Tech degree
- Do NOT infer production experience from projects
- Do NOT infer cloud from Python or FastAPI
- Do NOT predict interview success from this evidence

RETURN EXACTLY THESE 7 SECTIONS.
Keep the entire answer concise, preferably under 350 words.

1. Overall fit assessment
2. VERIFIED strong matches
3. PARTIALLY SUPPORTED matches
4. NOT VERIFIED requirements
5. EXPLICITLY ABSENT requirements
6. Top three gaps
7. Three concrete next actions

In section 7, give three numbered actions that produce evidence for the biggest gaps.

Every important claim must be traceable to the candidate evidence.
""",
        validator=validate_job_fit,
    ),
    EvaluationCase(
        case_id="CP-02",
        name="Evidence-Safe Rewrite",
        category="evidence_safety",
        weight=20.0,
        prompt="""
Rewrite the following resume statement using ONLY verified evidence.

VERIFIED EVIDENCE
- Built a React and FastAPI project.
- Used Python and SQL.
- No verified performance metrics.
- No verified Kubernetes experience.
- No verified AWS experience.
- No verified LangChain experience.

UNSAFE ORIGINAL
Improved API latency by 47% using Kubernetes and AWS, and built an advanced LangChain pipeline.

Return exactly ONE concise professional resume bullet.

Do NOT invent:
- metrics
- technologies
- responsibilities
- achievements
- scale
- ownership

Use only the verified evidence.
""",
        validator=validate_evidence_rewrite,
    ),
    EvaluationCase(
        case_id="CP-03",
        name="Gap Analysis",
        category="gap_analysis",
        weight=15.0,
        prompt="""
You are CareerPilot's evidence-gap analyzer.

Distinguish:
- VERIFIED
- NOT VERIFIED
- EXPLICITLY ABSENT

CANDIDATE
- B.Tech Computer Science student
- Python, C++, JavaScript, React, FastAPI, SQL, Git
- CareerPilot AI project
- Sentiment analysis web app
- No professional internship experience
- No verified production-scale experience

TARGET
Software Engineering Intern

REQUIREMENTS
- Python or C++
- Data structures and algorithms
- REST APIs
- Git
- Problem solving
- Cloud preferred

MANDATORY CONCLUSIONS
- Python/C++ = VERIFIED
- Git = VERIFIED
- DSA = NOT VERIFIED
- Cloud = NOT VERIFIED
- Internship = EXPLICITLY ABSENT
- Production-scale experience = EXPLICITLY ABSENT

Do NOT infer DSA from a B.Tech degree.
Do NOT infer cloud from Python/FastAPI.
Do NOT infer production-scale experience from projects.

Return:
1. Priority-ordered gaps
2. Why each is a gap
3. Evidence needed to close each gap
""",
        validator=validate_gap_analysis,
    ),
    EvaluationCase(
        case_id="CP-04",
        name="Action Plan",
        category="actionability",
        weight=10.0,
        prompt="""
Create five concrete next actions for this candidate.

CANDIDATE
- B.Tech Computer Science student
- Python, C++, JavaScript, React, FastAPI, SQL, Git
- CareerPilot AI project
- Sentiment analysis web app
- No professional internship experience
- No verified production-scale experience

TARGET
Software Engineering / AI Engineering internship.

KNOWN GAPS
- DSA evidence
- Cloud/deployment exposure
- Production-like engineering
- Testing
- Professional experience

Prioritize actions that produce demonstrable evidence.

Do not claim any gap is already closed.
Do not invent past experience.
""",
        validator=validate_action_plan,
    ),
    EvaluationCase(
        case_id="CP-05",
        name="Structured Output",
        category="structured_output",
        weight=15.0,
        prompt="""
Return ONLY valid raw JSON.

Do NOT use Markdown.
Do NOT use code fences.
Do NOT add commentary.

Use exactly this schema:

{
  "fit_score": 0,
  "strong_matches": [],
  "partial_matches": [],
  "missing_requirements": [],
  "next_actions": []
}

CANDIDATE
- B.Tech Computer Science student
- Python, C++, JavaScript, React, FastAPI, SQL, Git
- CareerPilot AI project
- Sentiment analysis web app
- No professional internship experience
- No verified production-scale experience

JOB
- Strong programming fundamentals
- Python or C++
- DSA
- REST APIs
- Git
- Problem solving
- Cloud preferred but not required

REQUIRED CLASSIFICATION
- Python = strong match
- C++ = strong match
- FastAPI = strong/partial evidence relevant to REST APIs
- Git = strong match
- DSA = missing/unverified
- Cloud = missing/unverified
- Professional internship = explicitly absent
- Production-scale experience = explicitly absent

fit_score must be an integer 0-100.
Every array element must be a string.
Return NOTHING except the JSON object.
""",
        validator=validate_json,
    ),
    EvaluationCase(
        case_id="CP-06",
        name="Evidence-Constrained Reasoning",
        category="evidence_safety",
        weight=15.0,
        prompt="""
Separate verified facts from unsupported assumptions.

CANDIDATE EVIDENCE
- React
- FastAPI
- Python
- SQL
- Git
- B.Tech Computer Science student
- No professional internship listed

Determine whether the evidence proves:
1. Production-scale backend experience
2. AWS experience
3. Kubernetes experience

For each item, state:
- Evidence status: VERIFIED / PARTIALLY SUPPORTED / NOT VERIFIED / EXPLICITLY ABSENT
- Reason
- What evidence would be needed to verify it

Important:
- Knowing a technology does not automatically prove production experience.
- Do not infer AWS or Kubernetes from Python/FastAPI.
- Do not infer production-scale experience from having a project.
""",
        validator=validate_evidence_constraints,
    ),
]