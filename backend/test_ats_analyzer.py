from pathlib import Path

from backend.services.resume_parser import ResumeParser
from backend.services.resume_structurer import ResumeStructurer
from backend.services.ats_analyzer import ATSAnalyzer


def test_ats_analyzer():

    resume_path = Path(
        "sample-data/sample_resume.pdf"
    )

    assert resume_path.exists()

    parser = ResumeParser()

    parsed = parser.parse(
        resume_path.read_bytes()
    )

    structurer = ResumeStructurer()

    structured = structurer.structure(
        parsed
    )

    job_description = """
    Senior Graphic Designer

    We are looking for a Senior Graphic Designer
    with 5+ years of experience.

    Required skills:
    Adobe Photoshop
    Adobe Illustrator
    Figma
    HTML
    CSS

    Experience with web design and digital
    storytelling is preferred.
    """

    analyzer = ATSAnalyzer()

    result = analyzer.analyze(
        structured,
        job_description,
    )

    print()
    print("=" * 70)
    print("ATS ANALYSIS")
    print("=" * 70)

    print(
        f"\nOVERALL ATS SCORE: "
        f"{result.overall_score}/100"
    )

    print("\nCOMPONENT SCORES:")
    print(
        f"  Keyword Coverage: "
        f"{result.keyword_coverage_score}/100"
    )
    print(
        f"  Skill Match:      "
        f"{result.skill_match_score}/100"
    )
    print(
        f"  Experience:       "
        f"{result.experience_alignment_score}/100"
    )
    print(
        f"  Education:        "
        f"{result.education_alignment_score}/100"
    )
    print(
        f"  Section Coverage: "
        f"{result.section_coverage_score}/100"
    )

    print("\nREQUIREMENT MATCHES:")

    for match in result.matches:
        print(
            f"  [{match.status}] "
            f"{match.requirement}"
        )

        if match.evidence:
            for evidence in match.evidence:
                print(
                    f"      Evidence: {evidence}"
                )

    print("\nSUPPORTED:")
    for item in result.supported_requirements:
        print(f"  ✓ {item}")

    print("\nMENTIONED ONLY:")
    for item in result.mentioned_only_requirements:
        print(f"  △ {item}")

    print("\nMISSING:")
    for item in result.missing_requirements:
        print(f"  ✗ {item}")

    print("\nSTRENGTHS:")
    for item in result.strengths:
        print(f"  ✓ {item}")

    print("\nISSUES:")
    for item in result.issues:
        print(f"  ⚠ {item}")

    print("\nRECOMMENDATIONS:")
    for item in result.recommendations:
        print(f"  → {item}")

    print("\nRISKS:")
    print(
        f"  Keyword stuffing: "
        f"{result.keyword_stuffing_risk}"
    )
    print(
        f"  Unsupported claims: "
        f"{result.unsupported_claim_risk}"
    )

    print("\nSUMMARY:")
    print(result.summary)

    assert 0 <= result.overall_score <= 100
    assert 0 <= result.keyword_coverage_score <= 100
    assert 0 <= result.skill_match_score <= 100
    assert 0 <= result.experience_alignment_score <= 100
    assert 0 <= result.education_alignment_score <= 100
    assert 0 <= result.section_coverage_score <= 100

    assert isinstance(
        result.requirements,
        list,
    )

    assert isinstance(
        result.matches,
        list,
    )

    assert isinstance(
        result.supported_requirements,
        list,
    )

    assert isinstance(
        result.missing_requirements,
        list,
    )

    print()
    print("=" * 70)
    print("ATS ANALYZER TEST PASSED")
    print("=" * 70)