"""Base interface for Policy System adapters following the Adapter Pattern."""

from abc import ABC, abstractmethod
from typing import Any


class PolicyAdapterBase(ABC):
    """Abstract base class defining the contract for all policy system adapters."""

    @abstractmethod
    async def search_policy(self, criteria: Any = None) -> Any:
        """Search policies matching criteria.

        Implementation: TBC.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_policy(self, policy_id: str) -> Any:
        """Retrieve policy details by identifier.

        Implementation: TBC.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_coverages(self, policy_id: str) -> Any:
        """Retrieve coverage details for a policy.

        Implementation: TBC.
        """
        raise NotImplementedError
