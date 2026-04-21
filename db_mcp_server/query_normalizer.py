"""
QueryNormalizer - 用户查询标准化
---------------------------------
流程：
  1. entity_normalizer 提取短语 + ChromaDB 向量检索候选
  2. LLM 一次调用：角色分类（8类）+ 实体纠错
  3. 防幻觉校验：entity/location 纠错结果必须在候选集内
"""

import json
import re

from langchain_core.messages import HumanMessage

from response import ROLE_DICT


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _build_prompt(query: str, candidates: dict, pre_classified: dict) -> str:
    role_lines = "\n".join(f"- {role}: {desc}" for role, desc in ROLE_DICT.items())

    if pre_classified:
        pre_lines = "\n".join(
            f"  {role}: {', '.join(words)}" for role, words in pre_classified.items()
        )
        pre_text = f"已识别的非实体词（仅供参考，角色分类以你的判断为准）：\n{pre_lines}"
    else:
        pre_text = ""

    if candidates:
        cand_lines = []
        allowed: list[str] = []
        for phrase, info in candidates.items():
            top1, top2 = info["top1"], info["top2"]
            cand_lines.append(
                f'  "{phrase}": top1={top1["group"]}「{top1["name"]}」({top1["score"]:.2f}), '
                f'top2={top2["group"]}「{top2["name"]}」({top2["score"]:.2f})'
            )
            for n in (top1["name"], top2["name"]):
                if n not in allowed:
                    allowed.append(n)
        whitelist = ", ".join(f'"{n}"' for n in allowed)
        cand_text = (
            "实体候选（向量检索结果，供纠错参考）：\n" + "\n".join(cand_lines) +
            f"\n\n⚠️  entity/location 的 \"normalized\" 值必须从以下列表中逐字复制，禁止自由改写：{whitelist}"
        )
    else:
        cand_text = "（无实体候选）"

    return f"""You are a US e-commerce data analyst assistant. Analyse the user query and do two things:
1. Correct spelling errors or abbreviations in entity/location words (use only the candidates below — do not invent names)
2. Classify query keywords by role

Role definitions:
{role_lines}

{pre_text}

{cand_text}

User query: "{query}"

Return JSON only, no extra text:
{{
  "normalized_query": "corrected full query (return as-is if no correction needed)",
  "roles": {{
    "metric":      [],
    "time":        [],
    "comparison":  [],
    "status":      [],
    "aggregation": [],
    "limit":       [],
    "entity":      [{{"original": "original word", "normalized": "canonical name", "group": "brand/category/sub_category"}}],
    "location":    [{{"original": "original word", "normalized": "canonical name", "group": "city/state"}}]
  }}
}}"""


def _validate_roles(roles: dict, candidates: dict) -> dict:
    """
    防幻觉校验：entity/location 的 normalized 必须在候选集内。
    若 LLM 自由生成了候选集之外的名称（如 NYC→"New York City"），
    fallback 到该短语的 top1 候选，而不是直接丢弃整条记录。
    """
    # canonical_map: lowercase → 数据库原始大小写（用于纠正 LLM 的大小写差异）
    canonical_map: dict[str, str] = {}
    # phrase_top1: 原始短语 lowercase → top1 canonical name（用于 fallback）
    phrase_top1: dict[str, str] = {}

    for phrase, info in candidates.items():
        t1, t2 = info["top1"]["name"], info["top2"]["name"]
        canonical_map[t1.lower()] = t1
        canonical_map[t2.lower()] = t2
        phrase_top1[phrase.lower()] = t1

    for role_key in ("entity", "location"):
        cleaned = []
        for item in roles.get(role_key, []):
            if not isinstance(item, dict):
                continue
            norm = item.get("normalized", "")
            orig = item.get("original", "").lower()

            if norm.lower() in canonical_map:
                # LLM 选对了，确保大小写与数据库一致
                item["normalized"] = canonical_map[norm.lower()]
                cleaned.append(item)
            elif orig in phrase_top1:
                # LLM 自由生成，回退到 top1 候选
                item["normalized"] = phrase_top1[orig]
                cleaned.append(item)
            # 两者都无法对应则丢弃（真正的幻觉）
        roles[role_key] = cleaned

    return roles


class QueryNormalizer:
    def __init__(self, llm, normalizer):
        self.llm        = llm
        self.normalizer = normalizer

    def run(self, question: str) -> dict:
        noun_phrases, time_phrases = self.normalizer._extract_phrases(question)
        result     = self.normalizer.get_candidates(noun_phrases, time_phrases)
        pre_cls    = result["pre_classified"]
        candidates = result["candidates"]

        prompt   = _build_prompt(question, candidates, pre_cls)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        try:
            parsed = json.loads(_clean_json(response.content))
        except Exception:
            return {"normalized_query": question, "roles": {k: [] for k in ROLE_DICT}}

        roles = _validate_roles(parsed.get("roles", {}), candidates)
        return {
            "normalized_query": parsed.get("normalized_query", question),
            "roles":            roles,
        }
