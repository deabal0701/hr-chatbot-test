# InsightLink AI 지식베이스 시스템 개발계획서

**프로젝트명**: InsightLink - 기업 AI 지식베이스 어시스턴트
**버전**: 1.0
**작성일**: 2026-01-10
**개발기간**: 4개월

---

## 1. 프로젝트 개요

### 1.1 목적
기업 내 문서 및 데이터베이스에 대한 자연어 질의응답 시스템 구축

### 1.2 핵심 기능
| 기능 | 설명 |
|------|------|
| **AI Agent (ReAct)** | 자율적 도구 선택 및 멀티스텝 추론 |
| **RAG** | 문서 기반 의미 검색 및 답변 생성 |
| **NL2SQL** | 자연어 → SQL 변환 및 실행 |
| **Multi-LLM** | OpenAI, Anthropic 제공자 지원 |

### 1.3 기대 효과
- 업무 효율성 향상 (문서/데이터 검색 시간 80% 단축)
- 비개발자도 데이터베이스 직접 조회 가능
- 지식 접근성 향상 및 업무 생산성 증대

---

## 2. 시스템 아키텍처

### 2.1 하드웨어 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        [클라이언트]                              │
│                    웹 브라우저 (Vue 3)                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS (443)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     [로드 밸런서]                                │
│                   Nginx / AWS ALB                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  App Server 1   │ │  App Server 2   │ │  App Server N   │
│  FastAPI        │ │  FastAPI        │ │  FastAPI        │
│  (4 workers)    │ │  (4 workers)    │ │  (4 workers)    │
│  8GB RAM        │ │  8GB RAM        │ │  8GB RAM        │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  PostgreSQL     │ │  Redis          │ │  External APIs  │
│  + pgvector     │ │  (캐시/세션)    │ │  OpenAI/Claude  │
│  Primary+Replica│ │  Cluster        │ │                 │
│  16GB RAM       │ │  4GB RAM        │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

**권장 사양**

| 구성요소 | 개발 환경 | 운영 환경 |
|---------|----------|----------|
| App Server | 4 vCPU, 8GB RAM x 1 | 4 vCPU, 8GB RAM x 2+ |
| DB Server | 2 vCPU, 8GB RAM | 4 vCPU, 16GB RAM (Primary + Replica) |
| Redis | - | 2 vCPU, 4GB RAM |
| Storage | 50GB SSD | 200GB SSD (DB) + 50GB (App) |

---

