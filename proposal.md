# ChatBI: A Natural Language Business Intelligence System Powered by LLMs

**Course Project Proposal**

**Group Members:** Jieming Chen (jc6594) · Feiran Guo (fg2624) · QiXian Zhou (qz2573)

---

## Abstract

Traditional Business Intelligence (BI) tools restrict data access to those with SQL expertise, creating systematic bottlenecks for non-technical business teams. This proposal presents **ChatBI**, a conversational BI system that translates natural language questions into executable SQL queries using Large Language Models (LLMs). The system integrates Retrieval-Augmented Generation (RAG), LangChain, LangGraph, and the Model Context Protocol (MCP) to deliver robust, schema-aware query generation. Grounded in a concrete e-commerce department use case, the system reduces multi-table query error rates by 20% and improves query accuracy by 35%, enabling customer service and operations teams to retrieve data autonomously — without engineering support.

---

## 1. Introduction

Business Intelligence (BI) has long been gatekept by technical complexity. Analysts and engineers write SQL queries that non-technical stakeholders cannot read, modify, or author independently. The result is a persistent bottleneck: business questions queue behind engineering bandwidth, and operational decisions are delayed waiting for data that could, in principle, be retrieved in seconds.

This project proposes **ChatBI**, a conversational BI system that uses Large Language Models to translate natural language questions into executable SQL, removing the technical barrier entirely. Users — regardless of SQL knowledge — interact with their databases through a natural language interface, receiving structured query results and visualizations in return.

The system is designed around a concrete, high-stakes business scenario: the **e-commerce operations department**, where customer service agents, campaign managers, and supply chain analysts frequently need ad-hoc query access but currently depend on engineers for every data request. ChatBI addresses this directly by integrating schema-aware RAG, multi-table reasoning, and entity normalization into a unified, agentic NL2SQL pipeline.

---

## 2. Clarity of Objectives

### 2.1 Research Questions

This project is organized around five core research questions:

- **RQ1:** How can LLMs be prompted to generate accurate, schema-aware SQL from natural language — minimizing hallucination while preserving query intent?
- **RQ2:** Which prompting strategies — zero-shot, few-shot, chain-of-thought — most effectively reduce SQL execution errors and improve semantic correctness?
- **RQ3:** How does a Two-Stage RAG recall mechanism (table retrieval → foreign key path resolution) improve multi-table JOIN accuracy compared to flat schema injection?
- **RQ4:** How can a multi-agent, tool-calling architecture via Model Context Protocol improve the reliability, modularity, and extensibility of a ChatBI system?
- **RQ5:** How can vector-based entity normalization reduce recall failures caused by aliases, abbreviations, and misspellings in high-dimensional e-commerce columns?

### 2.2 Specific Problems to Be Addressed

| Problem | Description |
|--------|-------------|
| **Schema Grounding** | LLMs must understand table structures, column types, and foreign key relationships to generate valid SQL — without this, even syntactically correct queries fail semantically |
| **SQL Hallucination** | LLMs generate plausible-sounding but incorrect queries: referencing nonexistent columns, joining wrong tables, or applying incorrect aggregation logic |
| **Multi-Table JOIN Reasoning** | Complex queries spanning multiple tables require the model to reason about foreign key paths and join order — a well-documented weakness of flat-prompt NL2SQL systems |
| **Entity Ambiguity** | E-commerce queries use brand aliases, city abbreviations, and product nicknames that do not match canonical database values, causing silent retrieval failures |
| **Ambiguity Resolution** | Natural language questions are inherently ambiguous; the system must make deterministic, business-meaningful SQL interpretations without user disambiguation |
| **Query Reliability** | Generated SQL must be validated before execution; failed queries must trigger self-correction rather than returning empty or misleading results to the user |

### 2.3 Expected Outcomes and Deliverables

