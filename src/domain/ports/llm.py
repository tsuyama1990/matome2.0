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
        timeout: float = 30.0,
    ) -> str:
        """Generates text from the LLM provider.

        Args:
            prompt (str): The main user prompt to pass to the model.
            system_prompt (str): System prompt to configure the model's behavior.

        Raises:
            TimeoutError: If the underlying API call exceeds the timeout period. Implementations
                          should ideally wrap library-specific timeouts to this built-in error.
                          They should also configure a resilient retry logic (e.g. exponential backoff)
                          to handle transient API downtime before failing.
            ConnectionError: If a connection error happens during interaction with the API.
        """
        ...

    @abstractmethod
    def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 30.0,
        chunk_size: int | None = None,
    ) -> AsyncIterator[str]:
        """Generates text from the LLM provider as an asynchronous stream.

        Args:
            prompt (str): The main user prompt.
            system_prompt (str): System prompt context.
            timeout (float): The request timeout limit.
            chunk_size (int | None): Configurable chunk sizes for backpressure handling.

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
