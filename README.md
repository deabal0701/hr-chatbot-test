# MUREUM - 기업용 AI 지식 베이스 어시스턴트

자연어 기반 기업 지식 검색 및 통계 조회를 위한 AI 어시스턴트 시스템

## 주요 기능

### 1. AI Agent (ReAct 패턴)
- **자율적 도구 선택**: 질문에 따라 자동으로 적절한 도구(SQL, 문서검색, 계산기) 선택
- **멀티스텝 질의**: 복잡한 질문을 단계별로 분해하여 처리
- **멀티턴 대화**: 세션 기반 대화 히스토리 관리 (BoundedInMemorySaver)
- **실행 과정 추적**: Thought → Action → Observation 패턴으로 추론 과정 확인
- **PII 보호**: Agent 미들웨어 기반 입출력 PII 마스킹

### 2. RAG (Retrieval Augmented Generation)
- **벡터 검색**: pgvector 기반 시맨틱 검색
- **하이브리드 검색**: 벡터 + BM25 키워드 결합 검색
- **문서 청킹**: 효율적인 검색을 위한 스마트 문서 분할
- **동적 필터링**: 문서 유형, 카테고리 기반 필터링
- **파일 업로드**: PDF, DOCX 파일 직접 업로드 및 임베딩

### 3. NL2SQL (멀티턴 + 의도 분석)
- **자연어 → SQL 변환**: LLM 기반 SQL 자동 생성
- **멀티턴 대화**: 세션 기반 히스토리, 의도 재작성(Intent Rewrite)
- **Few-shot 학습**: 정확도 향상을 위한 예제 기반 학습
- **SQL 보안 검증**: SQL Injection 방지, 읽기 전용 강제
- **다중 DB 지원**: PostgreSQL, Oracle (Adapter 패턴)
- **PII 필터링**: SQL 결과의 개인정보 마스킹 후 LLM 전송

### 4. 인증 및 권한 관리
- **JWT 인증**: Access Token (30분) + Refresh Token (7일, DB 저장)
- **SSO 통합**: RS256 공개키 기반 외부 SSO 토큰 검증, 자동 사용자 프로비저닝(JIT)
- **역할 기반 접근 제어**: GLOBAL / TENANT / USER 3계층 데이터 범위
- **메뉴 권한 시스템**: tb_user_menu 기반 CRUD + Export 권한 매트릭스
- **계정 보안**: 로그인 실패 5회 → 30분 잠금, bcrypt 해싱

### 5. 멀티 테넌트 아키텍처
- **테넌트 격리**: 미들웨어 기반 테넌트 컨텍스트 자동 설정
- **데이터 범위 제어**: role_code에 따른 자동 scope 필터링
- **시스템 보호**: is_system 플래그로 시스템 리소스 삭제 방지

### 6. 동적 설정 관리
- **DB 기반 설정**: 코드 배포 없이 실시간 설정 변경
- **Admin UI**: 웹 기반 설정 관리 인터페이스
- **Fallback 체계**: DB → 환경변수 → 기본값 순서로 설정 로드

### 7. SSE 스트리밍
- **실시간 응답**: Agent, NL2SQL 워크플로우의 SSE 기반 실시간 응답
- **스테이지 추적**: 노드별 진행 상태 이벤트 전송

### 8. 대시보드
- **시스템 대시보드**: KPI 요약, 일별 추이, 검색 유형 분포, 최근 활동, 시스템 현황
- **개인 대시보드**: 사용자별 커스터마이징 가능한 위젯 기반 대시보드

### 9. 부가 기능
- **부서(조직) 관리**: 본부/부서/팀/파트 계층형 조직 트리
- **코드 관리**: 마스터 코드 그룹/항목 CRUD
- **API 이력**: 전체 요청 이력 자동 저장 및 통계
- **Excel 내보내기**: NL2SQL 결과 Excel 다운로드
- **Rate Limiting**: 사용자/IP 기반 요청 속도 제한

## 기술 스택

### Backend
| 구분 | 기술 | 버전 |
|------|------|------|
| Language | Python | 3.13 (3.10+ 필수) |
| Framework | FastAPI | 0.115+ |
| AI Framework | LangChain | 1.2+ |
| AI Workflow | LangGraph | 1.0.5+ |
| Database | PostgreSQL + pgvector | 15+ |
| External DB | Oracle (oracledb) | 2.0+ |
| Embedding | OpenAI text-embedding-3-small | 1536 dimensions |

