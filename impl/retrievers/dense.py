from typing import List, Sequence, Tuple

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.interfaces import BaseRetriever, RetrievalHit
from core.registry import register_retriever


COLLECTION_NAME = "schema_fields"


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
        self.model = SentenceTransformer(embedding_model_name)
        self.qdrant = QdrantClient(":memory:")
        self._build_index()

    def _build_index(self) -> None:
        texts = [desc for _, _, desc in self.field_descriptions]
        vectors = self.model.encode(texts, normalize_embeddings=True).tolist()
        dim = len(vectors[0]) if vectors else 384
        self.qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        points = [
            PointStruct(
                id=i,
                vector=vectors[i],
                payload={
                    "table": self.field_descriptions[i][0],
                    "field": self.field_descriptions[i][1],
                },
            )
            for i in range(len(self.field_descriptions))
        ]
        self.qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

    def retrieve(self, query: str, top_k: int) -> List[RetrievalHit]:
        q_vec = self.model.encode([query], normalize_embeddings=True)[0].tolist()
        points = self.qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            limit=top_k,
        ).points
        return [
            RetrievalHit(
                table=p.payload["table"],
                field=p.payload["field"],
                score=float(p.score),
                field_idx=int(p.id),
            )
            for p in points
        ]
