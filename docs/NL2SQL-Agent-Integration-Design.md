# NL2SQL Agent 통합 설계서

**현재 코드베이스 기반 아키텍처**

버전 1.0 | 2026년 1월

---

## 목차

1. [개요](#1-개요)
2. [현재 아키텍처 분석](#2-현재-아키텍처-분석)
3. [통합 설계](#3-통합-설계)
4. [NL2SQL Agent 그래프 설계](#4-nl2sql-agent-그래프-설계)
5. [RAG 활용 전략](#5-rag-활용-전략)
6. [상태 및 데이터 모델](#6-상태-및-데이터-모델)
7. [API 설계](#7-api-설계)
8. [프로젝트 구조](#8-프로젝트-구조)
9. [구현 가이드](#9-구현-가이드)
10. [2차 개발 계획](#10-2차-개발-계획)

---

## 1. 개요

### 1.1 목적

본 문서는 기존 MUREUM 시스템의 Agent 모드에 NL2SQL-Agent-New.md의 설계 개념을 통합하는 방법을 기술합니다. 기존 RAG, NL2SQL 모드를 유지하면서 새로운 NL2SQL Agent 모드를 추가합니다.

### 1.2 설계 원칙

| 원칙 | 설명 |
|------|------|
| **기존 모드 유지** | RAG, NL2SQL, Agent 모드 모두 그대로 유지 |
| **코드 재사용** | 기존 sql_generator, schema_loader, vector_store 활용 |
| **점진적 확장** | 1차: 핵심 기능, 2차: 캐싱/보안/확장성 |
| **RAG 활용** | 스키마, Few-shot 예제, 비즈니스 용어집 검색에 RAG 적용 |

### 1.3 모드 비교

| 모드 | 용도 | 특징 |
|------|------|------|
| **RAG 모드** | 문서/정책 검색 | 벡터 검색 → LLM 답변 생성 |
| **NL2SQL 모드** | 단순 SQL 변환 | 직선 파이프라인, 빠른 응답 |
| **Agent 모드** | 복합 질문 처리 | ReAct 패턴, 다중 도구 활용 |
| **NL2SQL Agent 모드** (신규) | 고품질 SQL 생성 | 전문 노드, 자가 수정 루프, RAG 활용 |

---

## 2. 현재 아키텍처 분석

### 2.1 현재 모드별 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        현재 MUREUM 아키텍처                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ RAG 모드 (rag_graph.py)                                         │   │
│  │   retrieve → generate_answer → END                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ NL2SQL 모드 (nl2sql_graph.py)                                    │   │
│  │   generate_sql → validate_sql → execute_sql → generate_answer    │   │
│  │                       ↓                                          │   │
│  │                   handle_error → END                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Agent 모드 (agent_graph.py) - ReAct 패턴                         │   │
│  │   agent ←─→ tools (query_database, search_documents, calculate) │   │
│  │     └────────────→ END (tool_calls 없을 때)                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---------|------|------|
| `sql_generator` | `app/core/llm/sql_generator.py` | 자연어 → SQL 변환 |
| `schema_loader` | `app/core/database/schema_loader.py` | DB 스키마 메타데이터 로드 |
| `sql_executor` | `app/core/database/sql_executor.py` | SQL 검증 및 실행 |
| `vector_store` | `app/core/vector/vector_store.py` | 벡터 검색 (RAG) |
| `prompt_service` | `app/core/llm/prompt_service.py` | 프롬프트 템플릿 관리 |
| `LLMConfigManager` | `app/core/llm/llm_config.py` | LLM 인스턴스 생성 |

### 2.3 현재 한계점

1. **NL2SQL 모드**: 자가 수정 루프 없음, 한 번의 시도만 가능
2. **Agent 모드**: SQL 도구가 내부적으로 간단한 SQL 생성만 수행
3. **컨텍스트 부족**: Few-shot 예제나 비즈니스 용어집 활용 없음
4. **스키마 검색**: 전체 스키마를 항상 프롬프트에 포함 (비효율)

---

## 3. 통합 설계

### 3.1 새로운 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     통합 후 MUREUM 아키텍처                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────┐                             │
│  │ 기존 모드 (유지)                       │                             │
│  │  • RAG 모드                           │                             │
│  │  • NL2SQL 모드                        │                             │
│  │  • Agent 모드                         │                             │
│  └───────────────────────────────────────┘                             │
│                         │                                               │
│                         ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ NL2SQL Agent 모드 (신규) - nl2sql_agent_graph.py                  │ │
│  │                                                                   │ │
│  │  ┌──────────┐   ┌──────────────┐   ┌──────────────┐              │ │
│  │  │ 의도분석 │──▶│ 컨텍스트검색 │──▶│  SQL 생성   │              │ │
│  │  │  노드    │   │   (RAG)      │   │    노드     │              │ │
│  │  └──────────┘   └──────────────┘   └──────┬───────┘              │ │
│  │                                           │                       │ │
│  │                      ┌────────────────────┘                       │ │
│  │                      ▼                                            │ │
│  │               ┌──────────────┐                                    │ │
│  │               │  SQL 검증   │◀───────────────────┐               │ │
│  │               │    노드     │                    │               │ │
│  │               └──────┬───────┘                    │               │ │
│  │                      │                            │               │ │
│  │         ┌────────────┼────────────┐              │               │ │
│  │         ▼            ▼            ▼              │               │ │
│  │     [valid]     [regenerate]   [fail]            │               │ │
│  │         │            │            │              │               │ │
│  │         ▼            └────────────┘              │               │ │
│  │  ┌──────────────┐                                │               │ │
│  │  │  SQL 실행   │                    (max 3회)   │               │ │
│  │  │    노드     │────────────────────────────────┘               │ │
│  │  └──────┬───────┘                                                │ │
│  │         │                                                        │ │
│  │         ▼                                                        │ │
│  │  ┌──────────────┐                                                │ │
│  │  │ 결과 해석   │──▶ END                                         │ │
│  │  │    노드     │                                                │ │
│  │  └──────────────┘                                                │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 모드 선택 전략

```python
# 모드 자동 선택 로직 (예시)
def select_mode(question: str, explicit_mode: str = None) -> str:
    """
    질문 분석하여 최적 모드 선택

    Returns:
        "rag" | "nl2sql" | "agent" | "nl2sql_agent"
    """
    if explicit_mode:
        return explicit_mode

    # 정책/규정 관련 → RAG
    if contains_policy_keywords(question):
        return "rag"

    # 복합 질문 (DB + 문서) → Agent
    if is_complex_question(question):
        return "agent"

    # SQL 쿼리 필요 + 고품질 요구 → NL2SQL Agent
    if needs_sql(question) and is_complex_sql(question):
        return "nl2sql_agent"

    # 단순 SQL 쿼리 → NL2SQL
    if needs_sql(question):
        return "nl2sql"

    return "agent"  # 기본값
```

---

## 4. NL2SQL Agent 그래프 설계

### 4.1 그래프 상태 정의

```python
# app/graphs/nl2sql_agent_graph.py

from typing import TypedDict, List, Optional, Annotated, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class NL2SQLAgentState(TypedDict):
    """NL2SQL Agent 상태"""

    # 입력
    user_query: str
    session_id: str
    request_id: str

    # 의도 분석 결과
    intent: str                          # SELECT, AGGREGATE, JOIN, SUBQUERY
    entities: List[Dict[str, Any]]       # 추출된 테이블/컬럼/값
    filters: List[Dict[str, Any]]        # WHERE 조건
    aggregations: List[Dict[str, Any]]   # GROUP BY, ORDER BY 등

    # 컨텍스트 검색 결과 (RAG)
    relevant_schemas: List[Dict[str, Any]]    # 관련 테이블 스키마
    similar_queries: List[Dict[str, Any]]     # 유사 쿼리 예제 (Few-shot)
    business_terms: List[Dict[str, Any]]      # 비즈니스 용어 해석

    # SQL 생성 결과
    generated_sql: str
    sql_dialect: str                     # PostgreSQL, Oracle

    # 검증 결과
    is_valid: bool
    validation_errors: List[str]
    correction_count: int                # 수정 시도 횟수
    max_corrections: int                 # 최대 수정 횟수 (기본값: 3)

    # 실행 결과
    execution_success: bool
    query_results: Optional[List[Dict[str, Any]]]
    columns: List[str]
    row_count: int
    execution_time_ms: int

    # 최종 응답
    natural_response: str
    metadata: Dict[str, Any]
```

### 4.2 그래프 구성

```python
class NL2SQLAgentGraph:
    """NL2SQL Agent 그래프 (6개 노드)"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(NL2SQLAgentState)

        # 노드 추가 (6개)
        workflow.add_node("intent_analysis", self._intent_analysis_node)
        workflow.add_node("context_retrieval", self._context_retrieval_node)
        workflow.add_node("sql_generation", self._sql_generation_node)
        workflow.add_node("sql_validation", self._sql_validation_node)
        workflow.add_node("sql_execution", self._sql_execution_node)
        workflow.add_node("result_interpretation", self._result_interpretation_node)

        # 진입점
        workflow.set_entry_point("intent_analysis")

        # 순차 엣지
        workflow.add_edge("intent_analysis", "context_retrieval")
        workflow.add_edge("context_retrieval", "sql_generation")
        workflow.add_edge("sql_generation", "sql_validation")

        # 조건부 엣지: 검증 결과에 따른 분기
        workflow.add_conditional_edges(
            "sql_validation",
            self._validation_router,
            {
                "execute": "sql_execution",
                "regenerate": "sql_generation",
                "fail": END
            }
        )

        workflow.add_edge("sql_execution", "result_interpretation")
        workflow.add_edge("result_interpretation", END)

        return workflow.compile()

    def _validation_router(self, state: NL2SQLAgentState) -> str:
        """검증 결과에 따른 라우팅"""
        if state["is_valid"]:
            return "execute"

        if state["correction_count"] >= state["max_corrections"]:
            return "fail"

        return "regenerate"
```

### 4.3 각 노드 상세 설계

#### 4.3.1 의도 분석 노드

```python
def _intent_analysis_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    의도 분석 노드

    기능:
    - 의도 분류 (SELECT, AGGREGATE, JOIN, SUBQUERY)
    - 엔티티 추출 (테이블명, 컬럼명, 값)
    - 필터 조건 추출
    - 집계/정렬 조건 추출
    """
    request_id = state["request_id"]
    user_query = state["user_query"]

    log_step(request_id, "NL2SQL-AGENT", "1", "INTENT", "의도 분석 시작")

    # LLM으로 의도 분석
    llm = LLMConfigManager.create_llm(temperature=0)

    system_prompt = prompt_service.get_intent_analysis_prompt()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"질문: {user_query}")
    ]

    response = llm.invoke(messages)
    analysis = parse_intent_response(response.content)

    state["intent"] = analysis["intent"]
    state["entities"] = analysis["entities"]
    state["filters"] = analysis["filters"]
    state["aggregations"] = analysis["aggregations"]

    log_step(request_id, "NL2SQL-AGENT", "1", "INTENT",
             f"의도 분석 완료: {state['intent']}",
             entities_count=len(state['entities']))

    return state
```

#### 4.3.2 컨텍스트 검색 노드 (RAG 활용)

```python
def _context_retrieval_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    컨텍스트 검색 노드 (RAG 활용)

    기능:
    - 관련 테이블 스키마 검색 (schema_index)
    - 유사 쿼리 예제 검색 (query_history_index) - Few-shot
    - 비즈니스 용어 해석 (glossary_index)
    """
    request_id = state["request_id"]
    user_query = state["user_query"]
    entities = state["entities"]

    log_step(request_id, "NL2SQL-AGENT", "2", "CONTEXT", "컨텍스트 검색 시작")

    # 1. 관련 스키마 검색
    schema_docs = vector_store.search_similar_documents(
        query=user_query,
        top_k=5,
        filters=SearchFilters(doc_type="schema")
    )
    state["relevant_schemas"] = [doc.to_dict() for doc in schema_docs]

    # 2. 유사 쿼리 예제 검색 (Few-shot)
    similar_queries = vector_store.search_similar_documents(
        query=user_query,
        top_k=3,
        filters=SearchFilters(doc_type="query_example")
    )
    state["similar_queries"] = [doc.to_dict() for doc in similar_queries]

    # 3. 비즈니스 용어 검색
    # 엔티티에서 추출한 용어로 용어집 검색
    entity_names = [e["name"] for e in entities if e.get("name")]
    if entity_names:
        glossary_docs = vector_store.search_similar_documents(
            query=" ".join(entity_names),
            top_k=3,
            filters=SearchFilters(doc_type="glossary")
        )
        state["business_terms"] = [doc.to_dict() for doc in glossary_docs]
    else:
        state["business_terms"] = []

    log_step(request_id, "NL2SQL-AGENT", "2", "CONTEXT",
             "컨텍스트 검색 완료",
             schemas=len(state["relevant_schemas"]),
             examples=len(state["similar_queries"]),
             terms=len(state["business_terms"]))

    return state
```

#### 4.3.3 SQL 생성 노드

```python
def _sql_generation_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    SQL 생성 노드

    기능:
    - RAG 컨텍스트 활용한 SQL 생성
    - Few-shot 예제 포함
    - 이전 오류 피드백 반영 (재생성 시)
    """
    request_id = state["request_id"]
    user_query = state["user_query"]
    correction_count = state.get("correction_count", 0)

    log_step(request_id, "NL2SQL-AGENT", "3", "GENERATE",
             f"SQL 생성 시작 (시도 #{correction_count + 1})")

    # 컨텍스트 구성
    context = self._build_generation_context(state)

    # 이전 오류가 있으면 피드백 포함
    error_feedback = ""
    if correction_count > 0 and state.get("validation_errors"):
        error_feedback = f"""
이전 생성된 SQL에서 다음 오류가 발생했습니다:
{chr(10).join(state['validation_errors'])}

이 오류를 수정하여 새로운 SQL을 생성해주세요.
"""

    # LLM으로 SQL 생성
    llm = LLMConfigManager.create_llm(temperature=0)

    system_prompt = prompt_service.get_nl2sql_generation_prompt_with_context(
        context["schema"],
        context["examples"],
        context["terms"],
        sql_generator.get_db_type()
    )

    user_prompt = f"""질문: {user_query}

의도: {state['intent']}
필터: {state['filters']}
집계: {state['aggregations']}
{error_feedback}

위 정보를 바탕으로 {sql_generator.get_sql_dialect()} SQL을 생성해주세요.
SQL만 출력하세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    sql = strip_markdown_code_block(response.content, language="sql")

    state["generated_sql"] = sql
    state["sql_dialect"] = sql_generator.get_sql_dialect()
    state["correction_count"] = correction_count + 1

    log_step(request_id, "NL2SQL-AGENT", "3", "GENERATE",
             "SQL 생성 완료", sql_length=len(sql))

    return state

def _build_generation_context(self, state: NL2SQLAgentState) -> Dict[str, str]:
    """SQL 생성용 컨텍스트 구성"""
    # 스키마 정보
    schema_text = ""
    for schema in state.get("relevant_schemas", []):
        schema_text += f"테이블: {schema.get('title', '')}\n{schema.get('content', '')}\n\n"

    # Few-shot 예제
    examples_text = ""
    for i, example in enumerate(state.get("similar_queries", []), 1):
        examples_text += f"""예제 {i}:
질문: {example.get('title', '')}
SQL: {example.get('content', '')}

"""

    # 비즈니스 용어
    terms_text = ""
    for term in state.get("business_terms", []):
        terms_text += f"- {term.get('title', '')}: {term.get('content', '')}\n"

    return {
        "schema": schema_text,
        "examples": examples_text,
        "terms": terms_text
    }
```

#### 4.3.4 SQL 검증 노드

```python
def _sql_validation_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    SQL 검증 노드

    검증 항목:
    1. 구문 검증 (sqlparse)
    2. 스키마 검증 (테이블/컬럼 존재 여부)
    3. 보안 검사 (SQL Injection 패턴)
    4. 쿼리 복잡도 검사
    """
    request_id = state["request_id"]
    sql = state["generated_sql"]

    log_step(request_id, "NL2SQL-AGENT", "4", "VALIDATE", "SQL 검증 시작")

    errors = []

    # 1. 구문 검증
    is_valid_syntax, syntax_error = sql_executor.validate_sql(sql)
    if not is_valid_syntax:
        errors.append(f"구문 오류: {syntax_error}")

    # 2. 스키마 검증 (테이블/컬럼 존재 여부)
    schema_errors = self._validate_schema_references(sql)
    errors.extend(schema_errors)

    # 3. 보안 검사
    security_errors = self._validate_security(sql)
    errors.extend(security_errors)

    # 검증 결과 저장
    state["is_valid"] = len(errors) == 0
    state["validation_errors"] = errors

    if state["is_valid"]:
        log_step(request_id, "NL2SQL-AGENT", "4", "VALIDATE", "SQL 검증 성공")
    else:
        log_step(request_id, "NL2SQL-AGENT", "4", "VALIDATE",
                 f"SQL 검증 실패: {len(errors)}개 오류",
                 errors=errors)

    return state

def _validate_schema_references(self, sql: str) -> List[str]:
    """스키마 참조 검증"""
    errors = []
    # TODO: sqlparse로 테이블/컬럼 추출 후 스키마와 비교
    return errors

def _validate_security(self, sql: str) -> List[str]:
    """보안 검사"""
    errors = []

    # 금지 키워드 검사
    forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
                 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    sql_upper = sql.upper()
    for keyword in forbidden:
        if keyword in sql_upper:
            errors.append(f"금지된 키워드 감지: {keyword}")

    return errors
```

#### 4.3.5 SQL 실행 노드

```python
def _sql_execution_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    SQL 실행 노드

    기능:
    - 검증된 SQL 실행
    - 타임아웃 및 행 제한 적용
    - 결과 저장
    """
    request_id = state["request_id"]
    sql = state["generated_sql"]

    log_step(request_id, "NL2SQL-AGENT", "5", "EXECUTE", "SQL 실행 시작")

    try:
        result = sql_executor.execute_sql(sql, validate=False)

        state["execution_success"] = True
        state["query_results"] = result.rows
        state["columns"] = result.columns
        state["row_count"] = result.row_count
        state["execution_time_ms"] = result.execution_time_ms

        log_step(request_id, "NL2SQL-AGENT", "5", "EXECUTE",
                 "SQL 실행 성공",
                 row_count=result.row_count,
                 execution_time_ms=result.execution_time_ms)

    except Exception as e:
        state["execution_success"] = False
        state["validation_errors"] = [str(e)]
        log_step(request_id, "NL2SQL-AGENT", "5", "EXECUTE",
                 f"SQL 실행 실패: {e}", level="ERROR")

    return state
```

#### 4.3.6 결과 해석 노드

```python
def _result_interpretation_node(self, state: NL2SQLAgentState) -> NL2SQLAgentState:
    """
    결과 해석 노드

    기능:
    - 쿼리 결과를 자연어로 해석
    - 숫자 포맷팅, 통계 요약
    - 차트 추천 (2차 개발)
    """
    request_id = state["request_id"]
    user_query = state["user_query"]
    sql = state["generated_sql"]
    results = state.get("query_results", [])
    columns = state.get("columns", [])
    row_count = state.get("row_count", 0)

    log_step(request_id, "NL2SQL-AGENT", "6", "INTERPRET", "결과 해석 시작")

    if not state.get("execution_success"):
        state["natural_response"] = self._generate_error_response(state)
        return state

    if row_count == 0:
        state["natural_response"] = "조회된 결과가 없습니다."
        return state

    # LLM으로 결과 해석
    llm = LLMConfigManager.create_llm(temperature=0.1)

    system_prompt = prompt_service.get_nl2sql_answer_prompt()

    # 결과 요약 (최대 100개)
    results_sample = results[:100]
    truncated = row_count > 100

    user_prompt = f"""질문: {user_query}

실행된 SQL:
{sql}

조회 결과 ({row_count}개 행{", 상위 100개 표시" if truncated else ""}):
컬럼: {', '.join(columns)}
데이터:
{results_sample}

위 결과를 바탕으로 질문에 대한 답변을 작성해주세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    state["natural_response"] = response.content
    state["metadata"] = {
        "sql": sql,
        "sql_dialect": state["sql_dialect"],
        "row_count": row_count,
        "columns": columns,
        "execution_time_ms": state.get("execution_time_ms", 0),
        "correction_attempts": state.get("correction_count", 1),
        "intent": state.get("intent", "unknown")
    }

    log_step(request_id, "NL2SQL-AGENT", "6", "INTERPRET",
             "결과 해석 완료", answer_length=len(state["natural_response"]))

    return state
```

---

## 5. RAG 활용 전략

### 5.1 인덱스 구조

NL2SQL Agent에서 RAG를 활용하기 위해 3가지 인덱스를 tb_docs에 추가합니다:

| 인덱스 (doc_type) | 내용 | 용도 |
|------------------|------|------|
| `schema` | 테이블 DDL, 컬럼 설명, 관계 정보 | 관련 스키마 검색 |
| `query_example` | 자연어-SQL 쌍 예제 | Few-shot 학습 |
| `glossary` | 비즈니스 용어 정의 | 도메인 용어 해석 |

### 5.2 샘플 INSERT 문

```sql
-- ===================================================================
-- 스키마 정보 (doc_type: 'schema')
-- ===================================================================

-- employee 테이블 스키마
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    'employee 테이블',
    '## employee 테이블 (직원 정보)

### 컬럼
- emp_id: INTEGER (PK) - 직원 고유 ID
- emp_name: VARCHAR(100) NOT NULL - 직원 이름
- emp_no: VARCHAR(20) UNIQUE - 사번
- email: VARCHAR(200) - 이메일 주소
- phone: VARCHAR(20) - 전화번호
- hire_date: DATE NOT NULL - 입사일
- dept_id: INTEGER (FK → department.dept_id) - 소속 부서 ID
- position: VARCHAR(50) - 직급 (사원, 대리, 과장, 차장, 부장, 이사)
- status: VARCHAR(20) DEFAULT ''active'' - 재직상태 (active, inactive, resigned)
- work_type: VARCHAR(20) - 근무유형 (office, remote, hybrid)
- location: VARCHAR(100) - 근무지

### 주요 관계
- department 테이블과 dept_id로 연결
- salary 테이블과 emp_id로 연결
- job_history 테이블과 emp_id로 연결
- performance_review 테이블과 emp_id로 연결

### 예시 쿼리
- 특정 부서 직원 조회: SELECT * FROM employee WHERE dept_id = 1
- 2024년 입사자: SELECT * FROM employee WHERE EXTRACT(YEAR FROM hire_date) = 2024',
    'schema',
    'database',
    ARRAY['employee', '직원', '인사', 'HR'],
    true,
    '{"table_name": "employee", "row_count_estimate": 500}'
);

-- department 테이블 스키마
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    'department 테이블',
    '## department 테이블 (부서 정보)

### 컬럼
- dept_id: INTEGER (PK) - 부서 고유 ID
- dept_name: VARCHAR(100) NOT NULL - 부서명
- dept_code: VARCHAR(20) UNIQUE - 부서 코드
- parent_dept_id: INTEGER (FK → department.dept_id) - 상위 부서 ID
- manager_id: INTEGER (FK → employee.emp_id) - 부서장 직원 ID
- location: VARCHAR(100) - 부서 위치
- created_at: TIMESTAMP - 생성일

### 주요 관계
- employee 테이블과 dept_id로 연결 (1:N)
- 자기 참조로 상위/하위 부서 계층 구조

### 예시 쿼리
- 전체 부서 목록: SELECT * FROM department
- 특정 부서 직원 수: SELECT COUNT(*) FROM employee WHERE dept_id = 1',
    'schema',
    'database',
    ARRAY['department', '부서', '조직', 'organization'],
    true,
    '{"table_name": "department", "row_count_estimate": 20}'
);

-- salary 테이블 스키마
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    'salary 테이블',
    '## salary 테이블 (급여 정보)

### 컬럼
- id: INTEGER (PK) - 급여 기록 ID
- emp_id: INTEGER (FK → employee.emp_id) - 직원 ID
- base_salary: NUMERIC(15,2) - 기본급
- bonus: NUMERIC(15,2) - 상여금
- effective_date: DATE - 적용 시작일
- end_date: DATE - 적용 종료일 (NULL이면 현재 적용 중)
- currency: VARCHAR(3) DEFAULT ''KRW'' - 통화

### 주요 관계
- employee 테이블과 emp_id로 연결

### 현재 급여 조회 패턴
- 현재 급여: WHERE end_date IS NULL 또는 WHERE effective_date <= CURRENT_DATE AND (end_date IS NULL OR end_date > CURRENT_DATE)

### 예시 쿼리
- 직원별 현재 급여: SELECT e.emp_name, s.base_salary FROM employee e JOIN salary s ON e.emp_id = s.emp_id WHERE s.end_date IS NULL
- 평균 급여: SELECT AVG(base_salary) FROM salary WHERE end_date IS NULL',
    'schema',
    'database',
    ARRAY['salary', '급여', '연봉', '보수', 'pay'],
    true,
    '{"table_name": "salary", "row_count_estimate": 1000}'
);

-- ===================================================================
-- Few-shot 쿼리 예제 (doc_type: 'query_example')
-- ===================================================================

-- 기본 집계 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '2024년 입사자 수는 몇 명인가요?',
    'SELECT COUNT(*) as cnt
FROM employee
WHERE EXTRACT(YEAR FROM hire_date) = 2024
  AND status = ''active'';

-- 결과: 27명',
    'query_example',
    'aggregate',
    ARRAY['입사', '연도별', 'COUNT', '집계'],
    true,
    '{"intent": "AGGREGATE", "tables": ["employee"], "complexity": "simple"}'
);

-- 부서별 집계 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '부서별 직원 수를 알려줘',
    'SELECT d.dept_name, COUNT(e.emp_id) as employee_count
FROM department d
LEFT JOIN employee e ON d.dept_id = e.dept_id AND e.status = ''active''
GROUP BY d.dept_id, d.dept_name
ORDER BY employee_count DESC;

-- 결과: 개발팀 45명, 영업팀 32명, 마케팅팀 18명 ...',
    'query_example',
    'aggregate',
    ARRAY['부서별', 'GROUP BY', 'JOIN', '집계'],
    true,
    '{"intent": "AGGREGATE", "tables": ["employee", "department"], "complexity": "medium"}'
);

-- 평균 급여 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '직급별 평균 급여는 얼마인가요?',
    'SELECT e.position,
       AVG(s.base_salary) as avg_salary,
       MIN(s.base_salary) as min_salary,
       MAX(s.base_salary) as max_salary
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
WHERE e.status = ''active''
  AND s.end_date IS NULL
GROUP BY e.position
ORDER BY avg_salary DESC;

-- 결과: 부장 8500만원, 차장 7200만원, 과장 5800만원 ...',
    'query_example',
    'aggregate',
    ARRAY['급여', '평균', '직급별', 'AVG', 'GROUP BY'],
    true,
    '{"intent": "AGGREGATE", "tables": ["employee", "salary"], "complexity": "medium"}'
);

-- 조건부 조회 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '서울 근무 직원 중 재택근무자 목록',
    'SELECT e.emp_name, e.position, d.dept_name, e.work_type
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.location LIKE ''서울%''
  AND e.work_type IN (''remote'', ''hybrid'')
  AND e.status = ''active''
ORDER BY d.dept_name, e.emp_name;

-- 결과: 홍길동 (개발팀, 과장, hybrid) ...',
    'query_example',
    'filter',
    ARRAY['근무지', '재택근무', 'WHERE', 'IN', 'LIKE'],
    true,
    '{"intent": "SELECT", "tables": ["employee", "department"], "complexity": "medium"}'
);

-- 기간 조건 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '최근 3개월 이내 입사한 신입사원',
    'SELECT e.emp_name, e.hire_date, e.position, d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= CURRENT_DATE - INTERVAL ''3 months''
  AND e.status = ''active''
ORDER BY e.hire_date DESC;

-- 결과: 김철수 (2024-11-15, 사원, 개발팀) ...',
    'query_example',
    'filter',
    ARRAY['기간', '최근', 'INTERVAL', '날짜'],
    true,
    '{"intent": "SELECT", "tables": ["employee", "department"], "complexity": "medium"}'
);

-- 복잡한 조인 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '개발팀에서 급여가 가장 높은 5명은 누구인가요?',
    'SELECT e.emp_name, e.position, s.base_salary, d.dept_name
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
JOIN department d ON e.dept_id = d.dept_id
WHERE d.dept_name = ''개발팀''
  AND e.status = ''active''
  AND s.end_date IS NULL
ORDER BY s.base_salary DESC
LIMIT 5;

-- 결과: 박영희 (부장, 9500만원) ...',
    'query_example',
    'ranking',
    ARRAY['급여', '순위', 'ORDER BY', 'LIMIT', 'TOP'],
    true,
    '{"intent": "SELECT", "tables": ["employee", "salary", "department"], "complexity": "complex"}'
);

-- 서브쿼리 예제
INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '평균 급여보다 높은 급여를 받는 직원 수',
    'SELECT COUNT(*) as count
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
WHERE e.status = ''active''
  AND s.end_date IS NULL
  AND s.base_salary > (
      SELECT AVG(base_salary)
      FROM salary
      WHERE end_date IS NULL
  );

-- 결과: 123명',
    'query_example',
    'subquery',
    ARRAY['평균', '비교', '서브쿼리', 'SUBQUERY'],
    true,
    '{"intent": "SUBQUERY", "tables": ["employee", "salary"], "complexity": "complex"}'
);

-- ===================================================================
-- 비즈니스 용어집 (doc_type: 'glossary')
-- ===================================================================

INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '재직자',
    '재직자(active employee)는 현재 회사에 소속되어 근무 중인 직원을 의미합니다.

SQL 조건: employee.status = ''active''

관련 용어: 퇴직자(resigned), 휴직자(inactive)',
    'glossary',
    'hr_terms',
    ARRAY['재직', '재직자', 'active', '현직'],
    true,
    '{"term": "재직자", "sql_condition": "status = ''active''"}'
);

INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '재택근무',
    '재택근무(remote work)는 사무실이 아닌 자택에서 업무를 수행하는 근무 형태입니다.

SQL 조건: employee.work_type = ''remote'' (완전 재택) 또는 work_type = ''hybrid'' (혼합 근무)

관련 용어: 사무실 근무(office), 하이브리드(hybrid)',
    'glossary',
    'hr_terms',
    ARRAY['재택', '원격근무', 'remote', 'WFH', '하이브리드'],
    true,
    '{"term": "재택근무", "sql_condition": "work_type IN (''remote'', ''hybrid'')"}'
);

INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '현재 급여',
    '현재 급여(current salary)는 현재 시점에 적용되고 있는 급여를 의미합니다.

SQL 조건: salary.end_date IS NULL

설명: salary 테이블은 급여 이력을 관리하며, end_date가 NULL인 레코드가 현재 적용 중인 급여입니다.',
    'glossary',
    'hr_terms',
    ARRAY['급여', '현재급여', '연봉', 'current salary'],
    true,
    '{"term": "현재 급여", "sql_condition": "end_date IS NULL"}'
);

INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '신입사원',
    '신입사원(new employee)은 일반적으로 입사한지 1년 이내인 직원을 의미합니다.

SQL 조건: employee.hire_date >= CURRENT_DATE - INTERVAL ''1 year''

회사 정책에 따라 6개월, 3개월 등 다른 기준을 적용할 수 있습니다.',
    'glossary',
    'hr_terms',
    ARRAY['신입', '신입사원', '새직원', 'new hire'],
    true,
    '{"term": "신입사원", "sql_condition": "hire_date >= CURRENT_DATE - INTERVAL ''1 year''"}'
);

INSERT INTO tb_docs (title, content, doc_type, category, tags, indexed, metadata) VALUES
(
    '직급',
    '직급(position)은 조직 내에서의 계층적 위치를 나타냅니다.

직급 체계 (낮은 순):
- 사원 (Staff)
- 대리 (Assistant Manager)
- 과장 (Manager)
- 차장 (Deputy General Manager)
- 부장 (General Manager)
- 이사 (Director)

SQL 예시: employee.position = ''과장''',
    'glossary',
    'hr_terms',
    ARRAY['직급', '직위', 'position', 'rank', '사원', '대리', '과장', '차장', '부장'],
    true,
    '{"term": "직급", "values": ["사원", "대리", "과장", "차장", "부장", "이사"]}'
);
```

### 5.3 임베딩 실행

```bash
# 새로 추가한 문서 임베딩
python scripts/embed_documents.py

# 또는 특정 타입만
python scripts/embed_documents.py --doc-type schema
python scripts/embed_documents.py --doc-type query_example
python scripts/embed_documents.py --doc-type glossary
```

---

## 6. 상태 및 데이터 모델

### 6.1 요청/응답 모델

```python
# app/models/nl2sql_agent.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NL2SQLAgentRequest(BaseModel):
    """NL2SQL Agent 요청"""
    query: str = Field(..., min_length=1, max_length=2000, description="자연어 질문")
    session_id: Optional[str] = Field(None, description="세션 ID")
    max_corrections: int = Field(default=3, ge=1, le=5, description="최대 수정 시도 횟수")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "2024년 입사한 개발팀 직원 중 평균 급여보다 높은 사람은?",
                "session_id": None,
                "max_corrections": 3
            }
        }


class IntentAnalysis(BaseModel):
    """의도 분석 결과"""
    intent: str = Field(..., description="의도 유형 (SELECT, AGGREGATE, JOIN, SUBQUERY)")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="추출된 엔티티")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="필터 조건")
    aggregations: List[Dict[str, Any]] = Field(default_factory=list, description="집계 조건")
    confidence: float = Field(default=1.0, description="분석 신뢰도")


class SQLGenerationResult(BaseModel):
    """SQL 생성 결과"""
    sql: str = Field(..., description="생성된 SQL")
    dialect: str = Field(..., description="SQL 방언")
    correction_count: int = Field(default=0, description="수정 시도 횟수")
    context_used: Dict[str, int] = Field(default_factory=dict, description="사용된 컨텍스트 정보")


class SQLExecutionResult(BaseModel):
    """SQL 실행 결과"""
    columns: List[str] = Field(default_factory=list, description="컬럼명")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="결과 행")
    row_count: int = Field(default=0, description="총 행 수")
    execution_time_ms: int = Field(default=0, description="실행 시간(ms)")


class NL2SQLAgentResponse(BaseModel):
    """NL2SQL Agent 응답"""
    success: bool = Field(..., description="성공 여부")
    answer: str = Field(..., description="자연어 답변")

    # 상세 정보
    intent_analysis: Optional[IntentAnalysis] = Field(None, description="의도 분석 결과")
    sql_result: Optional[SQLGenerationResult] = Field(None, description="SQL 생성 결과")
    execution_result: Optional[SQLExecutionResult] = Field(None, description="실행 결과")

    # 메타데이터
    session_id: Optional[str] = Field(None, description="세션 ID")
    request_id: str = Field(..., description="요청 ID")
    response_time_ms: int = Field(default=0, description="전체 응답 시간(ms)")

    # 오류 정보
    error: Optional[str] = Field(None, description="오류 메시지")
    validation_errors: List[str] = Field(default_factory=list, description="검증 오류 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "2024년 입사한 개발팀 직원 중 평균 급여보다 높은 사람은 총 5명입니다...",
                "intent_analysis": {
                    "intent": "SUBQUERY",
                    "entities": [{"name": "employee", "type": "TABLE"}],
                    "filters": [{"column": "hire_date", "operator": ">=", "value": "2024-01-01"}],
                    "aggregations": [],
                    "confidence": 0.95
                },
                "sql_result": {
                    "sql": "SELECT e.emp_name, s.base_salary FROM ...",
                    "dialect": "PostgreSQL",
                    "correction_count": 0,
                    "context_used": {"schemas": 2, "examples": 1, "terms": 1}
                },
                "execution_result": {
                    "columns": ["emp_name", "base_salary"],
                    "rows": [{"emp_name": "홍길동", "base_salary": 6500}],
                    "row_count": 5,
                    "execution_time_ms": 45
                },
                "session_id": "session-abc123",
                "request_id": "req-xyz789",
                "response_time_ms": 1250
            }
        }
```

---

## 7. API 설계

### 7.1 엔드포인트

```python
# app/api/routes/nl2sql_agent.py

from fastapi import APIRouter, Depends, HTTPException
from app.models.nl2sql_agent import NL2SQLAgentRequest, NL2SQLAgentResponse
from app.api.services.nl2sql_agent_service import nl2sql_agent_service

router = APIRouter(prefix="/api/v1/nl2sql-agent", tags=["NL2SQL Agent"])


@router.post("/search", response_model=NL2SQLAgentResponse)
async def search(request: NL2SQLAgentRequest) -> NL2SQLAgentResponse:
    """
    NL2SQL Agent 검색

    고품질 SQL 생성을 위한 전문 에이전트 파이프라인:
    1. 의도 분석
    2. 컨텍스트 검색 (RAG)
    3. SQL 생성 (Few-shot)
    4. SQL 검증 및 자가 수정
    5. 실행
    6. 결과 해석
    """
    return await nl2sql_agent_service.search(request)


@router.get("/schema/refresh")
async def refresh_schema_cache():
    """스키마 캐시 갱신"""
    from app.core.llm.sql_generator import sql_generator
    sql_generator.refresh_schema_cache()
    return {"message": "Schema cache refreshed"}
```

### 7.2 기존 검색 API 통합

```python
# app/api/routes/search.py 수정

@router.post("/unified", response_model=UnifiedSearchResponse)
async def unified_search(request: UnifiedSearchRequest) -> UnifiedSearchResponse:
    """
    통합 검색 API

    mode 파라미터에 따라 적절한 검색 모드 실행:
    - "rag": 문서 검색
    - "nl2sql": 단순 SQL 변환
    - "agent": 복합 질문 처리
    - "nl2sql_agent": 고품질 SQL 생성 (신규)
    - "auto": 자동 모드 선택 (기본값)
    """
    mode = request.mode or "auto"

    if mode == "auto":
        mode = select_mode(request.query)

    if mode == "rag":
        return await rag_service.search(request)
    elif mode == "nl2sql":
        return await nl2sql_service.search(request)
    elif mode == "agent":
        return await agent_service.search(request)
    elif mode == "nl2sql_agent":
        return await nl2sql_agent_service.search(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode}")
```

---

## 8. 프로젝트 구조

### 8.1 신규 파일 구조

```
app/
├── main.py                           # FastAPI app (기존)
├── config.py                         # 설정 (기존)
├── api/
│   ├── routes/
│   │   ├── agent.py                  # Agent 엔드포인트 (기존)
│   │   ├── search.py                 # 검색 엔드포인트 (기존, 수정)
│   │   └── nl2sql_agent.py           # 🆕 NL2SQL Agent 엔드포인트
│   └── services/
│       ├── agent_service.py          # Agent 서비스 (기존)
│       └── nl2sql_agent_service.py   # 🆕 NL2SQL Agent 서비스
├── graphs/
│   ├── agent_graph.py                # ReAct Agent (기존)
│   ├── rag_graph.py                  # RAG 그래프 (기존)
│   ├── nl2sql_graph.py               # NL2SQL 그래프 (기존)
│   └── nl2sql_agent_graph.py         # 🆕 NL2SQL Agent 그래프
├── models/
│   ├── agent.py                      # Agent 모델 (기존)
│   ├── rag.py                        # RAG 모델 (기존)
│   ├── search.py                     # 검색 모델 (기존)
│   └── nl2sql_agent.py               # 🆕 NL2SQL Agent 모델
├── tools/                            # 기존 도구들 유지
│   ├── sql_tool.py
│   ├── rag_tool.py
│   └── calc_tool.py
├── core/
│   ├── llm/
│   │   ├── llm_config.py             # LLM 설정 (기존)
│   │   ├── prompt_service.py         # 프롬프트 (기존, 확장)
│   │   └── sql_generator.py          # SQL 생성 (기존)
│   ├── database/
│   │   ├── schema_loader.py          # 스키마 로더 (기존)
│   │   ├── sql_executor.py           # SQL 실행 (기존)
│   │   └── external.py               # 외부 DB (기존)
│   └── vector/
│       └── vector_store.py           # 벡터 스토어 (기존)
└── utils/
    ├── logger.py                     # 로깅 (기존)
    └── intent_parser.py              # 🆕 의도 분석 유틸리티
```

### 8.2 신규 파일 요약

| 파일 | 역할 |
|------|------|
| `app/graphs/nl2sql_agent_graph.py` | NL2SQL Agent 그래프 (6개 노드) |
| `app/api/routes/nl2sql_agent.py` | API 엔드포인트 |
| `app/api/services/nl2sql_agent_service.py` | 비즈니스 로직 |
| `app/models/nl2sql_agent.py` | 요청/응답 모델 |
| `app/utils/intent_parser.py` | 의도 분석 파싱 유틸리티 |

---

## 9. 구현 가이드

### 9.1 1차 개발 범위

| 구성요소 | 내용 | 우선순위 |
|---------|------|---------|
| NL2SQL Agent 그래프 | 6개 노드 기본 구현 | 🔴 필수 |
| RAG 인덱스 | schema, query_example, glossary 데이터 | 🔴 필수 |
| API 엔드포인트 | /api/v1/nl2sql-agent/search | 🔴 필수 |
| 자가 수정 루프 | 최대 3회 재시도 | 🔴 필수 |
| 프롬프트 템플릿 | 의도분석, SQL생성, 결과해석 | 🔴 필수 |

### 9.2 구현 순서

1. **모델 정의** (`app/models/nl2sql_agent.py`)
2. **그래프 구현** (`app/graphs/nl2sql_agent_graph.py`)
3. **서비스 구현** (`app/api/services/nl2sql_agent_service.py`)
4. **API 라우트** (`app/api/routes/nl2sql_agent.py`)
5. **프롬프트 확장** (`app/core/llm/prompt_service.py`)
6. **RAG 데이터 INSERT** (스키마, 예제, 용어집)
7. **통합 테스트**

### 9.3 프롬프트 확장 예시

```python
# app/core/llm/prompt_service.py 확장

def get_intent_analysis_prompt(self) -> str:
    """의도 분석 프롬프트"""
    return self._get_prompt_from_db("intent_analysis_system", default="""
당신은 자연어 질문을 분석하여 SQL 쿼리 생성에 필요한 정보를 추출하는 전문가입니다.

주어진 질문을 분석하여 다음 JSON 형식으로 응답하세요:

{
    "intent": "SELECT | AGGREGATE | JOIN | SUBQUERY",
    "entities": [
        {"name": "테이블/컬럼명", "type": "TABLE | COLUMN | VALUE", "confidence": 0.9}
    ],
    "filters": [
        {"column": "컬럼명", "operator": "= | > | < | LIKE | IN | BETWEEN", "value": "값"}
    ],
    "aggregations": [
        {"function": "COUNT | SUM | AVG | MIN | MAX", "column": "컬럼명", "group_by": ["컬럼"]}
    ]
}

의도 분류 기준:
- SELECT: 단순 조회 (필터링, 정렬)
- AGGREGATE: 집계 함수 사용 (COUNT, SUM, AVG 등)
- JOIN: 여러 테이블 연결 필요
- SUBQUERY: 서브쿼리 필요 (평균보다 높은, 최대값 등 비교)
""")


def get_nl2sql_generation_prompt_with_context(
    self,
    schema: str,
    examples: str,
    terms: str,
    db_type: str
) -> str:
    """컨텍스트 기반 SQL 생성 프롬프트"""
    base_prompt = self.get_nl2sql_generation_prompt(schema, db_type)

    context_section = ""

    if examples:
        context_section += f"""
## 유사 쿼리 예제 (Few-shot)
다음은 유사한 질문에 대한 SQL 예제입니다. 참고하세요:

{examples}
"""

    if terms:
        context_section += f"""
## 비즈니스 용어집
다음 용어의 의미를 참고하세요:

{terms}
"""

    return base_prompt + context_section
```

---

## 10. 2차 개발 계획

### 10.1 캐싱 전략 (2차)

| 캐시 유형 | 저장소 | TTL | 용도 |
|----------|-------|-----|------|
| 스키마 캐시 | 메모리/Redis | 1시간 | 스키마 메타데이터 |
| 쿼리 결과 캐시 | Redis | 5분 | 동일 SQL 결과 |
| 임베딩 캐시 | Redis | 24시간 | RAG 검색 결과 |
| 세션 상태 | Redis | 30분 | 멀티턴 대화 |

### 10.2 보안 강화 (2차)

| 항목 | 현재 | 2차 목표 |
|------|------|---------|
| SQL Injection | 기본 키워드 차단 | AST 기반 검증 |
| 테이블 접근 제어 | allowed_tables | 사용자별 RBAC |
| 쿼리 복잡도 제한 | 없음 | 조인 깊이, 서브쿼리 중첩 제한 |
| 감사 로깅 | 기본 로그 | 전용 감사 테이블 |

### 10.3 확장성 (2차)

| 항목 | 현재 | 2차 목표 |
|------|------|---------|
| 스트리밍 응답 | 미지원 | SSE 지원 |
| 체크포인팅 | InMemorySaver | PostgresSaver |
| 차트 추천 | 미지원 | 데이터 기반 자동 추천 |
| 하이브리드 검색 | 벡터만 | 벡터 + BM25 |

### 10.4 모니터링 (2차)

```python
# LangSmith 추적
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "mureum-nl2sql-agent"

# Prometheus 메트릭
from prometheus_client import Counter, Histogram

nl2sql_queries_total = Counter(
    'nl2sql_agent_queries_total',
    'Total NL2SQL Agent queries',
    ['status', 'intent']
)

nl2sql_latency = Histogram(
    'nl2sql_agent_latency_seconds',
    'NL2SQL Agent latency',
    buckets=[0.5, 1, 2, 3, 5, 10]
)
```

---

## 부록 A: 응답 형식 비교

### 기존 Agent vs 새 NL2SQL Agent

| 항목 | 기존 Agent | NL2SQL Agent |
|------|-----------|--------------|
| 응답 형식 | AgentResponse | NL2SQLAgentResponse |
| 실행 단계 | steps (도구 호출 기록) | intent_analysis, sql_result, execution_result |
| SQL 정보 | steps[].sql_result | sql_result.sql, sql_result.dialect |
| 재시도 정보 | 없음 | sql_result.correction_count |
| 컨텍스트 정보 | 없음 | sql_result.context_used |

### 장점 취합

- **기존 Agent 장점**: steps 기록으로 추론 과정 투명성
- **새 설계 장점**: 구조화된 결과, 재시도 정보, 컨텍스트 활용 정보

---

*— 문서 끝 —*
