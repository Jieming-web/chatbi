"""
Ollama LLM shell — placeholder for future Qwen2.5 QLoRA deployment.
Requires: pip install langchain-ollama
"""
from core.interfaces import BaseLLM
from core.registry import register_llm


@register_llm("ollama")
class OllamaLLM(BaseLLM):
    def __init__(self, cfg=None):
        try:
            from langchain_ollama import ChatOllama
            model = getattr(cfg, "model", "qwen2.5:3b") if cfg else "qwen2.5:3b"
            self._client = ChatOllama(model=model)
        except ImportError:
            raise ImportError(
                "langchain-ollama is not installed. "
                "Run: pip install langchain-ollama"
            )

    def invoke(self, messages: list) -> object:
        return self._client.invoke(messages)
