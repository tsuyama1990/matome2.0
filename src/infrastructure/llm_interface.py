from abc import ABC, abstractmethod


class ILLMProvider(ABC):
    @abstractmethod
    async def generate_completion(self, prompt: str) -> str:
        pass
