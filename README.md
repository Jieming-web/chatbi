# ChatBI

ChatBI is a natural-language interface for querying an e-commerce SQLite database. Users can ask questions in English, and the system generates SQL, executes the query, and returns the result in a Streamlit web app.

The project uses Streamlit for the demo interface, LangGraph for the workflow, schema-aware retrieval for database context, and SQLite as the backend database.

---

## 1. Project Overview

The goal of this project is to make database querying easier for users who may not know SQL. Instead of writing SQL manually, users can enter a business question in natural language.

For example:

```text
What is the total order amount in 2025?
Count orders by shipping city.
Show total revenue by product category.
Show the top 5 products by total sales.
Which shipping city has the most orders?
```

The system does not generate SQL directly from the question only. It first checks the database schema, retrieves relevant tables and columns, and then generates SQL based on that context. The generated SQL is executed on the local SQLite database.

---

## 2. Main Features

- Natural-language question input
- Multi-turn conversation with automatic reference resolution
- Streamlit web interface
- SQLite database query execution
- Schema-aware retrieval before SQL generation
- Entity and query normalization with typo correction
- SQL generation using an LLM
- SQL execution checking and retry (up to 2 retries)
- Fallback guidance when schema is empty or SQL repeatedly fails
- Result table display
- CSV download option
- ETL pipeline for bulk and incremental data loading
- Evaluation scripts for retrieval and SQL execution

---

## 3. System Workflow

The main LangGraph workflow consists of 7 nodes:

```text
resolve_query
     |
     v
normalize
     |
     v
retrieve_schema
     |
     v
validate_schema -----(empty schema)-----> respond
     |
     v
generate_sql <---------+
     |                 |
     v                 |
check_sql ----(error, retries < 2)--------+
     |
     v (success or retries >= 2)
respond
```

| Node | Description |
|---|---|
| `resolve_query` | Expands follow-up questions into standalone queries using conversation history |
| `normalize` | Extracts intent roles and normalizes entity names |
| `retrieve_schema` | Retrieves relevant tables and join paths from the schema |
| `validate_schema` | Short-circuits to `respond` with guidance if no tables were retrieved |
| `generate_sql` | Generates SQLite SQL using the LLM and schema context |
| `check_sql` | Executes the SQL; on failure, increments retry count and loops back |
| `respond` | Finalizes the response, appends to history, writes the audit log |

---

## 4. Repository Structure

```text
chatbi/
├── streamlit_app.py              # Streamlit web demo
├── client.py                     # LangGraph pipeline and CLI entry point
├── etl_globalorder.py            # Bulk ETL: GlobalOrder → normalized tables
├── etl_increment.py              # Incremental ETL: weekly CSV → normalized tables
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose setup
├── CHEAT_SHEET.md                # Notes and command reference
├── proposal.md                   # Project proposal document
├── proposal.ipynb                # Project proposal notebook
│
├── data/
│   ├── Ecommerce.db              # SQLite database
│   ├── Ecommerce_backup.db       # Backup database
│   ├── Ecommerce_Sqlite.sql      # SQL schema / dump file
│   └── ecommerce_sample_1000.csv # Sample data
│
├── config/
│   ├── settings.py               # Settings loader
│   └── settings.yaml             # Project configuration
│
├── core/
│   ├── interfaces/               # Base interfaces
│   ├── registry.py               # Component registry
│   ├── logger.py                 # Logging and audit trail
│   └── types.py                  # Shared data classes
│
├── db_mcp_server/
│   ├── server.py                 # MCP server (tools, resources, prompts)
│   ├── schema_rag.py             # Schema retrieval and join-path logic
│   ├── entity_normalizer.py      # Entity normalization and typo correction
│   ├── query_normalizer.py       # Query normalization and role extraction
│   └── utils.py                  # SQLite utilities
│
├── impl/
│   ├── retrievers/               # dense.py, bm25.py, hybrid.py
│   ├── rerankers/                # llm_rerank.py, cross_encoder.py
│   └── llms/                     # openai_llm.py, ollama_llm.py
│
├── response/
│   ├── prompts.py                # SQL generation prompt
│   ├── sql_builder.py            # SQL generation logic
│   └── schema_formatter.py       # Schema formatting helpers
│
├── evals/
│   ├── run_eval.py               # Evaluation runner
│   ├── golden_queries.jsonl      # Standard evaluation questions
│   ├── golden_queries_multijoin.jsonl  # Multi-join evaluation questions
│   ├── golden_queries_natural.jsonl    # Typo/entity normalization questions
│   ├── metrics/                  # Metric computation helpers
│   └── reports/                  # Saved evaluation reports
│
├── tests/
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
│
└── scripts/
    ├── mine_aliases.py           # Alias mining script
    ├── start_api.sh
    ├── start_api.ps1
    └── start_streamlit.sh
```

---

## 5. Database

The project uses a local SQLite database at `data/Ecommerce.db`.

Main tables include:

