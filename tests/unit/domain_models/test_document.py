from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.document import Document, IngestionStatus, SourceType


def test_valid_document() -> None:
    doc_id = uuid4()
    root_id = uuid4()
    doc = Document(
        id=doc_id,
        filename="research_paper.pdf",
        source_type=SourceType.PDF,
        root_node_id=root_id,
    )

    assert doc.id == doc_id
    assert doc.filename == "research_paper.pdf"
    assert doc.source_type == SourceType.PDF
    assert doc.ingestion_status == IngestionStatus.PENDING
    assert doc.root_node_id == root_id
    assert doc.metadata == {}


def test_invalid_source_type_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        Document(
            id=uuid4(),
            filename="document.txt",
            source_type="INVALID_TYPE",  # type: ignore[arg-type]
        )


def test_empty_filename_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        Document(
            id=uuid4(),
            filename="",
            source_type=SourceType.MARKDOWN,
        )

    with pytest.raises(ValidationError):
        Document(
            id=uuid4(),
            filename="   ",
            source_type=SourceType.MARKDOWN,
        )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Document(
            id=uuid4(),
            filename="doc.pdf",
            source_type=SourceType.PDF,
            extra_field="forbidden",  # type: ignore[call-arg]
        )
