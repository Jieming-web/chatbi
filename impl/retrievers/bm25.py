from typing import List, Sequence, Tuple

from rank_bm25 import BM25Okapi

from core.interfaces import BaseRetriever, RetrievalHit
from core.registry import register_retriever


@register_retriever("bm25")
class BM25Retriever(BaseRetriever):
    def __init__(
        self,
        cfg,
        field_descriptions: Sequence[Tuple[str, str, str]],
        **kwargs,
    ):
        self.cfg = cfg
        self.field_descriptions = list(field_descriptions)
        corpus = [desc.lower().split() for _, _, desc in self.field_descriptions]
        self.bm25 = BM25Okapi(corpus)

    def retrieve(self, query: str, top_k: int) -> List[RetrievalHit]:
        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])
        results = []
        for idx, score in ranked[:top_k]:
            table, field, _ = self.field_descriptions[idx]
            results.append(RetrievalHit(table=table, field=field, score=float(score), field_idx=idx))
        return results
