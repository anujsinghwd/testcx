"""Integration tests for Policy Search API adhering to Five Sigma v2 contract."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.exceptions import DatabaseError

VALID_API_KEY = "test-api-key"
HEADERS = {"X-API-Key": VALID_API_KEY}


# ==============================================================================
# Search API Tests: GET /policies/search
# ==============================================================================


def test_search_policies_valid_single_match(client: TestClient) -> None:
    """GET /policies/search with valid parameters returns single matching policy."""
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
    assert result["display_fields"]["policy_number"] == "BHSI-GL-2024-001"
    assert result["display_fields"]["policy_holder"] == "Acme Corporation"
    assert "retrieval_token" in result
    assert len(result["retrieval_token"]) > 0
    assert len(data["display_schema"]) > 0


def test_search_policies_multiple_matches(client: TestClient) -> None:
    """GET /policies/search with general criteria returns multiple matching policies."""
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


def test_search_policies_no_matching_policy(client: TestClient) -> None:
    """GET /policies/search when no policy matches returns empty results array."""
    response = client.get(
        "/policies/search",
        params={
            "lob": "AUTO",
            "org_external_id": "BHSI-ORG-01",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 0
    assert data["results"] == []
    assert len(data["display_schema"]) > 0


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
