import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

import marimo

from tutorials.tutorial_config import LLMSimulatorService, TutorialDataFactory
from tutorials.tutorial_domain import (
    MockAnalysisAxis,
    MockConceptNode,
    MockDocumentChunk,
    MockPivotBoard,
)

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def display_welcome_message(mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        """
        # matome - User Acceptance Test & Tutorial

        Welcome to matome! This interactive notebook will guide you through the "Aha! Moment" for a Product Manager (Scenario UAT-01).
        You will see how matome takes a dense business manual, extracts semantic meaning into a RAPTOR-like tree, engages the user via SQ3R (answering a question to unlock knowledge), and finally dynamically restructures the information into a new format (Pivot KJ).
        """
    )
    return (_message,)


@app.cell
def import_dependencies() -> tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]:

    import marimo as mo

    from tutorials.tutorial_config import LLMSimulatorService, TutorialDataFactory
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
    llm_simulator_service = LLMSimulatorService

    return (
        mock_analysis_axis,
        mock_concept_node,
        mock_document_chunk,
        Path,
        mock_pivot_board,
        tutorial_data_factory,
        llm_simulator_service,
        asyncio,
        mo,
        uuid4,
    )


@app.cell
def display_step_one(mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        """
        ## Step 1: Ingestion & RAPTOR Tree Generation

        Imagine you upload a legacy system manual (`testfiles/test_text.txt`). Instead of a wall of text, matome's ingestion pipeline (simulated here) creates **Document Chunks** and builds a hierarchical **Concept Node** tree.
        """
    )
    return (_message,)


@app.cell
def generate_mock_tree(
    mock_concept_node: Any,
    mock_document_chunk: Any,
    tutorial_data_factory: type[TutorialDataFactory],
    uuid4: Callable[[], Any],
) -> tuple[list[MockDocumentChunk], Any, MockConceptNode, MockConceptNode]:
    doc_id = uuid4()
    chunks = tutorial_data_factory.create_mock_chunks(doc_id, uuid4)
    root_node = tutorial_data_factory.create_mock_root_node(uuid4)
    locked_node = tutorial_data_factory.create_mock_locked_node(
        root_node.node_id, chunks[0].chunk_id, uuid4
    )
    return chunks, doc_id, locked_node, root_node


@app.cell
def display_step_two(locked_node: MockConceptNode, mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        f"""
        ## Step 2: Interactive Learning (SQ3R)

        You want to read the **{locked_node.title}** node. But it's currently locked to prevent passive reading.

        **AI Tutor asks:** "What condition do you think requires executive approval instead of just the manager's?"
        """
    )
    return (_message,)


@app.cell
def get_user_answer(mo: Any) -> tuple[marimo.ui.text]:
    user_answer = mo.ui.text(
        label="Your answer",
        placeholder="Type your answer here...",
        value="",
    )
    return (user_answer,)


@app.cell
async def evaluate_answer(
    locked_node: MockConceptNode,
    mo: Any,
    user_answer: marimo.ui.text,
    llm_simulator_service: type[LLMSimulatorService],
    asyncio: Any,
) -> tuple[marimo.Html]:
    sanitized_answer = str(user_answer.value).replace("<", "&lt;").replace(">", "&gt;").strip()

    if not sanitized_answer:
        eval_result = mo.md("*Awaiting your answer...*")
    else:
        simulator = llm_simulator_service(required_keywords=["5000", "executive"])
        try:
            is_correct = await asyncio.wait_for(
                simulator.check_understanding(sanitized_answer, locked_node.summary), timeout=2.0
            )
            if is_correct:
                locked_node.unlock()
                eval_result = mo.md(
                    f"**Success!** Node unlocked. \n\n**High-Density Summary (CoD):**\n> {locked_node.summary}"
                )
            else:
                eval_result = mo.md("**Not quite.** Try thinking about budget thresholds!")
        except asyncio.TimeoutError:
            eval_result = mo.md("**Error:** LLM Simulation timed out. Please try again.")
        except Exception as e:
            eval_result = mo.md(f"**Error:** An unexpected error occurred: {e}")

    return (eval_result,)


@app.cell
def display_step_three(locked_node: MockConceptNode, mo: Any) -> tuple[marimo.Html]:
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
    tutorial_data_factory: type[TutorialDataFactory],
    doc_id: Any,
    locked_node: MockConceptNode,
    mo: Any,
    uuid4: Callable[[], Any],
) -> tuple[MockAnalysisAxis, MockPivotBoard, dict[str, list[MockConceptNode]]]:

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
def display_step_four(
    tutorial_data_factory: type[TutorialDataFactory], board: MockPivotBoard, mo: Any
) -> tuple[str, marimo.Html]:
    try:
        mermaid_code = tutorial_data_factory.generate_mermaid_diagram(board.clusters)
    except Exception as e:
        mermaid_code = f"Error generating diagram: {e}"

    try:
        title = board.clusters["Executive"][0].title
    except (KeyError, IndexError):
        title = "Unknown Task"

    _message = mo.md(
        f"""
        ## Step 4: Export to Requirements Document

        Based on the new {board.axis.name} clusters, matome generates the To-Be system workflow!

        ### Extracted Workflow
        - **Executive:** Handles {title}

        ### Mermaid Diagram
        \n{mermaid_code}\n

        **Congratulations! You have completed UAT-01.**
        """
    )
    return (mermaid_code, _message)


