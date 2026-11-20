"""Duck Creek Policy Adapter implementing PolicyAdapterBase."""

from typing import Any

from app.integrations.policy_system.base import PolicyAdapterBase


class DuckCreekAdapter(PolicyAdapterBase):
    """Adapter for Duck Creek Policy Administration System."""

    def __init__(self, config: Any = None) -> None:
        """Initialize Duck Creek adapter with optional config.

        Implementation: TBC.
        """
        self.config = config

    async def search_policy(self, criteria: Any = None) -> Any:
        """Search Duck Creek policies matching criteria.

        Implementation: TBC.
        """
        raise NotImplementedError

    async def get_policy(self, policy_id: str) -> Any:
        """Retrieve policy details from Duck Creek.

        Implementation: TBC.
        """
        raise NotImplementedError

    async def get_coverages(self, policy_id: str) -> Any:
        """Retrieve coverage details from Duck Creek.

        Implementation: TBC.
        """
        raise NotImplementedError

