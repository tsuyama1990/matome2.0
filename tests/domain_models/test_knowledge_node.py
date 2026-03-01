from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.knowledge_node import KnowledgeNode


def test_knowledge_node_valid_creation() -> None:
    node_id = uuid4()
    node = KnowledgeNode(id=node_id, level=0, title="Root Node", dense_summary="This is a summary.")
    assert node.id == node_id
    assert node.level == 0
    assert node.title == "Root Node"


def test_knowledge_node_negative_level() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(id=uuid4(), level=-1, title="Test", dense_summary="Summary")


def test_knowledge_node_empty_title() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(id=uuid4(), level=1, title="", dense_summary="Summary")


def test_knowledge_node_malicious_title() -> None:
    with pytest.raises(ValidationError):
        KnowledgeNode(
            id=uuid4(), level=1, title="<script>alert()</script>", dense_summary="Summary"
        )


def test_knowledge_node_cyclic_child() -> None:
    node_id = uuid4()
    with pytest.raises(ValueError, match="Node cannot be its own child"):
        KnowledgeNode(
            id=node_id, level=1, title="Test", dense_summary="Summary", children=[node_id]
        )


def test_knowledge_node_validate_tree_acyclic() -> None:
    node_1 = KnowledgeNode(id=uuid4(), level=0, title="Root", dense_summary=".")
    node_2 = KnowledgeNode(id=uuid4(), level=1, title="Child 1", dense_summary=".")
    node_3 = KnowledgeNode(id=uuid4(), level=1, title="Child 2", dense_summary=".")

    node_1.children = [node_2.id, node_3.id]

    # Valid acyclic tree
    assert KnowledgeNode.validate_tree_acyclic([node_1, node_2, node_3]) is True

    # Introduce a cycle
    node_3.children = [node_1.id]
    assert KnowledgeNode.validate_tree_acyclic([node_1, node_2, node_3]) is False


def test_knowledge_node_validate_tree_missing_child() -> None:
    node_1 = KnowledgeNode(id=uuid4(), level=0, title="Root", dense_summary=".")
    node_1.children = [uuid4()]  # Unknown child ID
    assert KnowledgeNode.validate_tree_acyclic([node_1]) is False
