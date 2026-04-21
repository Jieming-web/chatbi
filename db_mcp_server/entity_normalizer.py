"""
实体候选检索模块（ChromaDB 版）
---------------------------------
职责：从用户 query 中提取候选短语，通过两阶段分类决定每个短语属于哪个角色：
  1. spaCy noun_chunks → 名词短语候选；NER DATE/TIME → 直接归 time 角色
  2. ROLE_EXAMPLES embedding argmax vs ChromaDB entity 相似度 → 决定名词短语归属

返回格式（get_candidates）：
  {
    "pre_classified": {"time": ["last month"], "metric": ["sales"]},
    "candidates": {
      "samsng": {"top1": {"name": "Samsung", "group": "品牌", "score": 0.85}, "top2": {...}},
    }
  }
纠错决策由 client.py 的 normalize_node 交给 LLM 完成。
"""

import os
import sqlite3
from typing import Optional

import chromadb
import numpy as np
import spacy
from rapidfuzz import fuzz, process as fuzz_process
from sentence_transformers import SentenceTransformer

from db_mcp_server.utils import DB_PATH



# Standard US city/state abbreviations → canonical DB values
ABBREV_MAP: dict[str, str] = {
    "LA": "Los Angeles", "SF": "San Francisco", "NYC": "New York",
    "NY": "New York",    "TX": "Texas",          "CA": "California",
    "FL": "Florida",     "IL": "Illinois",        "PA": "Pennsylvania",
    "Cali": "California","NJ": "New Jersey",      "WA": "Washington",
    "GA": "Georgia",     "OH": "Ohio",            "MI": "Michigan",
    "AZ": "Arizona",     "CO": "Colorado",        "NC": "North Carolina",
    "VA": "Virginia",    "MA": "Massachusetts",
}

COLLECTION_NAME = "entities"

_STOPWORDS = {
    "me", "we", "you", "he", "she", "it", "they", "what", "which", "who",
    "this", "that", "these", "those", "the", "a", "an", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "find", "show", "get", "give", "tell", "list", "count", "how", "why",
}
CHROMA_PATH     = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_entities"))

# 每个非实体角色的代表短语，用于 embedding 语义匹配（仅英文）
# 覆盖完整短语与单词缩写两类边缘情况
ROLE_EXAMPLES: dict[str, list[str]] = {
    "metric": [
        "total sales", "total revenue", "order count", "return rate",
        "inventory level", "profit margin", "average price",
        "gross margin", "conversion rate", "customer spend",
        # 单词指标（含业务缩写）
        "GMV", "turnover", "income", "cost", "refund amount",
        "customer rating", "review score", "stock level", "order volume",
    ],
    "comparison": [
        "highest revenue", "lowest sales", "top performing",
        "year over year", "month over month", "ranked by",
        "compared to last year", "exceeds average",
        # 单词比较词
        "vs", "versus", "best selling", "worst performing",
        "most popular", "least popular", "above average", "below average",
    ],
    "status": [
        "shipped orders", "pending payment", "cancelled items",
        "delivered packages", "refunded transactions",
        # 补充状态词
        "returned items", "completed orders", "processing orders",
        "paid orders", "unpaid invoices", "canceled orders",
    ],
    "aggregation": [
        "group by brand", "by category", "each city",
        "per region", "broken down by",
        # 单词聚合词
        "across regions", "by area", "grouped by",
    ],
    "limit": [
        "top 5", "first 10", "top 3 brands", "bottom 5",
        # 单词排序限定
        "latest orders", "newest products", "oldest records",
    ],
}


