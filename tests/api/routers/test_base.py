from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_matome_app_error_handler() -> None:
    # Trigger an error manually to test the exception handler
    from src.core.exceptions import MatomeAppError

    @app.get("/trigger-error")
    async def trigger_error() -> None:
        msg = "Triggered MatomeAppError"
        raise MatomeAppError(msg)

    response = client.get("/trigger-error")
    assert response.status_code == 400
    assert response.json() == {"message": "Triggered MatomeAppError"}


def test_node_not_found_error_handler() -> None:
    from src.core.exceptions import NodeNotFoundError

    @app.get("/trigger-not-found")
    async def trigger_not_found() -> None:
        node_id = "123"
        raise NodeNotFoundError(node_id)

    response = client.get("/trigger-not-found")
    assert response.status_code == 404
    assert response.json() == {"message": "Knowledge node with ID 123 was not found."}


def test_invalid_chunk_state_error_handler() -> None:
    from src.core.exceptions import InvalidChunkStateError

    @app.get("/trigger-invalid-chunk")
    async def trigger_invalid_chunk() -> None:
        chunk_id = "456"
        raise InvalidChunkStateError(chunk_id, "foo")

    response = client.get("/trigger-invalid-chunk")
    assert response.status_code == 422
    assert response.json() == {"message": "Chunk 456 is in an invalid state: foo."}


def test_llm_provider_error_handler() -> None:
    from src.core.exceptions import LLMProviderError

    @app.get("/trigger-llm-error")
    async def trigger_llm_error() -> None:
        provider = "Anthropic"
        raise LLMProviderError(provider, "timeout")

    response = client.get("/trigger-llm-error")
    assert response.status_code == 502
    assert response.json() == {"message": "LLM Provider Anthropic encountered an error: timeout."}
