from collections.abc import Callable
from uuid import UUID

from tutorials.tutorial_domain import (
    MockAnalysisAxis,
    MockConceptNode,
    MockDocumentChunk,
)

TUTORIAL_TEXTS = {
    "chunk_1": "Executive approval is needed if the budget exceeds £5000.",
    "chunk_2": "Manager approval is required for all travel expenses.",
    "root_summary": "High-level overview of company approval processes.",
    "locked_summary": "Detailed breakdown of budget thresholds requiring executive sign-off.",
}

TUTORIAL_ENTITIES = {
    "chunk_1": {"entities": ["Executive", "Budget", "£5000"]},
    "chunk_2": {"entities": ["Manager", "Travel"]},
}


class LLMSimulatorService:
    """Configurable service to simulate LLM logic without external calls."""

    def __init__(self, required_keywords: list[str]) -> None:
        self.required_keywords = [k.lower() for k in required_keywords]

    async def check_understanding(self, answer: str, summary: str) -> bool:
        """Simulates LLM context evaluation by matching keywords."""
        answer_lower = answer.lower()
        return any(keyword in answer_lower for keyword in self.required_keywords)


class TutorialDataFactory:
    """Provides mock data and templates for the UAT tutorial."""

    @staticmethod
    def create_mock_chunks(doc_id: UUID, uuid4_func: Callable[[], UUID]) -> list[MockDocumentChunk]:
        return [
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=doc_id,
                text=TUTORIAL_TEXTS["chunk_1"],
                metadata=TUTORIAL_ENTITIES["chunk_1"],
            ),
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=doc_id,
                text=TUTORIAL_TEXTS["chunk_2"],
                metadata=TUTORIAL_ENTITIES["chunk_2"],
            ),
        ]

    @staticmethod
    def create_mock_root_node(uuid4_func: Callable[[], UUID]) -> MockConceptNode:
        return MockConceptNode(
            node_id=uuid4_func(),
            title="Approval Processes",
            summary=TUTORIAL_TEXTS["root_summary"],
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
            summary=TUTORIAL_TEXTS["locked_summary"],
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
        """Dynamically generates a mermaid diagram based on clusters."""
        diagram = ["```mermaid", "sequenceDiagram"]

        # Declare actors dynamically
        actors = list(clusters.keys())
        for actor in actors:
            diagram.append(f"    actor {actor}")
        diagram.append("")

        # Generate flow logic based on actual nodes present in clusters
        for actor, nodes in clusters.items():
            for node in nodes:
                diagram.append(f"    Employee->>{actor}: Submit request for {node.title}")
                diagram.append(f"    {actor}-->>Employee: Approve")
                diagram.append("")

        # Append a generic edge case if specific conditions are missing to ensure validity
        if not any(nodes for nodes in clusters.values()):
            diagram.append("    Employee->>Manager: Submit generic task")

        diagram.append("```")
        return "\n".join(diagram)