### LLM Providers
| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4.1-mini |
| Anthropic | claude-3-5-sonnet-20241022 |
| Google | Gemini (langchain-google-genai) |

### Frontend
| 구분 | 기술 | 버전 |
|------|------|------|
| Framework | Vue 3 + Composition API | 3.3.13 |
| State | Vuex | 4.1.0 |
| UI Library | Element Plus | 2.4.4 |
| Charts | ECharts + vue-echarts | 6.0.0 / 8.0.1 |
| HTTP Client | Axios | 1.6.2 |
| Build Tool | Vite | 7.0.0 |
| Style | SCSS (Sass) | 1.80.0 |

### Infrastructure
| 구분 | 기술 |
|------|------|
| ASGI Server | Uvicorn (dev) / Gunicorn (prod) |
| Reverse Proxy | Nginx (frontend) |
| Container | Docker (Python 3.13-slim / Node 24 + Nginx alpine) |
| Monitoring | Prometheus (optional), LangSmith (optional) |

## 설치

### 1. 필수 요구사항
```bash
# Python 3.10 이상 (3.13 권장)
python --version

# PostgreSQL 15+ with pgvector extension
psql --version
```

### 2. 가상환경 생성 (Conda 권장)
```bash
# Conda 환경 생성
conda create -n penv3.13-nlq python=3.13
conda activate penv3.13-nlq

# 또는 venv 사용
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.sample .env
# .env 파일을 편집하여 실제 값 입력
```

### 5. 데이터베이스 초기화
```bash
# pgvector 확장 설치 (DB에서 수동 실행)
# CREATE EXTENSION IF NOT EXISTS vector;

# 테이블 생성 (DDL 스크립트)
# docs/sql/psql-hermes_db.sql 참조

# DB 초기화
python scripts/init_db.py
```

### 6. SSO 키 생성 (선택)
```bash
# RS256 키페어 생성
python scripts/generate_sso_keys.py
# keys/sso_private.pem, keys/sso_public.pem 생성됨
```

### 7. 문서 임베딩 (선택)
```bash
# 샘플 문서 임베딩
python scripts/embed_documents.py --sample

# 특정 파일 임베딩
python scripts/embed_documents.py --file data/documents.json
```

## 실행

### Backend 서버
```bash
conda activate penv3.13-nlq

# 개발 서버 (자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 19090

# 또는 직접 실행
python app/main.py

# 프로덕션 서버
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:19090
```

### Frontend 서버
```bash
cd frontend
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm run build    # 프로덕션 빌드
npm run preview  # 빌드 미리보기
```

### Docker 배포
```bash
# Backend
docker build -t mureum-backend .
docker run -p 19090:19090 mureum-backend

# Frontend
cd frontend
docker build -t mureum-frontend .
docker run -p 19080:19080 mureum-frontend
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:
- **Swagger UI**: http://localhost:19090/docs
- **ReDoc**: http://localhost:19090/redoc
- **API Info**: http://localhost:19090/api/v1/info

### 주요 API 엔드포인트

#### 인증 (Authentication)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/v1/auth/logout` | 로그아웃 (세션 삭제) |
| POST | `/api/v1/auth/refresh` | Access Token 갱신 |
| GET | `/api/v1/auth/me` | 현재 사용자 정보 조회 |
| PUT | `/api/v1/auth/me/password` | 비밀번호 변경 |

#### AI Agent (ReAct 멀티스텝)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/agent/search` | AI Agent 검색 (멀티스텝, 멀티턴) |
| GET | `/api/v1/agent/sessions` | 활성 세션 목록 |
| GET | `/api/v1/agent/sessions/{session_id}/memory` | 세션 메모리 조회 |
| DELETE | `/api/v1/agent/sessions/{session_id}` | 세션 삭제 |
| GET | `/api/v1/agent/tools` | 사용 가능한 도구 목록 |

