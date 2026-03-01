from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dependencies import ApplicationContainer
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions
    container = ApplicationContainer()
    container.config.from_pydantic(settings)
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
def read_root() -> dict[str, str]:
    return {"message": "Hello from matome2-0!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
