from pathlib import Path
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


def test_document_path_traversal(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = Document(id=uuid4(), title="Test", file_path="/app/data/../etc/passwd")
    with pytest.raises(ValueError, match="Directory traversal"):
        doc._validate_path_security("/app/data")


def test_document_path_outside_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = Document(id=uuid4(), title="Test", file_path="/etc/passwd")
    with pytest.raises(ValueError, match="File path must be within"):
        doc._validate_path_security("/app/data")


def test_document_path_traversal_prefix_bypass() -> None:
    # Ensure strings like /app/data_bypass do not bypass check when the real folder is /app/data
    doc = Document(id=uuid4(), title="Test", file_path="/app/data_bypass/file.txt")
    with pytest.raises(ValueError, match="File path must be within"):
        doc._validate_path_security("/app/data")


@pytest.mark.asyncio
async def test_document_stream_chunks_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    doc = Document(id=uuid4(), title="Test Doc", file_path="/app/data/nonexistent.txt")
    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security", lambda self, allowed_dir: None
    )
    with pytest.raises(FileNotFoundError):
        [chunk async for chunk in doc.stream_chunks(allowed_dir="/app/data")]


@pytest.mark.asyncio
async def test_document_stream_chunks_read_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test_file = tmp_path / "test_doc.txt"
    test_file.write_text("Test")
    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))

    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security", lambda self, allowed_dir: None
    )

    # Mock aiofiles.open to raise an OSError upon reading
    from typing import Any

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

    monkeypatch.setattr("aiofiles.open", lambda *args, **kwargs: BrokenFileAsyncMock())

    with pytest.raises(OSError, match="Failed to read document"):
        [chunk async for chunk in doc.stream_chunks(allowed_dir="/app/data")]


@pytest.mark.asyncio
async def test_document_stream_chunks_valid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anyio

    test_file = tmp_path / "test_doc.txt"
    async with await anyio.open_file(test_file, "w") as f:
        await f.write("Line 1\nLine 2\nLine 3\n")

    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))
    monkeypatch.setattr(
        "src.domain_models.document.Document._validate_path_security", lambda self, allowed_dir: None
    )

    chunks = [chunk async for chunk in doc.stream_chunks(allowed_dir="/app/data", block_size=10)]
    assert len(chunks) > 1

    full_content = "".join(chunk.content for chunk in chunks)
    assert full_content == "Line 1\nLine 2\nLine 3\n"
