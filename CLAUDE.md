# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR Chatbot system combining RAG (Retrieval Augmented Generation) and NL2SQL for natural language search over documents and databases. The system automatically classifies user intent and routes to the appropriate search method.

**Stack**: FastAPI + LangGraph + PostgreSQL (pgvector) + Vue 3 + OpenAI API

**LangChain Version**: v1.0+ (langchain>=1.2.0, langchain-core>=1.2.5, langchain-openai>=1.1.6, langgraph>=1.0.5)

## Common Commands

### Backend (Python/FastAPI)

```bash
# Development server (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Database initialization (first time only)
python scripts/init_db.py

# Document embedding
python scripts/embed_documents.py --sample
python scripts/embed_documents.py --file data/documents.json
```

### Frontend (Vue 3)

```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```

### Testing & Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Test RAG search
curl -X POST "http://localhost:8000/api/v1/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "재택근무 정책이 뭐야?", "mode": "rag"}'

# Test NL2SQL search
curl -X POST "http://localhost:8000/api/v1/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{"query": "2024년 입사자 수는?", "mode": "nl2sql"}'
```

## Architecture Highlights

### LangGraph Workflow Pattern

This codebase uses **LangGraph** for AI workflows, NOT traditional function calls. Understanding the graph execution model is critical:

**Key Concept**: `result = await self.graph.ainvoke(initial_state)`
- Entry point determined by `workflow.set_entry_point("node_name")`
- Nodes execute sequentially via `workflow.add_edge(from, to)`
- Conditional branching via `workflow.add_conditional_edges(node, decision_func, mapping)`

**Example Flow** (NL2SQL):
```
generate_sql → validate_sql → _should_execute() decision
                               ├─ "execute" → execute_sql → generate_answer → END
                               └─ "error" → handle_error → END
```

See `app/graphs/nl2sql_graph.py:73-102` for graph construction and `app/graphs/nl2sql_graph.py:368` for execution.

### Async/Await Pattern

**CRITICAL**: All graph invocations and API endpoints use `async/await` for I/O efficiency:
- FastAPI endpoints: `async def search()`
- Graph execution: `await nl2sql_graph.ainvoke(inputs)`
- LLM calls: Internal blocking `llm.invoke()` within async nodes

**Why**: Allows concurrent request handling. Without async, multiple users would block each other during LLM/DB calls.

### Dynamic Settings System

Settings are **dynamically loaded from DB** with fallback chain:
1. PostgreSQL `app_settings` table (highest priority)
2. Environment variables (`.env`)
3. Hardcoded defaults in `app/config.py`

**Pattern** (used throughout):
```python
from app.services.settings_service import settings_service

llm_model = settings_service.get_value("llm", "model", settings.llm_model)
# DB → .env → default
```

Admin UI can change settings in real-time without code deployment. See `app/services/settings_service.py`.

### LLM Integration Points

**Two LLM calls per NL2SQL request**:
1. **SQL Generation** (`nl2sql_graph.py:172`): Natural language → SQL query
2. **Answer Generation** (`nl2sql_graph.py:324`): SQL results → Natural language summary

**One LLM call per RAG request**:
1. **Answer Generation** (`rag_graph.py`): Retrieved documents → Natural language answer

**LLM Configuration**:
- Model: Dynamically loaded from DB settings (supports gpt-4, gpt-4o, gpt-4.1-nano, etc.)
- Temperature: 0 for SQL generation (deterministic), 0.1 for answers
- Embeddings: `text-embedding-3-small` (1536 dimensions) via `langchain_openai.OpenAIEmbeddings`
- All LLM/Embedding instances use LangChain v1.0 `langchain_openai` package

### Database Architecture

**PostgreSQL roles**:
1. **Primary storage**: Documents, settings, metadata
2. **Vector search**: pgvector extension for semantic search (1536-dim embeddings)
3. **NL2SQL target**: Can query itself or external Oracle DBs

**Key Tables**:
- `hr_docs`: Documents + embeddings (RAG source)
- `app_settings`: Dynamic configuration
- `employee`, `department`: NL2SQL query targets

**Connection Pattern**:
```python
from app.utils.database import db_manager

