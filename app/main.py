from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def root_health_check() -> dict[str, str]:
    return {"status": "healthy"}
