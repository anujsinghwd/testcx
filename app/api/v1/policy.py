"""Policy API route definitions implementing Five Sigma v2 Policy Search and Retrieval."""

from fastapi import APIRouter, Depends, Query, Security

from app.core.auth import verify_api_key
from app.dependencies.clients import get_policy_service
from app.schemas.policy import (
    PolicyApiRetrieveResponse,
    PolicyApiSearchResponse,
    PolicySearchRequest,
)
from app.services.policy_service import PolicyService

router = APIRouter()


@router.get(
    "/search",
    response_model=PolicyApiSearchResponse,
    summary="Search policies via GET (Five Sigma v2)",
    description=(
        "Search policies matching Line of Business and Organization criteria via query parameters. "
        "Allows optional filtering by suborg_external_id and policy_number. "
        "Returns display schema and policy items with opaque retrieval tokens."
    ),
)
async def search_policies(
    lob: str = Query(..., description="Line of business. Exactly one value."),
    org_external_id: str = Query(..., description="Five Sigma organization external ID."),
    suborg_external_id: str | None = Query(None, description="Sub-organization external ID."),
    policy_number: str | None = Query(None, description="Organization-configured search field."),
    service: PolicyService = Depends(get_policy_service),
    _api_key: str = Security(verify_api_key),
) -> PolicyApiSearchResponse:
    """GET /policies/search endpoint consumed by Five Sigma during FNOL."""
    return await service.search_policies(
        lob=lob,
        org_external_id=org_external_id,
        suborg_external_id=suborg_external_id,
        policy_number=policy_number,
    )


@router.post(
    "/search",
    response_model=PolicyApiSearchResponse,
    summary="Search policies via POST (Five Sigma v2)",
    description=(
        "Search policies matching Line of Business and Organization criteria via JSON body. "
        "Allows optional filtering by suborg_external_id and policy_number. "
        "Returns display schema and policy items with opaque retrieval tokens."
    ),
)
async def search_policies_post(
    request: PolicySearchRequest,
    service: PolicyService = Depends(get_policy_service),
    _api_key: str = Security(verify_api_key),
) -> PolicyApiSearchResponse:
    """POST /policies/search endpoint consumed by Five Sigma during FNOL."""
    return await service.search_policies(
        lob=request.lob,
        org_external_id=request.org_external_id,
        suborg_external_id=request.suborg_external_id,
        policy_number=request.policy_number,
    )


@router.get(
    "/retrieve_by_token",
    response_model=PolicyApiRetrieveResponse,
    response_model_exclude_none=True,
    summary="Retrieve policy by token (Five Sigma v2)",
    description=(
        "Retrieve the complete policy details associated with an opaque retrieval token "
        "previously issued during Policy Search."
    ),
)
async def retrieve_policy_by_token(
    retrieval_token: str = Query(
        ...,
        description="Opaque retrieval token issued by Policy Search.",
    ),
    service: PolicyService = Depends(get_policy_service),
    _api_key: str = Security(verify_api_key),
) -> PolicyApiRetrieveResponse:
    """GET /policies/retrieve_by_token endpoint consumed by Five Sigma during policy selection."""
    return await service.retrieve_policy_by_token(retrieval_token=retrieval_token)


@router.get(
    "/retrieve_by_external_id",
    response_model=PolicyApiRetrieveResponse,
    response_model_exclude_none=True,
    summary="Retrieve policy by external ID (Five Sigma v2)",
    description=(
        "Retrieve the policy as it existed on the supplied date_of_loss using its external ID, "
        "policy number, line of business, and organization context."
    ),
)
async def retrieve_policy_by_external_id(
    external_id: str = Query(..., description="External ID of the policy."),
    policy_number: str = Query(..., description="Policy number."),
    date_of_loss: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date of loss (YYYY-MM-DD).",
    ),
    claim_number: str = Query(..., description="Five Sigma claim number reference."),
    lob: str = Query(..., description="Line of business."),
    org_external_id: str = Query(..., description="Five Sigma organization external ID."),
    suborg_external_id: str = Query(..., description="Sub-organization external ID."),
    service: PolicyService = Depends(get_policy_service),
    _api_key: str = Security(verify_api_key),
) -> PolicyApiRetrieveResponse:
    """GET /policies/retrieve_by_external_id endpoint consumed by Five Sigma."""
    return await service.retrieve_policy_by_external_id(
        external_id=external_id,
        policy_number=policy_number,
        date_of_loss=date_of_loss,
        claim_number=claim_number,
        lob=lob,
        org_external_id=org_external_id,
        suborg_external_id=suborg_external_id,
    )
