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
async def test_document_stream_chunks() -> None:
    doc = Document(id=uuid4(), title="Test Doc", file_path="/path/to/doc")
    chunks = [chunk async for chunk in doc.stream_chunks()]
    assert len(chunks) == 1
    assert chunks[0].id == doc.id
    assert chunks[0].content == "dummy"
