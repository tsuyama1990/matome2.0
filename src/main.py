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
        openapi_url="/openapi.json"
    )
    app.container = container # type: ignore[attr-defined]

    return app

app = create_app()

@app.exception_handler(MatomeAppError)
async def matome_app_error_handler(request: Request, exc: MatomeAppError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )

@app.exception_handler(NodeNotFoundError)
async def node_not_found_error_handler(request: Request, exc: NodeNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"message": str(exc)},
    )

@app.exception_handler(InvalidChunkStateError)
async def invalid_chunk_state_error_handler(request: Request, exc: InvalidChunkStateError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"message": str(exc)},
    )

@app.exception_handler(LLMProviderError)
async def llm_provider_error_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"message": str(exc)},
    )

app.include_router(router)
