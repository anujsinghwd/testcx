from typing import Any

from app.core.exceptions import (
    MultiplePoliciesFoundError,
    PASTimeoutError,
    PASUnavailableError,
    PolicyNotFoundError,
)
from app.core.logger import get_logger
from app.data.mock_data import POLICIES, POLICY_COVERAGES, POLICY_HOLDERS
from app.schemas.policy import PolicySearchRequest

logger = get_logger("app.integrations.five_sigma.client")


class FiveSigmaClient:
    """Client for Five Sigma Claims and Policy integration.

    Currently returns confirmed mock data from app/data/mock_data.py.
    When Five Sigma API access is available, replace mock retrieval with
    actual HTTP calls using httpx inside these methods.
    """

    def __init__(self) -> None:
        pass

    def _check_simulation_triggers(self, key: str | None) -> None:
        """Evaluates deterministic mock simulation triggers for test scenarios."""
        if not key:
            return

        normalized = key.strip().upper()
        if any(t in normalized for t in ("SIM-PAS-UNAVAILABLE", "UNAVAILABLE", "PAS_UNAVAILABLE")):
            raise PASUnavailableError("Five Sigma policy service is currently unavailable.")
        if any(t in normalized for t in ("SIM-TIMEOUT", "TIMEOUT")):
            raise PASTimeoutError("Request to Five Sigma timed out.")
        if any(t in normalized for t in ("SIM-MULTIPLE", "MULTIPLE")):
            raise MultiplePoliciesFoundError(f"Multiple matching policies found for '{key}'.")
        if any(t in normalized for t in ("SIM-NOT-FOUND", "NOT_FOUND")):
            raise PolicyNotFoundError(f"No policy found matching '{key}'.")

    async def search_policy(self, criteria: PolicySearchRequest) -> list[dict[str, Any]]:
        """Searches Five Sigma policies matching the given criteria."""
        self._check_simulation_triggers(criteria.policy_number)
        self._check_simulation_triggers(criteria.insured_name)

        if criteria.policy_number and "INVALID" in criteria.policy_number.upper():
            return [{"invalid_structure": True}]

        results: list[dict[str, Any]] = []
        for p in POLICIES:
            match = True
            if (
                criteria.policy_number
                and criteria.policy_number.upper() not in p["policyNumber"].upper()
            ):
                match = False
            if (
                match
                and criteria.insured_name
                and criteria.insured_name.upper() not in p["insuredName"].upper()
            ):
                match = False
            if (
                match
                and criteria.customer_id
                and criteria.customer_id.upper() != p["customerId"].upper()
            ):
                match = False
            if (
                match
                and criteria.line_of_business
                and criteria.line_of_business.upper() != p["lineOfBusiness"].upper()
            ):
                match = False
            if match and criteria.status and criteria.status.upper() != p["policyStatus"].upper():
                match = False
            if match and criteria.vin and criteria.vin.upper() != p["vin"].upper():
                match = False

            if match:
                results.append(dict(p))

        logger.info(
            "Five Sigma policy search: criteria=%s, matched=%d",
            criteria.model_dump(exclude_none=True),
            len(results),
        )
        return results

    async def get_policy(self, policy_id: str) -> dict[str, Any]:
        """Retrieves a single policy by policy number from Five Sigma."""
        self._check_simulation_triggers(policy_id)

        if "INVALID" in policy_id.upper():
            return {"invalid_structure": True}

        for p in POLICIES:
            if p["policyNumber"].upper() == policy_id.upper():
                policy_dict = dict(p)
                # Enrich with matching policy holder details if available
                matching_holder = next(
                    (h for h in POLICY_HOLDERS if h["customerId"] == p["customerId"]),
                    None,
                )
                if matching_holder:
                    policy_dict["holder"] = dict(matching_holder)
                return policy_dict

        raise PolicyNotFoundError(f"Policy '{policy_id}' not found in Five Sigma.")

    async def get_coverages(self, policy_id: str) -> list[dict[str, Any]]:
        """Retrieves coverages for a given policy from Five Sigma."""
        self._check_simulation_triggers(policy_id)

        if "INVALID" in policy_id.upper():
            return [{"invalid_coverage": True}]

        normalized_id = policy_id.upper()
        for pol_num, coverages in POLICY_COVERAGES.items():
            if pol_num.upper() == normalized_id:
                return [dict(cov) for cov in coverages]

        # Verify whether the policy itself exists
        if not any(p["policyNumber"].upper() == normalized_id for p in POLICIES):
            raise PolicyNotFoundError(f"Policy '{policy_id}' not found in Five Sigma.")

        return []
