"""
QueryNormalizer - user query normalization
------------------------------------------
Flow:
  1. entity_normalizer extracts phrases and retrieves candidates with ChromaDB
  2. A single LLM call handles role classification (8 categories) and entity correction
  3. Anti-hallucination validation ensures entity/location corrections stay within candidates
"""

import json
import re

try:
    from langchain_core.messages import HumanMessage
except Exception:
    HumanMessage = None

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
        pre_text = (
            "Pre-identified non-entity terms (reference only; make your own role judgment):\n"
            f"{pre_lines}"
        )
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
            "Entity candidates (vector retrieval results for correction reference):\n"
            + "\n".join(cand_lines)
            + f'\n\nWARNING: the "normalized" value for entity/location must be copied verbatim '
              f"from this list only. Do not rewrite it freely: {whitelist}"
        )
    else:
        cand_text = "(no entity candidates)"

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
    Anti-hallucination validation: entity/location normalized values must stay within
    the candidate set. If the LLM invents a name outside the candidates
    (for example NYC -> "New York City"), fall back to the phrase's top1 candidate
    instead of dropping the entire record.
    """
    # canonical_map: lowercase -> original database casing for LLM case correction
    canonical_map: dict[str, str] = {}
    # phrase_top1: lowercase original phrase -> top1 canonical name for fallback
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
                # The LLM picked a valid value; align casing with the database.
                item["normalized"] = canonical_map[norm.lower()]
                cleaned.append(item)
            elif orig in phrase_top1:
                # The LLM invented a value, so fall back to the top1 candidate.
                item["normalized"] = phrase_top1[orig]
                cleaned.append(item)
            # Drop the item when neither mapping works; this is a true hallucination.
        roles[role_key] = cleaned

    return roles


def _backfill_roles_from_candidates(roles: dict, candidates: dict) -> dict:
    """
    Backfill obvious missed entities with high-confidence candidates.
    This preserves exact matches and stable typo correction even when spaCy or Chroma
    is unavailable.
    """
    roles = {k: list(v) if isinstance(v, list) else [] for k, v in roles.items()}
    for role in ROLE_DICT:
        roles.setdefault(role, [])

    seen = {
        role: {item.get("original", "").lower() for item in roles.get(role, []) if isinstance(item, dict)}
        for role in ("entity", "location")
    }

    for phrase, info in candidates.items():
        top1 = info["top1"]
        top2 = info["top2"]
        if phrase.lower() in seen["entity"] or phrase.lower() in seen["location"]:
            continue
        exact_match = phrase.lower() == top1["name"].lower()
        stable_match = top1["name"] == top2["name"] or top1["score"] >= 0.9
        if not (exact_match or stable_match):
            continue
        bucket = "location" if top1["group"] in {"city", "state"} else "entity"
        roles[bucket].append({
            "original": phrase,
            "normalized": top1["name"],
            "group": top1["group"],
        })
        seen[bucket].add(phrase.lower())

    return roles


def _apply_candidate_replacements(question: str, roles: dict) -> str:
    normalized_query = question
    replacements = []
    for bucket in ("entity", "location"):
        for item in roles.get(bucket, []):
            if not isinstance(item, dict):
                continue
            original = item.get("original", "")
            normalized = item.get("normalized", "")
            if not original or not normalized:
                continue
            replacements.append((original, normalized))

    for original, normalized in sorted(replacements, key=lambda item: -len(item[0])):
        pattern = re.compile(rf"\b{re.escape(original)}\b", re.IGNORECASE)
        normalized_query = pattern.sub(normalized, normalized_query)
    return normalized_query


def _fallback_result(question: str, pre_cls: dict, candidates: dict) -> dict:
    roles = {k: list(v) if isinstance(v, list) else [] for k, v in pre_cls.items()}
    for role in ROLE_DICT:
        roles.setdefault(role, [])
    roles = _backfill_roles_from_candidates(roles, candidates)
    roles = _validate_roles(roles, candidates)
    return {
        "normalized_query": _apply_candidate_replacements(question, roles),
        "roles": roles,
    }


class QueryNormalizer:
    def __init__(self, llm, normalizer):
        self.llm        = llm
        self.normalizer = normalizer

    def run(self, question: str) -> dict:
        noun_phrases, time_phrases = self.normalizer._extract_phrases(question)
        result     = self.normalizer.get_candidates(noun_phrases, time_phrases)
        pre_cls    = result["pre_classified"]
        candidates = result["candidates"]

        if not self.llm or HumanMessage is None:
            return _fallback_result(question, pre_cls, candidates)

        prompt   = _build_prompt(question, candidates, pre_cls)
        response = self.llm.invoke([HumanMessage(content=prompt)])

        try:
            parsed = json.loads(_clean_json(response.content))
        except Exception:
            return _fallback_result(question, pre_cls, candidates)

        roles = _validate_roles(parsed.get("roles", {}), candidates)
        roles = _backfill_roles_from_candidates(roles, candidates)
        roles = _validate_roles(roles, candidates)
        normalized_query = parsed.get("normalized_query", question)
        normalized_query = _apply_candidate_replacements(normalized_query, roles)
        return {
            "normalized_query": normalized_query,
            "roles":            roles,
        }
