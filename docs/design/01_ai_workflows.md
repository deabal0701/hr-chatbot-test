# AI 워크플로우 설계

> 최종 수정: 2026-03-12

LangGraph 기반 3개의 독립적인 AI 워크플로우를 운영한다.

---

## 1. AI Agent (ReAct 패턴)

### 1.1 개요

사용자 질문에 대해 LLM이 **자율적으로 도구를 선택**하여 반복 추론(Think→Action→Observe)하는 패턴.
복합 질문("2024년 입사자 수는 몇 명이고 재택근무 정책은?")을 SQL 도구 + RAG 도구 조합으로 처리한다.

- **파일**: `app/graphs/agent/graph.py` (InsightAgentGraph)
- **멀티턴**: BoundedInMemorySaver 체크포인팅 (TTL 24h, max 1000세션)
- **스트리밍**: SSE (`astream_events`, forward-only 스테이지)

### 1.2 그래프 흐름

```
START → agent_node → should_continue()
                      ├─ "tools"  → tools_node → agent_node (반복)
                      └─ "answer" → answer_node → END
```

- **agent_node**: LLM이 질문을 분석하고 도구 호출 또는 최종 답변 결정
- **should_continue()**: 마지막 AIMessage에 tool_calls가 있으면 "tools", 없으면 "answer"
- **tools_node**: TOOL_MAP 딕셔너리로 도구 라우팅, 결과를 ToolMessage로 수집
- **answer_node**: 현재 턴의 도구 결과를 종합하여 LLM(temperature=0.1)이 자연어 답변 생성

### 1.3 상태 (AgentState)

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 누적 (reducer)
    question: str               # 원본 질문
    session_id: str             # 멀티턴 세션
    request_id: str             # 요청 추적
    iteration_count: int        # 현재 반복 (기본 최대 10)
    max_iterations: int
    final_answer: str           # 최종 답변
    config: AgentConfig
    last_tool_name: str         # 마지막 도구명
    last_tool_result: str       # 마지막 도구 결과
    generated_sql: str          # SQL 도구 결과
    sql_result: Optional[SQLResult]
    rag_sources: List[Dict]     # RAG 도구 결과
    tools_used: List[str]       # 사용된 도구 목록
    error: Optional[str]        # 에러 메시지
    start_time: float
```

### 1.4 도구 (Tools)

| 도구 | 파일 | 기능 | 캐싱 |
|------|------|------|------|
| SQLQueryTool | `tools/sql_tool.py` | 자연어 → SQL 생성 → 실행 → 결과 반환 | max 100 쿼리 |
| DocumentSearchTool | `tools/rag_tool.py` | pgvector 벡터 검색 → 관련 문서 반환 | max 50 검색 |
| CalculatorTool | `tools/calc_tool.py` | 안전한 수식 계산 (AST 기반) | 없음 |

도구는 `BaseTool` ABC를 상속하며, LangChain `@tool` 데코레이터로 래핑하여 Agent에 제공한다.

**BaseTool 실행 흐름** (Template Method):
```
validate_input → before_execute (캐시 확인) → _execute (구현부) → validate_output → after_execute (캐시 저장) → record_metrics
```

**SQLQueryTool 상세**:
- Enhanced 모드: NL2SQL 노드 패턴 재사용 (schema → fewshot → prompt → generate → validate → execute)
- 재시도: max_retries=2
- PII 마스킹: 쿼리 결과에 pii_service 적용

**CalculatorTool 허용 연산**:
- 이항: +, -, *, /, //, %, **
- 함수: abs, round, min, max, sum, len, pow, sqrt, ceil, floor
- AST 화이트리스트 기반 (eval/exec 미사용)

### 1.5 미들웨어

```
입력: MiddlewareChain.process_input() → PIIMiddleware (PII 감지만, 마스킹 안함 - 경고 로그)
처리: graph.ainvoke()
출력: MiddlewareChain.process_output() → PIIMiddleware (답변 + SQL 결과 PII 마스킹)
```

- **process_input**: PII 감지 시 경고 로그만 남기고 원본 전달 (사용자 의도 보존)
- **process_output**: answer 텍스트 + sql_result 행의 PII를 마스킹 후 반환

### 1.6 주요 메서드 (InsightAgentGraph)

| 메서드 | 역할 |
|--------|------|
| `ainvoke(inputs)` | 비동기 그래프 실행 |
| `astream_events(inputs)` | SSE 스트리밍 (LangSmith 추적 포함) |
| `_extract_final_answer(result)` | AIMessage 역순 검색으로 최종 답변 추출 |
| `_extract_steps(result)` | 현재 턴의 tool_calls만 추출 (마지막 HumanMessage 이후) |
| `_extract_sql_result(content)` | ToolMessage JSON → AgentSQLResult 파싱 |

---

## 2. NL2SQL (멀티턴 + 의도분석)

### 2.1 개요

자연어를 SQL로 변환하여 비즈니스 DB를 조회한다. 멀티턴 대화를 지원하여 이전 질문/결과를 참조하고, 의도 분석으로 SQL이 불필요한 질문은 이력에서 바로 답변한다.

- **파일**: `app/graphs/nl2sql/graph.py` (NL2SQLGraph)
- **멀티턴**: BoundedInMemorySaver 체크포인팅 + conversation_history (TTL 24h, max 1000세션)
- **스트리밍**: SSE (forward-only 4스테이지)

### 2.2 그래프 흐름

```
[Stage 1: Intent]
load_history → intent_rewrite → should_route_after_intent
                                 │
                ┌────────────────┴──────────────────┐
                ▼                                    ▼
           [sql_needed]                        [sql_not_needed]
                │                                    │
