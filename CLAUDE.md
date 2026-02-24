# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MUREUM is an enterprise AI knowledge base assistant combining multiple AI techniques for natural language search over documents and databases. The system features an AI Agent (ReAct pattern), RAG, and NL2SQL capabilities with multi-turn conversation support, multi-tenant architecture, and role-based access control.

**Stack**: FastAPI + LangGraph + PostgreSQL (pgvector) + Vue 3 + Multi-LLM Provider (OpenAI, Anthropic) + Multi-DB Support (PostgreSQL, Oracle)

**Python Version**: 3.13 (Conda 환경: `penv3.13-nlq`)

**LangChain Version**: v1.0+ (langchain>=1.2.0, langchain-core>=1.2.5, langgraph>=1.0.5)

**Key Features**:
- AI Agent with ReAct pattern (autonomous tool selection, multi-step reasoning)
- NL2SQL with **multi-turn conversation** (session-based history, intent rewrite, PII filter)
- RAG document search with vector embeddings (pgvector)
- Multi-turn conversations with session-based memory (InMemorySaver)
- SSE streaming for real-time responses (Agent, NL2SQL)
- JWT authentication with role-based access control (GLOBAL/TENANT/USER)
- Multi-tenant architecture with scope-based data isolation
- Menu-based CRUD permission system (tb_user_menu)
- Dynamic settings management (DB-based real-time configuration)
- Multi-LLM provider support (OpenAI, Anthropic via init_chat_model)
- Multi-DB support for NL2SQL (PostgreSQL, Oracle via adapter pattern)
- PII detection and masking (Agent middleware, NL2SQL pipeline)
- Dashboard with KPI, charts, recent activity

**설계 문서**: `docs/design/` 디렉토리 참조

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
# Integration tests (순서대로 실행 권장)
pytest tests/ -v

# Single test file
pytest tests/test_02_auth.py -v

# Single test function
pytest tests/test_02_auth.py::test_login -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### API Health Checks

```bash
# API health check
curl http://localhost:19090/health

# Login (토큰 획득)
curl -X POST "http://localhost:19090/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login_id": "admin", "password": "Admin1234!"}'

# Test AI Agent search
curl -X POST "http://localhost:19090/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"question": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?"}'

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

### Authentication & Authorization

**JWT 인증** (`app/core/security/`):
- Access Token (30분) + Refresh Token (7일, DB 저장)
- 로그인 실패 5회 → 30분 계정 잠금
- bcrypt 패스워드 해싱

**권한 모델** (2계층):
```
tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가"  (기능 접근: CRUD + Export)
tb_role.role_code = "어디까지 볼 수 있는가"       (데이터 범위: GLOBAL/TENANT/USER)
```

**역할 계층**:
| role_code | sort_order | 데이터 범위 | landing_page |
|-----------|-----------|------------|--------------|
| GLOBAL | 1 | 전체 | /admin/dashboard |
| TENANT | 2 | 소속 테넌트 | /admin/dashboard |
| USER | 3 | 본인만 | /chat |

**라우트에서 권한 체크**:
```python
from app.core.security.permission import require_menu_permission

@router.post("")
async def create_user(
    current_user = Depends(require_menu_permission("USER_MGMT", "create"))
):
```

**보안 보호 메커니즘**:
- 시스템 리소스 보호: `is_system` 플래그 (테넌트, 역할 삭제 불가)
- 역할 권한 상승 방지: `sort_order` 기반 (자신보다 상위 역할 할당 불가)
- 역할-테넌트 조합 검증: GLOBAL→시스템테넌트, TENANT/USER→일반테넌트
- 메뉴 권한 상승 방지: 본인 미보유 메뉴 할당 불가
- 슈퍼유저 보호: is_superuser 수정/삭제 불가

### LangGraph Workflow Pattern

This codebase uses **LangGraph** for AI workflows. Understanding the graph execution model is critical:

**Key Concept**: `result = await self.graph.ainvoke(initial_state)`
- Entry point: `workflow.set_entry_point("node_name")`
- Sequential: `workflow.add_edge(from, to)`
- Conditional: `workflow.add_conditional_edges(node, decision_func, mapping)`
- Checkpointing: InMemorySaver for session-based conversation memory (Agent, NL2SQL)

**AI Agent Flow** (ReAct - `app/graphs/agent/graph.py`):
```
START → agent_node → should_continue()
                      ├─ "tools" → tools_node → agent_node (loop)
                      └─ "answer" → answer_node → END
