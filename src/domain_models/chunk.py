import zlib

from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator


class DimensionalTags(BaseModel):
    model_config = ConfigDict(extra="forbid")
    time_axis: str | None = None
    logic_axis: str | None = None
    polarity_axis: str | None = None
    system_design_axis: str | None = None


class SemanticChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    document_id: UUID4
    content: str = Field(..., min_length=1, max_length=10_000)
    entities: list[str] = Field(default_factory=list)
    dimensional_tags: DimensionalTags = Field(default_factory=DimensionalTags)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content_safety(self) -> "SemanticChunk":
        """Ensures the content does not contain obvious malicious patterns or invalid encodings."""
        import re

        # Extended XSS validation
        unsafe_patterns = [
            r"<\s*script.*?>.*?</\s*script\s*>",
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"onload\s*=",
            r"onerror\s*=",
            r"<\s*iframe.*?>",
        ]

        for pattern in unsafe_patterns:
            if re.search(pattern, self.content, flags=re.IGNORECASE | re.DOTALL):
                msg = "Potentially malicious content detected"
                raise ValueError(msg)

        # Validate that the string is properly encodable
        try:
            self.content.encode("utf-8")
        except UnicodeEncodeError as e:
            msg = "Content contains invalid UTF-8 characters"
            raise ValueError(msg) from e

        for key in self.metadata:
            if not isinstance(key, str):
                msg = "Metadata keys must be strings"
                raise TypeError(msg)
        return self

    def compress_content(self) -> bytes:
        """Compress large text data for efficient storage."""
        return zlib.compress(self.content.encode("utf-8"), level=zlib.Z_BEST_COMPRESSION)

    def decompress_content(self, compressed_data: bytes) -> str:
        """Decompress stored text data."""
        try:
            return zlib.decompress(compressed_data).decode("utf-8")
        except zlib.error as e:
            msg = f"Failed to decompress content: {e}"
            raise ValueError(msg) from e
