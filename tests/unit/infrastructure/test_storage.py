from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

from src.infrastructure.storage import LocalStorage, StorageFactory


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorage:
    return StorageFactory.create_local_storage(base_dir=tmp_path, create_dir=True)


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

    saved_path_str = await storage.save_upload_stream(filename, dummy_stream(content))

    # Run sync assertions out of the event loop to bypass ASYNC240 correctly using storage tools
    assert storage.exists(saved_path_str)
    content_chunks = list(storage.read_file_stream(saved_path_str))
    assert b"".join(content_chunks) == content


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

    stream = storage.read_file_stream(str(file_path))
    chunks = list(stream)

    assert b"".join(chunks) == b"File content"


def test_read_file_stream_path_traversal(storage: LocalStorage, tmp_path: Path) -> None:
    outside_path = tmp_path.parent / "outside.txt"

    with pytest.raises(ValueError, match="Path traversal attempt"):
        list(storage.read_file_stream(str(outside_path)))


@pytest.mark.asyncio
async def test_read_file_stream_async_success(storage: LocalStorage, tmp_path: Path) -> None:
    # Prepare file: write 5MB using a repeated byte chunk
    file_path = tmp_path / "read_async.txt"
    chunk = b"A" * 1024 * 1024  # 1MB
    file_path.write_bytes(chunk * 5)  # Write 5MB to disk to prevent OOM in memory string appending

    # Read asynchronously
    stream = storage.read_file_stream_async(str(file_path))
    chunks = []
    async for c in stream:
        chunks.append(c)

    assert "".join(chunks) == "A" * 5 * 1024 * 1024


@pytest.mark.asyncio
async def test_save_upload_stream_cleanup_on_error(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)

    async def err_stream() -> AsyncGenerator[bytes, None]:
        yield b"chunk1"
        raise OSError("fake error")

    with pytest.raises(IOError, match="fake error"):
        await storage.save_upload_stream("test.txt", err_stream())

    assert not (tmp_path / "test.txt.tmp").exists()
    assert not (tmp_path / "test.txt").exists()


def test_exists(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)
    f = tmp_path / "test.txt"
    f.write_text("ok")
    assert storage.exists(str(f)) is True
    assert storage.exists(str(tmp_path / "nonexistent.txt")) is False


def test_get_metadata(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)
    f = tmp_path / "test.txt"
    f.write_text("ok")
    meta = storage.get_metadata(str(f))
    assert "size" in meta
    assert meta["size"] == 2
    assert "modified" in meta


def test_initialize(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path / "init_dir", create_dir=False)
    assert not (tmp_path / "init_dir").exists()
    storage.initialize()
    assert (tmp_path / "init_dir").exists()


@pytest.mark.asyncio
async def test_read_file_stream_async_invalid_path(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)

    # Passing an invalid type that causes `resolve()` to throw an exception
    class BadPath(Path):
        def is_absolute(self) -> bool:
            return True

    with pytest.raises(ValueError, match="Path traversal attempt"):
        # Not a string, but simulating an Exception in the `try...except Exception:` block
        # The easiest way to trigger it is to provide a path that raises an exception when resolved
        bad_path = "\0invalid"  # Nul character often causes OS errors on resolve
        async for _ in storage.read_file_stream_async(bad_path):
            pass


@pytest.mark.asyncio
async def test_read_file_stream_async_final_decode(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)
    file_path = tmp_path / "test.txt"
    # Write a multi-byte character sequence that gets split, or just use a final text string
    file_path.write_bytes(b"hello")

    chunks = []
    async for chunk in storage.read_file_stream_async(str(file_path)):
        chunks.append(chunk)

    assert "".join(chunks) == "hello"


@pytest.mark.asyncio
async def test_read_file_stream_async_incomplete_unicode(tmp_path: Path) -> None:
    storage = StorageFactory.create_local_storage(base_dir=tmp_path)
    file_path = tmp_path / "test.txt"
    # Write a multi-byte sequence, but we truncate it so the incremental decoder
    # waits for the rest and eventually decodes it with errors="replace" on the final step
    file_path.write_bytes(b"\xe2\x82")  # Missing \xac for Euro sign

    chunks = []
    async for chunk in storage.read_file_stream_async(str(file_path)):
        chunks.append(chunk)

    assert len(chunks) == 1
    # U+FFFD is the replacement character
    assert chunks[0] == "\ufffd"
