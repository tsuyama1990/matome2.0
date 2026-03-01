from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.models.document import DocumentChunk
from src.domain.models.node import AnalysisAxis, ConceptNode, PivotBoard


@pytest.mark.asyncio
async def test_uat_aha_moment_scenario() -> None:
    """
    Simulates the User Acceptance Test scenario: UAT-01 - The "Aha!" Moment for a Product Manager
    This proves the core models can satisfy the requirements of:
    1. Document Ingestion (Chunks to Concept Nodes)
    2. Interactive Learning (Answering to Unlock Node)
    3. Pivot KJ Analysis (Restructuring to new Axis)
    """

    # --- Step 1: Ingestion (Simulated) ---
    doc_id = uuid4()
    chunks = [
        DocumentChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            text="Executive approval is needed if the budget exceeds £5000.",
            metadata={"entities": ["Executive", "Budget", "£5000"]},
        ),
        DocumentChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            text="Manager approval is required for all travel expenses.",
            metadata={"entities": ["Manager", "Travel"]},
        ),
    ]

    # Simulated RAPTOR tree generation
    root_node = ConceptNode(
        node_id=uuid4(),
        title="Approval Processes",
        summary="High-level overview of company approval processes.",
        level=0,
        is_unlocked=True,
    )

    locked_node = ConceptNode(
        node_id=uuid4(),
        parent_id=root_node.node_id,
        title="Special Approval Processes",
        summary="Detailed breakdown of budget thresholds requiring executive sign-off.",
        level=1,
        is_unlocked=False,
        chunk_references=[chunks[0].chunk_id],
    )

    # Assert initial state
    assert not locked_node.is_unlocked

    # --- Step 2: Interactive Learning (Question & Read) ---
    # User attempts to answer a question to unlock the node
    user_answer = "Executive approval is needed if the budget exceeds 5000."

    # Simulate LLM checking the answer (always success in this mock)
    mock_llm_check = AsyncMock(return_value=True)
    is_correct = await mock_llm_check(user_answer, locked_node.summary)

    if is_correct:
        # In actual business logic, we would use `.model_copy(update={"is_unlocked": True})`
        # because the domain model is immutable (frozen=True).
        unlocked_node = locked_node.model_copy(update={"is_unlocked": True})

    assert unlocked_node.is_unlocked

    # --- Step 3: Transformation (Pivot KJ) ---
    # User defines a new multi-dimensional axis
    axis = AnalysisAxis(
        name="Actor vs. State Transition", dimensions=["Executive", "Manager", "Employee"]
    )

    # Simulate LLM returning a structured clustering based on the axis
    mock_llm_pivot = AsyncMock(
        return_value={"Executive": [unlocked_node.node_id], "Manager": [], "Employee": []}
    )

    _ = await mock_llm_pivot([unlocked_node], axis)

    # Construct the PivotBoard domain model
    board = PivotBoard(
        board_id=uuid4(),
        original_document_id=doc_id,
        axis=axis,
        clusters={"Executive": [unlocked_node], "Manager": [], "Employee": []},
    )

    # Assert final structured state
    assert board.axis.name == "Actor vs. State Transition"
    assert "Executive" in board.clusters
    assert len(board.clusters["Executive"]) == 1
    assert board.clusters["Executive"][0].title == "Special Approval Processes"
    assert board.clusters["Executive"][0].is_unlocked
