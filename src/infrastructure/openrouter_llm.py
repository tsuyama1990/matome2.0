from src.infrastructure.llm_interface import ILLMProvider


class OpenRouterLLMProvider(ILLMProvider):
    async def generate_completion(self, prompt: str) -> str:
        """Call OpenRouter API to fetch completion.

        Args:
            prompt: Text to submit to open router.
        """
        msg = "OpenRouter SDK integration not fully implemented."
        raise NotImplementedError(msg)
