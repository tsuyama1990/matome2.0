from contextlib import AbstractAsyncContextManager
from typing import Any

import httpx

from src.domain.ports.http import IHttpClient, IHttpResponse


class HttpxAdapter(IHttpClient):
    """Adapter wrapping httpx.AsyncClient for IHttpClient."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def get(self, url: str, headers: dict[str, str], timeout: float) -> IHttpResponse:  # noqa: ASYNC109
        try:
            resp = await self.client.get(url, headers=headers, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e
        else:
            return resp  # type: ignore[return-value]

    def stream_post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> AbstractAsyncContextManager[IHttpResponse]:
        return self.client.stream("POST", url, headers=headers, json=json, timeout=timeout)  # type: ignore[return-value]

    async def post(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> IHttpResponse:
        try:
            resp = await self.client.post(url, headers=headers, json=json, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e
        else:
            return resp  # type: ignore[return-value]

    async def put(
        self,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,  # noqa: ASYNC109
    ) -> IHttpResponse:
        try:
            resp = await self.client.put(url, headers=headers, json=json, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e
        else:
            return resp  # type: ignore[return-value]

    async def delete(self, url: str, headers: dict[str, str], timeout: float) -> IHttpResponse:  # noqa: ASYNC109
        try:
            resp = await self.client.delete(url, headers=headers, timeout=timeout)
        except httpx.TimeoutException as e:
            msg = f"Request timed out: {e}"
            raise TimeoutError(msg) from e
        except httpx.RequestError as e:
            msg = f"HTTP connection error: {e}"
            raise ConnectionError(msg) from e
        else:
            return resp  # type: ignore[return-value]

    async def close(self) -> None:
        await self.client.aclose()
