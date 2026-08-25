from typing import Dict, List

from backend.connectors.base import JobSource


class JobSourceRegistry:
    """
    Central registry for all CareerPilot job-source connectors.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, JobSource] = {}

    def register(self, source: JobSource) -> None:
        self._sources[source.name] = source

    def get(self, name: str) -> JobSource:
        if name not in self._sources:
            raise KeyError(f"Job source '{name}' is not registered.")

        return self._sources[name]

    def all(self) -> List[JobSource]:
        return list(self._sources.values())

    def names(self) -> List[str]:
        return list(self._sources.keys())