| Table | Description |
|---|---|
| `Category` | Product category information, supports parent-child hierarchy |
| `Product` | Product information such as name, brand, price, and stock |
| `Customer` | Customer information such as city, province, segment, age, gender, and loyalty score |
| `Order_` | Order-level information such as date, status, amount, priority, and shipping location |
| `OrderItem` | Item-level order information |
| `OrderExtra` | Extra order information such as payment method, shipping method, device type, and fraud risk |
| `Review` | Product reviews and ratings |
| `SKU` | Product variant information |
| `GlobalOrder` | Flat global order table used as the source for ETL |

Important notes:

- The order table is named `Order_` because `ORDER` is a SQL reserved word.
- Total revenue is stored in the `TotalAmount` column of `Order_`.
- Dates are stored in `YYYY-MM-DD` format.
- Order status values include `Delivered`, `Returned`, `Cancelled`, `Shipped`, and `Pending`.
- `Category` has a self-referencing `ParentCategoryId` column for sub-categories.

---

## 6. Methodology

### 6.1 Multi-Turn Query Resolution

When conversation history exists, the `resolve_query` node uses the LLM to expand follow-up questions into standalone queries. For example, "show the same for Austin" becomes a complete self-contained question based on prior context. Up to 5 turns of history are kept per session.

### 6.2 Query Normalization

The system processes the user's question and extracts structured intent roles:

- `metric` — what to measure
- `time` — time period filter
- `comparison` — ranking or comparison type
- `status` — order or delivery status
- `aggregation` — SUM, AVG, COUNT, etc.
- `limit` — top-N constraint
- `entity` — product, brand, or category name (with typo correction)
- `location` — city, state, or country

### 6.3 Schema Retrieval

After normalization, the system retrieves relevant schema information. This includes tables, columns, descriptions, and possible join paths using Reciprocal Rank Fusion over:

- Dense retrieval (sentence-transformers, `all-MiniLM-L6-v2`)
- BM25 retrieval
- Hybrid retrieval combining both

If the retrieved schema is empty, the pipeline short-circuits and returns rephrasing guidance to the user instead of generating SQL.

### 6.4 SQL Generation

The SQL builder uses the normalized question and retrieved schema context to generate SQLite SQL. The prompt includes database-specific rules such as:

- use exact table and column names from the schema
- use `Order_` instead of `Order`
- follow the `YYYY-MM-DD` date format
- output only SQL with no explanation

### 6.5 SQL Execution Check and Retry

The generated SQL is executed on `data/Ecommerce.db`. If it fails, the error message is fed back to the SQL generation node and the system retries. After 2 failed retries, the pipeline proceeds to `respond` with a fallback hint.

Three fallback scenarios are handled:

- **Empty schema** — no relevant tables found; suggests rephrasing
- **Repeated SQL failure** — SQL generation could not succeed; suggests simplifying the question
- **Empty result** — SQL ran but returned no rows; suggests checking entity names or time range

### 6.6 Result Display

The Streamlit app displays:

- resolved and normalized question
- intent analysis (extracted roles)
- generated SQL
- query result table
- latency, row count, and token usage
- retry count if SQL needed correction
- CSV download button

---

## 7. Installation

### 7.1 Clone the Repository

```bash
git clone <your-repository-url>
cd chatbi
```

### 7.2 Create a Virtual Environment

For macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 7.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 7.4 Set the API Key

The SQL generation pipeline requires an OpenAI API key by default.

For macOS or Linux:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

For Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

The model can be changed in `config/settings.yaml`. To use a local model instead, see [Section 9 — Local Model](#9-local-model-ollama).

---

## 8. How to Run

### 8.1 Run the Streamlit App

```bash
streamlit run streamlit_app.py
```

Then open the local URL shown in the terminal (default: `http://localhost:8501`).

### 8.2 Run the CLI Client

```bash
python client.py
```

The CLI supports multi-turn conversation. Type `q` to quit.

Example session:

```text
Ask: Show total revenue by product category.
Ask: Which of those has the highest return rate?   ← follow-up resolved automatically
Ask: q
```

### 8.3 Run the MCP Server

```bash
python db_mcp_server/server.py
```

The MCP server is built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), a standard that allows AI agents such as Claude to discover and call tools at runtime. The server exposes the ChatBI pipeline as a set of structured tools so that a Claude agent (or any MCP-compatible client) can query the database, retrieve schema context, and normalize questions without needing to know the underlying implementation.

This design keeps the pipeline logic decoupled from any specific frontend or agent framework, and makes it straightforward to plug ChatBI into a larger agentic workflow in the future.

The MCP server exposes:

**Tools:**
- `get_table_schema` — returns the full database schema
- `run_sql` — executes a SQL query
- `normalize_query` — runs query normalization on a question
- `retrieve_schema` — retrieves relevant schema for a question

**Resources:**
- `schema://tables` — table descriptions
- `schema://relationships` — join paths between tables
- `examples://sql` — example SQL queries

**Prompts:**
- `analyze_query` — query analysis prompt template

---

## 9. Local Model (Ollama)

The project includes an Ollama LLM wrapper at `impl/llms/ollama_llm.py` for running a local model instead of calling the OpenAI API. The default model is `qwen2.5:3b`.

