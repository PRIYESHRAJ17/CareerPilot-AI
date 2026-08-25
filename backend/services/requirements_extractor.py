import re
from typing import List, Optional, Tuple

from backend.schemas.job import Job
from backend.schemas.requirements import JobRequirements


class JobRequirementsExtractor:
    """
    Deterministic first-pass job-description intelligence engine.

    Extracts:
    - required skills
    - preferred skills
    - experience
    - education
    - responsibilities
    - seniority
    - hard requirements
    - soft requirements
    - technologies
    - domain
    - keywords
    """

    SKILL_PATTERNS = {
        "python",
        "java",
        "c++",
        "c#",
        "javascript",
        "typescript",
        "react",
        "react.js",
        "node.js",
        "nodejs",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "git",
        "linux",
        "django",
        "flask",
        "fastapi",
        "spring",
        "tensorflow",
        "pytorch",
        "machine learning",
        "deep learning",
        "nlp",
        "langchain",
        "langgraph",
        "rest api",
        "rest apis",
        "graphql",
    }

    EDUCATION_PATTERNS = (
        "bachelor's degree",
        "bachelor degree",
        "b.tech",
        "b.e.",
        "b.e",
        "computer science degree",
        "master's degree",
        "master degree",
        "m.tech",
        "mca",
        "mba",
        "phd",
    )

    REQUIRED_MARKERS = (
        "required",
        "requirements",
        "must have",
        "must-have",
        "mandatory",
        "essential",
        "minimum",
        "required qualification",
        "experience with",
        "proficient in",
        "strong knowledge of",
        "knowledge of",
    )

    PREFERRED_MARKERS = (
        "nice to have",
        "nice-to-have",
        "preferred",
        "preferred qualifications",
        "preferred skills",
        "bonus",
        "plus",
        "good to have",
        "ideally",
    )

    DOMAIN_PATTERNS = (
        "fintech",
        "healthcare",
        "edtech",
        "e-commerce",
        "ecommerce",
        "saas",
        "cybersecurity",
        "cloud computing",
        "banking",
        "insurance",
        "gaming",
        "automotive",
        "logistics",
        "artificial intelligence",
        "machine learning",
        "data engineering",
        "data science",
    )

    SENIORITY_PATTERNS = (
        ("entry-level", "entry"),
        ("entry level", "entry"),
        ("internship", "intern"),
        ("intern", "intern"),
        ("fresher", "entry"),
        ("graduate", "entry"),
        ("junior", "junior"),
        ("associate", "associate"),
        ("mid-level", "mid"),
        ("mid level", "mid"),
        ("senior", "senior"),
        ("staff", "staff"),
        ("principal", "principal"),
        ("lead", "lead"),
        ("manager", "manager"),
    )

    def extract(self, job: Job) -> JobRequirements:
        text = self._clean_text(job.description)
        sentences = self._split_sentences(text)

        required_skills = self._extract_required_skills(sentences)
        preferred_skills = self._extract_preferred_skills(sentences)

        # Required classification takes precedence.
        preferred_skills = [
            skill
            for skill in preferred_skills
            if skill not in required_skills
        ]

        mentioned_skills = self._extract_all_skills(text)

        technologies = sorted(
            set(
                mentioned_skills
                + required_skills
                + preferred_skills
            )
        )

        min_experience, max_experience = (
            self._extract_experience_range(text)
        )

        return JobRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            years_experience_min=min_experience,
            years_experience_max=max_experience,
            education_requirements=self._extract_education(text),
            responsibilities=self._extract_responsibilities(
                text
            ),
            seniority=self._extract_seniority(
                text,
                job.title,
            ),
            hard_requirements=self._extract_hard_requirements(
                sentences
            ),
            soft_requirements=self._extract_soft_requirements(
                sentences
            ),
            technologies=technologies,
            domain=self._extract_domain(text),
            keywords=self._extract_keywords(text),
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text or ""

        text = text.replace("\r", " ")
        text = text.replace("\n", " ")

        text = re.sub(r"\s+", " ", text)

        return text.strip().lower()

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """
        Handle:
        - normal sentences
        - semicolon-separated content
        - bullet-style '- item' content
        """

        parts = re.split(
            r"[.;]|(?=\s+-\s+)",
            text,
        )

        return [
            part.strip(" -")
            for part in parts
            if part.strip(" -")
        ]

    def _extract_required_skills(
        self,
        sentences: List[str],
    ) -> List[str]:

        results = set()

        for sentence in sentences:
            if not self._contains_any(
                sentence,
                self.REQUIRED_MARKERS,
            ):
                continue

            for skill in self.SKILL_PATTERNS:
                if self._skill_in_text(
                    skill,
                    sentence,
                ):
                    results.add(skill)

        return sorted(results)

    def _extract_preferred_skills(
        self,
        sentences: List[str],
    ) -> List[str]:

        results = set()
        preferred_section = False

        section_start_markers = (
            "nice to have",
            "nice-to-have",
            "preferred qualifications",
            "preferred skills",
            "good to have",
            "bonus",
        )

        section_end_markers = (
            "responsibilities",
            "requirements",
            "qualifications",
            "what you'll do",
            "what you will do",
            "education",
        )

        for sentence in sentences:
            sentence = sentence.strip()

            if any(
                marker in sentence
                for marker in section_start_markers
            ):
                preferred_section = True

                # Extract skills appearing on the same line.
                remainder = sentence

                for marker in section_start_markers:
                    if marker in remainder:
                        remainder = remainder.split(
                            marker,
                            1,
                        )[1]
                        break

                for skill in self.SKILL_PATTERNS:
                    if self._skill_in_text(
                        skill,
                        remainder,
                    ):
                        results.add(skill)

                continue

            if preferred_section and any(
                marker in sentence
                for marker in section_end_markers
            ):
                preferred_section = False
                continue

            if preferred_section:
                for skill in self.SKILL_PATTERNS:
                    if self._skill_in_text(
                        skill,
                        sentence,
                    ):
                        results.add(skill)

        # Also catch one-line patterns like:
        # "nice to have: AWS, Docker, Kubernetes"
        joined_text = " ".join(sentences)

        for marker in section_start_markers:
            if marker not in joined_text:
                continue

            start = joined_text.find(marker)
            section = joined_text[
                start + len(marker):
            ]

            for end_marker in section_end_markers:
                end_index = section.find(end_marker)

                if end_index != -1:
                    section = section[:end_index]

            for skill in self.SKILL_PATTERNS:
                if self._skill_in_text(
                    skill,
                    section,
                ):
                    results.add(skill)

        return sorted(results)

    def _extract_all_skills(
        self,
        text: str,
    ) -> List[str]:

        return sorted(
            {
                skill
                for skill in self.SKILL_PATTERNS
                if self._skill_in_text(
                    skill,
                    text,
                )
            }
        )

    @staticmethod
    def _skill_in_text(
        skill: str,
        text: str,
    ) -> bool:

        escaped = re.escape(skill)

        pattern = (
            rf"(?<![a-z0-9+#.-])"
            rf"{escaped}"
            rf"(?![a-z0-9+#.-])"
        )

        return (
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            is not None
        )

    @staticmethod
    def _contains_any(
        text: str,
        markers: Tuple[str, ...],
    ) -> bool:

        return any(
            marker in text
            for marker in markers
        )

    @staticmethod
    def _extract_experience_range(
        text: str,
    ) -> Tuple[
        Optional[float],
        Optional[float],
    ]:

        # Example: 0-2 years / 0 to 2 years
        range_patterns = (
            r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*"
            r"(\d+(?:\.\d+)?)\s*years?",
        )

        for pattern in range_patterns:
            match = re.search(
                pattern,
                text,
            )

            if match:
                return (
                    float(match.group(1)),
                    float(match.group(2)),
                )

        # Example: 2+ years
        plus_match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+\s*years?",
            text,
        )

        if plus_match:
            return (
                float(plus_match.group(1)),
                None,
            )

        # Example: minimum 3 years / at least 3 years
        minimum_patterns = (
            r"minimum\s+of\s+(\d+(?:\.\d+)?)\s*years?",
            r"at\s+least\s+(\d+(?:\.\d+)?)\s*years?",
            r"minimum\s+(\d+(?:\.\d+)?)\s*years?",
        )

        for pattern in minimum_patterns:
            match = re.search(
                pattern,
                text,
            )

            if match:
                return (
                    float(match.group(1)),
                    None,
                )

        return None, None

    @classmethod
    def _extract_education(
        cls,
        text: str,
    ) -> List[str]:

        return sorted(
            {
                education
                for education in cls.EDUCATION_PATTERNS
                if cls._skill_in_text(
                    education,
                    text,
                )
            }
        )

    @staticmethod
    def _extract_responsibilities(
        text: str,
    ) -> List[str]:

        markers = (
            "responsibilities:",
            "responsibilities",
            "you will:",
            "what you'll do:",
            "what you will do:",
        )

        for marker in markers:
            index = text.find(marker)

            if index == -1:
                continue

            section = text[
                index + len(marker):
            ]

            responsibilities = []

            for sentence in re.split(
                r"[.;]",
                section,
            ):
                sentence = sentence.strip(" -")

                if any(
                    stop_marker in sentence
                    for stop_marker in (
                        "nice to have",
                        "requirements:",
                        "requirements",
                        "qualifications",
                    )
                ):
                    break

                if len(sentence) > 15:
                    responsibilities.append(
                        sentence
                    )

                if len(responsibilities) >= 8:
                    break

            return responsibilities

        return []

    @classmethod
    def _extract_seniority(
        cls,
        text: str,
        title: str,
    ) -> Optional[str]:

        combined = (
            f"{title.lower()} {text}"
        )

        for pattern, value in sorted(
            cls.SENIORITY_PATTERNS,
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if cls._skill_in_text(
                pattern,
                combined,
            ):
                return value

        return None

    @classmethod
    def _extract_hard_requirements(
        cls,
        sentences: List[str],
    ) -> List[str]:

        results = []

        for sentence in sentences:
            if cls._contains_any(
                sentence,
                cls.REQUIRED_MARKERS,
            ):
                if len(sentence) >= 15:
                    results.append(sentence)

        return results[:10]

    @classmethod
    def _extract_soft_requirements(
        cls,
        sentences: List[str],
    ) -> List[str]:

        results = []

        for sentence in sentences:
            if cls._contains_any(
                sentence,
                cls.PREFERRED_MARKERS,
            ):
                if len(sentence) >= 15:
                    results.append(sentence)

        return results[:10]

    @classmethod
    def _extract_domain(
        cls,
        text: str,
    ) -> Optional[str]:

        for domain in sorted(
            cls.DOMAIN_PATTERNS,
            key=len,
            reverse=True,
        ):
            if cls._skill_in_text(
                domain,
                text,
            ):
                return domain

        return None

    @staticmethod
    def _extract_keywords(
        text: str,
    ) -> List[str]:

        words = re.findall(
            r"\b[a-z][a-z0-9+#.-]{2,}\b",
            text,
        )

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "you",
            "your",
            "our",
            "are",
            "will",
            "have",
            "has",
            "into",
            "their",
            "they",
            "them",
            "about",
            "those",
        }

        return sorted(
            {
                word
                for word in words
                if word not in stop_words
            }
        )[:50]