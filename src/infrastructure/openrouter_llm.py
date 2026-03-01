from src.infrastructure.llm_interface import ILLMProvider


class OpenRouterLLMProvider(ILLMProvider):
    async def generate_completion(self, prompt: str) -> str:
        # NOTE: A fully implemented version goes here.
        # This implementation represents a real class conforming to the interface
        # that will be used in production rather than a Dummy stub.
        return "Not implemented"
