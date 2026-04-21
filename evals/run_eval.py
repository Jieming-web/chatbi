"""
Eval runner — 支持三种模式：

  python -m evals.run_eval --mode schema
      只测 SchemaRAG 召回质量（不需要 API key）

  python -m evals.run_eval --mode full
      运行完整 LangGraph pipeline 计算 Execution Match（需要 OPENAI_API_KEY）

  python -m evals.run_eval --mode entity --golden natural
      测试 QueryNormalizer 实体纠错准确率（需要 OPENAI_API_KEY）

  python -m evals.run_eval --config dense llm    (M1 baseline)
  python -m evals.run_eval --config hybrid llm   (切换 retriever)
  python -m evals.run_eval --config hybrid cross_encoder
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import Settings
import yaml


GOLDEN_PATH = Path(__file__).parent / "golden_queries.jsonl"
GOLDEN_FILES = {
    "standard":  "golden_queries.jsonl",
    "multijoin": "golden_queries_multijoin.jsonl",
    "natural":   "golden_queries_natural.jsonl",
}
REPORTS_DIR = Path(__file__).parent / "reports"
DB_PATH = str(Path(__file__).parent.parent / "Ecommerce.db")


def load_golden(golden: str = "standard"):
    path = Path(__file__).parent / GOLDEN_FILES.get(golden, GOLDEN_FILES["standard"])
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _build_settings(retriever_type: str, reranker_type: str) -> Settings:
    cfg_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with cfg_path.open() as f:
        raw = yaml.safe_load(f)
    raw["retriever"]["type"] = retriever_type
    raw["reranker"]["type"] = reranker_type
    return Settings(**raw)


def run_schema_eval(retriever_type: str, reranker_type: str, golden: str = "standard") -> dict:
    from evals.metrics import schema_recall
    import impl  # noqa: F401
    from core.registry import create_retriever, create_reranker
    from db_mcp_server.schema_rag import SchemaRAG, FIELD_DESCRIPTIONS, TABLE_DESCRIPTIONS

    cfg = _build_settings(retriever_type, reranker_type)

    retriever = create_retriever(
        cfg.retriever,
        field_descriptions=FIELD_DESCRIPTIONS,
        embedding_model_name=cfg.embedding.model_name,
    )
    # Apply reranker if it doesn't need an LLM (e.g. cross_encoder runs offline)
    use_reranker = reranker_type != "llm"
    reranker = None
    if use_reranker:
        reranker = create_reranker(
            cfg.reranker,
            table_descriptions=TABLE_DESCRIPTIONS,
        )

    golden_data = load_golden(golden)
    results = []
    total_recall = 0.0

    for item in golden_data:
        hits = retriever.retrieve(item["question"], top_k=cfg.retriever.top_k * 4)
        seen, retrieved = set(), []
        for h in hits:
            if h.table not in seen:
                seen.add(h.table)
                retrieved.append(h.table)
            if len(retrieved) == cfg.retriever.final_tables:
                break

        if reranker:
            retrieved = reranker.rerank(item["question"], retrieved, top_k=cfg.reranker.top_k)

        recall = schema_recall.compute(item["expected_tables"], retrieved)
        total_recall += recall
        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_tables": item["expected_tables"],
            "retrieved_tables": retrieved,
            "schema_recall": round(recall, 4),
        })

    avg_recall = total_recall / len(golden_data)
    return {"results": results, "schema_recall_avg": round(avg_recall, 4)}


def run_full_eval(retriever_type: str, reranker_type: str, golden: str = "standard") -> dict:
    from evals.metrics import schema_recall, execution_match

    # Patch settings before importing client modules that read them at import time
    cfg_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with cfg_path.open() as f:
        raw = yaml.safe_load(f)
    raw["retriever"]["type"] = retriever_type
    raw["reranker"]["type"] = reranker_type
    # Re-load settings singleton
    import config.settings as _s_mod
    _s_mod.settings = _s_mod.Settings(**raw)
    import db_mcp_server.schema_rag as _rag_mod
    import importlib
    importlib.reload(_rag_mod)

    from client import build_graph
    app = build_graph()
    config = {"configurable": {"thread_id": "eval"}}

    golden_data = load_golden(golden)
    results = []
    total_em = 0.0
    total_recall = 0.0

    initial_tpl = {
        "question": "", "normalized_query": "", "roles": {},
        "schema_context": {"tables": [], "join_paths": []},
        "generated_sql": "", "final_sql": "", "result": [], "error": "", "retries": 0,
    }

    for item in golden_data:
        t0 = time.time()
        state = dict(initial_tpl)
        state["question"] = item["question"]
        try:
            final = app.invoke(state, config=config)
        except Exception as e:
            results.append({
                "id": item["id"], "question": item["question"],
                "error": str(e), "schema_recall": 0.0, "em": 0.0,
            })
            continue

        retrieved = [t["name"] for t in final.get("schema_context", {}).get("tables", [])]
        recall = schema_recall.compute(item["expected_tables"], retrieved)
        pred_sql = final.get("final_sql") or final.get("generated_sql", "")
        em = execution_match.compute(DB_PATH, pred_sql, item["golden_sql"])
        total_recall += recall
        total_em += em
        results.append({
            "id": item["id"],
            "question": item["question"],
            "expected_tables": item["expected_tables"],
            "retrieved_tables": retrieved,
            "schema_recall": round(recall, 4),
            "pred_sql": pred_sql,
            "golden_sql": item["golden_sql"],
            "em": em,
            "latency_s": round(time.time() - t0, 2),
        })
        print(f"  [{item['id']}] recall={recall:.2f} EM={em:.0f}  ({results[-1]['latency_s']}s)")

    n = len(golden_data)
    return {
        "results": results,
        "schema_recall_avg": round(total_recall / n, 4),
        "execution_match": round(total_em / n, 4),
    }


def run_entity_eval() -> dict:
    """测试 QueryNormalizer 实体纠错准确率（需要 OPENAI_API_KEY）"""
    from evals.metrics import entity_f1
    from langchain_openai import ChatOpenAI
    from config import settings
    from db_mcp_server.entity_normalizer import EntityNormalizer
    from db_mcp_server.query_normalizer import QueryNormalizer

    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=0,
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    qn = QueryNormalizer(llm, EntityNormalizer())

    golden_data = load_golden("natural")
    results = []
    total_f1 = 0.0

    for item in golden_data:
        t0 = time.time()
        result = qn.run(item["question"])
        predicted = [
            e["normalized"]
            for e in result["roles"].get("entity", []) + result["roles"].get("location", [])
            if isinstance(e, dict)
        ]
        expected = [e["normalized"] for e in item["expected_entities"]]
        f1 = entity_f1.compute(expected, predicted)
        total_f1 += f1
        results.append({
            "id":               item["id"],
            "question":         item["question"],
            "expected_normalized": item["expected_normalized"],
            "predicted_normalized": result.get("normalized_query", ""),
            "expected_entities": expected,
            "predicted_entities": predicted,
            "entity_f1":        round(f1, 4),
            "latency_s":        round(time.time() - t0, 2),
        })
        print(f"  [{item['id']}] F1={f1:.2f}  pred={predicted}  expected={expected}")

    return {
        "results": results,
        "entity_f1_avg": round(total_f1 / len(golden_data), 4),
    }


def _save_report(summary: dict, tag: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{ts}_{tag}.json"
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = path.with_suffix(".md")
    lines = [
        f"# Eval Report — {tag}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Schema Recall | {summary.get('schema_recall_avg', 'N/A')} |",
    ]
    if "execution_match" in summary:
        lines.append(f"| Execution Match | {summary['execution_match']} |")
    if "entity_f1_avg" in summary:
        lines.append(f"| Entity F1 | {summary['entity_f1_avg']} |")
    if "entity_f1_avg" in summary:
        lines += ["", "## Per-query Results", "", "| ID | Question | Entity F1 | Predicted | Expected |", "|---|---|---|---|---|"]
        for r in summary.get("results", []):
            lines.append(f"| {r['id']} | {r['question'][:50]} | {r['entity_f1']} | {r['predicted_entities']} | {r['expected_entities']} |")
    else:
        lines += ["", "## Per-query Results", "", "| ID | Question | Recall | EM |", "|---|---|---|---|"]
        for r in summary.get("results", []):
            em = r.get("em", "-")
            lines.append(f"| {r['id']} | {r['question'][:50]} | {r['schema_recall']} | {em} |")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["schema", "full", "entity"], default="schema")
    parser.add_argument("--retriever", default="dense")
    parser.add_argument("--reranker", default="llm")
    parser.add_argument("--golden", choices=["standard", "multijoin", "natural"], default="standard")
    args = parser.parse_args()

    tag = f"{args.retriever}_{args.reranker}_{args.mode}_{args.golden}"
    print(f"\n=== Eval: retriever={args.retriever} reranker={args.reranker} mode={args.mode} golden={args.golden} ===\n")

    if args.mode == "schema":
        summary = run_schema_eval(args.retriever, args.reranker, args.golden)
    elif args.mode == "entity":
        summary = run_entity_eval()
    else:
        summary = run_full_eval(args.retriever, args.reranker, args.golden)

    report_path = _save_report(summary, tag)
    if "schema_recall_avg" in summary:
        print(f"\nSchema Recall: {summary['schema_recall_avg']:.1%}")
    if "execution_match" in summary:
        print(f"Execution Match: {summary['execution_match']:.1%}")
    if "entity_f1_avg" in summary:
        print(f"Entity F1: {summary['entity_f1_avg']:.1%}")
    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
