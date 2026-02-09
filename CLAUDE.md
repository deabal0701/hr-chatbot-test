# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MUREUM is an enterprise AI knowledge base assistant combining multiple AI techniques for natural language search over documents and databases. The system features an AI Agent (ReAct pattern), RAG, and NL2SQL capabilities with multi-turn conversation support.

**Stack**: FastAPI + LangGraph + PostgreSQL (pgvector) + Vue 3 + Multi-LLM Provider (OpenAI, Anthropic) + Multi-DB Support (PostgreSQL, Oracle)

**Python Version**: 3.13 (Conda 환경: `penv3.13-nlq`)

**LangChain Version**: v1.0+ (langchain>=1.2.0, langchain-core>=1.2.5, langgraph>=1.0.5)

**Key Features**:
- AI Agent with ReAct pattern (autonomous tool selection, multi-step reasoning)
- **Intent Analysis & Context Retrieval** (질문 의도 분석, SQL 컨텍스트 자동 주입)
- Multi-turn conversations with session-based memory (InMemorySaver)
- Dynamic settings management (DB-based real-time configuration)
- Multi-LLM provider support (OpenAI, Anthropic via init_chat_model)
- Multi-DB support for NL2SQL (PostgreSQL, Oracle via adapter pattern)

## Common Commands

### Backend (Python/FastAPI)

```bash
# Conda 환경 활성화
conda activate penv3.13-nlq

# Development server (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 19090

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

### Testing

```bash
# Unit tests
pytest tests/

# Single test file
pytest tests/test_agent.py -v

# Single test function
pytest tests/test_agent.py::test_function_name -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### API Health Checks

```bash
# API health check
curl http://localhost:19090/health

# Test AI Agent search
curl -X POST "http://localhost:19090/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?", "config": {"max_iterations": 10, "enable_memory": true}}'

# Test RAG search
curl -X POST "http://localhost:19090/api/v1/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "재택근무 정책이 뭐야?", "mode": "rag"}'

# Test NL2SQL search
curl -X POST "http://localhost:19090/api/v1/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{"query": "2024년 입사자 수는?", "mode": "nl2sql"}'
```

## Architecture Highlights

### LangGraph Workflow Pattern

This codebase uses **LangGraph** for AI workflows. Understanding the graph execution model is critical:

**Key Concept**: `result = await self.graph.ainvoke(initial_state)`
- Entry point: `workflow.set_entry_point("node_name")`
- Sequential: `workflow.add_edge(from, to)`
- Conditional: `workflow.add_conditional_edges(node, decision_func, mapping)`
- Checkpointing: InMemorySaver for session-based conversation memory

**AI Agent Flow** (ReAct + Intent Analysis - `app/graphs/agent_graph.py`):
```
┌─────────────────────────────────────────────────────────────┐
│  intent_analysis (질문 유형/의도 분석)                        │
│    ↓                                                        │
│  context_retrieval (SQL 컨텍스트: 스키마, Few-shot, 용어집)    │
│    ↓                                                        │
│  agent (LLM decides) → should_continue() decision           │
│                        ├─ "continue" → tools → agent (loop) │
│                        └─ "end" → END (final answer)        │
└─────────────────────────────────────────────────────────────┘
```

**NL2SQL Flow** (`app/graphs/nl2sql_graph.py`):
```
schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                                                        ├─ execute → execute_sql → should_continue_after_execute
                                                                        │                            ├─ answer → generate_answer → END
                                                                        │                            ├─ retry → fewshot_retrieval (enhanced)
                                                                        │                            └─ error → handle_error → END
                                                                        ├─ retry → fewshot_retrieval (enhanced)
                                                                        └─ error → handle_error → END
```

### AgentState (확장된 상태 관리)

Agent 상태는 TypedDict로 정의되며, LangGraph의 reducer 패턴을 사용합니다:

