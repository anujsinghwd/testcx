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

# Include API router: canonical contract endpoints at /policies; /api/v1 kept for backward compatibility (hidden from Swagger)
app.include_router(api_router, prefix="/api/v1", include_in_schema=False)
app.include_router(policy_router, prefix="/policies", tags=["Policies"])
