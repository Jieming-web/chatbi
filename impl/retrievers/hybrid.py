"""
Hybrid retriever: Dense + BM25 fused via Reciprocal Rank Fusion (RRF, k=60).
"""
from typing import Dict, List, Sequence, Tuple

from core.interfaces import BaseRetriever, RetrievalHit
from core.registry import register_retriever
from .dense import DenseRetriever
from .bm25 import BM25Retriever


_RRF_K = 60


def _rrf_score(rank: int) -> float:
    return 1.0 / (_RRF_K + rank + 1)


@register_retriever("hybrid")
class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        cfg,
        field_descriptions: Sequence[Tuple[str, str, str]],
        embedding_model_name: str,
        **kwargs,
    ):
        self.cfg = cfg
        self.field_descriptions = list(field_descriptions)
        self.dense = DenseRetriever(cfg, field_descriptions, embedding_model_name)
        self.bm25 = BM25Retriever(cfg, field_descriptions)

    def retrieve(self, query: str, top_k: int) -> List[RetrievalHit]:
        dense_hits = self.dense.retrieve(query, top_k=top_k)
        bm25_hits = self.bm25.retrieve(query, top_k=top_k)

        scores: Dict[int, float] = {}
        for rank, hit in enumerate(dense_hits):
            scores[hit.field_idx] = scores.get(hit.field_idx, 0.0) + _rrf_score(rank)
        for rank, hit in enumerate(bm25_hits):
            scores[hit.field_idx] = scores.get(hit.field_idx, 0.0) + _rrf_score(rank)

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        results = []
        for field_idx, score in ranked[:top_k]:
            table, field, _ = self.field_descriptions[field_idx]
            results.append(RetrievalHit(table=table, field=field, score=score, field_idx=field_idx))
        return results
