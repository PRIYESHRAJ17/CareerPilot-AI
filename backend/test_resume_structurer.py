from pathlib import Path

from backend.services.resume_parser import ResumeParser
from backend.services.resume_structurer import ResumeStructurer


def test_resume_structurer():
    resume_path = Path("sample-data/sample_resume.pdf")

    assert resume_path.exists(), (
        "sample_resume.pdf does not exist."
    )

    # Parse PDF
    parser = ResumeParser()
    parsed_resume = parser.parse(
        resume_path.read_bytes()
    )

    assert parsed_resume.page_count > 0
    assert parsed_resume.text.strip()

    # Structure resume
    structurer = ResumeStructurer()
    structured = structurer.structure(
        parsed_resume
    )

    # Basic validation
    assert structured.page_count > 0
    assert structured.raw_text.strip()
    assert structured.contact is not None

    # Debug output
    print("\n" + "=" * 70)
    print("STRUCTURED RESUME")
    print("=" * 70)

    print("\nCONTACT:")
    print(structured.contact.model_dump())

    print("\nHEADLINE:")
    print(structured.headline)

    print("\nSUMMARY:")
    print(structured.summary)

    print("\nEXPERIENCE:")
    for item in structured.experience:
        print(item.model_dump())

    print("\nEDUCATION:")
    for item in structured.education:
        print(item.model_dump())

    print("\nSKILLS:")
    print(structured.skills)

    print("\nTECHNICAL SKILLS:")
    print(structured.technical_skills)

    print("\nSOFT SKILLS:")
    print(structured.soft_skills)

    print("\nPROJECTS:")
    for item in structured.projects:
        print(item.model_dump())

    print("\nCERTIFICATIONS:")
    for item in structured.certifications:
        print(item.model_dump())

    print("\nACHIEVEMENTS:")
    for item in structured.achievements:
        print(item.model_dump())

    print("\nLANGUAGES:")
    print(structured.languages)

    print("\nMETADATA:")
    print("Pages:", structured.page_count)
    print("Raw text characters:", len(structured.raw_text))

    print("\n" + "=" * 70)
    print("RESUME STRUCTURING TEST PASSED")
    print("=" * 70)