```

**NL2SQL Flow** (Multi-turn + Intent Analysis + PII Filter - `app/graphs/nl2sql/graph.py`):
```
load_history → intent_rewrite → should_route_after_intent
                                 ├─ sql_needed → schema → fewshot → prompt → generate → validate
                                 │                                                        ├─ execute → execute_sql → should_continue_after_execute
                                 │                                                        │                            ├─ answer → pii_filter → generate_answer → save_history → END
                                 │                                                        │                            ├─ retry → prepare_retry → fewshot
                                 │                                                        │                            └─ error → handle_error → END
                                 │                                                        ├─ retry → prepare_retry → fewshot
                                 │                                                        └─ error → handle_error → END
                                 └─ sql_not_needed → answer_from_history → save_history → END
```

**RAG Flow** (`app/graphs/rag/graph.py`):
```
retrieve → generate_answer → END
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
llm = LLMConfigManager.create_llm(temperature=0.0)
```

**Providers**: OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet-20241022)
**Temperature**: 0 for SQL generation, 0.0-0.1 for Agent, 0.1 for answers
**Embeddings**: `text-embedding-3-small` (1536 dimensions)

### Database Architecture

**Service DB** (PostgreSQL with pgvector):
- `tb_tenant`: 멀티테넌트 (is_system 플래그)
- `tb_role`: 역할 정의 (GLOBAL/TENANT/USER, sort_order)
- `tb_user`: 사용자 (role_id, tenant_id, is_superuser)
- `tb_menu`: 메뉴 트리 (parent-child 계층)
- `tb_user_menu`: 권한 매트릭스 (CRUD + Export)
- `tb_user_session`: JWT 세션 (refresh_token)
- `tb_docs`: Documents + embeddings (RAG source)
- `tb_app_settings`: Dynamic configuration
- `tb_api_history`: API 요청 이력 (history middleware 자동 저장)
- `tb_code_group`, `tb_code_item`: 코드 관리

**External Business DB** (`app/core/database/external.py`):
- NL2SQL 대상 DB (PostgreSQL 또는 Oracle)
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
adapter = get_adapter("postgresql")  # postgresql, oracle
```

### SSE Streaming

Agent와 NL2SQL은 SSE(Server-Sent Events) 스트리밍을 지원합니다:
- `app/core/sse/stream_manager.py`: SSE 포맷팅, 스테이지 그룹핑
- `app/models/sse.py`: NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent
- Agent: `astream_events()` → 노드별 스테이지 이벤트 전송
- NL2SQL: `astream_events()` → forward-only 스테이지 전환

### Error Handling

통일된 에러 처리 시스템 (`app/core/errors/`):
- `error_codes.py`: ErrorCode enum (VALIDATION, AUTH, FORBIDDEN, NOT_FOUND 등 12종)
- `handlers.py`: FastAPI 전역 예외 핸들러
- `response.py`: 표준화된 응답 포맷 (success_response, error_response)

### API 응답 표준 패턴

**모든 API 응답은 `success_response()` 래퍼를 사용** (`app/core/errors/response.py`):
```json
{"success": true, "data": { ... }, "error": null}
{"success": false, "data": null, "error": {"code": "...", "message": "...", "detail": "..."}}
```

