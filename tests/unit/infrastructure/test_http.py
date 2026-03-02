from unittest.mock import AsyncMock

import httpx
import pytest

from src.infrastructure.http import HttpxAdapter


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def adapter(mock_httpx_client: AsyncMock) -> HttpxAdapter:
    return HttpxAdapter(client=mock_httpx_client)


@pytest.mark.asyncio
async def test_get_success(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.get.return_value = mock_response

    resp = await adapter.get("url", headers={})
    assert resp == mock_response
    mock_httpx_client.get.assert_called_once_with("url", headers={}, timeout=30.0)


@pytest.mark.asyncio
async def test_post_success(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.post.return_value = mock_response

    resp = await adapter.post("url", headers={}, json={"key": "val"})
    assert resp == mock_response
    mock_httpx_client.post.assert_called_once_with("url", headers={}, json={"key": "val"})


@pytest.mark.asyncio
async def test_put_success(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.put.return_value = mock_response

    resp = await adapter.put("url", headers={}, json={"key": "val"})
    assert resp == mock_response
    mock_httpx_client.put.assert_called_once_with("url", headers={}, json={"key": "val"})


@pytest.mark.asyncio
async def test_delete_success(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.delete.return_value = mock_response

    resp = await adapter.delete("url", headers={})
    assert resp == mock_response
    mock_httpx_client.delete.assert_called_once_with("url", headers={})


@pytest.mark.asyncio
async def test_timeout_exception(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_httpx_client.get.side_effect = httpx.TimeoutException("timeout")
    with pytest.raises(TimeoutError, match="Request timed out"):
        await adapter.get("url", headers={})


@pytest.mark.asyncio
async def test_request_exception(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_httpx_client.get.side_effect = httpx.RequestError("error")
    with pytest.raises(ConnectionError, match="HTTP connection error"):
        await adapter.get("url", headers={})


@pytest.mark.asyncio
async def test_http_status_error_500(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    request = httpx.Request("GET", "url")
    response = httpx.Response(500, request=request)
    # The real httpx client does not raise HTTPStatusError automatically on get(),
    # it only returns a response. The raise_for_status() does it.
    # We mock get() to raise it to simulate raise_for_status
    mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
        "error", request=request, response=response
    )

    with pytest.raises(ConnectionError, match="HTTP 500 error"):
        await adapter.get("url", headers={})


@pytest.mark.asyncio
async def test_http_status_error_429(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    request = httpx.Request("GET", "url")
    response = httpx.Response(429, request=request)
    mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
        "error", request=request, response=response
    )

    with pytest.raises(ConnectionError, match="HTTP 429 error"):
        await adapter.get("url", headers={})


@pytest.mark.asyncio
async def test_http_status_error_400(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    request = httpx.Request("GET", "url")
    response = httpx.Response(400, request=request)
    mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
        "error", request=request, response=response
    )

    with pytest.raises(httpx.HTTPStatusError):
        await adapter.get("url", headers={})


@pytest.mark.asyncio
async def test_stream_post(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    mock_response = AsyncMock()
    mock_httpx_client.stream.return_value = mock_response

    resp = adapter.stream_post("url", headers={}, json={})
    assert resp == mock_response
    mock_httpx_client.stream.assert_called_once_with("POST", "url", headers={}, json={})


@pytest.mark.asyncio
async def test_close(adapter: HttpxAdapter, mock_httpx_client: AsyncMock) -> None:
    await adapter.close()
    mock_httpx_client.aclose.assert_called_once()
