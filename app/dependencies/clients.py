"""Dependency injection providers for clients, adapters, and services."""

from functools import lru_cache

from app.integrations.policy_system.base import PolicyAdapterBase
from app.integrations.policy_system.duck_creek.adapter import DuckCreekAdapter
from app.services.policy_service import PolicyService


@lru_cache
def get_policy_adapter() -> PolicyAdapterBase:
    """Provides active policy system adapter (Duck Creek initial)."""
    return DuckCreekAdapter()


def get_policy_service() -> PolicyService:
    """Provides PolicyService dependency with injected adapter."""
    return PolicyService(
        adapter=get_policy_adapter(),
    )
