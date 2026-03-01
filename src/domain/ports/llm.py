from abc import ABC, abstractmethod
from typing import Any


class ILLMProvider(ABC):
    """Abstract interface for LLM interactions."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 30.0,  # noqa: ASYNC109
    ) -> str:
        """Generates text from the LLM provider.

        Args:
            prompt (str): The main user prompt to pass to the model.
            system_prompt (str): System prompt to configure the model's behavior.
            timeout (float): The maximum time to wait for the LLM API to respond.

        Raises:
            TimeoutError: If the underlying API call exceeds the timeout period. Implementations
                          should ideally wrap library-specific timeouts to this built-in error.
            ConnectionError: If a connection error happens during interaction with the API.
        """

    @abstractmethod
    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 30.0,  # noqa: ASYNC109
    ) -> Any:
        """Generates text from the LLM provider as an asynchronous stream.

        Args:
            prompt (str): The main user prompt.
            system_prompt (str): System prompt context.
            timeout (float): Timeout per chunk.

        Yields:
            str: Chunks of the generated response.
        """

    @abstractmethod
    async def extract_structured_data(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str = "",
        timeout: float = 30.0,  # noqa: ASYNC109
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema.

        Args:
            prompt (str): The input to base the extraction on.
            schema (dict): The target JSON schema representing the data shape.
            system_prompt (str): Additional context or formatting instructions.
            timeout (float): The timeout per request for extraction.

        Raises:
            TimeoutError: If the call to the LLM times out. Implementations must wrap internal timeouts.
            ValueError: If the generated output cannot be parsed into the target schema.
        """
