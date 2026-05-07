import pytest

from core.registry import create_reranker


class _Cfg:
    def __init__(self, type_, model_name=None):
        self.type = type_
        self.top_k = 3
        self.model_name = model_name


CANDIDATES = ["Order_", "OrderItem", "Product", "Customer", "GlobalOrder"]


def test_cross_encoder_reranker_returns_subset(table_descriptions):
    cfg = _Cfg("cross_encoder")
    reranker = create_reranker(cfg, table_descriptions=table_descriptions)
    result = reranker.rerank("Samsung phone sales last month", CANDIDATES, top_k=3)
    assert len(result) <= 3
    assert all(t in CANDIDATES for t in result)


def test_cross_encoder_reranker_empty_input(table_descriptions):
    cfg = _Cfg("cross_encoder")
    reranker = create_reranker(cfg, table_descriptions=table_descriptions)
    result = reranker.rerank("anything", [], top_k=3)
    assert result == []


def test_llm_reranker_passthrough_without_llm(table_descriptions):
    cfg = _Cfg("llm")
    reranker = create_reranker(cfg, table_descriptions=table_descriptions, llm=None)
    result = reranker.rerank("any query", CANDIDATES, top_k=3)
    assert result == CANDIDATES[:3]


def test_unknown_reranker_type():
    class _Bad:
        type = "bogus"
    from core.registry import create_reranker
    with pytest.raises(ValueError, match="Unknown reranker type"):
        create_reranker(_Bad())
