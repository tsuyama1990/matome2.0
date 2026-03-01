
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.routers.base import router as base_router
from src.core.exceptions import MatomeAppError


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="matome2-0",
        version="0.1.0",
        description="Knowledge Workspace API",
    )

    @app.exception_handler(MatomeAppError)
    async def matome_app_exception_handler(
        request: Request, exc: MatomeAppError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": exc.message, "type": exc.__class__.__name__},
        )

    app.include_router(base_router)

    return app


app = create_app()
