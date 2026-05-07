import re
from typing import Dict, List

from core.interfaces import BaseReranker
from core.registry import register_reranker


_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    normalized = set()
    for token in tokens:
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        normalized.add(token)
    return normalized


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
        self.model = None
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(model_name)
        except Exception:
            self.model = None

    def rerank(self, query: str, candidate_tables: List[str], top_k: int) -> List[str]:
        if not candidate_tables:
            return []
        if not self.model:
            query_tokens = _tokenize(query)
            ranked = sorted(
                candidate_tables,
                key=lambda table: -len(
                    query_tokens & _tokenize(self.table_descriptions.get(table, table))
                ),
            )
            return ranked[:top_k]
        pairs = [(query, self.table_descriptions.get(t, t)) for t in candidate_tables]
        scores = self.model.predict(pairs)
        ranked = sorted(
            zip(candidate_tables, scores), key=lambda x: -x[1]
        )
        return [t for t, _ in ranked[:top_k]]