class EntityNormalizer:
    def __init__(self):
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.nlp         = spacy.load("en_core_web_sm")
        self.chroma      = chromadb.PersistentClient(path=CHROMA_PATH)
        self._load_entities()
        self._load_role_embeddings()

    # ─────────────────────────────────────────────
    # 数据加载 & ChromaDB 索引构建
    # ─────────────────────────────────────────────
    def _load_entities(self):
        """Load entities from normalized tables into ChromaDB (skips rebuild if count matches)."""
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()

        cur.execute("SELECT DISTINCT City FROM Customer WHERE City IS NOT NULL")
        cities = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT Province FROM Customer WHERE Province IS NOT NULL")
        states = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT Brand FROM Product WHERE Brand IS NOT NULL")
        brands = [r[0] for r in cur.fetchall()]

        cur.execute(
            "SELECT DISTINCT Name FROM Category WHERE ParentCategoryId IS NULL AND Name IS NOT NULL"
        )
        categories = [r[0] for r in cur.fetchall()]

        cur.execute(
            "SELECT DISTINCT Name FROM Category WHERE ParentCategoryId IS NOT NULL AND Name IS NOT NULL"
        )
        sub_categories = [r[0] for r in cur.fetchall()]

        conn.close()

        entity_groups = {
            "city":         cities,
            "state":        states,
            "brand":        brands,
            "category":     categories,
            "sub_category": sub_categories,
        }

        self.all_entities: set[str] = {
            e.lower() for items in entity_groups.values() for e in items
        }

        # Flat map: lowercase_name → {name, group} — used by RapidFuzz lookup
        self.entity_map: dict[str, dict] = {
            name.lower(): {"name": name, "group": group}
            for group, items in entity_groups.items()
            for name in items
        }

        all_names  = [name  for items in entity_groups.values() for name  in items]
        all_groups = [group for group, items in entity_groups.items() for _ in items]
        total      = len(all_names)

        try:
            collection = self.chroma.get_collection(COLLECTION_NAME)
            if collection.count() == total:
                self.collection = collection
                return
            self.chroma.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        self.collection = self.chroma.create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        vectors = self.embed_model.encode(all_names, normalize_embeddings=True).tolist()
        self.collection.add(
            ids=[str(i) for i in range(total)],
            embeddings=vectors,
            metadatas=[{"group": g} for g in all_groups],
            documents=all_names,
        )

    # ─────────────────────────────────────────────
    # 角色 embedding 预加载
    # ─────────────────────────────────────────────
    def _load_role_embeddings(self):
        """预计算 5 个非实体角色的 ROLE_EXAMPLES embedding，初始化时一次性完成"""
        self.role_embeddings: dict[str, np.ndarray] = {}
        for role, examples in ROLE_EXAMPLES.items():
            vecs = self.embed_model.encode(examples, normalize_embeddings=True)
            self.role_embeddings[role] = vecs  # shape: (n_examples, dim)

    # ─────────────────────────────────────────────
    # 短语角色分类
    # ─────────────────────────────────────────────
    def _classify_phrase(self, phrase: str) -> tuple[str, Optional[dict]]:
        """
        两阶段分类，返回 (role, chroma_result)。
        - role: 角色名（time/metric/.../entity）
        - chroma_result: ChromaDB top-2 查询结果，仅 entity 时有值，供 get_candidates 复用
        """
        # 阶段1：5 个非实体角色 embedding max 相似度
        phrase_vec = self.embed_model.encode([phrase], normalize_embeddings=True)
        best_role, best_score = "entity", 0.0
        for role, vecs in self.role_embeddings.items():
            score = float((vecs @ phrase_vec.T).max())
            if score > best_score:
                best_role, best_score = role, score

        # 阶段2：ChromaDB 查 entity 相似度（结果缓存供 get_candidates 复用）
        res = self.collection.query(
            query_embeddings=phrase_vec.tolist(),
            n_results=2,
            include=["documents", "metadatas", "distances"],
        )
        entity_score = (
            float(1.0 - res["distances"][0][0]) if res["documents"][0] else 0.0
        )

        if entity_score > best_score:
            return "entity", res
        return best_role, None

    # ─────────────────────────────────────────────
    # 短语提取
    # ─────────────────────────────────────────────
    def _extract_phrases(self, query: str) -> tuple[list[str], list[str]]:
        """
        用 spaCy 切分短语，返回 (noun_phrases, time_phrases)。
        - noun_phrases: 名词短语，作为实体/指标等候选
        - time_phrases: NER 识别的 DATE/TIME 表达，直接归 time 角色

        额外扫描：spaCy noun_chunk 基于依存句法，会遗漏介词后的缩写
        （如 "in TX"、"from LA"），用 token 扫描补充全大写 token 和已知缩写。
        """
        doc          = self.nlp(query)
        noun_phrases = list(dict.fromkeys(
            chunk.text for chunk in doc.noun_chunks
            if chunk.text.lower() not in _STOPWORDS and len(chunk.text) > 2
        ))
        time_phrases = list(dict.fromkeys(
            ent.text for ent in doc.ents if ent.label_ in ("DATE", "TIME")
        ))

        time_set = {t.lower() for t in time_phrases}
        existing = set(noun_phrases)

        # 第一轮补充：全大写缩写 / 已知缩写表（如 TX、LA、Cali）
        # 介词后的地名缩写不会进入 noun_chunks，需要单独捞出来
        extra = [
            token.text for token in doc
            if token.text.isalpha()
            and len(token.text) >= 2
            and token.text.lower() not in _STOPWORDS
            and token.text.lower() not in time_set
            and token.text not in existing
            and (token.text.isupper() or token.text in ABBREV_MAP)
        ]

        # 第二轮补充：品牌错别字 token（spaCy 会把未知词误标为 VERB/ADP）
        # 判断依据：spaCy token.prob 是词频对数概率
        #   已知英语词（sales、phone）→ prob > -13
        #   未知词/错别字（samsng、appel）→ prob ≈ -20
        # 只对低概率 token 做 RapidFuzz，避免 "sales→Salem" 类假阳性
        existing2 = existing | set(extra)
        entity_keys = list(self.entity_map.keys())
        fuzzy_extra = []
        for token in doc:
            t = token.text
            if (
                not t.isalpha()
                or len(t) < 3
                or t.lower() in _STOPWORDS
                or t.lower() in time_set
                or t in existing2
                or token.prob > -13          # 跳过已知英语词
            ):
                continue
            match = fuzz_process.extractOne(
                t.lower(), entity_keys, scorer=fuzz.ratio, score_cutoff=75
            )
            if match:
                fuzzy_extra.append(t)

        return list(dict.fromkeys(noun_phrases + extra + fuzzy_extra)), time_phrases

    # ─────────────────────────────────────────────
    # 向量检索
    # ─────────────────────────────────────────────
    def get_candidates(self, noun_phrases: list[str], time_phrases: list[str]) -> dict:
        """
        对短语做两阶段角色分类，返回：
        {
          "pre_classified": {"time": ["last month"], "metric": ["sales"], ...},
          "candidates": {
            "samsng": {"top1": {"name": "Samsung", "group": "品牌", "score": 0.85},
                       "top2": {"name": "Samsonite", "group": "品牌", "score": 0.62}},
            ...
          }
        }
        time_phrases 由 spaCy NER 直接归入 time 角色，不走 embedding 分类。
        精确匹配 all_entities 的短语跳过（无需纠错）。
        entity 角色的 ChromaDB top-2 结果直接复用分类阶段的查询，不重复检索。
        """
        pre_classified: dict[str, list[str]] = {}
        candidates: dict[str, dict] = {}

        # time_phrases 直接归入 pre_classified，无需 embedding 分类
        if time_phrases:
            pre_classified["time"] = time_phrases

        for phrase in noun_phrases:
            if phrase.lower() in self.all_entities:
                continue

            # ── 预检索层 1：缩写字典直接映射 ──────────────────────────────
            if phrase in ABBREV_MAP:
                canonical = ABBREV_MAP[phrase]
                info = self.entity_map.get(canonical.lower())
                if info:
                    candidates[phrase] = {
                        "top1": {"name": info["name"], "group": info["group"], "score": 1.0},
                        "top2": {"name": info["name"], "group": info["group"], "score": 1.0},
                    }
                    continue

            # ── 预检索层 2：token 级 RapidFuzz（处理品牌错别字）────────────
            # 对 noun chunk 内每个 token 单独做字符模糊匹配，避免整段短语
            # 的语义向量被 "sales"/"orders" 等词拉偏导致误分类
            entity_keys = list(self.entity_map.keys())
            fuzzy_hit: Optional[tuple[str, str, float]] = None
            for token in phrase.split():
                if len(token) < 3 or token.lower() in _STOPWORDS:
                    continue
                result = fuzz_process.extractOne(
                    token.lower(), entity_keys,
                    scorer=fuzz.ratio, score_cutoff=75,
                )
                if result:
                    matched_key, score, _ = result
                    fuzzy_hit = (token, matched_key, score / 100)
                    break
            if fuzzy_hit:
                orig_token, matched_key, score = fuzzy_hit
                info = self.entity_map[matched_key]
                candidates[orig_token] = {
                    "top1": {"name": info["name"], "group": info["group"], "score": score},
                    "top2": {"name": info["name"], "group": info["group"], "score": score},
                }
                continue

            # ── 原有路径：embedding 分类 + ChromaDB ────────────────────────
            role, chroma_res = self._classify_phrase(phrase)

            if role != "entity":
                pre_classified.setdefault(role, []).append(phrase)
                continue

            # entity：用缓存的 ChromaDB 结果构建 top-2 候选
            if chroma_res is None or not chroma_res["documents"][0]:
                continue

            docs = chroma_res["documents"][0]

            def to_candidate(res: dict, i: int) -> dict:
                return {
                    "name":  res["documents"][0][i],
                    "group": res["metadatas"][0][i]["group"],
                    "score": float(1.0 - res["distances"][0][i]),
                }

            top1 = to_candidate(chroma_res, 0)
            top2 = to_candidate(chroma_res, 1) if len(docs) > 1 else top1
            candidates[phrase] = {"top1": top1, "top2": top2}

        # 最长匹配去重：短语的 token 序列已被更长 entity candidate 覆盖则移除
        def is_subphrase_of_entity(phrase: str) -> bool:
            phrase_tokens = phrase.lower().split()
            n = len(phrase_tokens)
            for entity_phrase in candidates:
                entity_tokens = entity_phrase.lower().split()
                if len(entity_tokens) <= n:
                    continue
                for start in range(len(entity_tokens) - n + 1):
                    if entity_tokens[start:start + n] == phrase_tokens:
                        return True
            return False

        # 去重 candidates 内部的子短语
        candidates = {p: v for p, v in candidates.items() if not is_subphrase_of_entity(p)}
        # 去重 pre_classified 中被 entity candidate 覆盖的子短语
        for role in pre_classified:
            pre_classified[role] = [
                p for p in pre_classified[role] if not is_subphrase_of_entity(p)
            ]
        pre_classified = {k: v for k, v in pre_classified.items() if v}

        return {"pre_classified": pre_classified, "candidates": candidates}


if __name__ == "__main__":
    normalizer = EntityNormalizer()

    test_queries = [
        "show me last month sales for samsng phones",
        "what is the inventory of iphone15 pro max in Los Angeles",
        "find the return rate for nkie sneakers in NYC",
    ]

    for q in test_queries:
        noun_phrases, time_phrases = normalizer._extract_phrases(q)
        result = normalizer.get_candidates(noun_phrases, time_phrases)
        pre_cls = result["pre_classified"]
        cands   = result["candidates"]

        print(f"Query: {q}")
        if pre_cls:
            print(f"Pre-classified:")
            for role, words in pre_cls.items():
                print(f"  {role}: {words}")
        print(f"Candidates:")
        for phrase, info in cands.items():
            print(f"  {phrase!r} → top1: {info['top1']['name']} ({info['top1']['score']:.2f}), "
                  f"top2: {info['top2']['name']} ({info['top2']['score']:.2f})")
        print("-" * 50)
