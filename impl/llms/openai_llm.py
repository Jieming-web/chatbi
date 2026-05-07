import os

from langchain_openai import ChatOpenAI

from config import settings
from core.interfaces import BaseLLM
from core.registry import register_llm


@register_llm("openai")
class OpenAILLM(BaseLLM):
    def __init__(self, cfg=None):
        cfg = cfg or settings.llm
        self._client = ChatOpenAI(
            model=cfg.model,
            temperature=cfg.temperature,
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def invoke(self, messages: list) -> object:
        return self._client.invoke(messages)
