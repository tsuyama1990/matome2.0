from fastapi.testclient import TestClient

from src.core.exceptions import ResourceNotFoundError, ValidationDomainError
from src.main import app

client = TestClient(app)


def test_health_check_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_matome_app_error_handler() -> None:
    # We will temporarily add an endpoint to trigger the error for testing
    @app.get("/trigger-error")
    def trigger_error() -> None:
        msg = "test resource not found"
        raise ResourceNotFoundError(msg)

    response = client.get("/trigger-error")
    assert response.status_code == 400
    assert response.json() == {
        "error": "test resource not found",
        "type": "ResourceNotFoundError",
    }


def test_validation_domain_error_handler() -> None:
    @app.get("/trigger-validation-error")
    def trigger_validation_error() -> None:
        msg = "invalid data"
        raise ValidationDomainError(msg)

    response = client.get("/trigger-validation-error")
    assert response.status_code == 400
    assert response.json() == {
        "error": "invalid data",
        "type": "ValidationDomainError",
    }
