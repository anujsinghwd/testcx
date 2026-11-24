from fastapi import FastAPI

from app.api.router import api_router
from app.api.v1.policy import router as policy_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logger import setup_logging
from app.core.middleware import CorrelationIdMiddleware

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

# Register middlewares
app.add_middleware(CorrelationIdMiddleware)

# Register centralized error handlers
register_error_handlers(app)

# Include API router (mounted at both /api/v1/policies and /policies)
app.include_router(api_router, prefix="/api/v1")
app.include_router(policy_router, prefix="/policies", tags=["Policies"])