@app.cell
def display_uat2_step_one(mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        """
        ---
        # Scenario UAT-02: Multi-Dimensional Analysis for a Consultant (Advanced)

        ## Step 1: Ingestion

        As a consultant, you need to synthesize multiple reports. You upload three separate documents detailing:
        1. Market Trends
        2. Competitor Analysis
        3. Regulatory Changes
        """
    )
    return (_message,)


@app.cell
def ingest_uat2_docs(
    tutorial_data_factory: type[TutorialDataFactory],
    uuid4: Callable[[], Any],
    mo: Any
) -> tuple[tuple[MockDocumentChunk, MockDocumentChunk, MockDocumentChunk], marimo.Html]:
    docs = tutorial_data_factory.create_mock_uat2_docs(uuid4)
    _message = mo.md(f"**Success:** Ingested {len(docs)} documents.")
    return docs, _message


@app.cell
def display_uat2_step_two(mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        """
        ## Step 2: Exploration

        You navigate the massive combined knowledge tree using the Semantic Zoom UI.
        You never lose your place thanks to the minimap and breadcrumbs:

        *Breadcrumbs: Home > Europe > Energy Sector > **Regulatory Constraints***
        """
    )
    return (_message,)


@app.cell
def display_uat2_step_three(mo: Any) -> tuple[marimo.Html]:
    _message = mo.md(
        """
        ## Step 3: Restructuring (Pivot KJ)

        You define a custom axis: "Opportunities vs Threats in the European Market."
        The system pulls data across all three documents and physically reorganises the nodes into a custom matrix on the canvas.
        """
    )
    return (_message,)


@app.cell
def create_uat2_pivot_board(
    tutorial_data_factory: type[TutorialDataFactory],
    docs: tuple[MockDocumentChunk, MockDocumentChunk, MockDocumentChunk],
    uuid4: Callable[[], Any],
    mock_pivot_board: Any,
    mo: Any
) -> tuple[MockPivotBoard, MockConceptNode, marimo.Html]:
    uat2_axis = tutorial_data_factory.create_mock_uat2_axis()
    chunk_refs = [d.chunk_id for d in docs]
    uat2_clusters = tutorial_data_factory.create_mock_uat2_clusters(uuid4, chunk_refs)

    uat2_board = mock_pivot_board(
        board_id=uuid4(),
        original_document_id=docs[0].document_id, # Simplified for mock
        axis=uat2_axis,
        clusters=uat2_clusters,
    )

    threat_node = uat2_clusters["Threats"][0]

    _message = mo.md(
        f"**Created Pivot Board!** Axis: {uat2_board.axis.name}\n\n"
        f"Identified Threat Node: **{threat_node.title}**"
    )
    return uat2_board, threat_node, _message


@app.cell
async def display_uat2_step_four(
    threat_node: MockConceptNode,
    llm_simulator_service: type[LLMSimulatorService],
    mo: Any
) -> tuple[marimo.Html]:
    uat2_simulator = llm_simulator_service(required_keywords=[])
    suggestion = await uat2_simulator.get_web_grounding_suggestion(threat_node.title)

    _message = mo.md(
        f"""
        ## Step 4: Web-Grounding

        The AI flags the "{threat_node.title}" node regarding a specific law and suggests:

        > "{suggestion}"

        Would you like to accept this suggestion and downgrade the threat to Neutral?
        """
    )
    return (_message,)


@app.cell
def uat2_accept_suggestion(
    mo: Any,
    uat2_board: MockPivotBoard,
    threat_node: MockConceptNode
) -> tuple[marimo.ui.button]:
    accept_btn = mo.ui.button(label="Accept Suggestion & Downgrade", on_change=lambda _: True)
    return (accept_btn,)


@app.cell
def handle_uat2_downgrade(
    accept_btn: marimo.ui.button,
    uat2_board: MockPivotBoard,
    threat_node: MockConceptNode,
    mo: Any
) -> tuple[marimo.Html]:
    if accept_btn.value:
        # State mutation for the mock UAT
        if threat_node in uat2_board.clusters["Threats"]:
            uat2_board.clusters["Threats"].remove(threat_node)
            uat2_board.clusters["Neutral"].append(threat_node)

        _message = mo.md(
            f"**Success!** Node '{threat_node.title}' has been moved to the **Neutral** cluster.\n\n"
            "**Congratulations! You have completed UAT-02.**"
        )
    else:
        _message = mo.md("*Awaiting your decision...*")

    return (_message,)


if __name__ == "__main__":
    app.run()
