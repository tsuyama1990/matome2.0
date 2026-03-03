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
    # Check if the object is iterable and supports __len__ but is not a string
    if not hasattr(embedding, "__iter__") or isinstance(embedding, str):
        raise ValueError(ERR_EMBEDDING_MUST_BE_LIST)
    try:
        length = len(embedding)
    except TypeError:
        raise ValueError(ERR_EMBEDDING_MUST_BE_LIST)

    if length == 0:
        raise ValueError(ERR_EMBEDDING_CANNOT_BE_EMPTY)

    # Support numeric validation even if it's a numpy array or similar wrapper
    for x in embedding:
        if not hasattr(x, "__float__") and not isinstance(x, (int, float)):
            raise ValueError(ERR_EMBEDDING_MUST_BE_NUMERIC)


async def _with_retries(
    func: Callable[[], Coroutine[Any, None, T]], max_retries: int = 3, base_delay: float = 1.0
) -> T:
    """Retries the async function with exponential backoff on exceptions."""
    for attempt in range(max_retries):
        try:
            return await func()
        except ConnectionError as e:
            if "not initialized" in str(e):
                raise
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
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
