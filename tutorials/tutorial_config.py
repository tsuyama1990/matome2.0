from collections.abc import Callable
from uuid import UUID

from tutorials.tutorial_domain import (
    MockAnalysisAxis,
    MockConceptNode,
    MockDocumentChunk,
)


class TutorialDataFactory:
    """Provides mock data and templates for the UAT tutorial to avoid hardcoding in the notebook."""

    @staticmethod
    def create_mock_chunks(doc_id: UUID, uuid4_func: Callable[[], UUID]) -> list[MockDocumentChunk]:
        return [
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=doc_id,
                text="Executive approval is needed if the budget exceeds £5000.",
                metadata={"entities": ["Executive", "Budget", "£5000"]},
            ),
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=doc_id,
                text="Manager approval is required for all travel expenses.",
                metadata={"entities": ["Manager", "Travel"]},
            ),
        ]

    @staticmethod
    def create_mock_root_node(uuid4_func: Callable[[], UUID]) -> MockConceptNode:
        return MockConceptNode(
            node_id=uuid4_func(),
            title="Approval Processes",
            summary="High-level overview of company approval processes.",
            level=0,
            is_unlocked=True,
        )

    @staticmethod
    def create_mock_locked_node(
        parent_id: UUID, chunk_id: UUID, uuid4_func: Callable[[], UUID]
    ) -> MockConceptNode:
        return MockConceptNode(
            node_id=uuid4_func(),
            parent_id=parent_id,
            title="Special Approval Processes",
            summary="Detailed breakdown of budget thresholds requiring executive sign-off.",
            level=1,
            is_unlocked=False,
            chunk_references=[chunk_id],
        )

    @staticmethod
    def create_mock_axis() -> MockAnalysisAxis:
        return MockAnalysisAxis(
            name="Actor vs. State Transition", dimensions=["Executive", "Manager", "Employee"]
        )

    @staticmethod
    def create_mock_clusters(locked_node: MockConceptNode) -> dict[str, list[MockConceptNode]]:
        return {"Executive": [locked_node], "Manager": [], "Employee": []}

    @staticmethod
    def generate_mermaid_diagram(clusters: dict[str, list[MockConceptNode]]) -> str:
        """Dynamically generates a mermaid diagram (mock logic for tutorial)."""
        diagram = "```mermaid\nsequenceDiagram\n"
        diagram += "    actor Employee\n"
        diagram += "    actor Manager\n"
        diagram += "    actor Executive\n\n"
        diagram += "    Employee->>Manager: Submit Travel Expense\n"
        diagram += "    Manager-->>Employee: Approve\n\n"
        diagram += "    Employee->>Manager: Submit Budget (£6000)\n"
        diagram += "    Manager->>Executive: Forward for Special Approval\n"
        diagram += "    Executive-->>Manager: Approve\n"
        diagram += "    Manager-->>Employee: Approve\n"
        diagram += "```"
        return diagram
