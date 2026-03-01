from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import Container
from src.api.routers.base import router
from src.core.exceptions import (
    InvalidChunkStateError,
    LLMProviderError,
    MatomeAppError,
    NodeNotFoundError,
)


def create_app() -> FastAPI:
    container = Container()
    container.wire(modules=["src.api.routers.base"])

    app = FastAPI(
        title="matome2-0 API",
        version="v1",
        description="The Core backend service for document ingestion and knowledge graph construction.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.container = container  # type: ignore[attr-defined]

    return app


app = create_app()


from collections.abc import Awaitable, Callable


def create_exception_handler(status_code: int) -> Callable[[Request, Exception], Awaitable[JSONResponse]]:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"message": str(exc)},
        )
    return handler


app.add_exception_handler(MatomeAppError, create_exception_handler(400))
app.add_exception_handler(NodeNotFoundError, create_exception_handler(404))
app.add_exception_handler(InvalidChunkStateError, create_exception_handler(422))
app.add_exception_handler(LLMProviderError, create_exception_handler(502))


app.include_router(router)
