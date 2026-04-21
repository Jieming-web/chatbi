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
    """获取电商数据库所有表的 SQLite Schema，生成SQL之前必须先调用该工具获取完整表结构"""
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
            example = "\n  -- 示例: " + " | ".join(col_names) + "\n"
            for row in rows:
                example += "  --        " + " | ".join(str(v) for v in row) + "\n"
        table_schema.append(f'CREATE TABLE "{table}" ({col_defs}){example}')
    conn.close()
    return "\n\n".join(table_schema)


@mcp.tool()
def run_sql(sql: str) -> str:
    """执行 SQLite SQL 语句查询电商数据，一次仅能执行一句 SQL！注意：订单表名为 Order_（加下划线）"""
    try:
        result = query(sql)
        return str(result)
    except Exception as e:
        return f"执行SQL错误：{str(e)}，请修正后重新发起。"


@mcp.tool()
def normalize_query(question: str) -> str:
    """对用户问题做实体标准化：纠正品牌/商品/城市拼写错误，返回标准化后的查询和角色分类"""
    from entity_normalizer import EntityNormalizer
    normalizer = EntityNormalizer()
    noun_phrases, time_phrases = normalizer._extract_phrases(question)
    result = normalizer.get_candidates(noun_phrases, time_phrases)
    return str(result)


@mcp.tool()
def retrieve_schema(question: str) -> str:
    """根据自然语言问题检索最相关的表结构（两阶段 RAG），返回 DDL + JOIN 路径"""
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
    """完整表结构（所有 9 张表的 DDL）"""
    return get_table_schema()


@mcp.resource("schema://relationships")
def schema_relationships() -> str:
    """外键关系列表"""
    from db_mcp_server.schema_rag import FOREIGN_KEYS
    lines = ["# Foreign Key Relationships\n"]
    for src_table, src_col, dst_table, dst_col in FOREIGN_KEYS:
        lines.append(f"- {src_table}.{src_col} → {dst_table}.{dst_col}")
    return "\n".join(lines)


@mcp.resource("examples://sql")
def sql_examples() -> str:
    """Few-shot SQL 示例"""
    return """# SQL Examples

## 示例1：品类销售额排行
问题：哪个品类的销售额最高？
SQL：
SELECT c.Name AS 品类, SUM(oi.UnitPrice * oi.Quantity * oi.Discount) AS 销售额
FROM OrderItem oi
JOIN Product p ON oi.ProductId = p.ProductId
JOIN Category c ON p.CategoryId = c.CategoryId
GROUP BY c.Name
ORDER BY 销售额 DESC
LIMIT 1;

## 示例2：高频购买客户
问题：下单超过3次的客户有哪些？
SQL：
SELECT cu.Name, cu.City, COUNT(o.OrderId) AS 下单次数
FROM Customer cu
JOIN Order_ o ON cu.CustomerId = o.CustomerId
GROUP BY cu.CustomerId
HAVING COUNT(o.OrderId) > 3
ORDER BY 下单次数 DESC;

## 示例3：品牌退货率
问题：各品牌退货率？
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
    """标准分析流程模板：给定用户问题，生成结构化的分析步骤提示"""
    return f"""你是电商数据分析助手，请按以下步骤回答用户问题：

用户问题：{question}

步骤：
1. 调用 normalize_query 工具标准化实体词
2. 调用 retrieve_schema 工具获取相关表结构
3. 根据表结构和 JOIN 路径生成 SQL
4. 调用 run_sql 工具执行 SQL 并返回结果
5. 用自然语言解释查询结果

注意：
- 订单表名为 Order_（加下划线）
- 金额计算：UnitPrice × Quantity × Discount
- 时间格式：'YYYY-MM-DD'
"""


if __name__ == "__main__":
    mcp.settings.port = settings.mcp.port
    mcp.run(transport='sse')