#### 검색 (RAG / NL2SQL)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/search` | 통합 검색 (auto/rag/nl2sql 모드) |
| POST | `/api/v1/rag` | RAG 문서 검색 전용 |
| POST | `/api/v1/nl2sql` | NL2SQL 데이터베이스 조회 전용 |

#### 관리자 - 문서 관리
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/admin/v1/documents` | 문서 저장 |
| GET | `/api/admin/v1/documents` | 문서 목록 조회 |
| GET | `/api/admin/v1/documents/{doc_id}` | 문서 상세 조회 |
| PUT | `/api/admin/v1/documents/{doc_id}` | 문서 수정 |
| DELETE | `/api/admin/v1/documents/{doc_id}` | 문서 삭제 |
| POST | `/api/admin/v1/documents/bulk-delete` | 문서 일괄 삭제 |
| POST | `/api/admin/v1/documents/embedding/execute` | 임베딩 실행 |
| POST | `/api/admin/v1/documents/embedding/preview` | 청킹 미리보기 |

#### 관리자 - 사용자/역할/테넌트/메뉴/부서
| Method | Endpoint | 설명 |
|--------|----------|------|
| CRUD | `/api/admin/v1/users` | 사용자 관리 |
| CRUD | `/api/admin/v1/roles` | 역할 관리 |
| CRUD | `/api/admin/v1/tenants` | 테넌트 관리 |
| CRUD | `/api/admin/v1/menus` | 메뉴 트리 관리 |
| CRUD | `/api/admin/v1/departments` | 부서(조직) 관리 |

#### 관리자 - 설정/코드
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET/PUT | `/api/admin/v1/settings` | 설정 조회/수정 |
| POST | `/api/admin/v1/settings/validate-api-key` | API 키 검증 |
| POST | `/api/admin/v1/settings/external-database/test` | 외부 DB 연결 테스트 |
| CRUD | `/api/admin/v1/codes` | 코드 관리 |

#### 대시보드/이력/내보내기
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/dashboard` | 시스템 대시보드 |
| CRUD | `/api/v1/dashboard/personal` | 개인 대시보드 위젯 |
| GET | `/api/v1/history` | API 이력 목록 (필터링) |
| GET | `/api/v1/history/statistics` | 이력 통계 |
| POST | `/api/v1/export` | Excel 내보내기 |

### API 테스트 예시

```bash
# 헬스 체크
curl http://localhost:19090/health

# 로그인 (토큰 획득)
curl -X POST "http://localhost:19090/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login_id": "admin", "password": "Admin1234!"}'

# AI Agent 검색 (인증 필요)
curl -X POST "http://localhost:19090/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"question": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?"}'

# RAG 검색
curl -X POST "http://localhost:19090/api/v1/rag" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "재택근무 정책이 뭐야?", "mode": "rag"}'

# NL2SQL 검색
curl -X POST "http://localhost:19090/api/v1/nl2sql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "2024년 입사자 수는?", "mode": "nl2sql"}'
```

## 프로젝트 구조

