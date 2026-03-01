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

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status=HealthStatus.OK)