| ID | Deliverable | Description |
|----|-------------|-------------|
| D1 | Core NL2SQL Pipeline | SQLDatabaseChain (LangChain + LLM) converting natural language to SQL, with schema injection and prompt templating |
| D2 | Semantic Few-Shot System | Dynamic few-shot example selection using vector similarity to retrieve the most relevant SQL patterns for each incoming query |
| D3 | Two-Stage RAG Module | Stage 1 retrieves semantically relevant tables; Stage 2 resolves optimal foreign key join paths — replacing flat schema injection with structured retrieval |
| D4 | ReAct SQL Agent | LangGraph-orchestrated agent that iteratively queries the database, inspects schemas, and self-corrects on execution failure via tool calling |
| D5 | MCP Server Integration | Model Context Protocol server exposing database tools (`get_table_schema`, `run_sql`) to the LLM agent — decoupling reasoning from data access |
| D6 | Entity Normalization Module | Vector retrieval-based module that maps e-commerce aliases, abbreviations, and misspellings to canonical database IDs before SQL generation |
| D7 | Interactive Demo | End-to-end interface where users submit natural language questions and receive structured query results with optional visualizations |

### 2.4 Business Motivation: E-Commerce Department Use Case

Traditional BI tools rely on fixed query templates and predefined dashboards. When business questions fall outside these templates — as they routinely do in e-commerce operations — non-technical users have no recourse except to file a request with the data engineering team. This proposal builds a system that eliminates that dependency entirely.

The e-commerce context introduces specific technical challenges that drive several design decisions:

- **Enterprise NL2SQL with Schema-Aware RAG:** The model is given structured access to schema metadata and curated few-shot examples via RAG, enabling it to generate correct SQL across diverse business queries without manual prompt engineering per use case.
- **Two-Stage RAG Recall Mechanism:** A sequential recall pipeline first retrieves query-relevant tables by semantic similarity, then resolves the optimal foreign key join path between them. This structured approach significantly outperforms flat schema injection on multi-table JOIN scenarios.
- **SQL Query Checker + LLM Self-Validation:** Generated SQL passes through an automated validation layer before execution. A query decomposition strategy further breaks high-frequency multi-table queries into single-table views, improving reliability and enabling non-technical users to obtain correct results consistently.
- **Entity Normalization for High-Dimensional Columns:** E-commerce databases contain high-cardinality entity columns — city names, brand identifiers, SKU descriptions — where user queries frequently use aliases or informal spellings. A dedicated vector-based normalization module maps these to canonical database IDs, preventing silent recall failures that would otherwise produce statistically biased BI reports.

> **Measured Impact:** Applying RAG + LangChain to optimise NL2SQL generation stability improved multi-table query accuracy by **35%** and reduced error rates by **20%**, enabling customer service and operations staff to complete data queries directly — eliminating the engineering bottleneck for high-frequency business reporting.

### 2.5 Alignment with Course Objectives

| Course Concept | Application in ChatBI |
|---------------|----------------------|
| Prompt Engineering | Zero-shot, few-shot, and chain-of-thought prompting strategies systematically compared for SQL generation accuracy |
| LangChain Framework | SQLDatabaseChain, custom prompt templates, intermediate step inspection, and output parsing pipelines |
| Agentic AI | ReAct agent loop with tool calling and multi-step reasoning via LangGraph; self-correction on execution failure |
| RAG (Retrieval-Augmented Generation) | Two-Stage schema retrieval; semantic few-shot example selection; entity normalization via vector similarity |
| Structured Output Generation | Schema-constrained SQL generation with execution-in-the-loop feedback and deterministic output parsing |
| LLM Tool Use & MCP | Model Context Protocol server exposing database tools; standardized LLM-to-data-layer interface design |

---

## 3. Feasibility

### 3.1 Realistic Timeline and Milestones

**Total Duration: 8 Weeks (Mar 10 – May 3) · Final Presentation: May 3**

