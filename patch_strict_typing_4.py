with open("tests/unit/test_config.py", "r") as f:
    c = f.read()

c = c.replace('def test_load_defaults_invalid_json(tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:', 'from pathlib import Path\ndef test_load_defaults_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:')

with open("tests/unit/test_config.py", "w") as f:
    f.write(c)
