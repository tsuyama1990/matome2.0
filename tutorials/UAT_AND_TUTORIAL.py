from typing import Any

import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def display_welcome_message(mo: Any) -> tuple[Any, ...]:
    _message = mo.md(
        """
        # matome - User Acceptance Test & Tutorial

        Welcome to matome! This interactive notebook will guide you through the "Aha! Moment" for a Product Manager (Scenario UAT-01).
        You will see how matome takes a dense business manual, extracts semantic meaning into a RAPTOR-like tree, engages the user via SQ3R (answering a question to unlock knowledge), and finally dynamically restructures the information into a new format (Pivot KJ).
        """
    )
    return (_message,)


@app.cell
def import_dependencies() -> tuple[Any, ...]:
    import asyncio
    from pathlib import Path
    from uuid import uuid4

    import marimo as mo

    from tutorials.tutorial_config import TutorialDataFactory
    from tutorials.tutorial_domain import (
        MockAnalysisAxis,
        MockConceptNode,
        MockDocumentChunk,
        MockPivotBoard,
    )

    mock_analysis_axis = MockAnalysisAxis
    mock_concept_node = MockConceptNode
    mock_document_chunk = MockDocumentChunk
    mock_pivot_board = MockPivotBoard
    tutorial_data_factory = TutorialDataFactory

    return (
        mock_analysis_axis,
        mock_concept_node,
        mock_document_chunk,
        Path,
        mock_pivot_board,
        tutorial_data_factory,
        asyncio,
        mo,
        uuid4,
    )


@app.cell
def display_step_one(mo: Any) -> tuple[Any, ...]:
    _message = mo.md(
        """
        ## Step 1: Ingestion & RAPTOR Tree Generation

        Imagine you upload a legacy system manual (`testfiles/test_text.txt`). Instead of a wall of text, matome's ingestion pipeline (simulated here) creates **Document Chunks** and builds a hierarchical **Concept Node** tree.
        """
    )
    return (_message,)


@app.cell
def generate_mock_tree(
    mock_concept_node: Any, mock_document_chunk: Any, tutorial_data_factory: Any, uuid4: Any
) -> tuple[Any, ...]:
    doc_id = uuid4()
    chunks = tutorial_data_factory.create_mock_chunks(doc_id, uuid4)
    root_node = tutorial_data_factory.create_mock_root_node(uuid4)
    locked_node = tutorial_data_factory.create_mock_locked_node(
        root_node.node_id, chunks[0].chunk_id, uuid4
    )
    return chunks, doc_id, locked_node, root_node


@app.cell
def display_step_two(locked_node: Any, mo: Any) -> tuple[Any, ...]:
    _message = mo.md(
        f"""
        ## Step 2: Interactive Learning (SQ3R)

        You want to read the **{locked_node.title}** node. But it's currently locked to prevent passive reading.

        **AI Tutor asks:** "What condition do you think requires executive approval instead of just the manager's?"
        """
    )
    return (_message,)


@app.cell
def get_user_answer(mo: Any) -> tuple[Any, ...]:
    user_answer = mo.ui.text(
        label="Your answer",
        placeholder="Type your answer here...",
        value="",
    )
    return (user_answer,)


@app.cell
async def evaluate_answer(locked_node: Any, mo: Any, user_answer: Any) -> tuple[Any, ...]:
    async def simulate_llm_check(answer: str, summary: str) -> bool:
        """Simulates LLM context evaluation."""
        return bool("5000" in answer or "executive" in answer.lower())

    if not user_answer.value:
        eval_result = mo.md("*Awaiting your answer...*")
    else:
        is_correct = await simulate_llm_check(user_answer.value, locked_node.summary)
        if is_correct:
            locked_node.unlock()
            eval_result = mo.md(
                f"**Success!** Node unlocked. \n\n**High-Density Summary (CoD):**\n> {locked_node.summary}"
            )
        else:
            eval_result = mo.md("**Not quite.** Try thinking about budget thresholds!")

    return (eval_result,)


@app.cell
def display_step_three(locked_node: Any, mo: Any) -> tuple[Any, ...]:
    _message = mo.md(
        f"""
        **Node Status Check:** Is the node unlocked? **{locked_node.is_unlocked}**

        ## Step 3: Transformation (Pivot KJ)

        Now that you've understood the manual, you want to redesign the system. Let's pivot the knowledge away from "Chapters" and into a workflow based on "Actors".
        """
    )
    return (_message,)


@app.cell
def create_pivot_board(
    mock_analysis_axis: Any,
    mock_pivot_board: Any,
    tutorial_data_factory: Any,
    doc_id: Any,
    locked_node: Any,
    mo: Any,
    uuid4: Any,
) -> tuple[Any, ...]:
    axis = tutorial_data_factory.create_mock_axis()
    clusters = tutorial_data_factory.create_mock_clusters(locked_node)

    board = mock_pivot_board(
        board_id=uuid4(),
        original_document_id=doc_id,
        axis=axis,
        clusters=clusters,
    )

    _message = mo.md(f"**Created Pivot Board!** Axis: {board.axis.name}")
    return axis, board, clusters


@app.cell
def display_step_four(tutorial_data_factory: Any, board: Any, mo: Any) -> tuple[Any, ...]:
    mermaid_code = tutorial_data_factory.generate_mermaid_diagram(board.clusters)

    _message = mo.md(
        f"""
        ## Step 4: Export to Requirements Document

        Based on the new {board.axis.name} clusters, matome generates the To-Be system workflow!

        ### Extracted Workflow
        - **Executive:** Handles {board.clusters["Executive"][0].title}

        ### Mermaid Diagram
        \n{mermaid_code}\n

        **Congratulations! You have completed the UAT flow.**
        """
    )
    return (mermaid_code, _message)


if __name__ == "__main__":
    app.run()
