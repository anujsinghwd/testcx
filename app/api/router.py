from fastapi import APIRouter

from app.api.v1 import policy

api_router = APIRouter()
api_router.include_router(policy.router, prefix="/policies", tags=["Policies"])
