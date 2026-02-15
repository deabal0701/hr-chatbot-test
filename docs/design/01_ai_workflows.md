# AI 워크플로우 설계

> 최종 수정: 2026-02-15

LangGraph 기반 3개의 독립적인 AI 워크플로우를 운영한다.

---

## 1. AI Agent (ReAct 패턴)

### 1.1 개요

사용자 질문에 대해 LLM이 **자율적으로 도구를 선택**하여 반복 추론(Think→Action→Observe)하는 패턴.
복합 질문("2024년 입사자 수는 몇 명이고 재택근무 정책은?")을 SQL 도구 + RAG 도구 조합으로 처리한다.

- **파일**: `app/graphs/agent/graph.py` (InsightAgentGraph)
- **멀티턴**: InMemorySaver 체크포인팅 (세션 기반)
- **스트리밍**: SSE (`astream_events`)

### 1.2 그래프 흐름

```
START → agent_node → should_continue()
                      ├─ "tools"  → tools_node → agent_node (반복)
                      └─ "answer" → answer_node → END
```

- **agent_node**: LLM이 질문을 분석하고 도구 호출 또는 최종 답변 결정
- **should_continue()**: `iteration_count < max_iterations` 이내에서 도구/답변 분기
- **tools_node**: 선택된 도구 실행 (SQL, RAG, Calculator)
- **answer_node**: 수집된 결과를 종합하여 자연어 답변 생성

### 1.3 상태 (AgentState)

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 누적
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
    start_time: float
```

### 1.4 도구 (Tools)

| 도구 | 파일 | 기능 |
|------|------|------|
| SQLQueryTool | `tools/sql_tool.py` | 자연어 → SQL 생성 → 실행 → 결과 반환 |
| DocumentSearchTool | `tools/rag_tool.py` | pgvector 벡터 검색 → 관련 문서 반환 |
| CalculatorTool | `tools/calc_tool.py` | 안전한 수식 계산 (AST 기반) |

도구는 `BaseTool` ABC를 상속하며, LangChain `@tool` 데코레이터로 래핑하여 Agent에 제공한다.

### 1.5 미들웨어

```
입력: MiddlewareChain.process_input() → PIIMiddleware (PII 마스킹)
처리: graph.ainvoke()
출력: MiddlewareChain.process_output() → PIIMiddleware (PII 마스킹)
```

---

## 2. NL2SQL (멀티턴 + 의도분석)

### 2.1 개요

자연어를 SQL로 변환하여 비즈니스 DB를 조회한다. 멀티턴 대화를 지원하여 이전 질문/결과를 참조하고, 의도 분석으로 SQL이 불필요한 질문은 이력에서 바로 답변한다.

- **파일**: `app/graphs/nl2sql/graph.py` (NL2SQLGraph)
- **멀티턴**: InMemorySaver 체크포인팅 + conversation_history
- **스트리밍**: SSE (forward-only 스테이지)

### 2.2 그래프 흐름

```
load_history → intent_rewrite → should_route_after_intent
                                 │
                ┌────────────────┴──────────────────┐
                ▼                                    ▼
           [sql_needed]                        [sql_not_needed]
                │                                    │
    schema_retrieval                        answer_from_history
        ↓                                           ↓
    fewshot_retrieval ←───── prepare_retry      save_history → END
        ↓                        ↑
    prompt_build                 │
        ↓                        │
    sql_generate                 │
        ↓                        │
    validate_sql                 │
        ↓                        │
    execute_sql → should_continue_after_execute
                   ├─ answer → pii_filter → generate_answer → save_history → END
                   ├─ retry  → prepare_retry (최대 3회)
                   └─ error  → handle_error → END
