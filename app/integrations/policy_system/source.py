"""PolicySource abstract interface defining data source contracts for policy search."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.policy import PolicyApiSearchResponse


class PolicySource(ABC):
    """Abstract interface for any policy data source (MySQL mock repository, PAS adapter, etc.)."""

    @abstractmethod
    async def search_policies(
        self,
        lob: str,
        org_external_id: str,
        suborg_external_id: str | None = None,
        search_fields: dict[str, Any] | None = None,
    ) -> PolicyApiSearchResponse:
        """Search policies matching criteria.

        Returns PolicyApiSearchResponse with total_results, display_schema, and results.
        """
        raise NotImplementedError
