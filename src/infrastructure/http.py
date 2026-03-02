from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

import httpx

from src.domain.ports.http import IHttpClient, IHttpResponse


class HttpxAdapter(IHttpClient):
    """Adapter wrapping httpx.AsyncClient for IHttpClient."""

    client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def _handle_request(
        self, request_func: Callable[[], Awaitable[httpx.Response]]
    ) -> IHttpResponse:
        try:
            resp = await request_func()
            resp.raise_for_status()
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.HTTPStatusError as e:
            # Map 5xx and 429 to ConnectionError so retry decorator catches them
            if e.response.status_code >= 500 or e.response.status_code == 429:
                msg = f"HTTP {e.response.status_code} error: {e}"
                raise ConnectionError(msg) from e
            raise
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e
        else:
            return resp

    async def get(self, url: str, headers: dict[str, str], timeout: float = 30.0) -> IHttpResponse:
        return await self._handle_request(lambda: self.client.get(url, headers=headers, timeout=timeout))

    def stream_post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> AbstractAsyncContextManager[IHttpResponse]:
        return self.client.stream("POST", url, headers=headers, json=json)

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> IHttpResponse:
        return await self._handle_request(lambda: self.client.post(url, headers=headers, json=json))

    async def put(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> IHttpResponse:
        return await self._handle_request(lambda: self.client.put(url, headers=headers, json=json))

    async def delete(self, url: str, headers: dict[str, str]) -> IHttpResponse:
        return await self._handle_request(lambda: self.client.delete(url, headers=headers))

    async def close(self) -> None:
        await self.client.aclose()
