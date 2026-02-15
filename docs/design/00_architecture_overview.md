# MUREUM 전체 아키텍처

> 최종 수정: 2026-02-15

---

## 1. 시스템 개요

MUREUM은 기업용 AI 지식베이스 어시스턴트로, 자연어 질의를 통해 문서 검색(RAG)과 데이터베이스 조회(NL2SQL)를 수행한다. AI Agent(ReAct 패턴)가 도구를 자율 선택하여 복합 질문도 처리한다.

**기술 스택**

| 구분 | 기술 |
|------|------|
| Backend | Python 3.13, FastAPI, LangGraph 1.0+, LangChain 1.2+ |
| Frontend | Vue 3, Vuex, Element Plus, ECharts, Vite |
| Database | PostgreSQL (pgvector), Oracle (외부 비즈니스 DB) |
| LLM | OpenAI (gpt-4o, gpt-4o-mini), Anthropic (claude-3-5-sonnet) |
| Embedding | OpenAI text-embedding-3-small (1536D) |
| Infra | Docker, Nginx, SSH 배포 |

---

## 2. 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 (Vue 3)                        │
│   사용자 채팅 (/chat)  │  관리자 대시보드 (/admin/*)              │
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
│  │  CORS → LoggingMiddleware → AuthMiddleware → HistoryMW    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌─ API Routes (13개) ───────────────────────────────────────┐  │
│  │  auth │ search │ agent │ documents │ settings │ codes     │  │
│  │  history │ export │ users │ roles │ tenants │ menus       │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ Services (13개) ────────────────────────────────────────┐   │
│  │  agent │ rag │ nl2sql │ auth │ document │ settings       │   │
│  │  code │ history │ export │ user │ role │ tenant │ menu   │   │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ LangGraph Workflows ────────────────────────────────────┐   │
│  │  Agent (ReAct)  │  NL2SQL (멀티턴)  │  RAG (문서검색)     │   │
│  └──────────────────────────┬────────────────────────────────┘  │
│                              ▼                                    │
│  ┌─ Core Infrastructure ────────────────────────────────────┐   │
│  │  database │ llm │ vector │ security │ pii │ sse │ errors │   │
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
  └─────────────────┘
```

---

## 3. 레이어 아키텍처

```
┌──────────────────────────────────────────────┐
│  Routes (HTTP 계층)                           │  API 엔드포인트, 요청/응답 직렬화
│  app/api/routes/*.py                          │  비즈니스 로직 없음, 서비스 위임
├──────────────────────────────────────────────┤
│  Services (비즈니스 로직)                      │  데이터 가공, 권한 검증, 흐름 조율
│  app/api/services/*.py                        │  싱글톤 패턴, 동기/비동기 혼용
├──────────────────────────────────────────────┤
│  Graphs (AI 워크플로우)                        │  LangGraph 상태 머신
│  app/graphs/{agent,nl2sql,rag}/              │  노드, 조건부 엣지, 체크포인팅
├──────────────────────────────────────────────┤
│  Core (인프라스트럭처)                         │  DB, LLM, 벡터, 보안, 에러
│  app/core/{database,llm,vector,security,...}/ │  재사용 가능한 기반 모듈
├──────────────────────────────────────────────┤
│  Models (데이터 계약)                          │  Pydantic 모델 (요청/응답)
│  app/models/*.py                              │  API 입출력 스키마 정의
├──────────────────────────────────────────────┤
│  Middleware (요청 파이프라인)                    │  인증, 로깅, 이력 저장
│  app/middleware/*.py                           │  BaseHTTPMiddleware 상속
└──────────────────────────────────────────────┘
```

---

## 4. 미들웨어 체인

등록 역순으로 실행된다 (외부→내부):

```
요청 → CORS → Logging → Auth → History → Handler
응답 ← CORS ← Logging ← Auth ← History ← Handler
```

| 미들웨어 | 파일 | 역할 |
|----------|------|------|
| CORSMiddleware | FastAPI 내장 | CORS 헤더 처리 |
| LoggingMiddleware | `middleware/logging.py` | request_id 생성, 요청/응답 로깅, 타이밍 |
| AuthMiddleware | `middleware/auth.py` | JWT 검증 (옵셔널 모드), UserContext 주입 |
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
│   ├── routes/                 # HTTP 엔드포인트 (13개)
│   └── services/               # 비즈니스 로직 (13개)
├── graphs/                     # LangGraph AI 워크플로우
│   ├── agent/                  # ReAct Agent (graph, state, nodes, tools, middleware)
│   ├── nl2sql/                 # NL2SQL (graph, state, nodes - 14개 노드)
│   └── rag/                    # RAG (graph, state, nodes)
├── core/                       # 인프라 모듈
│   ├── database/               # DB 커넥션, SQL 실행, 스키마, 어댑터
│   ├── llm/                    # LLM 설정, 프롬프트, SQL 생성
│   ├── vector/                 # pgvector 임베딩 + 검색
│   ├── security/               # JWT, 패스워드, 권한, 테넌트
│   ├── pii/                    # PII 감지 + 마스킹
│   ├── sse/                    # SSE 스트리밍 포맷
│   ├── errors/                 # 에러코드, 핸들러, 응답
│   └── config/                 # 설정 스키마
├── models/                     # Pydantic 모델 (API 계약)
├── middleware/                  # FastAPI 미들웨어
└── utils/                      # 로거, 유틸리티

frontend/src/
├── views/                      # 페이지 (admin 14개, user 1개, login 1개)
├── components/                 # 컴포넌트 (chat, chart, layout, user, documents)
├── api/                        # Axios API 클라이언트 (13개)
├── store/modules/              # Vuex 상태 (auth, chat, app, document)
├── router/                     # Vue Router + 가드
├── utils/                      # 포맷, 마크다운 파서
└── assets/styles/              # SCSS (variables, mixins, modules)
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

---

## 8. 관련 문서

| 문서 | 설명 |
|------|------|
| [01_ai_workflows.md](01_ai_workflows.md) | Agent, NL2SQL, RAG 워크플로우 상세 |
| [02_auth_and_permission.md](02_auth_and_permission.md) | 인증/인가 시스템 |
| [03_database.md](03_database.md) | 데이터베이스 설계 |
| [04_api_reference.md](04_api_reference.md) | API 엔드포인트 목록 |
| [05_frontend.md](05_frontend.md) | 프론트엔드 아키텍처 |
| [06_deployment.md](06_deployment.md) | 배포/인프라 |
