from typing import List

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job


class JobFilter:
    """
    Deterministic hard filter for CareerPilot jobs.
    """

    def filter(
        self,
        jobs: List[Job],
        candidate: CandidateProfile,
    ) -> List[Job]:

        filtered: List[Job] = []

        for job in jobs:

            if not self._location_match(
                job,
                candidate,
            ):
                continue

            if not self._salary_match(
                job,
                candidate,
            ):
                continue

            if not self._work_mode_match(
                job,
                candidate,
            ):
                continue

            if not self._notice_period_match(
                job,
                candidate,
            ):
                continue

            filtered.append(job)

        return filtered

    @staticmethod
    def _location_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

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
        Salary is a lower-bound preference.

        Example:

            candidate = 6 LPA

            job 6-10  -> PASS
            job 8-12  -> PASS
            job 20-50 -> PASS
            job 50-70 -> PASS
            job 5-12  -> REJECT
            unknown   -> KEEP as UNDISCLOSED

        Unknown salary is retained because the company may
        have a good opportunity but simply does not publish
        compensation.
        """

        minimum = (
            candidate
            .career_goal
            .minimum_salary_lpa
        )

        if minimum is None:
            return True

        salary_min = job.salary.min_lpa
        salary_max = job.salary.max_lpa

        # No usable salary information.
        #
        # Keep the job and let the API/UI mark it
        # as UNDISCLOSED.
        if (
            salary_min is None
            and salary_max is None
        ):
            return True

        # The advertised minimum is the safest value
        # for evaluating a candidate's minimum salary.
        if salary_min is not None:
            return salary_min >= minimum

        # Rare fallback: only a maximum exists.
        if salary_max is not None:
            return salary_max >= minimum

        return True

    @staticmethod
    def _work_mode_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:

        if not candidate.preferred_work_modes:
            return True

        preferred = {
            mode.casefold()
            for mode in candidate.preferred_work_modes
        }

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

        return bool(
            job_modes.intersection(
                preferred
            )
        )

    @staticmethod
    def _notice_period_match(
        job: Job,
        candidate: CandidateProfile,
    ) -> bool:
        return True