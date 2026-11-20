from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.clients import get_policy_service
from app.schemas.errors import ErrorResponse
from app.schemas.policy import (
    PolicyCoveragesResponse,
    PolicyDetailResponse,
    PolicySearchRequest,
    PolicySearchResponse,
)
from app.services.policy_service import PolicyService

router = APIRouter()


@router.post(
    "/search",
    response_model=PolicySearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search policies",
    description="Search for policies in Five Sigma matching query parameters.",
    responses={
        404: {"model": ErrorResponse, "description": "No policy found"},
        409: {"model": ErrorResponse, "description": "Multiple matches found"},
        502: {"model": ErrorResponse, "description": "Mapping error"},
        503: {"model": ErrorResponse, "description": "PAS unavailable"},
        504: {"model": ErrorResponse, "description": "PAS timeout"},
    },
)
async def search_policies(
    criteria: PolicySearchRequest,
    service: Annotated[PolicyService, Depends(get_policy_service)],
) -> PolicySearchResponse:
    return await service.search_policies(criteria)


@router.get(
    "/{id}",
    response_model=PolicyDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get policy detail",
    description="Retrieve comprehensive details for a specific policy by policy number.",
    responses={
        404: {"model": ErrorResponse, "description": "Policy not found"},
        409: {"model": ErrorResponse, "description": "Multiple matches found"},
        502: {"model": ErrorResponse, "description": "Mapping error"},
        503: {"model": ErrorResponse, "description": "PAS unavailable"},
        504: {"model": ErrorResponse, "description": "PAS timeout"},
    },
)
async def get_policy_detail(
    id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
) -> PolicyDetailResponse:
    return await service.get_policy_detail(policy_id=id)


@router.get(
    "/{id}/coverages",
    response_model=PolicyCoveragesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get policy coverages",
    description="Retrieve coverages and limits for a specific policy.",
    responses={
        404: {"model": ErrorResponse, "description": "Policy coverages not found"},
        502: {"model": ErrorResponse, "description": "Mapping error"},
        503: {"model": ErrorResponse, "description": "PAS unavailable"},
        504: {"model": ErrorResponse, "description": "PAS timeout"},
    },
)
async def get_policy_coverages(
    id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
) -> PolicyCoveragesResponse:
    return await service.get_policy_coverages(policy_id=id)
