"""
Integration tests — does not require OPENAI_API_KEY.
Tests the schema retrieval stage of the pipeline (normalize + retrieve_schema).
"""
import pytest

from db_mcp_server.schema_rag import SchemaRAG


@pytest.fixture(scope="module")
def rag():
    return SchemaRAG(llm=None)


@pytest.mark.parametrize("question,expected_tables", [
    ("top 5 brands by revenue", ["OrderItem", "Product"]),
    ("average rating for Apple products", ["Review", "Product"]),
    ("orders shipped to London", ["Order_"]),
    ("most common payment method", ["OrderExtra"]),
    ("top US states by sales", ["GlobalOrder"]),
    ("top 5 brands by revenue in Q1 2025", ["Order_", "OrderItem", "Product"]),
    ("average fraud risk score by customer segment", ["Order_", "OrderExtra", "Customer"]),
    ("average delivery days for electronics orders", ["OrderExtra", "Order_", "OrderItem", "Product", "Category"]),
    ("top 5 sub-categories by revenue from high loyalty customers", ["Order_", "OrderItem", "Product", "Category", "Customer"]),
])
def test_schema_retrieval_includes_key_tables(rag, question, expected_tables):
    ctx = rag.retrieve(question)
    retrieved = {t["name"] for t in ctx["tables"]}
    for expected in expected_tables:
        assert expected in retrieved, f"Missing '{expected}' for: {question}"


def test_schema_retrieval_returns_join_paths(rag):
    ctx = rag.retrieve("top 5 customers by total spend")
    assert "tables" in ctx
    assert "join_paths" in ctx
    assert isinstance(ctx["tables"], list)
    assert isinstance(ctx["join_paths"], list)


def test_schema_retrieval_table_has_ddl(rag):
    ctx = rag.retrieve("count orders by status")
    assert len(ctx["tables"]) > 0
    for t in ctx["tables"]:
        assert "ddl" in t
        assert t["ddl"].startswith("CREATE TABLE")
