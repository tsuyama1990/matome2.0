from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.pivot_graph import PivotGraph


def test_pivot_graph_valid_creation() -> None:
    graph_id = uuid4()
    graph = PivotGraph(id=graph_id, analytical_axis="SWOT")
    assert graph.id == graph_id
    assert graph.analytical_axis == "SWOT"
    assert graph.source_document_ids == []
    assert graph.clusters == {}


def test_pivot_graph_with_data() -> None:
    graph_id = uuid4()
    doc_id = uuid4()
    node_id = uuid4()
    graph = PivotGraph(
        id=graph_id,
        analytical_axis="SWOT",
        source_document_ids=[doc_id],
        clusters={"Strengths": [node_id]},
    )
    assert graph.source_document_ids == [doc_id]
    assert graph.clusters == {"Strengths": [node_id]}


def test_pivot_graph_empty_axis() -> None:
    with pytest.raises(ValidationError):
        PivotGraph(id=uuid4(), analytical_axis="")


def test_pivot_graph_extra_fields() -> None:
    with pytest.raises(ValidationError):
        PivotGraph(id=uuid4(), analytical_axis="SWOT", extra="invalid")  # type: ignore[call-arg]


def test_pivot_graph_invalid_analytical_axis() -> None:
    with pytest.raises(ValidationError):
        PivotGraph(id=uuid4(), analytical_axis="")

    with pytest.raises(ValidationError):
        PivotGraph(id=uuid4(), analytical_axis="a" * 256)
