# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MUREUM is an enterprise AI knowledge base assistant combining multiple AI techniques for natural language search over documents and databases. The system features an AI Agent (ReAct pattern), RAG, and NL2SQL capabilities with multi-turn conversation support.

**Stack**: FastAPI + LangGraph + PostgreSQL (pgvector) + Vue 3 + Multi-LLM Provider (OpenAI, Anthropic) + Multi-DB Support (PostgreSQL, Oracle)

**Python Version**: 3.13 (Conda 환경: `penv3.13-nlq`)

**LangChain Version**: v1.0+ (langchain>=1.2.0, langchain-core>=1.2.5, langgraph>=1.0.5)

**Key Features**:
- AI Agent with ReAct pattern (autonomous tool selection, multi-step reasoning)
- NL2SQL with **multi-turn conversation** (session-based history, intent rewrite, PII filter)
- RAG document search with vector embeddings (pgvector)
- Multi-turn conversations with session-based memory (InMemorySaver)
- SSE streaming for real-time responses (Agent, NL2SQL)
- Dynamic settings management (DB-based real-time configuration)
- Multi-LLM provider support (OpenAI, Anthropic via init_chat_model)
- Multi-DB support for NL2SQL (PostgreSQL, Oracle via adapter pattern)
- PII detection and masking (Agent middleware, NL2SQL pipeline)

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
- Checkpointing: InMemorySaver for session-based conversation memory (Agent, NL2SQL)

**AI Agent Flow** (ReAct - `app/graphs/agent/graph.py`):
```
┌──────────────────────────────────────────────────────────┐
│  START → agent_node → should_continue() decision         │
│                        ├─ "tools" → tools_node → agent   │
│                        └─ "answer" → answer_node → END   │
└──────────────────────────────────────────────────────────┘
```

**NL2SQL Flow** (Multi-turn + Intent Analysis + PII Filter - `app/graphs/nl2sql/graph.py`):
```
load_history → intent_rewrite → should_route_after_intent
                                 ├─ sql_needed → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                 │                                                                                      ├─ execute → execute_sql → should_continue_after_execute
                                 │                                                                                      │                            ├─ answer → pii_filter → generate_answer → save_history → END
                                 │                                                                                      │                            ├─ retry → prepare_retry → fewshot_retrieval
                                 │                                                                                      │                            └─ error → handle_error → END
                                 │                                                                                      ├─ retry → prepare_retry → fewshot_retrieval
                                 │                                                                                      └─ error → handle_error → END
                                 └─ sql_not_needed → answer_from_history → save_history → END
```

**RAG Flow** (`app/graphs/rag/graph.py`):
```
retrieve → generate_answer → END
```

### AgentState (ReAct 상태 관리)

Agent 상태는 TypedDict로 정의됩니다 (`app/graphs/agent/state.py`):

```python
class AgentState(TypedDict):
    # ===== 기본 필드 =====
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 히스토리 (누적)
    question: str                        # 원본 질문
    session_id: str                      # 세션 ID (멀티턴)
    request_id: str                      # 요청 추적 ID

    # ===== ReAct 제어 필드 =====
    iteration_count: int                 # 현재 반복 횟수
    max_iterations: int                  # 최대 반복 횟수
    final_answer: str                    # 최종 답변

    # ===== 설정 =====
    config: AgentConfig                  # Agent 설정

    # ===== Tool 결과 =====
    last_tool_name: str                  # 마지막 사용 Tool
    last_tool_result: str                # 마지막 Tool 결과

    # ===== SQL Tool 결과 (프론트엔드 표시용) =====
    generated_sql: str                   # 생성된 SQL
    sql_result: Optional[SQLResult]      # SQL 실행 결과

    # ===== RAG Tool 결과 =====
    rag_sources: List[Dict]              # 검색된 문서 목록

    # ===== 메타데이터 =====
    tools_used: List[str]                # 사용된 Tool 목록
    start_time: float                    # 시작 시간
```

