from unittest.mock import AsyncMock

import httpx
import pytest

from src.core.config import AppSettings
from src.infrastructure.llm import OpenRouterClient


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def llm_client(mock_httpx_client: AsyncMock, test_config: AppSettings) -> OpenRouterClient:
    return OpenRouterClient(
        api_key="dummy_key",
        default_model="dummy-model",
        client=mock_httpx_client,
        base_url=test_config.openrouter_base_url,
    )


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
    mock_httpx_client.post.side_effect = httpx.TimeoutException("Timeout")
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