```
app/
├── main.py                       # FastAPI 엔트리포인트 + lifespan + 미들웨어/라우터 등록
├── config.py                     # Pydantic Settings (JWT, SSO, Rate Limit 등)
├── api/
│   ├── routes/                   # HTTP 엔드포인트 (thin layer)
│   │   ├── auth.py               # 인증 (login/logout/refresh/me/password)
│   │   ├── agent.py              # AI Agent (search, stream, sessions, tools)
│   │   ├── search.py             # RAG/NL2SQL 검색 (auto/rag/nl2sql + stream)
│   │   ├── documents.py          # 문서 관리 CRUD + 임베딩
│   │   ├── users.py              # 사용자 CRUD + 메뉴 권한 할당
│   │   ├── roles.py              # 역할 CRUD + 기본 메뉴
│   │   ├── menus.py              # 메뉴 트리 CRUD + reorder
│   │   ├── tenants.py            # 테넌트 CRUD
│   │   ├── departments.py        # 부서(조직) 트리 CRUD
│   │   ├── settings.py           # 설정 관리
│   │   ├── codes.py              # 코드 관리 + 공개 조회
│   │   ├── history.py            # API 이력 (필터, 통계, 세션별)
│   │   ├── dashboard.py          # 시스템 대시보드
│   │   ├── personal_dashboard.py # 개인 대시보드 위젯
│   │   └── export.py             # Excel 내보내기
│   └── services/                 # 비즈니스 로직 계층 (16개)
│       ├── auth_service.py       # 인증 (로그인, 토큰, 세션)
│       ├── agent_service.py      # Agent 오케스트레이션
│       ├── rag_service.py        # RAG 오케스트레이션
│       ├── nl2sql_service.py     # NL2SQL 오케스트레이션
│       ├── user_service.py       # 사용자 CRUD + scope 필터
│       ├── role_service.py       # 역할 CRUD + 기본 메뉴
│       ├── menu_service.py       # 메뉴 트리 CRUD
│       ├── tenant_service.py     # 테넌트 CRUD
│       ├── department_service.py # 부서(조직) 관리
│       ├── document_service.py   # 문서 CRUD + 임베딩
│       ├── settings_service.py   # 동적 설정 (DB fallback chain)
│       ├── code_service.py       # 코드 관리
│       ├── history_service.py    # 이력 저장 (비동기 워커 큐)
│       ├── dashboard_service.py  # 대시보드 KPI/차트/시스템
│       ├── personal_dashboard_service.py # 개인 대시보드 위젯
│       └── export_service.py     # Excel export
├── graphs/                       # LangGraph AI 워크플로우
│   ├── agent/                    # AI Agent (ReAct 패턴)
│   │   ├── graph.py              # InsightAgentGraph 클래스
│   │   ├── state.py              # AgentState TypedDict
│   │   ├── nodes/                # agent_node, tools_node, answer_node
│   │   ├── tools/                # sql_tool, rag_tool, calc_tool
│   │   └── middleware/           # PII 필터링, 미들웨어 체인
│   ├── nl2sql/                   # NL2SQL (멀티턴 + 의도분석 + PII)
│   │   ├── graph.py              # NL2SQLGraph 클래스
│   │   ├── state.py              # NL2SQLState TypedDict
│   │   └── nodes.py              # 14개 노드 함수
│   └── rag/                      # RAG (벡터 + 하이브리드 검색)
│       ├── graph.py              # RAGGraph 클래스
│       ├── state.py              # RAGState TypedDict
│       └── nodes.py              # retrieve, generate 노드
├── core/                         # 핵심 인프라
│   ├── security/                 # 인증/인가 시스템
│   │   ├── jwt.py                # JWT 생성/검증
│   │   ├── password.py           # bcrypt 해싱
│   │   ├── dependencies.py       # FastAPI Depends 헬퍼
│   │   ├── permission.py         # 메뉴 권한 체크
│   │   ├── tenant_context.py     # 테넌트 컨텍스트
│   │   ├── scope_filter.py       # 행 레벨 데이터 필터링
│   │   └── sso.py                # RS256 SSO 토큰 검증
│   ├── database/                 # 데이터베이스 계층
│   │   ├── connection.py         # PostgreSQL 커넥션 풀
│   │   ├── external.py           # 외부 비즈니스 DB (Lazy 초기화)
│   │   ├── sql_executor.py       # SQL 검증 + 실행
│   │   ├── schema_loader.py      # DB 스키마 인트로스펙션
│   │   ├── table_catalog.py      # 테이블 메타데이터 캐싱
│   │   └── adapters/             # DB 어댑터 (PostgreSQL, Oracle)
│   ├── llm/                      # LLM 통합 계층
│   │   ├── llm_config.py         # 멀티 프로바이더 LLM 초기화
│   │   ├── prompt_service.py     # 프롬프트 템플릿
│   │   └── sql_generator.py      # SQL 생성 오케스트레이션
│   ├── vector/                   # 벡터 검색 계층
│   │   ├── vector_store.py       # pgvector 연산
│   │   ├── text_chunker.py       # 문서 청킹
│   │   ├── hybrid_search.py      # 벡터 + 키워드 결합 검색
│   │   └── keyword_extractor.py  # 키워드 추출
│   ├── pii/                      # PII 감지 및 마스킹
│   ├── file/                     # 파일 파싱 (PDF, DOCX)
│   ├── sse/                      # Server-Sent Events
│   ├── checkpoint.py             # BoundedInMemorySaver (TTL+max 세션)
│   ├── errors/                   # 통일된 에러 처리
│   └── config/                   # 설정 스키마
├── models/                       # Pydantic 모델 (API 계약)
│   ├── auth.py                   # LoginRequest, TokenResponse
│   ├── agent.py                  # AgentRequest, AgentResponse
│   ├── search.py                 # SearchRequest, SearchResponse
│   ├── documents.py              # Document CRUD 모델
│   ├── users.py                  # User CRUD 모델
│   ├── roles.py                  # Role CRUD 모델
│   ├── tenants.py                # Tenant CRUD 모델
│   ├── menus.py                  # Menu 트리 모델
│   ├── departments.py            # Department 트리 모델
│   ├── settings.py               # Settings 모델
│   ├── codes.py                  # Code 모델
│   ├── history.py                # History 모델
│   ├── sse.py                    # SSE 이벤트 모델
│   ├── personal_dashboard.py     # 개인 대시보드 모델
│   ├── rag.py                    # DocumentSource, SQLResult
│   └── common.py                 # 공통 모델
├── middleware/                   # FastAPI 미들웨어 (6개)
│   ├── base.py                   # 미들웨어 베이스 클래스
│   ├── security.py               # 보안 응답 헤더 (CSP, XSS 방지)
│   ├── logging.py                # 요청/응답 로깅 + request_id
│   ├── auth.py                   # JWT/SSO 인증 (선택적 모드)
│   ├── rate_limit.py             # 요청 속도 제한 (Token Bucket)
│   └── history.py                # API 이력 비동기 저장
└── utils/                        # 유틸리티
    ├── logger.py                 # 구조화 로깅 + 파일 로테이션
    ├── langsmith.py              # LangSmith 통합 (선택)
    └── common.py                 # 공통 헬퍼

frontend/src/
├── views/
│   ├── LoginView.vue             # 로그인 페이지
│   ├── SSOCallbackView.vue       # SSO 리다이렉트 처리
│   ├── user/
│   │   ├── UserChatView.vue      # 사용자 채팅 인터페이스
│   │   └── PersonalDashboardView.vue  # 개인 대시보드
│   └── admin/
│       ├── AdminLayout.vue       # 관리자 레이아웃
│       ├── DashboardView.vue     # 시스템 대시보드
│       ├── ChatView.vue          # 관리자 채팅
│       ├── DocumentsView.vue     # 문서 관리
│       ├── DocumentDetailView.vue
│       ├── DocumentEditView.vue
│       ├── UsersView.vue         # 사용자 관리
│       ├── RolesView.vue         # 역할 관리
│       ├── MenusView.vue         # 메뉴 관리
│       ├── TenantsView.vue       # 테넌트 관리
│       ├── DepartmentsView.vue   # 부서(조직) 관리
│       ├── SettingsView.vue      # 설정 관리
│       ├── CodesView.vue         # 코드 관리
│       ├── HistoryView.vue       # API 이력
│       └── HistoryDetailView.vue
├── components/
│   ├── chat/                     # ChatMessage, ChatInput, SourceCard 등
│   ├── dashboard/                # KpiCards, DailyTrendChart, SystemStatus 등
│   ├── personal-dashboard/       # DashboardGrid, DashboardWidget 등
│   ├── chart/                    # ChartBuilder
│   ├── user/                     # UserChatLayout, UserChatMessage 등
│   ├── documents/                # ChunkPreview
│   └── layout/                   # AppHeader, AppSidebar
├── api/                          # Axios API 클라이언트 (16개 모듈)
├── store/modules/                # Vuex 상태 관리
├── router/                       # Vue Router 라우트 정의
├── composables/                  # Vue 3 Composition 함수
└── assets/styles/                # SCSS 변수 + Mixin 시스템
    ├── _variables.scss
    ├── main.scss
    └── mixins/                   # 재사용 스타일 mixin

scripts/                          # 유틸리티 스크립트
tests/                            # 통합 테스트 (16개 파일)
docs/sql/                         # DDL 스크립트 + Oracle 비즈니스 DB
```

