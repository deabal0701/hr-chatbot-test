# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MUREUM is an enterprise AI knowledge base assistant combining multiple AI techniques for natural language search over documents and databases. The system features an AI Agent (ReAct pattern), RAG, and NL2SQL capabilities with multi-turn conversation support.

**Stack**: FastAPI + LangGraph + PostgreSQL (pgvector) + Vue 3 + Multi-LLM Provider (OpenAI, Anthropic)

**LangChain Version**: v1.0+ (langchain>=1.2.0, langchain-core>=1.2.5, langchain-openai>=1.1.6, langchain-anthropic>=0.2.4, langgraph>=1.0.5)

**Key Features**:
- AI Agent with ReAct pattern (autonomous tool selection, multi-step reasoning)
- Multi-turn conversations with session-based memory (InMemorySaver)
- Dynamic settings management (DB-based real-time configuration)
- Multi-LLM provider support (OpenAI, Anthropic via init_chat_model)

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

# Test AI Agent search (multi-step, multi-turn)
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?",
    "config": {
      "max_iterations": 10,
      "enable_memory": true
    }
  }'

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
- **Checkpointing**: InMemorySaver for session-based conversation memory

**Example Flow** (AI Agent - ReAct):
```
agent (LLM decides) → should_continue() decision
                      ├─ "continue" → tools (execute) → agent (loop)
                      └─ "end" → END (final answer)
```

**Example Flow** (NL2SQL):
```
generate_sql → validate_sql → _should_execute() decision
                               ├─ "execute" → execute_sql → generate_answer → END
                               └─ "error" → handle_error → END
```

See `app/graphs/agent_graph.py:124-156` for Agent graph and `app/graphs/nl2sql_graph.py` for NL2SQL graph.

### Async/Await Pattern

**CRITICAL**: All graph invocations and API endpoints use `async/await` for I/O efficiency:
- FastAPI endpoints: `async def search()`
- Graph execution: `await nl2sql_graph.ainvoke(inputs)`
- LLM calls: Internal blocking `llm.invoke()` within async nodes

**Why**: Allows concurrent request handling. Without async, multiple users would block each other during LLM/DB calls.

### Dynamic Settings System

Settings are **dynamically loaded from DB** with fallback chain:
1. PostgreSQL `tb_app_settings` table (highest priority)
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

**AI Agent (ReAct) LLM calls** (variable, depends on iterations):
1. **Agent Decision** (`agent_graph.py:196`): Analyze question → Choose tool or provide answer
2. **Tool Execution**: If tool chosen, execute and observe results
3. **Repeat**: Loop until max_iterations or final answer

**Two LLM calls per NL2SQL request**:
1. **SQL Generation** (`nl2sql_graph.py:172`): Natural language → SQL query
2. **Answer Generation** (`nl2sql_graph.py:324`): SQL results → Natural language summary

**One LLM call per RAG request**:
1. **Answer Generation** (`rag_graph.py`): Retrieved documents → Natural language answer

**LLM Configuration** (via `app/utils/llm_config.py`):
- **Unified Interface**: `init_chat_model` from LangChain (provider-independent)
- **Providers**: OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet-20241022)
- **Dynamic Loading**: Model and provider from DB settings → .env → defaults
- **Temperature**: 0 for SQL generation (deterministic), 0.0-0.1 for Agent, 0.1 for answers
- **Fallback**: Automatic fallback to OpenAI if primary provider fails
- **Embeddings**: `text-embedding-3-small` (1536 dimensions) via `langchain_openai.OpenAIEmbeddings`

### Database Architecture

**PostgreSQL roles**:
1. **Primary storage**: Documents, settings, metadata
2. **Vector search**: pgvector extension for semantic search (1536-dim embeddings)
3. **NL2SQL target**: Can query itself or external Oracle DBs

