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
            f"候选表：\n{table_lines}\n\n"
            f"请选出回答该问题所需的最少表集合，只选必要的表。\n"
            f"以 JSON 数组格式返回表名，例如：[\"Order_\", \"OrderItem\"]\n"
            f"只返回 JSON，不要其他内容。"
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
