"""Policy API route definitions implementing Five Sigma v2 Policy Search."""

from fastapi import APIRouter, Depends, Query, Request, Security

from app.core.auth import verify_api_key
from app.dependencies.clients import get_policy_service
from app.schemas.policy import PolicyApiSearchResponse
from app.services.policy_service import PolicyService

router = APIRouter()


@router.get(
    "/search",
    response_model=PolicyApiSearchResponse,
    summary="Search policies (Five Sigma v2)",
    description=(
        "Search policies matching Line of Business and Organization criteria. "
        "Returns display schema and policy items with opaque retrieval tokens."
    ),
)
async def search_policies(
    request: Request,
    lob: str = Query(..., description="Line of business (required, exactly one)"),
    org_external_id: str = Query(..., description="Organization external ID (required)"),
    suborg_external_id: str | None = Query(
        None, description="Sub-organization external ID (optional)"
    ),
    service: PolicyService = Depends(get_policy_service),
    _api_key: str = Security(verify_api_key),
) -> PolicyApiSearchResponse:
    """GET /policies/search endpoint consumed by Five Sigma during FNOL."""
    standard_params = {"lob", "org_external_id", "suborg_external_id"}
    search_fields = {k: v for k, v in request.query_params.items() if k not in standard_params}

    return await service.search_policies(
        lob=lob,
        org_external_id=org_external_id,
        suborg_external_id=suborg_external_id,
        search_fields=search_fields if search_fields else None,
    )
