import re
from typing import Dict, List, Tuple

from backend.schemas.job import Job


class JobDeduplicator:
    """
    Groups likely duplicate job listings into canonical opportunities.

    This first version uses deterministic normalization.
    Semantic similarity will be added in a later iteration.
    """

    def deduplicate(self, jobs: List[Job]) -> List[Job]:
        groups: Dict[str, List[Job]] = {}

        for job in jobs:
            fingerprint = self._fingerprint(job)
            groups.setdefault(fingerprint, []).append(job)

        return [
            self._merge_group(group)
            for group in groups.values()
        ]

    def _fingerprint(self, job: Job) -> str:
        """
        Build a deterministic fingerprint from the most useful
        job identity fields.
        """

        company = self._normalize_text(job.company)
        title = self._normalize_title(job.title)

        location = self._normalize_location(job.location)

        return "|".join(
            [
                company,
                title,
                location,
            ]
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        value = re.sub(r"\s+", " ", value)

        return value

    @classmethod
    def _normalize_title(cls, value: str) -> str:
        normalized = cls._normalize_text(value)

        replacements = {
            "software development engineer": "software engineer",
            "software dev engineer": "software engineer",
            "sde": "software engineer",
            "swe": "software engineer",
        }

        for old, new in replacements.items():
            normalized = normalized.replace(old, new)

        return normalized

    @classmethod
    def _normalize_location(
        cls,
        locations: List[str],
    ) -> str:
        normalized = [
            cls._normalize_text(location)
            for location in locations
        ]

        normalized = sorted(
            set(
                location
                for location in normalized
                if location
            )
        )

        return "|".join(normalized)

    @staticmethod
    def _merge_group(group: List[Job]) -> Job:
        """
        Keep the first listing as the canonical record.

        Additional source listings are preserved inside metadata.
        """

        primary = group[0]

        source_records = []

        for job in group:
            source_records.append(
                {
                    "source": job.source,
                    "source_job_id": job.source_job_id,
                    "apply_url": job.apply_url,
                    "source_url": job.source_url,
                }
            )

        primary.metadata = {
            **primary.metadata,
            "source_count": len(group),
            "source_records": source_records,
        }

        return primary