# Read-only
with db_manager.get_cursor() as cur:
    cur.execute("SELECT ...")
    rows = cur.fetchall()

# Write (commit=True required)
with db_manager.get_cursor(commit=True) as cur:
    cur.execute("INSERT ...")
```

Connection pool initialized in `app/main.py` lifespan, configured in `app/utils/database.py`.

## Code Organization

### Layer Responsibilities

```
app/
├── main.py              # FastAPI app + lifespan (DB pool init/cleanup)
├── config.py            # Pydantic settings (env vars + validation)
├── api/routes/          # HTTP endpoints (thin layer, delegates to graphs)
├── graphs/              # LangGraph workflows (core AI logic)
│   ├── rag_graph.py     # Document search → LLM answer
│   └── nl2sql_graph.py  # Question → SQL → Execute → LLM summary
├── services/            # Reusable business logic
│   ├── vector_store.py  # Embedding + pgvector search
│   ├── sql_executor.py  # SQL validation + execution + security
│   ├── schema_loader.py # DB schema introspection
│   └── settings_service.py  # Dynamic config management
├── models/schemas.py    # Pydantic models (API contracts)
└── utils/               # Infrastructure utilities
    ├── database.py      # Connection pool (psycopg3 + pgvector)
    ├── logger.py        # Structured logging
    └── text_chunker.py  # Document splitting for embeddings
```

### Request Flow Example

**User query** → `api/routes/search.py:search()` → **classify intent** → `graphs/nl2sql_graph.py:ainvoke()` → **graph nodes execute**:
1. `_generate_sql()` - LLM creates SQL
2. `_validate_sql()` - Security checks (no DDL/DML, table whitelist)
3. `_should_execute()` - Decision function returns "execute" or "error"
4. `_execute_sql()` - Run query via `services/sql_executor.py`
5. `_generate_answer()` - LLM summarizes results
→ **response returned**

Each step has detailed logging with `request_id` for traceability.

### Frontend Structure

```
frontend/src/
├── views/
│   ├── HomeView.vue           # Main chat interface
│   └── admin/
│       ├── DocumentsView.vue  # Document CRUD + embedding
│       └── SettingsView.vue   # System settings (OpenAI, LLM, RAG, NL2SQL)
├── components/
│   └── chat/MessageList.vue   # Chat message display
├── store/index.js             # Vuex state (settings, documents)
└── api/                       # Axios API clients
```

## Critical Implementation Details

### Security - NL2SQL

**SQL Injection Prevention** (`app/services/sql_executor.py:validate_sql()`):
1. **Keyword blacklist**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. **Table whitelist**: Only `employee`, `department`, `hr_docs`, etc. allowed
3. **SELECT-only enforcement**: sqlparse verification
4. **Parameterized queries**: psycopg3 automatic escaping
5. **Timeout**: 30-second statement_timeout
6. **Row limit**: Auto-add `LIMIT 1000` if missing

**Never disable validation** except for already-validated queries in execute node.

### Embedding & Chunking

**Document processing flow**:
1. Save document (without embedding): `POST /api/admin/v1/documents`
2. Preview chunking: `POST /api/admin/v1/documents/embedding/preview`
3. Execute chunking + embedding: `POST /api/admin/v1/documents/embedding/execute`

**Chunking strategy** (`app/utils/text_chunker.py`):
- Default: 1000 chars with 100-char overlap
- Preserves context across chunk boundaries
- Metadata tracks `parent_id`, `chunk_index`, `start_char`, `end_char`

**Why chunk?**: Long documents exceed LLM context windows and reduce retrieval precision. Each chunk gets its own embedding for granular search.

### Logging Conventions

**Request tracing**:
```python
request_id = str(uuid.uuid4())[:8]  # 8-char ID
logger.info(f"[{request_id}] [STEP 1] [STAGE] Message | key=value")
```

**NL2SQL stages**: INIT (0) → GENERATE (1) → VALIDATE (2) → EXECUTE (3) → ANSWER (4) → COMPLETE (5)
**RAG stages**: INIT (0) → RETRIEVE (1) → GENERATE (2) → COMPLETE (3)

All logs include `request_id` for end-to-end tracking across async operations.

## Environment Variables

Required `.env` configuration:

```bash
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/hr_chatbot

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# Application
APP_ENV=development  # or production
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR

