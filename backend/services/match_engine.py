from dataclasses import dataclass
from typing import List

from backend.schemas.candidate import CandidateProfile
from backend.schemas.job import Job


@dataclass
class MatchBreakdown:
    role_fit: float
    skill_fit: float
    experience_fit: float
    location_fit: float
    salary_fit: float
    career_goal_fit: float
    overall_score: float
    matched_skills: List[str]
    missing_skills: List[str]


class MatchEngine:
    """
    Deterministic candidate-to-job matching engine.

    The score is intentionally transparent:
    every dimension can be inspected and explained.
    """

    WEIGHTS = {
        "role": 0.25,
        "skills": 0.30,
        "experience": 0.15,
        "location": 0.10,
        "salary": 0.10,
        "career_goal": 0.10,
    }

    def score(
        self,
        candidate: CandidateProfile,
        job: Job,
    ) -> MatchBreakdown:

        role_fit = self._role_fit(candidate, job)
        skill_fit, matched_skills, missing_skills = (
            self._skill_fit(candidate, job)
        )
        experience_fit = self._experience_fit(candidate, job)
        location_fit = self._location_fit(candidate, job)
        salary_fit = self._salary_fit(candidate, job)
        career_goal_fit = self._career_goal_fit(candidate, job)

        overall_score = round(
            (
                role_fit * self.WEIGHTS["role"]
                + skill_fit * self.WEIGHTS["skills"]
                + experience_fit * self.WEIGHTS["experience"]
                + location_fit * self.WEIGHTS["location"]
                + salary_fit * self.WEIGHTS["salary"]
                + career_goal_fit * self.WEIGHTS["career_goal"]
            ),
            2,
        )

        return MatchBreakdown(
            role_fit=role_fit,
            skill_fit=skill_fit,
            experience_fit=experience_fit,
            location_fit=location_fit,
            salary_fit=salary_fit,
            career_goal_fit=career_goal_fit,
            overall_score=overall_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return value.casefold().strip()

    def _role_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
    ) -> float:

        if not candidate.career_goal.target_roles:
            return 70.0

        job_title = self._normalize(job.title)

        for target_role in candidate.career_goal.target_roles:
            target = self._normalize(target_role)

            if target == job_title:
                return 100.0

            if target in job_title or job_title in target:
                return 90.0

            target_words = set(target.split())
            job_words = set(job_title.split())

            if not target_words:
                continue

            overlap = len(
                target_words.intersection(job_words)
            ) / len(target_words)

            if overlap >= 0.5:
                return 75.0

        return 35.0

    def _skill_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
    ):
        candidate_skills = {
            self._normalize(skill)
            for skill in (
                candidate.skills
                + candidate.technical_skills
            )
        }

        job_skills = {
            self._normalize(skill)
            for skill in job.skills
        }

        if not job_skills:
            return 60.0, [], []

        matched = sorted(
            candidate_skills.intersection(job_skills)
        )

        missing = sorted(
            job_skills.difference(candidate_skills)
        )

        score = (
            len(matched) / len(job_skills)
        ) * 100

        return (
            round(score, 2),
            matched,
            missing,
        )

    @staticmethod
    def _experience_fit(
        candidate: CandidateProfile,
        job: Job,
    ) -> float:

        min_years = job.experience.min_years
        max_years = job.experience.max_years

        if min_years is None and max_years is None:
            return 70.0

        years = candidate.years_of_experience

        if min_years is not None and years < min_years:
            return 40.0

        if max_years is not None and years > max_years:
            return 65.0

        return 100.0

    def _location_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
    ) -> float:

        if not candidate.preferred_locations:
            return 70.0

        candidate_locations = {
            self._normalize(location)
            for location in candidate.preferred_locations
        }

        job_locations = {
            self._normalize(location)
            for location in job.location
        }

        if candidate_locations.intersection(
            job_locations
        ):
            return 100.0

        if job.remote:
            return 85.0

        return 20.0

    @staticmethod
    def _salary_fit(
        candidate: CandidateProfile,
        job: Job,
    ) -> float:

        minimum = (
            candidate.career_goal.minimum_salary_lpa
        )

        if minimum is None:
            return 70.0

        if job.salary.max_lpa is None:
            return 60.0

        if job.salary.max_lpa >= minimum:
            return 100.0

        ratio = (
            job.salary.max_lpa / minimum
        ) * 100

        return max(0.0, min(100.0, ratio))

    def _career_goal_fit(
        self,
        candidate: CandidateProfile,
        job: Job,
    ) -> float:

        target_industries = {
            self._normalize(industry)
            for industry in (
                candidate.career_goal.target_industries
            )
        }

        if not target_industries:
            return 70.0

        metadata_text = str(
            job.metadata
        ).casefold()

        matches = [
            industry
            for industry in target_industries
            if industry in metadata_text
        ]

        if matches:
            return 100.0

        return 50.0