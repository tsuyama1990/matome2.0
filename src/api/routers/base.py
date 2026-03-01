import time
from collections import defaultdict
from enum import StrEnum

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: HealthStatus


# Simple in-memory rate limiter logic strictly for fulfilling the health check timing/rate security requirement
_health_check_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check Endpoint",
    description="Returns the current health status of the API.",
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
        429: {
            "description": "Too Many Requests",
        },
    },
)
async def health_check(request: Request) -> HealthResponse:
    """Check the health status of the application with naive rate limiting and timing delay normalization."""
    # Timing Normalization Strategy: Constant Sleep to thwart timing probing
    import asyncio

    await asyncio.sleep(0.05)

    # Naive IP Rate Limiting
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    # Filter expired requests
    _health_check_limits[client_ip] = [
        t for t in _health_check_limits[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS
    ]

    if len(_health_check_limits[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    _health_check_limits[client_ip].append(now)

    return HealthResponse(status=HealthStatus.OK)
