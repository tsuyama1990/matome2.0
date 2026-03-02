import json
from dataclasses import dataclass
from typing import Any

from src.domain.ports.http import IHttpClient
from src.domain.ports.llm import ILLMProvider


@dataclass
class OpenRouterConfig:
    """Configuration wrapper for OpenRouterClient."""

    api_key: str
    default_model: str
    base_url: str
    timeout: float


class OpenRouterClient(ILLMProvider):
    """Concrete implementation for OpenRouter LLM Client."""

    def __init__(
        self,
        config: OpenRouterConfig,
        client: IHttpClient,
    ) -> None:
        self.config = config
        self.client = client

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> str:
        """Generates text from the LLM provider using httpx."""
        if not self.config.api_key or len(self.config.api_key) < 10:
            msg = "Invalid OpenRouter API Key configuration."
            raise ValueError(msg)

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.default_model,
            "messages": messages,
        }

        try:
            response = await self.client.post(
                self.config.base_url, headers=headers, json=payload, timeout=self.config.timeout
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
        except Exception as e:
            # Fallback for unexpected HTTP client adapter errors (e.g. from raise_for_status())
            msg = f"Unexpected error during OpenRouter API call: {e}"
            raise ConnectionError(msg) from e

    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> Any:
        """Stream implementation."""
        if not self.config.api_key or len(self.config.api_key) < 10:
            msg = "Invalid OpenRouter API Key configuration."
            raise ValueError(msg)

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.default_model,
            "messages": messages,
            "stream": True,
        }

        try:
            async with self.client.stream_post(
                self.config.base_url, headers=headers, json=payload, timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    chunk = self._parse_stream_line(line)
                    if chunk == "[DONE]":
                        break
                    if chunk:
                        yield chunk
        except TimeoutError as e:
            msg = f"OpenRouter API stream request timed out: {e}"
            raise TimeoutError(msg) from e
        except ConnectionError as e:
            msg = f"Error communicating with OpenRouter stream: {e}"
            raise ConnectionError(msg) from e
        except Exception as e:
            msg = f"Unexpected error during OpenRouter API stream call: {e}"
            raise ConnectionError(msg) from e

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
        schema: type[Any] | dict[str, Any],
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema using httpx."""
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
