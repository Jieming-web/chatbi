"""
ChatBI Application - LangGraph 有状态工作流
-------------------------------------------
节点流程：
  normalize → retrieve_schema → generate_sql → check_sql
                                      ↑                ↓ (失败且 retries < 2)
                                      └────────────────┘
                                                        ↓ (成功 or retries >= 2)
                                                     respond
"""

import os
import sys

from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict

sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from core.logger import audit, new_trace_id
from response import format_roles
from response.sql_builder import SQLBuilder
from db_mcp_server.entity_normalizer import EntityNormalizer
from db_mcp_server.query_normalizer import QueryNormalizer
from db_mcp_server.schema_rag import SchemaRAG
from db_mcp_server.utils import query as db_query


# ─────────────────────────────────────────────
# State 定义
# ─────────────────────────────────────────────
class ChatBIState(TypedDict):
    question:         str
    normalized_query: str
    roles:            dict   # {metric, time, comparison, status, aggregation, limit, entity, location}
    schema_context:   dict   # {"tables": [...], "join_paths": [...]}
    generated_sql:    str    # LLM 每次生成的原始 SQL
    final_sql:        str    # check_sql 执行成功后确认的 SQL
    result:           list
    error:            str
    retries:          int



# ─────────────────────────────────────────────
# 组件初始化
# ─────────────────────────────────────────────
llm              = ChatOpenAI(
    model=settings.llm.model,
    temperature=settings.llm.temperature,
    api_key=os.environ.get("OPENAI_API_KEY"),
)
normalizer       = EntityNormalizer()
query_normalizer = QueryNormalizer(llm, normalizer)
rag              = SchemaRAG(llm=llm)
builder          = SQLBuilder(llm)


# ─────────────────────────────────────────────
# 节点定义
# ─────────────────────────────────────────────
def normalize_node(state: ChatBIState) -> dict:
    return query_normalizer.run(state["question"])


def retrieve_schema_node(state: ChatBIState) -> dict:
    schema = rag.retrieve(state["normalized_query"])
    return {"schema_context": schema}


def generate_sql_node(state: ChatBIState) -> dict:
    sql = builder.build(
        normalized_query=state["normalized_query"],
        schema_context=state["schema_context"],
        roles=state.get("roles", {}),
        error=state.get("error", ""),
        prev_sql=state.get("generated_sql", ""),
    )
    return {"generated_sql": sql, "error": ""}


def check_sql_node(state: ChatBIState) -> dict:
    try:
        result = db_query(state["generated_sql"])
        return {"result": result, "final_sql": state["generated_sql"], "error": ""}
    except Exception as e:
        return {"error": str(e), "retries": state.get("retries", 0) + 1}


def respond_node(state: ChatBIState) -> dict:
    audit({
        "question":         state["question"],
        "normalized_query": state["normalized_query"],
        "roles":            state.get("roles", {}),
        "final_sql":        state.get("final_sql", state.get("generated_sql", "")),
        "success":          not bool(state.get("error")),
        "retries":          state.get("retries", 0),
        "row_count":        len(state.get("result", [])),
        "error":            state.get("error", ""),
    })
    return state


# ─────────────────────────────────────────────
# 条件边
# ─────────────────────────────────────────────
def should_retry(state: ChatBIState) -> str:
    if state.get("error") and state.get("retries", 0) < 2:
        return "generate_sql"
    return "respond"


# ─────────────────────────────────────────────
# 构建 StateGraph
# ─────────────────────────────────────────────
def build_graph():
    graph = StateGraph(ChatBIState)
    graph.add_node("normalize",       normalize_node)
    graph.add_node("retrieve_schema", retrieve_schema_node)
    graph.add_node("generate_sql",    generate_sql_node)
    graph.add_node("check_sql",       check_sql_node)
    graph.add_node("respond",         respond_node)

    graph.set_entry_point("normalize")
    graph.add_edge("normalize",       "retrieve_schema")
    graph.add_edge("retrieve_schema", "generate_sql")
    graph.add_edge("generate_sql",    "check_sql")
    graph.add_conditional_edges("check_sql", should_retry, {
        "generate_sql": "generate_sql",
        "respond":      "respond",
    })
    graph.add_edge("respond", END)

    return graph.compile(checkpointer=InMemorySaver())


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────
def main():
    app    = build_graph()
    config = {"configurable": {"thread_id": "1"}}

    print(Fore.CYAN + Style.BRIGHT + "ChatBI Application (LangGraph StateGraph)")
    print("输入问题开始查询，输入 'q' 退出\n" + Style.RESET_ALL)

    while True:
        question = input("请输入：").strip()
        if not question:
            continue
        if question == "q":
            break

        new_trace_id()

        initial_state: ChatBIState = {
            "question":         question,
            "normalized_query": "",
            "roles":            {},
            "schema_context":   {"tables": [], "join_paths": []},
            "generated_sql":    "",
            "final_sql":        "",
            "result":           [],
            "error":            "",
            "retries":          0,
        }

        final_state = app.invoke(initial_state, config=config)

        if final_state["normalized_query"] != question:
            print(Fore.YELLOW + f"[实体标准化] {question} → {final_state['normalized_query']}" + Style.RESET_ALL)

        roles_text = format_roles(final_state.get("roles", {}))
        if roles_text:
            print(Fore.CYAN + f"[意图解析]\n{roles_text}" + Style.RESET_ALL)

        display_sql = final_state.get("final_sql") or final_state.get("generated_sql", "")
        print(Fore.BLUE + f"[SQL]\n{display_sql}" + Style.RESET_ALL)

        if final_state.get("error"):
            print(Fore.RED + f"[错误] {final_state['error']}" + Style.RESET_ALL)
        else:
            print(Fore.GREEN + f"[结果] 共 {len(final_state['result'])} 行" + Style.RESET_ALL)
            for row in final_state["result"][:5]:
                print(f"  {row}")

        retries = final_state.get("retries", 0)
        if retries > 0:
            print(Fore.YELLOW + f"[SQL Checker] 重试次数: {retries}" + Style.RESET_ALL)
        print()


if __name__ == "__main__":
    main()
