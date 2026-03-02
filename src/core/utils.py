import asyncio
import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_ERROR_MSG_SHOULD_NOT_REACH_HERE = "Should not reach here"


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