프론트엔드 Axios 인터셉터(`frontend/src/api/index.js`)가 `result.data`를 자동 언래핑하므로, 프론트엔드 코드는 항상 내부 `data`만 직접 받음.

**응답 유형별 표준 패턴:**

| 작업 | HTTP Status | data 구조 | 예시 |
|------|-------------|-----------|------|
| CREATE | 201 | 생성된 객체 | `{"user_id": 1, "login_id": "admin", ...}` |
| GET (단건) | 200 | 객체 | `{"user_id": 1, ...}` |
| GET (목록) | 200 | `{"items": [...], "total": N}` | `{"items": [{...}, {...}], "total": 25}` |
| UPDATE | 200 | 수정된 객체 | `{"user_id": 1, "display_name": "변경됨", ...}` |
| DELETE | 200 | `{"message": "...", "deleted_count": N}` | `{"message": "삭제되었습니다", "deleted_count": 1}` |
| REORDER | 200 | `{"message": "...", "updated_count": N}` | `{"message": "순서가 변경되었습니다", "updated_count": 3}` |
| BULK DELETE | 200 | `{"message": "...", "total_deleted": N}` | `{"message": "일괄 삭제 완료", "total_deleted": 5}` |

**라우트 작성 규칙:**
```python
from fastapi import status

# CREATE → 반드시 status_code=201
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_item(...):
    result = service.create(...)
    return success_response(result)

# LIST → items/total 구조
@router.get("")
async def list_items(...):
    items, total = service.list(...)
    return success_response({"items": items, "total": total})

# DELETE → message/deleted_count
@router.delete("/{item_id}")
async def delete_item(...):
    service.delete(item_id)
    return success_response({"message": "삭제되었습니다", "deleted_count": 1})
```

**서비스 작성 시 주의:**
- `get_cursor(commit=True)` 사용 시, 커밋이 필요한 조회(`get_by_id` 등)는 반드시 `with` 블록 **밖에서** 호출
```python
# ✅ 올바른 패턴
with db_manager.get_cursor(commit=True) as cur:
    cur.execute("UPDATE ...")
# 커밋 완료 후 조회
return self.get_by_id(item_id)

# ❌ 잘못된 패턴 (커밋 전 조회 → 이전 데이터 반환)
with db_manager.get_cursor(commit=True) as cur:
    cur.execute("UPDATE ...")
    return self.get_by_id(item_id)  # 아직 커밋 안 됨!
```

### Middleware

