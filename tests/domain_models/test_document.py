from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.document import Document


def test_document_valid_creation() -> None:
    doc_id = uuid4()
    doc = Document(id=doc_id, title="Test Doc", file_path="/path/to/doc")
    assert doc.id == doc_id
    assert doc.title == "Test Doc"
    assert doc.file_path == "/path/to/doc"


def test_document_empty_title() -> None:
    with pytest.raises(ValidationError):
        Document(id=uuid4(), title="", file_path="/path/to/doc")


def test_document_empty_file_path() -> None:
    with pytest.raises(ValidationError):
        Document(id=uuid4(), title="Test Doc", file_path="")


def test_document_malicious_title() -> None:
    with pytest.raises(ValidationError):
        Document(id=uuid4(), title="<script>alert(1)</script>", file_path="/path")


def test_document_malicious_path() -> None:
    with pytest.raises(ValidationError):
        Document(id=uuid4(), title="Valid", file_path="/path/&rm -rf")


@pytest.mark.asyncio
async def test_document_path_traversal() -> None:
    doc = Document(id=uuid4(), title="Test", file_path="/app/data/../etc/passwd")
    with pytest.raises(ValueError, match="Directory traversal"):
        await doc._validate_path_security_async("/app/data")


@pytest.mark.asyncio
async def test_document_path_outside_allowed() -> None:
    doc = Document(id=uuid4(), title="Test", file_path="/etc/passwd")
    with pytest.raises(ValueError, match="File path must be within"):
        await doc._validate_path_security_async("/app/data")


@pytest.mark.asyncio
async def test_document_path_traversal_prefix_bypass() -> None:
    # Ensure strings like /app/data_bypass do not bypass check when the real folder is /app/data
    doc = Document(id=uuid4(), title="Test", file_path="/app/data_bypass/file.txt")
    with pytest.raises(ValueError, match="File path must be within"):
        await doc._validate_path_security_async("/app/data")


@pytest.mark.asyncio
async def test_document_stream_chunks_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = Document(id=uuid4(), title="Test Doc", file_path="/app/data/nonexistent.txt")

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )
    with pytest.raises(FileNotFoundError):
        async for _chunk in doc.stream_chunks(allowed_dir="/app/data"):
            pass


@pytest.mark.asyncio
async def test_document_stream_chunks_read_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("Test")
    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    # Mock aiofiles.open to raise an OSError upon reading
    class BrokenFileAsyncMock:
        async def __aenter__(self) -> "BrokenFileAsyncMock":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

        def __aiter__(self) -> "BrokenFileAsyncMock":
            return self

        async def __anext__(self) -> bytes:
            msg = "Mocked read error"
            raise OSError(msg)

        async def read(self, size: int) -> bytes:
            msg = "Mocked read error"
            raise OSError(msg)

    monkeypatch.setattr("aiofiles.open", lambda *args, **kwargs: BrokenFileAsyncMock())

    with pytest.raises(OSError, match="Failed to read document"):
        async for _chunk in doc.stream_chunks(allowed_dir="/app/data"):
            pass


@pytest.mark.asyncio
async def test_document_stream_chunks_partial_read_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "test_doc.txt"
    test_file.write_bytes(b"Good start\n")
    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    class PartialFailureAsyncMock:
        def __init__(self) -> None:
            self.reads = 0

        async def __aenter__(self) -> "PartialFailureAsyncMock":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

        def __aiter__(self) -> "PartialFailureAsyncMock":
            return self

        async def read(self, size: int) -> bytes:
            if self.reads == 0:
                self.reads += 1
                return b"First read is okay"
            msg = "Mocked partial read error"
            raise OSError(msg)

    monkeypatch.setattr("aiofiles.open", lambda *args, **kwargs: PartialFailureAsyncMock())

    with pytest.raises(OSError, match="Failed to read document"):
        async for _chunk in doc.stream_chunks(allowed_dir="/app/data", block_size=10):
            pass


@pytest.mark.asyncio
async def test_document_stream_chunks_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anyio

    test_file = tmp_path / "test_doc.txt"
    async with await anyio.open_file(test_file, "w") as f:
        await f.write("Line 1\nLine 2\nLine 3\n")

    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    chunks = []
    async for chunk in doc.stream_chunks(allowed_dir="/app/data", block_size=10):
        chunks.append(chunk)
    assert len(chunks) > 1

    full_content = "".join(chunk.content for chunk in chunks)
    assert full_content == "Line 1\nLine 2\nLine 3"


@pytest.mark.asyncio
async def test_document_stream_chunks_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "empty_doc.txt"
    test_file.write_text("")

    doc = Document(id=uuid4(), title="Empty Doc", file_path=str(test_file))

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    chunks = []
    async for chunk in doc.stream_chunks(allowed_dir=str(tmp_path)):
        chunks.append(chunk)

    assert len(chunks) == 0


@pytest.mark.asyncio
async def test_document_stream_chunks_encoding_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "bad_encoding.txt"
    # Make sure we write valid UTF-8, but split it right on a multi-byte sequence to test IncrementalDecoder logic

    # 🤡 is a 4-byte character. We'll write it, but if streamed in chunks of 2, it would break normal decoders.
    # However, our IncrementalDecoder cleanly handles it. The bytes for 🤡 are b'\xf0\x9f\xa4\xa1'
    emoji_bytes = b"\xf0\x9f\xa4\xa1" * 5  # Write 5 emojis

    # Add a truly broken byte sequence in the middle to trigger the fallback path as well
    broken_bytes = b"\xff\xfe\xfd"

    test_file.write_bytes(emoji_bytes + broken_bytes + emoji_bytes)

    doc = Document(id=uuid4(), title="Bad Encoding", file_path=str(test_file))

    async def mock_validate(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security_async", mock_validate
    )

    # The stream chunks now replaces invalid encoding characters cleanly rather than crashing the pipeline.
    # We assert that the fallback is applied successfully.
    chunks = []
    async for chunk in doc.stream_chunks(
        allowed_dir=str(tmp_path), block_size=2
    ):  # Force chunking in the middle of characters
        chunks.append(chunk)

    assert len(chunks) > 0
    # Ensure no data corruption. Our 5 emojis should be fully recovered since IncrementalDecoder buffers them.
    full_text = "".join(c.content for c in chunks)
    assert "🤡🤡🤡🤡🤡" in full_text
