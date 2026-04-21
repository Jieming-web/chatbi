from typing import Dict, List

from sentence_transformers import CrossEncoder as _CrossEncoder

from core.interfaces import BaseReranker
from core.registry import register_reranker


_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@register_reranker("cross_encoder")
class CrossEncoderReranker(BaseReranker):
    def __init__(
        self,
        cfg,
        table_descriptions: Dict[str, str],
        **kwargs,
    ):
        self.cfg = cfg
        self.table_descriptions = table_descriptions
        model_name = cfg.model_name or _DEFAULT_MODEL
        self.model = _CrossEncoder(model_name)

    def rerank(self, query: str, candidate_tables: List[str], top_k: int) -> List[str]:
        if not candidate_tables:
            return []
        pairs = [(query, self.table_descriptions.get(t, t)) for t in candidate_tables]
        scores = self.model.predict(pairs)
        ranked = sorted(
            zip(candidate_tables, scores), key=lambda x: -x[1]
        )
        return [t for t, _ in ranked[:top_k]]
