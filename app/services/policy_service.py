"""Policy Service coordinating policy search independently of the underlying policy system."""

from typing import Any

from app.integrations.policy_system.source import PolicySource
from app.schemas.policy import PolicyApiSearchResponse


class PolicyService:
    """Service handling policy search independently of underlying provider systems."""

    def __init__(self, policy_source: PolicySource) -> None:
        """Initialize PolicyService with an injected PolicySource."""
        self.policy_source = policy_source

    async def search_policies(
        self,
        lob: str,
        org_external_id: str,
        suborg_external_id: str | None = None,
        search_fields: dict[str, Any] | None = None,
    ) -> PolicyApiSearchResponse:
        """Searches policies via the configured policy source."""
        return await self.policy_source.search_policies(
            lob=lob,
            org_external_id=org_external_id,
            suborg_external_id=suborg_external_id,
            search_fields=search_fields,
        )
