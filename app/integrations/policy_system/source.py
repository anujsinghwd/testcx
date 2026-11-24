"""PolicySource abstract interface defining data source contracts for policy search and retrieval."""

from abc import ABC, abstractmethod

from app.schemas.policy import PolicyApiRetrieveResponse, PolicyApiSearchResponse


class PolicySource(ABC):
    """Abstract interface for any policy data source (MySQL mock repository, PAS adapter, etc.)."""

    @abstractmethod
    async def search_policies(
        self,
        lob: str,
        org_external_id: str,
        suborg_external_id: str | None = None,
        policy_number: str | None = None,
    ) -> PolicyApiSearchResponse:
        """Search policies matching criteria.

        Args:
            lob: Line of business. Exactly one value (required).
            org_external_id: Five Sigma organization external ID (required).
            suborg_external_id: Sub-organization external ID (optional).
            policy_number: Organization-configured search field (optional).

        Returns:
            PolicyApiSearchResponse with total_results, display_schema, and results.
        """
        raise NotImplementedError

    @abstractmethod
    async def retrieve_policy_by_token(
        self,
        retrieval_token: str,
    ) -> PolicyApiRetrieveResponse:
        """Retrieve policy details associated with an opaque retrieval token.

        Args:
            retrieval_token: Opaque token issued during policy search.

        Returns:
            PolicyApiRetrieveResponse containing the complete policy details.
        """
        raise NotImplementedError

    @abstractmethod
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
        """Retrieve policy details by external ID and date of loss.

        Args:
            external_id: Policy external ID.
            policy_number: Policy number.
            date_of_loss: Date of loss (YYYY-MM-DD).
            claim_number: Five Sigma claim number reference.
            lob: Line of business.
            org_external_id: Organization external ID.
            suborg_external_id: Sub-organization external ID.

        Returns:
            PolicyApiRetrieveResponse containing the policy in force on the date of loss.
        """
        raise NotImplementedError
