from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    def invoke(self, messages: list) -> object:
        """Accept a list of LangChain-style messages, return a response with a .content str."""
