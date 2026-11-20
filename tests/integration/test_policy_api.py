from fastapi.testclient import TestClient


class TestPolicyApiIntegration:
    """End-to-end integration tests for Five Sigma Policy endpoints and error handling."""

    # =========================================================================
    # HTTP 200 Successful Responses
    # =========================================================================

    def test_search_policy_success_200(self, client: TestClient) -> None:
        payload = {"policy_number": "POL12345"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["policies"]) == 1
        policy = data["policies"][0]
        assert policy["policy_number"] == "POL12345"
        assert policy["customer_id"] == "CUST001"
        assert policy["insured_name"] == "John Smith"
        assert policy["status"] == "Active"
        assert policy["sub_organization"] == "ORGCA"
        assert policy["line_of_business"] == "Auto"
        assert policy["vin"] == "VIN123456789"

    def test_search_policy_by_insured_name_200(self, client: TestClient) -> None:
        payload = {"insured_name": "David"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["policies"][0]["policy_number"] == "POL67890"

    def test_get_policy_detail_success_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/POL12345")

        assert response.status_code == 200
        data = response.json()
        assert "policy" in data
        policy = data["policy"]
        assert policy["policy_number"] == "POL12345"
        assert policy["customer_id"] == "CUST001"
        assert policy["insured_name"] == "John Smith"
        assert policy["status"] == "Active"
        assert len(policy["insured_parties"]) >= 1
        assert len(policy["coverages"]) == 2

    def test_get_policy_coverages_success_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/POL12345/coverages")

        assert response.status_code == 200
        data = response.json()
        assert data["policy_number"] == "POL12345"
        assert data["total_count"] == 2
        coverages = data["coverages"]
        assert coverages[0]["code"] == "BI"
        assert coverages[0]["name"] == "Bodily Injury"
        assert len(coverages[0]["limits"]) == 1

    # =========================================================================
    # HTTP 404 NOT_FOUND
    # =========================================================================

    def test_get_policy_not_found_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/POL-DOES-NOT-EXIST")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "not found" in data["error"]["message"].lower()

    def test_search_policy_not_found_simulation_404(self, client: TestClient) -> None:
        payload = {"policy_number": "SIM-NOT-FOUND"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_coverages_not_found_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/POL-UNKNOWN/coverages")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"

    # =========================================================================
    # HTTP 409 MULTIPLE_MATCHES
    # =========================================================================

    def test_search_policy_multiple_matches_409(self, client: TestClient) -> None:
        payload = {"policy_number": "SIM-MULTIPLE"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "MULTIPLE_MATCHES"

    def test_get_policy_multiple_matches_409(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/SIM-MULTIPLE")

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "MULTIPLE_MATCHES"

    # =========================================================================
    # HTTP 503 PAS_UNAVAILABLE
    # =========================================================================

    def test_search_policy_pas_unavailable_503(self, client: TestClient) -> None:
        payload = {"policy_number": "SIM-PAS-UNAVAILABLE"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "PAS_UNAVAILABLE"

    def test_get_policy_pas_unavailable_503(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/SIM-PAS-UNAVAILABLE")

        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "PAS_UNAVAILABLE"

    # =========================================================================
    # HTTP 504 TIMEOUT
    # =========================================================================

    def test_search_policy_timeout_504(self, client: TestClient) -> None:
        payload = {"policy_number": "SIM-TIMEOUT"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "TIMEOUT"

    def test_get_policy_timeout_504(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/SIM-TIMEOUT")

        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "TIMEOUT"

    # =========================================================================
    # HTTP 502 MAPPING_ERROR
    # =========================================================================

    def test_search_policy_mapping_error_502(self, client: TestClient) -> None:
        payload = {"policy_number": "INVALID"}
        response = client.post("/api/v1/policies/search", json=payload)

        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "MAPPING_ERROR"

    def test_get_policy_mapping_error_502(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/INVALID")

        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "MAPPING_ERROR"

    # =========================================================================
    # Correlation ID & Validation
    # =========================================================================

    def test_correlation_id_propagation(self, client: TestClient) -> None:
        custom_corr_id = "test-corr-id-998877"
        headers = {"X-Correlation-ID": custom_corr_id}
        response = client.get("/api/v1/policies/POL12345", headers=headers)

        assert response.status_code == 200
        assert response.headers.get("X-Correlation-ID") == custom_corr_id

    def test_correlation_id_in_error_response(self, client: TestClient) -> None:
        custom_corr_id = "error-corr-id-12345"
        headers = {"X-Correlation-ID": custom_corr_id}
        response = client.get("/api/v1/policies/POL-NOT-FOUND", headers=headers)

        assert response.status_code == 404
        assert response.headers.get("X-Correlation-ID") == custom_corr_id
        data = response.json()
        assert data["correlation_id"] == custom_corr_id

    def test_search_request_validation_failure_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/policies/search", json={})

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