**Key Tables**:
- `tb_docs`: Documents + embeddings (RAG source)
- `tb_app_settings`: Dynamic configuration
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
│   ├── agent.py         # AI Agent endpoints (ReAct pattern)
│   ├── search.py        # RAG/NL2SQL/Auto search
│   ├── documents.py     # Document management
│   ├── settings.py      # Settings management
│   └── codes.py         # Code management
├── graphs/              # LangGraph workflows (core AI logic)
│   ├── agent_graph.py   # AI Agent (ReAct pattern, tool orchestration)
│   ├── rag_graph.py     # Document search → LLM answer
│   └── nl2sql_graph.py  # Question → SQL → Execute → LLM summary
├── tools/               # AI Agent tools
│   ├── base.py          # BaseTool class with hooks
│   ├── sql_tool.py      # SQL query tool (NL2SQL wrapper)
│   ├── rag_tool.py      # Document search tool (RAG wrapper)
│   └── calc_tool.py      # Calculator tool (safe AST evaluation)
├── services/            # Reusable business logic
│   ├── vector_store.py  # Embedding + pgvector search
│   ├── sql_executor.py  # SQL validation + execution + security
│   ├── schema_loader.py # DB schema introspection
│   └── settings_service.py  # Dynamic config management
├── models/              # Pydantic models (API contracts)
│   ├── schemas.py       # Common schemas (RAG, NL2SQL)
│   ├── agent_schemas.py # Agent-specific schemas (ReAct)
│   └── hr_schema_def.py # HR schema definitions
└── utils/               # Infrastructure utilities
    ├── database.py      # Connection pool (psycopg3 + pgvector)
    ├── external_database.py # External DB connection
    ├── llm_config.py    # Unified LLM configuration (init_chat_model)
    ├── logger.py        # Structured logging
    ├── text_chunker.py  # Document splitting for embeddings
    ├── langsmith.py     # LangSmith integration (optional)
    └── common.py        # Common utilities
```

### Request Flow Examples

**AI Agent Flow** (ReAct pattern, multi-step):
```
User question → api/routes/agent.py:agent_search()
  → graphs/agent_graph.py:ainvoke(initial_state, config={thread_id: session_id})
    → Iteration 1:
      → agent_node: LLM decides → "Use query_database_tool"
      → tools_node: Execute SQL tool → Result: "27명 발견"
      → agent_node: LLM reviews → "Need policy info, use search_documents_tool"
    → Iteration 2:
      → tools_node: Execute RAG tool → Result: "재택근무 정책 문서"
      → agent_node: LLM synthesizes → Final answer in Korean
    → END (InMemorySaver auto-saves session)
  → Return AgentResponse with answer, steps, tools_used
```

**NL2SQL Flow**:
```
User query → api/routes/search.py:search() → classify intent → graphs/nl2sql_graph.py:ainvoke()
  → 1. _generate_sql(): LLM creates SQL
  → 2. _validate_sql(): Security checks (no DDL/DML, table whitelist)
  → 3. _should_execute(): Decision function returns "execute" or "error"
  → 4. _execute_sql(): Run query via services/sql_executor.py
  → 5. _generate_answer(): LLM summarizes results
  → Return NL2SQLResponse