## 미들웨어 스택

요청은 다음 순서로 처리됩니다:

```
Request → CORSMiddleware
  → SecurityHeadersMiddleware (보안 응답 헤더)
  → LoggingMiddleware (request_id 생성, 요청/응답 로깅)
  → AuthMiddleware (JWT/SSO 토큰 검증 → request.state.current_user)
  → RateLimitMiddleware (사용자/IP 기반 속도 제한)
  → HistoryMiddleware (API 이력 DB 저장)
  → Route Handler
  → Response (역순 실행)
```

## AI 워크플로우

### Agent Flow (ReAct)
```
START → agent_node → should_continue()
                      ├─ "tools" → tools_node → agent_node (반복)
                      └─ "answer" → answer_node → END
```

### NL2SQL Flow (멀티턴)
```
load_history → intent_rewrite → should_route
  ├─ sql_needed → schema → fewshot → prompt → generate → validate
  │                                                        ├─ execute → pii_filter → answer → save_history → END
  │                                                        ├─ retry → prepare_retry → fewshot (재시도)
  │                                                        └─ error → handle_error → END
  └─ sql_not_needed → answer_from_history → save_history → END
```

### RAG Flow
```
retrieve → generate_answer → END
```

## 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| **Core** |
| `DATABASE_URL` | PostgreSQL 연결 URL | - | ✅ |
| `SECRET_KEY` | JWT 시크릿 키 | - | ✅ |
| `APP_ENV` | 환경 (development/production) | development | |
| `APP_HOST` | 서버 호스트 | 0.0.0.0 | |
| `APP_PORT` | 서버 포트 | 19090 | |
| `CONTEXT_PATH` | API 컨텍스트 경로 | (없음) | |
| **Database** |
| `DB_POOL_SIZE` | 커넥션 풀 크기 | 20 | |
| `DB_MAX_OVERFLOW` | 풀 최대 오버플로 | 10 | |
| **LLM (DB 설정 fallback)** |
| `OPENAI_API_KEY` | OpenAI API 키 | - | |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - | |
| `LLM_MODEL` | 기본 LLM 모델 | gpt-4o | |
| `EMBEDDING_MODEL` | 임베딩 모델 | text-embedding-3-small | |
| **Security** |
| `ALGORITHM` | JWT 알고리즘 | HS256 | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 만료 | 30 | |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 만료 | 1 | |
| `PASSWORD_MIN_LENGTH` | 비밀번호 최소 길이 | 8 | |
| `LOGIN_MAX_FAIL_COUNT` | 로그인 실패 잠금 횟수 | 5 | |
| `LOGIN_LOCK_MINUTES` | 계정 잠금 시간(분) | 30 | |
| **SSO** |
| `SSO_ENABLED` | SSO 활성화 | false | |
| `SSO_PUBLIC_KEY_PATH` | SSO 공개키 경로 | keys/sso_public.pem | |
| `SSO_ALLOWED_ISSUERS` | 허용 발급자 | h5-system | |
| `SSO_TOKEN_MAX_AGE` | SSO 토큰 유효기간(초) | 300 | |
| `SSO_AUTO_CREATE_USER` | 자동 사용자 생성 | true | |
| `SSO_FRONTEND_URL` | SSO 프론트엔드 URL | http://localhost:19080 | |
| **Rate Limiting** |
| `RATE_LIMIT_ENABLED` | Rate Limit 활성화 | true | |
| `RATE_LIMIT_DEFAULT_RPM` | 기본 분당 요청 수 | 600 | |
| `RATE_LIMIT_LOGIN_RPM` | 로그인 분당 요청 수 | 20 | |
| `RATE_LIMIT_AI_RPM` | AI 분당 요청 수 | 20 | |
| `RATE_LIMIT_ADMIN_RPM` | 관리자 분당 요청 수 | 600 | |
| **Logging** |
| `LOG_LEVEL` | 로그 레벨 | INFO | |
| `LOG_FORMAT` | 로그 포맷 (text/json) | text | |
| `LOG_FILE` | 로그 파일 경로 | ./logs/app.log | |
| `LOG_BACKUP_COUNT` | 로그 보관 일수 | 30 | |
| **File Upload** |
| `UPLOAD_MAX_SIZE_MB` | 최대 업로드 크기(MB) | 50 | |
| `UPLOAD_ALLOWED_EXTENSIONS` | 허용 확장자 | .pdf,.docx | |
| **Monitoring (선택)** |
| `LANGCHAIN_TRACING_V2` | LangSmith 추적 | false | |
| `LANGCHAIN_API_KEY` | LangSmith API 키 | - | |