### 2.2 소프트웨어 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Vue 3)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  ChatView    │  │  Documents   │  │  Settings    │  │  Dashboard  │ │
│  │  (Agent UI)  │  │  (문서관리)  │  │  (설정관리)  │  │  (모니터링) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        API Layer                                 │   │
│  │   /agent/search    /search    /documents    /settings    /codes  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     LangGraph Workflows                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │ AgentGraph  │  │  RAGGraph   │  │ NL2SQLGraph │              │   │
│  │  │  (ReAct)    │  │  (검색+생성)│  │ (SQL 변환)  │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Service Layer                               │   │
│  │  VectorStore  │  SQLExecutor  │  SchemaLoader  │  SettingsService│  │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      AI Tools Layer                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │  SQL Tool   │  │  RAG Tool   │  │ Calculator  │              │   │
│  │  │  (NL2SQL)   │  │  (문서검색) │  │  (계산기)   │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │   External DB   │     │    LLM APIs     │
│  + pgvector     │     │  (Business DB)  │     │  OpenAI/Claude  │
│ ┌─────────────┐ │     │ ┌─────────────┐ │     └─────────────────┘
│ │  hr_docs    │ │     │ │  employee   │ │
│ │  settings   │ │     │ │  department │ │
│ │  query_log  │ │     │ │  salary     │ │
│ └─────────────┘ │     │ └─────────────┘ │
└─────────────────┘     └─────────────────┘
```

---

## 3. AI Agent 상세 Flow (ReAct 패턴)

### 3.1 Agent 실행 흐름

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AI AGENT FLOW (ReAct Pattern)                        │
└──────────────────────────────────────────────────────────────────────────────┘

[사용자 질문]
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [1. INIT] Agent 초기화                                                      │
│  • request_id 생성                                                          │
│  • session_id로 InMemorySaver에서 대화 히스토리 로드                        │
│  • AgentState 초기화 (messages, question, config)                           │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [2. AGENT NODE] LLM 의사결정                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ System Prompt:                                                        │  │
│  │ "You are an AI assistant with access to tools:                        │  │
│  │  - query_database_tool: DB 조회 (통계, 집계, 레코드)                  │  │
│  │  - search_documents_tool: 문서 검색 (정책, 규정, FAQ)                 │  │
│  │  - calculate_tool: 수학 계산 (백분율, 평균, 합계)"                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  LLM 판단:                                                                   │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │ 도구 필요?  │────▶│  어떤 도구? │────▶│ 파라미터는? │                   │
│  └─────────────┘     └─────────────┘     └─────────────┘                   │
│         │                   │                   │                           │
│         ▼                   ▼                   ▼                           │
│  tool_calls 생성 또는 최종 답변 생성                                        │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [3. SHOULD_CONTINUE] 분기 결정                                              │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 체크 항목:                                                          │    │
│  │  • iteration_count >= max_iterations (기본 10회)?                   │    │
│  │  • elapsed_time > timeout_seconds (기본 60초)?                      │    │
│  │  • 마지막 메시지에 tool_calls 존재?                                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│      ┌─────────────────────────┬────────────────────────────┐               │
│      │                         │                            │               │
│      ▼                         ▼                            ▼               │
│  [tool_calls 있음]        [tool_calls 없음]          [제한 도달]            │
│  return "continue"        return "end"               return "end"           │
└────────────────────────────────────────────────────────────────────────────┘
     │
     │ "continue"
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [4. TOOLS NODE] 도구 실행                                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ToolNode(tools) - LangGraph 내장                                     │   │
│  │                                                                       │   │
│  │  선택된 도구에 따라 실행:                                            │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ [SQL Tool] query_database_tool                               │    │   │
│  │  │  1. 자연어 → SQL 변환 (NL2SQL Graph 호출)                    │    │   │
│  │  │  2. SQL 보안 검증 (금지 키워드, 테이블 화이트리스트)         │    │   │
│  │  │  3. SQL 실행 (30초 타임아웃, 1000행 제한)                    │    │   │
│  │  │  4. 결과 반환                                                 │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ [RAG Tool] search_documents_tool                             │    │   │
│  │  │  1. 질문 임베딩 생성 (text-embedding-3-small)                │    │   │
│  │  │  2. pgvector 유사도 검색 (cosine similarity)                 │    │   │
│  │  │  3. 상위 K개 문서 반환 (기본 5개)                            │    │   │
│  │  │  4. 스니펫 포맷팅                                            │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │ [Calculator Tool] calculate_tool                             │    │   │
│  │  │  1. 수식 파싱 (AST 기반, eval 사용 안함)                     │    │   │
│  │  │  2. 허용된 연산만 실행 (+,-,*,/,sqrt,sum,...)               │    │   │
│  │  │  3. 결과 반환                                                 │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Observation (도구 실행 결과) → ToolMessage로 추가                          │
└────────────────────────────────────────────────────────────────────────────┘
     │
     │ (Agent Node로 복귀 - 루프)
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [5. AGENT NODE] 결과 분석 및 다음 행동 결정                                 │
│                                                                              │
│  LLM이 Observation 분석:                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ "DB에서 2024년 입사자 27명 확인.                                      │  │
│  │  정책 정보도 필요하므로 search_documents_tool 호출 필요."             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  다음 행동 결정:                                                            │
│   • 추가 도구 필요 → tool_calls 생성 → SHOULD_CONTINUE로                   │
│   • 충분한 정보 수집 → 최종 답변 생성 → END                                │
└────────────────────────────────────────────────────────────────────────────┘
     │
     │ "end" (최종 답변 생성됨)
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ [6. COMPLETE] 응답 구성                                                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ AgentResponse:                                                        │  │
│  │  • answer: "2024년 입사자는 총 27명이며, 재택근무 정책은..."          │  │
│  │  • steps: [Step1: SQL Tool, Step2: RAG Tool]                          │  │
│  │  • total_iterations: 2                                                 │  │
│  │  • tools_used: ["query_database", "search_documents"]                 │  │
│  │  • session_id: "user123-session456"                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  InMemorySaver에 대화 히스토리 자동 저장 (thread_id = session_id)          │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
[사용자에게 응답 반환]
```

