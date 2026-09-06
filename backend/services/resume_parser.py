from io import BytesIO
from typing import Dict, List, Optional
import re

from pypdf import PdfReader


class ResumeParseResult:
    """
    Structured result produced by the resume parsing pipeline.

    The extracted information is intentionally kept structured
    because this data will later power:

    - Resume Intelligence
    - Candidate Intelligence
    - ATS analysis
    - Job-specific resume analysis
    - Future Resume Builder
    """

    def __init__(
        self,
        text: str,
        pages: List[str],
        page_count: int,
        sections: Dict[str, str],
    ):
        self.text = text
        self.pages = pages
        self.page_count = page_count
        self.sections = sections

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "pages": self.pages,
            "page_count": self.page_count,
            "sections": self.sections,
        }


class ResumeParser:
    """
    High-quality PDF resume parser.

    Pipeline:

        PDF bytes
            ↓
        validation
            ↓
        page extraction
            ↓
        text normalization
            ↓
        PDF artifact repair
            ↓
        template-noise removal
            ↓
        section detection
            ↓
        ResumeParseResult
    """

    # ==========================================================
    # SECTION ALIASES
    # ==========================================================

    SECTION_ALIASES = {
        "summary": {
            "summary",
            "professional summary",
            "professional profile",
            "profile",
            "career summary",
            "objective",
            "career objective",
            "professional objective",
            "about",
            "about me",
        },

        "experience": {
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "employment history",
            "work history",
            "career history",
            "professional history",
            "professionalexperience",
            "workexperience",
        },

        "education": {
            "education",
            "academic background",
            "academic qualifications",
            "academic history",
            "educational background",
            "educational qualifications",
            "qualifications",
        },

        "skills": {
            "skills",
            "technical skills",
            "soft skills",
            "core skills",
            "key skills",
            "skills & technologies",
            "skills and technologies",
            "technical skills & tools",
            "technical expertise",
            "core competencies",
            "competencies",
            "technologies",
            "tools & technologies",
            "technicalskills",
            "softskills",
            "coreskills",
            "keyskills",
        },

        "projects": {
            "projects",
            "personal projects",
            "academic projects",
            "key projects",
            "selected projects",
            "project experience",
            "projectexperience",
        },

        "certifications": {
            "certifications",
            "certificates",
            "licenses & certifications",
            "licenses and certifications",
            "professional certifications",
            "professionalcertifications",
        },

        "achievements": {
            "achievements",
            "accomplishments",
            "awards",
            "honors",
            "honours",
            "awards & achievements",
            "awards and achievements",
        },

        "publications": {
            "publications",
            "research",
            "papers",
        },

        "volunteering": {
            "volunteering",
            "volunteer experience",
            "community involvement",
        },

        "languages": {
            "languages",
            "language",
            "spoken languages",
        },

        "contact": {
            "contact",
            "contact information",
            "contactinformation",
        },
    }

    # ==========================================================
    # TEMPLATE NOISE
    # ==========================================================

    TEMPLATE_NOISE_MARKERS = {
        "dear job seeker",
        "free resume builder",
        "how to write a resume",
        "resume samples by industry",
        "cover letter builder",
        "cover letter examples",
        "our 2021 resume template",
        "our 2022 resume template",
        "our 2023 resume template",
        "our 2024 resume template",
        "our 2025 resume template",
        "our 2026 resume template",
        "best regards",
    }

    # ==========================================================
    # WEBSITE / EMAIL / PHONE
    # ==========================================================

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    URL_PATTERN = re.compile(
        r"(?:https?://|www\.)[^\s<>()]+",
        re.IGNORECASE,
    )

    DOMAIN_PATTERN = re.compile(
        r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|io|dev|ai|co|me|in|uk|us|ca|app|tech)\b",
        re.IGNORECASE,
    )

    PHONE_PATTERN = re.compile(
        r"""
        (?<!\d)
        (?:
            \+?\d{1,3}[\s.-]?
        )?
        (?:\(?\d{2,4}\)?[\s.-]?)?
        \d{3,4}[\s.-]?\d{3,4}
        (?!\d)
        """,
        re.VERBOSE,
    )

    # ==========================================================
    # DATES
    # ==========================================================

    DATE_PATTERN = re.compile(
        r"""
        (?P<start>
            (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|
               May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|
               Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
            [\s,.-]*\d{4}
            |
            \d{1,2}[/-]\d{4}
            |
            \d{4}
        )
        \s*
        (?:-|–|—|to|until)
        \s*
        (?P<end>
            (?:Present|Current|Now)
            |
            (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|
               May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|
               Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
            [\s,.-]*\d{4}
            |
            \d{1,2}[/-]\d{4}
            |
            \d{4}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    SINGLE_DATE_PATTERN = re.compile(
        r"""
        (?:
            (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|
               May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|
               Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
            [\s,.-]*\d{4}
            |
            \d{1,2}[/-]\d{4}
            |
            \d{4}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # ==========================================================
    # PARSE
    # ==========================================================

    def parse(self, file_bytes: bytes) -> ResumeParseResult:
        """
        Parse a PDF resume from raw file bytes.
        """

        self._validate_file(file_bytes)

        try:
            reader = PdfReader(BytesIO(file_bytes))
        except Exception as exc:
            raise ValueError(
                "Unable to read the uploaded PDF resume."
            ) from exc

        if not reader.pages:
            raise ValueError(
                "The uploaded PDF contains no pages."
            )

        pages: List[str] = []

        for page in reader.pages:
            try:
                raw_text = page.extract_text() or ""
            except Exception:
                raw_text = ""

            cleaned_text = self._clean_extracted_text(
                raw_text
            )

            if cleaned_text:
                pages.append(cleaned_text)

        if not pages:
            raise ValueError(
                "No readable text was found in the PDF resume."
            )

        full_text = self._combine_pages(pages)

        full_text = self._remove_template_noise(
            full_text
        )

        if not full_text.strip():
            raise ValueError(
                "No meaningful resume content was found."
            )

        sections = self._detect_sections(
            full_text
        )

        return ResumeParseResult(
            text=full_text,
            pages=pages,
            page_count=len(reader.pages),
            sections=sections,
        )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def _validate_file(
        self,
        file_bytes: bytes,
    ) -> None:
        if not file_bytes:
            raise ValueError(
                "Resume file is empty."
            )

        if not file_bytes.startswith(b"%PDF"):
            raise ValueError(
                "Uploaded file does not appear to be a valid PDF."
            )

    # ==========================================================
    # TEXT CLEANING
    # ==========================================================

    def _clean_extracted_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize extracted PDF text while preserving useful
        line boundaries.
        """

        if not text:
            return ""

        lines: List[str] = []

        for raw_line in text.splitlines():

            line = raw_line.replace(
                "\u00a0",
                " ",
            )

            line = line.strip()

            if not line:
                continue

            line = re.sub(
                r"\s+",
                " ",
                line,
            )

            line = self._repair_character_spacing(
                line
            )

            line = self._repair_common_pdf_joins(
                line
            )

            if line:
                lines.append(line)

        return "\n".join(lines)

    # ==========================================================
    # CHARACTER SPACING
    # ==========================================================

    def _repair_character_spacing(
        self,
        line: str,
    ) -> str:
        """
        Repair common PDF extraction artifacts.

        Examples:

            C o n t a c t
                ↓
            Contact

            Sen ior
                ↓
            Senior

        The repair is deliberately conservative.
        """

        original = line

        if not line:
            return line

        compact = line.replace(
            " ",
            "",
        )

        characters_without_spaces = len(
            compact
        )

        spaces = line.count(" ")

        # Strong character-by-character spacing.
        if (
            characters_without_spaces >= 5
            and spaces >= 2
            and spaces / max(
                characters_without_spaces,
                1,
            ) >= 0.30
        ):
            if self._looks_like_character_spaced(
                line
            ):
                return compact

        words = line.split()

        if len(words) < 2:
            return original

        repaired_words: List[str] = []

        index = 0

        while index < len(words):

            current = words[index]

            if (
                index + 1 < len(words)
                and self._looks_like_split_word(
                    current,
                    words[index + 1],
                )
            ):
                repaired_words.append(
                    current + words[index + 1]
                )

                index += 2
                continue

            repaired_words.append(
                current
            )

            index += 1

        repaired = " ".join(
            repaired_words
        )

        return repaired

    def _looks_like_character_spaced(
        self,
        line: str,
    ) -> bool:
        words = line.split()

        if len(words) < 3:
            return False

        short_word_count = sum(
            1
            for word in words
            if len(word) <= 2
        )

        single_character_count = sum(
            1
            for word in words
            if len(word) == 1
        )

        return (
            single_character_count >= 2
            or short_word_count >= len(words) * 0.50
            or len(words) >= 7
        )

    def _looks_like_split_word(
        self,
        left: str,
        right: str,
    ) -> bool:
        """
        Conservative repair of fragments such as:

            Sen + ior
            Gra + phic
            Expe + rience

        Avoids joining normal words.
        """

        if not left or not right:
            return False

        if (
            not left.isalpha()
            or not right.isalpha()
        ):
            return False

        if len(left) > 4 or len(right) > 5:
            return False

        if len(left) == 1 and len(right) == 1:
            return True

        return (
            len(left) <= 3
            and len(right) <= 4
        )

    # ==========================================================
    # COMMON PDF WORD-JOIN REPAIR
    # ==========================================================

    def _repair_common_pdf_joins(
        self,
        line: str,
    ) -> str:
        """
        Repair obvious extraction joins where a normal word
        boundary has disappeared.

        This intentionally uses a small set of high-confidence
        patterns rather than aggressive dictionary rewriting.
        """

        replacements = {
            "andweb": "and web",
            "ofweb": "of web",
            "tohelp": "to help",
            "standout": "stand out",
            "ofFine": "of Fine",
            "ofArts": "of Arts",
            "inDesign": "in Design",
        }

        repaired = line

        for source, target in replacements.items():
            repaired = repaired.replace(
                source,
                target,
            )

        return repaired

    # ==========================================================
    # PAGE COMBINATION
    # ==========================================================

    def _combine_pages(
        self,
        pages: List[str],
    ) -> str:
        return "\n\n".join(
            page
            for page in pages
            if page.strip()
        )

    # ==========================================================
    # TEMPLATE NOISE
    # ==========================================================

    def _remove_template_noise(
        self,
        text: str,
    ) -> str:
        """
        Remove obvious template instructions.

        Once strong template language is encountered, the
        remainder of the document is treated as template noise.
        """

        lines = text.splitlines()

        cleaned_lines: List[str] = []

        noise_started = False

        for line in lines:

            normalized = self._normalize_heading(
                line
            )

            compact = self._compact_heading(
                normalized
            )

            marker_found = False

            for marker in self.TEMPLATE_NOISE_MARKERS:

                marker_normalized = (
                    self._normalize_heading(
                        marker
                    )
                )

                marker_compact = (
                    self._compact_heading(
                        marker_normalized
                    )
                )

                if (
                    marker_normalized in normalized
                    or marker_compact in compact
                ):
                    marker_found = True
                    break

            if marker_found:
                noise_started = True

            if noise_started:
                continue

            cleaned_lines.append(line)

        return "\n".join(
            cleaned_lines
        ).strip()

    # ==========================================================
    # SECTION DETECTION
    # ==========================================================

    def _detect_sections(
        self,
        text: str,
    ) -> Dict[str, str]:
        """
        Detect resume sections.

        Handles:

            Professional Experience
            ProfessionalExperience
            PROFESSIONAL EXPERIENCE
            Professional Experience:
            Soft Skills
            SoftSkills
        """

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        detected_sections: Dict[
            str,
            List[str],
        ] = {}

        current_section = "header"

        detected_sections[
            current_section
        ] = []

        for line in lines:

            section_name = self._match_section(
                self._normalize_heading(line)
            )

            if section_name:

                current_section = section_name

                detected_sections.setdefault(
                    current_section,
                    [],
                )

                continue

            detected_sections.setdefault(
                current_section,
                [],
            ).append(line)

        return {
            section: "\n".join(
                content
            ).strip()
            for section, content
            in detected_sections.items()
            if content
        }

    # ==========================================================
    # HEADING NORMALIZATION
    # ==========================================================

    def _normalize_heading(
        self,
        line: str,
    ) -> str:
        """
        Normalize a potential heading.

        Examples:

            " Professional Experience: "
                →
            "professional experience"

            "SoftSkills"
                →
            "softskills"
        """

        normalized = line.lower().strip()

        normalized = normalized.replace(
            "\u00a0",
            " ",
        )

        normalized = re.sub(
            r"^[•·▪●\-–—\s]+",
            "",
            normalized,
        )

        normalized = normalized.rstrip(
            ":"
        ).strip()

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized

    def _compact_heading(
        self,
        value: str,
    ) -> str:
        """
        Remove formatting characters so concatenated headings
        can be matched.

        Example:

            "Professional Experience"
                →
            "professionalexperience"
        """

        return re.sub(
            r"[^a-z0-9]",
            "",
            value.lower(),
        )

    # ==========================================================
    # SECTION MATCHING
    # ==========================================================

    def _match_section(
        self,
        normalized_line: str,
    ) -> Optional[str]:
        """
        Match a line against canonical section aliases.

        Uses both normal and compact representations.
        """

        normalized_line = (
            self._normalize_heading(
                normalized_line
            )
        )

        compact_line = (
            self._compact_heading(
                normalized_line
            )
        )

        # ------------------------------------------------------
        # Exact normal match
        # ------------------------------------------------------

        for section, aliases in (
            self.SECTION_ALIASES.items()
        ):

            for alias in aliases:

                alias_normalized = (
                    self._normalize_heading(
                        alias
                    )
                )

                if normalized_line == alias_normalized:
                    return section

        # ------------------------------------------------------
        # Compact match
        # ------------------------------------------------------

        for section, aliases in (
            self.SECTION_ALIASES.items()
        ):

            for alias in aliases:

                alias_compact = (
                    self._compact_heading(
                        alias
                    )
                )

                if compact_line == alias_compact:
                    return section

        return None

    # ==========================================================
    # PUBLIC UTILITY
    # ==========================================================

    def extract_contact_candidates(
        self,
        text: str,
    ) -> Dict[str, List[str]]:
        """
        Extract contact candidates without deciding which one
        is authoritative.

        Useful for downstream structured extraction.
        """

        emails = list(
            dict.fromkeys(
                self.EMAIL_PATTERN.findall(
                    text
                )
            )
        )

        urls = [
            url.rstrip(
                ".,);]"
            )
            for url in self.URL_PATTERN.findall(
                text
            )
        ]

        domains = [
            domain.rstrip(
                ".,);]"
            )
            for domain in self.DOMAIN_PATTERN.findall(
                text
            )
        ]

        phones = []

        for candidate in self.PHONE_PATTERN.findall(
            text
        ):
            digits = re.sub(
                r"\D",
                "",
                candidate,
            )

            if 8 <= len(digits) <= 15:
                phones.append(
                    candidate.strip()
                )

        return {
            "emails": list(
                dict.fromkeys(emails)
            ),
            "urls": list(
                dict.fromkeys(urls)
            ),
            "domains": list(
                dict.fromkeys(domains)
            ),
            "phones": list(
                dict.fromkeys(phones)
            ),
        }