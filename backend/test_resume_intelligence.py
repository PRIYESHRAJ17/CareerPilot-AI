from pathlib import Path

from backend.services.resume_parser import ResumeParser
from backend.services.resume_structurer import ResumeStructurer
from backend.services.resume_intelligence import (
    ResumeIntelligenceEngine,
)


def test_resume_intelligence():

    resume_path = Path(
        "sample-data/sample_resume.pdf"
    )

    assert resume_path.exists(), (
        "sample_resume.pdf does not exist."
    )

    # ---------------------------------------------------------
    # PDF → PARSED RESUME
    # ---------------------------------------------------------

    parser = ResumeParser()

    parsed = parser.parse(
        resume_path.read_bytes()
    )

    assert parsed.text.strip()
    assert parsed.page_count > 0

    # ---------------------------------------------------------
    # PARSED RESUME → STRUCTURED RESUME
    # ---------------------------------------------------------

    structurer = ResumeStructurer()

    structured = structurer.structure(
        parsed
    )

    assert structured is not None

    # ---------------------------------------------------------
    # STRUCTURED RESUME → INTELLIGENCE
    # ---------------------------------------------------------

    engine = ResumeIntelligenceEngine()

    result = engine.analyze(
        structured
    )

    # ---------------------------------------------------------
    # DISPLAY
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("RESUME INTELLIGENCE")
    print("=" * 70)

    print(
        f"\nOVERALL SCORE: "
        f"{result.overall_score}/100"
    )

    print("\nSUMMARY:")
    print(result.summary)

    print("\nSECTION SCORES:")

    for name, section in (
        result.section_scores.items()
    ):
        print(
            f"  {name:<18} "
            f"{section.score:>5.1f}/100"
        )

    print("\nSTRENGTHS:")

    for item in result.strengths:
        print(f"  ✓ {item}")

    print("\nISSUES:")

    for item in result.issues:
        print(f"  ⚠ {item}")

    print("\nMISSING SECTIONS:")

    for item in result.missing_sections:
        print(f"  • {item}")

    print("\nRECOMMENDATIONS:")

    for item in result.recommendations:
        print(f"  → {item}")

    print("\nACHIEVEMENT ANALYSIS:")
    print(
        result.achievement_analysis
    )

    print("\nKEYWORD QUALITY:")
    print(
        result.keyword_quality
    )

    # ---------------------------------------------------------
    # BASIC VALIDATION
    # ---------------------------------------------------------

    assert 0 <= result.overall_score <= 100

    assert result.section_scores

    assert isinstance(
        result.strengths,
        list,
    )

    assert isinstance(
        result.issues,
        list,
    )

    assert isinstance(
        result.recommendations,
        list,
    )

    assert isinstance(
        result.missing_sections,
        list,
    )

    assert isinstance(
        result.keyword_quality,
        dict,
    )

    assert isinstance(
        result.achievement_analysis,
        dict,
    )

    print()
    print("=" * 70)
    print("RESUME INTELLIGENCE TEST PASSED")
    print("=" * 70)