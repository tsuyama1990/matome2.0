from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel


class ILLMProvider(ABC):
    """Abstract interface for LLM interactions.

    Implementations must enforce structured error handling and provide
    adaptive retry logic (e.g. exponential backoff and jitter) to deal
    with common remote API service degradation or throttling (429s).
    """

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float | None = None,
    ) -> str:
        """Generates text from the LLM provider.

        Args:
            prompt (str): The main user prompt to pass to the model.
            system_prompt (str): System prompt to configure the model's behavior.
            timeout (float | None): Maximum time to wait for a response before timing out.

        Raises:
            TimeoutError: If the underlying API call exceeds the timeout period. Implementations
                          should ideally wrap library-specific timeouts to this built-in error.
                          They MUST configure a resilient retry logic (e.g., maximum 3 retries
                          with exponential backoff) to handle transient API downtime, 5xx errors,
                          or 429 throttling before ultimately failing and bubbling up the error.
            ConnectionError: If a connection error happens during interaction with the API.
        """
        ...

    @abstractmethod
    def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        """Generates text from the LLM provider as an asynchronous stream.

        Args:
            prompt (str): The main user prompt.
            system_prompt (str): System prompt context.
            timeout (float | None): The request timeout limit.

        Yields:
            str: Chunks of the generated response.
        """
        ...

    @abstractmethod
    async def extract_structured_data(
        self,
        prompt: str,
        schema: type[BaseModel] | dict[str, Any],
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """Extracts JSON matching a specific schema.

        Args:
            prompt (str): The input to base the extraction on.
            schema (type | dict): The target JSON schema representing the data shape (or a Pydantic model class).
            system_prompt (str): Additional context or formatting instructions.

        Raises:
            TimeoutError: If the call to the LLM times out. Implementations must wrap internal timeouts.
            ValueError: If the generated output cannot be parsed into the target schema.
        """
        ...
