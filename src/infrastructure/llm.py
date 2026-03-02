import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, SecretStr

from src.core.utils import _with_retries
from src.domain.ports.http import IHttpClient
from src.domain.ports.llm import ILLMProvider


@dataclass
class OpenRouterConfig:
    """Configuration wrapper for OpenRouterClient."""

    api_key: SecretStr
    default_model: str
    base_url: str
    timeout: float


class OpenRouterClient(ILLMProvider):
    """Concrete implementation for OpenRouter LLM Client."""

    config: OpenRouterConfig
    client: IHttpClient

    def __init__(
        self,
        config: OpenRouterConfig,
        client: IHttpClient,
    ) -> None:
        if not config.base_url.startswith(("http://", "https://")):
            msg = "base_url must be a valid HTTP/HTTPS URL"
            raise ValueError(msg)
        self.config = config
        self.client = client

    def _get_headers(self) -> dict[str, str]:
        """Constructs secure headers for API communication."""
        token = self.config.api_key.get_secret_value()
        if not token:
            msg = "api_key must not be empty"
            raise ValueError(msg)

        if "\n" in token or "\r" in token:
            msg = "Invalid characters in API key"
            raise ValueError(msg)

        auth_value = f"Bearer {token}"
        return {
            "Authorization": auth_value,
            "Content-Type": "application/json",
        }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> str:
        """Generates text from the LLM provider using httpx."""
        headers = self._get_headers()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.default_model,
            "messages": messages,
        }

        async def _call() -> str:
            try:
                response = await self.client.post(
                    self.config.base_url, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                return str(data["choices"][0]["message"]["content"])
            except TimeoutError as e:
                msg = f"OpenRouter API request timed out: {e}"
                raise TimeoutError(msg) from e
            except ConnectionError as e:
                msg = f"Error communicating with OpenRouter: {e}"
                raise ConnectionError(msg) from e

        return await _with_retries(_call)

    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        """Stream implementation."""
        headers = self._get_headers()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.default_model,
            "messages": messages,
            "stream": True,
        }

        async def _connect() -> Any:
            try:
                cm = self.client.stream_post(self.config.base_url, headers=headers, json=payload)
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

        response_cm, response = await _with_retries(_connect)

        # Now stream from the established connection
        try:
            async for line in response.aiter_lines():
                chunk = self._parse_stream_line(line)
                if chunk == "[DONE]":
                    break
                if chunk:
                    yield chunk
        except (TimeoutError, ConnectionError) as e:
            # We raise a new error here to signal the stream broke mid-way, but we don't retry.
            if isinstance(e, TimeoutError):
                msg = f"OpenRouter API stream request timed out mid-stream: {e}"
                raise TimeoutError(msg) from e
            msg = f"Error communicating with OpenRouter stream mid-stream: {e}"
            raise ConnectionError(msg) from e
        finally:
            await response_cm.__aexit__(None, None, None)

    def _parse_stream_line(self, line: str) -> str | None:
        if not line or not line.startswith("data: "):
            return None
        data_str = line[len("data: ") :].strip()
        if data_str == "[DONE]":
            return "[DONE]"
        try:
            data = json.loads(data_str)
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("delta", {}).get("content")
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
            raise ValueError(msg)

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
            raise ValueError(msg) from e
        else:
            if not isinstance(result, dict):
                msg = "Parsed JSON is not a dictionary"
                raise TypeError(msg)
            return result