To use it:

```bash
pip install langchain-ollama
```

Then update `config/settings.yaml`:

```yaml
llm:
  model: "qwen2.5:3b"
```

And register the `ollama` LLM type in the component registry.

---

## 10. Configuration

Settings are stored in `config/settings.yaml`.

```yaml
embedding:
  model_name: "all-MiniLM-L6-v2"

retriever:
  type: "hybrid"
  top_k: 10
  final_tables: 6

reranker:
  type: "llm"
  top_k: 6
  model_name: null

llm:
  model: "gpt-4o"
  temperature: 0

db:
  path: "data/Ecommerce.db"

mcp:
  port: 8787
  fallback_on_error: true
```

Useful options:

- `retriever.type`: `dense`, `bm25`, or `hybrid`
- `reranker.type`: `llm` or `cross_encoder`
- `llm.model`: model name
- `db.path`: SQLite database path (relative to project root)

---

## 11. ETL Pipeline

### 11.1 Bulk Load from GlobalOrder

Populates normalized tables (`Customer`, `Product`, `Order_`, `OrderItem`, etc.) from the flat `GlobalOrder` table.

```bash
python etl_globalorder.py
```

### 11.2 Incremental Weekly Load

Loads a new weekly CSV file in GlobalOrder format into the normalized tables.

```bash
python etl_increment.py --file weekly_2026_W17.csv
```

Expected CSV columns include `order_id`, `order_date`, `order_status`, `customer_id`, `product_id`, `unit_price_usd`, `quantity`, `discount_percent`, `payment_method`, `shipping_method`, `rating`, and others.

---

## 12. Evaluation

The project includes evaluation scripts in `evals/run_eval.py` with three golden query sets:

| File | Description |
|---|---|
| `golden_queries.jsonl` | Standard single-table and simple join queries |
| `golden_queries_multijoin.jsonl` | Complex multi-join queries |
| `golden_queries_natural.jsonl` | Queries with entity typos for normalization testing |

### 12.1 Schema Retrieval Evaluation

```bash
python -m evals.run_eval --mode schema
```

Checks whether the retriever returns the expected tables. Does not require an API key.

### 12.2 Full Pipeline Evaluation

```bash
python -m evals.run_eval --mode full
```

Runs the full LangGraph pipeline and compares generated SQL results against golden SQL results (Execution Match). Requires `OPENAI_API_KEY`.

### 12.3 Entity Normalization Evaluation

```bash
python -m evals.run_eval --mode entity --golden natural
```

Checks whether misspelled entity names are corrected. Requires `OPENAI_API_KEY`.

### 12.4 Configuration Comparison

```bash
python -m evals.run_eval --config dense llm
python -m evals.run_eval --config hybrid llm
python -m evals.run_eval --config hybrid cross_encoder
```

Reports are saved to `evals/reports/`.

---

## 13. Testing

Run all tests:

```bash
pytest
```

Run unit tests only:

```bash
pytest tests/unit
```

Run integration tests only:

```bash
pytest tests/integration
```

---

## 14. Docker

The Docker Compose setup runs the Streamlit frontend on port 8501 with an optional Nginx reverse proxy.

```bash
docker compose up --build
```

Set the API key before building if required by your LLM configuration:

```bash
export DEEPSEEK_API_KEY="your_api_key_here"
docker compose up --build
```

The database is mounted as a read-only volume:

```yaml
volumes:
  - ./data/Ecommerce.db:/app/Ecommerce.db:ro
```

---

## 15. Example

Question:

```text
Show total revenue by product category.
```

Generated SQL:

```sql
SELECT c.Name AS category,
       SUM(o.TotalAmount) AS revenue
FROM Order_ o
JOIN OrderItem oi ON o.OrderId = oi.OrderId
JOIN Product p ON oi.ProductId = p.ProductId
JOIN Category c ON p.CategoryId = c.CategoryId
GROUP BY c.Name
ORDER BY revenue DESC;
```

The result is shown as a table in the Streamlit app with a CSV download button.

---

## 16. Limitations

- The full pipeline requires an LLM API key unless a local Ollama model is configured.
- A generated SQL query may run successfully but still not fully match the user's intended meaning.
- Very vague questions may need clearer wording.
- The prompts and normalization logic are designed for this e-commerce database schema.
- Automatic chart generation is not implemented; results are shown as tables only.

---

## 17. Future Improvements

- **Agent integration** — connect the MCP server to a Claude agent so that Claude can autonomously handle multi-step business questions, call tools, and iterate on results without a fixed pipeline
- Add automatic chart generation for numeric results
- Improve SQL validation beyond execution checking
- Support other databases such as PostgreSQL or MySQL
- Add more golden queries to the evaluation sets
- Improve the Streamlit interface with richer formatting

---

## 18. Development Notes

Files to keep out of version control:

```text
.venv/
__pycache__/
.pytest_cache/
.DS_Store
.env
chatbi_audit.log
```

Do not commit API keys. Use environment variables for all secrets.