```python
class AgentState(TypedDict):
    # ===== 기본 필드 =====
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 누적
    question: Annotated[str, _overwrite]
    session_id: Annotated[str, _overwrite]
    config: Annotated[AgentConfig, _overwrite]
    iteration_count: Annotated[int, _overwrite]
    final_answer: Annotated[str, _overwrite]
    request_id: Annotated[str, _overwrite]
    start_time: Annotated[float, _overwrite]

    # ===== 의도 분석 =====
    intent_analysis: Annotated[Dict[str, Any], _overwrite]
    intent_confidence: Annotated[float, _overwrite]
    is_ambiguous: Annotated[bool, _overwrite]
    ambiguity_options: Annotated[List[str], _overwrite]
    extracted_entities: Annotated[Dict[str, Any], _overwrite]

    # ===== 컨텍스트 검색 =====
    relevant_schemas: Annotated[List[Dict], _overwrite]     # 관련 테이블 스키마
    similar_queries: Annotated[List[Dict], _overwrite]      # Few-shot 예제
    business_terms: Annotated[List[Dict], _overwrite]       # 비즈니스 용어집
    context_prompt: Annotated[str, _overwrite]              # Agent에 주입할 컨텍스트

    # ===== Human in the Loop =====
    waiting_for_human: Annotated[bool, _overwrite]
    human_intervention: Annotated[Dict[str, Any], _overwrite]
    human_response: Annotated[str, _overwrite]
```

**초기 상태 생성**:
```python
from app.graphs.agent_graph import create_state_defaults

initial_state = {
    **create_state_defaults(),  # 확장 필드 기본값
    "messages": [HumanMessage(content=question)],
    "question": question,
    # ...
}
```

### Intent Analysis & Context Retrieval

Agent 실행 전에 의도 분석과 컨텍스트 검색이 자동으로 수행됩니다:

**의도 분석** (`app/graphs/nodes/agent_nodes.py:intent_analysis_node`):
- 질문 유형 분류: `sql_query`, `document_search`, `hybrid`, `calculation`, `general`
- 쿼리 의도: `select`, `aggregate`, `compare`, `trend`, `join`, `search`, `calculate`
- 모호성 감지: `period`, `quantity`, `criteria`, `table`, `column`
- 신뢰도 점수 산출

**컨텍스트 검색** (`app/graphs/nodes/agent_nodes.py:context_retrieval_node`):
- SQL 질의 시 자동으로 관련 스키마, Few-shot 예제, 용어집 검색
- Vector Store에서 유사도 기반 검색 (usage_type='rag_action')
- 결과는 `state["context_prompt"]`에 저장되어 Agent System Prompt에 자동 주입

### Async/Await Pattern

**CRITICAL**: All graph invocations and API endpoints use `async/await`:
- FastAPI endpoints: `async def search()`
- Graph execution: `await graph.ainvoke(inputs)`
- LLM calls: Internal blocking `llm.invoke()` within async nodes

### Dynamic Settings System

Settings are **dynamically loaded from DB** with fallback chain:
1. PostgreSQL `tb_app_settings` table (highest priority)
2. Environment variables (`.env`)
3. Hardcoded defaults in `app/config.py`

**Pattern** (used throughout):
```python
from app.api.services.settings_service import settings_service
llm_model = settings_service.get_value("llm", "model", settings.llm_model)
```

### LLM Configuration

**Unified Interface** via `app/core/llm/llm_config.py`:
```python
from app.core.llm.llm_config import LLMConfigManager
llm = LLMConfigManager.create_llm(temperature=0.0)  # Auto-loads from DB/env
```

**Providers**: OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet-20241022)
**Temperature**: 0 for SQL generation, 0.0-0.1 for Agent, 0.1 for answers
**Embeddings**: `text-embedding-3-small` (1536 dimensions)

### Database Architecture

**PostgreSQL** (Primary DB with pgvector):
- `tb_docs`: Documents + embeddings (RAG source)
- `tb_app_settings`: Dynamic configuration
- `employee`, `department`: NL2SQL query targets

**Connection Pattern** (`app/core/database/connection.py`):
```python
from app.core.database.connection import db_manager

with db_manager.get_cursor() as cur:
    cur.execute("SELECT ...")
    rows = cur.fetchall()

with db_manager.get_cursor(commit=True) as cur:
    cur.execute("INSERT ...")
```

