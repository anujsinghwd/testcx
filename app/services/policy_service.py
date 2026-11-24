"""Policy Service coordinating policy search and retrieval independently of the underlying policy system."""

from app.integrations.policy_system.source import PolicySource
from app.schemas.policy import PolicyApiRetrieveResponse, PolicyApiSearchResponse


class PolicyService:
    """Service handling policy search and retrieval independently of underlying provider systems."""

    def __init__(self, policy_source: PolicySource) -> None:
        """Initialize PolicyService with an injected PolicySource."""
        self.policy_source = policy_source

    async def search_policies(
        self,
        lob: str,
        org_external_id: str,
        suborg_external_id: str | None = None,
        policy_number: str | None = None,
    ) -> PolicyApiSearchResponse:
        """Searches policies via the configured policy source."""
        return await self.policy_source.search_policies(
            lob=lob,
            org_external_id=org_external_id,
            suborg_external_id=suborg_external_id,
            policy_number=policy_number,
        )

    async def retrieve_policy_by_token(
        self,
        retrieval_token: str,
    ) -> PolicyApiRetrieveResponse:
        """Retrieves a complete policy record associated with an opaque retrieval token."""
        return await self.policy_source.retrieve_policy_by_token(retrieval_token=retrieval_token)

    async def retrieve_policy_by_external_id(
        self,
        external_id: str,
        policy_number: str,
        date_of_loss: str,
        claim_number: str,
        lob: str,
        org_external_id: str,
        suborg_external_id: str,
    ) -> PolicyApiRetrieveResponse:
        """Retrieves policy by external ID and date of loss via the configured policy source."""
        return await self.policy_source.retrieve_policy_by_external_id(
            external_id=external_id,
            policy_number=policy_number,
            date_of_loss=date_of_loss,
            claim_number=claim_number,
            lob=lob,
            org_external_id=org_external_id,
            suborg_external_id=suborg_external_id,
        )
