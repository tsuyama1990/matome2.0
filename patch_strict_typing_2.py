
with open("src/infrastructure/llm.py") as f:
    c = f.read()

c = c.replace('if not config.base_url.startswith', 'if not str(config.base_url).startswith')
c = c.replace('self.config.base_url, headers=headers', 'str(self.config.base_url), headers=headers')

with open("src/infrastructure/llm.py", "w") as f:
    f.write(c)