**Multi-DB Support** (NL2SQL via Factory Pattern - `app/core/database/adapters/factory.py`):
```python
from app.core.database.adapters.factory import get_adapter, get_supported_db_types

# 지원 DB 타입: postgresql, oracle
adapter = get_adapter("postgresql")  # DatabaseAdapter 구현체 반환
supported = get_supported_db_types()  # ["postgresql", "oracle"]
```

- PostgreSQL: `LIMIT N`, `information_schema`
- Oracle: `FETCH FIRST N ROWS ONLY`, `ALL_TABLES`

## Code Organization

```
app/
├── main.py                    # FastAPI app + lifespan
├── config.py                  # Pydantic settings
├── api/
│   ├── routes/                # HTTP endpoints (thin layer)
│   │   ├── agent.py           # AI Agent endpoints
│   │   ├── search.py          # RAG/NL2SQL search
│   │   ├── documents.py       # Document management
│   │   ├── settings.py        # Settings management
│   │   └── codes.py           # Code management
│   └── services/              # Business logic layer
│       ├── agent_service.py   # Agent orchestration
│       ├── rag_service.py     # RAG service
│       ├── nl2sql_service.py  # NL2SQL service
│       ├── document_service.py # Document CRUD
│       ├── settings_service.py # Dynamic config
│       └── code_service.py    # Code service
├── graphs/                    # LangGraph workflows (core AI logic)
│   ├── agent_graph.py         # AI Agent (ReAct + Intent Analysis)
│   ├── rag_graph.py           # Document search
│   ├── nl2sql_graph.py        # NL2SQL
│   └── nodes/                 # 분리된 노드 모듈
│       ├── __init__.py
│       ├── agent_nodes.py     # intent_analysis_node, context_retrieval_node
│       ├── nl2sql_nodes.py    # NL2SQL 노드 함수들
│       └── rag_nodes.py       # RAG 노드 함수들
├── graphs/agent/tools/        # AI Agent tools (ReAct 패턴에서만 사용)
│   ├── base.py                # BaseTool class with hooks
│   ├── sql_tool.py            # SQL query tool
│   ├── rag_tool.py            # Document search tool
│   └── calc_tool.py           # Calculator tool (safe AST)
├── core/                      # Core infrastructure
│   ├── database/              # Database layer
│   │   ├── adapters/          # DB adapter pattern
│   │   │   ├── base.py        # DatabaseAdapter ABC
│   │   │   ├── postgresql.py  # PostgreSQL adapter
│   │   │   ├── oracle.py      # Oracle adapter
│   │   │   └── factory.py     # Adapter factory
│   │   ├── connection.py      # Connection pool (psycopg3)
│   │   ├── external.py        # External DB manager
│   │   ├── schema_loader.py   # DB schema introspection
│   │   └── sql_executor.py    # SQL validation + execution
│   ├── llm/                   # LLM layer
│   │   ├── llm_config.py      # Unified LLM configuration
│   │   ├── prompt_service.py  # Prompt templates
│   │   └── sql_generator.py   # SQL generation
│   ├── vector/                # Vector search layer
│   │   ├── vector_store.py    # Embedding + pgvector
│   │   └── text_chunker.py    # Document chunking
│   └── config/                # Configuration
│       └── settings_config.py # Settings schema
├── models/                    # Pydantic models (API contracts)
│   ├── agent.py, rag.py, search.py, documents.py, settings.py, codes.py, common.py
└── utils/                     # Utilities
    ├── logger.py              # Structured logging
    ├── langsmith.py           # LangSmith integration
    └── common.py              # Common utilities

frontend/src/
├── views/
│   ├── user/
│   │   └── UserChatView.vue   # User chat interface (dark mode default)
│   └── admin/                 # Admin views
│       ├── AdminLayout.vue    # Admin navigation wrapper
│       ├── ChatView.vue       # Admin chat interface
│       ├── DashboardView.vue  # Dashboard/analytics
│       ├── DocumentsView.vue  # Document management
│       ├── DocumentDetailView.vue  # Document detail
│       ├── DocumentEditView.vue    # Document editor
│       ├── SettingsView.vue   # Settings management
│       └── CodesView.vue      # Code management
├── components/
│   ├── chat/                  # Chat components
│   │   └── PromptGuideModal.vue # Prompt guide modal (NL2SQL/RAG examples)
│   ├── user/                  # User-facing components
│   │   ├── UserChatLayout.vue
│   │   ├── UserChatMessage.vue
│   │   └── UserChatSidebar.vue
│   └── layout/                # Layout components
├── store/                     # Vuex state
│   └── modules/               # chat.js, document.js, app.js
└── api/                       # Axios API clients

scripts/
├── init_db.py                 # DB initialization
├── embed_documents.py         # Document embedding
├── check_oracle_schema.py     # Oracle schema validation
├── check_tools_config.py      # Tool configuration checker
└── sql/                       # SQL scripts
```

