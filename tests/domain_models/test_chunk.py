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


def test_semantic_chunk_malicious_content() -> None:
    with pytest.raises(ValidationError, match="Potentially malicious content detected"):
        SemanticChunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Normal <script>alert('pwn')</script> text",
            metadata={},
        )

    with pytest.raises(ValidationError, match="Potentially malicious content detected"):
        SemanticChunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Check this link javascript:alert(1)",
            metadata={},
        )

    with pytest.raises(ValidationError, match="Potentially malicious content detected"):
        SemanticChunk(
            id=uuid4(), document_id=uuid4(), content="<img src='x' onerror='alert(1)'>", metadata={}
        )


def test_semantic_chunk_invalid_encoding() -> None:
    # Directly test the validator since pydantic does pre-casting before the model_validator
    from src.domain_models.chunk import SemanticChunk

    class BadString(str):
        def encode(self, *args, **kwargs):
            raise UnicodeEncodeError("utf-8", "", 0, 1, "mocked")

    # Bypass pydantic's internal coercion logic by explicitly testing the manual step
    chunk = SemanticChunk(id=uuid4(), document_id=uuid4(), content="test", metadata={})
    chunk.content = BadString("test")

    with pytest.raises(ValueError, match="Content contains invalid UTF-8 characters"):
        chunk.validate_content_safety()


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


def test_semantic_chunk_decompression_error() -> None:
    chunk = SemanticChunk(id=uuid4(), document_id=uuid4(), content="test", metadata={})
    with pytest.raises(ValueError, match="Failed to decompress content"):
        chunk.decompress_content(b"invalid data")
