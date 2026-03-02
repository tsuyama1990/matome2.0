import typing

from pydantic import BaseModel, ConfigDict, Field


class BaseManifestModel(BaseModel):
    """Base model for manifest schemas enforcing strict validation rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def update_model(self, **kwargs: typing.Any) -> typing.Self:
        """Creates an updated copy of the model, maintaining immutability."""
        update_dict: dict[str, typing.Any] = kwargs
        return self.model_copy(update=update_dict)


class ProjectManifest(BaseManifestModel):
    """Domain model representing the project manifest."""

    project_name: str = Field(..., min_length=1, description="Name of the project")
    version: str = Field(..., min_length=1, description="Version of the project")
    description: str = Field(default="", description="Description of the project")
