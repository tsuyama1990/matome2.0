from abc import ABC, abstractmethod


class ILLMProvider(ABC):
    """
    Abstract interface for LLM operations.
    """

    @abstractmethod
    async def generate_completion(self, prompt: str) -> str:
        """
        Generates a text completion for a given prompt.
        """
