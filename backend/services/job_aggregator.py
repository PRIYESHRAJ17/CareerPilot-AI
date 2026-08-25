from typing import Any, List

from backend.connectors.base import JobSource
from backend.schemas.job import Job


class JobAggregator:
    """
    Query multiple job sources and combine their normalized results.

    A failure in one source does not stop other sources from responding.
    """

    def __init__(self, sources: List[JobSource]) -> None:
        self.sources = sources

    def search(
        self,
        query: str,
        location: str | None = None,
        limit_per_source: int = 20,
        **filters: Any,
    ) -> List[Job]:
        all_jobs: List[Job] = []

        for source in self.sources:
            try:
                jobs = source.search(
                    query=query,
                    location=location,
                    limit=limit_per_source,
                    **filters,
                )

                all_jobs.extend(jobs)

                print(
                    f"[JobAggregator] "
                    f"{source.name}: {len(jobs)} jobs"
                )

            except Exception as exc:
                print(
                    f"[JobAggregator] "
                    f"{source.name} failed: {exc}"
                )

        return self._deduplicate_source_results(all_jobs)

    @staticmethod
    def _deduplicate_source_results(
        jobs: List[Job],
    ) -> List[Job]:
        """
        Remove duplicate records from the same source.

        Cross-source deduplication will be implemented separately.
        """

        seen = set()
        unique_jobs: List[Job] = []

        for job in jobs:
            key = f"{job.source}:{job.source_job_id}"

            if key in seen:
                continue

            seen.add(key)
            unique_jobs.append(job)

        return unique_jobs