from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.node import KnowledgeNode


def test_valid_knowledge_node() -> None:
    node_id = uuid4()
    child_id = uuid4()
    chunk_id = uuid4()

    node = KnowledgeNode(
        id=node_id,
        level=0,
        title="Valid Node",
        dense_summary="This is a valid summary.",
        children=[child_id],
        source_chunks=[chunk_id],
    )
    assert node.id == node_id
    assert node.level == 0
    assert node.title == "Valid Node"
    assert node.dense_summary == "This is a valid summary."
    assert child_id in node.children
    assert chunk_id in node.source_chunks


def test_invalid_level_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=-1,
            title="Invalid Level Node",
            dense_summary="Summary",
        )


def test_empty_title_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=0,
            title="",
            dense_summary="Summary",
        )

    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=0,
            title="   ",
            dense_summary="Summary",
        )


def test_empty_summary_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=0,
            title="Node Title",
            dense_summary="",
        )

    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=0,
            title="Node Title",
            dense_summary="   ",
        )


def test_self_child_raises_validation_error() -> None:
    node_id = uuid4()
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=node_id,
            level=0,
            title="Self Child Node",
            dense_summary="Summary",
            children=[node_id],
        )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(),
            level=0,
            title="Node Title",
            dense_summary="Summary",
            extra_field="forbidden",  # type: ignore[call-arg]
        )
