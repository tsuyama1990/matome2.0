with open("tests/unit/test_config.py") as f:
    content = f.read()

content = content.replace('    settings = AppSettings()\n    # Should not raise any exception', '    _ = AppSettings()\n    # Should not raise any exception')

with open("tests/unit/test_config.py", "w") as f:
    f.write(content)
