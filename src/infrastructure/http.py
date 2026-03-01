from typing import Any

import httpx

from src.domain.ports.http import IHttpClient


class HttpxAdapter(IHttpClient):
    """Adapter wrapping httpx.AsyncClient for IHttpClient."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def post(
        self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: float  # noqa: ASYNC109
    ) -> Any:
        return await self.client.post(url, headers=headers, json=json, timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()
