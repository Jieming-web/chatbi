from typing import Callable, Dict

from .interfaces import BaseRetriever, BaseReranker, BaseLLM


_retrievers: Dict[str, Callable[..., BaseRetriever]] = {}
_rerankers: Dict[str, Callable[..., BaseReranker]] = {}
_llms: Dict[str, Callable[..., BaseLLM]] = {}


def register_retriever(name: str):
    def _wrap(cls):
        _retrievers[name] = cls
        return cls
    return _wrap


def register_reranker(name: str):
    def _wrap(cls):
        _rerankers[name] = cls
        return cls
    return _wrap


def create_retriever(cfg, **kwargs) -> BaseRetriever:
    if cfg.type not in _retrievers:
        raise ValueError(
            f"Unknown retriever type '{cfg.type}'. Registered: {list(_retrievers)}"
        )
    return _retrievers[cfg.type](cfg, **kwargs)


def create_reranker(cfg, **kwargs) -> BaseReranker:
    if cfg.type not in _rerankers:
        raise ValueError(
            f"Unknown reranker type '{cfg.type}'. Registered: {list(_rerankers)}"
        )
    return _rerankers[cfg.type](cfg, **kwargs)


def register_llm(name: str):
    def _wrap(cls):
        _llms[name] = cls
        return cls
    return _wrap


def create_llm(cfg=None, **kwargs) -> BaseLLM:
    llm_type = getattr(cfg, "type", "openai") if cfg else "openai"
    if llm_type not in _llms:
        raise ValueError(
            f"Unknown LLM type '{llm_type}'. Registered: {list(_llms)}"
        )
    return _llms[llm_type](cfg, **kwargs)
