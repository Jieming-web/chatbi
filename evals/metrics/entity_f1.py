"""
Entity F1: compares normalized entity/location names extracted by the pipeline
against expected entities in the golden query.
"""
from typing import List


def compute(
    expected_entities: List[str],
    predicted_entities: List[str],
) -> float:
    """Micro F1 over entity name sets (case-insensitive)."""
    if not expected_entities and not predicted_entities:
        return 1.0
    if not expected_entities or not predicted_entities:
        return 0.0

    exp = {e.lower().strip() for e in expected_entities}
    pred = {p.lower().strip() for p in predicted_entities}

    tp = len(exp & pred)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(exp) if exp else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