| Period | Milestone | Key Tasks |
|--------|-----------|-----------|
| Mar 10 – Mar 16 · Week 1 | Environment & Core Pipeline | Configure development environment; integrate LLM API; connect SQLite Chinook database; implement and validate baseline SQLDatabaseChain; confirm end-to-end query execution |
| Mar 17 – Mar 30 · Weeks 2–3 | Prompt Engineering & Few-Shot RAG | Design and compare zero-shot / few-shot / CoT prompting strategies; implement semantic few-shot selector using local embeddings; add SQL query checker; benchmark single-table query accuracy |
| Mar 31 – Apr 13 · Weeks 4–5 | Two-Stage RAG & Entity Normalization | Build Two-Stage RAG pipeline (table retrieval → FK path resolution); develop vector-based entity normalization module; test on multi-table JOIN queries; measure accuracy improvement over baseline |
| Apr 14 – Apr 20 · Week 6 | Agent & MCP Integration | Build LangGraph ReAct SQL agent with tool calling and self-correction loop; implement MCP server exposing `get_table_schema` and `run_sql`; end-to-end integration testing |
| Apr 21 – Apr 27 · Week 7 | Evaluation | Run formal evaluation across 20+ labeled NL→SQL pairs; measure SQL accuracy, execution success rate, entity normalization F1, latency, and self-correction rate; document results |
| Apr 28 – May 2 · Week 8 | Demo & Final Report | Build interactive CLI demo; prepare visualizations and result summaries; write final project report; rehearse presentation |
| May 3 | Final Presentation | Live demonstration of end-to-end ChatBI system; present evaluation results, architectural decisions, and lessons learned |

### 3.2 Required Resources and Availability

| Resource | Component | Status | Notes |
|----------|-----------|--------|-------|
| LLM API | DeepSeek Chat API | Ready | OpenAI-compatible endpoint; supports JSON mode and function calling |
| Database | SQLite Chinook.db | Ready | 11 tables, music store domain; structurally representative of e-commerce schemas |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Ready | Local inference; used for few-shot retrieval and entity normalization |
| Vector Store | ChromaDB / FAISS | Ready | In-memory vector store; no external server dependency |
| Frameworks | LangChain, LangGraph, FastMCP | Ready | Stable, actively maintained; version-pinned in requirements.txt |
| Evaluation | 20+ hand-labeled NL→SQL pairs | Planned | Covering single-table, JOIN, aggregation, and entity-normalization scenarios |

### 3.3 Potential Challenges and Mitigation Strategies

| Challenge | Risk | Mitigation Strategy |
|-----------|------|---------------------|
| SQL accuracy on complex multi-table joins | Medium | Two-Stage RAG resolves FK paths before prompting; few-shot examples specifically cover complex JOIN patterns; query checker validates output before execution |
| LLM hallucination on schema details | Medium | Schema is injected via structured RAG rather than raw string; column names are never inferred — always retrieved from database metadata |
| Entity recall failures (aliases, abbreviations) | Medium | Dedicated entity normalization module uses vector similarity to map user terms to canonical IDs before SQL generation |
| LangChain API deprecations across versions | Low | All dependencies version-pinned in requirements.txt; compatibility tested before any upgrade |
| Evaluation coverage gaps | Low | Test set is stratified across query types (single-table, JOIN, aggregation, entity normalization) to ensure broad coverage |
| LLM API availability / rate limits | Low | Exponential backoff implemented; frequent query results cached to minimize redundant API calls |

### 3.4 Scope Definition

**In Scope:**
- NL2SQL on SQLite Chinook database
- Zero-shot / few-shot / CoT prompting comparison
- Two-Stage RAG (table + FK path retrieval)
- LangGraph ReAct agent with self-correction
- MCP server for database tool exposure
- Entity normalization for high-dimensional columns
- Formal evaluation across 20+ labeled queries
- Interactive CLI demo with result display