```

### 2.3 주요 노드 (14개)

| 노드 | 역할 |
|------|------|
| load_history | 세션 이전 대화 로드 |
| intent_rewrite | 의도 분석 + 질문 리라이트 (멀티턴 문맥 반영) |
| schema_retrieval | 관련 테이블 스키마 검색 |
| fewshot_retrieval | 유사 SQL 예제 검색 |
| prompt_build | SQL 생성 프롬프트 조립 |
| sql_generate | LLM으로 SQL 생성 |
| validate_sql | SQL 보안 검증 (블랙리스트, 화이트리스트, SELECT 전용) |
| execute_sql | SQL 실행 (30초 타임아웃, 1000행 제한) |
| pii_filter | SQL 결과의 PII 마스킹 (LLM 전송 전) |
| generate_answer | 결과를 자연어로 변환 |
| save_history | 세션 메모리에 Q&A 저장 |
| answer_from_history | SQL 불필요 시 이력 기반 답변 |
| prepare_retry | 실패 시 enhanced fewshot으로 재시도 준비 |
| handle_error | 에러 처리 |

### 2.4 상태 (NL2SQLState) 핵심 필드

| 카테고리 | 필드 |
|----------|------|
| 기본 | question, generated_sql, validated, sql_result, answer, request_id |
| 스키마 | selected_tables, schema_retrieval_confidence |
| Few-shot | fewshot_context, fewshot_examples, fewshot_count |
| 재시도 | retry_count (max 3), previous_sql, previous_error |
| 멀티턴 | session_id, conversation_history, current_turn, max_turns |
| 의도 | query_type, rewritten_question, intent_reasoning |

### 2.5 SQL 보안

1. **키워드 블랙리스트**: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
2. **테이블 화이트리스트**: 허용된 테이블만 조회 가능
3. **SELECT 전용**: sqlparse로 구문 분석
4. **타임아웃**: 30초
5. **행 제한**: 어댑터별 자동 추가 (PostgreSQL: LIMIT, Oracle: FETCH FIRST)

---

## 3. RAG (문서 검색)

### 3.1 개요

pgvector 벡터 유사도 검색으로 관련 문서를 찾아 LLM이 답변을 생성한다.

- **파일**: `app/graphs/rag/graph.py` (RAGGraph)
- **멀티턴**: 없음 (단발 질의)

### 3.2 그래프 흐름

```
retrieve_documents → generate_answer → END
```

| 노드 | 역할 |
|------|------|
| retrieve_documents | pgvector 코사인 유사도 검색 (top-k, 임계값 필터) |
| generate_answer | 검색된 문서 컨텍스트로 LLM 답변 생성 |

### 3.3 상태 (RAGState)

```python
class RAGState(TypedDict):
    query: str
    filters: dict              # tenant_id, doc_type 등
    retrieved_documents: list   # 문서 + 유사도 점수
    answer: str
    response_time_ms: int
```

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

- **포맷**: `app/core/sse/stream_manager.py` - `format_sse()`, `get_node_stage()`
- **NL2SQL 스테이지**: INIT → INTENT → GENERATE → VALIDATE → EXECUTE → ANSWER → COMPLETE
- **Agent 스테이지**: INIT → THINK → ACTION → OBSERVE → FINISH → COMPLETE
- NL2SQL은 forward-only (재시도 시 스테이지 역행하지 않음)

---

## 5. LLM 설정

### 5.1 통합 인터페이스

```python
from app.core.llm.llm_config import LLMConfigManager
llm = LLMConfigManager.create_llm(temperature=0.0)
```

- DB 설정(tb_app_settings) → 환경변수 → 기본값 순으로 로드
- 프로바이더: OpenAI, Anthropic (init_chat_model 사용)

### 5.2 Temperature 가이드

| 용도 | Temperature | 이유 |
|------|------------|------|
| SQL 생성 | 0 | 정확한 구문 필요 |
| Agent 추론 | 0.0~0.1 | 일관된 도구 선택 |
| 답변 생성 | 0.1 | 약간의 자연스러움 |

---

## 6. PII 보호

| 적용 지점 | 파일 | 방식 |
|----------|------|------|
| Agent 입력/출력 | `graphs/agent/middleware/pii.py` | MiddlewareChain에서 마스킹 |
| NL2SQL 결과 | `graphs/nl2sql/nodes.py` (pii_filter_node) | SQL 결과 PII를 LLM 전송 전 마스킹 |
| Core 서비스 | `core/pii/pii_service.py` | 이름, 이메일, 전화번호, 주민번호 등 감지+마스킹 |
