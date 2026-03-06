with open("tests/unit/infrastructure/test_factories.py") as f:
    c = f.read()

c = c.replace(
    "mock_config = MagicMock()",
    'mock_config = MagicMock()\n    mock_config.base_url = "https://openrouter.ai"',
)

with open("tests/unit/infrastructure/test_factories.py", "w") as f:
    f.write(c)