**초기 상태 생성**:
```python
from app.graphs.agent.state import create_initial_state

initial_state = create_initial_state(
    question="사용자 질문",
    session_id="session-123",
    request_id="abc12345",
    config=AgentConfig(),
    max_iterations=10,
)
initial_state["messages"] = [HumanMessage(content=question)]
```

### NL2SQLState (멀티턴 상태 관리)

NL2SQL 상태는 멀티턴 대화와 의도 분석을 포함합니다 (`app/graphs/nl2sql/state.py`):

```python
class NL2SQLState(TypedDict):
    # 기본 필드: question, schema_description, generated_sql, validated, sql_result, answer, metadata, request_id
    # 스키마 검색: selected_tables, schema_retrieval_confidence
    # Few-shot: fewshot_context, fewshot_examples, fewshot_count
    # 프롬프트: sql_prompt, user_prompt, prompt_metadata
    # 재시도: retry_count, max_retries, previous_sql, previous_error, enhanced_fewshot
    # 멀티턴: session_id, conversation_history, current_turn, max_turns, history_truncated
    # 의도 분석: query_type, rewritten_question, intent_reasoning, sql_result_summary
```

### Async/Await Pattern

**CRITICAL**: All graph invocations and API endpoints use `async/await`:
- FastAPI endpoints: `async def search()`
- Graph execution: `await graph.ainvoke(inputs)`
- SSE streaming: `async for chunk in graph.astream(inputs)`

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
- `tb_api_history`: API 요청 이력 (history middleware 자동 저장)
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

