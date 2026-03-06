import asyncio
import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_ERROR_MSG_SHOULD_NOT_REACH_HERE = "Should not reach here"

def validate_embedding(embedding: Any) -> None:
    from src.core.constants import (
        ERR_EMBEDDING_CANNOT_BE_EMPTY,
        ERR_EMBEDDING_MUST_BE_LIST,
        ERR_EMBEDDING_MUST_BE_NUMERIC,
    )
    if not isinstance(embedding, list):
        raise TypeError(ERR_EMBEDDING_MUST_BE_LIST)
    if len(embedding) == 0:
        raise ValueError(ERR_EMBEDDING_CANNOT_BE_EMPTY)
    if not all(isinstance(x, (int, float)) for x in embedding):
        raise ValueError(ERR_EMBEDDING_MUST_BE_NUMERIC)


from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Encapsulates retry strategies and makes them configurable per service."""
    max_retries: int = 3
    base_delay: float = 1.0

async def _with_retries(
    func: Callable[[], Coroutine[Any, None, T]],
    max_retries: int | None = None,
    base_delay: float | None = None,
    policy: RetryPolicy | None = None
) -> T:
    """Retries the async function with exponential backoff on exceptions."""
    retries = max_retries if max_retries is not None else (policy.max_retries if policy else 3)
    delay = base_delay if base_delay is not None else (policy.base_delay if policy else 1.0)

    for attempt in range(retries):
        try:
            return await func()
        except ConnectionError as e:
            if "not initialized" in str(e):
                raise
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay * (2**attempt))
        except TimeoutError:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay * (2**attempt))
        except Exception:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay * (2**attempt))
    raise RuntimeError(_ERROR_MSG_SHOULD_NOT_REACH_HERE)


def with_retries(
    max_retries: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[..., Coroutine[Any, None, T]]], Callable[..., Coroutine[Any, None, T]]]:
    def decorator(
        func: Callable[..., Coroutine[Any, None, T]],
    ) -> Callable[..., Coroutine[Any, None, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async def _func_wrapper() -> T:
                return await func(*args, **kwargs)

            return await _with_retries(_func_wrapper, max_retries, base_delay)

        return wrapper

    return decorator
