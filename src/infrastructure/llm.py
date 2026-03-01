from typing import Any

from src.domain.ports.llm import ILLMProvider


class OpenRouterClient(ILLMProvider):
    """Concrete implementation for OpenRouter LLM Client."""

    def __init__(self, api_key: str, default_model: str) -> None:
        self.api_key = api_key
        self.default_model = default_model

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 30.0,  # noqa: ASYNC109
    ) -> str:
        """Generates text from the LLM provider."""
        # Simulated response for now
        return f"Simulated text response for prompt: {prompt}"

    async def extract_structured_data(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str = "",
        timeout: float = 30.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema."""
        # Simulated response for now
        return {"result": f"Simulated structured data for prompt: {prompt}"}
