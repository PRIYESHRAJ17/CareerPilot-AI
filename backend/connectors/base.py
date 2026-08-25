from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from backend.schemas.job import Job


class JobSource(ABC):
    """
    Common interface that every job source connector must implement.

    Each connector is responsible for:
    1. Fetching jobs from its source.
    2. Converting source-specific data into our canonical Job schema.
    3. Returning normalized Job objects.
    """

    name: str = "unknown"

    @abstractmethod
    def search(
        self,
        query: str,
        location: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        **filters: Any,
    ) -> List[Job]:
        """
        Search this source and return normalized Job objects.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Check whether the source is currently available.
        """
        raise NotImplementedError

    def normalize(self, raw_job: Dict[str, Any]) -> Job:
        """
        Convert source-specific job data into the canonical Job schema.
        Each connector can override this method.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement normalize()"
        )
