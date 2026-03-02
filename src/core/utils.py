import asyncio
import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_ERROR_MSG_SHOULD_NOT_REACH_HERE = "Should not reach here"


async def _with_retries(
    func: Callable[[], Coroutine[Any, Any, T]], max_retries: int = 3, base_delay: float = 1.0
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
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(base_delay * (2**attempt))
    raise RuntimeError(_ERROR_MSG_SHOULD_NOT_REACH_HERE)


def with_retries(
    max_retries: int = 3, base_delay: float = 1.0
) -> Callable[[Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]]:
    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
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

        return wrapper

    return decorator