**External Business DB** (`app/core/database/external.py`):
```python
from app.core.database.external import external_db_manager
# NL2SQL 대상 DB (PostgreSQL 또는 Oracle)
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

### SSE Streaming

Agent와 NL2SQL은 SSE(Server-Sent Events) 스트리밍을 지원합니다:
- `app/core/sse/stream_manager.py`: SSE 포맷팅, 스테이지 그룹핑
- `app/models/sse.py`: NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent
- Agent: `astream_events()` → 노드별 스테이지 이벤트 전송
- NL2SQL: `astream_events()` → forward-only 스테이지 전환 (재시도 루프 시 뒤로 안 감)

### Error Handling

통일된 에러 처리 시스템 (`app/core/errors/`):
- `error_codes.py`: ErrorCode enum 정의
- `handlers.py`: FastAPI 전역 예외 핸들러
- `response.py`: 표준화된 응답 포맷 (success_response, error_response)

### Middleware

**FastAPI Middleware** (`app/middleware/`):
```
요청 순서: LoggingMiddleware → HistoryMiddleware → CORSMiddleware → Handler
응답 순서: Handler → CORSMiddleware → HistoryMiddleware → LoggingMiddleware
```
- `logging.py`: 요청/응답 로깅 + request_id 생성
- `history.py`: API 요청 이력 DB 저장 (비동기 워커)
- `base.py`: 미들웨어 베이스 클래스

**Agent Middleware** (`app/graphs/agent/middleware/`):
- `chain.py`: 미들웨어 체인 실행기
- `pii.py`: PII 필터링 미들웨어
- `base.py`: 미들웨어 베이스 클래스

## Code Organization

```
app/
├── main.py                    # FastAPI app + lifespan + router/middleware 등록
├── config.py                  # Pydantic settings
├── api/
│   ├── routes/                # HTTP endpoints (thin layer)
│   │   ├── agent.py           # AI Agent endpoints (search, stream, sessions, tools)
│   │   ├── search.py          # RAG/NL2SQL search (auto/rag/nl2sql + stream)
│   │   ├── documents.py       # Document management CRUD
│   │   ├── settings.py        # Settings management
│   │   ├── codes.py           # Code management
│   │   ├── history.py         # API 요청 이력 (필터, 통계, 세션별)
│   │   └── export.py          # Excel 내보내기
│   └── services/              # Business logic layer
│       ├── agent_service.py   # Agent orchestration (→ graphs/agent/graph.py)
│       ├── rag_service.py     # RAG orchestration (→ graphs/rag/graph.py)
│       ├── nl2sql_service.py  # NL2SQL orchestration (→ graphs/nl2sql/graph.py)
│       ├── document_service.py # Document CRUD
│       ├── settings_service.py # Dynamic config (DB fallback chain)
│       ├── code_service.py    # Code service
│       ├── history_service.py # 이력 저장 (비동기 워커 큐)
│       └── export_service.py  # Excel export logic
├── graphs/                    # LangGraph workflows (core AI logic)
│   ├── agent/                 # AI Agent (ReAct 패턴)
│   │   ├── graph.py           # InsightAgentGraph 클래스
│   │   ├── state.py           # AgentState TypedDict + create_initial_state()
│   │   ├── nodes/             # Agent 노드 함수들
│   │   │   ├── agent_node.py  # LLM Think/Action + should_continue()
│   │   │   ├── tools_node.py  # Tool 실행 라우터
│   │   │   └── answer_node.py # 최종 답변 생성
│   │   ├── tools/             # AI Agent tools (ReAct에서 LLM이 선택)
│   │   │   ├── base.py        # BaseTool ABC, ToolResult, ToolValidator, ToolMetrics
│   │   │   ├── sql_tool.py    # SQL query tool (query_database_tool)
│   │   │   ├── rag_tool.py    # Document search tool
│   │   │   └── calc_tool.py   # Calculator tool (safe AST)
│   │   └── middleware/        # Agent 미들웨어
│   │       ├── base.py        # Middleware base class
│   │       ├── chain.py       # MiddlewareChain (input/output processing)
│   │       └── pii.py         # PIIMiddleware
│   ├── nl2sql/                # NL2SQL (멀티턴 + 의도분석 + PII 필터)
│   │   ├── graph.py           # NL2SQLGraph 클래스 (세션 관리 포함)
│   │   ├── state.py           # NL2SQLState TypedDict + create_initial_state()
│   │   └── nodes.py           # 모든 NL2SQL 노드 함수 (14개)
│   └── rag/                   # RAG (문서 검색)
│       ├── graph.py           # RAGGraph 클래스
│       ├── state.py           # RAGState TypedDict + create_initial_state()
│       └── nodes.py           # retrieve_documents_node, generate_answer_node
├── core/                      # Core infrastructure
│   ├── database/              # Database layer
│   │   ├── connection.py      # Connection pool (psycopg3) - db_manager
│   │   ├── external.py        # External DB manager (NL2SQL 대상 DB)
│   │   ├── schema_loader.py   # DB schema introspection
│   │   ├── sql_executor.py    # SQL validation + execution
│   │   ├── table_catalog.py   # Table metadata caching
│   │   └── adapters/          # DB adapter pattern
│   │       ├── base.py        # DatabaseAdapter ABC
│   │       ├── postgresql.py  # PostgreSQL adapter
│   │       ├── oracle.py      # Oracle adapter
│   │       └── factory.py     # Adapter factory (get_adapter, get_supported_db_types)
│   ├── llm/                   # LLM layer
│   │   ├── llm_config.py      # LLMConfigManager (create_llm, get_rag_settings)
│   │   ├── prompt_service.py  # Prompt templates (agent, nl2sql, rag)
│   │   └── sql_generator.py   # SQL generation orchestration
│   ├── vector/                # Vector search layer
│   │   ├── vector_store.py    # Embedding + pgvector search
│   │   └── text_chunker.py    # Document chunking
│   ├── pii/                   # PII 처리
│   │   └── pii_service.py     # PII detection + masking
│   ├── sse/                   # Server-Sent Events
│   │   └── stream_manager.py  # format_sse, get_node_stage, get_stage_label
│   ├── errors/                # Error handling
│   │   ├── error_codes.py     # ErrorCode enum
│   │   ├── handlers.py        # 전역 예외 핸들러 (register_exception_handlers)
│   │   └── response.py        # success_response, error_response
│   └── config/                # Configuration
│       └── settings_config.py # Settings schema (settings_config)
├── models/                    # Pydantic models (API contracts)
│   ├── agent.py               # AgentRequest, AgentResponse, AgentConfig, AgentStep, AgentSQLResult
│   ├── search.py              # SearchRequest, SearchResponse, SearchFilters, ExcelExportRequest
│   ├── rag.py                 # DocumentSource, SQLResult
│   ├── documents.py           # Document CRUD models
│   ├── settings.py            # Settings models
│   ├── codes.py               # Code management models
│   ├── history.py             # History models
│   ├── sse.py                 # NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent
│   └── common.py              # Common shared models
├── middleware/                 # FastAPI middleware
│   ├── base.py                # Middleware base class
│   ├── logging.py             # Request/response logging + request_id 생성
│   └── history.py             # API history recording (async worker)
└── utils/                     # Utilities
    ├── logger.py              # Structured logging + log_step()
    ├── langsmith.py           # LangSmith integration (init_langsmith)
    └── common.py              # truncate_text 등 유틸리티