**FastAPI Middleware** (`app/middleware/`):
```
등록 순서: HistoryMiddleware → AuthMiddleware → LoggingMiddleware → CORSMiddleware
요청 실행: CORS → Logging → Auth → History → Handler
응답 실행: Handler → History → Auth → Logging → CORS
```
- `logging.py`: 요청/응답 로깅 + request_id 생성
- `auth.py`: JWT 토큰 검증 → `request.state.current_user` 설정 (선택적 모드)
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
├── config.py                  # Pydantic settings (JWT, 보안 설정 포함)
├── api/
│   ├── routes/                # HTTP endpoints (thin layer)
│   │   ├── auth.py            # 인증 (login/logout/refresh/me/password)
│   │   ├── agent.py           # AI Agent (search, stream, sessions, tools)
│   │   ├── search.py          # RAG/NL2SQL search (auto/rag/nl2sql + stream)
│   │   ├── documents.py       # Document management CRUD
│   │   ├── users.py           # 사용자 CRUD + options + 메뉴 권한 할당
│   │   ├── roles.py           # 역할 CRUD + default-menus
│   │   ├── menus.py           # 메뉴 트리 CRUD + reorder
│   │   ├── tenants.py         # 테넌트 CRUD
│   │   ├── settings.py        # Settings management
│   │   ├── codes.py           # Code management + public lookup
│   │   ├── history.py         # API 이력 (필터, 통계, 세션별)
│   │   ├── dashboard.py       # 대시보드 KPI/차트/최근활동
│   │   └── export.py          # Excel 내보내기
│   └── services/              # Business logic layer
│       ├── auth_service.py    # 인증 (로그인, 토큰, 세션, 권한 조회)
│       ├── agent_service.py   # Agent orchestration (→ graphs/agent/graph.py)
│       ├── rag_service.py     # RAG orchestration (→ graphs/rag/graph.py)
│       ├── nl2sql_service.py  # NL2SQL orchestration (→ graphs/nl2sql/graph.py)
│       ├── document_service.py # Document CRUD
│       ├── user_service.py    # 사용자 CRUD + 권한 상승 방지 + scope 필터
│       ├── role_service.py    # 역할 CRUD + 기본 메뉴
│       ├── menu_service.py    # 메뉴 트리 CRUD + reorder
│       ├── tenant_service.py  # 테넌트 CRUD + is_system 보호
│       ├── settings_service.py # Dynamic config (DB fallback chain)
│       ├── code_service.py    # Code service
│       ├── history_service.py # 이력 저장 (비동기 워커 큐)
│       ├── dashboard_service.py # 대시보드 통합 데이터 (KPI, 추이, 시스템)
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
│   ├── security/              # 인증/인가 시스템
│   │   ├── jwt.py             # JWT 생성/검증 (Access + Refresh)
│   │   ├── password.py        # bcrypt 해싱/검증
│   │   ├── dependencies.py    # get_current_user, get_current_active_user
│   │   ├── permission.py      # require_menu_permission, require_superuser
│   │   └── tenant_context.py  # ContextVar 기반 테넌트 컨텍스트
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
│   │       └── factory.py     # Adapter factory
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
│   ├── auth.py                # LoginRequest, TokenResponse, UserContext, MenuPermission
│   ├── user.py                # UserCreate/Update/Response, RoleCreate/Update/Response
│   ├── menu.py                # MenuCreate/Update, MenuTreeResponse, UserMenuPermission
│   ├── tenant.py              # TenantCreate/Update/Response
│   ├── agent.py               # AgentRequest, AgentResponse, AgentConfig
│   ├── search.py              # SearchRequest, SearchResponse, SearchFilters
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
│   ├── auth.py                # JWT 인증 미들웨어 (선택적 모드)
│   └── history.py             # API history recording (async worker)
└── utils/                     # Utilities
    ├── logger.py              # Structured logging + log_step()
    ├── langsmith.py           # LangSmith integration (init_langsmith)
    └── common.py              # truncate_text 등 유틸리티

frontend/src/
├── views/
│   ├── LoginView.vue                 # 로그인 페이지
│   ├── user/
│   │   └── UserChatView.vue          # User chat interface (dark mode default)
│   └── admin/
│       ├── AdminLayout.vue           # Admin navigation wrapper
│       ├── DashboardView.vue         # Dashboard (KPI, 차트, 최근활동)
│       ├── ChatView.vue              # Admin chat interface
│       ├── DocumentsView.vue         # Document management
│       ├── DocumentDetailView.vue    # Document detail
│       ├── DocumentEditView.vue      # Document editor
│       ├── UsersView.vue             # 사용자 관리 (CRUD + 메뉴 권한)
│       ├── RolesView.vue             # 역할 관리
│       ├── MenusView.vue             # 메뉴 트리 관리
│       ├── TenantsView.vue           # 테넌트 관리
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
│   ├── dashboard/             # Dashboard components
│   │   ├── KpiCards.vue       # KPI 요약 카드 (4개)
│   │   ├── DailyTrendChart.vue # 일별 요청 추이 (Stacked Bar)
│   │   ├── RequestTypeChart.vue # 검색 유형 분포 (Donut)
│   │   ├── RecentActivity.vue # 최근 검색 요청 피드
│   │   └── SystemStatus.vue   # 시스템 현황 패널
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
│   ├── index.js               # Axios instance + interceptors (401 auto-refresh)
│   ├── auth.js                # 인증 API (login/logout/refresh/me)
│   ├── agent.js               # Agent API
│   ├── search.js              # Search API (RAG/NL2SQL)
│   ├── documents.js           # Document API
│   ├── users.js               # 사용자 관리 + options API
│   ├── roles.js               # 역할 관리 API
│   ├── menus.js               # 메뉴 관리 API
│   ├── tenants.js             # 테넌트 관리 API
│   ├── dashboard.js           # 대시보드 API
│   ├── settings.js            # Settings API
│   ├── codes.js               # Code API
│   ├── history.js             # History API
│   └── sse.js                 # SSE stream client
├── store/modules/             # Vuex state management
│   ├── auth.js                # 인증 상태 (token, user, menus, hasMenuPermission)
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
        ├── _dashboard.scss
        ├── _forms.scss
        ├── _layout.scss
        └── _markdown.scss

