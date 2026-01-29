# Cortex Agent 설계서

**기존 Agent를 대체하는 통합 지능형 SQL 에이전트**

버전 2.1 | 2026년 1월

---

## 목차

1. [개요](#1-개요)
2. [아키텍처 설계](#2-아키텍처-설계)
3. [Cortex 그래프 상세 설계](#3-cortex-그래프-상세-설계)
4. [노드별 상세 설계](#4-노드별-상세-설계)
5. [Human in the Loop](#5-human-in-the-loop)
6. [에러 복구 전략](#6-에러-복구-전략)
7. [Cortex 전용 RAG 구조](#7-cortex-전용-rag-구조)
8. [상태 및 데이터 모델](#8-상태-및-데이터-모델)
9. [API 설계](#9-api-설계)
10. [프로젝트 구조](#10-프로젝트-구조)
11. [구현 가이드](#11-구현-가이드)
12. [2차 개발 계획](#12-2차-개발-계획)

---

## 1. 개요

### 1.1 목적

Cortex는 기존 Agent 모드를 대체하는 **SQL 특화 지능형 에이전트**입니다.
- RAG를 활용한 고품질 SQL 생성
- 자가 수정 루프
- Human in the Loop (사람 개입)
- 유연한 에러 복구

### 1.2 핵심 특징

| 특징 | 설명 |
|------|------|
| **SQL 특화** | 자연어 → 고품질 SQL 변환에 집중 |
| **RAG 활용** | 스키마, Few-shot 예제, 용어집으로 SQL 품질 향상 |
| **자가 수정** | 검증/실행 실패 시 자동 재시도 (최대 3회) |
| **Human in the Loop** | 모호성 해결, 승인 요청, 에스컬레이션 |
| **유연한 복구** | 에러 유형별 다른 복구 경로 |

### 1.3 모드 구성 (변경 후)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MUREUM 모드 구성 (3개)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────┐                             │
│  │ RAG 모드 (유지)                        │                             │
│  │  • 정책/규정/가이드 문서 검색          │                             │
│  │  • SQL 없이 문서 기반 답변             │                             │
│  │  • doc_type: policy, guide, faq 등    │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  ┌───────────────────────────────────────┐                             │
│  │ NL2SQL 모드 (유지)                     │                             │
│  │  • 단순 SQL 변환 (빠른 응답)           │                             │
│  │  • 자가 수정 없음, 1회 시도            │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Cortex 모드 (Agent 대체) ⭐                                        │ │
│  │  • SQL 특화 지능형 에이전트                                       │ │
│  │  • Cortex 전용 RAG (스키마, Few-shot, 용어집)                     │ │
│  │  • 자가 수정 루프 + Human in the Loop                            │ │
│  │  • doc_type: schema, query_example, glossary                      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 아키텍처 설계

### 2.1 Cortex 핵심 플로우

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Cortex Agent Graph v2.1                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                                           │
│  │   의도분석    │                                                           │
│  │   (Intent)   │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐         ┌──────────────────────────────────────────┐     │
│  │ 명확화 필요?  │───YES──▶│  Human: 명확화 요청 (Clarification)      │     │
│  │              │         │  • 모호한 질문 → 사용자에게 선택지 제시   │     │
│  └──────┬───────┘         └──────────────────┬───────────────────────┘     │
│         │ NO                                  │                             │
│         ▼                                     ▼                             │
│  ┌──────────────┐◀────────────────────────────┘                            │
│  │ 컨텍스트검색  │                                                          │
│  │ (SQL용 RAG)  │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                           │
│  │  SQL 생성    │◀─────────────────────────────────────────────┐           │
│  │ (Generate)   │                                               │           │
│  └──────┬───────┘                                               │           │
│         │                                                       │           │
│         ▼                                                       │           │
│  ┌──────────────┐                                               │           │
│  │  SQL 검증    │                                               │           │
│  │ (Validate)   │                                               │           │
│  └──────┬───────┘                                               │           │
│         │                                                       │           │
│    ┌────┴────┬─────────────┬─────────────┐                     │           │
│    ▼         ▼             ▼             ▼                     │           │
│ [valid]  [syntax]     [schema]       [security]                │           │
│    │         │             │             │                     │           │
│    │         │             │             ▼                     │           │
│    │         │             │    ┌──────────────────────┐       │           │
│    │         │             │    │ Human: 보안 승인 요청 │       │           │
│    │         │             │    │ (민감 테이블 접근 등)  │       │           │
│    │         │             │    └──────────┬───────────┘       │           │
│    │         │             │               │                   │           │
│    │         │             └───────────────┼───────────────────┤           │
│    │         │             (컨텍스트 재검색)│                   │           │
│    │         │                             │                   │           │
│    │         └─────────────────────────────┼───────────────────┘           │
│    │         (SQL 재생성)                  │                               │
│    │                                       │                               │
│    ▼                                       ▼                               │
│  ┌──────────────┐              ┌──────────────────────┐                    │
│  │ 승인 필요?   │──YES────────▶│ Human: 실행 전 승인   │                    │
│  │ (대량 조회)  │              │ (대량 데이터, 복잡 쿼리)│                    │
│  └──────┬───────┘              └──────────┬───────────┘                    │
│         │ NO                              │ 승인됨                          │
│         ▼                                 ▼                                │
│  ┌──────────────┐◀────────────────────────┘                               │
│  │  SQL 실행    │                                                          │
│  │  (Execute)   │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│    ┌────┴────┬─────────────┐                                              │
│    ▼         ▼             ▼                                              │
│ [success] [exec_err]   [timeout]                                          │
│    │         │             │                                              │
│    │         │             └──────────────────────────────────────────┐   │
│    │         │             (최적화 힌트와 재생성)                        │   │
│    │         └────────────────────────────────────────────────────────┤   │
│    │         (에러 피드백과 재생성)                                     │   │
│    │                                                                   ▼   │
│    │                                                           SQL 생성으로 │
│    ▼                                                                       │
│  ┌──────────────┐                                                          │
│  │  결과해석    │                                                          │
│  │ (Interpret)  │                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                   │
│         ▼                                                                   │
│       END                                                                   │
│                                                                             │
│  ※ 최대 재시도: 3회                                                        │
│  ※ 재시도 초과 시: Human 에스컬레이션 또는 에러 응답                        │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Human in the Loop 개입 지점

| 개입 지점 | 트리거 조건 | 사용자 액션 |
|----------|------------|------------|
| **명확화 요청** | 모호한 질문 감지 | 선택지 중 선택 |
| **보안 승인** | 민감 테이블 접근 | 승인/거부 |
| **실행 전 승인** | 대량 조회, 복잡 쿼리 | 승인/거부/수정 |
| **에스컬레이션** | 최대 재시도 초과 | 관리자 검토 |

---

## 3. Cortex 그래프 상세 설계

### 3.1 상태 정의

```python
# app/graphs/cortex_graph.py

from typing import TypedDict, List, Optional, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

class HumanInterventionRequest(TypedDict):
    """Human 개입 요청"""
    type: Literal["clarification", "approval", "security", "escalation"]
    message: str
    options: Optional[List[str]]  # 선택지 (clarification용)
    context: Dict[str, Any]       # 추가 컨텍스트


class CortexState(TypedDict):
    """Cortex Agent 상태"""

    # === 입력 ===
    user_query: str
    session_id: str
    request_id: str

    # === 의도 분석 ===
    intent_confidence: float              # 의도 분석 신뢰도
    ambiguity_detected: bool              # 모호성 감지 여부
    ambiguity_options: List[str]          # 명확화 선택지

    # === Human in the Loop ===
    requires_human: bool                  # Human 개입 필요 여부
    human_intervention: Optional[HumanInterventionRequest]
    human_response: Optional[str]         # 사용자 응답
    waiting_for_human: bool               # Human 응답 대기 중

    # === 컨텍스트 (Cortex 전용 RAG) ===
    relevant_schemas: List[Dict[str, Any]]
    similar_queries: List[Dict[str, Any]]
    business_terms: List[Dict[str, Any]]

    # === SQL 생성/검증 ===
    generated_sql: str
    sql_dialect: str
    is_valid: bool
    validation_errors: List[str]
    error_type: Optional[Literal["syntax", "schema", "execution", "timeout", "security"]]
    requires_approval: bool               # 실행 전 승인 필요

    # === 재시도 관리 ===
    correction_count: int
    max_corrections: int
    last_error_feedback: str

    # === 실행 결과 ===
    execution_success: bool
    query_results: Optional[List[Dict[str, Any]]]
    columns: List[str]
    row_count: int
    execution_time_ms: int

    # === 최종 응답 ===
    natural_response: str
    metadata: Dict[str, Any]
```

### 3.2 그래프 구성

```python
class CortexGraph:
    """Cortex Agent 그래프 - Human in the Loop 포함"""

    def __init__(self):
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(CortexState)

        # ===== 노드 추가 =====
        workflow.add_node("intent_analysis", self._intent_analysis_node)
        workflow.add_node("human_clarification", self._human_clarification_node)
        workflow.add_node("context_retrieval", self._context_retrieval_node)
        workflow.add_node("sql_generation", self._sql_generation_node)
        workflow.add_node("sql_validation", self._sql_validation_node)
        workflow.add_node("human_approval", self._human_approval_node)
        workflow.add_node("sql_execution", self._sql_execution_node)
        workflow.add_node("result_interpretation", self._result_interpretation_node)
        workflow.add_node("human_escalation", self._human_escalation_node)
        workflow.add_node("error_response", self._error_response_node)

        # ===== 진입점 =====
        workflow.set_entry_point("intent_analysis")

        # ===== 의도 분석 후 라우팅 =====
        workflow.add_conditional_edges(
            "intent_analysis",
            self._intent_router,
            {
                "need_clarification": "human_clarification",
                "proceed": "context_retrieval"
            }
        )

        # ===== Human 명확화 후 =====
        workflow.add_edge("human_clarification", "context_retrieval")

        # ===== SQL 생성 흐름 =====
        workflow.add_edge("context_retrieval", "sql_generation")
        workflow.add_edge("sql_generation", "sql_validation")

        # ===== 검증 결과 라우팅 =====
        workflow.add_conditional_edges(
            "sql_validation",
            self._validation_router,
            {
                "execute": "sql_execution",
                "need_approval": "human_approval",
                "regenerate_sql": "sql_generation",
                "refetch_context": "context_retrieval",
                "escalate": "human_escalation",
                "fail": "error_response"
            }
        )

        # ===== Human 승인 후 =====
        workflow.add_conditional_edges(
            "human_approval",
            self._approval_router,
            {
                "approved": "sql_execution",
                "rejected": "error_response",
                "modify": "sql_generation"
            }
        )

        # ===== 실행 결과 라우팅 =====
        workflow.add_conditional_edges(
            "sql_execution",
            self._execution_router,
            {
                "success": "result_interpretation",
                "regenerate_sql": "sql_generation",
                "escalate": "human_escalation",
                "fail": "error_response"
            }
        )

        # ===== Human 에스컬레이션 후 =====
        workflow.add_edge("human_escalation", "error_response")

        # ===== 종료 =====
        workflow.add_edge("result_interpretation", END)
        workflow.add_edge("error_response", END)

        return workflow.compile(checkpointer=self.checkpointer)
```

### 3.3 라우터 함수

```python
def _intent_router(self, state: CortexState) -> str:
    """의도 분석 후 라우팅"""
    if state.get("ambiguity_detected") and state.get("ambiguity_options"):
        return "need_clarification"
    return "proceed"


def _validation_router(self, state: CortexState) -> str:
    """검증 결과 라우팅"""
    # 유효한 SQL
    if state["is_valid"]:
        # 승인 필요 여부 체크
        if state.get("requires_approval"):
            return "need_approval"
        return "execute"

    # 최대 재시도 초과 → 에스컬레이션
    if state["correction_count"] >= state["max_corrections"]:
        return "escalate"

    error_type = state.get("error_type")

    # 보안 문제 → 승인 필요
    if error_type == "security":
        return "need_approval"

    # 스키마 오류 → 컨텍스트 재검색
    if error_type == "schema":
        return "refetch_context"

    # 구문 오류 등 → SQL 재생성
    return "regenerate_sql"


def _approval_router(self, state: CortexState) -> str:
    """Human 승인 결과 라우팅"""
    response = state.get("human_response", "").lower()

    if response in ["approved", "yes", "승인", "확인"]:
        return "approved"
    elif response in ["modify", "수정"]:
        return "modify"
    else:
        return "rejected"


def _execution_router(self, state: CortexState) -> str:
    """실행 결과 라우팅"""
    if state["execution_success"]:
        return "success"

    # 최대 재시도 초과 → 에스컬레이션
    if state["correction_count"] >= state["max_corrections"]:
        return "escalate"

    return "regenerate_sql"
```

---

## 4. 노드별 상세 설계

### 4.1 의도 분석 노드

```python
def _intent_analysis_node(self, state: CortexState) -> CortexState:
    """
    의도 분석 + 모호성 감지

    기능:
    1. 질문 분석
    2. 모호성 감지 → Human 명확화 필요 여부 결정
    3. 신뢰도 평가
    """
    request_id = state["request_id"]
    user_query = state["user_query"]

    log_step(request_id, "CORTEX", "1", "INTENT", "의도 분석 시작")

    llm = LLMConfigManager.create_llm(temperature=0)

    system_prompt = """당신은 질문 분석 전문가입니다.
사용자 질문을 분석하여 다음을 JSON으로 응답하세요:

{
    "is_sql_question": true/false,
    "confidence": 0.0~1.0,
    "ambiguous": true/false,
    "ambiguity_reason": "모호한 이유 (있으면)",
    "clarification_options": ["선택지1", "선택지2", ...],
    "extracted_entities": {
        "tables": ["추정 테이블"],
        "columns": ["추정 컬럼"],
        "conditions": ["추정 조건"]
    }
}

모호성 판단 기준:
- 여러 테이블이 해당될 수 있는 경우
- 기간이 명시되지 않은 경우 (예: "최근" → 1주? 1개월?)
- 집계 기준이 불명확한 경우 (예: "많은" → 상위 몇 개?)
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"질문: {user_query}")
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content)

    state["intent_confidence"] = result.get("confidence", 1.0)
    state["ambiguity_detected"] = result.get("ambiguous", False)
    state["ambiguity_options"] = result.get("clarification_options", [])
    state["correction_count"] = 0
    state["max_corrections"] = 3
    state["requires_human"] = state["ambiguity_detected"]

    if state["ambiguity_detected"]:
        log_step(request_id, "CORTEX", "1", "INTENT",
                 "모호성 감지 → Human 명확화 필요",
                 options=state["ambiguity_options"][:3])
    else:
        log_step(request_id, "CORTEX", "1", "INTENT",
                 f"의도 분석 완료 (신뢰도: {state['intent_confidence']:.2f})")

    return state
```

### 4.2 컨텍스트 검색 노드 (Cortex 전용 RAG)

```python
def _context_retrieval_node(self, state: CortexState) -> CortexState:
    """
    Cortex 전용 RAG: 스키마, Few-shot 예제, 용어집 검색

    tb_sql_context 또는 tb_docs (doc_type 필터) 활용
    """
    request_id = state["request_id"]
    user_query = state["user_query"]
    error_type = state.get("error_type")
    correction_count = state.get("correction_count", 0)

    # Human 명확화 결과 반영
    if state.get("human_response"):
        user_query = f"{user_query} ({state['human_response']})"

    log_step(request_id, "CORTEX", "2", "CONTEXT",
             f"컨텍스트 검색 시작 (시도 #{correction_count + 1})")

    # 검색 전략 결정
    strategy = self._get_search_strategy(state)

    # 일괄 검색 (tb_docs 활용)
    contexts = cortex_vector_store.search_all_contexts(
        query=user_query,
        schema_top_k=strategy["schema"],
        example_top_k=strategy["query_example"],
        glossary_top_k=strategy["glossary"]
    )

    state["relevant_schemas"] = contexts["schemas"]
    state["similar_queries"] = contexts["examples"]
    state["business_terms"] = contexts["terms"]

    log_step(request_id, "CORTEX", "2", "CONTEXT",
             "컨텍스트 검색 완료",
             schemas=len(schema_docs),
             examples=len(example_docs),
             terms=len(term_docs))

    return state


def _get_search_strategy(self, state: CortexState) -> Dict[str, int]:
    """상황별 검색 전략"""
    error_type = state.get("error_type")
    correction_count = state.get("correction_count", 0)

    # 기본 전략
    strategy = {
        "schema": 5,
        "query_example": 3,
        "glossary": 3
    }

    # 스키마 오류 재시도: 검색 범위 확대
    if error_type == "schema":
        strategy["schema"] = 10
        strategy["query_example"] = 5

    # 여러 번 재시도: 예제 더 많이 검색
    if correction_count >= 2:
        strategy["query_example"] = min(strategy["query_example"] + correction_count, 8)

    return strategy
```

### 4.3 SQL 검증 노드 (승인 필요 체크 추가)

```python
def _sql_validation_node(self, state: CortexState) -> CortexState:
    """
    SQL 검증 + 승인 필요 여부 결정

    검증 항목:
    1. 구문 검증
    2. 스키마 검증
    3. 보안 검사
    4. 승인 필요 여부 (대량 조회, 민감 테이블)
    """
    request_id = state["request_id"]
    sql = state["generated_sql"]

    log_step(request_id, "CORTEX", "4", "VALIDATE", "SQL 검증 시작")

    errors = []
    error_type = None
    requires_approval = False

    # 1. 구문 검증
    is_valid_syntax, syntax_error = sql_executor.validate_sql(sql)
    if not is_valid_syntax:
        errors.append(f"구문 오류: {syntax_error}")
        error_type = "syntax"

    # 2. 스키마 검증
    if is_valid_syntax:
        schema_errors = self._validate_schema_references(sql, state)
        if schema_errors:
            errors.extend(schema_errors)
            error_type = "schema"

    # 3. 보안 검사
    security_result = self._validate_security(sql)
    if security_result["errors"]:
        errors.extend(security_result["errors"])
        error_type = "security"
    if security_result["requires_approval"]:
        requires_approval = True

    # 4. 대량 조회 체크 (LIMIT 없는 경우)
    if is_valid_syntax and not errors:
        if self._is_large_query(sql):
            requires_approval = True
            log_step(request_id, "CORTEX", "4", "VALIDATE",
                     "대량 조회 감지 → 승인 필요")

    # 결과 저장
    state["is_valid"] = len(errors) == 0
    state["validation_errors"] = errors
    state["error_type"] = error_type
    state["requires_approval"] = requires_approval

    if errors:
        state["last_error_feedback"] = "\n".join(errors)

    return state


def _validate_security(self, sql: str) -> Dict[str, Any]:
    """보안 검사"""
    result = {"errors": [], "requires_approval": False}

    # 금지 키워드
    forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
                 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']

    sql_upper = sql.upper()
    for keyword in forbidden:
        import re
        if re.search(rf'\b{keyword}\b', sql_upper):
            result["errors"].append(f"금지된 키워드: {keyword}")

    # 민감 테이블 접근 체크
    sensitive_tables = ['salary', 'performance_review']
    for table in sensitive_tables:
        if re.search(rf'\b{table}\b', sql.lower()):
            result["requires_approval"] = True
            log_step("SYSTEM", "CORTEX", "SEC", "CHECK",
                     f"민감 테이블 접근: {table}")

    return result


def _is_large_query(self, sql: str) -> bool:
    """대량 조회 여부 판단"""
    sql_upper = sql.upper()

    # LIMIT이 없는 SELECT
    if 'SELECT' in sql_upper and 'LIMIT' not in sql_upper:
        # 집계 쿼리가 아닌 경우
        if not any(agg in sql_upper for agg in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
            return True

    return False
```

---

## 5. Human in the Loop

### 5.1 개입 유형

| 유형 | 노드 | 트리거 | 사용자 액션 |
|------|------|-------|------------|
| **Clarification** | `human_clarification` | 모호한 질문 | 선택지 선택 또는 직접 입력 |
| **Approval** | `human_approval` | 민감 데이터, 대량 조회 | 승인/거부/수정 |
| **Escalation** | `human_escalation` | 최대 재시도 초과 | 관리자 검토 요청 |

### 5.2 Human 노드 구현

```python
def _human_clarification_node(self, state: CortexState) -> CortexState:
    """
    Human 명확화 요청

    interrupt_before 패턴 사용:
    - 그래프 실행 중단
    - 사용자 응답 대기
    - 응답 후 그래프 재개
    """
    request_id = state["request_id"]
    options = state.get("ambiguity_options", [])

    log_step(request_id, "CORTEX", "H1", "HUMAN", "명확화 요청")

    state["requires_human"] = True
    state["waiting_for_human"] = True
    state["human_intervention"] = {
        "type": "clarification",
        "message": "질문이 모호합니다. 다음 중 선택하거나 구체적으로 설명해주세요:",
        "options": options,
        "context": {"original_query": state["user_query"]}
    }

    # LangGraph의 interrupt 패턴으로 여기서 중단
    # 사용자 응답 후 resume하면 human_response가 채워짐

    return state


def _human_approval_node(self, state: CortexState) -> CortexState:
    """
    Human 실행 전 승인 요청
    """
    request_id = state["request_id"]
    sql = state["generated_sql"]

    reason = []
    if state.get("error_type") == "security":
        reason.append("민감한 테이블(급여, 성과평가)에 접근합니다")
    if state.get("requires_approval"):
        reason.append("대량 데이터 조회가 예상됩니다")

    log_step(request_id, "CORTEX", "H2", "HUMAN",
             "실행 승인 요청", reasons=reason)

    state["requires_human"] = True
    state["waiting_for_human"] = True
    state["human_intervention"] = {
        "type": "approval",
        "message": f"다음 SQL 실행을 승인하시겠습니까?\n\n{sql}\n\n사유: {', '.join(reason)}",
        "options": ["승인", "거부", "수정"],
        "context": {
            "sql": sql,
            "reasons": reason
        }
    }

    return state


def _human_escalation_node(self, state: CortexState) -> CortexState:
    """
    Human 에스컬레이션 (최대 재시도 초과)
    """
    request_id = state["request_id"]
    correction_count = state.get("correction_count", 0)
    errors = state.get("validation_errors", [])

    log_step(request_id, "CORTEX", "H3", "HUMAN",
             f"에스컬레이션 (재시도 {correction_count}회 실패)")

    state["requires_human"] = True
    state["waiting_for_human"] = True
    state["human_intervention"] = {
        "type": "escalation",
        "message": f"""자동 처리에 실패했습니다. 관리자 검토가 필요합니다.

질문: {state['user_query']}
시도 횟수: {correction_count}
마지막 오류: {errors[-1] if errors else 'N/A'}

생성된 SQL:
{state.get('generated_sql', 'N/A')}""",
        "options": None,
        "context": {
            "query": state["user_query"],
            "attempts": correction_count,
            "errors": errors,
            "last_sql": state.get("generated_sql")
        }
    }

    return state
```

### 5.3 API에서 Human 응답 처리

```python
# app/api/routes/cortex.py

@router.post("/search", response_model=CortexResponse)
async def search(request: CortexRequest) -> CortexResponse:
    """Cortex 검색 (Human 개입 필요 시 중단)"""
    result = await cortex_service.search(request)

    # Human 개입 필요 시
    if result.requires_human:
        return CortexResponse(
            success=False,
            answer="",
            requires_human=True,
            human_intervention=result.human_intervention,
            session_id=result.session_id,
            request_id=result.request_id
        )

    return result


@router.post("/respond", response_model=CortexResponse)
async def respond_to_human_request(
    session_id: str,
    response: str
) -> CortexResponse:
    """
    Human 응답 제출 후 그래프 재개

    Args:
        session_id: 세션 ID
        response: 사용자 응답 (선택지 또는 직접 입력)
    """
    return await cortex_service.resume_with_response(session_id, response)
```

### 5.4 프론트엔드 연동 흐름

```
1. 사용자 질문 제출
   POST /api/v1/cortex/search

2. 응답 확인
   - requires_human=false → 최종 답변 표시
   - requires_human=true → Human 개입 UI 표시

3. Human 개입 UI
   ┌─────────────────────────────────────────┐
   │ 질문이 모호합니다. 선택해주세요:         │
   │                                         │
   │ ○ 2024년 1분기 (1-3월)                 │
   │ ○ 2024년 상반기 (1-6월)                │
   │ ○ 2024년 전체                          │
   │ ○ 직접 입력: [_________________]       │
   │                                         │
   │           [확인] [취소]                 │
   └─────────────────────────────────────────┘

4. 사용자 응답 제출
   POST /api/v1/cortex/respond
   { "session_id": "...", "response": "2024년 1분기" }

5. 그래프 재개 → 최종 답변
```

---

## 6. 에러 복구 전략

### 6.1 에러 유형별 복구 경로

| 에러 유형 | 복구 경로 | 설명 |
|----------|----------|------|
| **syntax** | SQL 생성 → 재시도 | 구문 오류 피드백과 함께 재생성 |
| **schema** | 컨텍스트 검색 → 재시도 | 추가 스키마 검색 후 재생성 |
| **execution** | SQL 생성 → 재시도 | DB 에러 메시지와 함께 재생성 |
| **timeout** | SQL 생성 → 재시도 | 최적화 힌트 추가 요청 |
| **security** | Human 승인 → 분기 | 승인 시 실행, 거부 시 종료 |
| **max_retry** | Human 에스컬레이션 | 관리자 검토 요청 |

### 6.2 재시도 카운터

```python
# correction_count 관리
# - SQL 생성 노드에서 증가
# - 최대값: max_corrections (기본 3)

# 경로별 재시도 소모
# - syntax 오류 → 1회 소모
# - schema 오류 → 1회 소모 (컨텍스트 재검색 포함)
# - execution 오류 → 1회 소모

# 재시도 초과 시
# - Human 에스컬레이션 노드로 이동
# - 관리자에게 검토 요청
```

---

## 7. Cortex 전용 RAG 구조

### 7.1 데이터베이스 스키마

**기존 tb_docs 테이블 활용 + usage_type 컬럼 추가**

기존 `tb_docs` 테이블을 재사용하되, `usage_type` 컬럼을 추가하여 RAG와 Cortex 문서를 명확히 구분합니다.

| usage_type | 용도 | doc_type 예시 |
|------------|------|--------------|
| `rag` | 문서 기반 답변 (기존) | policy, guide, faq, job_posting |
| `cortex` | SQL 생성 컨텍스트 | schema, query_example, glossary |

```sql
-- tb_docs에 usage_type 컬럼 추가
ALTER TABLE tb_docs ADD COLUMN IF NOT EXISTS
    usage_type VARCHAR(20) DEFAULT 'rag';

COMMENT ON COLUMN tb_docs.usage_type IS '문서 용도: rag(문서 답변), cortex(SQL 생성)';

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_tb_docs_usage_type ON tb_docs(usage_type);
CREATE INDEX IF NOT EXISTS idx_tb_docs_usage_doc_type ON tb_docs(usage_type, doc_type);
```

**tb_docs 테이블 구조 (확장 후)**

```sql
CREATE TABLE tb_docs (
    id bigserial NOT NULL,
    title text NOT NULL,
    doc_type text NOT NULL,           -- 'schema', 'query_example', 'glossary'
    usage_type varchar(20) DEFAULT 'rag', -- 🆕 'rag' 또는 'cortex'
    "language" text DEFAULT 'ko'::text NULL,
    "content" text NOT NULL,
    metadata jsonb NULL,               -- Cortex 전용 필드를 여기에 저장
    embedding public.vector(1536) NULL,
    embedding_model text DEFAULT 'text-embedding-3-small'::text NULL,
    indexed bool DEFAULT false NULL,
    ...
);
```

**코드 추가 (tb_code)**

```sql
-- USAGE_TYPE 코드 그룹 추가
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
('CODE_GROUP', 'USAGE_TYPE', '문서 용도', 'tb_docs usage_type 컬럼 값', NULL, 12, true, true, NULL);

-- USAGE_TYPE 값
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
('USAGE_TYPE', 'rag', 'RAG 문서', '문서 기반 답변용', '{"tag_type": "primary"}', 1, true, true, 'USAGE_TYPE'),
('USAGE_TYPE', 'cortex', 'Cortex SQL', 'SQL 생성 컨텍스트용', '{"tag_type": "warning"}', 2, true, true, 'USAGE_TYPE');

-- DOC_TYPE에 Cortex 전용 유형 추가
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
('DOC_TYPE', 'schema', 'DB 스키마', '데이터베이스 테이블 스키마 정보', '{"tag_type": "danger"}', 10, true, true, 'DOC_TYPE'),
('DOC_TYPE', 'query_example', '쿼리 예제', 'NL2SQL Few-shot 예제', '{"tag_type": "warning"}', 11, true, true, 'DOC_TYPE'),
('DOC_TYPE', 'glossary', '용어집', '비즈니스 용어-SQL 매핑', '{"tag_type": "secondary"}', 12, true, true, 'DOC_TYPE');
```

**metadata JSONB 구조 (doc_type별)**

```jsonc
// doc_type: 'schema'
{
    "table_name": "employee",
    "columns": ["emp_id", "emp_name", "hire_date", ...],
    "primary_key": "emp_id",
    "foreign_keys": {"dept_id": "department.dept_id"},
    "row_count_estimate": 500,
    "tags": ["employee", "직원", "인사", "HR"]
}

// doc_type: 'query_example'
{
    "intent": "AGGREGATE",           // SELECT, AGGREGATE, JOIN, SUBQUERY
    "complexity": "medium",          // simple, medium, complex
    "tables": ["employee", "department"],
    "sql_template": "SELECT COUNT(*) FROM employee WHERE ...",
    "tags": ["입사", "연도별", "COUNT", "집계"]
}

// doc_type: 'glossary'
{
    "term": "재직자",
    "sql_condition": "status = 'active'",
    "synonyms": ["현직", "재직중", "active"],
    "column_reference": "employee.status",
    "tags": ["재직", "상태", "status"]
}
```

### 7.2 샘플 데이터 (tb_docs 활용)

```sql
-- ===================================================================
-- 스키마 정보 (doc_type: 'schema', usage_type: 'cortex')
-- ===================================================================

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, usage_type) VALUES
(
    'employee 테이블',
    'schema',
    '## employee 테이블 (직원 정보)

### 컬럼
- emp_id: INTEGER (PK) - 직원 고유 ID
- emp_name: VARCHAR(100) NOT NULL - 직원 이름
- hire_date: DATE NOT NULL - 입사일
- dept_id: INTEGER (FK) - 소속 부서 ID
- position: VARCHAR(50) - 직급
- status: VARCHAR(20) DEFAULT ''active'' - 재직상태
- work_type: VARCHAR(20) - 근무유형 (office, remote, hybrid)

### 주요 관계
- department 테이블과 dept_id로 연결
- salary 테이블과 emp_id로 연결',
    '{
        "table_name": "employee",
        "columns": ["emp_id", "emp_name", "hire_date", "dept_id", "position", "status", "work_type"],
        "primary_key": "emp_id",
        "foreign_keys": {"dept_id": "department.dept_id"},
        "row_count_estimate": 500,
        "tags": ["employee", "직원", "인사", "HR"]
    }'::jsonb,
    true,
    'cortex'
);

-- ===================================================================
-- Few-shot 쿼리 예제 (doc_type: 'query_example', usage_type: 'cortex')
-- ===================================================================

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, usage_type) VALUES
(
    '2024년 입사자 수는 몇 명인가요?',
    'query_example',
    '연도별 입사자 수를 집계하는 쿼리 예제

```sql
SELECT COUNT(*) as total_count
FROM employee
WHERE EXTRACT(YEAR FROM hire_date) = 2024
  AND status = ''active'';
```

**핵심 패턴**: EXTRACT(YEAR FROM hire_date), status = ''active''',
    '{
        "intent": "AGGREGATE",
        "complexity": "simple",
        "tables": ["employee"],
        "sql_template": "SELECT COUNT(*) FROM employee WHERE EXTRACT(YEAR FROM hire_date) = ? AND status = ''active''",
        "tags": ["입사", "연도별", "COUNT", "집계"]
    }'::jsonb,
    true,
    'cortex'
),
(
    '부서별 직원 수를 알려줘',
    'query_example',
    '부서별 그룹화하여 직원 수 집계

```sql
SELECT d.dept_name, COUNT(e.emp_id) as employee_count
FROM department d
LEFT JOIN employee e ON d.dept_id = e.dept_id AND e.status = ''active''
GROUP BY d.dept_id, d.dept_name
ORDER BY employee_count DESC;
```

**핵심 패턴**: LEFT JOIN, GROUP BY, COUNT',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["employee", "department"],
        "sql_template": "SELECT dept_name, COUNT(*) FROM department JOIN employee GROUP BY dept_name",
        "tags": ["부서별", "GROUP BY", "JOIN", "집계"]
    }'::jsonb,
    true,
    'cortex'
);

-- ===================================================================
-- 비즈니스 용어집 (doc_type: 'glossary', usage_type: 'cortex')
-- ===================================================================

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, usage_type) VALUES
(
    '재직자',
    'glossary',
    '**재직자 (Active Employee)**

현재 회사에 소속되어 근무 중인 직원을 의미합니다.

**SQL 조건**: WHERE status = ''active''

**반대 개념**: 퇴직자 (status = ''resigned''), 휴직자 (status = ''inactive'')',
    '{
        "term": "재직자",
        "sql_condition": "status = ''active''",
        "synonyms": ["현직", "재직중", "active"],
        "column_reference": "employee.status",
        "tags": ["재직", "상태", "status"]
    }'::jsonb,
    true,
    'cortex'
),
(
    '재택근무',
    'glossary',
    '**재택근무 (Remote Work)**

사무실이 아닌 자택에서 업무를 수행하는 근무 형태입니다.

**SQL 조건**: WHERE work_type IN (''remote'', ''hybrid'')

**근무 유형**: office (사무실), remote (완전 재택), hybrid (혼합)',
    '{
        "term": "재택근무",
        "sql_condition": "work_type IN (''remote'', ''hybrid'')",
        "synonyms": ["원격근무", "WFH", "하이브리드"],
        "column_reference": "employee.work_type",
        "tags": ["근무형태", "work_type"]
    }'::jsonb,
    true,
    'cortex'
);
```

### 7.3 Cortex Vector Store

```python
# app/core/vector/cortex_vector_store.py

from typing import List, Dict, Any
from app.core.database.connection import db_manager
from app.core.vector.vector_store import vector_store  # 기존 벡터 스토어 재사용


class CortexVectorStore:
    """
    Cortex 전용 벡터 스토어

    기존 tb_docs 테이블을 활용하여 SQL 컨텍스트 검색
    usage_type='cortex'로 필터링 후 doc_type으로 세부 구분
    """

    def search(
        self,
        query: str,
        context_type: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Cortex 전용 컨텍스트 검색

        Args:
            query: 검색 쿼리
            context_type: 'schema', 'query_example', 'glossary'
            top_k: 반환할 문서 수
            min_similarity: 최소 유사도 (tb_docs는 더 낮은 임계값)

        Returns:
            검색 결과 리스트
        """
        # 기존 vector_store의 임베딩 함수 재사용
        embedding = vector_store.get_embedding(query)

        # tb_docs에서 벡터 검색 (usage_type='cortex' 필터링)
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT
                    id, title, content, doc_type,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM tb_docs
                WHERE usage_type = 'cortex'
                  AND doc_type = %s
                  AND indexed = true
                  AND embedding IS NOT NULL
                  AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT %s
            """, (embedding, context_type, embedding, min_similarity, top_k))

            columns = [desc[0] for desc in cur.description]
            results = []
            for row in cur.fetchall():
                doc = dict(zip(columns, row))
                # metadata에서 추가 필드 추출
                if doc.get('metadata'):
                    doc.update(doc['metadata'])
                results.append(doc)
            return results

    def search_all_contexts(
        self,
        query: str,
        schema_top_k: int = 5,
        example_top_k: int = 3,
        glossary_top_k: int = 3,
        min_similarity: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 컨텍스트 유형 일괄 검색

        Returns:
            {
                "schemas": [...],
                "examples": [...],
                "terms": [...]
            }
        """
        return {
            "schemas": self.search(query, "schema", schema_top_k, min_similarity),
            "examples": self.search(query, "query_example", example_top_k, min_similarity),
            "terms": self.search(query, "glossary", glossary_top_k, min_similarity)
        }


# 싱글톤
cortex_vector_store = CortexVectorStore()
```

---

## 8. 상태 및 데이터 모델

### 8.1 요청/응답 모델

```python
# app/models/cortex.py

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class HumanInterventionInfo(BaseModel):
    """Human 개입 정보"""
    type: Literal["clarification", "approval", "escalation"]
    message: str
    options: Optional[List[str]] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class CortexRequest(BaseModel):
    """Cortex 요청"""
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    max_corrections: int = Field(default=3, ge=1, le=5)


class CortexSQLResult(BaseModel):
    """SQL 결과"""
    sql: str
    dialect: str
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0


class CortexResponse(BaseModel):
    """Cortex 응답"""
    success: bool
    answer: str = ""

    # Human in the Loop
    requires_human: bool = False
    human_intervention: Optional[HumanInterventionInfo] = None

    # SQL 결과
    sql_result: Optional[CortexSQLResult] = None

    # 메타데이터
    session_id: Optional[str] = None
    request_id: str = ""
    response_time_ms: int = 0
    correction_attempts: int = 0

    # 에러
    error: Optional[str] = None
```

---

## 9. API 설계

### 9.1 엔드포인트

```python
# app/api/routes/cortex.py

router = APIRouter(prefix="/api/v1/cortex", tags=["Cortex"])


@router.post("/search", response_model=CortexResponse)
async def search(request: CortexRequest) -> CortexResponse:
    """
    Cortex 검색

    Human 개입 필요 시 requires_human=true 반환
    """
    return await cortex_service.search(request)


@router.post("/respond")
async def respond(session_id: str, response: str) -> CortexResponse:
    """Human 응답 후 그래프 재개"""
    return await cortex_service.resume_with_response(session_id, response)


@router.get("/sessions")
async def list_sessions():
    """활성 세션 목록"""
    return {"sessions": cortex_service.get_sessions()}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    return cortex_service.delete_session(session_id)
```

---

## 10. 프로젝트 구조

```
app/
├── graphs/
│   ├── cortex_graph.py           # 🆕 Cortex 그래프 (Human in the Loop 포함)
│   ├── rag_graph.py              # 유지 (문서 답변용)
│   └── nl2sql_graph.py           # 유지 (단순 SQL)
├── api/
│   ├── routes/
│   │   ├── cortex.py             # 🆕 Cortex API
│   │   └── search.py             # RAG, NL2SQL API (유지)
│   └── services/
│       └── cortex_service.py     # 🆕 Cortex 서비스
├── models/
│   └── cortex.py                 # 🆕 Cortex 모델
├── core/
│   ├── vector/
│   │   ├── vector_store.py       # 기존 RAG용 (재사용)
│   │   └── cortex_vector_store.py # 🆕 Cortex 전용 (tb_docs 필터링)
│   └── llm/
│       └── prompt_service.py     # 🔄 Cortex 프롬프트 추가
└── scripts/
    └── sql/
        ├── insert_nl2sql_rag_data.sql  # 🔄 Cortex SQL 컨텍스트 데이터
        └── insert_cortex_codes.sql     # 🆕 DOC_TYPE 코드 추가
```

---

## 11. 구현 가이드

### 11.1 1차 개발 범위

| 구성요소 | 내용 | 우선순위 |
|---------|------|---------|
| Cortex 그래프 | 10개 노드 구현 | 필수 |
| Human in the Loop | clarification, approval, escalation | 필수 |
| tb_docs 활용 | doc_type으로 schema/query_example/glossary 구분 | 필수 |
| tb_code 확장 | DOC_TYPE에 Cortex 전용 유형 추가 | 필수 |
| cortex_vector_store | tb_docs 기반 Cortex 전용 검색 | 필수 |
| API 엔드포인트 | search, respond | 필수 |
| 에러 복구 루프 | 검증/실행 실패 재시도 | 필수 |

### 11.2 구현 순서

1. **tb_code 확장** (`scripts/sql/insert_cortex_codes.sql`)
2. **모델 정의** (`app/models/cortex.py`)
3. **Cortex Vector Store** (`app/core/vector/cortex_vector_store.py`)
4. **그래프 구현** (`app/graphs/cortex_graph.py`)
5. **서비스 구현** (`app/api/services/cortex_service.py`)
6. **API 라우트** (`app/api/routes/cortex.py`)
7. **프롬프트 확장** (`app/core/llm/prompt_service.py`)
8. **샘플 데이터 INSERT** (`scripts/sql/insert_nl2sql_rag_data.sql`)
9. **임베딩 생성** (`python scripts/embed_documents.py`)
10. **프론트엔드 Human 개입 UI**
11. **통합 테스트**

---

## 12. 2차 개발 계획

### 12.1 캐싱 (2차)

| 캐시 | 저장소 | TTL |
|------|-------|-----|
| 스키마 캐시 | Redis | 1시간 |
| 쿼리 결과 캐시 | Redis | 5분 |
| 임베딩 캐시 | Redis | 24시간 |

### 12.2 보안 강화 (2차)

- AST 기반 SQL 검증
- 사용자별 테이블 접근 제어 (RBAC)
- 감사 로깅 테이블

### 12.3 확장 기능 (2차)

- 스트리밍 응답 (SSE)
- PostgresSaver 체크포인팅
- 차트 추천
- WebSocket Human 개입

### 12.4 기존 코드 정리 (2차)

- `app/graphs/agent_graph.py` 제거
- `app/tools/` 폴더 제거
- `app/models/agent.py` 제거

---

*— 문서 끝 —*
