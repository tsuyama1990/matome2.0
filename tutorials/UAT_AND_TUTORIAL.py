import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def __(mo):
    mo.md(
        """
        # matome - User Acceptance Test & Tutorial

        Welcome to matome! This interactive notebook will guide you through the "Aha! Moment" for a Product Manager (Scenario UAT-01).
        You will see how matome takes a dense business manual, extracts semantic meaning into a RAPTOR-like tree, engages the user via SQ3R (answering a question to unlock knowledge), and finally dynamically restructures the information into a new format (Pivot KJ).
        """
    )


@app.cell
def __():
    import asyncio
    from pathlib import Path
    from uuid import uuid4

    import marimo as mo

    from src.domain.models.document import DocumentChunk
    from src.domain.models.node import AnalysisAxis, ConceptNode, PivotBoard

    return AnalysisAxis, ConceptNode, DocumentChunk, Path, PivotBoard, asyncio, mo, uuid4


@app.cell
def __(mo):
    mo.md(
        """
        ## Step 1: Ingestion & RAPTOR Tree Generation

        Imagine you upload a legacy system manual (`testfiles/test_text.txt`). Instead of a wall of text, matome's ingestion pipeline (simulated here) creates **Document Chunks** and builds a hierarchical **Concept Node** tree.
        """
    )


@app.cell
def __(ConceptNode, DocumentChunk, uuid4):
    doc_id = uuid4()

    # 1. Simulate extracted semantic chunks from the text
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

    # 2. Simulate RAPTOR tree generation bottom-up clustering
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

    dict(
        root_node_title=root_node.title,
        locked_node_title=locked_node.title,
        is_unlocked=locked_node.is_unlocked,
    )
    return chunks, doc_id, locked_node, root_node


@app.cell
def __(locked_node, mo):
    mo.md(
        f"""
        ## Step 2: Interactive Learning (SQ3R)

        You want to read the **{locked_node.title}** node. But it's currently locked to prevent passive reading.

        **AI Tutor asks:** "What condition do you think requires executive approval instead of just the manager's?"
        """
    )


@app.cell
def __(mo):
    user_answer = mo.ui.text(
        label="Your answer",
        placeholder="Type your answer here...",
        value="Executive approval is needed if the budget exceeds 5000.",
    )
    user_answer
    return (user_answer,)


@app.cell
def __(locked_node, mo, user_answer, asyncio):
    async def simulate_llm_check(answer: str, summary: str) -> bool:
        """Simulates LLM context evaluation."""
        return bool("5000" in answer or "executive" in answer.lower())

    async def evaluate():
        if not user_answer.value:
            return mo.md("*Awaiting your answer...*")

        is_correct = await simulate_llm_check(user_answer.value, locked_node.summary)

        if is_correct:
            locked_node.unlock()
            return mo.md(
                f"**Success!** Node unlocked. \n\n**High-Density Summary (CoD):**\n> {locked_node.summary}"
            )
        return mo.md("**Not quite.** Try thinking about budget thresholds!")

    eval_result = asyncio.run(evaluate())
    return eval_result, evaluate, simulate_llm_check


@app.cell
def __(locked_node, mo):
    mo.md(
        f"""
        **Node Status Check:** Is the node unlocked? **{locked_node.is_unlocked}**

        ## Step 3: Transformation (Pivot KJ)

        Now that you've understood the manual, you want to redesign the system. Let's pivot the knowledge away from "Chapters" and into a workflow based on "Actors".
        """
    )


@app.cell
def __(AnalysisAxis, PivotBoard, doc_id, locked_node, mo, uuid4):
    axis = AnalysisAxis(
        name="Actor vs. State Transition", dimensions=["Executive", "Manager", "Employee"]
    )

    # Simulate LLM clustering
    clusters = {"Executive": [locked_node], "Manager": [], "Employee": []}

    board = PivotBoard(
        board_id=uuid4(),
        original_document_id=doc_id,
        axis=axis,
        clusters=clusters,
    )

    mo.md(f"**Created Pivot Board!** Axis: {board.axis.name}")
    return axis, board, clusters


@app.cell
def __(board, mo):
    mermaid_code = """
    ```mermaid
    sequenceDiagram
        actor Employee
        actor Manager
        actor Executive

        Employee->>Manager: Submit Travel Expense
        Manager-->>Employee: Approve

        Employee->>Manager: Submit Budget (£6000)
        Manager->>Executive: Forward for Special Approval
        Executive-->>Manager: Approve
        Manager-->>Employee: Approve
    ```
    """

    mo.md(
        f"""
        ## Step 4: Export to Requirements Document

        Based on the new {board.axis.name} clusters, matome generates the To-Be system workflow!

        ### Extracted Workflow
        - **Executive:** Handles {board.clusters["Executive"][0].title}

        ### Mermaid Diagram
        {mermaid_code}

        **Congratulations! You have completed the UAT flow.**
        """
    )
    return (mermaid_code,)


if __name__ == "__main__":
    app.run()