```

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

### AI Agent (ReAct Pattern)

**Architecture** (`app/graphs/agent_graph.py`):
- **Pattern**: ReAct (Reasoning + Acting)
- **Checkpointer**: InMemorySaver for session-based memory
- **Tools**: SQL query, document search, calculator
- **Flow**: agent → should_continue → tools → agent (loop)

**Key Components**:
1. **Agent Node** (`_agent_node`):
   - LLM analyzes question and decides next action
   - Can call tools or provide final answer
   - System prompt defines tool usage guidelines
   - Temperature: 0.0-0.1 for consistent reasoning

2. **Tool Node** (LangGraph's `ToolNode`):
   - Executes selected tools automatically
   - Returns observations to agent
   - Each tool has before/after hooks for caching, logging

3. **Decision Node** (`_should_continue`):
   - Checks if LLM wants to call more tools
   - Enforces max_iterations limit (default: 10)
   - Enforces timeout (default: 60s)
   - Returns "continue" or "end"

**Tools Architecture** (`app/tools/`):
- **Base Class** (`BaseTool`): Template method pattern with hooks
  - `before_execute()`: Pre-processing (caching, validation)
  - `_execute()`: Core logic (must implement)
  - `after_execute()`: Post-processing (caching, logging)
  - Returns `ToolResult` with success, data, error, metadata

- **SQL Tool** (`SQLQueryTool`):
  - Wraps NL2SQL graph functionality
  - Caches frequent queries (in-memory, max 100)
  - Schema cached on first use
  - Returns formatted results (single vs multiple rows)

- **RAG Tool** (`DocumentSearchTool`):
  - Wraps vector search functionality
  - Supports filters (doc_type, category)
  - Caches search results (in-memory, max 50)
  - Returns formatted snippets with metadata

- **Calculator Tool** (`CalculatorTool`):
  - Safe AST-based evaluation (no `eval()`)
  - Whitelist: operators (+, -, *, /, **), functions (sum, min, max, sqrt, etc.)
  - Prevents code injection attacks

**Session Management** (InMemorySaver):
- **Thread ID**: Unique session identifier (e.g., "user123-session456")
- **Auto-saving**: LangGraph automatically saves state after each node
- **Retrieval**: Load previous conversation via same thread_id
- **Cleanup**: Manual deletion via `/sessions/{session_id}` endpoint
- **No external DB**: In-memory only (lost on restart)

**Agent Configuration** (`AgentConfig`):
```python
{
    "max_iterations": 10,          # Max reasoning loops
    "llm_model": "gpt-4o",         # LLM model (DB → .env → default)
    "llm_temperature": 0.0,        # Reasoning temperature
    "enable_memory": True,         # Session memory
    "tools_whitelist": None,       # Allowed tools (None = all)
    "tools_blacklist": None,       # Blocked tools
    "timeout_seconds": 60          # Total timeout
}
```

**Logging Pattern**:
```python
log_agent_step(request_id, iteration, "ACTION", "Calling SQL tool", tool_name="query_database")
```
Stages: INIT → THINK → ACTION → OBSERVE → FINISH → COMPLETE

### Security - NL2SQL

**SQL Injection Prevention** (`app/services/sql_executor.py:validate_sql()`):
1. **Keyword blacklist**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. **Table whitelist**: Only `employee`, `department`, `tb_docs`, etc. allowed
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

**Agent stages**: INIT → THINK → ACTION → OBSERVE → FINISH → COMPLETE
**NL2SQL stages**: INIT (0) → GENERATE (1) → VALIDATE (2) → EXECUTE (3) → ANSWER (4) → COMPLETE (5)
**RAG stages**: INIT (0) → RETRIEVE (1) → GENERATE (2) → COMPLETE (3)

All logs include `request_id` for end-to-end tracking across async operations.

## Environment Variables

Required `.env` configuration:

```bash
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/hr_chatbot

# OpenAI API (Required)
OPENAI_API_KEY=sk-proj-...

# Anthropic API (Optional, for Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Application
APP_ENV=development  # or production
LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR

# Optional: Override defaults (can also set via Admin UI)
LLM_MODEL=gpt-4o
LLM_PROVIDER=openai  # or anthropic
EMBEDDING_MODEL=text-embedding-3-small
RAG_TOP_K=10
SQL_TIMEOUT_SECONDS=30
```

**Priority**: Admin UI settings (DB) > `.env` > code defaults

**Testing Database Connection**:
```bash
# Using the provided test database
DATABASE_URL=postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb
```

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
INSERT INTO tb_app_settings (category, key, value, value_type, description)
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

### Adding a New AI Agent Tool

```python
# 1. Create tool class in app/tools/new_tool.py
from app.tools.base import BaseTool, ToolResult
from langchain_core.tools import tool

