"""Policy Adapter Registry for registering and resolving policy system adapters."""

from typing import Any

from app.integrations.policy_system.base import PolicyAdapterBase


class PolicyAdapterRegistry:
    """Registry maintaining active and available policy system adapters."""

    def __init__(self) -> None:
        pass

    def register(self, name: str, adapter_cls: type[PolicyAdapterBase]) -> None:
        """Register a policy adapter class under a unique name.

        Implementation: TBC.
        """
        pass

    def get_adapter(self, name: str, config: Any = None) -> PolicyAdapterBase:
        """Resolve and instantiate a registered adapter by name.

        Implementation: TBC.
        """
        raise NotImplementedError

