import json
import re
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage

from core.interfaces import BaseReranker
from core.registry import register_reranker


@register_reranker("llm")
class LLMReranker(BaseReranker):
    def __init__(
        self,
        cfg,
        table_descriptions: Dict[str, str],
        llm=None,
    ):
        self.cfg = cfg
        self.table_descriptions = table_descriptions
        self.llm = llm

    def rerank(self, query: str, candidate_tables: List[str], top_k: int) -> List[str]:
        if not self.llm or not candidate_tables:
            return candidate_tables[:top_k]
        table_lines = "\n".join(
            f"- {t}: {self.table_descriptions.get(t, '')}" for t in candidate_tables
        )
        prompt = (
            f"Query: {query}\n\n"
            f"Candidate tables:\n{table_lines}\n\n"
            "Select the minimum set of tables needed to answer the question. "
            "Choose only necessary tables.\n"
            'Return table names as a JSON array, for example: ["Order_", "OrderItem"]\n'
            "Return JSON only, with no extra text."
        )
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            text = response.content.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            selected = json.loads(text)
            valid = [t for t in selected if t in candidate_tables]
            if valid:
                return valid[:top_k]
        except Exception:
            pass
        return candidate_tables[:top_k]
