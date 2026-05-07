from abc import ABC, abstractmethod
from typing import List


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, candidate_tables: List[str], top_k: int) -> List[str]:
        """Select / reorder tables, returning up to top_k survivors."""
