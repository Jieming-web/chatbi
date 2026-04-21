from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
"""
    不同检索算法可以自由实现,但必须遵守统一的接口(retrieve)和统一的输出格式(RetrievalHit)
"""

@dataclass
class RetrievalHit:
    table: str
    field: str
    score: float
    field_idx: int


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[RetrievalHit]:
        """Return hits over the schema field index, ordered by descending score."""
