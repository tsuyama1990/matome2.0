import httpx

from src.infrastructure.llm_interface import ILLMProvider


class OpenRouterLLMProvider(ILLMProvider):
    """Provides LLM completions leveraging the OpenRouter API with connection pooling."""

    def __init__(self, api_key: str) -> None:
        """Initialize the OpenRouter provider.

        Args:
            api_key: The OpenRouter API key.
        """
        self.api_key = api_key
        # Configure connection pooling: Max keepalive limits, explicit timeouts.
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        timeout = httpx.Timeout(10.0, read=30.0)
        self._client = httpx.AsyncClient(limits=limits, timeout=timeout)

    async def generate_completion(self, prompt: str) -> str:
        """Call OpenRouter API to fetch completion.

        Args:
            prompt: Text to submit to open router.
        """
        # A fully implemented version would send the payload here, e.g. via post(...)
        msg = "OpenRouter SDK integration not fully implemented."
        raise NotImplementedError(msg)

    async def close(self) -> None:
        """Close the underlying HTTPX client connection pool."""
        await self._client.aclose()
