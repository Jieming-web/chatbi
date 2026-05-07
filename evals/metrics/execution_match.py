import sqlite3
from typing import Any, List, Optional, Tuple


def _run_sql(db_path: str, sql: str) -> Optional[List[Tuple]]:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return None


def compute(db_path: str, pred_sql: str, golden_sql: str) -> float:
    """1.0 if pred and golden produce identical result sets, else 0.0."""
    pred_rows = _run_sql(db_path, pred_sql)
    gold_rows = _run_sql(db_path, golden_sql)
    if pred_rows is None or gold_rows is None:
        return 0.0
    return float(set(map(tuple, pred_rows)) == set(map(tuple, gold_rows)))