[Stage 2: Schema]                          answer_from_history
    schema_retrieval                               ↓
        ↓                                    save_history → END
    should_continue_after_schema (★ NEW)
        ├─ relevant   → fewshot_retrieval ←───── prepare_retry
        │                    ↓                        ↑
        │              [Stage 3: Generate]            │
        │                  prompt_build               │
        │                      ↓                      │
        │                  sql_generate               │
        │                      ↓                      │
        │                  validate_sql               │
        │                      ↓                      │
        │                  should_execute              │
        │                      ├─ execute → execute_sql → should_continue_after_execute
        │                      │                           ├─ answer → [Stage 4]
        │                      │                           ├─ retry  → prepare_retry
        │                      │                           └─ error  → handle_error → END
        │                      ├─ retry  → prepare_retry
        │                      └─ error  → handle_error → END
        │
        └─ irrelevant → handle_error → END  ★ DB 무관 질문 차단

[Stage 4: Answer]
    pii_filter → generate_answer → save_history → END
```

### 2.3 주요 노드

**Stage 1 - 의도 분석 (Intent)**

| 노드 | 역할 |
|------|------|
| load_history | 체크포인트에서 대화 이력 로드, current_turn 증가, max_turns 초과 시 FIFO 삭제 |
| intent_rewrite | 의도 분석 (sql_needed/sql_not_needed) + 멀티턴 문맥 반영 질문 리라이트 |

**Stage 2 - 스키마 (Schema)**

| 노드 | 역할 |
|------|------|
| schema_retrieval | 경량 LLM(gpt-4.1-nano)으로 관련 테이블 선택 + DB 관련성 판단(`db_relevant`), FK 테이블 자동 포함, confidence < 0.7이면 전체 스키마 폴백, `db_relevant=false`이면 즉시 차단 |
| fewshot_retrieval | 벡터 검색으로 유사 SQL 예제 조회 (usage_type=rag_action, enhanced 모드: top_k × 2) |

**Stage 3 - SQL 생성 (Generate)**

| 노드 | 역할 |
|------|------|
| prompt_build | 기본 프롬프트 + 스키마 + Few-shot + 대화이력 + 에러 컨텍스트 조합 |
| sql_generate | LLM(temperature=0)으로 SQL 생성 |
| validate_sql | 보안 검증 (키워드 블랙리스트, 테이블 화이트리스트, SELECT 전용) |
| execute_sql | SQL 실행 (30초 타임아웃, 행 수 제한) |
| prepare_retry | 재시도 준비 (retry_count 증가, enhanced_fewshot=True) |

**Stage 4 - 답변 (Answer)**

| 노드 | 역할 |
|------|------|
| pii_filter | SQL 결과의 PII 마스킹 (LLM 전송 전) |
| generate_answer | 결과를 자연어로 변환 (temperature=0.1) |
| save_history | 세션 메모리에 Q&A 저장 (질문, SQL, 답변, sql_result_summary) |

**기타**

| 노드 | 역할 |
|------|------|
| answer_from_history | SQL 불필요 시 이전 sql_result_summary 기반 답변 |
| handle_error | 에러 처리 및 사용자 메시지 반환 (`db_relevant=false`이면 안내 메시지, 그 외는 SQL 오류 메시지) |

### 2.4 조건부 라우팅

| 함수 | 분기 조건 |
|------|----------|
| should_route_after_intent | query_type → "sql_needed" / "sql_not_needed" |
| should_continue_after_schema | db_relevant=true → "relevant" (fewshot으로 진행), db_relevant=false → "irrelevant" (handle_error로 차단) |
| should_execute | validated=True → "execute", 재시도 가능 → "retry", 그 외 → "error" |
| should_continue_after_execute | 실행 성공 → "answer", 재시도 가능 → "retry", 그 외 → "error" |

### 2.5 상태 (NL2SQLState) 핵심 필드

| 카테고리 | 필드 |
|----------|------|
| 기본 | question, generated_sql, validated, validation_error, sql_result, answer, request_id |
| 스키마 | selected_tables, schema_retrieval_confidence, schema_description, **db_relevant** |
| Few-shot | fewshot_context, fewshot_examples, fewshot_count |
| 프롬프트 | sql_prompt, user_prompt, prompt_metadata |
| 재시도 | retry_count (max 2), max_retries, previous_sql, previous_error, enhanced_fewshot |
| 멀티턴 | session_id, conversation_history, current_turn, max_turns (5), history_truncated |
| 의도 | query_type, rewritten_question, intent_reasoning, sql_result_summary |
| 테넌트 | tenant_id |
| 제어 | skip_answer (답변 생성 건너뛰기 플래그) |

### 2.6 SQL 보안

1. **키워드 블랙리스트**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. **테이블 화이트리스트**: 허용된 테이블만 조회 가능
3. **SELECT 전용**: sqlparse로 구문 분석
4. **타임아웃**: 30초
5. **행 제한**: 어댑터별 자동 추가 (PostgreSQL: LIMIT, Oracle: FETCH FIRST)

### 2.7 재시도 로직

- **재시도 가능 에러**: 테이블/컬럼 미발견, 구문 오류, 검증 실패
- **재시도 불가 에러**: 권한, 타임아웃, 연결 오류
- **최대 재시도**: 2회 (설정 가능)
- **Enhanced Few-shot**: 재시도 시 top_k × 2배로 더 많은 예제 검색

### 2.8 세션 관리 메서드 (NL2SQLGraph)

| 메서드 | 역할 |
|--------|------|
| `get_sessions()` | 활성 nl2sql-* 세션 목록 반환 |
| `get_session_history(session_id)` | 체크포인트에서 conversation_history 반환 |
| `delete_session(session_id)` | _evict_thread()로 세션 삭제 |

---

## 3. RAG (문서 검색)

### 3.1 개요

하이브리드 검색(벡터 유사도 + 키워드 매칭)으로 관련 문서를 찾아 LLM이 답변을 생성한다.

- **파일**: `app/graphs/rag/graph.py` (RAGGraph)
- **멀티턴**: 없음 (단발 질의, 체크포인터 없음)
- **검색 방식**: 하이브리드 (pgvector 시맨틱 + pg_trgm 키워드 + RRF 융합)

### 3.2 그래프 흐름

```
query_analysis → retrieve_documents → rerank_documents → generate_answer → END
```

| 노드 | 역할 |
|------|------|
| query_analysis | 문서 ID 패턴(HR-001, #1234) 감지 → direct_lookup 모드 설정, 키워드 추출 |
| retrieve_documents | 하이브리드 검색 (vector + keyword + RRF Reciprocal Rank Fusion) |
| rerank_documents | 재순위 (현재 passthrough, 향후 CrossEncoder/LLM 리랭킹 확장 예정) |
| generate_answer | 검색된 문서 컨텍스트로 LLM 답변 생성 |

### 3.3 상태 (RAGState)

```python
class RAGState(TypedDict):
    question: str
    filters: dict               # tenant_id, doc_type 등
    top_k: int                  # 검색 문서 수
    retrieved_docs: list        # 문서 + 유사도 점수
    answer: str
    metadata: dict
    request_id: str
    tenant_id: Optional[str]
    # 하이브리드 검색 필드
    vector_query: str           # 시맨틱 검색용 쿼리
    keyword_query: str          # 키워드 검색용 쿼리
    search_type: str            # "normal" | "direct_lookup"
    doc_pattern: str            # 문서 ID 패턴 (direct_lookup 시)
