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


class CircuitBreakerOpenError(MatomeAppError):
    """Raised when the circuit breaker is open to prevent cascading failures."""


class BaseService(ABC):
    def __init__(
        self, llm_provider: ILLMProvider, vector_store: IVectorStore, config: AppSettings
    ) -> None:
        self.llm_provider = llm_provider
        self.vector_store = vector_store
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._circuit_open = False
        self._failure_count = 0
        self._circuit_reset_time: float = 0

    def _check_circuit(self) -> None:
        import time

        if self._circuit_open:
            if time.time() > self._circuit_reset_time:
                self._circuit_open = False
                self._failure_count = 0
                self.logger.info("Circuit breaker closed (reset)")
            else:
                msg = "Circuit is currently open. Blocking request."
                raise CircuitBreakerOpenError(msg)

    def _record_failure(self) -> None:
        import time

        self._failure_count += 1
        # Arbitrary threshold: 5 consecutive failures trips the breaker
        if self._failure_count >= 5:
            self._circuit_open = True
            # Arbitrary reset timeout: 30 seconds
            self._circuit_reset_time = time.time() + 30
            self.logger.warning("Circuit breaker opened due to %d failures", self._failure_count)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        """Centralized retry mechanism for external API calls with Circuit Breaker.

        Args:
            operation: An async callable that returns type T.

        Returns:
            The successful result of the operation of type T.

        Raises:
            MatomeAppError: If the maximum retry attempts are exceeded.
            CircuitBreakerOpenError: If the circuit breaker is active.
        """
        self._check_circuit()
        max_retries = self.config.RETRY_MAX_ATTEMPTS
        for attempt in range(max_retries):
            try:
                self.logger.info("Executing operation attempt %d/%d", attempt + 1, max_retries)
                result = await operation()
            except MatomeAppError as e:
                if attempt == max_retries - 1:
                    self.logger.exception("Operation failed after %d attempts", max_retries)
                    self._record_failure()
                    raise
                self.logger.warning("Retry %d/%d due to: %s", attempt + 1, max_retries, e)
                await asyncio.sleep(self.config.RETRY_DELAY_SECONDS)
            except Exception as e:
                msg = f"Operation failed: {e}"
                self.logger.exception(msg)
                self._record_failure()
                raise MatomeAppError(msg) from e
            else:
                self.logger.info("Operation attempt %d/%d succeeded", attempt + 1, max_retries)
                self._failure_count = 0  # reset on success
                return result

        self._record_failure()
        msg = "Operation failed after max retries"
        raise MatomeAppError(msg)

    async def execute_batch_with_retry(
        self,
        operations: list[Callable[[], Awaitable[T]]],
        batch_size: int = 10,
    ) -> list[T]:
        """Executes a list of operations concurrently with batching and retry mechanisms to prevent API flooding."""
        semaphore = asyncio.Semaphore(batch_size)

        async def _bounded_execute(op: Callable[[], Awaitable[T]]) -> T:
            async with semaphore:
                return await self.execute_with_retry(op)

        tasks = [_bounded_execute(op) for op in operations]
        return await asyncio.gather(*tasks)

    @abstractmethod
    async def execute(self) -> None:
        """Abstract method that concrete services must implement."""
