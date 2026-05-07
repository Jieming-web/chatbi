from db_mcp_server.entity_normalizer import EntityNormalizer
from db_mcp_server.query_normalizer import QueryNormalizer


class _DummyNormalizer:
    def __init__(self, candidates, pre_classified=None, phrases=None):
        self._candidates = candidates
        self._pre_classified = pre_classified or {}
        self._phrases = phrases or list(candidates)

    def _extract_phrases(self, question):
        return self._phrases, []

    def get_candidates(self, noun_phrases, time_phrases):
        return {
            "pre_classified": self._pre_classified,
            "candidates": self._candidates,
        }


class _BadLLM:
    class _Resp:
        content = "not-json"

    def invoke(self, messages):
        return self._Resp()


def test_query_normalizer_preserves_exact_match_without_llm():
    normalizer = _DummyNormalizer({
        "sony": {
            "top1": {"name": "Sony", "group": "brand", "score": 1.0},
            "top2": {"name": "Sony", "group": "brand", "score": 1.0},
        }
    })
    result = QueryNormalizer(llm=None, normalizer=normalizer).run("sony delivery performance")

    assert result["normalized_query"] == "Sony delivery performance"
    assert result["roles"]["entity"] == [
        {"original": "sony", "normalized": "Sony", "group": "brand"}
    ]


def test_query_normalizer_falls_back_to_candidates_when_llm_output_is_invalid():
    normalizer = _DummyNormalizer({
        "delll": {
            "top1": {"name": "Dell", "group": "brand", "score": 0.95},
            "top2": {"name": "Dell", "group": "brand", "score": 0.95},
        },
        "fitbit": {
            "top1": {"name": "Fitbit", "group": "brand", "score": 1.0},
            "top2": {"name": "Fitbit", "group": "brand", "score": 1.0},
        },
    })
    result = QueryNormalizer(llm=_BadLLM(), normalizer=normalizer).run(
        "delll vs fitbit revenue comparison"
    )

    assert result["normalized_query"] == "Dell vs Fitbit revenue comparison"
    assert result["roles"]["entity"] == [
        {"original": "delll", "normalized": "Dell", "group": "brand"},
        {"original": "fitbit", "normalized": "Fitbit", "group": "brand"},
    ]


def test_entity_normalizer_extracts_multiword_typos_without_spacy():
    normalizer = EntityNormalizer.__new__(EntityNormalizer)
    normalizer.nlp = None
    normalizer.entity_map = {
        "sony": {"name": "Sony", "group": "brand"},
        "the hague": {"name": "The Hague", "group": "city"},
        "belgium": {"name": "Belgium", "group": "state"},
    }

    noun_phrases, time_phrases = EntityNormalizer._extract_phrases(
        normalizer,
        "sony delivery performance in The Hage and Belguim",
    )

    assert time_phrases == []
    assert "sony" in noun_phrases
    assert "The Hage" in noun_phrases
    assert "Belguim" in noun_phrases


def test_entity_normalizer_keeps_exact_matches_as_candidates():
    normalizer = EntityNormalizer.__new__(EntityNormalizer)
    normalizer.all_entities = {"sony"}
    normalizer.entity_map = {"sony": {"name": "Sony", "group": "brand"}}
    normalizer.embed_model = None
    normalizer.collection = None

    result = EntityNormalizer.get_candidates(normalizer, ["sony"], [])

    assert result["candidates"]["sony"]["top1"] == {
        "name": "Sony",
        "group": "brand",
        "score": 1.0,
    }
