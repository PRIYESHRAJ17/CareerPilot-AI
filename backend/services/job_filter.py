from typing import List, Optional

from backend.schemas.job import Job
from backend.schemas.candidate import CandidateProfile


class JobFilter:
    """
    Deterministic pre-filter for job opportunities.

    This layer handles hard constraints before semantic/AI ranking.
    """

    def filter(
        self,
        jobs: List[Job],
        candidate: CandidateProfile,
    ) -> List[Job]:
        filtered: List[Job] = []

        for job in jobs:
            if not self._location_match(job, candidate):
                continue

            if not self._salary_match(job, candidate):
                continue

            if not self._work_mode_match(job, candidate):
                continue

            if not self._notice_period_match(job, candidate):
                continue

            filtered.append(job)

        return filtered

    @staticmethod
    def _location_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:
        """
        Hard location filter.

        If the candidate has no location preference,
        all locations are accepted.
        """

        if not candidate.preferred_locations:
            return True

        job_locations = {
            location.casefold()
            for location in job.location
        }

        preferred_locations = {
            location.casefold()
            for location in candidate.preferred_locations
        }

        return bool(
            job_locations.intersection(
                preferred_locations
            )
        )

    @staticmethod
    def _salary_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:
        """
        Salary filter.

        Jobs without salary data are not rejected here.
        They are allowed through for later scoring.
        """

        minimum = candidate.career_goal.minimum_salary_lpa

        if minimum is None:
            return True

        if job.salary.max_lpa is None:
            return True

        return job.salary.max_lpa >= minimum

    @staticmethod
    def _work_mode_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:
        """
        Work-mode filter.

        Empty preferences mean no restriction.
        """

        if not candidate.preferred_work_modes:
            return True

        if job.remote:
            job_modes = {
                "remote",
                "work from home",
                "wfh",
            }
        else:
            job_modes = {
                "onsite",
                "on-site",
                "hybrid",
            }

        preferred = {
            mode.casefold()
            for mode in candidate.preferred_work_modes
        }

        return bool(job_modes.intersection(preferred))

    @staticmethod
    def _notice_period_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:
        """
        Placeholder for future India-specific notice-period
        compatibility.

        We currently allow all jobs because our canonical Job
        schema does not yet contain employer notice-period data.
        """

        return True