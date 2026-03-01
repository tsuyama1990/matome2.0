import zlib

from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator


class SemanticChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    document_id: UUID4
    content: str = Field(..., min_length=1, max_length=100_000)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metadata_keys(self) -> "SemanticChunk":
        for key in self.metadata:
            if not isinstance(key, str):
                msg = "Metadata keys must be strings"
                raise TypeError(msg)
        return self

    def compress_content(self) -> bytes:
        """Compress large text data for efficient storage."""
        return zlib.compress(self.content.encode("utf-8"))

    def decompress_content(self, compressed_data: bytes) -> str:
        """Decompress stored text data."""
        return zlib.decompress(compressed_data).decode("utf-8")