**설정 우선순위**: Admin UI (DB `tb_app_settings`) > `.env` > 코드 기본값

## 테스트

```bash
# 가상환경 활성화
conda activate penv3.13-nlq

# 전체 테스트 실행 (순서대로 실행 권장)
pytest tests/ -v

# 단일 테스트 파일
pytest tests/test_02_auth.py -v

# 단일 테스트 함수
pytest tests/test_02_auth.py::test_login -v

# 커버리지
pytest tests/ --cov=app --cov-report=html
```

### 테스트 파일 목록
| 파일 | 테스트 대상 |
|------|------------|
| test_01_health.py | 헬스 체크 |
| test_02_auth.py | 인증 (login/refresh/logout/me) |
| test_03_tenants.py | 테넌트 CRUD |
| test_04_roles.py | 역할 CRUD |
| test_05_menus.py | 메뉴 CRUD |
| test_06_users.py | 사용자 CRUD + scope 검증 |
| test_07_codes.py | 코드 관리 |
| test_08_settings.py | 동적 설정 |
| test_09_documents.py | 문서 관리 |
| test_10_search.py | 검색 (RAG/NL2SQL) |
| test_11_personal_dashboard.py | 개인 대시보드 위젯 |
| test_12_rate_limit.py | Rate Limiting |
| test_sso.py | SSO 토큰 검증 |
| test_hr_analytics_coverage_*.py | HR 분석 쿼리 커버리지 |

