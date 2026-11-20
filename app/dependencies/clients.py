from functools import lru_cache

from app.integrations.five_sigma.client import FiveSigmaClient
from app.services.policy_service import (
    PolicyClientProtocol,
    PolicyService,
)


@lru_cache
def get_policy_client() -> PolicyClientProtocol:
    """Provides the active policy system client (Five Sigma initially, flexible for future providers)."""
    return FiveSigmaClient()


# Backward-compatible alias
get_five_sigma_client = get_policy_client


def get_policy_service() -> PolicyService:
    """Provides PolicyService dependency with injected provider client."""
    return PolicyService(
        client=get_policy_client(),
    )
