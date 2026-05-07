import re
from typing import List, Sequence, Tuple

import numpy as np

from core.interfaces import BaseRetriever, RetrievalHit
from core.registry import register_retriever


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9_]+", text.lower())
    normalized = []
    for token in tokens:
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        normalized.append(token)
    return normalized


@register_retriever("dense")
class DenseRetriever(BaseRetriever):
    def __init__(
        self,
        cfg,
        field_descriptions: Sequence[Tuple[str, str, str]],
        embedding_model_name: str,
    ):
        self.cfg = cfg
        self.field_descriptions = list(field_descriptions)
        self.embedding_model_name = embedding_model_name
        self.model = None
        self._field_vectors = None
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(embedding_model_name)
        except Exception:
            self.model = None
        self._build_index()

    def _build_index(self) -> None:
        texts = [
            f"{table} {field} {desc}"
            for table, field, desc in self.field_descriptions
        ]
        if self.model:
            self._field_vectors = self.model.encode(
                texts,
                normalize_embeddings=True,
            )
            return

        vocab = sorted({token for text in texts for token in _tokenize(text)})
        self._vocab = {token: idx for idx, token in enumerate(vocab)}
        vectors = np.zeros((len(texts), len(vocab)), dtype=float)
        for row, text in enumerate(texts):
            for token in _tokenize(text):
                vectors[row, self._vocab[token]] += 1.0
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._field_vectors = vectors / norms

    def retrieve(self, query: str, top_k: int) -> List[RetrievalHit]:
        if self.model:
            q_vec = self.model.encode([query], normalize_embeddings=True)[0]
        else:
            q_vec = np.zeros(len(self._vocab), dtype=float)
            for token in _tokenize(query):
                idx = self._vocab.get(token)
                if idx is not None:
                    q_vec[idx] += 1.0
            norm = np.linalg.norm(q_vec)
            if norm:
                q_vec = q_vec / norm

        scores = np.dot(self._field_vectors, q_vec)
        ranked = sorted(enumerate(scores), key=lambda x: -float(x[1]))
        return [
            RetrievalHit(
                table=self.field_descriptions[idx][0],
                field=self.field_descriptions[idx][1],
                score=float(score),
                field_idx=idx,
            )
            for idx, score in ranked[:top_k]
        ]