## 보안

### SQL Injection 방지 (NL2SQL)
1. **키워드 블랙리스트**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. **테이블 화이트리스트**: 허용된 테이블만 접근
3. **SELECT-only 강제**: sqlparse 기반 검증
4. **타임아웃**: 30초 SQL 실행 시간 제한
5. **Row 제한**: 어댑터별 자동 LIMIT 추가

### PII 보호
- **Agent**: 입출력 PII 마스킹 (미들웨어)
- **NL2SQL**: pii_filter_node로 SQL 결과 PII 마스킹 후 LLM 전송
- **Core**: `app/core/pii/pii_service.py` PII 감지/마스킹 서비스

### 인증/인가
- JWT + SSO 이중 인증 지원
- 역할 기반 접근 제어 (GLOBAL/TENANT/USER)
- 메뉴 기반 CRUD 권한 매트릭스
- Rate Limiting (Token Bucket 알고리즘)
- 보안 헤더 (X-Frame-Options, X-Content-Type-Options, CSP 등)

## 트러블슈팅

### pgvector 확장 없음
**증상**: `extension "vector" does not exist`
**해결**: PostgreSQL에서 수동 설치
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### LLM 모델 404 오류
**증상**: `Error code: 404 - The model 'xxx' does not exist`
**해결**: Admin UI → Settings → LLM에서 유효한 모델명으로 변경

### 벡터 검색 결과 없음
**증상**: RAG 검색 시 "관련 문서를 찾을 수 없습니다"
**해결**: `tb_docs`에서 `indexed=true` 확인, 임베딩 실행, `similarity_threshold` 낮추기

### DB Connection Pool 소진
**증상**: 연결 타임아웃
**해결**: `.env`에서 `DB_POOL_SIZE` 증가 (기본: 20)

### FastAPI Reload 미감지
**증상**: 코드 변경 후 반영 안 됨
**해결**: 서버 수동 재기동 (`--reload` 모드에서도 미감지 가능)

### 라우트 순서 문제
**증상**: 고정 경로가 파라미터 경로에 매칭
**해결**: `/sessions` 같은 고정 경로를 `/{request_id}` 같은 파라미터 경로보다 앞에 배치

## 추가 문서

- [CLAUDE.md](CLAUDE.md) - Claude Code 작업 가이드 (코드베이스 상세 설명)
- [docs/design/](docs/design/) - 설계 문서 (아키텍처, AI 워크플로우, 인증/인가 등)
- [docs/sql/](docs/sql/) - DB DDL 스크립트

## 라이선스

MIT License
