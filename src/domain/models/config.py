from pydantic import Field

from src.domain.models.base import BaseDomainModel


class AppDomainConfig(BaseDomainModel):
    """Domain model representing the application configuration settings."""

    environment: str = Field(..., description="Application environment (e.g., dev, prod)")
    debug_mode: bool = Field(..., description="Whether debug mode is enabled")


class SubConfig(BaseDomainModel):
    """Sub-configuration for specific settings."""

    module_name: str = Field(..., min_length=1)
