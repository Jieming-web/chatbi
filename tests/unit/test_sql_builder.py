import pytest
from unittest.mock import MagicMock

from response.sql_builder import SQLBuilder


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="SELECT 1")
    return llm


@pytest.fixture
def schema_ctx():
    return {
        "tables": [{"name": "Product", "description": "products", "ddl": "CREATE TABLE Product (ProductId INT)", "columns": ["ProductId"], "sample_rows": []}],
        "join_paths": [],
    }


def test_builder_calls_llm(mock_llm, schema_ctx):
    builder = SQLBuilder(mock_llm)
    sql = builder.build("which brand sells most", schema_ctx, {})
    assert sql == "SELECT 1"
    mock_llm.invoke.assert_called_once()


def test_builder_includes_error_in_prompt(mock_llm, schema_ctx):
    builder = SQLBuilder(mock_llm)
    builder.build("retry query", schema_ctx, {}, error="syntax error", prev_sql="SELECT bad")
    prompt_text = mock_llm.invoke.call_args[0][0][0].content
    assert "syntax error" in prompt_text
    assert "SELECT bad" in prompt_text


def test_builder_strips_markdown_fences(mock_llm, schema_ctx):
    mock_llm.invoke.return_value = MagicMock(content="```sql\nSELECT 1\n```")
    builder = SQLBuilder(mock_llm)
    sql = builder.build("q", schema_ctx, {})
    assert sql == "SELECT 1"