### 3.2 멀티스텝 질의 예시

```
질문: "2024년 입사자는 몇 명이고, 재택근무 정책은 무엇인가요?"

[Iteration 1]
┌──────────────────────────────────────────────────────────────┐
│ THOUGHT: "입사자 수는 DB 조회, 정책은 문서 검색 필요"        │
│ ACTION: query_database_tool                                   │
│ INPUT: "2024년 입사자 수"                                     │
│ OBSERVATION: "27명의 직원이 2024년에 입사했습니다"           │
└──────────────────────────────────────────────────────────────┘

[Iteration 2]
┌──────────────────────────────────────────────────────────────┐
│ THOUGHT: "DB 정보 확인됨. 이제 재택근무 정책 검색 필요"      │
│ ACTION: search_documents_tool                                 │
│ INPUT: "재택근무 정책"                                        │
│ OBSERVATION: "재택근무 정책 문서: 주 2회 재택근무 가능..."   │
└──────────────────────────────────────────────────────────────┘

[Iteration 3]
┌──────────────────────────────────────────────────────────────┐
│ THOUGHT: "모든 정보 수집 완료. 최종 답변 생성"               │
│ FINAL ANSWER:                                                 │
│ "2024년 입사자는 총 27명입니다.                              │
│  재택근무 정책에 따르면 주 2회 재택근무가 가능하며,          │
│  사전 신청 후 팀장 승인이 필요합니다."                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. 데이터베이스 설계

### 4.1 시스템 DB (hermes_db)

#### 4.1.1 app_settings (동적 설정)
```sql
CREATE TABLE app_settings (
    id BIGSERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,      -- openai, llm, rag, nl2sql, agent 등
    key VARCHAR(100) NOT NULL,          -- api_key, model, temperature 등
    value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',  -- string, int, float, bool, text
    description TEXT,
    is_secret BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (category, key)
);
```

#### 4.1.2 hr_docs (문서 + 벡터)
```sql
CREATE TABLE hr_docs (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,             -- policy, faq, regulation, guideline
    language TEXT DEFAULT 'ko',
    content TEXT NOT NULL,
    metadata JSONB,                      -- 추가 메타데이터
    embedding VECTOR(1536),             -- pgvector 임베딩
    embedding_model TEXT DEFAULT 'text-embedding-3-small',
    indexed BOOLEAN DEFAULT FALSE,
    embedded_at TIMESTAMPTZ,
    chunk_index INT DEFAULT 0,          -- 청킹 시 인덱스
    total_chunks INT DEFAULT 1,
    parent_doc_id BIGINT REFERENCES hr_docs(id),
    source_type TEXT DEFAULT 'ui_input',
    source_file TEXT,
    content_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벡터 인덱스 (IVFFlat)
CREATE INDEX idx_hr_docs_embedding ON hr_docs
    USING ivfflat (embedding) WITH (lists = 100);
```

#### 4.1.3 query_log (질의 로그)
```sql
CREATE TABLE query_log (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT,
    query_text TEXT NOT NULL,
    query_type TEXT,                    -- agent, rag, nl2sql
    intent TEXT,
    filters JSONB,
    response_time_ms INT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4.1.4 code_master (공통코드)
```sql
CREATE TABLE code_master (
    code_id BIGSERIAL PRIMARY KEY,
    code_group VARCHAR(50) NOT NULL,
    code_value VARCHAR(100) NOT NULL,
    code_name VARCHAR(200) NOT NULL,
    description TEXT,
    metadata JSONB,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (code_group, code_value)
);
```

### 4.2 비즈니스 DB (business_db)

#### 4.2.1 employee (직원)
```sql
CREATE TABLE employee (
    emp_id BIGSERIAL PRIMARY KEY,
    emp_no TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    name_en TEXT,
    gender TEXT,
    birth_date DATE,
    hire_date DATE NOT NULL,
    position TEXT,                      -- 직급
    job_family TEXT,                    -- 직군
    department_id BIGINT REFERENCES department(dept_id),
    work_location TEXT,
    employment_type TEXT,               -- 정규직/계약직
    status TEXT DEFAULT 'active',
    resignation_date DATE,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4.2.2 department (부서)
```sql
CREATE TABLE department (
    dept_id BIGSERIAL PRIMARY KEY,
    dept_name TEXT NOT NULL,
    dept_code TEXT UNIQUE,
    parent_dept_id BIGINT REFERENCES department(dept_id),
    region TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4.2.3 salary (급여)
```sql
CREATE TABLE salary (
    id BIGSERIAL PRIMARY KEY,
    emp_id BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
    effective_date DATE NOT NULL,
    base_salary NUMERIC(12,2),
    currency TEXT DEFAULT 'KRW',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4.2.4 job_history (인사이력)
```sql
CREATE TABLE job_history (
    id BIGSERIAL PRIMARY KEY,
    emp_id BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
    from_date DATE NOT NULL,
    to_date DATE,
    department_id BIGINT REFERENCES department(dept_id),
    position TEXT,
    job_family TEXT,
    work_location TEXT,
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4.2.5 performance_review (성과평가)
```sql
CREATE TABLE performance_review (
    id BIGSERIAL PRIMARY KEY,
    emp_id BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
    review_period TEXT NOT NULL,        -- '2024-H1', '2024-H2'
    reviewer_id BIGINT REFERENCES employee(emp_id),
    rating TEXT,                        -- S, A, B, C, D
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.3 ERD (Entity Relationship Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SYSTEM DB (hermes_db)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐    │
│  │  app_settings   │      │    hr_docs      │      │   query_log     │    │
│  ├─────────────────┤      ├─────────────────┤      ├─────────────────┤    │
│  │ PK id           │      │ PK id           │      │ PK id           │    │
│  │    category     │      │    title        │      │    user_id      │    │
│  │    key          │      │    content      │      │    query_text   │    │
│  │    value        │      │    embedding    │◀──┐  │    query_type   │    │
│  │    value_type   │      │ FK parent_doc_id│───┘  │    response_ms  │    │
│  └─────────────────┘      └─────────────────┘      └────────┬────────┘    │
│                                                              │             │
│                           ┌──────────────────────────────────┼─────┐      │
│                           │                                  │     │      │
│                           ▼                                  ▼     ▼      │
│                    ┌─────────────────┐            ┌─────────────────┐    │
│                    │ rag_search_log  │            │sql_execution_log│    │
│                    ├─────────────────┤            ├─────────────────┤    │
│                    │ PK id           │            │ PK id           │    │
│                    │ FK query_log_id │            │ FK query_log_id │    │
│                    │    top_k        │            │    generated_sql│    │
│                    │    llm_model    │            │    row_count    │    │
│                    └─────────────────┘            └─────────────────┘    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          BUSINESS DB (business_db)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                       │
│  │   department    │◀───────────────────────┐                              │
│  ├─────────────────┤                        │                              │
│  │ PK dept_id      │                        │                              │
│  │    dept_name    │                        │                              │
│  │    dept_code    │                        │                              │
│  │ FK parent_id    │────────────────────────┘                              │
│  │    region       │                                                       │
│  └────────┬────────┘                                                       │
│           │                                                                 │
│           │ 1:N                                                            │
│           ▼                                                                 │
│  ┌─────────────────┐                                                       │
│  │    employee     │◀──────────────────────────────────────┐               │
│  ├─────────────────┤                                       │               │
│  │ PK emp_id       │                                       │               │
│  │    emp_no       │                                       │               │
│  │    name         │                                       │               │
│  │ FK department_id│                                       │               │
│  │    position     │                                       │               │
│  │    hire_date    │                                       │               │
│  │    status       │                                       │               │
│  └────────┬────────┘                                       │               │
│           │                                                │               │
│           │ 1:N                                            │               │
│           ├────────────────┬───────────────────┐          │               │
│           ▼                ▼                   ▼          │               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐              │
│  │    salary       │ │  job_history    │ │performance_review              │
│  ├─────────────────┤ ├─────────────────┤ ├─────────────────┤              │
│  │ PK id           │ │ PK id           │ │ PK id           │              │
│  │ FK emp_id       │ │ FK emp_id       │ │ FK emp_id       │              │
│  │    base_salary  │ │ FK department_id│ │ FK reviewer_id  │──────────────┘
│  │    effective_dt │ │    position     │ │    rating       │               │
│  │    currency     │ │    from_date    │ │    review_period│               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 기능 리스트

### 5.1 핵심 기능

| No | 기능 | 설명 | 우선순위 |
|----|------|------|----------|
| 1 | AI Agent 검색 | ReAct 패턴 기반 멀티스텝 질의응답 | P0 |
| 2 | RAG 문서 검색 | 벡터 기반 의미 검색 + LLM 답변 생성 | P0 |
| 3 | NL2SQL 쿼리 | 자연어 → SQL 변환 및 실행 | P0 |
| 4 | 멀티턴 대화 | 세션 기반 대화 히스토리 관리 | P0 |
| 5 | 문서 관리 | 문서 CRUD + 청킹 + 임베딩 | P0 |
| 6 | 동적 설정 | DB 기반 실시간 설정 관리 | P1 |
| 7 | Multi-LLM | OpenAI/Anthropic 제공자 전환 | P1 |

### 5.2 관리 기능

| No | 기능 | 설명 | 우선순위 |
|----|------|------|----------|
| 8 | 설정 관리 UI | LLM, RAG, NL2SQL 설정 관리 | P1 |
| 9 | 프롬프트 관리 | 시스템 프롬프트 편집 및 이력 | P1 |
| 10 | 코드 관리 | 공통코드 CRUD | P2 |
| 11 | 대시보드 | 사용 통계 및 모니터링 | P2 |
| 12 | 사용자 관리 | 인증/인가 (향후) | P3 |

### 5.3 보안 기능

| No | 기능 | 설명 | 우선순위 |
|----|------|------|----------|
| 13 | SQL Injection 방지 | 키워드 필터, 테이블 화이트리스트 | P0 |
| 14 | API 키 암호화 | is_secret 플래그 기반 마스킹 | P0 |
| 15 | 쿼리 타임아웃 | 30초 타임아웃, 1000행 제한 | P0 |
| 16 | 안전한 계산 | AST 기반 수식 평가 (eval 미사용) | P0 |

---

## 6. 개발 일정 (4개월)

### 6.1 Phase 1: 기반 구축 (1개월차)

```
Week 1-2: 환경 구성 및 기본 구조
├── 개발 환경 설정 (Python, Node.js, PostgreSQL)
├── 프로젝트 구조 설계
├── DB 스키마 설계 및 생성
└── API 기본 구조 (FastAPI)

Week 3-4: 핵심 서비스 개발
├── LLM 통합 모듈 (LLMConfigManager)
├── 벡터 저장소 서비스 (VectorStore)
├── 설정 서비스 (SettingsService)
└── 기본 API 엔드포인트
```

### 6.2 Phase 2: AI 기능 개발 (2개월차)

```
Week 5-6: RAG 시스템
├── 문서 청킹 (TextChunker)
├── 임베딩 생성 및 저장
├── 벡터 검색 구현
└── RAG Graph 개발

Week 7-8: NL2SQL 시스템
├── 스키마 로더 개발
├── SQL 생성 프롬프트
├── SQL 검증 및 실행
└── NL2SQL Graph 개발
```

### 6.3 Phase 3: Agent 개발 (3개월차)

```
Week 9-10: AI Agent 핵심
├── BaseTool 추상 클래스
├── SQL Tool, RAG Tool, Calculator Tool
├── Agent Graph (ReAct 패턴)
└── InMemorySaver 세션 관리

Week 11-12: 통합 및 최적화
├── 도구 간 연동 테스트
├── 멀티스텝 시나리오 테스트
├── 성능 최적화 (캐싱)
└── 에러 처리 강화
```

### 6.4 Phase 4: UI 및 완성 (4개월차)

```
Week 13-14: 프론트엔드 개발
├── 채팅 UI (Agent 모드)
├── 문서 관리 UI
├── 설정 관리 UI
└── 대시보드

Week 15-16: 테스트 및 배포
├── 통합 테스트
├── 성능 테스트
├── 보안 점검
├── 문서화
└── 운영 환경 배포
```

### 6.5 마일스톤

| 마일스톤 | 완료 시점 | 주요 산출물 |
|---------|----------|------------|
| M1 | 1개월차 종료 | 기본 API, DB 구조, LLM 통합 |
| M2 | 2개월차 종료 | RAG + NL2SQL 작동 |
| M3 | 3개월차 종료 | AI Agent 완성 |
| M4 | 4개월차 종료 | 전체 시스템 배포 |

---

## 7. 기술 스택

### 7.1 Backend

| 기술 | 버전 | 용도 |
|------|------|------|
| Python | 3.11+ | 메인 언어 |
| FastAPI | 0.115+ | 웹 프레임워크 |
| LangChain | 1.2+ | LLM 통합 |
| LangGraph | 1.0+ | AI 워크플로우 |
| psycopg3 | 3.0+ | PostgreSQL 드라이버 |
| Pydantic | 2.7+ | 데이터 검증 |

### 7.2 Frontend

| 기술 | 버전 | 용도 |
|------|------|------|
| Vue.js | 3.x | 프론트엔드 프레임워크 |
| Vuex | 4.x | 상태 관리 |
| Vue Router | 4.x | 라우팅 |
| Axios | 1.x | HTTP 클라이언트 |
| Tailwind CSS | 3.x | 스타일링 |

### 7.3 Database & AI

| 기술 | 버전 | 용도 |
|------|------|------|
| PostgreSQL | 15+ | 메인 DB |
| pgvector | 0.5+ | 벡터 검색 |
| OpenAI API | - | GPT-4o, Embeddings |
| Anthropic API | - | Claude 3.5 Sonnet |

---

## 8. 향후 확장 계획

### 8.1 Phase 5: 고급 기능 (향후)

| 기능 | 설명 | 예상 시기 |
|------|------|----------|
| 스트리밍 응답 | 실시간 타이핑 효과 | +1개월 |
| Multi-Agent | 에이전트 간 협업 | +2개월 |
| 장기 메모리 | 영구 대화 히스토리 | +2개월 |
| 파일 업로드 | PDF/Excel 직접 업로드 | +3개월 |
| 음성 인터페이스 | STT/TTS 통합 | +4개월 |

### 8.2 Phase 6: 엔터프라이즈 (향후)

| 기능 | 설명 | 예상 시기 |
|------|------|----------|
| SSO 통합 | LDAP/SAML 인증 | +3개월 |
| 권한 관리 | RBAC 기반 접근 제어 | +3개월 |
| 감사 로그 | 상세 행위 추적 | +4개월 |
| API Gateway | 외부 시스템 연동 | +5개월 |
| 멀티테넌시 | 조직별 격리 | +6개월 |

### 8.3 Phase 7: 분석 및 최적화 (향후)

| 기능 | 설명 | 예상 시기 |
|------|------|----------|
| 사용 분석 | 질의 패턴 분석 | +4개월 |
| 모델 파인튜닝 | 도메인 특화 모델 | +6개월 |
| 비용 최적화 | LLM 호출 최소화 | +4개월 |
| 캐시 고도화 | Redis 클러스터 | +5개월 |

---

## 9. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| LLM API 장애 | 서비스 중단 | 멀티 제공자 자동 폴백 |
| 비용 초과 | 예산 초과 | 캐싱, 저렴한 모델 활용 |
| 응답 지연 | UX 저하 | 스트리밍, 타임아웃 |
| 보안 취약점 | 정보 유출 | SQL 검증, 화이트리스트 |
| 데이터 품질 | 답변 오류 | 문서 검증, 피드백 루프 |

---

## 10. 결론

InsightLink는 AI Agent, RAG, NL2SQL을 통합한 기업용 지식베이스 시스템으로, 4개월간의 체계적인 개발을 통해 기업 내 정보 접근성과 업무 효율성을 획기적으로 개선할 것으로 기대됩니다.

---

**문서 이력**

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 1.0 | 2026-01-10 | - | 최초 작성 |
