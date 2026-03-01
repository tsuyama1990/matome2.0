from typing import Any

import httpx

from src.domain.ports.http import IHttpClient


class HttpxAdapter(IHttpClient):
    """Adapter wrapping httpx.AsyncClient for IHttpClient."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        return await self.client.get(url, headers=headers, timeout=timeout)

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> Any:
        return await self.client.post(url, headers=headers, json=json, timeout=timeout)

    async def put(
        self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: float  # noqa: ASYNC109
    ) -> Any:
        return await self.client.put(url, headers=headers, json=json, timeout=timeout)

    async def delete(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        return await self.client.delete(url, headers=headers, timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()
