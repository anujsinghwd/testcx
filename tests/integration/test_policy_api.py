"""Integration tests for Policy Search API adhering strictly to Five Sigma v2 contract."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.exceptions import DatabaseError

VALID_API_KEY = "test-api-key"
HEADERS = {"X-API-Key": VALID_API_KEY}


# ==============================================================================
# 1. Search with Required lob and org_external_id
# ==============================================================================


def test_search_policies_with_required_lob_and_org_only(client: TestClient) -> None:
    """GET /policies/search using required lob and org_external_id returns 200 with matching policies."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2

    # Verify display schema matches Five Sigma v2 contract
    schema_ids = [field["id"] for field in data["display_schema"]]
    assert schema_ids == ["policy_number", "insured_name", "effective_date", "expiration_date"]


# ==============================================================================
# 2. Search with Optional suborg_external_id
# ==============================================================================


def test_search_policies_with_optional_suborg_external_id(client: TestClient) -> None:
    """GET /policies/search with suborg_external_id filters to the specific sub-organization."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "suborg_external_id": "BHSI-SUB-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["display_fields"]["policy_number"] == "BHSI-GL-2024-001"


# ==============================================================================
# 3. Search with Optional policy_number
# ==============================================================================


def test_search_policies_with_optional_policy_number(client: TestClient) -> None:
    """GET /policies/search with optional policy_number parameter returns single matching policy."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "policy_number": "BHSI-GL-2024-001",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    result = data["results"][0]

    # Verify exact display fields from contract
    assert result["display_fields"]["policy_number"] == "BHSI-GL-2024-001"
    assert result["display_fields"]["insured_name"] == "Acme Corporation"
    assert result["display_fields"]["effective_date"] == "2024-01-01"
    assert result["display_fields"]["expiration_date"] == "2025-01-01"
    assert "retrieval_token" in result
    assert len(result["retrieval_token"]) > 0


# ==============================================================================
# 4. Search Without policy_number
# ==============================================================================


def test_search_policies_without_policy_number(client: TestClient) -> None:
    """GET /policies/search omitting policy_number allows search using lob and org_external_id."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2


# ==============================================================================
# 5. Combined Search (All Parameters)
# ==============================================================================


def test_search_policies_combined_all_parameters(client: TestClient) -> None:
    """GET /policies/search combining lob, org_external_id, suborg_external_id, and policy_number."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "suborg_external_id": "BHSI-SUB-01",
            "policy_number": "BHSI-GL-2024-001",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert data["results"][0]["display_fields"]["policy_number"] == "BHSI-GL-2024-001"
    assert data["results"][0]["display_fields"]["insured_name"] == "Acme Corporation"


# ==============================================================================
# 6. Search with No Matching Records (HTTP 200)
# ==============================================================================


def test_search_policies_no_matching_records_returns_200(client: TestClient) -> None:
    """GET /policies/search when no policy matches returns HTTP 200 with empty results array."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "policy_number": "NON_EXISTENT_POLICY_123",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 0
    assert data["results"] == []
    assert len(data["display_schema"]) == 4


# ==============================================================================
# 7. Multiple Matching Records
# ==============================================================================


def test_search_policies_multiple_matching_records(client: TestClient) -> None:
    """GET /policies/search with general criteria returns multiple records."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2


# ==============================================================================
# 8. Missing Required Parameters (HTTP 422)
# ==============================================================================


