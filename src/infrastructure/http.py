from typing import Any

import httpx

from src.domain.ports.http import IHttpClient


class HttpxAdapter(IHttpClient):
    """Adapter wrapping httpx.AsyncClient for IHttpClient."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        try:
            return await self.client.get(url, headers=headers, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> Any:
        try:
            return await self.client.post(url, headers=headers, json=json, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e

    async def put(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> Any:
        try:
            return await self.client.put(url, headers=headers, json=json, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e

    async def delete(self, url: str, headers: dict[str, str], timeout: float) -> Any:  # noqa: ASYNC109
        try:
            return await self.client.delete(url, headers=headers, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e

    async def close(self) -> None:
        await self.client.aclose()
