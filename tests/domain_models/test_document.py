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


@pytest.mark.asyncio
async def test_document_stream_chunks_not_found() -> None:
    doc = Document(id=uuid4(), title="Test Doc", file_path="/nonexistent/path/to/doc")
    with pytest.raises(FileNotFoundError):
        [chunk async for chunk in doc.stream_chunks()]


@pytest.mark.asyncio
async def test_document_stream_chunks_valid(tmp_path: Path) -> None:
    import anyio

    test_file = tmp_path / "test_doc.txt"
    async with await anyio.open_file(test_file, "w") as f:
        await f.write("Line 1\nLine 2\nLine 3\n")

    doc = Document(id=uuid4(), title="Test Doc", file_path=str(test_file))

    chunks = [chunk async for chunk in doc.stream_chunks(block_size=10)]
    assert len(chunks) > 1

    full_content = "".join(chunk.content for chunk in chunks)
    assert full_content == "Line 1\nLine 2\nLine 3\n"

    # Assert compression was integrated
    assert "_compressed" in chunks[0].metadata
    assert isinstance(chunks[0].metadata["_compressed"], str)
    assert len(chunks[0].metadata["_compressed"]) > 0
