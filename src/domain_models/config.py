from pydantic import BaseModel, ConfigDict, Field

from src.domain_models.manifest import BaseManifestModel


class AppDomainConfig(BaseManifestModel):
    """Domain model representing the application configuration settings."""

    environment: str = Field(..., description="Application environment (e.g., dev, prod)")
    debug_mode: bool = Field(default=False, description="Whether debug mode is enabled")


class SubConfig(BaseModel):
    """Sub-configuration for specific settings."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    module_name: str = Field(..., min_length=1)
