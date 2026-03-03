import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, HttpUrl, SecretStr

from src.core.constants import API_KEY_REGEX_PATTERN
from src.core.utils import _with_retries
from src.domain.exceptions import ConfigurationError
from src.domain.ports.http import IHttpClient
from src.domain.ports.llm import ILLMProvider


@dataclass
class OpenRouterConfig:
    """Configuration wrapper for OpenRouterClient."""

    api_key: SecretStr
    default_model: str
    base_url: HttpUrl | str
    timeout: float
    max_retries: int
    base_delay: float


class OpenRouterClient(ILLMProvider):
    """Concrete implementation for OpenRouter LLM Client."""

    _config: OpenRouterConfig
    _client: IHttpClient

    def __init__(
        self,
        config: OpenRouterConfig,
        client: IHttpClient,
    ) -> None:
        if not str(config.base_url).startswith(("http://", "https://")):
            msg = "base_url must be a valid HTTP/HTTPS URL"
            raise ConfigurationError(msg)
        self._config = config
        self._client = client

    def _get_headers(self) -> dict[str, str]:
        """Constructs secure headers for API communication."""
        import re

        token = self._config.api_key.get_secret_value()
        if not token:
            msg = "api_key must not be empty"
            raise ConfigurationError(msg)

        if "\n" in token or "\r" in token:
            msg = "Invalid characters in API key"
            raise ConfigurationError(msg)

        # Secure string format validation
        if not re.match(API_KEY_REGEX_PATTERN, token) or len(token) < 20:
            msg = "API key fails pattern validation"
            raise ConfigurationError(msg)

        auth_value = f"Bearer {token}"
        return {
            "Authorization": auth_value,
            "Content-Type": "application/json",
        }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float | None = None,
    ) -> str:
        """Generates text from the LLM provider using httpx."""

        async def _func() -> str:
            return await self._generate_text(prompt, system_prompt, timeout)

        return await _with_retries(_func, self._config.max_retries, self._config.base_delay)

    async def _generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float | None = None,
    ) -> str:
        if not prompt.strip():
            msg = "Prompt cannot be empty"
            raise ConfigurationError(msg)

        headers = self._get_headers()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._config.default_model,
            "messages": messages,
        }

        try:
            response = await self._client.post(
                str(self._config.base_url), headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Safely navigate JSON response
            if not isinstance(data, dict):
                msg = "Invalid response format"
                raise TypeError(msg)

            choices = data.get("choices", [])
            if not choices or not isinstance(choices, list):
                msg = "Missing or invalid 'choices' in response"
                raise ConfigurationError(msg)

            choice = choices[0]
            if not isinstance(choice, dict):
                msg = "Missing or invalid 'message' in response"
                raise TypeError(msg)

            message = choice.get("message", {})
            if not isinstance(message, dict):
                msg = "Missing or invalid 'message' in response"
                raise TypeError(msg)

            content = message.get("content")
            if content is None:
                msg = "Missing 'content' in response"
                raise ConfigurationError(msg)

            return str(content)
        except TimeoutError as e:
            msg = f"OpenRouter API request timed out: {e}"
            raise TimeoutError(msg) from e
        except ConnectionError as e:
            msg = f"Error communicating with OpenRouter: {e}"
            raise ConnectionError(msg) from e

    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream implementation."""
        headers = self._get_headers()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._config.default_model,
            "messages": messages,
            "stream": True,
        }

        async def _connect() -> Any:
            try:
                cm = self._client.stream_post(
                    str(self._config.base_url), headers=headers, json=payload
                )
                resp = await cm.__aenter__()
                resp.raise_for_status()
            except Exception as e:
                if "cm" in locals():
                    await cm.__aexit__(type(e), e, e.__traceback__)
                if isinstance(e, TimeoutError):
                    msg = f"OpenRouter API stream request timed out: {e}"
                    raise TimeoutError(msg) from e
                if isinstance(e, ConnectionError):
                    msg = f"Error communicating with OpenRouter stream: {e}"
                    raise ConnectionError(msg) from e
                raise
            else:
                return cm, resp

        response_cm, response = await _with_retries(
            _connect, self._config.max_retries, self._config.base_delay
        )

        # Now stream from the established connection
        try:
            async with asyncio.timeout(self._config.timeout):
                async for line in response.aiter_lines():
                    chunk = self._parse_stream_line(line)
                    if chunk == "[DONE]":
                        break
                    if chunk:
                        yield chunk
        except TimeoutError as e:
            msg = f"OpenRouter API stream request timed out mid-stream: {e}"
            raise TimeoutError(msg) from e
        except ConnectionError as e:
            msg = f"Error communicating with OpenRouter stream mid-stream: {e}"
            raise ConnectionError(msg) from e
        finally:
            if response_cm:
                await response_cm.__aexit__(None, None, None)

    def _parse_stream_line(self, line: str) -> str | None:
        if not line or not line.startswith("data: "):
            return None
        data_str = line[len("data: ") :].strip()
        if data_str == "[DONE]":
            return "[DONE]"
        try:
            data = json.loads(data_str)
            if not isinstance(data, dict):
                return None

            choices = data.get("choices", [])
            if not isinstance(choices, list) or not choices:
                return None

            choice = choices[0]
            if not isinstance(choice, dict):
                return None

            delta = choice.get("delta", {})
            if not isinstance(delta, dict):
                return None

            content = delta.get("content")
            return str(content) if content is not None else None
        except json.JSONDecodeError:
            pass
        return None

    async def extract_structured_data(
        self,
        prompt: str,
        schema: type[BaseModel] | dict[str, Any],
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema using httpx."""
        if isinstance(schema, dict) and not schema:
            msg = "schema dictionary cannot be empty"
            raise ConfigurationError(msg)

        schema_dict = schema if isinstance(schema, dict) else schema.model_json_schema()
        extended_prompt = (
            f"{prompt}\n\nYou must return strictly valid JSON matching the following schema:\n"
            f"{json.dumps(schema_dict)}"
        )

        raw_text = await self.generate_text(prompt=extended_prompt, system_prompt=system_prompt)

        try:
            # Simple heuristic to extract JSON block if wrapped in markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            result = json.loads(raw_text)
        except json.JSONDecodeError as e:
            msg = f"Failed to parse LLM response into JSON: {raw_text}"
            raise ConfigurationError(msg) from e
        else:
            if not isinstance(result, dict):
                msg = "Parsed JSON is not a dictionary"
                raise TypeError(msg)

            # Strict schema validation
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                return schema.model_validate(result).model_dump()
            return result