class NewTool(BaseTool):
    @property
    def name(self) -> str:
        return "new_tool"

    @property
    def description(self) -> str:
        return """Description for LLM to understand when to use this tool.

        Use this when:
        - Scenario 1
        - Scenario 2

        Args:
            param1: Description

        Returns:
            Result description
        """

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Param description"}
            },
            "required": ["param1"]
        }

    def _execute(self, param1: str, **kwargs) -> ToolResult:
        try:
            # Your logic here
            result = process(param1)
            return ToolResult(success=True, data=result, metadata={"param1": param1})
        except Exception as e:
            return ToolResult(success=False, error=str(e), metadata={"param1": param1})

# 2. Create LangChain tool wrapper
@tool
def new_tool_func(param1: str) -> str:
    """Description (same as class description)"""
    tool_instance = NewTool()
    result = tool_instance.execute(param1=param1)
    return str(result.data) if result.success else f"Error: {result.error}"

# 3. Register in app/graphs/agent_graph.py
def _get_tools(self) -> List:
    return [
        query_database_tool,
        search_documents_tool,
        calculate_tool,
        new_tool_func,  # Add here
    ]
```

## Known Issues & Workarounds

### Issue: Model Not Found (404)
**Symptom**: `Error code: 404 - The model 'xxx' does not exist`
**Cause**: Model name typo or unavailable in your API account
**Fix**:
- OpenAI: Check https://platform.openai.com/docs/models for valid models (gpt-4o, gpt-4o-mini, etc.)
- Anthropic: Check https://docs.anthropic.com/claude/docs/models-overview (claude-3-5-sonnet-20241022, etc.)
- Update via Admin UI → Settings → LLM section

### Issue: Provider API Key Missing
**Symptom**: `Error: openai API 키가 설정되지 않았습니다` or `Anthropic API 키가 설정되지 않았습니다`
**Cause**: API key not configured
**Fix**:
1. Add to `.env`: `OPENAI_API_KEY=sk-proj-...` or `ANTHROPIC_API_KEY=sk-ant-...`
2. Or set in Admin UI → Settings → OpenAI/Anthropic section
3. Restart server if `.env` was changed

### Issue: Vector Search Returns Nothing
**Symptom**: RAG always returns "관련 문서를 찾을 수 없습니다"
**Cause**:
1. Documents not embedded (`indexed=false`)
2. Similarity threshold too high
3. Embedding model mismatch

**Fix**:
```sql
-- Check indexed status
SELECT id, title, indexed FROM tb_docs;

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
  - Use cheaper models (gpt-4o-mini) for testing and development
  - Switch providers based on cost/performance needs

- **Agent performance** (typical multi-step query):
  - Per iteration: ~1-3s (LLM decision + tool execution)
  - Average iterations: 2-5 for complex questions
  - Total: ~5-15s for multi-step queries
  - Cache hits reduce tool execution time significantly

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
anthropic>=0.39.0,<1.0.0
langchain-core>=1.2.5,<2.0.0
langchain-text-splitters>=0.3.0,<1.0.0
langchain>=1.2.0,<2.0.0
langchain-openai>=1.1.6,<2.0.0
langchain-anthropic>=0.2.4,<1.0.0
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
| langchain-anthropic | 0.2.4 | <1.0.0 | ✅ Stable (Production) |
| langgraph | 1.0.5 | <2.0.0 | ✅ Stable (Production) |

## Multi-LLM Provider Support

This project supports multiple LLM providers through LangChain's unified `init_chat_model` interface.

### Supported Providers (Phase 2)

**Current**:
- ✅ **OpenAI** (GPT-4o, GPT-4o-mini, GPT-4 Turbo, etc.)
- ✅ **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.)