# Optional: Override defaults (can also set via Admin UI)
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
RAG_TOP_K=10
SQL_TIMEOUT_SECONDS=30
```

**Priority**: Admin UI settings > `.env` > code defaults

## Common Patterns

### Adding a New Graph Node

```python
# In graph class
def _new_node(self, state: GraphState) -> GraphState:
    """Node description"""
    # 1. Extract from state
    data = state["key"]

    # 2. Process
    result = do_something(data)

    # 3. Update state
    state["new_key"] = result

    # 4. Log
    log_step(state.get("request_id"), "X", "STAGE", "Message")

    return state

# In _build_graph()
workflow.add_node("new_node", self._new_node)
workflow.add_edge("prev_node", "new_node")
```

### Adding Dynamic Settings

```python
# 1. Add to app/config.py defaults
class Settings(BaseSettings):
    new_setting: str = "default_value"

# 2. Insert into DB (one-time)
INSERT INTO app_settings (category, key, value, value_type, description)
VALUES ('category', 'new_setting', 'default', 'string', 'Description');

# 3. Use in code
value = settings_service.get_value("category", "new_setting", settings.new_setting)
```

### Adding API Endpoint

```python
# In app/api/routes/
@router.post("/endpoint")
async def endpoint_name(request: RequestModel):
    request_id = str(uuid.uuid4())[:8]

    try:
        # Delegate to service/graph
        result = await some_graph.ainvoke({"data": request.data, "request_id": request_id})
        return ResponseModel(**result)
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Register in app/main.py
app.include_router(router, prefix="/api/v1", tags=["category"])
```

## Known Issues & Workarounds

### Issue: Model Not Found (404)
**Symptom**: `Error code: 404 - The model 'gpt-4.1-nano' does not exist`
**Cause**: Model name typo or unavailable in your OpenAI account
**Fix**: Check `/docs/pricing` for valid model names, update via Settings UI

### Issue: Vector Search Returns Nothing
**Symptom**: RAG always returns "관련 문서를 찾을 수 없습니다"
**Cause**:
1. Documents not embedded (`indexed=false`)
2. Similarity threshold too high
3. Embedding model mismatch

**Fix**:
```sql
-- Check indexed status
SELECT id, title, indexed FROM hr_docs;

-- Run embedding
POST /api/admin/v1/documents/embedding/execute

