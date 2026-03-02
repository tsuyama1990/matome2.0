import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


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
    msg = "Should not reach here"
    raise RuntimeError(msg)