def test_search_policies_missing_required_lob(client: TestClient) -> None:
    """GET /policies/search missing required lob query parameter returns 422."""
    response = client.get(
        "/policies/search",
        params={"org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_search_policies_missing_required_org_external_id(client: TestClient) -> None:
    """GET /policies/search missing required org_external_id returns 422."""
    response = client.get(
        "/policies/search",
        params={"lob": "GL"},
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


# ==============================================================================
# 9. Authentication Errors (HTTP 401)
# ==============================================================================


def test_search_policies_missing_api_key(client: TestClient) -> None:
    """GET /policies/search without API key returns 401 Unauthorized."""
    response = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_search_policies_invalid_api_key(client: TestClient) -> None:
    """GET /policies/search with invalid API key returns 401 Unauthorized."""
    response = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers={"X-API-Key": "invalid-secret-key"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 10. Database Failure (HTTP 500)
# ==============================================================================


def test_search_policies_database_failure(client: TestClient) -> None:
    """GET /policies/search returns 500 when database failure occurs."""
    with patch(
        "app.repositories.policy_repository.MySQLPolicyRepository.search_policies",
        side_effect=DatabaseError("Database disk I/O error"),
    ):
        response = client.get(
            "/policies/search",
            params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
            headers=HEADERS,
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "DATABASE_ERROR"


# ==============================================================================
# POST /policies/search Integration Tests (Five Sigma v2)
# ==============================================================================


def test_post_search_policies_valid_with_all_fields(client: TestClient) -> None:
    """POST /policies/search with all fields returns HTTP 200 with matching policy."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "suborg_external_id": "BHSI-SUB-01",
            "policy_number": "BHSI-GL-2024-001",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    res = data["results"][0]
    assert res["display_fields"]["policy_number"] == "BHSI-GL-2024-001"
    assert res["display_fields"]["insured_name"] == "Acme Corporation"
    assert res["display_fields"]["effective_date"] == "2024-01-01"
    assert res["display_fields"]["expiration_date"] == "2025-01-01"
    assert "retrieval_token" in res


def test_post_search_policies_without_suborg_external_id(client: TestClient) -> None:
    """POST /policies/search without suborg_external_id succeeds with optional field omitted."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "policy_number": "BHSI-GL-2024-001",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert data["results"][0]["display_fields"]["policy_number"] == "BHSI-GL-2024-001"


def test_post_search_policies_without_policy_number(client: TestClient) -> None:
    """POST /policies/search without policy_number returns all matching policies for LOB & org."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2


def test_post_search_policies_with_policy_number(client: TestClient) -> None:
    """POST /policies/search with policy_number filters to single policy."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "policy_number": "BHSI-GL-2024-003",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 1
    assert data["results"][0]["display_fields"]["policy_number"] == "BHSI-GL-2024-003"
    assert data["results"][0]["display_fields"]["insured_name"] == "Apex Manufacturing LLC"


def test_post_search_policies_no_matching_policies(client: TestClient) -> None:
    """POST /policies/search when no policy matches returns HTTP 200 with empty results array."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "policy_number": "NON_EXISTENT_POLICY_POST",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 0
    assert data["results"] == []
    assert len(data["display_schema"]) == 4


def test_post_search_policies_multiple_matching_policies(client: TestClient) -> None:
    """POST /policies/search with broader criteria returns multiple matching records."""
    response = client.post(
        "/policies/search",
        json={
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 2
    assert len(data["results"]) == 2


def test_post_search_policies_missing_lob(client: TestClient) -> None:
    """POST /policies/search missing required lob in body returns HTTP 422."""
    response = client.post(
        "/policies/search",
        json={"org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_post_search_policies_missing_org_external_id(client: TestClient) -> None:
    """POST /policies/search missing required org_external_id in body returns HTTP 422."""
    response = client.post(
        "/policies/search",
        json={"lob": "GL"},
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_post_search_policies_missing_api_key(client: TestClient) -> None:
    """POST /policies/search without API key returns HTTP 401 Unauthorized."""
    response = client.post(
        "/policies/search",
        json={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_post_search_policies_invalid_api_key(client: TestClient) -> None:
    """POST /policies/search with invalid API key returns HTTP 401 Unauthorized."""
    response = client.post(
        "/policies/search",
        json={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers={"X-API-Key": "invalid-secret-key"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_post_search_policies_database_failure(client: TestClient) -> None:
    """POST /policies/search returns HTTP 500 when database failure occurs."""
    with patch(
        "app.repositories.policy_repository.MySQLPolicyRepository.search_policies",
        side_effect=DatabaseError("Database disk I/O error"),
    ):
        response = client.post(
            "/policies/search",
            json={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
            headers=HEADERS,
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "DATABASE_ERROR"


def test_post_search_policies_response_structure_contract(client: TestClient) -> None:
    """POST /policies/search response strictly matches the Five Sigma v2 display schema contract."""
    response = client.post(
        "/policies/search",
        json={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    schema_ids = [field["id"] for field in data["display_schema"]]
    assert schema_ids == ["policy_number", "insured_name", "effective_date", "expiration_date"]


# ==============================================================================
# Policy Retrieval by Token Tests (GET /policies/retrieve_by_token)
# ==============================================================================


def test_retrieve_by_token_valid_returns_200_and_full_policy(client: TestClient) -> None:
    """GET /policies/retrieve_by_token with a valid token returns HTTP 200 and complete policy."""
    # Step 1: Perform search to obtain a valid retrieval token
    search_res = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    assert search_res.status_code == 200
    token = search_res.json()["results"][0]["retrieval_token"]

    # Step 2: Retrieve policy using token
    response = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token},
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert "policy" in data
    policy = data["policy"]

    # Verify required policy fields
    assert policy["version"] == 1
    assert policy["external_id"] == "POL-BHSI-001"
    assert policy["policy_number"] == "BHSI-GL-2024-001"
    assert policy["effective_date"] == "2024-01-01"
    assert policy["expiration_date"] == "2025-01-01"
    assert policy["policy_holder_contact_ref_id"] == "CNT-001"
    assert policy["lob"] == "GL"
    assert policy["sub_organization_external_id"] == "BHSI-SUB-01"
    assert policy["is_claims_made"] is False

    # Verify contacts and phone numbers
    assert len(policy["contacts"]) == 1
    contact = policy["contacts"][0]
    assert contact["ref_id"] == "CNT-001"
    assert contact["external_id"] == "CUST-001"
    assert contact["is_company"] is True
    assert contact["company_name"] == "Acme Corporation"
    assert contact["address1"] == "100 Financial Way"
    assert contact["city"] == "Boston"
    assert contact["state"] == "MA"
    assert contact["zipcode"] == "02110"
    assert contact["country"] == "USA"

    assert len(contact["phones"]) == 1
    assert contact["phones"][0]["phone_number"] == "+1-800-555-0100"
    assert contact["phones"][0]["phone_type"] == "work"


def test_retrieve_by_token_unknown_token_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_token with an unknown token returns HTTP 404 Not Found."""
    response = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": "non-existent-opaque-token-12345"},
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_retrieve_by_token_missing_token_returns_422(client: TestClient) -> None:
    """GET /policies/retrieve_by_token without retrieval_token returns HTTP 422 Validation Error."""
    response = client.get(
        "/policies/retrieve_by_token",
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_retrieve_by_token_missing_api_key_returns_401(client: TestClient) -> None:
    """GET /policies/retrieve_by_token without API key returns HTTP 401 Unauthorized."""
    response = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": "some-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_retrieve_by_token_invalid_api_key_returns_401(client: TestClient) -> None:
    """GET /policies/retrieve_by_token with invalid API key returns HTTP 401 Unauthorized."""
    response = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": "some-token"},
        headers={"X-API-Key": "wrong-secret-key"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_retrieve_by_token_database_failure_returns_500(client: TestClient) -> None:
    """GET /policies/retrieve_by_token returns HTTP 500 when database failure occurs."""
    with patch(
        "app.repositories.policy_repository.MySQLPolicyRepository.retrieve_policy_by_token",
        side_effect=DatabaseError("Database query timed out"),
    ):
        response = client.get(
            "/policies/retrieve_by_token",
            params={"retrieval_token": "valid-looking-token"},
            headers=HEADERS,
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "DATABASE_ERROR"


def test_retrieve_by_token_isolation_between_different_policies(client: TestClient) -> None:
    """Verifies that retrieval tokens strictly isolate policies and return only the linked policy."""
    # Search for GL policy
    res_gl = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01", "policy_number": "BHSI-GL-2024-001"},
        headers=HEADERS,
    )
    token_gl = res_gl.json()["results"][0]["retrieval_token"]

    # Search for PROPERTY policy
    res_prop = client.get(
        "/policies/search",
        params={"lob": "PROPERTY", "org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    token_prop = res_prop.json()["results"][0]["retrieval_token"]

    # Retrieve each by its own token
    pol_gl = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token_gl},
        headers=HEADERS,
    ).json()["policy"]

    pol_prop = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token_prop},
        headers=HEADERS,
    ).json()["policy"]

    assert pol_gl["policy_number"] == "BHSI-GL-2024-001"
    assert pol_gl["lob"] == "GL"

    assert pol_prop["policy_number"] == "BHSI-PROP-2024-002"
    assert pol_prop["lob"] == "PROPERTY"


def test_retrieve_by_token_consistency(client: TestClient) -> None:
    """Verifies that repeatedly calling retrieval with the same token returns identical data."""
    search_res = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    token = search_res.json()["results"][0]["retrieval_token"]

    res_1 = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token},
        headers=HEADERS,
    )
    res_2 = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token},
        headers=HEADERS,
    )

    assert res_1.status_code == 200
    assert res_2.status_code == 200
    assert res_1.json() == res_2.json()


def test_retrieve_by_token_api_v1_prefix(client: TestClient) -> None:
    """GET /api/v1/policies/retrieve_by_token is routed identically to /policies/retrieve_by_token."""
    search_res = client.get(
        "/policies/search",
        params={"lob": "GL", "org_external_id": "BHSI-ORG-01"},
        headers=HEADERS,
    )
    token = search_res.json()["results"][0]["retrieval_token"]

    response = client.get(
        "/api/v1/policies/retrieve_by_token",
        params={"retrieval_token": token},
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["policy"]["policy_number"] == "BHSI-GL-2024-001"


def test_end_to_end_search_post_then_retrieve(client: TestClient) -> None:
    """Verifies end-to-end flow: POST /policies/search -> get token -> GET /policies/retrieve_by_token."""
    post_res = client.post(
        "/policies/search",
        json={"lob": "GL", "org_external_id": "BHSI-ORG-01", "policy_number": "BHSI-GL-2024-001"},
        headers=HEADERS,
    )
    assert post_res.status_code == 200
    results = post_res.json()["results"]
    assert len(results) == 1
    token = results[0]["retrieval_token"]

    retrieve_res = client.get(
        "/policies/retrieve_by_token",
        params={"retrieval_token": token},
        headers=HEADERS,
    )
    assert retrieve_res.status_code == 200
    retrieved_policy = retrieve_res.json()["policy"]
    assert retrieved_policy["policy_number"] == "BHSI-GL-2024-001"
    assert retrieved_policy["external_id"] == "POL-BHSI-001"
    assert retrieved_policy["policy_holder_contact_ref_id"] == "CNT-001"
    assert retrieved_policy["contacts"][0]["company_name"] == "Acme Corporation"


# ==============================================================================
# Policy Retrieval by External ID Tests (GET /policies/retrieve_by_external_id)
# ==============================================================================

VALID_EXTERNAL_ID_PARAMS = {
    "external_id": "POL-BHSI-001",
    "policy_number": "BHSI-GL-2024-001",
    "date_of_loss": "2024-06-15",
    "claim_number": "CLM-001",
    "lob": "GL",
    "org_external_id": "BHSI-ORG-01",
    "suborg_external_id": "BHSI-SUB-01",
}


def test_retrieve_by_external_id_valid_and_in_force_returns_200(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with matching parameters returns HTTP 200 and full policy."""
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=VALID_EXTERNAL_ID_PARAMS,
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert "policy" in data
    policy = data["policy"]

    assert policy["version"] == 1
    assert policy["external_id"] == "POL-BHSI-001"
    assert policy["policy_number"] == "BHSI-GL-2024-001"
    assert policy["effective_date"] == "2024-01-01"
    assert policy["expiration_date"] == "2025-01-01"
    assert policy["policy_holder_contact_ref_id"] == "CNT-001"
    assert policy["lob"] == "GL"
    assert policy["sub_organization_external_id"] == "BHSI-SUB-01"
    assert policy["is_claims_made"] is False
    assert len(policy["contacts"]) == 1
    assert policy["contacts"][0]["company_name"] == "Acme Corporation"


def test_retrieve_by_external_id_not_in_force_after_expiration_returns_404(
    client: TestClient,
) -> None:
    """GET /policies/retrieve_by_external_id with loss date after expiration returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "date_of_loss": "2026-01-15"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "was not in force on date of loss" in data["error"]["message"]


def test_retrieve_by_external_id_not_in_force_before_effective_returns_404(
    client: TestClient,
) -> None:
    """GET /policies/retrieve_by_external_id with loss date before effective date returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "date_of_loss": "2023-12-15"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "was not in force on date of loss" in data["error"]["message"]


def test_retrieve_by_external_id_unknown_external_id_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with unknown external_id returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "external_id": "PAS-POL-UNKNOWN-999"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()


def test_retrieve_by_external_id_mismatched_policy_number_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with mismatched policy_number returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "policy_number": "WRONG-POLICY-NUM"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "policy number" in data["error"]["message"].lower()


def test_retrieve_by_external_id_mismatched_lob_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with mismatched lob returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "lob": "PROPERTY"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "line of business" in data["error"]["message"].lower()


def test_retrieve_by_external_id_mismatched_org_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with mismatched org_external_id returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "org_external_id": "WRONG-ORG-99"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "organization" in data["error"]["message"].lower()


def test_retrieve_by_external_id_mismatched_suborg_returns_404(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with mismatched suborg_external_id returns HTTP 404."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "suborg_external_id": "WRONG-SUBORG-99"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert "sub-organization" in data["error"]["message"].lower()


def test_retrieve_by_external_id_missing_required_parameter_returns_422(
    client: TestClient,
) -> None:
    """GET /policies/retrieve_by_external_id missing a required query parameter returns HTTP 422."""
    params = {k: v for k, v in VALID_EXTERNAL_ID_PARAMS.items() if k != "claim_number"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_retrieve_by_external_id_invalid_date_format_returns_422(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with invalid date format returns HTTP 422."""
    params = {**VALID_EXTERNAL_ID_PARAMS, "date_of_loss": "15-06-2024"}
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=params,
        headers=HEADERS,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_retrieve_by_external_id_missing_api_key_returns_401(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id without API key returns HTTP 401 Unauthorized."""
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=VALID_EXTERNAL_ID_PARAMS,
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_retrieve_by_external_id_invalid_api_key_returns_401(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id with invalid API key returns HTTP 401 Unauthorized."""
    response = client.get(
        "/policies/retrieve_by_external_id",
        params=VALID_EXTERNAL_ID_PARAMS,
        headers={"X-API-Key": "invalid-secret"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_retrieve_by_external_id_database_failure_returns_500(client: TestClient) -> None:
    """GET /policies/retrieve_by_external_id returns HTTP 500 on database failure."""
    with patch(
        "app.repositories.policy_repository.MySQLPolicyRepository.retrieve_policy_by_external_id",
        side_effect=DatabaseError("Database query timed out"),
    ):
        response = client.get(
            "/policies/retrieve_by_external_id",
            params=VALID_EXTERNAL_ID_PARAMS,
            headers=HEADERS,
        )
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "DATABASE_ERROR"


def test_retrieve_by_external_id_api_v1_prefix(client: TestClient) -> None:
    """GET /api/v1/policies/retrieve_by_external_id is routed identically to /policies/retrieve_by_external_id."""
    response = client.get(
        "/api/v1/policies/retrieve_by_external_id",
        params=VALID_EXTERNAL_ID_PARAMS,
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["policy"]["policy_number"] == "BHSI-GL-2024-001"
