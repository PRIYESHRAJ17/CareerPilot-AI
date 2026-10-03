from pathlib import Path

from backend.services.resume_parser import ResumeParser


def test_resume_parser():
    resume_path = Path("sample-data/sample_resume.pdf")

    assert resume_path.exists(), (
        "sample_resume.pdf does not exist. "
        "Place a test resume PDF inside sample-data/"
    )

    parser = ResumeParser()

    result = parser.parse(
        resume_path.read_bytes()
    )

    print("\n=== PAGE COUNT ===")
    print(result.page_count)

    print("\n=== EXTRACTED TEXT ===")
    print(result.text)

    print("\n=== DETECTED SECTIONS ===")
    for section, content in result.sections.items():
        print(f"\n--- {section.upper()} ---")
        print(content)

    assert result.page_count > 0
    assert result.text.strip()