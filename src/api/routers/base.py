from enum import StrEnum

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

router = APIRouter()

class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"

class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: HealthStatus

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check Endpoint",
    description="Returns the current health status of the API.",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            },
        }
    }
)
async def health_check() -> HealthResponse:
    """Check the health status of the application."""
    return HealthResponse(status=HealthStatus.OK)
