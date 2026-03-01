from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

from src.infrastructure.storage import LocalStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return LocalStorage(base_dir=tmp_path, create_dir=True)


async def dummy_stream(content: bytes, chunks: int = 2) -> AsyncGenerator[bytes, None]:
    chunk_size = len(content) // chunks
    for i in range(chunks):
        start = i * chunk_size
        end = start + chunk_size if i < chunks - 1 else len(content)
        yield content[start:end]


@pytest.mark.asyncio
async def test_save_upload_stream_success(storage: LocalStorage, tmp_path: Path) -> None:
    filename = "test.txt"
    content = b"Hello, World!"

    saved_path = await storage.save_upload_stream(filename, dummy_stream(content))

    assert saved_path.exists()
    assert saved_path.read_bytes() == content


@pytest.mark.asyncio
async def test_save_upload_stream_path_traversal(storage: LocalStorage) -> None:
    filename = "../test.txt"
    content = b"Malicious"

    with pytest.raises(ValueError, match="Path traversal attempt"):
        await storage.save_upload_stream(filename, dummy_stream(content))


@pytest.mark.asyncio
async def test_save_upload_stream_size_limit(storage: LocalStorage) -> None:
    filename = "large.txt"
    content = b"1234567890"  # 10 bytes

    with pytest.raises(ValueError, match="File size exceeds maximum allowed"):
        # Limit to 5 bytes
        await storage.save_upload_stream(filename, dummy_stream(content), max_size_bytes=5)


def test_read_file_stream_success(storage: LocalStorage, tmp_path: Path) -> None:
    # Prepare file
    file_path = tmp_path / "read.txt"
    file_path.write_bytes(b"File content")

    stream = storage.read_file_stream(file_path)
    chunks = list(stream)

    assert b"".join(chunks) == b"File content"


def test_read_file_stream_path_traversal(storage: LocalStorage, tmp_path: Path) -> None:
    outside_path = tmp_path.parent / "outside.txt"

    with pytest.raises(ValueError, match="Path traversal attempt"):
        list(storage.read_file_stream(outside_path))


@pytest.mark.asyncio
async def test_read_file_stream_async_success(storage: LocalStorage, tmp_path: Path) -> None:
    # Prepare file: write 5MB using a repeated byte chunk
    file_path = tmp_path / "read_async.txt"
    chunk = b"A" * 1024 * 1024  # 1MB
    file_path.write_bytes(chunk * 5)  # Write 5MB to disk to prevent OOM in memory string appending

    # Read asynchronously
    stream = storage.read_file_stream_async(file_path)
    chunks = []
    async for c in stream:
        chunks.append(c)

    assert "".join(chunks) == "A" * 5 * 1024 * 1024


@pytest.mark.asyncio
async def test_read_file_stream_async_path_traversal(storage: LocalStorage, tmp_path: Path) -> None:
    outside_path = tmp_path.parent / "outside.txt"

    stream = storage.read_file_stream_async(outside_path)
    with pytest.raises(ValueError, match="Path traversal attempt"):
        async for _ in stream:
            pass
