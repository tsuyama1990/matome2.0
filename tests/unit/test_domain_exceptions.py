from src.domain.exceptions import ConfigurationError, DocumentProcessingError


def test_configuration_error() -> None:
    error = ConfigurationError("test message", config_key="my_key")
    assert str(error) == "test message"
    assert error.config_key == "my_key"


def test_document_processing_error() -> None:
    error = DocumentProcessingError("test message", document_id="my_id")
    assert str(error) == "test message"
    assert error.document_id == "my_id"
