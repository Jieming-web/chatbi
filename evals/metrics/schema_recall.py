from typing import List


def compute(expected: List[str], retrieved: List[str]) -> float:
    """Fraction of expected tables that appear in retrieved tables."""
    if not expected:
        return 1.0
    hit = sum(1 for t in expected if t in retrieved)
    return hit / len(expected)
