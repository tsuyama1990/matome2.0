from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.chunk import DimensionalTags, SemanticChunk


def test_semantic_chunk_valid_creation() -> None:
    chunk_id = uuid4()
    doc_id = uuid4()
    chunk = SemanticChunk(
        id=chunk_id, document_id=doc_id, content="This is valid content.", metadata={}
    )
    assert chunk.id == chunk_id
    assert chunk.document_id == doc_id
    assert chunk.content == "This is valid content."
    assert chunk.entities == []
    assert chunk.dimensional_tags.time_axis is None


def test_semantic_chunk_with_entities() -> None:
    chunk = SemanticChunk(
        id=uuid4(), document_id=uuid4(), content="Test", entities=["Person", "Organization"]
    )
    assert chunk.entities == ["Person", "Organization"]


def test_semantic_chunk_with_dimensional_tags() -> None:
    tags = DimensionalTags(
        time_axis="future",
        logic_axis="reasoning",
        polarity_axis="positive",
        system_design_axis="actor",
    )
    chunk = SemanticChunk(id=uuid4(), document_id=uuid4(), content="Test", dimensional_tags=tags)
    assert chunk.dimensional_tags.time_axis == "future"
    assert chunk.dimensional_tags.logic_axis == "reasoning"


def test_semantic_chunk_empty_content() -> None:
    with pytest.raises(ValidationError):
        SemanticChunk(id=uuid4(), document_id=uuid4(), content="", metadata={})


def test_semantic_chunk_metadata_invalid_key() -> None:
    with pytest.raises(ValidationError):
        SemanticChunk(id=uuid4(), document_id=uuid4(), content="test", metadata={1: "test"})  # type: ignore[dict-item]


def test_semantic_chunk_compression() -> None:
    chunk_id = uuid4()
    doc_id = uuid4()
    original_text = "This is a test content that needs to be compressed." * 10
    chunk = SemanticChunk(id=chunk_id, document_id=doc_id, content=original_text, metadata={})

    compressed = chunk.compress_content()
    assert isinstance(compressed, bytes)
    assert len(compressed) < len(original_text.encode("utf-8"))

    decompressed = chunk.decompress_content(compressed)
    assert decompressed == original_text
