from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.models.board import AnalysisAxis, PivotBoard
from src.domain.models.document import DocumentChunk
from src.domain.models.node import ConceptNode


def test_document_chunk_validation() -> None:
    """Test valid creation of DocumentChunk."""
    chunk = DocumentChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="A valid test string representing semantic proposition.",
    )
    assert chunk.text == "A valid test string representing semantic proposition."


def test_document_chunk_forbids_extra() -> None:
    """Test DocumentChunk raises error on extra fields."""
    with pytest.raises(ValidationError):
        DocumentChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            text="Valid string",
            extra_field="Should fail",  # type: ignore
        )


def test_concept_node_validation() -> None:
    """Test constraints on ConceptNode."""
    node = ConceptNode(
        node_id=uuid4(),
        title="Valid Title",
        summary="A summary string representing high-density information.",
        level=0,
    )
    assert node.level == 0
    assert not node.is_unlocked


def test_concept_node_level_constraint() -> None:
    """Test ConceptNode level cannot be negative."""
    with pytest.raises(ValidationError):
        ConceptNode(node_id=uuid4(), title="Title", summary="A summary", level=-1)


def test_analysis_axis_validation() -> None:
    """Test AnalysisAxis validation."""
    axis = AnalysisAxis(name="SWOT", dimensions=["Strengths", "Weaknesses"])
    assert axis.name == "SWOT"
    assert len(axis.dimensions) == 2


def test_pivot_board_validation() -> None:
    """Test PivotBoard validation."""
    axis = AnalysisAxis(name="SWOT", dimensions=["Strengths"])
    board = PivotBoard(board_id=uuid4(), original_document_id=uuid4(), axis=axis)
    assert board.axis.name == "SWOT"
    assert len(board.clusters) == 0


def test_pivot_board_with_complex_clusters() -> None:
    """Test complex nested structure of PivotBoard."""
    axis = AnalysisAxis(name="System", dimensions=["Actors", "DataFlow"])

    node1 = ConceptNode(node_id=uuid4(), title="Node 1", summary="Sum 1", level=1)
    node2 = ConceptNode(node_id=uuid4(), title="Node 2", summary="Sum 2", level=2)

    board = PivotBoard(
        board_id=uuid4(),
        original_document_id=uuid4(),
        axis=axis,
        clusters={"Actors": [node1], "DataFlow": [node2, node1]},
    )

    assert "Actors" in board.clusters
    assert len(board.clusters["Actors"]) == 1
    assert board.clusters["DataFlow"][0].title == "Node 2"


def test_document_chunk_metadata_typing() -> None:
    """Ensure DocumentChunk metadata validates properly when given complex types."""
    chunk = DocumentChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="Sample",
        metadata={"entities": ["API", "DB"], "score": 0.95, "tags": {"time": "future"}},
    )
    assert chunk.metadata["score"] == 0.95
    assert len(chunk.metadata["entities"]) == 2


def test_concept_node_unlock() -> None:
    node = ConceptNode(node_id=uuid4(), title="Test", summary="Summary", level=1)
    assert node.is_unlocked is False
    node.unlock()
    assert node.is_unlocked is True


def test_base_domain_model_update() -> None:
    chunk_id = uuid4()
    doc_id = uuid4()
    chunk = DocumentChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        text="Original text",
    )
    updated_chunk = chunk.update(text="New text")
    assert updated_chunk.text == "New text"
    assert updated_chunk.chunk_id == chunk_id
    assert chunk.text == "Original text"  # Ensure original is immutable
