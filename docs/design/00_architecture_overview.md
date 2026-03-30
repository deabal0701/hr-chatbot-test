# win-AI 전체 아키텍처

> 최종 수정: 2026-03-09

---

## 1. 시스템 개요

win-AI는 기업용 AI 지식베이스 어시스턴트로, 자연어 질의를 통해 문서 검색(RAG)과 데이터베이스 조회(NL2SQL)를 수행한다. AI Agent(ReAct 패턴)가 도구를 자율 선택하여 복합 질문도 처리한다.

**기술 스택**

| 구분 | 기술 |
|------|------|
| Backend | Python 3.13, FastAPI, LangGraph 1.0+, LangChain 1.2+ |
| Frontend | Vue 3, Vuex, Element Plus, ECharts, Vite |
| Database | PostgreSQL (pgvector), Oracle (외부 비즈니스 DB) |
| LLM | OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet), Google Gemini |
| Embedding | OpenAI text-embedding-3-small (1536D) |
| Infra | Docker, Nginx, SSH 배포 |

---

## 2. 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 (Vue 3)                        │
│   사용자 채팅 (/chat)  │  관리자 대시보드 (/admin/*)              │
│   개인 대시보드 (/personal-dashboard)                            │
└────────────┬────────────────────────────────┬───────────────────┘
             │ HTTP/SSE                       │ HTTP
             ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx (19080)                               │
│   정적 파일 서빙  │  /api/* → Backend 프록시 (19090)              │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (19090)                        │
│                                                                   │
│  ┌─ Middleware Chain ─────────────────────────────────────────┐  │
│  │  CORS → Logging → Auth → RateLimit → History              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─ API Routes (16개) ──────────────────────────────────────┐   │
│  │  auth │ search │ agent │ documents │ settings │ codes     │   │
│  │  history │ export │ users │ roles │ tenants │ menus       │   │
│  │  departments │ dashboard │ personal_dashboard             │   │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ Services (17개) ────────────────────────────────────────┐   │
│  │  agent │ rag │ nl2sql │ auth │ document │ settings       │   │
│  │  code │ history │ export │ user │ role │ tenant │ menu   │   │
│  │  department │ dashboard │ personal_dashboard              │   │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ LangGraph Workflows ────────────────────────────────────┐   │
│  │  Agent (ReAct)  │  NL2SQL (멀티턴)  │  RAG (문서검색)     │   │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ Core Infrastructure ────────────────────────────────────┐   │
│  │  database │ llm │ vector │ security │ pii │ sse          │   │
│  │  errors │ file │ checkpoint │ config                      │   │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└──────────┬──────────────────────────────┬───────────────────────┘
           ▼                              ▼
  ┌─────────────────┐          ┌──────────────────┐
  │ PostgreSQL       │          │ 외부 비즈니스 DB  │
  │ (pgvector)       │          │ (PostgreSQL/Oracle)│
  │ - tb_docs        │          │ - employee        │
  │ - tb_user        │          │ - department      │
  │ - tb_app_settings│          │ (NL2SQL 대상)     │
  │ - tb_api_history │          └──────────────────┘
  │ - tb_department  │
  └─────────────────┘
```

---

## 3. 레이어 아키텍처

```
┌──────────────────────────────────────────────┐
│  Routes (HTTP 계층)                           │  API 엔드포인트, 요청/응답 직렬화
│  app/api/routes/*.py (16개)                   │  비즈니스 로직 없음, 서비스 위임
├──────────────────────────────────────────────┤
│  Services (비즈니스 로직)                      │  데이터 가공, 권한 검증, 흐름 조율
│  app/api/services/*.py (17개)                 │  싱글톤 패턴, 동기/비동기 혼용
├──────────────────────────────────────────────┤
│  Graphs (AI 워크플로우)                        │  LangGraph 상태 머신
│  app/graphs/{agent,nl2sql,rag}/              │  노드, 조건부 엣지, 체크포인팅
├──────────────────────────────────────────────┤
│  Core (인프라스트럭처)                         │  DB, LLM, 벡터, 보안, 에러, 파일
│  app/core/{database,llm,vector,security,...}/ │  재사용 가능한 기반 모듈
├──────────────────────────────────────────────┤
│  Models (데이터 계약)                          │  Pydantic 모델 (요청/응답)
│  app/models/*.py (15개)                       │  API 입출력 스키마 정의
├──────────────────────────────────────────────┤
│  Middleware (요청 파이프라인)                    │  인증, 로깅, 이력, 속도제한
│  app/middleware/*.py (5개)                     │  BaseHTTPMiddleware 상속
└──────────────────────────────────────────────┘
```

---

## 4. 미들웨어 체인

등록 역순으로 실행된다 (외부→내부):

```
요청 → CORS → Logging → Auth → RateLimit → History → Handler
응답 ← CORS ← Logging ← Auth ← RateLimit ← History ← Handler
```

| 미들웨어 | 파일 | 역할 |
|----------|------|------|
| CORSMiddleware | FastAPI 내장 | CORS 헤더 처리 |
| LoggingMiddleware | `middleware/logging.py` | request_id 생성, 요청/응답 로깅, 타이밍 |
| AuthMiddleware | `middleware/auth.py` | JWT 검증 (옵셔널 모드), UserContext 주입 |
| RateLimitMiddleware | `middleware/rate_limit.py` | 사용자별 요청 속도 제한 (Auth 이후 실행) |
| HistoryMiddleware | `middleware/history.py` | API 이력 비동기 저장 (워커 큐) |

---

## 5. 요청 흐름

### 5.1 Agent 검색 (ReAct 멀티스텝)

```
POST /api/v1/agent/search
  → agent_service.search()
    → middleware.process_input() (PII 마스킹)
    → graph.ainvoke(initial_state)
      → agent_node → [도구 선택] → tools_node → agent_node (반복) → answer_node
    → middleware.process_output()
  → AgentResponse (final_answer, tools_used)
```

### 5.2 NL2SQL 검색 (멀티턴)

```
POST /api/v1/search (mode=nl2sql)
  → nl2sql_service.search()
    → graph.ainvoke(initial_state)
      → load_history → intent_rewrite → [SQL 필요?]
        → YES: schema → fewshot → prompt → generate → validate → execute → pii_filter → answer → save
        → NO:  answer_from_history → save
  → SearchResponse (answer, sql, result)
```

### 5.3 RAG 검색

```
POST /api/v1/search (mode=rag)
  → rag_service.search()
    → graph.ainvoke(initial_state)
      → retrieve_documents (pgvector) → generate_answer (LLM)
  → SearchResponse (answer, sources)
```

---

## 6. 디렉토리 구조

```
app/
├── main.py                     # FastAPI 앱 + lifespan + 라우터/미들웨어 등록
├── config.py                   # Pydantic Settings (환경변수 + 기본값)
├── api/
│   ├── routes/                 # HTTP 엔드포인트 (16개)
│   │   ├── auth.py             # 인증 (login/logout/refresh/me/password)
│   │   ├── search.py           # 통합 검색 (auto/rag/nl2sql + stream)
│   │   ├── agent.py            # AI Agent (search, stream, sessions, tools)
│   │   ├── documents.py        # 문서 관리 CRUD
│   │   ├── settings.py         # 설정 관리
│   │   ├── codes.py            # 코드 관리 + public lookup
│   │   ├── history.py          # API 이력 (필터, 통계, 세션별)
│   │   ├── export.py           # Excel 내보내기
│   │   ├── users.py            # 사용자 CRUD + options + 메뉴 권한
│   │   ├── roles.py            # 역할 CRUD + default-menus
│   │   ├── tenants.py          # 테넌트 CRUD
│   │   ├── menus.py            # 메뉴 트리 CRUD + reorder
│   │   ├── departments.py      # 부서(조직) 트리 관리
│   │   ├── dashboard.py        # 관리자 대시보드 KPI/차트
│   │   └── personal_dashboard.py # 개인 대시보드
│   └── services/               # 비즈니스 로직 (17개)
│       ├── auth_service.py     # 인증 (로그인, 토큰, 세션, 권한 조회)
│       ├── agent_service.py    # Agent 오케스트레이션
│       ├── rag_service.py      # RAG 오케스트레이션
│       ├── nl2sql_service.py   # NL2SQL 오케스트레이션
│       ├── document_service.py # 문서 CRUD
│       ├── user_service.py     # 사용자 CRUD + 권한 상승 방지 + scope 필터
│       ├── role_service.py     # 역할 CRUD + 기본 메뉴
│       ├── menu_service.py     # 메뉴 트리 CRUD + reorder
│       ├── tenant_service.py   # 테넌트 CRUD + is_system 보호
│       ├── department_service.py # 부서(조직) 관리
│       ├── settings_service.py # Dynamic config (DB fallback chain)
│       ├── code_service.py     # 코드 관리
│       ├── history_service.py  # 이력 저장 (비동기 워커 큐)
│       ├── dashboard_service.py # 관리자 대시보드 통합 데이터
│       ├── personal_dashboard_service.py # 개인 대시보드
│       └── export_service.py   # Excel export
├── graphs/                     # LangGraph AI 워크플로우
│   ├── agent/                  # ReAct Agent
│   │   ├── graph.py            # InsightAgentGraph 클래스
│   │   ├── state.py            # AgentState TypedDict + create_initial_state()
│   │   ├── nodes/              # 노드 함수들
│   │   │   ├── agent_node.py   # LLM Think/Action + should_continue()
│   │   │   ├── tools_node.py   # Tool 실행 라우터
│   │   │   └── answer_node.py  # 최종 답변 생성
│   │   ├── tools/              # Agent 도구
│   │   │   ├── base.py         # BaseTool ABC, ToolResult, ToolMetrics
│   │   │   ├── sql_tool.py     # SQL query tool
│   │   │   ├── rag_tool.py     # 문서 검색 tool
│   │   │   └── calc_tool.py    # 계산기 tool (safe AST)
│   │   └── middleware/         # Agent 미들웨어
│   │       ├── base.py         # Middleware base class
│   │       ├── chain.py        # MiddlewareChain
│   │       └── pii.py          # PIIMiddleware
│   ├── nl2sql/                 # NL2SQL (멀티턴 + 의도분석 + PII 필터)
│   │   ├── graph.py            # NL2SQLGraph 클래스
│   │   ├── state.py            # NL2SQLState TypedDict
│   │   └── nodes.py            # 모든 NL2SQL 노드 함수 (14개)
│   └── rag/                    # RAG (문서 검색)
│       ├── graph.py            # RAGGraph 클래스
│       ├── state.py            # RAGState TypedDict
│       └── nodes.py            # retrieve, generate_answer
├── core/                       # 인프라 모듈
│   ├── checkpoint.py           # BoundedInMemorySaver (TTL 24h, max 1000세션)
│   ├── database/               # DB 커넥션, SQL 실행, 스키마, 어댑터
│   │   ├── connection.py       # Connection pool (psycopg3) - db_manager
│   │   ├── external.py         # External DB manager (NL2SQL 대상)
│   │   ├── schema_loader.py    # DB schema introspection
│   │   ├── sql_executor.py     # SQL validation + execution
│   │   ├── table_catalog.py    # Table metadata caching
│   │   └── adapters/           # DB adapter pattern
│   │       ├── base.py         # DatabaseAdapter ABC
│   │       ├── postgresql.py   # PostgreSQL adapter
│   │       ├── oracle.py       # Oracle adapter
│   │       └── factory.py      # Adapter factory
│   ├── llm/                    # LLM 계층
│   │   ├── llm_config.py       # LLMConfigManager (OpenAI/Anthropic/Google)
│   │   ├── prompt_service.py   # Prompt templates
│   │   └── sql_generator.py    # SQL generation
│   ├── vector/                 # 벡터 검색 계층
│   │   ├── vector_store.py     # pgvector 임베딩 + 유사도 검색
│   │   ├── text_chunker.py     # 문서 청킹
│   │   ├── keyword_extractor.py # 키워드 추출 (하이브리드 검색용)
│   │   └── hybrid_search.py    # 하이브리드 검색 (키워드 + 시맨틱)
│   ├── security/               # 인증/인가
│   │   ├── jwt.py              # JWT 생성/검증
│   │   ├── password.py         # bcrypt 해싱
│   │   ├── dependencies.py     # get_current_user, get_current_active_user
│   │   ├── permission.py       # require_menu_permission, require_superuser
│   │   ├── scope_filter.py     # 데이터 범위 필터링 (GLOBAL/TENANT/USER)
│   │   └── tenant_context.py   # ContextVar 기반 테넌트 컨텍스트
│   ├── pii/                    # PII 처리
│   │   └── pii_service.py      # PII 감지 + 마스킹
│   ├── sse/                    # Server-Sent Events
│   │   └── stream_manager.py   # SSE 포맷팅, 스테이지 그룹핑
│   ├── errors/                 # 에러 처리
│   │   ├── error_codes.py      # ErrorCode enum
│   │   ├── handlers.py         # 전역 예외 핸들러
│   │   └── response.py         # success_response, error_response
│   ├── file/                   # 파일 처리
│   │   └── file_extractor.py   # 문서 텍스트 추출 (PDF, DOCX 등)
│   └── config/                 # 설정
│       └── settings_config.py  # Settings schema
├── models/                     # Pydantic 모델 (15개)
│   ├── auth.py                 # LoginRequest, TokenResponse, UserContext
│   ├── user.py                 # User/Role CRUD 모델
│   ├── menu.py                 # MenuCreate/Update, MenuTreeResponse
│   ├── tenant.py               # Tenant CRUD 모델
│   ├── department.py           # Department 모델
│   ├── agent.py                # AgentRequest, AgentResponse
│   ├── search.py               # SearchRequest, SearchResponse
│   ├── rag.py                  # DocumentSource, SQLResult
│   ├── documents.py            # Document CRUD 모델
│   ├── settings.py             # Settings 모델
│   ├── codes.py                # Code 관리 모델
│   ├── history.py              # History 모델
│   ├── personal_dashboard.py   # 개인 대시보드 모델
│   ├── sse.py                  # SSE 이벤트 모델
│   └── common.py               # 공통 모델
├── middleware/                  # FastAPI 미들웨어 (5개)
│   ├── base.py                 # Middleware base class
│   ├── logging.py              # 요청/응답 로깅 + request_id
│   ├── auth.py                 # JWT 인증 (선택적 모드)
│   ├── rate_limit.py           # 사용자별 요청 속도 제한
│   └── history.py              # API 이력 비동기 저장
└── utils/                      # 유틸리티
    ├── logger.py               # Structured logging + log_step()
    ├── langsmith.py            # LangSmith integration
    └── common.py               # truncate_text 등

frontend/src/
├── views/                      # 페이지 (admin 16개, user 2개, login 1개)
│   ├── LoginView.vue           # 로그인 페이지
│   ├── user/
│   │   ├── UserChatView.vue    # 사용자 채팅 인터페이스
│   │   └── PersonalDashboardView.vue # 개인 대시보드
│   └── admin/
│       ├── AdminLayout.vue     # Admin 네비게이션 래퍼
│       ├── DashboardView.vue   # 관리자 대시보드
│       ├── ChatView.vue        # 관리자 채팅 인터페이스
│       ├── DocumentsView.vue   # 문서 관리
│       ├── DocumentDetailView.vue # 문서 상세
│       ├── DocumentEditView.vue # 문서 편집기
│       ├── UsersView.vue       # 사용자 관리
│       ├── RolesView.vue       # 역할 관리
│       ├── MenusView.vue       # 메뉴 트리 관리
│       ├── TenantsView.vue     # 테넌트 관리
│       ├── DepartmentsView.vue # 부서(조직) 관리
│       ├── SettingsView.vue    # 설정 관리
│       ├── CodesView.vue       # 코드 관리
│       ├── HistoryView.vue     # API 이력
│       └── HistoryDetailView.vue # 이력 상세
├── components/                 # 컴포넌트 (31개)
│   ├── chat/                   # 채팅 컴포넌트
│   │   ├── ChatMessage.vue     # 메시지 표시 (admin)
│   │   ├── ChatInput.vue       # 메시지 입력
│   │   ├── SourceCard.vue      # 소스 문서 카드
│   │   ├── SqlResultPanel.vue  # SQL 결과 패널
│   │   └── PromptGuideModal.vue # 프롬프트 가이드 모달
│   ├── chart/
│   │   └── ChartBuilder.vue    # SQL 결과 차트 시각화
│   ├── dashboard/              # 관리자 대시보드
│   │   ├── KpiCards.vue        # KPI 요약 카드
│   │   ├── DailyTrendChart.vue # 일별 요청 추이
│   │   ├── RequestTypeChart.vue # 검색 유형 분포
│   │   ├── RecentActivity.vue  # 최근 검색 피드
│   │   └── SystemStatus.vue    # 시스템 현황
│   ├── dashboard-personal/     # 개인 대시보드
│   │   ├── DashboardGrid.vue   # 위젯 그리드 레이아웃
│   │   ├── DashboardWidget.vue # 개별 위젯
│   │   ├── DashboardToolbar.vue # 툴바
│   │   ├── AddWidgetModal.vue  # 위젯 추가 모달
│   │   ├── WidgetEditModal.vue # 위젯 편집 모달
│   │   ├── WidgetConfigForm.vue # 위젯 설정 폼
│   │   ├── DashboardManageModal.vue # 대시보드 관리
│   │   ├── DashboardShareModal.vue  # 대시보드 공유
│   │   ├── SaveToDashboardModal.vue # 차트→대시보드 저장
│   │   ├── DashboardEmptyState.vue  # 빈 상태 표시
│   │   └── widgets/            # 위젯 렌더러
│   │       ├── WidgetChart.vue # 차트 위젯
│   │       ├── WidgetKpi.vue   # KPI 위젯
│   │       └── WidgetTable.vue # 테이블 위젯
│   ├── user/                   # 사용자용 컴포넌트
│   │   ├── UserChatLayout.vue
│   │   ├── UserChatMessage.vue
│   │   ├── UserChatSidebar.vue
│   │   └── MenuPermissionTable.vue # 권한 테이블
│   ├── documents/
│   │   └── ChunkPreview.vue    # 청크 미리보기
│   └── layout/
│       ├── AppHeader.vue
│       └── AppSidebar.vue
├── api/                        # Axios API 클라이언트 (16개)
│   ├── index.js                # Axios 인스턴스 + 인터셉터
│   ├── auth.js                 # 인증 API
│   ├── agent.js                # Agent API
│   ├── search.js               # 검색 API (RAG/NL2SQL)
│   ├── documents.js            # 문서 API
│   ├── users.js                # 사용자 관리 API
│   ├── roles.js                # 역할 관리 API
│   ├── menus.js                # 메뉴 관리 API
│   ├── tenants.js              # 테넌트 관리 API
│   ├── departments.js          # 부서 관리 API
│   ├── dashboard.js            # 관리자 대시보드 API
│   ├── personalDashboard.js    # 개인 대시보드 API
│   ├── settings.js             # 설정 API
│   ├── codes.js                # 코드 API
│   ├── history.js              # 이력 API
│   └── sse.js                  # SSE 스트림 클라이언트
├── store/modules/              # Vuex 상태 관리 (5개)
│   ├── auth.js                 # 인증 상태 (token, user, menus)
│   ├── chat.js                 # 채팅 대화 상태
│   ├── dashboard.js            # 대시보드 상태
│   ├── document.js             # 문서 상태
│   └── app.js                  # 글로벌 앱 상태
├── router/                     # Vue Router + 가드
│   └── index.js
├── utils/                      # 유틸리티 (4개)
│   ├── format.js               # 포맷 유틸리티
│   ├── error.js                # 에러 처리 유틸리티
│   ├── exportUtils.js          # Excel 내보내기 유틸리티
│   └── markdownParser.js       # 마크다운 파서
└── assets/styles/              # SCSS 스타일
    ├── main.scss               # 메인 스타일시트
    ├── _variables.scss         # CSS 변수
    ├── mixins/                 # SCSS Mixins (10개)
    │   ├── _index.scss
    │   ├── _animations.scss
    │   ├── _cards.scss
    │   ├── _chart.scss
    │   ├── _chat.scss
    │   ├── _dashboard.scss
    │   ├── _forms.scss
    │   ├── _layout.scss
    │   ├── _markdown.scss
    │   └── _responsive.scss    # 반응형 브레이크포인트
    └── modules/                # 스타일 모듈 (5개)
        ├── _reset.scss
        ├── _utilities.scss
        ├── _chat-global.scss
        ├── _dropdown.scss
        └── _element-dark.scss
```

---

## 7. 핵심 설계 패턴

| 패턴 | 적용 위치 | 설명 |
|------|----------|------|
| Service Layer | routes → services → core | 얇은 라우트, 두꺼운 서비스 |
| LangGraph State Machine | graphs/ | TypedDict 상태 + 노드 + 조건부 엣지 |
| Adapter Factory | database/adapters/ | PostgreSQL/Oracle DB별 구현 교체 |
| Dynamic Settings | settings_service | DB → 환경변수 → 기본값 우선순위 |
| Singleton Service | 모든 서비스 | 모듈 레벨 인스턴스 생성 |
| Middleware Chain | app/middleware/ | BaseHTTPMiddleware 상속, exclude_paths |
| SSE Streaming | Agent, NL2SQL | astream_events() → format_sse() |
| PII Protection | Agent 미들웨어, NL2SQL 노드 | 입출력 PII 마스킹 |
| BoundedInMemorySaver | core/checkpoint.py | TTL 24h + max 1000세션, LRU 퇴거 |
| Rate Limiting | middleware/rate_limit.py | 사용자별 요청 속도 제한 |
| Scope Filter | security/scope_filter.py | GLOBAL/TENANT/USER 데이터 범위 필터링 |
| Hybrid Search | core/vector/ | 키워드 + 시맨틱 결합 검색 |

---

## 8. 주요 모듈 요약

### 8.1 Backend 모듈 수량

| 모듈 | 파일 수 | 설명 |
|------|---------|------|
| Routes | 16 | HTTP 엔드포인트 |
| Services | 17 | 비즈니스 로직 |
| Graphs | 24 | AI 워크플로우 (Agent 16 + NL2SQL 4 + RAG 4) |
| Core | 41 | 인프라 모듈 |
| Models | 15 | Pydantic 데이터 계약 |
| Middleware | 5 | 요청 파이프라인 |
| Utils | 3 | 로거, LangSmith, 공통 |

### 8.2 Frontend 모듈 수량

| 모듈 | 파일 수 | 설명 |
|------|---------|------|
| Views | 19 | 페이지 (admin 16, user 2, login 1) |
| Components | 31 | UI 컴포넌트 |
| API Clients | 16 | Axios 기반 API 호출 |
| Store Modules | 5 | Vuex 상태 관리 |
| Utils | 4 | 포맷, 에러, Export, 마크다운 |
| Styles | 20 | SCSS (variables, mixins, modules) |

---

## 9. 관련 문서

| 문서 | 설명 |
|------|------|
| [01_ai_workflows.md](01_ai_workflows.md) | Agent, NL2SQL, RAG 워크플로우 상세 |
| [02_auth_and_permission.md](02_auth_and_permission.md) | 인증/인가 시스템 |
| [03_database.md](03_database.md) | 데이터베이스 설계 |
| [04_api_reference.md](04_api_reference.md) | API 엔드포인트 목록 |
| [05_frontend.md](05_frontend.md) | 프론트엔드 아키텍처 |
| [06_deployment.md](06_deployment.md) | 배포/인프라 |
| [07_user_role_design.md](07_user_role_design.md) | 사용자/역할/권한 상세 설계 |
| [08_dashboard_design.md](08_dashboard_design.md) | 관리자 대시보드 설계 |
| [09_future_roadmap.md](09_future_roadmap.md) | 향후 로드맵 |
| [10_nl2sql_accuracy_analysis.md](10_nl2sql_accuracy_analysis.md) | NL2SQL 정확도 분석 |