### Request Flow Examples

**AI Agent Flow** (ReAct + Intent Analysis):
```
User question → api/routes/agent.py
  → api/services/agent_service.py
    → graphs/agent_graph.py:ainvoke(state, config={thread_id})
      → intent_analysis_node (의도 분석)
      → context_retrieval_node (SQL 컨텍스트 검색)
      → agent_node → tools_node → agent_node (loop)
    → END (InMemorySaver auto-saves session)
  → Return AgentResponse
```

**NL2SQL Flow**:
```
User query → api/routes/search.py
  → api/services/nl2sql_service.py
    → graphs/nl2sql_graph.py:ainvoke()
      → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate
        → validate_sql → execute_sql → generate_answer (with retry on error)
  → Return NL2SQLResponse
```

## Critical Implementation Details

### Security - NL2SQL

**SQL Injection Prevention** (`app/core/database/sql_executor.py`):
1. Keyword blacklist: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. Table whitelist: Only allowed tables
3. SELECT-only enforcement via sqlparse
4. Timeout: 30-second
5. Row limit: Auto-add via adapter

### Logging Conventions

```python
request_id = str(uuid.uuid4())[:8]
logger.info(f"[{request_id}] [STEP] [STAGE] Message | key=value")
```

**Agent stages**: INIT → INTENT → CONTEXT → THINK → ACTION → OBSERVE → FINISH → COMPLETE
**NL2SQL stages**: INIT → GENERATE → VALIDATE → EXECUTE → ANSWER → COMPLETE
**RAG stages**: INIT → RETRIEVE → GENERATE → COMPLETE

log_step은 가능한 한줄에 작성하라.

## Environment Variables

```bash
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/hr_chatbot

# OpenAI API (Required)
OPENAI_API_KEY=sk-proj-...

# Anthropic API (Optional)
ANTHROPIC_API_KEY=sk-ant-...

# LLM Provider
LLM_PROVIDER=openai           # openai or anthropic
EMBEDDING_PROVIDER=openai     # openai only (Anthropic doesn't provide embeddings)

# Application
APP_ENV=development
LOG_LEVEL=INFO
LOG_FORMAT=text               # text or json
LOG_FILE=./logs/app.log       # Optional, None for no file output
```

**Priority**: Admin UI (DB) > `.env` > code defaults

**Test Database**:
```bash
DATABASE_URL=postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb
```

## Common Patterns

### Adding a New Graph Node

**In separate node file** (`app/graphs/nodes/new_nodes.py`):
```python
from typing import Dict, Any

def new_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node description - returns only updated fields"""
    request_id = state.get("request_id", "unknown")

    # Process state
    result = do_something(state["question"])

    # Return only changed fields (LangGraph merges automatically)
    return {
        "new_field": result,
        "another_field": "value"
    }
```

**In graph class** (`app/graphs/agent_graph.py`):
```python
from app.graphs.nodes.new_nodes import new_node

# In _build_graph()
workflow.add_node("new_node", new_node)
workflow.add_edge("prev_node", "new_node")
```