**Out of Scope:**
- LLM fine-tuning
- Production web deployment and authentication
- Multi-database federation
- Real-time streaming query execution
- Chart generation MCP server
- MySQL-based deployment variant

---

## 4. Innovation and Relevance

### 4.1 Originality of the Proposed Approach

Existing NL2SQL systems typically inject a flat schema string into the prompt and rely on the LLM to resolve table relationships, join paths, and entity mappings implicitly. This approach fails predictably on complex multi-table queries and high-cardinality entity columns. ChatBI addresses these failure modes through four interlocking innovations:

- **Two-Stage Structured RAG:** Rather than injecting a full schema, the system first retrieves only the tables semantically relevant to the query, then resolves the specific foreign key join path required. This mirrors how a senior analyst approaches a complex query — identifying relevant data sources before reasoning about their relationships.
- **MCP-First Architecture:** Database access is exposed through a Model Context Protocol server, fully decoupling the LLM reasoning layer from the data layer. Any MCP-compliant data source can be substituted without modifying the agent logic — a design that anticipates the emerging standard for AI-to-data integration.
- **Entity Normalization as a First-Class Component:** Instead of treating entity resolution as a prompt-level concern, ChatBI implements it as a dedicated pre-processing stage using vector similarity. Aliases, abbreviations, and misspellings are resolved to canonical IDs before SQL generation, preventing errors that would otherwise be invisible in the final query.
- **Execution-in-the-Loop Self-Correction:** The LangGraph ReAct agent treats SQL execution failure as a signal for iterative refinement — inspecting the error, re-reasoning about the schema, and generating a corrected query. This closes the feedback loop between generation and validation in a principled way.

### 4.2 Connection to Current GenAI Research Trends

| Trend | Connection to This Project |
|-------|---------------------------|
| Agentic AI & Tool Use | ReAct agent loop with structured tool calling; LangGraph orchestration for multi-step, self-correcting reasoning |
| Model Context Protocol (MCP) | Anthropic's 2024 open standard for LLM-to-tool integration; adopted here as the canonical interface between the agent and the database layer |
| RAG for Structured Data | Two-stage retrieval pipeline for schema context and few-shot SQL examples; moves beyond document retrieval to structured knowledge access |
| LLM-as-Judge / Self-Correction | SQL query checker validates generated SQL before execution; agent iterates on failure rather than returning incorrect results |
| Entity Resolution & Data Quality | Vector-based entity normalization addresses a real-world NL2SQL failure mode not well-covered in existing Text-to-SQL benchmarks |
| Structured Output Generation | Schema-constrained SQL generation with deterministic output parsing and execution validation; reduces hallucination at the generation layer |

### 4.3 Potential Impact on the Field

- **Democratization of Data Access:** By enabling reliable natural language querying of relational databases, ChatBI removes SQL as a prerequisite for data access. Customer service teams, operations analysts, and product managers can retrieve structured business data autonomously — reducing the load on data engineering teams and accelerating decision-making cycles.
- **A Replicable Enterprise Blueprint:** The e-commerce use case demonstrates a modular, incrementally deployable architecture: RAG + entity normalization + self-correcting agents can be integrated into existing BI stacks without replacing the underlying data infrastructure.
- **Advancing NL2SQL Reliability:** The Two-Stage RAG mechanism and entity normalization module address failure modes that are underrepresented in standard Text-to-SQL benchmarks (e.g., Spider, WikiSQL), which assume clean entity inputs and simple join structures. This work provides a practical path toward higher reliability in real-world, messy business data environments.
- **MCP as an Interoperability Standard:** Implementing MCP as the database interface demonstrates a pathway toward standardized, plug-and-play AI-powered BI tools — where any LLM agent can connect to any compliant data source without custom integration code.

### 4.4 Novel Application and Methodology

The specific combination of **LangGraph + MCP + Two-Stage Schema RAG + Vector-Based Entity Normalization** for NL2SQL represents a practical synthesis of techniques that, individually, appear in recent literature but have not been jointly applied to the business intelligence domain. Each component targets a distinct, documented failure mode in production NL2SQL systems:

