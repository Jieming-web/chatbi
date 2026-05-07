"""
Entity candidate retrieval module (ChromaDB version)
----------------------------------------------------
Responsibility: extract candidate phrases from the user query and assign each phrase
to a role with a two-stage classifier:
  1. spaCy noun_chunks -> noun phrase candidates; NER DATE/TIME -> direct time role
  2. ROLE_EXAMPLES embedding argmax vs ChromaDB entity similarity -> final role decision

Return format (get_candidates):
  {
    "pre_classified": {"time": ["last month"], "metric": ["sales"]},
    "candidates": {
      "samsng": {"top1": {"name": "Samsung", "group": "brand", "score": 0.85}, "top2": {...}},
    }
  }
The final correction decision is delegated to the LLM in client.py's normalize_node.
"""

import os
import re
import sqlite3
from typing import Optional

try:
    import chromadb
except Exception:
    chromadb = None

try:
    import numpy as np
except Exception:
    np = None

try:
    import spacy
except Exception:
    spacy = None
from rapidfuzz import fuzz, process as fuzz_process

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

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
    # business-intent words that often fuzzy-match nearby entities (e.g. sales->Salem)
    "sales", "revenue", "orders", "order", "customer", "customers", "products",
    "product", "reviews", "review", "ratings", "rating", "city", "country",
    "state", "performance", "delivery", "shipping", "shipment", "shipments",
    "cost", "buyers", "comparison", "breakdown", "fraud", "risk", "avg",
    "average", "top", "most", "best", "month", "year", "quarter", "weekend",
    # common verbs/adverbs that created false fuzzy hits like make->Makeup, well->Lowell
    "make", "sell", "well", "doing",
}
CHROMA_PATH     = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_entities"))

# Representative phrases for each non-entity role, used for embedding-based
# semantic matching. These examples cover both full phrases and short keyword cases.
ROLE_EXAMPLES: dict[str, list[str]] = {
    "metric": [
        "total sales", "total revenue", "order count", "return rate",
        "inventory level", "profit margin", "average price",
        "gross margin", "conversion rate", "customer spend",
        # Single-word metrics, including business abbreviations.
        "GMV", "turnover", "income", "cost", "refund amount",
        "customer rating", "review score", "stock level", "order volume",
    ],
    "comparison": [
        "highest revenue", "lowest sales", "top performing",
        "year over year", "month over month", "ranked by",
        "compared to last year", "exceeds average",
        # Single-word comparison cues.
        "vs", "versus", "best selling", "worst performing",
        "most popular", "least popular", "above average", "below average",
    ],
    "status": [
        "shipped orders", "pending payment", "cancelled items",
        "delivered packages", "refunded transactions",
        # Additional status words.
        "returned items", "completed orders", "processing orders",
        "paid orders", "unpaid invoices", "canceled orders",
    ],
    "aggregation": [
        "group by brand", "by category", "each city",
        "per region", "broken down by",
        # Single-word aggregation cues.
        "across regions", "by area", "grouped by",
    ],
    "limit": [
        "top 5", "first 10", "top 3 brands", "bottom 5",
        # Single-word ranking and recency cues.
        "latest orders", "newest products", "oldest records",
    ],
}


