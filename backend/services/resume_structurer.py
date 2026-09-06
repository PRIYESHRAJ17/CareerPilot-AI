from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from backend.schemas.resume import (
    ResumeAchievement,
    ResumeCertification,
    ResumeContact,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    StructuredResume,
)
from backend.services.resume_parser import ResumeParseResult


class ResumeStructurer:
    """
    Converts parser output into the canonical StructuredResume model.

    Design goals:
    - deterministic first
    - conservative extraction
    - preserve source evidence
    - avoid inventing resume information
    - tolerate common resume formatting variations
    - provide a stable foundation for future LLM enrichment
    """

    SECTION_ALIASES = {
        "summary": {
            "summary",
            "professional summary",
            "profile",
            "professional profile",
            "career summary",
            "objective",
            "career objective",
            "about me",
        },
        "experience": {
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "employment history",
            "work history",
            "professional history",
        },
        "education": {
            "education",
            "academic background",
            "academic history",
            "educational background",
            "qualifications",
        },
        "skills": {
            "skills",
            "technical skills",
            "core skills",
            "key skills",
            "skills & technologies",
            "technical skills & tools",
            "technologies",
            "tools & technologies",
        },
        "projects": {
            "projects",
            "personal projects",
            "academic projects",
            "selected projects",
            "key projects",
            "project experience",
        },
        "certifications": {
            "certifications",
            "certificates",
            "professional certifications",
            "licenses & certifications",
            "licenses and certifications",
        },
        "achievements": {
            "achievements",
            "awards",
            "honors",
            "honours",
            "accomplishments",
            "awards & achievements",
        },
        "languages": {
            "languages",
            "language skills",
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
    }

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

    URL_PATTERN = re.compile(
        r"(https?://[^\s]+|www\.[^\s]+)",
        re.IGNORECASE,
    )

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
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

    COMMON_TECHNOLOGIES = {
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
        "sql",
        "html",
        "css",
        "react",
        "react.js",
        "next.js",
        "node.js",
        "nodejs",
        "express",
        "fastapi",
        "flask",
        "django",
        "spring",
        "spring boot",
        "docker",
        "kubernetes",
        "git",
        "github",
        "gitlab",
        "aws",
        "azure",
        "gcp",
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "firebase",
        "graphql",
        "rest",
        "rest api",
        "langchain",
        "langgraph",
        "openai",
        "llm",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "scikit-learn",
        "power bi",
        "tableau",
        "spark",
        "hadoop",
    }

    SOFT_SKILLS = {
        "communication",
        "leadership",
        "teamwork",
        "problem solving",
        "problem-solving",
        "collaboration",
        "adaptability",
        "time management",
        "critical thinking",
        "creativity",
        "mentoring",
        "presentation",
        "decision making",
        "decision-making",
    }

    def structure(
        self,
        parsed_resume: ResumeParseResult,
    ) -> StructuredResume:
        """
        Main structuring entry point.
        """

        if not parsed_resume.text.strip():
            return StructuredResume(
                raw_text="",
                page_count=parsed_resume.page_count,
            )

        sections = self._normalize_sections(parsed_resume.sections)

        contact = self._extract_contact(parsed_resume.text)
        headline = self._extract_headline(parsed_resume.text, contact)

        summary = sections.get("summary", "").strip()

        experience = self._extract_experience(
            sections.get("experience", "")
        )

        education = self._extract_education(
            sections.get("education", "")
        )

        skills, technical_skills, soft_skills = self._extract_skills(
            sections.get("skills", "")
        )

        projects = self._extract_projects(
            sections.get("projects", "")
        )

        certifications = self._extract_certifications(
            sections.get("certifications", "")
        )

        achievements = self._extract_achievements(
            sections.get("achievements", "")
        )

        languages = self._extract_languages(
            sections.get("languages", "")
        )

        return StructuredResume(
            contact=contact,
            headline=headline,
            summary=summary,
            experience=experience,
            education=education,
            skills=skills,
            technical_skills=technical_skills,
            soft_skills=soft_skills,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
            languages=languages,
            raw_text=parsed_resume.text,
            page_count=parsed_resume.page_count,
        )

    # ==========================================================
    # SECTION NORMALIZATION
    # ==========================================================

    def _normalize_sections(
        self,
        sections: Dict[str, str],
    ) -> Dict[str, str]:
        normalized: Dict[str, str] = {}

        for key, value in sections.items():
            canonical = self._canonical_section_name(key)

            if canonical:
                if canonical in normalized:
                    normalized[canonical] += "\n" + value
                else:
                    normalized[canonical] = value

        return normalized

    def _canonical_section_name(
        self,
        section_name: str,
    ) -> Optional[str]:
        normalized = self._normalize_heading(section_name)

        for canonical, aliases in self.SECTION_ALIASES.items():
            for alias in aliases:
                if normalized == self._normalize_heading(alias):
                    return canonical

        compact = re.sub(r"[^a-z0-9]", "", normalized)

        for canonical, aliases in self.SECTION_ALIASES.items():
            for alias in aliases:
                alias_compact = re.sub(
                    r"[^a-z0-9]",
                    "",
                    self._normalize_heading(alias),
                )

                if compact == alias_compact:
                    return canonical

        return None

    @staticmethod
    def _normalize_heading(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[\s:_|]+", " ", value)
        value = re.sub(r"[^\w\s&/-]", "", value)
        return value.strip()

    # ==========================================================
    # CONTACT
    # ==========================================================

    def _extract_contact(
        self,
        text: str,
    ) -> ResumeContact:
        email_match = self.EMAIL_PATTERN.search(text)

        email = email_match.group(0) if email_match else None

        phone = self._extract_phone(text)

        urls = self.URL_PATTERN.findall(text)

        linkedin = None
        github = None
        website = None

        for url in urls:
            clean_url = url.rstrip(".,);]")

            lowered = clean_url.lower()

            if "linkedin.com" in lowered:
                linkedin = clean_url
            elif "github.com" in lowered:
                github = clean_url
            elif website is None:
                website = clean_url

        name = self._extract_name(text)

        location = self._extract_location(text)

        return ResumeContact(
            name=name,
            email=email,
            phone=phone,
            location=location,
            website=website,
            linkedin=linkedin,
            github=github,
        )

    def _extract_name(self, text: str) -> Optional[str]:
        lines = [
            self._clean_line(line)
            for line in text.splitlines()
            if self._clean_line(line)
        ]

        for line in lines[:12]:
            lowered = line.lower()

            if (
                "@" in line
                or "linkedin" in lowered
                or "github" in lowered
                or "http" in lowered
                or "www." in lowered
            ):
                continue

            if any(char.isdigit() for char in line):
                continue

            if self._canonical_section_name(line):
                continue

            words = line.split()

            if 2 <= len(words) <= 5 and len(line) <= 80:
                return line

        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        candidates = self.PHONE_PATTERN.findall(text)

        for candidate in candidates:
            digits = re.sub(r"\D", "", candidate)

            if 8 <= len(digits) <= 15:
                return candidate.strip()

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        location_patterns = [
            r"(?:location|based in|address)\s*[:\-]\s*([^\n|]+)",
            r"\b(Bangalore|Bengaluru|Mumbai|Delhi|New Delhi|Hyderabad|Pune|Chennai|Kolkata|Noida|Gurgaon|Gurugram|Ahmedabad|Jaipur|Lucknow)\b",
        ]

        for pattern in location_patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return None

    # ==========================================================
    # HEADLINE
    # ==========================================================

    def _extract_headline(
        self,
        text: str,
        contact: ResumeContact,
    ) -> Optional[str]:
        lines = [
            self._clean_line(line)
            for line in text.splitlines()
            if self._clean_line(line)
        ]

        for index, line in enumerate(lines[:15]):
            if contact.name and line == contact.name:
                if index + 1 < len(lines):
                    candidate = lines[index + 1]

                    if self._looks_like_headline(candidate):
                        return candidate

        for line in lines[:10]:
            if self._looks_like_headline(line):
                return line

        return None

    @staticmethod
    def _looks_like_headline(line: str) -> bool:
        lowered = line.lower()

        blocked = {
            "contact",
            "email",
            "phone",
            "linkedin",
            "github",
            "summary",
            "profile",
            "experience",
            "education",
            "skills",
        }

        if lowered in blocked:
            return False

        if "@" in line:
            return False

        if "http" in lowered or "www." in lowered:
            return False

        if any(char.isdigit() for char in line):
            return False

        words = line.split()

        return 2 <= len(words) <= 10 and len(line) <= 100

    # ==========================================================
    # EXPERIENCE
    # ==========================================================

    def _extract_experience(
        self,
        content: str,
    ) -> List[ResumeExperience]:
        if not content.strip():
            return []

        blocks = self._split_into_record_blocks(content)

        experiences: List[ResumeExperience] = []

        for block in blocks:
            lines = self._meaningful_lines(block)

            if not lines:
                continue

            date_match = self.DATE_PATTERN.search(block)

            start_date = None
            end_date = None

            if date_match:
                start_date = self._clean_date(
                    date_match.group("start")
                )
                end_date = self._clean_date(
                    date_match.group("end")
                )

            non_date_lines = [
                line
                for line in lines
                if not self.DATE_PATTERN.search(line)
            ]

            job_title = None
            company = None
            location = None

            if non_date_lines:
                job_title = non_date_lines[0]

            if len(non_date_lines) >= 2:
                company = non_date_lines[1]

            if len(non_date_lines) >= 3:
                possible_location = non_date_lines[2]

                if self._looks_like_location(possible_location):
                    location = possible_location

            description_lines = []

            for line in non_date_lines:
                if line in {
                    job_title,
                    company,
                    location,
                }:
                    continue

                if self._is_bullet(line):
                    description_lines.append(
                        self._strip_bullet(line)
                    )
                else:
                    description_lines.append(line)

            description = "\n".join(description_lines).strip()

            achievements = [
                line
                for line in description_lines
                if self._looks_like_achievement(line)
            ]

            technologies = self._extract_technologies(
                block
            )

            experiences.append(
                ResumeExperience(
                    job_title=job_title,
                    company=company,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                    achievements=achievements,
                    technologies=technologies,
                )
            )

        return experiences

    # ==========================================================
    # EDUCATION
    # ==========================================================

    def _extract_education(
        self,
        content: str,
    ) -> List[ResumeEducation]:
        if not content.strip():
            return []

        blocks = self._split_into_record_blocks(content)

        education_records: List[ResumeEducation] = []

        for block in blocks:
            lines = self._meaningful_lines(block)

            if not lines:
                continue

            date_match = self.DATE_PATTERN.search(block)

            start_date = None
            end_date = None

            if date_match:
                start_date = self._clean_date(
                    date_match.group("start")
                )
                end_date = self._clean_date(
                    date_match.group("end")
                )

            non_date_lines = [
                line
                for line in lines
                if not self.DATE_PATTERN.search(line)
            ]

            degree = None
            institution = None
            location = None
            field_of_study = None
            grade = None

            if non_date_lines:
                first = non_date_lines[0]

                if self._looks_like_degree(first):
                    degree = first
                else:
                    institution = first

            for line in non_date_lines[1:]:
                lowered = line.lower()

                if (
                    "gpa" in lowered
                    or "cgpa" in lowered
                    or "grade" in lowered
                    or re.search(r"\b\d+(?:\.\d+)?\s*/\s*\d+\b", line)
                ):
                    grade = line
                elif (
                    "computer" in lowered
                    or "engineering" in lowered
                    or "science" in lowered
                    or "business" in lowered
                    or "management" in lowered
                    or "technology" in lowered
                    or "art" in lowered
                ):
                    field_of_study = line
                elif self._looks_like_location(line):
                    location = line
                elif institution is None:
                    institution = line

            education_records.append(
                ResumeEducation(
                    degree=degree,
                    institution=institution,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    field_of_study=field_of_study,
                    grade=grade,
                )
            )

        return education_records

    # ==========================================================
    # SKILLS
    # ==========================================================

    def _extract_skills(
        self,
        content: str,
    ) -> Tuple[List[str], List[str], List[str]]:
        if not content.strip():
            return [], [], []

        raw_items = re.split(
            r"[,|•·;]\s*|\n",
            content,
        )

        skills: List[str] = []
        technical: List[str] = []
        soft: List[str] = []

        for item in raw_items:
            item = self._clean_line(item)

            if not item:
                continue

            item = re.sub(
                r"^(technical skills|soft skills|skills)\s*:?\s*",
                "",
                item,
                flags=re.IGNORECASE,
            ).strip()

            if not item:
                continue

            parts = re.split(
                r"\s{2,}|:\s*",
                item,
            )

            if len(parts) > 1:
                possible_items = parts
            else:
                possible_items = [item]

            for skill in possible_items:
                skill = self._clean_skill(skill)

                if not skill:
                    continue

                if len(skill) > 60:
                    continue

                self._append_unique(
                    skills,
                    skill,
                )

                lowered = skill.lower()

                if (
                    lowered in self.COMMON_TECHNOLOGIES
                    or any(
                        tech in lowered
                        for tech in self.COMMON_TECHNOLOGIES
                        if len(tech) >= 4
                    )
                ):
                    self._append_unique(
                        technical,
                        skill,
                    )

                if lowered in self.SOFT_SKILLS:
                    self._append_unique(
                        soft,
                        skill,
                    )

        return skills, technical, soft

    # ==========================================================
    # PROJECTS
    # ==========================================================

    def _extract_projects(
        self,
        content: str,
    ) -> List[ResumeProject]:
        if not content.strip():
            return []

        blocks = self._split_into_record_blocks(content)

        projects: List[ResumeProject] = []

        for block in blocks:
            lines = self._meaningful_lines(block)

            if not lines:
                continue

            name = lines[0]

            url_match = self.URL_PATTERN.search(block)
            url = (
                url_match.group(0).rstrip(".,);]")
                if url_match
                else None
            )

            description_lines = []

            for line in lines[1:]:
                if url and url in line:
                    continue

                description_lines.append(
                    self._strip_bullet(line)
                )

            description = "\n".join(
                description_lines
            ).strip()

            achievements = [
                line
                for line in description_lines
                if self._looks_like_achievement(line)
            ]

            technologies = self._extract_technologies(
                block
            )

            projects.append(
                ResumeProject(
                    name=name,
                    description=description,
                    technologies=technologies,
                    url=url,
                    achievements=achievements,
                )
            )

        return projects

    # ==========================================================
    # CERTIFICATIONS
    # ==========================================================

    def _extract_certifications(
        self,
        content: str,
    ) -> List[ResumeCertification]:
        if not content.strip():
            return []

        blocks = self._split_into_record_blocks(content)

        certifications: List[ResumeCertification] = []

        for block in blocks:
            lines = self._meaningful_lines(block)

            if not lines:
                continue

            name = lines[0]

            issuer = None
            issue_date = None
            expiry_date = None
            credential_id = None
            credential_url = None

            url_match = self.URL_PATTERN.search(block)

            if url_match:
                credential_url = (
                    url_match.group(0).rstrip(".,);]")
                )

            credential_match = re.search(
                r"(?:credential\s*(?:id|number)|certificate\s*id)"
                r"\s*[:#-]?\s*([A-Za-z0-9_-]+)",
                block,
                re.IGNORECASE,
            )

            if credential_match:
                credential_id = credential_match.group(1)

            date_matches = list(
                self.DATE_PATTERN.finditer(block)
            )

            if date_matches:
                issue_date = self._clean_date(
                    date_matches[0].group("start")
                )

                expiry_candidate = date_matches[0].group(
                    "end"
                )

                if expiry_candidate:
                    expiry_date = self._clean_date(
                        expiry_candidate
                    )

            for line in lines[1:]:
                lowered = line.lower()

                if (
                    "issued by" in lowered
                    or "issuer" in lowered
                    or "from " in lowered
                ):
                    issuer = re.sub(
                        r"^(?:issued by|issuer|from)\s*:?\s*",
                        "",
                        line,
                        flags=re.IGNORECASE,
                    ).strip()

            certifications.append(
                ResumeCertification(
                    name=name,
                    issuer=issuer,
                    issue_date=issue_date,
                    expiry_date=expiry_date,
                    credential_id=credential_id,
                    credential_url=credential_url,
                )
            )

        return certifications

    # ==========================================================
    # ACHIEVEMENTS
    # ==========================================================

    def _extract_achievements(
        self,
        content: str,
    ) -> List[ResumeAchievement]:
        if not content.strip():
            return []

        blocks = self._split_into_record_blocks(content)

        achievements: List[ResumeAchievement] = []

        for block in blocks:
            lines = self._meaningful_lines(block)

            if not lines:
                continue

            title = self._strip_bullet(lines[0])

            description = "\n".join(
                self._strip_bullet(line)
                for line in lines[1:]
            ).strip()

            date_match = self.DATE_PATTERN.search(block)

            date = None

            if date_match:
                date = self._clean_date(
                    date_match.group("start")
                )

            achievements.append(
                ResumeAchievement(
                    title=title,
                    description=description,
                    date=date,
                )
            )

        return achievements

    # ==========================================================
    # LANGUAGES
    # ==========================================================

    def _extract_languages(
        self,
        content: str,
    ) -> List[str]:
        if not content.strip():
            return []

        raw_items = re.split(
            r"[,|•·;]\s*|\n",
            content,
        )

        languages: List[str] = []

        for item in raw_items:
            item = self._clean_line(item)

            if not item:
                continue

            item = re.sub(
                r"\s*\((?:native|fluent|professional|basic|"
                r"intermediate|advanced)\)\s*$",
                "",
                item,
                flags=re.IGNORECASE,
            )

            if ":" in item:
                _, item = item.split(
                    ":",
                    1,
                )

            for language in item.split(","):
                language = self._clean_line(language)

                if language:
                    self._append_unique(
                        languages,
                        language,
                    )

        return languages

    # ==========================================================
    # GENERIC HELPERS
    # ==========================================================

    def _split_into_record_blocks(
        self,
        content: str,
    ) -> List[str]:
        """
        Splits section content into likely records.

        Blank lines are the strongest boundary. If a resume extractor
        collapses spacing, date lines and bullets are also used as
        secondary signals.
        """

        content = content.strip()

        if not content:
            return []

        raw_blocks = re.split(
            r"\n\s*\n+",
            content,
        )

        blocks = [
            block.strip()
            for block in raw_blocks
            if block.strip()
        ]

        if len(blocks) > 1:
            return blocks

        lines = self._meaningful_lines(content)

        if not lines:
            return []

        records: List[List[str]] = []
        current: List[str] = []

        for line in lines:
            if (
                current
                and self.DATE_PATTERN.search(line)
                and any(
                    self.DATE_PATTERN.search(existing)
                    for existing in current
                )
            ):
                records.append(current)
                current = []

            current.append(line)

        if current:
            records.append(current)

        return [
            "\n".join(record)
            for record in records
            if record
        ]

    @staticmethod
    def _meaningful_lines(
        text: str,
    ) -> List[str]:
        lines = []

        for raw_line in text.splitlines():
            line = ResumeStructurer._clean_line(raw_line)

            if line:
                lines.append(line)

        return lines

    @staticmethod
    def _clean_line(line: str) -> str:
        line = line.replace("\u00a0", " ")
        line = re.sub(r"\s+", " ", line)
        return line.strip()

    @staticmethod
    def _clean_skill(skill: str) -> str:
        skill = skill.strip(" \t\r\n-–—•·:;|")

        skill = re.sub(
            r"\s+",
            " ",
            skill,
        )

        return skill

    @staticmethod
    def _strip_bullet(line: str) -> str:
        return re.sub(
            r"^[\s•●○▪◦\-–—*]+\s*",
            "",
            line,
        ).strip()

    @staticmethod
    def _is_bullet(line: str) -> bool:
        return bool(
            re.match(
                r"^\s*[•●○▪◦\-–—*]\s+",
                line,
            )
        )

    @staticmethod
    def _clean_date(value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        return value

    def _extract_technologies(
        self,
        text: str,
    ) -> List[str]:
        lowered = text.lower()

        technologies: List[str] = []

        for technology in sorted(
            self.COMMON_TECHNOLOGIES,
            key=len,
            reverse=True,
        ):
            pattern = re.escape(
                technology
            )

            if re.search(
                rf"(?<!\w){pattern}(?!\w)",
                lowered,
            ):
                self._append_unique(
                    technologies,
                    technology,
                )

        return technologies

    @staticmethod
    def _looks_like_location(
        value: str,
    ) -> bool:
        lowered = value.lower()

        known_locations = {
            "bangalore",
            "bengaluru",
            "mumbai",
            "delhi",
            "new delhi",
            "hyderabad",
            "pune",
            "chennai",
            "kolkata",
            "noida",
            "gurgaon",
            "gurugram",
            "ahmedabad",
            "jaipur",
            "lucknow",
            "remote",
        }

        if lowered in known_locations:
            return True

        return bool(
            re.search(
                r",\s*[A-Za-z]{2,}",
                value,
            )
        )

    @staticmethod
    def _looks_like_degree(
        value: str,
    ) -> bool:
        lowered = value.lower()

        degree_keywords = (
            "b.tech",
            "btech",
            "b.e.",
            "be ",
            "bachelor",
            "m.tech",
            "mtech",
            "m.e.",
            "master",
            "mba",
            "phd",
            "doctorate",
            "b.sc",
            "bsc",
            "m.sc",
            "msc",
            "bca",
            "mca",
            "diploma",
        )

        return any(
            keyword in lowered
            for keyword in degree_keywords
        )

    @staticmethod
    def _looks_like_achievement(
        value: str,
    ) -> bool:
        lowered = value.lower()

        action_words = (
            "increased",
            "decreased",
            "improved",
            "reduced",
            "saved",
            "built",
            "developed",
            "designed",
            "implemented",
            "led",
            "launched",
            "achieved",
            "won",
            "ranked",
            "generated",
            "optimized",
            "automated",
        )

        has_metric = bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*%?\b",
                value,
            )
        )

        return has_metric or any(
            word in lowered
            for word in action_words
        )

    @staticmethod
    def _append_unique(
        target: List[str],
        value: str,
    ) -> None:
        normalized = value.strip().lower()

        if not normalized:
            return

        existing = {
            item.strip().lower()
            for item in target
        }

        if normalized not in existing:
            target.append(value.strip())