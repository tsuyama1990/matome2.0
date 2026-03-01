from abc import ABC, abstractmethod
from typing import Any


class ILLMProvider(ABC):
    """Abstract interface for LLM interactions."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generates text from the LLM provider."""

    @abstractmethod
    async def extract_structured_data(
        self, prompt: str, schema: dict[str, Any], system_prompt: str = ""
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema."""