frontend/src/
├── views/
│   ├── user/
│   │   └── UserChatView.vue          # User chat interface (dark mode default)
│   └── admin/
│       ├── AdminLayout.vue           # Admin navigation wrapper
│       ├── ChatView.vue              # Admin chat interface
│       ├── DashboardView.vue         # Dashboard/analytics
│       ├── DocumentsView.vue         # Document management
│       ├── DocumentDetailView.vue    # Document detail
│       ├── DocumentEditView.vue      # Document editor
│       ├── SettingsView.vue          # Settings management
│       ├── CodesView.vue             # Code management
│       ├── HistoryView.vue           # API history
│       └── HistoryDetailView.vue     # History detail
├── components/
│   ├── chat/                  # Chat components
│   │   ├── ChatMessage.vue    # Message display (admin)
│   │   ├── ChatInput.vue      # Message input
│   │   ├── SourceCard.vue     # Source document display
│   │   └── PromptGuideModal.vue # NL2SQL/RAG examples modal
│   ├── chart/                 # Chart components
│   │   └── ChartBuilder.vue   # SQL result chart visualization
│   ├── user/                  # User-facing components
│   │   ├── UserChatLayout.vue
│   │   ├── UserChatMessage.vue
│   │   └── UserChatSidebar.vue
│   ├── documents/
│   │   └── ChunkPreview.vue   # Document chunk preview
│   └── layout/
│       ├── AppHeader.vue
│       └── AppSidebar.vue
├── api/                       # Axios API clients
│   ├── index.js               # Axios instance + interceptors
│   ├── agent.js               # Agent API
│   ├── search.js              # Search API (RAG/NL2SQL)
│   ├── documents.js           # Document API
│   ├── settings.js            # Settings API
│   ├── codes.js               # Code API
│   ├── history.js             # History API
│   └── sse.js                 # SSE stream client
├── store/modules/             # Vuex state management
│   ├── chat.js                # Chat conversation state
│   ├── document.js            # Document state
│   └── app.js                 # Global app state
└── assets/styles/
    ├── _variables.scss         # CSS variables
    ├── main.scss               # Main stylesheet
    └── mixins/                 # SCSS mixins (스타일 참조 필수)
        ├── _index.scss
        ├── _animations.scss
        ├── _cards.scss
        ├── _chart.scss
        ├── _chat.scss
        ├── _forms.scss
        ├── _layout.scss
        └── _markdown.scss

scripts/
├── add_multiturn_settings.py  # Multi-turn settings initialization
├── check_oracle_schema.py     # Oracle schema validation
├── check_tools_config.py      # Tool configuration checker
├── check_feedback.py          # Feedback data validation

tests/
├── test_agent.py              # Agent + Calculator tool tests
├── test_classfy.py            # Classification tests
├── test_pii_service.py        # PII service tests
└── test_pii_redaction.py      # PII redaction tests
```

### Request Flow Examples

**AI Agent Flow** (ReAct):
```
User question → api/routes/agent.py
  → api/services/agent_service.py
    → graphs/agent/graph.py:ainvoke(inputs)
      → middleware.process_input()
      → create_initial_state()
      → agent_node → tools_node → agent_node (loop) → answer_node
      → middleware.process_output()
    → END (InMemorySaver auto-saves session)
  → Return AgentResponse
