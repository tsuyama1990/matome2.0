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
        api_key=SecretStr("sk-or-v1-key12345678901234567890"),
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

    config.api_key = SecretStr("sk-or-v1-key\nwith\nnewline")
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


@pytest.mark.asyncio
async def test_stream_generate_text_generic_exception(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_httpx_client.stream_post.side_effect = ValueError("generic stream error")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ValueError, match="generic stream error"):
            async for _ in llm_client.stream_generate_text("test"):
                pass


def test_parse_stream_line(llm_client: OpenRouterClient) -> None:
    # invalid prefix
    assert llm_client._parse_stream_line("invalid") is None
    # done signal
    assert llm_client._parse_stream_line("data: [DONE]") == "[DONE]"
    # empty data
    assert llm_client._parse_stream_line("data: ") is None
    # invalid JSON
    assert llm_client._parse_stream_line("data: {invalid}") is None
    # not a dict JSON
    assert llm_client._parse_stream_line("data: []") is None
    # no choices list
    assert llm_client._parse_stream_line('data: {"choices": null}') is None
    # choices not a dict
    assert llm_client._parse_stream_line('data: {"choices": ["invalid"]}') is None
    # delta missing
    assert llm_client._parse_stream_line('data: {"choices": [{}]}') is None
    # delta not dict
    assert llm_client._parse_stream_line('data: {"choices": [{"delta": null}]}') is None
    # valid payload without content
    assert llm_client._parse_stream_line('data: {"choices": [{"delta": {}}]}') is None
    # valid payload with content
    assert (
        llm_client._parse_stream_line('data: {"choices": [{"delta": {"content": "data"}}]}')
        == "data"
    )


@pytest.mark.asyncio
async def test_generate_text_invalid_format(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json=[],  # Invalid root
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(TypeError, match="Invalid response format"):
        await llm_client.generate_text("Hello")

    mock_response = httpx.Response(
        200,
        json={"choices": {}},  # Invalid choices
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(ValueError, match="Missing or invalid 'choices' in response"):
        await llm_client.generate_text("Hello")

    mock_response = httpx.Response(
        200,
        json={"choices": [[]]},  # Invalid message type
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(TypeError, match="Missing or invalid 'message' in response"):
        await llm_client.generate_text("Hello")

    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {}}]},  # Missing content
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(ValueError, match="Missing 'content' in response"):
        await llm_client.generate_text("Hello")


@pytest.mark.asyncio
async def test_extract_structured_data_empty_schema(llm_client: OpenRouterClient) -> None:
    with pytest.raises(ValueError, match="schema dictionary cannot be empty"):
        await llm_client.extract_structured_data("Extract", {})


@pytest.mark.asyncio
async def test_extract_structured_data_not_dict(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": '["Not a dict"]'}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )

    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(TypeError, match="Parsed JSON is not a dictionary"):
        await llm_client.extract_structured_data("Extract", {"type": "object"})


@pytest.mark.asyncio
async def test_generate_text_empty_prompt(llm_client: OpenRouterClient) -> None:
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        await llm_client.generate_text("")


@pytest.mark.asyncio
async def test_generate_text_connection_error(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    mock_httpx_client.post.side_effect = ConnectionError("Connection refused")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match="Error communicating with OpenRouter"):
            await llm_client.generate_text("Hello")


@pytest.mark.asyncio
async def test_stream_generate_text_mid_stream_connection_error(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self) -> Any:
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            raise ConnectionError("Mid stream error")

        async def __aenter__(self) -> "MockStreamResponse":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    mock_httpx_client.stream_post.return_value = MockStreamResponse()

    with pytest.raises(
        ConnectionError, match="Error communicating with OpenRouter stream mid-stream"
    ):
        async for _ in llm_client.stream_generate_text("test prompt"):
            pass


@pytest.mark.asyncio
async def test_stream_generate_text_mid_stream_timeout_error(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self) -> Any:
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            raise TimeoutError("Mid stream error")

        async def __aenter__(self) -> "MockStreamResponse":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    mock_httpx_client.stream_post.return_value = MockStreamResponse()

    with pytest.raises(TimeoutError, match="OpenRouter API stream request timed out mid-stream"):
        async for _ in llm_client.stream_generate_text("test prompt"):
            pass


def test_api_key_fails_pattern(mock_httpx_client: AsyncMock) -> None:
    config = OpenRouterConfig(
        api_key=SecretStr("sk-or-v1-tooshort"),
        default_model="m",
        base_url="http://valid.url",
        timeout=10.0,
    )
    client = OpenRouterClient(config=config, client=mock_httpx_client)
    with pytest.raises(ValueError, match="API key fails pattern validation"):
        client._get_headers()


@pytest.mark.asyncio
async def test_generate_text_with_system_prompt(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": "Test response"}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    result = await llm_client.generate_text("Hello", system_prompt="System Prompt")
    assert result == "Test response"


@pytest.mark.asyncio
async def test_generate_text_choice_not_dict(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": ["not a dict"]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(TypeError, match="Missing or invalid 'message' in response"):
        await llm_client.generate_text("Hello")


@pytest.mark.asyncio
async def test_generate_text_message_not_dict(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": "not a dict"}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    with pytest.raises(TypeError, match="Missing or invalid 'message' in response"):
        await llm_client.generate_text("Hello")


@pytest.mark.asyncio
async def test_stream_generate_text_system_prompt(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    class MockStreamResponse:
        def raise_for_status(self) -> None:
            pass

        async def aiter_lines(self) -> Any:
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'

        async def __aenter__(self) -> "MockStreamResponse":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    mock_httpx_client.stream_post.return_value = MockStreamResponse()
    async for _ in llm_client.stream_generate_text("test", system_prompt="System"):
        pass
    mock_httpx_client.stream_post.assert_called_once()


@pytest.mark.asyncio
async def test_stream_connect_cm_cleanup(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock
) -> None:
    class BrokenCM:
        async def __aenter__(self) -> "BrokenCM":
            return self

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        def raise_for_status(self) -> None:
            raise ConnectionError("broken connection")

    mock_httpx_client.stream_post.return_value = BrokenCM()

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match="Error communicating with OpenRouter stream"):
            async for _ in llm_client.stream_generate_text("test"):
                pass


from pydantic import BaseModel


class DummyModel(BaseModel):
    key: str


@pytest.mark.asyncio
async def test_extract_structured_data_pydantic_schema(
    llm_client: OpenRouterClient, mock_httpx_client: AsyncMock, test_config: AppSettings
) -> None:
    mock_response = httpx.Response(
        200,
        json={"choices": [{"message": {"content": '{"key": "value"}'}}]},
        request=httpx.Request("POST", test_config.openrouter_base_url),
    )
    mock_httpx_client.post.return_value = mock_response
    result = await llm_client.extract_structured_data("Extract", DummyModel)
    assert result == {"key": "value"}