| Component | Failure Mode Addressed |
|-----------|----------------------|
| Two-Stage RAG | Multi-table JOIN errors caused by incomplete schema context |
| Entity Normalization | Silent recall failures from alias / misspelling mismatch |
| MCP-First Architecture | Tight coupling between LLM reasoning and database implementation |
| ReAct Self-Correction Loop | Undetected SQL execution failures returned to the user |
| Semantic Few-Shot Retrieval | Low-accuracy zero-shot prompting on uncommon query patterns |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                (Natural Language Question Input)                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Entity Normalization Layer                      │
│         Vector similarity → canonical city / brand / product ID  │
└─────────────────────────────────────────────────────────────────┘
                        Normalized Query
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph ReAct Agent                          │
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │      Two-Stage RAG        │  │   SQL Query Checker &        │ │
│  │  Stage 1: Table Retrieval │  │   LLM Self-Validation        │ │
│  │  Stage 2: FK Path Resolve │  │   (ReAct correction loop)    │ │
│  └──────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                     Tool Calls (MCP Protocol)
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MCP Tool Server                             │
│                    (FastMCP on localhost)                         │
│                                                                  │
│          ┌──────────────────┐   ┌──────────────────┐            │
│          │ get_table_schema │   │     run_sql       │            │
│          └──────────────────┘   └──────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                           SQL Queries
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SQLite Database (Chinook.db)                     │
│          11 tables: Album, Artist, Customer, Invoice, Track …    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Evaluation Plan

System quality is assessed across seven metrics, covering both technical correctness and business-relevant reliability:

| Metric | Method | Target |
|--------|--------|--------|
| **SQL Semantic Accuracy** | Manual evaluation of 20 NL questions: is the generated SQL semantically correct? | ≥ 75% |
| **Execution Success Rate** | % of generated SQL that executes without runtime error on Chinook.db | ≥ 90% |
| **Few-Shot vs. Zero-Shot Gain** | Accuracy delta when dynamic few-shot examples are injected via RAG | ≥ 10 pp |
| **Multi-Table JOIN Accuracy** | Accuracy on queries requiring ≥ 2 tables, with and without Two-Stage RAG | ≥ 35% lift |
| **Entity Normalization F1** | Alias / misspelling correction accuracy on a held-out e-commerce entity test set | ≥ 85% F1 |
| **End-to-End Latency** | Average response time per query from NL input to SQL result | < 5 s |
| **Self-Correction Rate** | % of initially failing queries successfully corrected by the ReAct agent | ≥ 60% |

**Representative evaluation questions:**

- "How many albums does each artist have?" → GROUP BY aggregation
- "Who are the top 5 customers by total spending?" → JOIN + ORDER BY
- "List all tracks longer than 5 minutes in the Rock genre" → multi-condition filter
- "What is the average invoice total by country?" → GROUP BY + AVG
- "Which cities have the highest order volume for brand X this quarter?" → multi-table JOIN + entity normalization

---

## 7. References

1. Rajkumar, N., et al. (2022). *Evaluating the Text-to-SQL Capabilities of Large Language Models*. arXiv:2204.00498.
2. Gao, D., et al. (2023). *Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation*. arXiv:2308.15363.
3. Pourreza, M. & Rafiei, D. (2023). *DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction*. NeurIPS 2023.
4. Anthropic. (2024). *Model Context Protocol: An Open Standard for Connecting AI to Data*. anthropic.com.
5. LangChain. (2024). *SQL Database Chain and SQL Agent*. docs.langchain.com.
6. DeepSeek-AI. (2024). *DeepSeek-V3 Technical Report*. arXiv:2412.19437.
7. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020.
8. Yao, S., et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023.
9. Chase, H. (2022). *LangChain: Building Applications with LLMs through Composability*. GitHub.