class EntityNormalizer:
    def __init__(self):
        self.embed_model = None
        self.nlp = None
        self.chroma = None
        if SentenceTransformer is not None:
            try:
                self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.embed_model = None
        if spacy is not None:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = None
        if chromadb is not None and self.embed_model is not None:
            try:
                self.chroma = chromadb.PersistentClient(path=CHROMA_PATH)
            except Exception:
                self.chroma = None
        self._load_entities()
        self._load_role_embeddings()

    # ─────────────────────────────────────────────
    # Data loading and ChromaDB index construction
    # ─────────────────────────────────────────────
    def _load_entities(self):
        """Load entities from normalized tables into ChromaDB (skips rebuild if count matches)."""
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()

        def extend_distinct(target: list[str], table: str, *column_candidates: str) -> None:
            try:
                cols = {
                    row[1].lower(): row[1]
                    for row in cur.execute(f'PRAGMA table_info("{table}")').fetchall()
                }
            except Exception:
                return
            for candidate in column_candidates:
                real_name = cols.get(candidate.lower())
                if not real_name:
                    continue
                cur.execute(
                    f'SELECT DISTINCT "{real_name}" FROM "{table}" '
                    f'WHERE "{real_name}" IS NOT NULL AND TRIM("{real_name}") != ""'
                )
                target.extend(r[0] for r in cur.fetchall())
                return

        cities: list[str] = []
        states: list[str] = []
        extend_distinct(cities, "Customer", "City")
        extend_distinct(states, "Customer", "Province", "State", "Country")

        # Shipping/global geo columns widen coverage when Customer only stores a subset
        # of the available locations (for example, country names mapped into Province).
        extend_distinct(cities, "Order_", "ShippingCity", "City")
        extend_distinct(states, "Order_", "ShippingProvince", "State", "Country")
        extend_distinct(cities, "GlobalOrder", "City", "ShippingCity")
        extend_distinct(states, "GlobalOrder", "State", "Province", "Country", "shipping_country")

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
            "city":         list(dict.fromkeys(cities)),
            "state":        list(dict.fromkeys(states)),
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

        self.collection = None
        if not self.chroma or not self.embed_model:
            return

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
    # Role embedding preload
    # ─────────────────────────────────────────────
    def _load_role_embeddings(self):
        """Precompute ROLE_EXAMPLES embeddings for the 5 non-entity roles once at startup."""
        self.role_embeddings: dict[str, np.ndarray] = {}
        if not self.embed_model or np is None:
            return
        for role, examples in ROLE_EXAMPLES.items():
            vecs = self.embed_model.encode(examples, normalize_embeddings=True)
            self.role_embeddings[role] = vecs  # shape: (n_examples, dim)

    # ─────────────────────────────────────────────
    # Phrase role classification
    # ─────────────────────────────────────────────
    def _classify_phrase(self, phrase: str) -> tuple[str, Optional[dict]]:
        """
        Run a two-stage classifier and return (role, chroma_result).
        - role: role name (time/metric/.../entity)
        - chroma_result: cached ChromaDB top-2 result, only present for entity phrases
        """
        if not self.embed_model or not self.collection or np is None:
            return "entity", None
        # Stage 1: max embedding similarity against the 5 non-entity roles.
        phrase_vec = self.embed_model.encode([phrase], normalize_embeddings=True)
        best_role, best_score = "entity", 0.0
        for role, vecs in self.role_embeddings.items():
            score = float((vecs @ phrase_vec.T).max())
            if score > best_score:
                best_role, best_score = role, score

        # Stage 2: query entity similarity from ChromaDB and cache it for reuse.
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
    # Phrase extraction
    # ─────────────────────────────────────────────
    def _extract_phrases(self, query: str) -> tuple[list[str], list[str]]:
        """
        Split the query with spaCy and return (noun_phrases, time_phrases).
        - noun_phrases: noun phrases used as entity/metric/etc. candidates
        - time_phrases: DATE/TIME expressions detected by NER and assigned directly to time

        Extra scan: spaCy noun_chunks are dependency-based and can miss abbreviations
        after prepositions (for example "in TX" or "from LA"), so we add a token scan
        for uppercase abbreviations and known aliases.
        """
        if self.nlp is None:
            tokens = re.findall(r"[A-Za-z][A-Za-z\-]*", query)
            entity_keys = list(self.entity_map.keys())
            noun_phrases = []
            max_ngram = min(4, len(tokens))
            for n in range(max_ngram, 0, -1):
                for i in range(len(tokens) - n + 1):
                    window = tokens[i:i + n]
                    phrase = " ".join(window)
                    lower = phrase.lower()
                    if all(part.lower() in _STOPWORDS for part in window):
                        continue
                    if n == 1 and phrase in ABBREV_MAP:
                        noun_phrases.append(phrase)
                        continue
                    if lower in self.entity_map:
                        noun_phrases.append(phrase)
                        continue
                    match = fuzz_process.extractOne(
                        lower,
                        entity_keys,
                        scorer=fuzz.ratio,
                        score_cutoff=82 if n > 1 else 75,
                    )
                    if match:
                        noun_phrases.append(phrase)
            return list(dict.fromkeys(noun_phrases)), []

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

        # First pass: uppercase abbreviations and known aliases such as TX, LA, and Cali.
        # Location abbreviations after prepositions often do not appear in noun_chunks.
        extra = [
            token.text for token in doc
            if token.text.isalpha()
            and len(token.text) >= 2
            and token.text.lower() not in _STOPWORDS
            and token.text.lower() not in time_set
            and token.text not in existing
            and (token.text.isupper() or token.text in ABBREV_MAP)
        ]

        # Second pass: likely typo tokens for brands/entities. spaCy may tag unknown words
        # as VERB/ADP, so use token.prob as a rough frequency signal:
        #   common English words (sales, phone) -> prob > -13
        #   unknown words / typos (samsng, appel) -> prob ~= -20
        # Only low-probability tokens go through RapidFuzz to avoid false positives
        # like "sales" -> "Salem".
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
                or token.prob > -13          # Skip known English words.
            ):
                continue
            match = fuzz_process.extractOne(
                t.lower(), entity_keys, scorer=fuzz.ratio, score_cutoff=75
            )
            if match:
                fuzzy_extra.append(t)

        return list(dict.fromkeys(noun_phrases + extra + fuzzy_extra)), time_phrases

    # ─────────────────────────────────────────────
    # Vector retrieval
    # ─────────────────────────────────────────────
    def get_candidates(self, noun_phrases: list[str], time_phrases: list[str]) -> dict:
        """
        Apply two-stage role classification to phrases and return:
        {
          "pre_classified": {"time": ["last month"], "metric": ["sales"], ...},
          "candidates": {
            "samsng": {"top1": {"name": "Samsung", "group": "brand", "score": 0.85},
                       "top2": {"name": "Samsonite", "group": "brand", "score": 0.62}},
            ...
          }
        }
        time_phrases are assigned directly to the time role by spaCy NER.
        Exact matches in all_entities are skipped because they do not need correction.
        For entity phrases, the ChromaDB top-2 result is reused from classification time.
        """
        pre_classified: dict[str, list[str]] = {}
        candidates: dict[str, dict] = {}

        # time_phrases go straight into pre_classified without embedding classification.
        if time_phrases:
            pre_classified["time"] = time_phrases

        for phrase in noun_phrases:
            if phrase.lower() in self.all_entities:
                info = self.entity_map[phrase.lower()]
                candidates[phrase] = {
                    "top1": {"name": info["name"], "group": info["group"], "score": 1.0},
                    "top2": {"name": info["name"], "group": info["group"], "score": 1.0},
                }
                continue

            # ── Pre-retrieval layer 1: direct alias dictionary mapping ─────────────────
            if phrase in ABBREV_MAP:
                canonical = ABBREV_MAP[phrase]
                info = self.entity_map.get(canonical.lower())
                if info:
                    candidates[phrase] = {
                        "top1": {"name": info["name"], "group": info["group"], "score": 1.0},
                        "top2": {"name": info["name"], "group": info["group"], "score": 1.0},
                    }
                    continue

            # ── Pre-retrieval layer 2: token-level RapidFuzz for brand/entity typos ───
            # Match tokens inside a noun chunk individually so words like "sales" or
            # "orders" do not skew the full-phrase embedding toward the wrong role.
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

            # ── Default path: embedding classification + ChromaDB ─────────────────────
            if not self.embed_model or not self.collection:
                entity_keys = list(self.entity_map.keys())
                result = fuzz_process.extractOne(
                    phrase.lower(),
                    entity_keys,
                    scorer=fuzz.ratio,
                    score_cutoff=75,
                )
                if result:
                    matched_key, score, _ = result
                    info = self.entity_map[matched_key]
                    candidates[phrase] = {
                        "top1": {"name": info["name"], "group": info["group"], "score": score / 100},
                        "top2": {"name": info["name"], "group": info["group"], "score": score / 100},
                    }
                continue

            role, chroma_res = self._classify_phrase(phrase)

            if role != "entity":
                pre_classified.setdefault(role, []).append(phrase)
                continue

            # For entity phrases, build top-2 candidates from the cached ChromaDB result.
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

        # Longest-match dedupe: drop phrases whose token sequence is already covered
        # by a longer entity candidate.
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

        # Remove covered subphrases inside candidates.
        candidates = {p: v for p, v in candidates.items() if not is_subphrase_of_entity(p)}
        # Remove pre_classified subphrases already covered by entity candidates.
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