-- Lower threshold (Admin UI → RAG → similarity_threshold: 0.4 → 0.3)
```

### Issue: DB Connection Pool Exhausted
**Symptom**: `PoolTimeout: connection pool exhausted`
**Cause**: Long-running queries blocking connections
**Fix**: Increase pool size in `.env`:
```bash
DB_POOL_SIZE=30  # default: 20
DB_MAX_OVERFLOW=15  # default: 10
```

## Testing Considerations

- **LLM calls**: Expensive and non-deterministic. Mock `llm.invoke()` for unit tests.
- **DB tests**: Use separate test DB or transaction rollback
- **Graph tests**: Test individual nodes, not full graph (too slow)
- **Vector search**: Requires actual embeddings, hard to mock

## Performance Notes

- **Response time breakdown** (typical NL2SQL):
  - SQL generation LLM call: ~1s
  - SQL execution: ~50ms
  - Answer generation LLM call: ~2s
  - Total: ~3.5s

- **Bottlenecks**:
  1. OpenAI API latency (cannot control)
  2. Large embedding batches (use `embed_texts()` for bulk)
  3. Complex SQL queries (index optimization)

- **Optimization opportunities**:
  - Cache common schema descriptions
  - Batch embedding operations
  - Use cheaper models (gpt-4.1-nano) for testing

## LangChain v1.0 Migration

This project has been migrated to LangChain v1.0+ for improved stability and production readiness.

**CRITICAL REQUIREMENT**: Python 3.10 or higher (Python 3.9 not supported)

### Key Changes

**0. Python Version Requirement**:
- **Minimum**: Python 3.10.0
- **Recommended**: Python 3.11+
- **Not Supported**: Python 3.9 (EOL October 2025)

Check version: `python check_python_version.py`

**1. Dependencies** ([requirements.txt](requirements.txt)):
```python
# Core Framework (Pydantic v2 compatible)
fastapi>=0.115.0,<1.0.0
pydantic>=2.7.4,<3.0.0  # CRITICAL: langchain-core requires >=2.7.4

# LangChain v1.0+ stable versions (actual 1.x series)
openai>=1.30.0,<2.0.0
langchain-core>=1.2.5,<2.0.0
langchain-text-splitters>=0.3.0,<1.0.0
langchain>=1.2.0,<2.0.0
langchain-openai>=1.1.6,<2.0.0
langgraph>=1.0.5,<2.0.0
```

**2. Import Patterns** (already compliant):
```python
# Correct (LangChain v1.0)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

# NEVER use (deprecated)
from langchain_community.chat_models import ChatOpenAI  # ❌
from openai import OpenAI  # ❌ Use OpenAIEmbeddings instead
```

**3. Embeddings Migration** ([vector_store.py:54-70](app/services/vector_store.py#L54-L70)):
```python
# Old (direct OpenAI SDK)
from openai import OpenAI
client = OpenAI(api_key=api_key)
response = client.embeddings.create(model=model, input=text)

# New (LangChain v1.0)
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model=model, openai_api_key=api_key)
vector = embeddings.embed_query(text)  # Single text
vectors = embeddings.embed_documents(texts)  # Batch
```

**Benefits**:
- Built-in retry logic and error handling
- Caching support for repeated queries
- Unified interface across different embedding providers
- Better integration with LangChain ecosystem

**4. LangGraph Stability**:
- No breaking changes in StateGraph API
- Backward compatible with v0.x patterns
- Production-ready with durable execution and checkpointing

### Migration Checklist

- ✅ Update `requirements.txt` version constraints
- ✅ Replace direct OpenAI SDK calls with `langchain_openai` equivalents
- ✅ Use `ChatOpenAI` from `langchain_openai` (not `langchain_community`)
- ✅ Use `OpenAIEmbeddings` for all embedding operations
- ✅ Verify all imports use `langchain_openai` package
- ⚠️ **Regenerate `requirements.lock`** (see [UPDATE_LOCK_FILE.md](UPDATE_LOCK_FILE.md))

### Version Compatibility

| Package | Min Version | Max Version | Status |
|---------|-------------|-------------|--------|
| langchain-core | 1.2.5 | <2.0.0 | ✅ Stable (Production) |
| langchain | 1.2.0 | <2.0.0 | ✅ Stable (Production) |
| langchain-openai | 1.1.6 | <2.0.0 | ✅ Stable (Production) |
| langgraph | 1.0.5 | <2.0.0 | ✅ Stable (Production) |

## Additional Documentation

- `ARCHITECTURE.md` - Detailed system design, data flow diagrams
- `PYTHON_CODE_GUIDE.md` - File-by-file code explanations
- `SETUP.md` - Installation and deployment guide
- `README.md` - Quick start guide

For questions about specific files, refer to PYTHON_CODE_GUIDE.md which documents every module in detail.


