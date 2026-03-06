import pytest
from pydantic import ValidationError

from src.domain.models.config import AppDomainConfig, SubConfig
from src.domain.models.manifest import ProjectManifest


def test_project_manifest_valid() -> None:
    manifest = ProjectManifest(
        project_name="TestApp", version="1.0.0", description="A test application"
    )
    assert manifest.project_name == "TestApp"
    assert manifest.version == "1.0.0"
    assert manifest.description == "A test application"


def test_project_manifest_invalid_empty_name() -> None:
    with pytest.raises(ValidationError):
        ProjectManifest(project_name="", version="1.0.0")


def test_project_manifest_immutability() -> None:
    manifest = ProjectManifest(project_name="TestApp", version="1.0.0")
    with pytest.raises(ValidationError):
        manifest.project_name = "ChangedApp"


def test_project_manifest_update() -> None:
    manifest = ProjectManifest(project_name="TestApp", version="1.0.0")
    updated_manifest = manifest.update(version="1.1.0")
    assert updated_manifest.version == "1.1.0"
    assert manifest.version == "1.0.0"
    assert updated_manifest.project_name == "TestApp"


def test_app_domain_config_valid() -> None:
    config = AppDomainConfig(environment="dev", debug_mode=True)
    assert config.environment == "dev"
    assert config.debug_mode is True


def test_app_domain_config_forbid_extra() -> None:
    with pytest.raises(ValidationError):
        AppDomainConfig(environment="dev", extra_field="not_allowed")  # type: ignore[call-arg]


def test_sub_config_valid() -> None:
    sub = SubConfig(module_name="auth")
    assert sub.module_name == "auth"


def test_sub_config_invalid() -> None:
    with pytest.raises(ValidationError):
        SubConfig(module_name="")
