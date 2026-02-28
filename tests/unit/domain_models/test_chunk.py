from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.chunk import SemanticChunk


def test_valid_semantic_chunk() -> None:
    chunk_id = uuid4()
    chunk = SemanticChunk(
        id=chunk_id,
        content="This is a valid chunk.",
        embedding=[0.1, 0.2, 0.3],
        metadata={"source": "book"},
    )
    assert chunk.id == chunk_id
    assert chunk.content == "This is a valid chunk."
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.metadata == {"source": "book"}


def test_empty_content_raises_validation_error() -> None:
    chunk_id = uuid4()
    with pytest.raises(ValidationError):
        SemanticChunk(id=chunk_id, content="")


def test_whitespace_content_raises_validation_error() -> None:
    chunk_id = uuid4()
    with pytest.raises(ValidationError):
        SemanticChunk(id=chunk_id, content="   ")


def test_invalid_uuid_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        SemanticChunk(id="invalid-uuid", content="valid")  # type: ignore[arg-type]


def test_extra_fields_forbidden() -> None:
    chunk_id = uuid4()
    with pytest.raises(ValidationError):
        SemanticChunk(id=chunk_id, content="valid", extra_field="forbidden")  # type: ignore[call-arg]
