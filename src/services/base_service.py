import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from src.core.config import AppSettings
from src.core.exceptions import MatomeAppError
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore

T = TypeVar("T")


class BaseService(ABC):
    def __init__(self, llm_provider: ILLMProvider, vector_store: IVectorStore, config: AppSettings) -> None:
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        """Centralized retry mechanism for external API calls."""
        max_retries = self.config.RETRY_MAX_ATTEMPTS
        for attempt in range(max_retries):
            try:
                self.logger.info("Executing operation attempt %d/%d", attempt + 1, max_retries)
                result = await operation()
            except MatomeAppError as e:
                if attempt == max_retries - 1:
                    self.logger.exception("Operation failed after %d attempts", max_retries)
                    raise
                self.logger.warning("Retry %d/%d due to: %s", attempt + 1, max_retries, e)
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                msg = f"Operation failed: {e}"
                self.logger.exception(msg)
                raise MatomeAppError(msg) from e
            else:
                self.logger.info("Operation attempt %d/%d succeeded", attempt + 1, max_retries)
                return result
        msg = "Operation failed after max retries"
        raise MatomeAppError(msg)

    @abstractmethod
    async def execute(self) -> None:
        """Abstract method that concrete services must implement."""
