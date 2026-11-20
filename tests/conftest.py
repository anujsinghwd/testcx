import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.integrations.five_sigma.client import FiveSigmaClient
from app.main import app
from app.services.policy_service import PolicyService


@pytest.fixture
def sample_raw_policy() -> dict[str, Any]:
    fixture_path = Path(__file__).parent / "fixtures" / "policy_response.json"
    with open(fixture_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


@pytest.fixture
def five_sigma_client() -> FiveSigmaClient:
    return FiveSigmaClient()


@pytest.fixture
def service(five_sigma_client: FiveSigmaClient) -> PolicyService:
    return PolicyService(client=five_sigma_client)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