scripts/
├── add_multiturn_settings.py  # Multi-turn settings initialization
├── check_admin.py             # Admin user validation
├── check_codes.py             # Code table validation
├── check_feedback.py          # Feedback data validation
├── check_oracle_schema.py     # Oracle schema validation
├── check_tadmin.py            # Tenant admin validation
├── check_tools_config.py      # Tool configuration checker
├── cleanup_test_codes.py      # Test data cleanup
├── reset_admin_password.py    # Admin password reset

tests/
├── conftest.py                # Pytest fixtures (auth helper, API client)
├── test_01_health.py          # Health check
├── test_02_auth.py            # Authentication (login/refresh/logout/me)
├── test_03_tenants.py         # Tenant CRUD
├── test_04_roles.py           # Role CRUD
├── test_05_menus.py           # Menu CRUD
├── test_06_users.py           # User CRUD + scope validation
├── test_07_codes.py           # Code management
├── test_08_settings.py        # Settings
├── test_09_documents.py       # Document management
├── test_10_search.py          # Search (RAG/NL2SQL)
├── test_agent.py              # Agent + Calculator tool tests
├── test_classfy.py            # Classification tests
├── test_pii_service.py        # PII service tests
├── test_pii_redaction.py      # PII redaction tests
└── test_user_management.py    # User management comprehensive tests

docs/
├── design/                    # 설계 문서 (영역별 정리)
│   ├── 00_architecture_overview.md  # 시스템 아키텍처 전체 개요
│   ├── 01_ai_workflows.md          # AI 워크플로우 (Agent, NL2SQL, RAG)
│   ├── 02_auth_and_permission.md   # 인증/인가 시스템
│   ├── 03_database.md              # 데이터베이스 설계
│   ├── 04_api_reference.md         # API 엔드포인트 레퍼런스
│   ├── 05_frontend.md              # 프론트엔드 아키텍처
│   ├── 06_deployment.md            # 배포/인프라
│   ├── 07_user_role_design.md      # 사용자/역할/권한 상세 설계
│   └── 08_dashboard_design.md      # 대시보드 설계
└── sql/
    ├── psql-hermes_db.sql           # 전체 DB DDL 스크립트
    └── orcl-business_db.sql         # Oracle 비즈니스 DB 스크립트
```

### Request Flow Examples

**인증 포함 API 요청**:
```
Request → CORSMiddleware → LoggingMiddleware (request_id 생성)
  → AuthMiddleware (Bearer token → request.state.current_user)
  → HistoryMiddleware → Route Handler
  → Depends(require_menu_permission("MENU_CODE", "action"))
  → Service → Response
```

**AI Agent Flow** (ReAct):
```
User question → api/routes/agent.py
  → Depends(get_current_active_user)
  → api/services/agent_service.py
    → graphs/agent/graph.py:ainvoke(inputs)
      → middleware.process_input()
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
EMBEDDING_PROVIDER=openai     # openai only

# Security (JWT)
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
LOGIN_MAX_FAIL_COUNT=5
LOGIN_LOCK_MINUTES=30

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