### Adding a New AI Agent Tool

```python
# 1. Create tool class in app/graphs/agent/tools/new_tool.py
from app.graphs.agent.tools.base import BaseTool, ToolResult
from langchain_core.tools import tool

class NewTool(BaseTool):
    @property
    def name(self) -> str:
        return "new_tool"

    def _execute(self, param1: str, **kwargs) -> ToolResult:
        result = process(param1)
        return ToolResult(success=True, data=result)

# 2. Create LangChain tool wrapper
@tool
def new_tool_func(param1: str) -> str:
    """Tool description for LLM"""
    tool_instance = NewTool()
    result = tool_instance.execute(param1=param1)
    return str(result.data) if result.success else f"Error: {result.error}"

# 3. Register in app/graphs/agent/nodes/agent_node.py _get_tools()
```

### Adding Dynamic Settings

```python
# 1. Add to app/config.py
class Settings(BaseSettings):
    new_setting: str = "default_value"

# 2. Insert into DB
INSERT INTO tb_app_settings (category, key, value, value_type, description)
VALUES ('category', 'new_setting', 'default', 'string', 'Description');

# 3. Use in code
value = settings_service.get_value("category", "new_setting", settings.new_setting)
```

### Adding New Database Adapter

1. Create adapter in `app/core/database/adapters/newdb.py` extending `DatabaseAdapter`
2. Register in `app/core/database/adapters/factory.py`:
   ```python
   _ADAPTERS["newdb"] = NewDBAdapter
   DEFAULT_PORTS["newdb"] = 3306
   ```
3. Update prompts in `app/core/llm/prompt_service.py`

## Deployment

### Docker

```bash
# Backend
docker build -t mureum-backend .
docker run -p 19090:19090 mureum-backend

# Frontend
cd frontend
docker build -t mureum-frontend .
docker run -p 80:80 mureum-frontend
```

**Files**:
- `Dockerfile` - Backend container
- `frontend/Dockerfile` - Frontend container
- `deploy-docker.sh` - Deployment script
- `frontend/nginx.conf` - Nginx configuration
- `frontend/.env.development`, `.env.docker`, `.env.production` - Environment configs

## Known Issues & Workarounds

### Model Not Found (404)
**Fix**: Check valid model names at provider docs, update via Admin UI → Settings → LLM

### Vector Search Returns Nothing
**Fix**: Check `indexed=true` in tb_docs, run embedding, lower similarity_threshold

### DB Connection Pool Exhausted
**Fix**: Increase `DB_POOL_SIZE` in `.env` (default: 20)

### Intent Analysis Not Working
**Fix**: Ensure `config.enable_intent_analysis=True` in AgentConfig

## Dependencies (requirements.txt)

```python
# Core: Python 3.10+ required, 3.13 tested
fastapi>=0.115.0, pydantic>=2.7.4, pydantic-settings>=2.1.0

# Database
psycopg[binary,pool]>=3.2.0, pgvector>=0.2.5, oracledb>=2.0.0

# LangChain v1.0+
langchain-core>=1.2.5, langchain>=1.2.0, langchain-openai>=1.1.6
langchain-anthropic>=0.2.4, langgraph>=1.0.5
openai>=1.30.0, anthropic>=0.39.0

# Utilities
numpy>=1.26.2, sqlparse>=0.4.4, python-json-logger>=2.0.7
```

**Import Pattern** (LangChain v1.0):
```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # ✅ Correct
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
```

---

중요:
- 가상환경: `conda activate penv3.13-nlq`
- DB확인: `postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb`
- DB스크립트 및 데이터:  docs/sql/psql-hermes_db.sql
- 로그파일 : ./logs/app.log 
- log_step출력: log_step는 로그이니 다른비즈니스 로직과 분리하여 한줄에 출력하라.
- 변경시에는 항상 변경된 소스코드파일 및 변경된 내용에 대해 설명을하라.
- __init__에는 가능한 파일만 생성하고 import모듈등은 구현하지 말라.
- css의 style는 asset/styles/mixins하위 디렉토리를 참조하라.
