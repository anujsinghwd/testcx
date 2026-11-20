from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable

from pydantic import ValidationError

from app.core.exceptions import PolicyMappingError
from app.core.logger import get_logger
from app.integrations.five_sigma.client import FiveSigmaClient
from app.schemas.policy import (
    Coverage,
    Deductible,
    Insured,
    Limit,
    Policy,
    PolicyCoveragesResponse,
    PolicyDetailResponse,
    PolicySearchRequest,
    PolicySearchResponse,
    PolicyVersion,
    SourceReference,
)

logger = get_logger("app.services.policy_service")


@runtime_checkable
class PolicyClientProtocol(Protocol):
    """Contract defining the operations required from any underlying policy system client."""

    async def search_policy(self, criteria: PolicySearchRequest) -> list[dict[str, Any]]: ...

    async def get_policy(self, policy_id: str) -> dict[str, Any]: ...

    async def get_coverages(self, policy_id: str) -> list[dict[str, Any]]: ...


class PolicyService:
    """Coordinates policy integration workflows independently of the underlying provider system."""

    def __init__(
        self,
        client: PolicyClientProtocol | None = None,
    ) -> None:
        # Default to Five Sigma as the initial policy provider
        self.client: PolicyClientProtocol = client or FiveSigmaClient()

    @staticmethod
    def _parse_date(value: Any, field_name: str) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            clean_str = value.strip()
            if not clean_str:
                raise ValueError(f"Empty date string for field '{field_name}'")
            try:
                return date.fromisoformat(clean_str[:10])
            except ValueError as err:
                raise ValueError(f"Invalid date format '{value}' for field '{field_name}'") from err
        raise ValueError(f"Expected date string for '{field_name}', got {type(value).__name__}")

    @staticmethod
    def _parse_decimal(value: Any, field_name: str) -> Decimal:
        if value is None:
            raise ValueError(f"Field '{field_name}' cannot be null")
        if isinstance(value, Decimal):
            if value < Decimal("0.00"):
                raise ValueError(f"Field '{field_name}' cannot be negative: {value}")
            return value
        if isinstance(value, (int, float, str)):
            try:
                dec = Decimal(str(value))
            except Exception as err:
                raise ValueError(f"Cannot convert '{value}' to Decimal for '{field_name}'") from err
            if dec < Decimal("0.00"):
                raise ValueError(f"Field '{field_name}' cannot be negative: {dec}")
            return dec
        raise ValueError(f"Invalid monetary type for '{field_name}'")

    @classmethod
    def _to_canonical_coverage(cls, raw: dict[str, Any]) -> Coverage:
        if not isinstance(raw, dict):
            raise ValueError("Coverage record must be a dictionary")

        code = raw.get("coverageCode") or raw.get("code")
        name = raw.get("coverageName") or raw.get("name")

        if not code or not name:
            raise ValueError("Coverage missing mandatory fields (coverageCode, coverageName)")

        limits: list[Limit] = []
        raw_limit = raw.get("limit") if "limit" in raw else raw.get("LimitAmount")
        if raw_limit is not None:
            limit_amount = cls._parse_decimal(raw_limit, "limit")
            limits.append(
                Limit(
                    name=str(name),
                    amount=limit_amount,
                    currency="USD",
                    description=f"{name} limit",
                )
            )

        deductibles: list[Deductible] = []
        raw_deductible = (
            raw.get("deductible") if "deductible" in raw else raw.get("DeductibleAmount")
        )
        if raw_deductible is not None:
            deductible_amount = cls._parse_decimal(raw_deductible, "deductible")
            deductibles.append(
                Deductible(
                    name=str(name),
                    amount=deductible_amount,
                    currency="USD",
                    description=f"{name} deductible",
                )
            )

        return Coverage(
            coverage_id=str(raw.get("coverageId") or code),
            code=str(code),
            name=str(name),
            status="Active",
            limits=limits,
            deductibles=deductibles,
            source_reference=SourceReference(
                system="Five Sigma",
                source_id=str(code),
            ),
        )

    @classmethod
    def _to_canonical_coverages(
        cls, raw_data: list[dict[str, Any]] | dict[str, Any]
    ) -> list[Coverage]:
        try:
            if isinstance(raw_data, dict):
                items = raw_data.get("coverages") or raw_data.get("POLICY_COVERAGES") or [raw_data]
            elif isinstance(raw_data, list):
                items = raw_data
            else:
                raise ValueError("Expected list or dict of coverages")

            coverages: list[Coverage] = []
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("Coverage item must be a dictionary")
                coverages.append(cls._to_canonical_coverage(item))
            return coverages

        except (KeyError, ValueError, TypeError, ValidationError) as err:
            raise PolicyMappingError(
                f"Failed to map coverages: {err}",
                details={"error": str(err)},
            ) from err

    @classmethod
    def _to_canonical_policy(cls, raw: dict[str, Any]) -> Policy:
        if not isinstance(raw, dict):
            raise PolicyMappingError(
                "Invalid policy data: expected dictionary structure",
                details={"provided_type": type(raw).__name__},
            )

        try:
            policy_number = raw.get("policyNumber") or raw.get("policy_number")
            status = raw.get("policyStatus") or raw.get("status")
            eff_val = raw.get("effectiveDate") or raw.get("effective_date")
            exp_val = raw.get("expirationDate") or raw.get("expiration_date")

            if not policy_number or not status or not eff_val or not exp_val:
                raise ValueError(
                    "Missing mandatory policy fields (policyNumber, policyStatus, effectiveDate, expirationDate)"
                )

            effective_date = cls._parse_date(eff_val, "effectiveDate")
            expiration_date = cls._parse_date(exp_val, "expirationDate")

            customer_id = raw.get("customerId") or raw.get("customer_id")
            insured_name = raw.get("insuredName") or raw.get("insured_name")

            insured_parties: list[Insured] = []
            if "holder" in raw and isinstance(raw["holder"], dict):
                holder = raw["holder"]
                full_name = f"{holder.get('firstName', '')} {holder.get('lastName', '')}".strip()
                insured_parties.append(
                    Insured(
                        customer_id=holder.get("customerId") or customer_id,
                        name=full_name or str(insured_name),
                        first_name=holder.get("firstName"),
                        last_name=holder.get("lastName"),
                        email=holder.get("email"),
                        phone_number=holder.get("phoneNumber"),
                        type="Primary",
                    )
                )
            elif insured_name:
                insured_parties.append(
                    Insured(
                        customer_id=customer_id,
                        name=str(insured_name),
                        type="Primary",
                    )
                )

            current_version = PolicyVersion(
                version_id="V1",
                effective_date=effective_date,
                expiration_date=expiration_date,
                status=str(status),
            )

            source_ref = SourceReference(
                system="Five Sigma",
                source_id=str(policy_number),
            )

            return Policy(
                policy_number=str(policy_number),
                customer_id=str(customer_id) if customer_id else None,
                insured_name=str(insured_name) if insured_name else None,
                status=str(status),
                effective_date=effective_date,
                expiration_date=expiration_date,
                sub_organization=raw.get("subOrganization") or raw.get("sub_organization"),
                line_of_business=raw.get("lineOfBusiness") or raw.get("line_of_business"),
                vin=raw.get("vin"),
                current_version=current_version,
                insured_parties=insured_parties,
                source_reference=source_ref,
            )

        except (KeyError, ValueError, TypeError, ValidationError) as err:
            raise PolicyMappingError(
                f"Failed to map policy data: {err}",
                details={"error": str(err)},
            ) from err

    async def search_policies(self, criteria: PolicySearchRequest) -> PolicySearchResponse:
        """Searches policies via the configured policy client and maps to canonical schema."""
        logger.info(
            "Searching policies: criteria=%s",
            criteria.model_dump(exclude_none=True),
        )

        raw_policies = await self.client.search_policy(criteria)
        canonical_policies: list[Policy] = [self._to_canonical_policy(raw) for raw in raw_policies]

        logger.info("Found %d policies", len(canonical_policies))
        return PolicySearchResponse(
            policies=canonical_policies,
            total_count=len(canonical_policies),
        )

    async def get_policy_detail(self, policy_id: str) -> PolicyDetailResponse:
        """Retrieves policy details via the configured policy client and maps to canonical schema."""
        logger.info("Retrieving policy detail for policy_id=%s", policy_id)

        raw_policy = await self.client.get_policy(policy_id)
        policy = self._to_canonical_policy(raw_policy)

        # Retrieve and attach coverages if available
        raw_coverages = await self.client.get_coverages(policy.policy_number)
        if raw_coverages:
            policy.coverages = self._to_canonical_coverages(raw_coverages)

        return PolicyDetailResponse(policy=policy)

    async def get_policy_coverages(self, policy_id: str) -> PolicyCoveragesResponse:
        """Retrieves coverages for a policy via the configured policy client."""
        logger.info("Retrieving policy coverages for policy_id=%s", policy_id)

        raw_coverages = await self.client.get_coverages(policy_id)
        canonical_coverages = self._to_canonical_coverages(raw_coverages)

        return PolicyCoveragesResponse(
            policy_number=policy_id,
            coverages=canonical_coverages,
            total_count=len(canonical_coverages),
        )
