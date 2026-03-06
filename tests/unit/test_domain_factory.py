from uuid import uuid4

from src.domain.models.document import DocumentChunk
from src.domain.models.factory import DomainModelFactory
from src.domain.models.node import ConceptNode


def test_create_immutable() -> None:
    chunk = DomainModelFactory.create_immutable(
        DocumentChunk, chunk_id=uuid4(), document_id=uuid4(), text="Test"
    )
    assert chunk.text == "Test"


def test_create_mutable() -> None:
    node = DomainModelFactory.create_mutable(
        ConceptNode, node_id=uuid4(), title="Test Node", summary="Test summary", level=0
    )
    assert node.title == "Test Node"
    node.unlock()
    assert node.is_unlocked is True