```

**NL2SQL Flow** (Multi-turn):
```
User query → api/routes/search.py
  → api/services/nl2sql_service.py
    → graphs/nl2sql/graph.py:ainvoke(inputs)
      → load_history → intent_rewrite
        → sql_needed? → schema → fewshot → prompt → generate → validate → execute → pii_filter → answer → save_history
        → sql_not_needed? → answer_from_history → save_history
    → END (InMemorySaver auto-saves session)
  → Return SearchResponse
```

**RAG Flow**:
```
User query → api/routes/search.py
  → api/services/rag_service.py
    → graphs/rag/graph.py:ainvoke(inputs)
      → retrieve_documents → generate_answer
  → Return SearchResponse
```

## Critical Implementation Details

### Security - NL2SQL

**SQL Injection Prevention** (`app/core/database/sql_executor.py`):
1. Keyword blacklist: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. Table whitelist: Only allowed tables
3. SELECT-only enforcement via sqlparse
4. Timeout: 30-second
5. Row limit: Auto-add via adapter

### PII Protection

- **Agent**: `app/graphs/agent/middleware/pii.py` - 입출력 PII 마스킹
- **NL2SQL**: `pii_filter_node` - SQL 결과의 PII를 LLM 전송 전 마스킹
- **Core**: `app/core/pii/pii_service.py` - PII 감지 및 마스킹 서비스

### Logging Conventions

```python
request_id = str(uuid.uuid4())[:8]
log_step(logger, request_id, "MODULE", "STEP", "ACTION", "Message", key=value)
```

**Agent stages**: INIT → THINK → ACTION → OBSERVE → FINISH → COMPLETE
**NL2SQL stages**: INIT → INTENT → GENERATE → VALIDATE → EXECUTE → ANSWER → COMPLETE
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

**In node file** (`app/graphs/{workflow}/nodes.py`):
```python
from typing import Dict, Any

def new_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node description - returns only updated fields"""
    request_id = state.get("request_id", "unknown")
    result = do_something(state["question"])
    return {"new_field": result}
```

**In graph class** (`app/graphs/{workflow}/graph.py`):
```python
from app.graphs.{workflow}.nodes import new_node

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
- `deploy-docker.sh` - Backend deployment script (SSH + Docker)
- `frontend/deploy-docker.sh` - Frontend deployment script
- `frontend/nginx.conf` - Nginx configuration
- `frontend/.env.development`, `.env.docker`, `.env.production` - Environment configs

## Known Issues & Workarounds

### Model Not Found (404)
**Fix**: Check valid model names at provider docs, update via Admin UI → Settings → LLM

### Vector Search Returns Nothing
**Fix**: Check `indexed=true` in tb_docs, run embedding, lower similarity_threshold

### DB Connection Pool Exhausted
**Fix**: Increase `DB_POOL_SIZE` in `.env` (default: 20)

### FastAPI Reload Not Detecting Changes
**Fix**: 서버 수동 재기동 필요 (`--reload` 모드에서도 감지 안 될 수 있음)

### Route Order Matters
**Fix**: `/sessions` 같은 고정 경로는 `/{request_id}` 같은 파라미터 경로보다 **앞에** 배치

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
aiofiles>=24.1.0, httpx>=0.27.0, openpyxl>=3.1.0

# Monitoring (Optional)
prometheus-client>=0.19.0
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
- DB 확인할 경우: `postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb`
- DB스크립트 및 데이터:  docs/sql/psql-hermes_db.sql
- 로컬의 로그파일 : ./logs/app.log
- log_step출력: log_step는 로그이니 다른비즈니스 로직과 분리하여 한줄에 출력하라.
- 변경시에는 항상 변경된 소스코드파일 및 변경된 내용에 대해 설명을하라.
- __init__에는 가능한 파일만 생성하고 import모듈등은 구현하지 말라.
- css의 style는 asset/styles/mixins하위 디렉토리를 참조하라.
