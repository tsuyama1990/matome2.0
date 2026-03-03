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
    # UAT-02 Texts
    "uat2_doc1": "Market trends indicate a shift towards renewable energy in Europe.",
    "uat2_doc2": "Competitor X is investing heavily in solar panel manufacturing.",
    "uat2_doc3": "New regulatory changes will impose strict tariffs on non-green imports by 2026.",
    "uat2_threat_summary": "New regulatory changes imposing strict tariffs on non-green imports by 2026.",
}

TUTORIAL_ENTITIES = {
    "chunk_1": {"entities": ["Executive", "Budget", "£5000"]},
    "chunk_2": {"entities": ["Manager", "Travel"]},
    "uat2_doc1": {"entities": ["Market Trends", "Renewable Energy", "Europe"]},
    "uat2_doc2": {"entities": ["Competitor X", "Solar Panels"]},
    "uat2_doc3": {"entities": ["Regulatory Changes", "Tariffs", "2026"]},
}


class LLMSimulatorService:
    """Configurable service to simulate LLM logic without external calls."""

    def __init__(self, required_keywords: list[str]) -> None:
        self.required_keywords = [k.lower() for k in required_keywords]

    async def check_understanding(self, answer: str, summary: str) -> bool:
        """Simulates LLM context evaluation by matching keywords."""
        answer_lower = answer.lower()
        return any(keyword in answer_lower for keyword in self.required_keywords)

    async def get_web_grounding_suggestion(self, node_title: str) -> str:
        """Simulates an AI Web-Grounding check flagging a specific node."""
        if "Regulatory" in node_title or "Threat" in node_title:
            return "Recent news indicates this law's enforcement has been delayed. Would you like to downgrade this threat?"
        return "No recent external updates found for this node."


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
    def create_mock_uat2_docs(uuid4_func: Callable[[], UUID]) -> tuple[MockDocumentChunk, MockDocumentChunk, MockDocumentChunk]:
        return (
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=uuid4_func(),
                text=TUTORIAL_TEXTS["uat2_doc1"],
                metadata=TUTORIAL_ENTITIES["uat2_doc1"],
            ),
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=uuid4_func(),
                text=TUTORIAL_TEXTS["uat2_doc2"],
                metadata=TUTORIAL_ENTITIES["uat2_doc2"],
            ),
            MockDocumentChunk(
                chunk_id=uuid4_func(),
                document_id=uuid4_func(),
                text=TUTORIAL_TEXTS["uat2_doc3"],
                metadata=TUTORIAL_ENTITIES["uat2_doc3"],
            ),
        )

    @staticmethod
    def create_mock_uat2_axis() -> MockAnalysisAxis:
        return MockAnalysisAxis(
            name="Opportunities vs Threats in the European Market",
            dimensions=["Opportunities", "Threats", "Neutral"]
        )

    @staticmethod
    def create_mock_uat2_clusters(
        uuid4_func: Callable[[], UUID], chunk_refs: list[UUID]
    ) -> dict[str, list[MockConceptNode]]:
        threat_node = MockConceptNode(
            node_id=uuid4_func(),
            title="Regulatory Tariff Threat",
            summary=TUTORIAL_TEXTS["uat2_threat_summary"],
            level=1,
            is_unlocked=True,
            chunk_references=chunk_refs
        )
        return {
            "Opportunities": [],
            "Threats": [threat_node],
            "Neutral": []
        }

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
