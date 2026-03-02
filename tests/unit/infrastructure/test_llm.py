import asyncio
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr

from src.core.config import AppSettings
from src.domain.ports.http import IHttpClient
from src.infrastructure.http import HttpxAdapter
from src.infrastructure.llm import OpenRouterClient, OpenRouterConfig


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    return AsyncMock(spec=IHttpClient)


@pytest.fixture
def llm_client(mock_httpx_client: AsyncMock, test_config: AppSettings) -> OpenRouterClient:
    config = OpenRouterConfig(
        api_key=test_config.openrouter_api_key,
        default_model=test_config.text_fast_model,
        base_url=test_config.openrouter_base_url,
        timeout=test_config.llm_timeout,
    )
    return OpenRouterClient(config=config, client=mock_httpx_client)


def test_llm_client_initialization_errors(mock_httpx_client: AsyncMock) -> None:
    config = OpenRouterConfig(
        api_key=SecretStr("key"),
        default_model="m",
        base_url="invalid_url",
        timeout=10.0,
    )
    with pytest.raises(ValueError, match="base_url must be a valid HTTP/HTTPS URL"):
        OpenRouterClient(config=config, client=mock_httpx_client)

    config.base_url = "http://valid.url"
    config.api_key = SecretStr("")
    client = OpenRouterClient(config=config, client=mock_httpx_client)
    with pytest.raises(ValueError, match="api_key must not be empty"):
        client._get_headers()

    config.api_key = SecretStr("key\nwith\nnewline")
    client = OpenRouterClient(config=config, client=mock_httpx_client)
    with pytest.raises(ValueError, match="Invalid characters in API key"):
        client._get_headers()


@pytest.mark.asyncio
async def test_generate_text_success(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Test response"}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )

    mock_httpx_client.post.return_value = mock_response
    result = await llm_client.generate_text("Hello")
    assert result == "Test response"
    mock_httpx_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_generate_text_timeout(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    mock_httpx_client.post.side_effect = TimeoutError("Timeout")
    with pytest.raises(TimeoutError, match="OpenRouter API request timed out"):
        await llm_client.generate_text("Hello")


@pytest.mark.asyncio
async def test_extract_structured_data_success(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": '```json\n{"key": "value"}\n```'}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )

    mock_httpx_client.post.return_value = mock_response
    result = await llm_client.extract_structured_data("Extract this", {"type": "object"})
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_extract_structured_data_invalid_json(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Not JSON at all"}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )

    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(ValueError, match="Failed to parse LLM response into JSON"):
        await llm_client.extract_structured_data("Extract this", {"type": "object"})


@pytest.mark.asyncio
async def test_stream_generate_text_success(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    """Test successful text streaming."""

    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self) -> Any:
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: {"choices": [{"delta": {"content": " World"}}]}'
            yield "data: [DONE]"

        async def __aenter__(self) -> "MockStreamResponse":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    mock_httpx_client.stream_post.return_value = MockStreamResponse()

    chunks = []
    async for chunk in llm_client.stream_generate_text("test prompt"):
        chunks.append(chunk)

    assert chunks == ["Hello", " World"]
    mock_httpx_client.stream_post.assert_called_once()


@pytest.mark.asyncio
async def test_httpx_adapter_methods() -> None:
    """Test HttpxAdapter basic methods to cover IHttpClient mapping."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    adapter = HttpxAdapter(client=mock_client)

    # get
    mock_resp_get = AsyncMock()
    mock_client.get.return_value = mock_resp_get
    assert await adapter.get("url", {}) == mock_resp_get
    mock_client.get.assert_called_once_with("url", headers={})

    # post
    mock_resp_post = AsyncMock()
    mock_client.post.return_value = mock_resp_post
    assert await adapter.post("url", {}, {"json": "data"}) == mock_resp_post
    mock_client.post.assert_called_once_with("url", headers={}, json={"json": "data"})

    # stream_post
    mock_resp_stream = AsyncMock()
    mock_client.stream.return_value = mock_resp_stream
    assert adapter.stream_post("url", {}, {"json": "data"}) == mock_resp_stream
    mock_client.stream.assert_called_once_with("POST", "url", headers={}, json={"json": "data"})

    # exceptions
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    with pytest.raises(TimeoutError):
        await adapter.get("url", {})

    mock_client.get.side_effect = httpx.RequestError("error")
    with pytest.raises(ConnectionError):
        await adapter.get("url", {})

    mock_client.post.side_effect = httpx.TimeoutException("timeout")
    with pytest.raises(TimeoutError):
        await adapter.post("url", {}, {})

    mock_client.post.side_effect = httpx.RequestError("error")
    with pytest.raises(ConnectionError):
        await adapter.post("url", {}, {})

    mock_client.put.side_effect = httpx.TimeoutException("timeout")
    with pytest.raises(TimeoutError):
        await adapter.put("url", {}, {})

    mock_client.put.side_effect = httpx.RequestError("error")
    with pytest.raises(ConnectionError):
        await adapter.put("url", {}, {})

    mock_client.delete.side_effect = httpx.TimeoutException("timeout")
    with pytest.raises(TimeoutError):
        await adapter.delete("url", {})

    mock_client.delete.side_effect = httpx.RequestError("error")
    with pytest.raises(ConnectionError):
        await adapter.delete("url", {})

    # close
    await adapter.close()
    mock_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_generate_text_retry_success(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    # Fail on first call, succeed on second
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Retry success"}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )

    mock_httpx_client.post.side_effect = [TimeoutError("Timeout 1"), mock_response]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        result = await llm_client.generate_text("Hello")

    assert result == "Retry success"
    assert mock_httpx_client.post.call_count == 2


@pytest.mark.asyncio
async def test_stream_generate_text_retry_success(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self) -> Any:
            yield 'data: {"choices": [{"delta": {"content": "Retry stream"}}]}'
            yield "data: [DONE]"

        async def __aenter__(self) -> "MockStreamResponse":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    mock_httpx_client.stream_post.side_effect = [
        ConnectionError("Network Error"),
        MockStreamResponse(),
    ]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        chunks = []
        async for chunk in llm_client.stream_generate_text("test"):
            chunks.append(chunk)

    assert chunks == ["Retry stream"]
    assert mock_httpx_client.stream_post.call_count == 2


@pytest.mark.asyncio
async def test_stream_generate_text_retry_failure(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    mock_httpx_client.stream_post.side_effect = TimeoutError("Timeout")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(TimeoutError, match="OpenRouter API stream request timed out"):
            async for _ in llm_client.stream_generate_text("test"):
                pass
    assert mock_httpx_client.stream_post.call_count == 3
