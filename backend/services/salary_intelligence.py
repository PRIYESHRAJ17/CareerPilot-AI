import re
from dataclasses import dataclass
from typing import List, Optional

from backend.schemas.job import Job, Salary


@dataclass
class SalaryEvidence:
    """
    Normalized salary evidence extracted from a job listing.
    """

    min_lpa: Optional[float] = None
    max_lpa: Optional[float] = None

    source: str = "unknown"

    confidence: float = 0.0

    evidence_text: str = ""

    disclosed: bool = False


class SalaryIntelligence:
    """
    CareerPilot salary intelligence layer.

    Salary evidence priority:

        1. Valid structured salary
        2. Salary stored in metadata
        3. Job description
        4. Source snippet / other text

    All salary values are normalized to INR LPA.

    Supported examples include:

        ₹8–12 LPA
        8 - 12 LPA
        10 to 15 LPA
        20 LPA
        ₹80,000 per month
        ₹1 lakh per year
        6-10 lakhs per annum
        INR 1200000 - 1800000

    Unknown salary remains UNKNOWN / UNDISCLOSED.

    We never manufacture salary information.
    """

    NUMBER = (
        r"(?:"
        r"\d+(?:,\d{2,3})*(?:\.\d+)?"
        r"|"
        r"\d+(?:\.\d+)?"
        r")"
    )

    # --------------------------------------------------
    # LPA ranges
    # --------------------------------------------------

    LPA_RANGE = re.compile(
        rf"""
        (?P<min>{NUMBER})
        \s*
        (?:-|–|—|\bto\b)
        \s*
        (?P<max>{NUMBER})
        \s*
        (?:lpa|lac|lacs|lakh|lakhs)
        (?:\s*(?:per|/)\s*(?:annum|year))?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    LPA_SINGLE = re.compile(
        rf"""
        (?P<value>{NUMBER})
        \s*
        (?:lpa|lac|lacs|lakh|lakhs)
        (?:\s*(?:per|/)\s*(?:annum|year))?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    CURRENCY_LPA_RANGE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)
        \s*
        (?P<min>{NUMBER})
        \s*
        (?:-|–|—|\bto\b)
        \s*
        (?:₹|rs\.?|inr)?
        \s*
        (?P<max>{NUMBER})
        \s*
        (?:lpa|lac|lacs|lakh|lakhs)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    CURRENCY_LPA_SINGLE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)
        \s*
        (?P<value>{NUMBER})
        \s*
        (?:lpa|lac|lacs|lakh|lakhs)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # --------------------------------------------------
    # Annual INR
    # --------------------------------------------------

    ANNUAL_INR_RANGE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)
        \s*
        (?P<min>{NUMBER})
        \s*
        (?:-|–|—|\bto\b)
        \s*
        (?:₹|rs\.?|inr)?
        \s*
        (?P<max>{NUMBER})
        \s*
        (?:
            (?:per|/)\s*(?:annum|year)
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    ANNUAL_INR_SINGLE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)
        \s*
        (?P<value>{NUMBER})
        \s*
        (?:
            (?:per|/)\s*(?:annum|year)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # --------------------------------------------------
    # Monthly salary
    # --------------------------------------------------

    MONTHLY_RANGE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)?
        \s*
        (?P<min>{NUMBER})
        \s*
        (?:k|K)?
        \s*
        (?:-|–|—|\bto\b)
        \s*
        (?:₹|rs\.?|inr)?
        \s*
        (?P<max>{NUMBER})
        \s*
        (?:k|K)?
        \s*
        (?:
            per\s*month
            |/\s*month
            |monthly
            |per\s*mo
            |/\s*mo
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    MONTHLY_SINGLE = re.compile(
        rf"""
        (?:₹|rs\.?|inr)?
        \s*
        (?P<value>{NUMBER})
        \s*
        (?:k|K)?
        \s*
        (?:
            per\s*month
            |/\s*month
            |monthly
            |per\s*mo
            |/\s*mo
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def enrich(
        self,
        job: Job,
    ) -> Job:
        """
        Enrich a canonical Job with salary evidence.

        Valid structured salary wins.

        Invalid structured salary such as:
            0 - 0
            -1 - 5
            0 - None

        is treated as undisclosed and does not block
        description-based extraction.
        """

        existing = self._structured_salary(
            job
        )

        if existing.disclosed:
            self._apply_evidence(
                job,
                existing,
            )
            return job

        text = self._build_search_text(
            job
        )

        evidence = self.extract(
            text
        )

        self._apply_evidence(
            job,
            evidence,
        )

        return job

    def extract(
        self,
        text: str,
    ) -> SalaryEvidence:
        """
        Extract the strongest salary evidence
        available from arbitrary job text.
        """

        if not text:
            return SalaryEvidence()

        # Avoid unnecessary processing of huge
        # descriptions.
        text = text[:30000]

        candidates: List[
            SalaryEvidence
        ] = []

        self._collect_lpa_candidates(
            text,
            candidates,
        )

        self._collect_annual_inr_candidates(
            text,
            candidates,
        )

        self._collect_monthly_candidates(
            text,
            candidates,
        )

        if not candidates:
            return SalaryEvidence()

        candidates.sort(
            key=lambda item: (
                item.confidence,
                item.min_lpa
                if item.min_lpa is not None
                else -1,
            ),
            reverse=True,
        )

        return candidates[0]

    # ==================================================
    # LPA extraction
    # ==================================================

    def _collect_lpa_candidates(
        self,
        text: str,
        candidates: List[
            SalaryEvidence
        ],
    ) -> None:

        # ₹8–12 LPA
        for match in (
            self.CURRENCY_LPA_RANGE.finditer(
                text
            )
        ):
            minimum = self._number(
                match.group("min")
            )

            maximum = self._number(
                match.group("max")
            )

            if (
                minimum is None
                or maximum is None
            ):
                continue

            if not self._valid_lpa_range(
                minimum,
                maximum,
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=minimum,
                    max_lpa=maximum,
                    source="description",
                    confidence=0.98,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

        # 8–12 LPA
        for match in (
            self.LPA_RANGE.finditer(
                text
            )
        ):
            minimum = self._number(
                match.group("min")
            )

            maximum = self._number(
                match.group("max")
            )

            if (
                minimum is None
                or maximum is None
            ):
                continue

            if not self._valid_lpa_range(
                minimum,
                maximum,
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=minimum,
                    max_lpa=maximum,
                    source="description",
                    confidence=0.97,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

        # ₹20 LPA
        for match in (
            self.CURRENCY_LPA_SINGLE.finditer(
                text
            )
        ):
            value = self._number(
                match.group("value")
            )

            if value is None:
                continue

            if not self._reasonable_lpa(
                value
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=value,
                    max_lpa=None,
                    source="description",
                    confidence=0.96,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

        # 20 LPA
        for match in (
            self.LPA_SINGLE.finditer(
                text
            )
        ):
            value = self._number(
                match.group("value")
            )

            if value is None:
                continue

            if not self._reasonable_lpa(
                value
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=value,
                    max_lpa=None,
                    source="description",
                    confidence=0.94,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

    # ==================================================
    # Annual INR extraction
    # ==================================================

    def _collect_annual_inr_candidates(
        self,
        text: str,
        candidates: List[
            SalaryEvidence
        ],
    ) -> None:

        # ₹1200000 - ₹1800000
        for match in (
            self.ANNUAL_INR_RANGE.finditer(
                text
            )
        ):
            minimum_raw = self._number(
                match.group("min")
            )

            maximum_raw = self._number(
                match.group("max")
            )

            if (
                minimum_raw is None
                or maximum_raw is None
            ):
                continue

            minimum_lpa = (
                self._annual_to_lpa(
                    minimum_raw
                )
            )

            maximum_lpa = (
                self._annual_to_lpa(
                    maximum_raw
                )
            )

            if not self._valid_lpa_range(
                minimum_lpa,
                maximum_lpa,
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=minimum_lpa,
                    max_lpa=maximum_lpa,
                    source="description",
                    confidence=0.95,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

        # ₹1200000 per year
        for match in (
            self.ANNUAL_INR_SINGLE.finditer(
                text
            )
        ):
            value_raw = self._number(
                match.group("value")
            )

            if value_raw is None:
                continue

            value_lpa = (
                self._annual_to_lpa(
                    value_raw
                )
            )

            if not self._reasonable_lpa(
                value_lpa
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=value_lpa,
                    max_lpa=None,
                    source="description",
                    confidence=0.94,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

    # ==================================================
    # Monthly extraction
    # ==================================================

    def _collect_monthly_candidates(
        self,
        text: str,
        candidates: List[
            SalaryEvidence
        ],
    ) -> None:

        # ₹50k–₹80k/month
        for match in (
            self.MONTHLY_RANGE.finditer(
                text
            )
        ):
            minimum_raw = self._number(
                match.group("min")
            )

            maximum_raw = self._number(
                match.group("max")
            )

            if (
                minimum_raw is None
                or maximum_raw is None
            ):
                continue

            minimum_monthly = (
                self._monthly_value(
                    minimum_raw,
                    match.group(0),
                )
            )

            maximum_monthly = (
                self._monthly_value(
                    maximum_raw,
                    match.group(0),
                )
            )

            if (
                minimum_monthly is None
                or maximum_monthly is None
            ):
                continue

            minimum_lpa = round(
                minimum_monthly
                * 12
                / 100000,
                2,
            )

            maximum_lpa = round(
                maximum_monthly
                * 12
                / 100000,
                2,
            )

            if not self._valid_lpa_range(
                minimum_lpa,
                maximum_lpa,
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=minimum_lpa,
                    max_lpa=maximum_lpa,
                    source="description",
                    confidence=0.90,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

        # ₹80,000/month
        for match in (
            self.MONTHLY_SINGLE.finditer(
                text
            )
        ):
            value_raw = self._number(
                match.group("value")
            )

            if value_raw is None:
                continue

            monthly_value = (
                self._monthly_value(
                    value_raw,
                    match.group(0),
                )
            )

            if monthly_value is None:
                continue

            value_lpa = round(
                monthly_value
                * 12
                / 100000,
                2,
            )

            if not self._reasonable_lpa(
                value_lpa
            ):
                continue

            candidates.append(
                SalaryEvidence(
                    min_lpa=value_lpa,
                    max_lpa=None,
                    source="description",
                    confidence=0.88,
                    evidence_text=match.group(
                        0
                    ),
                    disclosed=True,
                )
            )

    # ==================================================
    # Structured salary
    # ==================================================

    @staticmethod
    def _structured_salary(
        job: Job,
    ) -> SalaryEvidence:
        """
        Use structured salary only when its values
        are genuinely valid.

        Critical rule:

            0 / 0 is NOT salary information.

        Neither zero nor negative salary values may
        become VERIFIED.
        """

        minimum = (
            job.salary.min_lpa
        )

        maximum = (
            job.salary.max_lpa
        )

        # Clean invalid minimum.
        if (
            minimum is not None
            and minimum <= 0
        ):
            minimum = None

        # Clean invalid maximum.
        if (
            maximum is not None
            and maximum <= 0
        ):
            maximum = None

        # Nothing valid remains.
        if (
            minimum is None
            and maximum is None
        ):
            return SalaryEvidence()

        # If both exist, maximum must not be below
        # minimum.
        if (
            minimum is not None
            and maximum is not None
            and maximum < minimum
        ):
            return SalaryEvidence()

        return SalaryEvidence(
            min_lpa=minimum,
            max_lpa=maximum,
            source="structured",
            confidence=1.0,
            evidence_text="structured salary",
            disclosed=True,
        )

    # ==================================================
    # Metadata / text construction
    # ==================================================

    @staticmethod
    def _build_search_text(
        job: Job,
    ) -> str:

        pieces: List[str] = []

        if job.description:
            pieces.append(
                job.description
            )

        metadata = (
            job.metadata
            if isinstance(
                job.metadata,
                dict,
            )
            else {}
        )

        for key in (
            "salary_raw",
            "description",
            "snippet",
            "text",
            "summary",
            "content",
            "job_description",
            "body",
        ):
            value = metadata.get(
                key
            )

            if value:
                pieces.append(
                    str(value)
                )

        return "\n".join(
            pieces
        )

    # ==================================================
    # Apply evidence to canonical Job
    # ==================================================

    @staticmethod
    def _apply_evidence(
        job: Job,
        evidence: SalaryEvidence,
    ) -> None:

        # --------------------------------------------------
        # No salary evidence
        # --------------------------------------------------

        if not evidence.disclosed:

            # Make sure invalid source salary does
            # not remain in the canonical object.
            job.salary = Salary(
                min_lpa=None,
                max_lpa=None,
                currency="INR",
            )

            job.metadata[
                "salary_status"
            ] = "UNDISCLOSED"

            job.metadata[
                "salary_source"
            ] = "unavailable"

            job.metadata[
                "salary_confidence"
            ] = 0.0

            job.metadata[
                "salary_evidence"
            ] = None

            return

        # --------------------------------------------------
        # Valid salary evidence
        # --------------------------------------------------

        job.salary = Salary(
            min_lpa=evidence.min_lpa,
            max_lpa=evidence.max_lpa,
            currency="INR",
        )

        job.metadata[
            "salary_status"
        ] = "VERIFIED"

        job.metadata[
            "salary_source"
        ] = evidence.source

        job.metadata[
            "salary_confidence"
        ] = evidence.confidence

        job.metadata[
            "salary_evidence"
        ] = evidence.evidence_text

    # ==================================================
    # Numeric utilities
    # ==================================================

    @staticmethod
    def _number(
        value: Optional[str],
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(
                value.replace(
                    ",",
                    "",
                )
            )
        except (
            ValueError,
            TypeError,
        ):
            return None

    @staticmethod
    def _annual_to_lpa(
        value: float,
    ) -> Optional[float]:

        if value <= 0:
            return None

        # Values below 1000 are assumed to
        # already be expressed as LPA.
        if value <= 1000:
            return round(
                value,
                2,
            )

        return round(
            value / 100000,
            2,
        )

    @staticmethod
    def _monthly_value(
        value: float,
        evidence_text: str,
    ) -> Optional[float]:

        if value <= 0:
            return None

        normalized = (
            evidence_text.lower()
        )

        # Explicit thousand notation:
        #
        # 80k/month → ₹80,000/month
        if re.search(
            r"\bk\b",
            normalized,
        ):
            return value * 1000

        # Already an absolute monthly amount:
        #
        # ₹80,000/month
        if value >= 1000:
            return value

        # For an explicitly monthly amount below
        # 1000, treat it as absolute INR rather
        # than silently assuming thousands.
        return value

    @staticmethod
    def _reasonable_lpa(
        value: Optional[float],
    ) -> bool:

        if value is None:
            return False

        return (
            value > 0
            and value <= 1000
        )

    def _valid_lpa_range(
        self,
        minimum: Optional[float],
        maximum: Optional[float],
    ) -> bool:

        if not self._reasonable_lpa(
            minimum
        ):
            return False

        if maximum is None:
            return True

        if not self._reasonable_lpa(
            maximum
        ):
            return False

        return (
            maximum >= minimum
        )