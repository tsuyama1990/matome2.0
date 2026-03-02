from pydantic import Field

from src.domain.models.base import BaseDomainModel


class ProjectManifest(BaseDomainModel):
    """Domain model representing the project manifest."""

    project_name: str = Field(..., min_length=1, description="Name of the project")
    version: str = Field(..., min_length=1, description="Version of the project")
    description: str = Field(default="", description="Description of the project")
