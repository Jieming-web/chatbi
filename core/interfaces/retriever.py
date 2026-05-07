from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
"""
Different retrieval algorithms can implement their own logic, but they must follow
the shared `retrieve` interface and the common `RetrievalHit` output format.
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
