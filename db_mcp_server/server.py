import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from config import settings
from utils import query, DB_PATH

mcp = FastMCP("Ecommerce-DB-Query-Mcp-Server")

_ALL_TABLES = [
    "Category", "Product", "Customer",
    "Order_", "OrderItem", "Review",
    "SKU", "OrderExtra", "GlobalOrder",
]


# ─── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_table_schema() -> str:
    """Return the SQLite schema for all ecommerce tables. Call this before generating SQL."""
    table_schema = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for table in _ALL_TABLES:
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = cursor.fetchall()
        col_defs = ", ".join(
            f"{col[1]} {col[2]}{'  PRIMARY KEY' if col[5] else ''}"
            for col in columns
        )
        cursor.execute(f'SELECT * FROM "{table}" LIMIT 2')
        rows = cursor.fetchall()
        col_names = [col[1] for col in columns]
        example = ""
        if rows:
            example = "\n  -- Example: " + " | ".join(col_names) + "\n"
            for row in rows:
                example += "  --        " + " | ".join(str(v) for v in row) + "\n"
        table_schema.append(f'CREATE TABLE "{table}" ({col_defs}){example}')
    conn.close()
    return "\n\n".join(table_schema)


@mcp.tool()
def run_sql(sql: str) -> str:
    """Execute one SQLite query against the ecommerce data. Note: the orders table is named Order_."""
    try:
        result = query(sql)
        return str(result)
    except Exception as e:
        return f"SQL execution error: {str(e)}. Please fix the query and try again."


@mcp.tool()
def normalize_query(question: str) -> str:
    """Normalize user questions by correcting brand/product/city typos and returning roles."""
    from entity_normalizer import EntityNormalizer
    normalizer = EntityNormalizer()
    noun_phrases, time_phrases = normalizer._extract_phrases(question)
    result = normalizer.get_candidates(noun_phrases, time_phrases)
    return str(result)


@mcp.tool()
def retrieve_schema(question: str) -> str:
    """Retrieve the most relevant schema for a natural-language question and return DDL plus JOIN paths."""
    from db_mcp_server.schema_rag import SchemaRAG
    rag = SchemaRAG()
    ctx = rag.retrieve(question)
    lines = []
    for t in ctx["tables"]:
        lines.append(t["ddl"])
        if t.get("description"):
            lines.append(f"-- {t['description']}")
    if ctx["join_paths"]:
        lines.append("\n-- JOIN paths:")
        for jp in ctx["join_paths"]:
            lines.append(f"--   {jp}")
    return "\n".join(lines)


# ─── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("schema://tables")
def schema_tables() -> str:
    """Full schema for all 9 tables."""
    return get_table_schema()


@mcp.resource("schema://relationships")
def schema_relationships() -> str:
    """List of foreign-key relationships."""
    from db_mcp_server.schema_rag import FOREIGN_KEYS
    lines = ["# Foreign Key Relationships\n"]
    for src_table, src_col, dst_table, dst_col in FOREIGN_KEYS:
        lines.append(f"- {src_table}.{src_col} → {dst_table}.{dst_col}")
    return "\n".join(lines)


@mcp.resource("examples://sql")
def sql_examples() -> str:
    """Few-shot SQL examples."""
    return """# SQL Examples

## Example 1: Category revenue ranking
Question: Which category has the highest revenue?
SQL:
SELECT c.Name AS category, SUM(oi.UnitPrice * oi.Quantity * oi.Discount) AS revenue
FROM OrderItem oi
JOIN Product p ON oi.ProductId = p.ProductId
JOIN Category c ON p.CategoryId = c.CategoryId
GROUP BY c.Name
ORDER BY revenue DESC
LIMIT 1;

## Example 2: Frequent buyers
Question: Which customers have placed more than 3 orders?
SQL:
SELECT cu.Name, cu.City, COUNT(o.OrderId) AS order_count
FROM Customer cu
JOIN Order_ o ON cu.CustomerId = o.CustomerId
GROUP BY cu.CustomerId
HAVING COUNT(o.OrderId) > 3
ORDER BY order_count DESC;

## Example 3: Return rate by brand
Question: What is the return rate for each brand?
SQL：
SELECT p.Brand,
       ROUND(SUM(CASE WHEN o.Status = 'returned' THEN 1.0 ELSE 0 END) / COUNT(*), 4) AS return_rate
FROM Order_ o
JOIN OrderItem oi ON o.OrderId = oi.OrderId
JOIN Product p ON oi.ProductId = p.ProductId
GROUP BY p.Brand
ORDER BY return_rate DESC;
"""


# ─── Prompts ──────────────────────────────────────────────────────────────────

@mcp.prompt()
def analyze_query(question: str) -> str:
    """Return a structured analysis workflow prompt for a given user question."""
    return f"""You are an ecommerce data analysis assistant. Answer the user's question with the following steps:

User question: {question}

Steps:
1. Call the normalize_query tool to standardize entity terms.
2. Call the retrieve_schema tool to fetch the relevant schema.
3. Generate SQL using the schema and JOIN paths.
4. Call the run_sql tool to execute the SQL and return the result.
5. Explain the result in natural language.

Notes:
- The orders table is named Order_.
- Amount calculation: UnitPrice * Quantity * Discount
- Date format: 'YYYY-MM-DD'
"""


if __name__ == "__main__":
    mcp.settings.port = settings.mcp.port
    mcp.run(transport='sse')
