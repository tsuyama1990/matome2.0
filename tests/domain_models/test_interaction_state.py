from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain_models.interaction_state import InteractionState


def test_interaction_state_valid_creation() -> None:
    user_id = uuid4()
    doc_id = uuid4()
    state = InteractionState(user_id=user_id, document_id=doc_id)
    assert state.user_id == user_id
    assert state.document_id == doc_id
    assert state.locked_nodes == []
    assert state.reviewed_nodes == []
    assert state.active_question is None
    assert state.next_review_date is None


def test_interaction_state_with_data() -> None:
    user_id = uuid4()
    doc_id = uuid4()
    node_id = uuid4()
    now = datetime.now(UTC)
    state = InteractionState(
        user_id=user_id,
        document_id=doc_id,
        locked_nodes=[node_id],
        reviewed_nodes=[node_id],
        active_question="Test?",
        next_review_date=now,
    )
    assert state.locked_nodes == [node_id]
    assert state.reviewed_nodes == [node_id]
    assert state.active_question == "Test?"
    assert state.next_review_date == now


def test_interaction_state_extra_fields() -> None:
    with pytest.raises(ValidationError):
        InteractionState(user_id=uuid4(), document_id=uuid4(), extra="invalid")  # type: ignore[call-arg]
