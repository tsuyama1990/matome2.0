from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src.api.dependencies import ContainerFactory
from src.core.config import AppSettings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions
    # Using AppSettings instantiates the configuration and performs post init validation automatically
    settings = AppSettings()

    container = ContainerFactory.create_container(settings)
    app.container = container  # type: ignore
    yield
    # Shutdown actions


app = FastAPI(
    title="matome2-0",
    description="Knowledge Workspace Platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def read_root() -> dict[str, Any]:
    # In a full deployment, features would be dynamically fetched from
    # a feature flag or available router modules.
    return {
        "status": "online",
        "message": "Welcome to matome2-0 Knowledge Workspace Platform API.",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
