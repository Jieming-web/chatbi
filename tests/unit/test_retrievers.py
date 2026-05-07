import pytest

from core.registry import create_retriever
from core.interfaces import RetrievalHit
from config import settings


class _Cfg:
    def __init__(self, type_):
        self.type = type_
        self.top_k = 10
        self.final_tables = 5


@pytest.mark.parametrize("retriever_type", ["dense", "bm25", "hybrid"])
def test_retriever_returns_hits(retriever_type, field_descriptions):
    cfg = _Cfg(retriever_type)
    kwargs = {"field_descriptions": field_descriptions}
    if retriever_type in ("dense", "hybrid"):
        kwargs["embedding_model_name"] = settings.embedding.model_name
    retriever = create_retriever(cfg, **kwargs)
    hits = retriever.retrieve("Samsung phone sales last month", top_k=10)
    assert len(hits) > 0
    assert all(isinstance(h, RetrievalHit) for h in hits)


@pytest.mark.parametrize("retriever_type", ["dense", "bm25", "hybrid"])
def test_retriever_includes_relevant_table(retriever_type, field_descriptions):
    cfg = _Cfg(retriever_type)
    kwargs = {"field_descriptions": field_descriptions}
    if retriever_type in ("dense", "hybrid"):
        kwargs["embedding_model_name"] = settings.embedding.model_name
    retriever = create_retriever(cfg, **kwargs)
    hits = retriever.retrieve("Samsung phone sales last month", top_k=40)
    tables = {h.table for h in hits}
    assert "Product" in tables
    assert "OrderItem" in tables


def test_unknown_retriever_type():
    class _Bad:
        type = "nonexistent"
    from core.registry import create_retriever
    with pytest.raises(ValueError, match="Unknown retriever type"):
        create_retriever(_Bad())
