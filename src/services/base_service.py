import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.core.exceptions import MatomeAppError
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore

T = TypeVar("T")

class BaseService(ABC):
    def __init__(self, llm_provider: ILLMProvider, vector_store: IVectorStore) -> None:
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        max_retries: int = 3,
    ) -> T:
        """Centralized retry mechanism for external API calls."""
        for attempt in range(max_retries):
            try:
                return await operation()
            except MatomeAppError as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{max_retries} due to: {e}")
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                msg = f"Operation failed: {e}"
                raise MatomeAppError(msg) from e
        msg = "Operation failed after max retries"
        raise MatomeAppError(msg)

    @abstractmethod
    async def execute(self) -> None:
        """Abstract method that concrete services must implement."""
