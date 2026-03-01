from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.models.document import DocumentChunk
from src.domain.models.node import AnalysisAxis, ConceptNode, PivotBoard


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