### Adding Permission-Protected Route

```python
from app.core.security.dependencies import get_current_active_user
from app.core.security.permission import require_menu_permission

# 1. 메뉴 권한 체크가 필요한 경우
@router.get("")
async def list_items(
    current_user = Depends(require_menu_permission("MENU_CODE", "read"))
):
    # current_user.role_code로 scope 필터링
    if current_user.role_code == "GLOBAL":
        # 전체 데이터
    elif current_user.role_code == "TENANT":
        # tenant_id 기반 필터
    else:
        # user_id 기반 필터

# 2. 로그인만 필요한 경우
@router.get("/me")
async def get_me(
    current_user = Depends(get_current_active_user)
):
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
- `frontend/nginx.conf` - Nginx configuration (19080 → 19090 proxy)
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

### Memory Leak (InMemorySaver)
**원인**: UI 닫아도 서버에 세션 잔존 (`agent/graph.py`, `nl2sql/graph.py`)
**해결**: `app/core/checkpoint.py`에 `BoundedInMemorySaver` 생성 완료 (TTL+max세션), 적용 필요

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

# Security
python-jose[cryptography]>=3.3.0, passlib[bcrypt]>=1.7.4

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

## **중요**:
- 가상환경: `conda activate penv3.13-nlq`
- DB 확인할 경우: `postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb`
- UI 테스트시 Token을 받기위한 총괄관리자의 아이디/패스워드는 admin/Win1234! (다른 계정도 모두 마찬가지)
- DB스크립트 및 데이터:  docs/sql/psql-hermes_db.sql
- 로컬의 로그파일 : ./logs/app.log
- log_step출력: log_step는 로그이니 다른비즈니스 로직과 분리하여 한줄에 출력하라.
- 변경시에는 항상 변경된 소스코드파일 및 변경된 내용에 대해 설명을하라.
- __init__에는 가능한 파일만 생성하고 import모듈등은 구현하지 말라.
- css의 style는 asset/styles/mixins하위 디렉토리를 참조하라.


## Development Workflow

모든 기능 개발/변경 요청 시, 코드 작성 전에 반드시 아래 절차를 따른다:

1. **분석**: 관련 코드와 의존성을 탐색하여 영향 범위를 파악한다
2. **스타일 확인**: 구현 전 동일/유사 기능의 기존 코드를 참조하여 일관성을 확보한다
   - **Backend API**: 기존 라우트의 URL 패턴, HTTP method, status_code, Depends 구조를 따른다
   - **응답 형식**: `success_response()` 래퍼 사용, CREATE→201, LIST→items/total, DELETE→message/deleted_count
   - **서비스 계층**: db_manager.get_cursor 패턴, 에러 처리, log_step 형식을 기존 서비스와 동일하게 작성한다
   - **Frontend 화면**: 기존 Vue 컴포넌트의 레이아웃 구조, SCSS mixin 사용법, API 호출 패턴을 따른다
   - **Pydantic 모델**: 기존 models/ 파일의 네이밍, 필드 타입, Optional 처리 방식을 따른다
   - **참조 방법**: 새 기능과 가장 유사한 기존 파일 1~2개를 먼저 읽고 그 패턴을 따른다
3. **계획 수립**: TodoWrite로 작업 목록을 작성한다
   - 각 항목은 구체적이고 실행 가능해야 한다
   - 중요도/의존성 순으로 정렬한다
   - 테스트 항목을 반드시 포함한다
4. **사용자 확인**: 작업 목록을 사용자에게 제시하고 승인을 받은 후 구현을 시작한다
5. **구현**: 승인된 항목을 순서대로 진행하며, 완료 시마다 TodoWrite를 갱신한다
6. **검증**: 각 단계 완료 후 테스트 가능한 항목은 테스트를 수행한다

예외: 오타 수정, 한줄 버그 픽스 등 단순 작업은 즉시 수행 가능하다.
