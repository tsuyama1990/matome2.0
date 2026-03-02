
with open("pyproject.toml") as f:
    c = f.read()

# ignore ASYNC109 because timeout params are requested by instructions explicitly and ASYNC is just a lint suggestion.
c = c.replace('"ASYNC", ', '"ASYNC", ')
if '"ASYNC109"' not in c:
    c = c.replace('ignore = [\n', 'ignore = [\n    "ASYNC109",\n')

with open("pyproject.toml", "w") as f:
    f.write(c)


# Fix OpenRouterConfig typing
with open("src/infrastructure/llm.py") as f:
    c = f.read()
if "from pydantic import BaseModel, SecretStr, HttpUrl" not in c:
    c = c.replace("from pydantic import BaseModel, SecretStr", "from pydantic import BaseModel, SecretStr, HttpUrl")

c = c.replace("base_url: str", "base_url: HttpUrl | str")
c = c.replace('prompt: str,\n        system_prompt: str = "",', 'prompt: str,\n        system_prompt: str = "",\n        timeout: float = 30.0,')
c = c.replace('str(content)', 'str(content)')

# fix the method signature for stream_generate_text
c = c.replace('''    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> AsyncIterator[str]:''', '''    async def stream_generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        timeout: float = 30.0,
    ) -> AsyncIterator[str]:''')

with open("src/infrastructure/llm.py", "w") as f:
    f.write(c)

# tests fix URL | str error in test_llm.py
with open("tests/unit/infrastructure/test_llm.py") as f:
    c = f.read()

c = c.replace('request=httpx.Request("POST", test_config.openrouter_base_url)', 'request=httpx.Request("POST", str(test_config.openrouter_base_url))')

with open("tests/unit/infrastructure/test_llm.py", "w") as f:
    f.write(c)
