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
