import re

with open("src/core/config.py", "r") as f:
    c = f.read()

c = c.replace('def _load_defaults() -> dict[str, Any]:', 'def _load_defaults() -> dict[str, Any]:')
c = c.replace('return json.loads(default_path.read_text())', 'res = json.loads(default_path.read_text())\n            return dict(res) if isinstance(res, dict) else {}')

with open("src/core/config.py", "w") as f:
    f.write(c)

with open("tests/unit/test_domain_factory.py", "r") as f:
    c = f.read()
c = c.replace('def test_create_immutable():', 'def test_create_immutable() -> None:')
c = c.replace('def test_create_mutable():', 'def test_create_mutable() -> None:')
with open("tests/unit/test_domain_factory.py", "w") as f:
    f.write(c)

with open("tests/unit/test_config.py", "r") as f:
    c = f.read()
c = c.replace('def test_load_defaults_invalid_json(tmp_path, monkeypatch):', 'def test_load_defaults_invalid_json(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:')
c = c.replace('def test_load_defaults_file_not_found(monkeypatch):', 'def test_load_defaults_file_not_found(monkeypatch: pytest.MonkeyPatch) -> None:')

c = c.replace('m.setattr(src.core.config.Path, "exists", lambda self: True)', 'm.setattr("src.core.config.Path.exists", lambda self: True)')
c = c.replace('m.setattr(src.core.config.Path, "read_text", lambda self: "{invalid")', 'm.setattr("src.core.config.Path.read_text", lambda self: "{invalid")')
c = c.replace('m.setattr(src.core.config.Path, "exists", lambda self: False)', 'm.setattr("src.core.config.Path.exists", lambda self: False)')
with open("tests/unit/test_config.py", "w") as f:
    f.write(c)