**Configuration** (`app/utils/llm_config.py`):
```python
from app.utils.llm_config import LLMConfigManager

# Automatic configuration (reads from DB/env)
llm = LLMConfigManager.create_llm(
    temperature=0.0,
    # model and provider are auto-loaded from DB settings
)

# Explicit configuration
llm = LLMConfigManager.create_llm(
    temperature=0.1,
    model="claude-3-5-sonnet-20241022",
    provider="anthropic"
)
```

### How It Works

**1. Unified Interface** (`init_chat_model`):
- Provider-independent code (same interface for all providers)
- Automatic fallback to OpenAI if primary provider fails
- Dynamic provider switching without code changes

**2. Configuration Priority**:
```
1. Function parameters (highest)
2. DB settings (tb_app_settings table)
3. Environment variables (.env)
4. Code defaults (lowest)
```

**3. Settings Management**:
```sql
-- Set LLM provider and model via DB
UPDATE tb_app_settings SET value = 'anthropic' WHERE category = 'llm' AND key = 'provider';
UPDATE tb_app_settings SET value = 'claude-3-5-sonnet-20241022' WHERE category = 'llm' AND key = 'model';

-- Or via Admin UI: Settings → LLM section
```

**4. API Key Management**:
- OpenAI: `OPENAI_API_KEY` (required)
- Anthropic: `ANTHROPIC_API_KEY` (optional, required if using Anthropic)
- Both can be set via `.env` or Admin UI

### Provider-Specific Features

**OpenAI**:
- Fast response times
- Cost-effective models (gpt-4o-mini)
- Wide model selection
- Function calling (tool use)

**Anthropic**:
- Larger context windows (200K tokens)
- High-quality reasoning (Claude 3.5 Sonnet)
- Better instruction following
- Function calling (tool use)

### Migration Guide (Adding New Provider)

To add a new provider (e.g., Cohere, Google Vertex):

1. **Add dependency** to `requirements.txt`:
```python
langchain-cohere>=0.1.0,<1.0.0
```

2. **Update LLMConfigManager** (`app/utils/llm_config.py`):
```python
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "cohere": "command-r-plus",  # Add here
}

def _get_api_key(provider: str) -> str:
    if provider == "cohere":
        api_key = settings_service.get_value("cohere", "api_key", getattr(settings, "cohere_api_key", None))
        # ... error handling
    # ...
```

3. **Add DB settings**:
```sql
INSERT INTO tb_app_settings (category, key, value, value_type, description)
VALUES
    ('cohere', 'api_key', '', 'string', 'Cohere API Key'),
    ('llm', 'provider', 'cohere', 'string', 'LLM Provider');
```

4. **Test**:
```python
llm = LLMConfigManager.create_llm(provider="cohere", model="command-r-plus")
```

### Best Practices

**Cost Optimization**:
- Use `gpt-4o-mini` for development/testing (cheapest)
- Use `gpt-4o` or `claude-3-5-sonnet` for production
- Monitor usage via provider dashboards

**Reliability**:
- Set API keys for both OpenAI and Anthropic (automatic fallback)
- Monitor error rates and switch providers if needed
- Use retries with exponential backoff (built into LangChain)

**Performance**:
- OpenAI generally faster for simple queries
- Anthropic better for complex reasoning tasks
- Test both providers to find optimal balance

## Additional Documentation

- `ARCHITECTURE.md` - Detailed system design, data flow diagrams
- `PYTHON_CODE_GUIDE.md` - File-by-file code explanations
- `SETUP.md` - Installation and deployment guide
- `README.md` - Quick start guide

For questions about specific files, refer to PYTHON_CODE_GUIDE.md which documents every module in detail.

중요: 
나는 가상환경으로 conda를 사용하고  있고, 가상환경의 이름은 my-env3.11_chat2 이다. 테스트시나 파이썬 실행시 이를 이용하라.

DB확인시는 아래를 이용하라.
postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb


변경시에는 항상 변경된 소스코드파일 및 변경된 내용에 대해 설명을하라.

log_step은 가능한 한줄에 작성하라.


