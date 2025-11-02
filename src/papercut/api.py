"""
Papercut FastAPI application.
Main app that includes platform-specific routers.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from papercut.logging_config import setup_logging
from config import config

setup_logging()

app = FastAPI(
    title="Papercut",
    description="Print your tickets on a real receipt printer",
    version="0.1.0",
)


class HealthCheckResponse(BaseModel):
    """Response from the health check endpoint"""

    status: str = Field(..., description="Server status")
    message: str = Field(..., description="Status message")


# Dynamically include platform routers (only if enabled)
if config.providers.linear and not config.providers.linear.disabled:
    from papercut.platforms.linear.router import router as linear_router

    app.include_router(linear_router, prefix="/webhooks")


@app.get("/", response_model=HealthCheckResponse, summary="Health Check")
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse(status="ok", message="Papercut is running")
