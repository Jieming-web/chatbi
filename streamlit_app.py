import uuid
from datetime import datetime
from time import perf_counter
from typing import Any

import pandas as pd
import streamlit as st

from client import ChatBIState, build_graph
from core.logger import new_trace_id
from response import format_roles

try:
    from langchain_community.callbacks.manager import get_openai_callback
except Exception:  # pragma: no cover - graceful fallback when unavailable
    get_openai_callback = None


def _build_initial_state(question: str) -> ChatBIState:
    return {
        "question": question,
        "normalized_query": "",
        "roles": {},
        "schema_context": {"tables": [], "join_paths": []},
        "generated_sql": "",
        "final_sql": "",
        "result": [],
        "error": "",
        "retries": 0,
    }


def _run_question(question: str) -> tuple[dict[str, Any], dict[str, Any]]:
    app = st.session_state.graph
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    initial_state = _build_initial_state(question)
    new_trace_id()

    started_at = perf_counter()
    usage = {
        "latency_seconds": 0.0,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "total_cost_usd": None,
    }

    if get_openai_callback is not None:
        with get_openai_callback() as cb:
            final_state = app.invoke(initial_state, config=config)
            usage["prompt_tokens"] = cb.prompt_tokens
            usage["completion_tokens"] = cb.completion_tokens
            usage["total_tokens"] = cb.total_tokens
            usage["total_cost_usd"] = cb.total_cost
    else:
        final_state = app.invoke(initial_state, config=config)

    usage["latency_seconds"] = perf_counter() - started_at
    return final_state, usage


def _render_result(final_state: dict[str, Any], usage: dict[str, Any]) -> None:
    normalized_query = final_state.get("normalized_query", "")
    if normalized_query and normalized_query != final_state.get("question", ""):
        st.info(f"Normalized: `{normalized_query}`")

    roles_text = format_roles(final_state.get("roles", {}))
    if roles_text:
        with st.expander("Intent Analysis", expanded=False):
            st.text(roles_text)

    final_sql = final_state.get("final_sql") or final_state.get("generated_sql", "")
    st.subheader("Generated SQL")
    st.code(final_sql or "-- empty --", language="sql")

    retries = final_state.get("retries", 0)
    if retries > 0:
        st.warning(f"SQL checker retries: {retries}")

    error = final_state.get("error", "")
    if error:
        st.error(error)
        return

    rows = final_state.get("result", [])
    latency_seconds = float(usage.get("latency_seconds") or 0.0)
    total_tokens = usage.get("total_tokens")
    token_text = str(total_tokens) if total_tokens is not None else "N/A"

    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    metrics_col1.metric("Latency", f"{latency_seconds:.2f}s")
    metrics_col2.metric("Rows", str(len(rows)))
    metrics_col3.metric("Total Tokens", token_text)

    st.success(f"Query succeeded: {len(rows)} rows")
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"chatbi_result_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("No rows returned.")


def main() -> None:
    st.set_page_config(page_title="ChatBI Demo", page_icon=":bar_chart:", layout="wide")
    st.title("ChatBI Streamlit Demo")
    st.caption("Ask business questions in natural language and inspect generated SQL/results.")

    if "graph" not in st.session_state:
        st.session_state.graph = build_graph()
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "history" not in st.session_state:
        st.session_state.history = []

    with st.sidebar:
        st.subheader("Session")
        st.text(f"Thread ID: {st.session_state.thread_id}")
        if st.button("New Session", use_container_width=True):
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.history = []
            st.rerun()

        if st.session_state.history:
            st.subheader("Recent Questions")
            for item in reversed(st.session_state.history[-10:]):
                st.caption(f"- {item}")

    sample_questions = [
        "What is the total order amount in 2025?",
        "Count orders by shipping city.",
        "Show total revenue by product category.",
        "Show the top 5 products by total sales.",
        "Which shipping city has the most orders?",
    ]
    selected_sample = st.selectbox("Try a sample question", [""] + sample_questions, index=0)
    default_question = selected_sample if selected_sample else ""

    question = st.text_input("Your question", value=default_question, placeholder="e.g. 本月每个品牌的销售额 Top 10")
    run_clicked = st.button("Run Query", type="primary", use_container_width=True)

    if run_clicked:
        clean_question = question.strip()
        if not clean_question:
            st.warning("Please enter a question first.")
            return

        with st.spinner("Running ChatBI pipeline..."):
            final_state, usage = _run_question(clean_question)
            st.session_state.history.append(clean_question)
        _render_result(final_state, usage)


if __name__ == "__main__":
    main()
