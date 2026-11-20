from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.core.error_handlers import (
    integration_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import (
    MultiplePoliciesFoundError,
    PASTimeoutError,
    PASUnavailableError,
    PolicyMappingError,
    PolicyNotFoundError,
)
from app.core.logger import redact_sensitive_data
from app.integrations.five_sigma.client import FiveSigmaClient
from app.integrations.five_sigma.mapper import to_canonical as fs_to_canonical
from app.mappers.policy_mapper import (
    to_canonical_coverage,
    to_canonical_coverages,
    to_canonical_policy,
)
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
from app.services.policy_service import (
    PolicyClientProtocol,
    PolicyService,
)

# =============================================================================
# 1. Schema Tests
# =============================================================================


class TestPolicySchemas:
    """Tests for Policy Pydantic v2 schemas and validation rules."""

    def test_valid_policy_with_all_objects(self) -> None:
        source_ref = SourceReference(
            system="Five Sigma",
            source_id="POL12345",
            metadata={"source": "Five Sigma Policy System"},
        )
        limit = Limit(
            limit_id="LIM-1",
            name="Bodily Injury",
            amount=Decimal("100000.00"),
            currency="USD",
            description="Bodily injury limit",
        )
        deductible = Deductible(
            deductible_id="DED-1",
            name="Standard Collision",
            amount=Decimal("500.00"),
            currency="USD",
        )
        coverage = Coverage(
            coverage_id="COV-1",
            code="BI",
            name="Bodily Injury",
            effective_date=date(2026, 1, 1),
            expiration_date=date(2026, 12, 31),
            limits=[limit],
            deductibles=[deductible],
            source_reference=source_ref,
        )
        insured = Insured(
            customer_id="CUST001",
            name="John Smith",
            first_name="John",
            last_name="Smith",
            email="john.smith@test.com",
            phone_number="9999999999",
            type="Primary",
        )
        version = PolicyVersion(
            version_id="VER-1",
            effective_date=date(2026, 1, 1),
            expiration_date=date(2026, 12, 31),
            status="Active",
        )
        policy = Policy(
            policy_number="POL12345",
            customer_id="CUST001",
            insured_name="John Smith",
            status="Active",
            effective_date=date(2026, 1, 1),
            expiration_date=date(2026, 12, 31),
            sub_organization="ORGCA",
            line_of_business="Auto",
            vin="VIN123456789",
            current_version=version,
            insured_parties=[insured],
            coverages=[coverage],
            total_premium=Decimal("1500.00"),
            source_reference=source_ref,
        )

        assert policy.policy_number == "POL12345"
        assert policy.total_premium == Decimal("1500.00")
        assert len(policy.coverages) == 1
        assert len(policy.insured_parties) == 1
        assert policy.coverages[0].limits[0].amount == Decimal("100000.00")
        assert policy.coverages[0].deductibles[0].amount == Decimal("500.00")

    def test_invalid_negative_monetary_amount(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Limit(name="Negative Limit", amount=Decimal("-10.00"))
        assert "Input should be greater than or equal to 0" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            Deductible(name="Negative Ded", amount=Decimal("-500.00"))
        assert "Input should be greater than or equal to 0" in str(exc.value)

        with pytest.raises(ValidationError) as exc:
            Policy(
                policy_number="POL12345",
                status="Active",
                effective_date=date(2026, 1, 1),
                expiration_date=date(2026, 12, 31),
                total_premium=Decimal("-1.00"),
            )
        assert "Input should be greater than or equal to 0" in str(exc.value)

    def test_invalid_policy_dates(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Policy(
                policy_number="POL12345",
                status="Active",
                effective_date=date(2026, 6, 1),
                expiration_date=date(2026, 1, 1),
            )
        assert "expiration date cannot be earlier than effective date" in str(exc.value).lower()

        with pytest.raises(ValidationError) as exc:
            PolicyVersion(
                version_id="V-1",
                effective_date=date(2026, 12, 31),
                expiration_date=date(2026, 1, 1),
            )
        assert "expiration date cannot be earlier than effective date" in str(exc.value).lower()

        with pytest.raises(ValidationError) as exc:
            Coverage(
                code="BI",
                name="Bodily Injury",
                effective_date=date(2026, 6, 1),
                expiration_date=date(2026, 5, 31),
            )
        assert "expiration date cannot be earlier than effective date" in str(exc.value).lower()

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Policy.model_validate({"policy_number": "POL12345"})

    def test_rejects_unexpected_fields(self) -> None:
        with pytest.raises(ValidationError) as exc:
            PolicySearchRequest(
                policy_number="POL12345",
                unknown_attribute="not_allowed",  # type: ignore[call-arg]
            )
        assert "extra_forbidden" in str(exc.value)

    def test_search_request_requires_at_least_one_criterion(self) -> None:
        with pytest.raises(ValidationError) as exc:
            PolicySearchRequest()
        assert "At least one search criterion must be provided" in str(exc.value)


# =============================================================================
# 2. Five Sigma Client Tests
# =============================================================================


class TestFiveSigmaClient:
    """Tests for Five Sigma Mock Client and deterministic behavior simulation."""

    @pytest.mark.asyncio
    async def test_successful_search_by_policy_number(
        self, five_sigma_client: FiveSigmaClient
    ) -> None:
        criteria = PolicySearchRequest(policy_number="POL12345")
        results = await five_sigma_client.search_policy(criteria)

        assert len(results) == 1
        assert results[0]["policyNumber"] == "POL12345"
        assert results[0]["customerId"] == "CUST001"

    @pytest.mark.asyncio
    async def test_successful_search_by_insured_name(
        self, five_sigma_client: FiveSigmaClient
    ) -> None:
        criteria = PolicySearchRequest(insured_name="David")
        results = await five_sigma_client.search_policy(criteria)

        assert len(results) == 1
        assert results[0]["insuredName"] == "David Johnson"

    @pytest.mark.asyncio
    async def test_successful_search_by_status_and_vin(
        self, five_sigma_client: FiveSigmaClient
    ) -> None:
        criteria = PolicySearchRequest(status="Expired", vin="VIN67846666")
        results = await five_sigma_client.search_policy(criteria)

        assert len(results) == 1
        assert results[0]["policyNumber"] == "POL67890"

    @pytest.mark.asyncio
    async def test_successful_get_policy(self, five_sigma_client: FiveSigmaClient) -> None:
        policy = await five_sigma_client.get_policy("POL12345")
        assert policy["policyNumber"] == "POL12345"
        assert policy["insuredName"] == "John Smith"
        assert "holder" in policy
        assert policy["holder"]["email"] == "john.smith@test.com"

    @pytest.mark.asyncio
    async def test_successful_get_coverages(self, five_sigma_client: FiveSigmaClient) -> None:
        coverages = await five_sigma_client.get_coverages("POL12345")
        assert isinstance(coverages, list)
        assert len(coverages) == 2
        assert coverages[0]["coverageCode"] == "BI"
        assert coverages[0]["limit"] == 100000

    @pytest.mark.asyncio
    async def test_simulate_policy_not_found(self, five_sigma_client: FiveSigmaClient) -> None:
        with pytest.raises(PolicyNotFoundError):
            await five_sigma_client.get_policy("NONEXISTENT")

        with pytest.raises(PolicyNotFoundError):
            await five_sigma_client.get_policy("SIM-NOT-FOUND")

        with pytest.raises(PolicyNotFoundError):
            await five_sigma_client.search_policy(
                PolicySearchRequest(policy_number="SIM-NOT-FOUND")
            )

    @pytest.mark.asyncio
    async def test_simulate_multiple_matches(self, five_sigma_client: FiveSigmaClient) -> None:
        with pytest.raises(MultiplePoliciesFoundError):
            await five_sigma_client.search_policy(PolicySearchRequest(policy_number="SIM-MULTIPLE"))

        with pytest.raises(MultiplePoliciesFoundError):
            await five_sigma_client.get_policy("SIM-MULTIPLE")

    @pytest.mark.asyncio
    async def test_simulate_timeout(self, five_sigma_client: FiveSigmaClient) -> None:
        with pytest.raises(PASTimeoutError):
            await five_sigma_client.search_policy(PolicySearchRequest(policy_number="SIM-TIMEOUT"))

        with pytest.raises(PASTimeoutError):
            await five_sigma_client.get_policy("SIM-TIMEOUT")

    @pytest.mark.asyncio
    async def test_simulate_pas_unavailable(self, five_sigma_client: FiveSigmaClient) -> None:
        with pytest.raises(PASUnavailableError):
            await five_sigma_client.search_policy(
                PolicySearchRequest(policy_number="SIM-PAS-UNAVAILABLE")
            )

        with pytest.raises(PASUnavailableError):
            await five_sigma_client.get_policy("SIM-PAS-UNAVAILABLE")


# =============================================================================
# 3. Policy Mapper Tests
# =============================================================================


class TestPolicyMapper:
    """Tests for PolicyMapper empty function definitions."""

    def test_mapper_functions_exist_and_take_no_args(self) -> None:
        to_canonical_policy()
        to_canonical_coverage()
        to_canonical_coverages()
        fs_to_canonical()

    def test_service_map_valid_response(
        self, service: PolicyService, sample_raw_policy: dict[str, Any]
    ) -> None:
        policy = service._to_canonical_policy(sample_raw_policy)

        assert policy.policy_number == "POL12345"
        assert policy.customer_id == "CUST001"
        assert policy.insured_name == "John Smith"
        assert policy.status == "Active"
        assert policy.effective_date == date(2026, 1, 1)
        assert policy.expiration_date == date(2026, 12, 31)
        assert policy.sub_organization == "ORGCA"
        assert policy.line_of_business == "Auto"
        assert policy.vin == "VIN123456789"
        assert len(policy.insured_parties) == 1
        assert policy.insured_parties[0].email == "john.smith@test.com"

    def test_service_map_missing_required_fields(self, service: PolicyService) -> None:
        raw_missing: dict[str, Any] = {
            "policyNumber": "POL12345",
            "policyStatus": "Active",
        }
        with pytest.raises(PolicyMappingError) as exc:
            service._to_canonical_policy(raw_missing)
        assert "Missing mandatory policy fields" in str(exc.value)

    def test_service_map_invalid_monetary_value(self, service: PolicyService) -> None:
        raw_coverage = {
            "coverageCode": "BI",
            "coverageName": "Bodily Injury",
            "limit": -500,
        }
        with pytest.raises(ValueError) as exc:
            service._to_canonical_coverage(raw_coverage)
        assert "cannot be negative" in str(exc.value)

    def test_service_map_invalid_date_value(
        self, service: PolicyService, sample_raw_policy: dict[str, Any]
    ) -> None:
        sample_raw_policy["effectiveDate"] = "not-a-date"
        with pytest.raises(PolicyMappingError) as exc:
            service._to_canonical_policy(sample_raw_policy)
        assert "Invalid date format" in str(exc.value)

    def test_service_map_invalid_structure(self, service: PolicyService) -> None:
        with pytest.raises(PolicyMappingError) as exc:
            service._to_canonical_policy("invalid-payload")  # type: ignore[arg-type]
        assert "expected dictionary structure" in str(exc.value)

    def test_service_parse_date_formats(self, service: PolicyService) -> None:
        dt = datetime(2026, 5, 10, 14, 30, 0)
        assert service._parse_date(dt, "eff") == date(2026, 5, 10)
        d = date(2026, 5, 10)
        assert service._parse_date(d, "eff") == d

        with pytest.raises(ValueError):
            service._parse_date("", "eff")
        with pytest.raises(ValueError):
            service._parse_date(12345, "eff")

    def test_service_parse_decimal_formats(self, service: PolicyService) -> None:
        with pytest.raises(ValueError):
            service._parse_decimal(None, "limit")

        assert service._parse_decimal(100, "val") == Decimal("100")
        assert service._parse_decimal(99.5, "val") == Decimal("99.5")
        assert service._parse_decimal(Decimal("50.00"), "val") == Decimal("50.00")

        with pytest.raises(ValueError):
            service._parse_decimal({"dict": 1}, "val")

    def test_service_coverage_mapping_validation(self, service: PolicyService) -> None:
        with pytest.raises(ValueError):
            service._to_canonical_coverage({"coverageCode": "BI"})

        dict_input = {
            "coverages": [
                {
                    "coverageCode": "BI",
                    "coverageName": "Bodily Injury",
                    "limit": 100000,
                }
            ]
        }
        mapped = service._to_canonical_coverages(dict_input)
        assert len(mapped) == 1

        with pytest.raises(PolicyMappingError):
            service._to_canonical_coverages("invalid")  # type: ignore[arg-type]


# =============================================================================
# 4. Policy Service Tests
# =============================================================================


class TestPolicyService:
    """Tests for PolicyService workflow orchestration."""

    @pytest.mark.asyncio
    async def test_search_policies_success(self, service: PolicyService) -> None:
        req = PolicySearchRequest(policy_number="POL12345")
        response: PolicySearchResponse = await service.search_policies(req)

        assert response.total_count == 1
        assert response.policies[0].policy_number == "POL12345"

    @pytest.mark.asyncio
    async def test_get_policy_detail_success(self, service: PolicyService) -> None:
        response: PolicyDetailResponse = await service.get_policy_detail("POL12345")
        assert response.policy.policy_number == "POL12345"
        assert response.policy.insured_name == "John Smith"
        assert len(response.policy.coverages) == 2

    @pytest.mark.asyncio
    async def test_get_policy_coverages_success(self, service: PolicyService) -> None:
        response: PolicyCoveragesResponse = await service.get_policy_coverages("POL12345")
        assert response.policy_number == "POL12345"
        assert response.total_count == 2
        assert response.coverages[0].code == "BI"

    @pytest.mark.asyncio
    async def test_error_propagation(self, service: PolicyService) -> None:
        with pytest.raises(PolicyNotFoundError):
            await service.get_policy_detail("NONEXISTENT")

        with pytest.raises(PASUnavailableError):
            await service.get_policy_detail("SIM-PAS-UNAVAILABLE")

        with pytest.raises(PASTimeoutError):
            await service.get_policy_detail("SIM-TIMEOUT")


# =============================================================================
# 5. Redaction and Handler Fallback Tests
# =============================================================================


class TestRedactionAndHandlerFallbacks:
    """Tests for sensitive data redaction and error handlers."""

    def test_redact_sensitive_data(self) -> None:
        sample = {
            "api_key": "secret-123",
            "normal_field": "hello",
            "nested": [{"auth_token": "credential-456", "safe": "world"}],
            "auth_header": "Bearer token-xyz-789",
        }
        redacted = redact_sensitive_data(sample)
        assert redacted["api_key"] == "******"  # noqa: S105
        assert redacted["normal_field"] == "hello"
        assert redacted["nested"][0]["auth_token"] == "******"  # noqa: S105
        assert redacted["nested"][0]["safe"] == "world"
        assert redacted["auth_header"] == "Bearer ******"

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler(self) -> None:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/error-test",
            "headers": [(b"x-correlation-id", b"test-corr-500")],
        }
        request = Request(scope)
        response = await unhandled_exception_handler(request, RuntimeError("Boom"))
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_handler_fallbacks(self) -> None:
        headers: list[tuple[bytes, bytes]] = []
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/error-fallback",
            "headers": headers,
        }
        request = Request(scope)
        res1 = await integration_exception_handler(request, RuntimeError("Not integration"))
        assert res1.status_code == 500

        res2 = await validation_exception_handler(request, RuntimeError("Not validation"))
        assert res2.status_code == 500


# =============================================================================
# 6. Policy Service Provider Independence Tests
# =============================================================================


class TestPolicyServiceIndependence:
    """Verifies PolicyService is decoupled from any specific underlying policy provider."""

    def test_five_sigma_implements_protocol(self) -> None:
        client = FiveSigmaClient()
        assert isinstance(client, PolicyClientProtocol)

    @pytest.mark.asyncio
    async def test_policy_service_with_alternate_provider(self) -> None:
        class MockAlternateClient:
            async def search_policy(self, criteria: PolicySearchRequest) -> list[dict[str, Any]]:
                return [
                    {
                        "policy_number": "BHSI-POL-99",
                        "status": "Active",
                        "effective_date": "2026-01-01",
                        "expiration_date": "2027-01-01",
                    }
                ]

            async def get_policy(self, policy_id: str) -> dict[str, Any]:
                return {
                    "policy_number": policy_id,
                    "status": "Active",
                    "effective_date": "2026-01-01",
                    "expiration_date": "2027-01-01",
                }

            async def get_coverages(self, policy_id: str) -> list[dict[str, Any]]:
                return [
                    {
                        "code": "CUSTOM_COV",
                        "name": "Custom Liability",
                    }
                ]

        alt_client = MockAlternateClient()
        assert isinstance(alt_client, PolicyClientProtocol)

        service = PolicyService(client=alt_client)
        res = await service.search_policies(PolicySearchRequest(policy_number="BHSI"))
        assert res.total_count == 1
        assert res.policies[0].policy_number == "BHSI-POL-99"

        detail_res = await service.get_policy_detail("BHSI-POL-99")
        assert detail_res.policy.policy_number == "BHSI-POL-99"
        assert len(detail_res.policy.coverages) == 1

        cov_res = await service.get_policy_coverages("BHSI-POL-99")
        assert cov_res.total_count == 1
        assert cov_res.coverages[0].code == "CUSTOM_COV"