```

### 3.4 하이브리드 검색 상세

- **파일**: `app/core/vector/hybrid_search.py`
- **벡터 검색**: pgvector 코사인 유사도 (OpenAI text-embedding-3-small)
- **키워드 검색**: PostgreSQL pg_trgm 유사도
- **융합**: RRF (Reciprocal Rank Fusion) - 두 검색 결과의 순위를 결합
- **키워드 추출**: `app/core/vector/keyword_extractor.py`
- **Direct Lookup**: 문서 ID 패턴 감지 시 ID 기반 직접 조회

---

## 4. SSE 스트리밍

Agent와 NL2SQL은 실시간 진행 상황을 SSE로 전송한다.

```
Client ← SSE ← Backend
         event: node_start    → {"stage": "INTENT", "label": "의도 분석 중..."}
         event: node_complete → {"stage": "INTENT", "label": "의도 분석 완료"}
         event: complete      → {"answer": "...", "sql": "...", "result": {...}}
         event: error         → {"code": "SQL_FAILED", "message": "..."}
```

- **포맷**: `app/core/sse/stream_manager.py` - `format_sse()`, `get_node_stage()`, `get_stage_label()`
- **NL2SQL 스테이지**: Stage 1(Intent) → Stage 2(Schema) → Stage 3(Generate) → Stage 4(Answer)
- **Agent 스테이지**: Stage 1(Think) → Stage 2(Action) → Stage 3(Observe) → Stage 4(Finish)
- NL2SQL/Agent 모두 **forward-only** (재시도 시 스테이지 역행하지 않음)

---

## 5. LLM 설정

### 5.1 통합 인터페이스

```python
from app.core.llm.llm_config import LLMConfigManager
llm = LLMConfigManager.create_llm(temperature=0.0)
```

- DB 설정(tb_app_settings) → 환경변수 → 기본값 순으로 로드
- 프로바이더: OpenAI, Anthropic, Google Gemini (`init_chat_model` 사용)

### 5.2 Temperature 가이드

| 용도 | Temperature | 이유 |
|------|------------|------|
| SQL 생성 | 0 | 정확한 구문 필요 |
| Agent 추론 | 0.0~0.1 | 일관된 도구 선택 |
| 답변 생성 | 0.1 | 약간의 자연스러움 |
| 스키마 리트리벌 | 0 | 정확한 테이블 선택 |

---

## 6. PII 보호

| 적용 지점 | 파일 | 방식 |
|----------|------|------|
| Agent 입력 | `graphs/agent/middleware/pii.py` | 감지만 (경고 로그), 마스킹 안함 (사용자 의도 보존) |
| Agent 출력 | `graphs/agent/middleware/pii.py` | 답변 텍스트 + SQL 결과 행 PII 마스킹 |
| NL2SQL 결과 | `graphs/nl2sql/nodes.py` (pii_filter_node) | SQL 결과 PII를 LLM 전송 전 마스킹 |
| SQL Tool | `graphs/agent/tools/sql_tool.py` | 쿼리 결과에 pii_service 적용 |
| Core 서비스 | `core/pii/pii_service.py` | 이름, 이메일, 전화번호, 주민번호 등 감지+마스킹 |

---

## 7. 세션 관리 (BoundedInMemorySaver)

Agent와 NL2SQL 모두 `BoundedInMemorySaver`를 사용하여 메모리 누수를 방지한다.

- **파일**: `app/core/checkpoint.py`
- **TTL**: 24시간 (86400초)
- **최대 세션**: 1000개
- **정리 주기**: 5분마다 만료/LRU 세션 퇴거
- **Thread-safe**: threading.Lock() 기반
- **세션 삭제**: `_evict_thread(thread_id)` - storage + writes + blobs + _last_access 일괄 정리
- **통계**: `get_stats()` → active, expired, max 카운트
