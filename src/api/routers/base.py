from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint to verify the API's operational status.
    """
    return {"status": "ok"}
