# Agent 모드 확장 설계서

**기존 InsightAgentGraph 기반 고도화**

버전 3.1 | 2026년 1월

---

## 목차

1. [개요](#1-개요)
2. [현재 Agent 구조 분석](#2-현재-agent-구조-분석)
3. [확장 아키텍처](#3-확장-아키텍처)
4. [추가 노드 설계](#4-추가-노드-설계)
5. [추가 도구(Tools) 설계](#5-추가-도구tools-설계)
6. [Human in the Loop](#6-human-in-the-loop)
7. [확장된 상태(State) 설계](#7-확장된-상태state-설계)
8. [에러 복구 전략](#8-에러-복구-전략)
9. [플러그인 아키텍처](#9-플러그인-아키텍처)
10. [구현 가이드](#10-구현-가이드)
11. [2차 개발 로드맵](#11-2차-개발-로드맵)

---

## 1. 개요

### 1.1 목적

기존 `InsightAgentGraph`(ReAct 패턴)를 확장하여 다음 기능을 추가합니다:
- **의도 분석 노드**: 질문 이해, 모호성 감지
- **컨텍스트 검색 강화**: 스키마, Few-shot, 용어집 RAG 검색
- **SQL 검증 노드**: 구문/스키마/보안 검증
- **Human in the Loop**: 명확화, 승인, 에스컬레이션

### 1.2 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **기존 구조 유지** | `InsightAgentGraph`, `AgentState`, 기존 도구 유지 |
| **점진적 확장** | 새 노드/엣지/도구를 추가하는 방식 |
| **하위 호환성** | 기존 API 응답 형식 유지 |
| **플러그인 패턴** | 새 기능은 플러그인으로 추가 가능 |

### 1.3 모드 구성 (변경 없음)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MUREUM 모드 구성 (3개)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────┐                             │
│  │ RAG 모드 (유지)                        │                             │
│  │  • 정책/규정/가이드 문서 검색          │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  ┌───────────────────────────────────────┐                             │
│  │ NL2SQL 모드 (유지)                     │                             │
│  │  • 단순 SQL 변환 (빠른 응답)           │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Agent 모드 (확장) ⭐                                               │ │
│  │  • 기존: ReAct 패턴 (agent → tools → agent 루프)                  │ │
│  │  • 추가: 의도 분석, 컨텍스트 검색, SQL 검증, Human 개입            │ │
│  │  • 추가 도구: schema_search, fewshot_search, glossary_search      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 Agent 구조 분석

### 2.1 기존 구조 (`app/graphs/agent_graph.py`)

```python
# 현재 AgentState
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    session_id: str
    config: AgentConfig
    iteration_count: int
    final_answer: str
    request_id: str
    start_time: float
```

### 2.2 기존 그래프 플로우

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     현재 InsightAgentGraph (ReAct)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                      │
│  │   START      │                                                      │
│  └──────┬───────┘                                                      │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────┐                                                      │
│  │    agent     │◀─────────────────────────────────────┐               │
│  │  (LLM 결정)  │                                      │               │
│  └──────┬───────┘                                      │               │
│         │                                              │               │
│         ▼                                              │               │
│  ┌──────────────┐                                      │               │
│  │should_continue│                                     │               │
│  │              │                                      │               │
│  └──────┬───────┘                                      │               │
│         │                                              │               │
│    ┌────┴────┐                                         │               │
│    ▼         ▼                                         │               │
│ [continue] [end]                                       │               │
│    │         │                                         │               │
│    │         ▼                                         │               │
│    │       END                                         │               │
│    │                                                   │               │
│    ▼                                                   │               │
│  ┌──────────────┐                                      │               │
│  │    tools     │──────────────────────────────────────┘               │
│  │ (ToolNode)   │                                                      │
│  └──────────────┘                                                      │
│                                                                         │
│  도구 목록:                                                             │
│  • query_database_tool (SQL 실행)                                      │
│  • search_documents_tool (RAG 검색)                                    │
│  • calculate_tool (계산기)                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 기존 코드 위치

| 파일 | 역할 |
|------|------|
| `app/graphs/agent_graph.py` | Agent 그래프 (InsightAgentGraph) |
| `app/models/agent.py` | AgentState, AgentResponse 등 |
| `app/tools/sql_tool.py` | SQL 실행 도구 |
| `app/tools/rag_tool.py` | RAG 검색 도구 |
| `app/tools/calc_tool.py` | 계산기 도구 |
| `app/api/services/agent_service.py` | Agent 서비스 |
| `app/api/routes/agent.py` | Agent API 라우트 |

---

## 3. 확장 아키텍처

### 3.1 확장된 그래프 플로우

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     확장된 InsightAgentGraph v3.0                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐                                                              │
│  │   START      │                                                              │
│  └──────┬───────┘                                                              │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │   🆕 intent_analysis (의도 분석 노드)                                    │   │
│  │   • 질문 유형 분류 (SQL 질의 / 단순 질문 / 복합 질문)                    │   │
│  │   • 엔티티 추출: 테이블, 컬럼, 조건값                                    │   │
│  │   • 모호성 감지: 기간/범위/기준이 불명확한 경우                          │   │
│  │   • 신뢰도 점수 산출 (0.0 ~ 1.0)                                        │   │
│  └──────┬───────────────────────────────────────────────────────────────────┘   │
│         │                                                                       │
│         ▼                                                                       │
│  ┌──────────────┐         ┌───────────────────────────────────────────────┐    │
│  │ 🆕 명확화    │───YES──▶│  🆕 human_clarification (Human 명확화 노드)    │    │
│  │ 필요?        │         │  • interrupt 패턴으로 실행 중단                 │    │
│  │              │         │  • 사용자에게 선택지 제시                       │    │
│  └──────┬───────┘         └──────────────────────┬────────────────────────┘    │
│         │ NO                                      │ (사용자 선택 후 재개)       │
│         ▼                                         ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │   🆕 context_retrieval (컨텍스트 검색 노드)                              │   │
│  │   • 스키마 벡터 검색 (doc_type: schema)                                  │   │
│  │   • Few-shot 예제 검색 (doc_type: query_example)                        │   │
│  │   • 용어집 검색 (doc_type: glossary)                                    │   │
│  │   • 에러 복구 시 검색 범위 동적 확장                                     │   │
│  └──────┬───────────────────────────────────────────────────────────────────┘   │
│         │                                                                       │
│         ▼                                                                       │
│  ┌──────────────┐                                                              │
│  │    agent     │◀─────────────────────────────────────┐                       │
│  │  (LLM 결정)  │                                      │                       │
│  │  ※ 기존 유지 │                                      │                       │
│  └──────┬───────┘                                      │                       │
│         │                                              │                       │
│         ▼                                              │                       │
│  ┌──────────────┐                                      │                       │
│  │should_continue│                                     │                       │
│  │  ※ 기존 유지 │                                      │                       │
│  └──────┬───────┘                                      │                       │
│         │                                              │                       │
│    ┌────┴────┐                                         │                       │
│    ▼         ▼                                         │                       │
│ [continue] [end]                                       │                       │
│    │         │                                         │                       │
│    │         ▼                                         │                       │
│    │  ┌──────────────┐                                 │                       │
│    │  │🆕 sql_validate│ (SQL 검증 노드, 선택적)         │                       │
│    │  │  • query_database_tool 결과 후처리             │                       │
│    │  └──────┬───────┘                                 │                       │
│    │         │                                         │                       │
│    │         ▼                                         │                       │
│    │       END                                         │                       │
│    │                                                   │                       │
│    ▼                                                   │                       │
│  ┌──────────────┐                                      │                       │
│  │    tools     │──────────────────────────────────────┘                       │
│  │ (ToolNode)   │                                                              │
│  │  ※ 기존 + 신규 도구                                                        │
│  └──────────────┘                                                              │
│                                                                                 │
│  도구 목록 (기존 + 신규):                                                       │
│  ✅ query_database_tool (기존, SQL 실행)                                       │
│  ✅ search_documents_tool (기존, RAG 검색, usage_type='rag_knowledge')         │
│  ✅ calculate_tool (기존, 계산기)                                              │
│  🆕 context_search_tool (통합, SQL 컨텍스트 검색, usage_type='rag_action')     │
│     • context_type: "schema" | "example" | "glossary" | "all"                 │
│  🆕 sql_validate_tool (SQL 검증, 선택적)                                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 확장 요소 요약

| 구분 | 기존 | 추가 |
|------|------|------|
| **노드** | agent, tools | intent_analysis, context_retrieval, human_clarification, sql_validate |
| **엣지** | agent↔tools 루프 | intent→human/context, context→agent, agent→validate |
| **도구** | 3개 | +2개 (context_search 통합, sql_validate) |
| **상태** | AgentState | ExtendedAgentState (기존 확장) |

### 3.3 usage_type 구분

| usage_type | 용도 | doc_type | 사용 도구 |
|------------|------|----------|----------|
| `rag_knowledge` | 문서 기반 답변 | policy, guide, faq, job_posting | search_documents_tool |
| `rag_action` | SQL 컨텍스트 | schema, query_example, glossary | context_search_tool |

### 3.4 Human in the Loop 개입 지점

| 개입 유형 | 트리거 노드 | 트리거 조건 | 후속 처리 |
|----------|------------|------------|----------|
| **명확화** | intent_analysis | 모호성 감지 (신뢰도 < 0.7) | context_retrieval로 진행 |
| **보안 승인** | sql_validate | 민감 테이블 접근 | 승인 시 실행, 거부 시 종료 |
| **실행 승인** | sql_validate | 대량 조회, 복잡 쿼리 | 승인 시 실행 |
| **에스컬레이션** | agent | 최대 재시도 초과 | 에러 응답 |

---

## 4. 추가 노드 설계

### 4.1 의도 분석 노드 (intent_analysis)

```python
# app/graphs/nodes/intent_analysis.py

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage


def intent_analysis_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    의도 분석 노드

    기존 agent 노드 전에 실행되어 질문을 분석합니다.
    모호성이 감지되면 human_clarification으로 분기합니다.
    """
    request_id = state.get("request_id", "unknown")
    question = state["question"]

    log_step(request_id, "AGENT", "INTENT", "START", f"의도 분석 시작 | question={question[:50]}")

    llm = LLMConfigManager.create_llm(temperature=0)

    system_prompt = """당신은 자연어 질문을 분석하는 전문가입니다.
사용자 질문을 분석하여 다음 JSON 형식으로 응답하세요:

{
    "query_type": "sql_query | document_search | calculation | general",
    "intent": "select | aggregate | compare | trend | join | search | calculate",
    "confidence": 0.0~1.0,
    "is_ambiguous": true/false,
    "ambiguity_type": "period | quantity | criteria | table | null",
    "ambiguity_reason": "모호한 이유",
    "clarification_options": ["선택지1", "선택지2", "선택지3"],
    "extracted_entities": {
        "tables": ["추정 테이블명"],
        "columns": ["추정 컬럼명"],
        "conditions": [{"column": "컬럼", "operator": "=", "value": "값"}]
    }
}

모호성 판단 기준:
- period: 기간 불명확 ("최근", "올해" 등)
- quantity: 수량 기준 불명확 ("많은", "상위" 등)
- criteria: 평가 기준 불명확 ("좋은", "우수한" 등)
- table: 여러 테이블이 해당 가능
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"질문: {question}")
    ]

    response = llm.invoke(messages)
    result = parse_json_response(response.content)

    # 상태 업데이트
    state["intent_analysis"] = result
    state["intent_confidence"] = result.get("confidence", 1.0)
    state["is_ambiguous"] = result.get("is_ambiguous", False)
    state["ambiguity_options"] = result.get("clarification_options", [])
    state["extracted_entities"] = result.get("extracted_entities", {})

    if state["is_ambiguous"]:
        log_step(request_id, "AGENT", "INTENT", "AMBIGUOUS",
                 f"모호성 감지 | type={result.get('ambiguity_type')}, options={len(state['ambiguity_options'])}")
    else:
        log_step(request_id, "AGENT", "INTENT", "COMPLETE",
                 f"의도 분석 완료 | intent={result.get('intent')}, confidence={state['intent_confidence']:.2f}")

    return state


def should_clarify(state: ExtendedAgentState) -> str:
    """의도 분석 후 라우팅"""
    if state.get("is_ambiguous") and state.get("intent_confidence", 1.0) < 0.7:
        return "need_clarification"
    return "proceed"
```

### 4.2 Human 명확화 노드 (human_clarification)

```python
# app/graphs/nodes/human_clarification.py

def human_clarification_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    Human 명확화 요청 노드

    LangGraph의 interrupt 패턴을 사용하여 실행을 중단하고
    사용자 응답을 대기합니다.
    """
    request_id = state.get("request_id", "unknown")
    options = state.get("ambiguity_options", [])

    log_step(request_id, "AGENT", "HUMAN", "CLARIFY", "Human 명확화 요청")

    state["waiting_for_human"] = True
    state["human_intervention"] = {
        "type": "clarification",
        "message": "질문이 모호합니다. 다음 중 선택하거나 구체적으로 설명해주세요:",
        "options": options,
        "context": {
            "original_query": state["question"],
            "ambiguity_type": state.get("intent_analysis", {}).get("ambiguity_type")
        }
    }

    # LangGraph interrupt 패턴
    # 사용자 응답 후 resume하면 human_response가 채워짐

    return state
```

### 4.3 컨텍스트 검색 노드 (context_retrieval)

```python
# app/graphs/nodes/context_retrieval.py

def context_retrieval_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    컨텍스트 검색 노드

    tb_docs에서 SQL 생성에 필요한 컨텍스트를 검색합니다:
    - 스키마 정보 (doc_type: schema)
    - Few-shot 예제 (doc_type: query_example)
    - 용어집 (doc_type: glossary)
    """
    request_id = state.get("request_id", "unknown")
    question = state["question"]

    # Human 명확화 결과 반영
    if state.get("human_response"):
        question = f"{question} ({state['human_response']})"

    log_step(request_id, "AGENT", "CONTEXT", "START", "컨텍스트 검색 시작")

    # 1. 의도 기반 검색 전략 결정
    intent = state.get("intent_analysis", {}).get("intent", "select")
    strategy = _get_search_strategy(intent, state)

    # 2. 벡터 검색 실행
    contexts = cortex_vector_store.search_all_contexts(
        query=question,
        schema_top_k=strategy["schema"],
        example_top_k=strategy["query_example"],
        glossary_top_k=strategy["glossary"]
    )

    # 3. 상태 업데이트
    state["relevant_schemas"] = contexts["schemas"]
    state["similar_queries"] = contexts["examples"]
    state["business_terms"] = contexts["terms"]

    # 4. 시스템 프롬프트에 컨텍스트 추가
    context_prompt = _build_context_prompt(contexts)
    state["context_prompt"] = context_prompt

    log_step(request_id, "AGENT", "CONTEXT", "COMPLETE",
             f"검색 완료 | schemas={len(contexts['schemas'])}, examples={len(contexts['examples'])}, terms={len(contexts['terms'])}")

    return state


def _get_search_strategy(intent: str, state: ExtendedAgentState) -> Dict[str, int]:
    """의도별 검색 전략"""
    strategies = {
        "select": {"schema": 5, "query_example": 3, "glossary": 3},
        "aggregate": {"schema": 5, "query_example": 5, "glossary": 3},
        "join": {"schema": 10, "query_example": 5, "glossary": 3},
        "compare": {"schema": 8, "query_example": 5, "glossary": 5},
        "trend": {"schema": 5, "query_example": 8, "glossary": 3},
    }
    return strategies.get(intent, strategies["select"])


def _build_context_prompt(contexts: Dict) -> str:
    """검색된 컨텍스트를 프롬프트 문자열로 변환"""
    lines = []

    # 스키마 정보
    if contexts["schemas"]:
        lines.append("## 관련 테이블 스키마")
        for schema in contexts["schemas"][:5]:
            lines.append(f"### {schema.get('table_name', 'unknown')}")
            lines.append(f"컬럼: {', '.join(schema.get('columns', []))}")
            lines.append(schema.get('content', '')[:300])
            lines.append("")

    # Few-shot 예제
    if contexts["examples"]:
        lines.append("## 유사 쿼리 예제")
        for ex in contexts["examples"][:3]:
            lines.append(f"Q: {ex.get('title', '')}")
            lines.append(f"SQL: {ex.get('sql_template', '')}")
            lines.append("")

    # 용어집
    if contexts["terms"]:
        lines.append("## 비즈니스 용어")
        for term in contexts["terms"][:5]:
            lines.append(f"- {term.get('term', '')}: {term.get('sql_condition', '')}")

    return "\n".join(lines)
```

### 4.4 SQL 검증 노드 (sql_validate) - 선택적

```python
# app/graphs/nodes/sql_validate.py

def sql_validate_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    SQL 검증 노드 (선택적)

    query_database_tool 실행 전/후에 SQL을 검증합니다.
    민감 테이블 접근, 대량 조회 시 Human 승인을 요청합니다.
    """
    request_id = state.get("request_id", "unknown")

    # 마지막 tool call에서 SQL 추출
    last_message = state["messages"][-1] if state["messages"] else None
    if not last_message or not hasattr(last_message, "tool_calls"):
        return state

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "query_database_tool":
            sql = tool_call["args"].get("query", "")

            # 1. 보안 검사
            security_result = _check_security(sql)
            if security_result["requires_approval"]:
                state["waiting_for_human"] = True
                state["human_intervention"] = {
                    "type": "security_approval",
                    "message": f"민감 테이블 접근 승인이 필요합니다.\n\nSQL:\n{sql}",
                    "options": ["승인", "거부"],
                    "context": {"sql": sql, "tables": security_result["sensitive_tables"]}
                }
                log_step(request_id, "AGENT", "VALIDATE", "SECURITY",
                         f"민감 테이블 접근 | tables={security_result['sensitive_tables']}")

            # 2. 대량 조회 검사
            if _is_large_query(sql):
                state["waiting_for_human"] = True
                state["human_intervention"] = {
                    "type": "execution_approval",
                    "message": f"대량 데이터 조회 경고\n\nSQL:\n{sql}\n\nLIMIT이 없습니다.",
                    "options": ["승인 (1000행 제한)", "취소", "행 수 변경"],
                    "context": {"sql": sql}
                }
                log_step(request_id, "AGENT", "VALIDATE", "LARGE_QUERY", "대량 조회 감지")

    return state


def _check_security(sql: str) -> Dict[str, Any]:
    """보안 검사"""
    sensitive_tables = ['salary', 'performance_review', 'personal_info']
    found_tables = []

    for table in sensitive_tables:
        if table.lower() in sql.lower():
            found_tables.append(table)

    return {
        "requires_approval": len(found_tables) > 0,
        "sensitive_tables": found_tables
    }


def _is_large_query(sql: str) -> bool:
    """대량 조회 여부 판단"""
    sql_upper = sql.upper()

    if 'SELECT' in sql_upper and 'LIMIT' not in sql_upper:
        # 집계 함수가 없는 경우만
        if not any(agg in sql_upper for agg in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
            return True

    return False
```

---

## 5. 추가 도구(Tools) 설계

### 5.1 도구 목록

| 도구 | 용도 | usage_type | 파일 |
|------|------|------------|------|
| **query_database_tool** (기존) | SQL 실행 | - | `app/tools/sql_tool.py` |
| **search_documents_tool** (기존) | RAG 검색 | `rag_knowledge` | `app/tools/rag_tool.py` |
| **calculate_tool** (기존) | 계산기 | - | `app/tools/calc_tool.py` |
| **context_search_tool** (신규) | SQL 컨텍스트 통합 검색 | `rag_action` | `app/tools/context_tool.py` |
| **sql_validate_tool** (신규, 선택적) | SQL 검증 | - | `app/tools/validate_tool.py` |

### 5.2 SQL 컨텍스트 검색 도구 (통합)

> **설계 근거**: 스키마, Few-shot, 용어집 검색은 모두 동일한 `vector_store`와 `tb_docs` 테이블을 사용하므로 하나의 도구로 통합하여 LLM 도구 선택 복잡도를 낮추고 프롬프트 토큰을 절약합니다.

```python
# app/tools/context_tool.py

from langchain_core.tools import tool
from typing import Literal
from app.core.vector.vector_store import vector_store
from app.models.search import SearchFilters


@tool
def context_search_tool(
    query: str,
    context_type: Literal["schema", "example", "glossary", "all"] = "all",
    top_k: int = 5
) -> str:
    """
    SQL 생성에 필요한 컨텍스트를 검색합니다.

    테이블 스키마, 유사 쿼리 예제, 비즈니스 용어를 통합 검색합니다.
    SQL 쿼리 작성 전에 필요한 정보를 조회할 때 사용하세요.

    Args:
        query: 검색할 자연어 질문
        context_type: 검색 유형
            - "schema": 테이블 구조, 컬럼, 관계 정보
            - "example": 유사 SQL 쿼리 예제 (Few-shot)
            - "glossary": 비즈니스 용어 → SQL 조건 변환
            - "all": 모든 유형 통합 검색 (권장)
        top_k: 각 유형별 최대 결과 수 (기본 5)

    Returns:
        검색된 컨텍스트 정보

    Example:
        context_search_tool("부서별 입사자 수", "all")
        → 스키마 + 예제 + 용어 통합 결과

        context_search_tool("직원 테이블", "schema")
        → employee 테이블 스키마 정보

        context_search_tool("재직자", "glossary")
        → "재직자" → "WHERE status = 'active'"
    """
    results = []

    # 스키마 검색 (doc_type: schema)
    if context_type in ("schema", "all"):
        schemas = vector_store.search_similar_documents(
            query=query,
            filters=SearchFilters(usage_type="rag_action", doc_type="schema"),
            top_k=top_k,
            similarity_threshold=0.4
        )
        if schemas:
            results.append("## 관련 테이블 스키마")
            for s in schemas:
                results.append(f"### {s.get('title', 'Unknown')}")
                results.append(f"{s.get('content', '')[:300]}")
                results.append(f"유사도: {s.get('similarity', 0):.2f}\n")

    # Few-shot 예제 검색 (doc_type: query_example)
    if context_type in ("example", "all"):
        examples = vector_store.search_similar_documents(
            query=query,
            filters=SearchFilters(usage_type="rag_action", doc_type="query_example"),
            top_k=top_k,
            similarity_threshold=0.3
        )
        if examples:
            results.append("## 유사 쿼리 예제")
            for i, ex in enumerate(examples, 1):
                results.append(f"### 예제 {i}: {ex.get('title', '')}")
                results.append(f"```sql\n{ex.get('content', '')}\n```\n")

    # 용어집 검색 (doc_type: glossary)
    if context_type in ("glossary", "all"):
        terms = vector_store.search_similar_documents(
            query=query,
            filters=SearchFilters(usage_type="rag_action", doc_type="glossary"),
            top_k=top_k,
            similarity_threshold=0.5
        )
        if terms:
            results.append("## 비즈니스 용어")
            for t in terms:
                results.append(f"- **{t.get('title', '')}**: {t.get('content', '')[:100]}")

    return "\n".join(results) if results else "관련 컨텍스트를 찾을 수 없습니다."
```

### 5.3 기존 스키마 로더와의 관계

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     스키마 정보 소스 비교                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────────────────────────┐  ┌───────────────────────────────────┐  │
│  │  schema_loader (기존, 내부 사용)   │  │  context_search_tool (신규)       │  │
│  ├───────────────────────────────────┤  ├───────────────────────────────────┤  │
│  │  데이터 소스: 실제 DB 메타데이터   │  │  데이터 소스: tb_docs 벡터 임베딩  │  │
│  │  (information_schema 쿼리)        │  │  (usage_type='rag_action')        │  │
│  ├───────────────────────────────────┤  ├───────────────────────────────────┤  │
│  │  용도: NL2SQL 프롬프트에 자동 포함 │  │  용도: Agent가 필요시 호출         │  │
│  │  (정확한 테이블/컬럼 구조)         │  │  (비즈니스 컨텍스트, 예제)         │  │
│  ├───────────────────────────────────┤  ├───────────────────────────────────┤  │
│  │  정보: 테이블, 컬럼, FK, 인덱스    │  │  정보: 스키마 설명, 예제, 용어집   │  │
│  │  (DB 구조 정보)                   │  │  (의미/맥락 정보)                 │  │
│  └───────────────────────────────────┘  └───────────────────────────────────┘  │
│                                                                                 │
│  ✅ 두 가지는 상호 보완적이므로 둘 다 유지                                        │
│  • schema_loader: SQL 생성 시 정확한 구조 정보 (자동)                            │
│  • context_search_tool: Agent가 필요시 추가 컨텍스트 검색 (수동)                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 도구 등록

```python
# app/graphs/agent_graph.py 수정

def _get_tools(self) -> List:
    """
    사용 가능한 도구 목록 (확장)
    """
    from app.tools.context_tool import context_search_tool

    return [
        # 기존 도구
        query_database_tool,      # SQL 실행
        search_documents_tool,    # RAG 검색 (usage_type='rag_knowledge')
        calculate_tool,           # 계산기
        # 신규 도구
        context_search_tool,      # SQL 컨텍스트 통합 검색 (usage_type='rag_action')
    ]
```

---

## 6. Human in the Loop

### 6.1 개입 유형별 상세

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Human in the Loop Flow                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│  ┃  1️⃣ 명확화 요청 (Clarification)                                           ┃   │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛   │
│                                                                                 │
│  [트리거] intent_analysis 노드에서 모호성 감지 시                               │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │  • "최근 입사자" → 최근이 언제? (1주/1개월/3개월/6개월)                 │      │
│  │  • "많은 직원" → 몇 명 이상? (상위 10명/20명/100명)                     │      │
│  │  • 여러 테이블 해당 가능 → 어느 테이블?                                 │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│  [UI 예시]                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │  💬 질문을 더 명확하게 이해하고 싶습니다.                              │       │
│  │                                                                     │       │
│  │  "최근 입사자"의 기간을 선택해 주세요:                                │       │
│  │                                                                     │       │
│  │  ○ 최근 1주                                                         │       │
│  │  ○ 최근 1개월                                                       │       │
│  │  ○ 최근 3개월 (권장)                                                │       │
│  │  ○ 직접 입력: [____________]                                        │       │
│  │                                                                     │       │
│  │                      [확인]  [취소]                                  │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│  ┃  2️⃣ 보안 승인 (Security Approval)                                         ┃   │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛   │
│                                                                                 │
│  [트리거] sql_validate 노드에서 민감 테이블 접근 감지 시                        │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │  • salary (급여 테이블)                                               │      │
│  │  • performance_review (성과 평가 테이블)                              │      │
│  │  • personal_info (개인정보 테이블)                                    │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│  [UI 예시]                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │  ⚠️ 보안 승인이 필요합니다                                            │       │
│  │                                                                     │       │
│  │  다음 쿼리는 민감한 데이터에 접근합니다:                               │       │
│  │                                                                     │       │
│  │  SELECT emp_name, salary_amount                                     │       │
│  │  FROM employee e JOIN salary s ON e.emp_id = s.emp_id;              │       │
│  │                                                                     │       │
│  │  접근 테이블: salary (급여 정보)                                      │       │
│  │                                                                     │       │
│  │                  [승인]  [거부]                                      │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│  ┃  3️⃣ 실행 전 승인 (Execution Approval)                                     ┃   │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛   │
│                                                                                 │
│  [트리거] sql_validate 노드에서 대량 조회 감지 시                               │
│  ┌──────────────────────────────────────────────────────────────────────┐      │
│  │  • LIMIT 없는 SELECT (집계 함수 제외)                                 │      │
│  │  • 복잡한 JOIN (3개 테이블 이상)                                      │      │
│  └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│  [UI 예시]                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │  📊 대량 데이터 조회 경고                                              │       │
│  │                                                                     │       │
│  │  SELECT * FROM employee WHERE status = 'active';                    │       │
│  │                                                                     │       │
│  │  ⚠️ LIMIT이 없습니다. 최대 1000행까지만 조회합니다.                   │       │
│  │                                                                     │       │
│  │           [승인 (1000행 제한)]  [취소]  [행 수 변경]                  │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 API 응답 처리

```python
# app/api/routes/agent.py (수정)

@router.post("/search", response_model=AgentResponse)
async def search(request: AgentRequest) -> AgentResponse:
    """Agent 검색 (Human 개입 필요 시 중단)"""
    result = await agent_service.search(request)

    # Human 개입 필요 시
    if result.waiting_for_human:
        return AgentResponse(
            success=False,
            answer="",
            waiting_for_human=True,
            human_intervention=result.human_intervention,
            session_id=result.session_id,
            request_id=result.request_id
        )

    return result


@router.post("/respond")
async def respond(session_id: str, response: str) -> AgentResponse:
    """Human 응답 후 그래프 재개"""
    return await agent_service.resume_with_response(session_id, response)
```

---

## 7. 확장된 상태(State) 설계

### 7.1 ExtendedAgentState

```python
# app/models/agent.py (확장)

class ExtendedAgentState(TypedDict):
    """확장된 Agent 상태"""

    # ===== 기존 필드 (유지) =====
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    session_id: str
    config: AgentConfig
    iteration_count: int
    final_answer: str
    request_id: str
    start_time: float

    # ===== 의도 분석 (신규) =====
    intent_analysis: Dict[str, Any]       # 의도 분석 결과 전체
    intent_confidence: float              # 신뢰도 (0.0 ~ 1.0)
    is_ambiguous: bool                    # 모호성 여부
    ambiguity_options: List[str]          # 명확화 선택지
    extracted_entities: Dict[str, Any]    # 추출된 엔티티

    # ===== 컨텍스트 검색 (신규) =====
    relevant_schemas: List[Dict[str, Any]]   # 검색된 스키마
    similar_queries: List[Dict[str, Any]]    # 검색된 Few-shot 예제
    business_terms: List[Dict[str, Any]]     # 검색된 용어집
    context_prompt: str                      # 컨텍스트 프롬프트 문자열

    # ===== Human in the Loop (신규) =====
    waiting_for_human: bool                  # Human 응답 대기 중
    human_intervention: Optional[Dict]       # Human 개입 요청 정보
    human_response: Optional[str]            # Human 응답
```

### 7.2 하위 호환성

```python
# 기존 AgentState와 호환 유지
def migrate_state(old_state: AgentState) -> ExtendedAgentState:
    """기존 상태를 확장 상태로 변환"""
    return ExtendedAgentState(
        # 기존 필드
        **old_state,
        # 신규 필드 기본값
        intent_analysis={},
        intent_confidence=1.0,
        is_ambiguous=False,
        ambiguity_options=[],
        extracted_entities={},
        relevant_schemas=[],
        similar_queries=[],
        business_terms=[],
        context_prompt="",
        waiting_for_human=False,
        human_intervention=None,
        human_response=None,
    )
```

---

## 8. 에러 복구 전략

### 8.1 에러 유형별 복구

| 에러 유형 | 감지 위치 | 복구 전략 |
|----------|----------|----------|
| **모호한 질문** | intent_analysis | Human 명확화 요청 |
| **스키마 오류** | tools (SQL 실행) | context_retrieval 재실행 (범위 확장) |
| **구문 오류** | tools (SQL 실행) | agent 노드 재실행 (에러 피드백) |
| **타임아웃** | should_continue | 간소화된 쿼리로 재시도 |
| **최대 반복** | should_continue | 에러 응답 반환 |

### 8.2 재시도 로직

```python
# app/graphs/agent_graph.py (수정)

def _should_continue(self, state: ExtendedAgentState) -> Literal["continue", "end", "retry_context"]:
    """조건부 분기 (확장)"""

    # 기존 체크 로직...

    # 스키마 오류 감지 시 컨텍스트 재검색
    if state.get("last_error_type") == "schema_error":
        if state.get("context_retry_count", 0) < 2:
            state["context_retry_count"] = state.get("context_retry_count", 0) + 1
            return "retry_context"

    # 기존 로직...
```

---

## 9. 플러그인 아키텍처

### 9.1 Output 플러그인

```python
# app/plugins/output/excel_export.py

class ExcelExportPlugin:
    """Excel 내보내기 플러그인"""

    def execute(self, context: Dict) -> Dict:
        """SQL 결과를 Excel로 변환"""
        from openpyxl import Workbook
        import io

        data = context.get("data", {})
        rows = data.get("rows", [])
        columns = data.get("columns", [])

        wb = Workbook()
        ws = wb.active

        # 헤더
        for col_idx, col_name in enumerate(columns, 1):
            ws.cell(row=1, column=col_idx, value=col_name)

        # 데이터
        for row_idx, row_data in enumerate(rows, 2):
            for col_idx, col_name in enumerate(columns, 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data.get(col_name, ""))

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return {
            "file_bytes": output.getvalue(),
            "filename": context.get("filename", "export.xlsx"),
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
```

### 9.2 Chart 플러그인

```python
# app/plugins/output/chart_generator.py

class ChartGeneratorPlugin:
    """차트 생성 플러그인"""

    def execute(self, context: Dict) -> Dict:
        """SQL 결과를 차트로 변환"""
        import matplotlib.pyplot as plt
        import io

        data = context.get("data", {})
        rows = data.get("rows", [])
        chart_type = context.get("chart_type", "bar")
        x_col = context.get("x_column")
        y_col = context.get("y_column")

        x_values = [row.get(x_col) for row in rows]
        y_values = [row.get(y_col) for row in rows]

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            ax.bar(x_values, y_values)
        elif chart_type == "line":
            ax.plot(x_values, y_values, marker='o')
        elif chart_type == "pie":
            ax.pie(y_values, labels=x_values, autopct='%1.1f%%')

        ax.set_title(context.get("title", "Chart"))
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        plt.close()

        return {
            "chart_data": buffer.getvalue(),
            "format": "image/png"
        }
```

---

## 10. 구현 가이드

### 10.1 파일 구조

```
app/
├── graphs/
│   ├── agent_graph.py              # 🔄 수정 (확장된 그래프)
│   └── nodes/                      # 🆕 신규 폴더
│       ├── __init__.py
│       ├── intent_analysis.py      # 🆕 의도 분석 노드
│       ├── context_retrieval.py    # 🆕 컨텍스트 검색 노드
│       ├── human_clarification.py  # 🆕 Human 명확화 노드
│       └── sql_validate.py         # 🆕 SQL 검증 노드
├── tools/
│   ├── sql_tool.py                 # 기존 유지
│   ├── rag_tool.py                 # 기존 유지 (usage_type='rag_knowledge')
│   ├── calc_tool.py                # 기존 유지
│   └── context_tool.py             # 🆕 SQL 컨텍스트 통합 검색 (usage_type='rag_action')
├── models/
│   └── agent.py                    # 🔄 수정 (ExtendedAgentState)
├── core/
│   └── vector/
│       └── vector_store.py         # 기존 유지 (search_similar_documents 활용)
├── plugins/                        # 🆕 신규 폴더
│   ├── __init__.py
│   ├── base.py                     # 플러그인 기본 클래스
│   ├── manager.py                  # 플러그인 매니저
│   └── output/
│       ├── excel_export.py         # Excel 플러그인
│       └── chart_generator.py      # Chart 플러그인
└── api/
    └── routes/
        └── agent.py                # 🔄 수정 (Human 응답 API)
```

### 10.2 구현 순서

1. **ExtendedAgentState 정의** (`app/models/agent.py`)
2. **context_search_tool 구현** (`app/tools/context_tool.py`, usage_type='rag_action')
3. **신규 노드 구현** (`app/graphs/nodes/`)
4. **agent_graph.py 수정** (노드/엣지 추가, 도구 등록)
5. **tb_docs 데이터 추가** (schema, query_example, glossary with usage_type='rag_action')
6. **API 수정** (Human 응답 처리)
7. **프론트엔드 Human 개입 UI**
8. **플러그인 구현** (Excel, Chart)

### 10.3 _build_graph 수정 예시

```python
# app/graphs/agent_graph.py

def _build_graph(self) -> CompiledStateGraph:
    """확장된 Agent 그래프"""
    workflow = StateGraph(ExtendedAgentState)

    # ===== 노드 추가 =====
    workflow.add_node("intent_analysis", intent_analysis_node)  # 🆕
    workflow.add_node("human_clarification", human_clarification_node)  # 🆕
    workflow.add_node("context_retrieval", context_retrieval_node)  # 🆕
    workflow.add_node("agent", self._agent_node)  # 기존
    workflow.add_node("tools", ToolNode(self.tools))  # 기존
    workflow.add_node("sql_validate", sql_validate_node)  # 🆕 (선택적)

    # ===== 진입점 변경 =====
    workflow.set_entry_point("intent_analysis")  # 🔄 변경

    # ===== 의도 분석 후 분기 =====
    workflow.add_conditional_edges(
        "intent_analysis",
        should_clarify,
        {
            "need_clarification": "human_clarification",
            "proceed": "context_retrieval"
        }
    )

    # ===== Human 명확화 후 =====
    workflow.add_edge("human_clarification", "context_retrieval")

    # ===== 컨텍스트 검색 후 =====
    workflow.add_edge("context_retrieval", "agent")

    # ===== 기존 agent ↔ tools 루프 유지 =====
    workflow.add_conditional_edges(
        "agent",
        self._should_continue,
        {
            "continue": "tools",
            "end": END,
            "retry_context": "context_retrieval"  # 🆕
        }
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=self.checkpointer)
```

---

## 11. 2차 개발 로드맵

### 11.1 Phase 1: 핵심 기능 (2026 Q1)

| 항목 | 설명 | 상태 |
|------|------|------|
| ExtendedAgentState | 확장된 상태 정의 | 설계 완료 |
| intent_analysis 노드 | 의도 분석 | 설계 완료 |
| context_retrieval 노드 | 컨텍스트 검색 | 설계 완료 |
| context_search_tool | 통합 컨텍스트 검색 도구 (usage_type='rag_action') | 설계 완료 |
| tb_docs 확장 | usage_type 컬럼 (rag_knowledge, rag_action) | 설계 완료 |

### 11.2 Phase 2: Human in the Loop (2026 Q2)

| 항목 | 설명 |
|------|------|
| human_clarification 노드 | 명확화 요청 |
| sql_validate 노드 | SQL 검증 + 승인 |
| API 확장 | /respond 엔드포인트 |
| 프론트엔드 UI | Human 개입 UI 컴포넌트 |

### 11.3 Phase 3: 플러그인 (2026 Q3)

| 항목 | 설명 |
|------|------|
| Excel Export | openpyxl 기반 |
| Chart Generator | matplotlib/plotly 기반 |
| CSV Export | 간단한 CSV |
| 플러그인 매니저 | 동적 로드/언로드 |

### 11.4 Phase 4: 고급 기능 (2026 Q4)

| 항목 | 설명 |
|------|------|
| 스트리밍 응답 | SSE 기반 |
| WebSocket Human | 실시간 Human 개입 |
| 캐싱 | Redis 기반 스키마/결과 캐시 |

---

*— 문서 끝 (v3.1) —*
