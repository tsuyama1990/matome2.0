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
    timeout: float = 30.0


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
            return data["choices"][0]["message"]["content"]  # type: ignore[no-any-return]
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
        # Simple non-streaming fallback for now if strict streams are unsupported or require special headers
        text = await self.generate_text(prompt, system_prompt)
        yield text

    async def extract_structured_data(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema using httpx."""
        extended_prompt = (
            f"{prompt}\n\nYou must return strictly valid JSON matching the following schema:\n"
            f"{json.dumps(schema)}"
        )

        raw_text = await self.generate_text(prompt=extended_prompt, system_prompt=system_prompt)

        try:
            # Simple heuristic to extract JSON block if wrapped in markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            return json.loads(raw_text)  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            msg = f"Failed to parse LLM response into JSON: {raw_text}"
            raise ValueError(msg) from e
