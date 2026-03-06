import asyncio
from unittest.mock import AsyncMock

import pytest

from src.core.utils import _with_retries, with_retries


@pytest.mark.asyncio
async def test_with_retries_success() -> None:
    @with_retries(max_retries=3, base_delay=0)
    async def success_func() -> str:
        return "success"

    assert await success_func() == "success"


@pytest.mark.asyncio
async def test_with_retries_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    mock_func = AsyncMock()
    mock_func.side_effect = [ConnectionError("timeout"), "success"]

    @with_retries(max_retries=3, base_delay=0)
    async def retry_func() -> str:
        return str(await mock_func())

    assert await retry_func() == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_with_retries_connection_error_not_initialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    @with_retries(max_retries=3, base_delay=0)
    async def fail_func() -> str:
        raise ConnectionError("not initialized")

    with pytest.raises(ConnectionError, match="not initialized"):
        await fail_func()


@pytest.mark.asyncio
async def test_with_retries_connection_error_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    @with_retries(max_retries=2, base_delay=0)
    async def fail_func() -> str:
        raise ConnectionError("network failed")

    with pytest.raises(ConnectionError, match="network failed"):
        await fail_func()


@pytest.mark.asyncio
async def test_with_retries_timeout_error_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    @with_retries(max_retries=2, base_delay=0)
    async def fail_func() -> str:
        raise TimeoutError("timed out")

    with pytest.raises(TimeoutError, match="timed out"):
        await fail_func()


@pytest.mark.asyncio
async def test_with_retries_exception_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    @with_retries(max_retries=2, base_delay=0)
    async def fail_func() -> str:
        raise ValueError("generic error")

    with pytest.raises(ValueError, match="generic error"):
        await fail_func()


@pytest.mark.asyncio
async def test__with_retries_success() -> None:
    async def success_func() -> str:
        return "success"

    assert await _with_retries(success_func, max_retries=3, base_delay=0) == "success"


@pytest.mark.asyncio
async def test__with_retries_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    mock_func = AsyncMock()
    mock_func.side_effect = [ConnectionError("timeout"), "success"]

    assert await _with_retries(mock_func, max_retries=3, base_delay=0) == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test__with_retries_connection_error_not_initialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    async def fail_func() -> str:
        raise ConnectionError("not initialized")

    with pytest.raises(ConnectionError, match="not initialized"):
        await _with_retries(fail_func, max_retries=3, base_delay=0)


@pytest.mark.asyncio
async def test__with_retries_connection_error_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    async def fail_func() -> str:
        raise ConnectionError("network failed")

    with pytest.raises(ConnectionError, match="network failed"):
        await _with_retries(fail_func, max_retries=2, base_delay=0)


@pytest.mark.asyncio
async def test__with_retries_exception_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    async def fail_func() -> str:
        raise ValueError("generic error")

    with pytest.raises(ValueError, match="generic error"):
        await _with_retries(fail_func, max_retries=2, base_delay=0)


@pytest.mark.asyncio
async def test_with_retries_runtime_error() -> None:
    async def always_fails() -> str:
        raise ValueError("generic")

    # max_retries=0 should immediately raise RuntimeError since the loop won't execute
    with pytest.raises(RuntimeError, match="Should not reach here"):
        await _with_retries(always_fails, max_retries=0)
