from typing import Any
from uuid import uuid4

from src.domain.models.document import DocumentChunk


class TestDataFactory:
    """Factory for generating consistent test data to avoid magic strings and duplicated dictionaries."""

    @staticmethod
    def get_valid_api_key() -> str:
        return "a" * 35

    @staticmethod
    def get_invalid_api_key() -> str:
        return "short"

    @staticmethod
    def create_mock_chunk(
        embedding: list[float] | None = None, metadata: dict[str, Any] | None = None
    ) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=uuid4(),
            document_id=uuid4(),
            text="Test chunk data",
            embedding=embedding if embedding is not None else [0.1, 0.2, 0.3],
            metadata=metadata if metadata is not None else {},
        )

    @staticmethod
    def get_empty_list() -> list[Any]:
        return []

    @staticmethod
    def get_invalid_embedding() -> list[Any]:
        return ["not", "float"]
