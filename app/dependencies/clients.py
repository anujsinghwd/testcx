"""Dependency injection providers for repositories and services."""

from functools import lru_cache

from fastapi import Depends

from app.database.connection import get_engine
from app.integrations.policy_system.source import PolicySource
from app.repositories.policy_repository import (
    MySQLPolicyRepository,
)
from app.services.policy_service import PolicyService


@lru_cache
def get_mysql_policy_repository() -> MySQLPolicyRepository:
    """Provides singleton instance of MySQLPolicyRepository."""
    return MySQLPolicyRepository(
        engine=get_engine(),
        auto_init=False,
        auto_seed=False,
    )


# Backward-compatible alias
get_mock_policy_repository = get_mysql_policy_repository


def get_policy_source() -> PolicySource:
    """Provides active policy data source (MySQLPolicyRepository for Phase 1)."""
    return get_mysql_policy_repository()


def get_policy_service(
    source: PolicySource = Depends(get_policy_source),
) -> PolicyService:
    """Provides PolicyService dependency with injected policy source."""
    return PolicyService(policy_source=source)
