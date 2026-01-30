# Agent 모드 확장 설계서

**기존 InsightAgentGraph 기반 고도화**

버전 3.3 | 2026년 1월 30일

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
- **SQL 컨텍스트 도구**: 스키마, Few-shot, 용어집 RAG 검색 (Agent가 직접 호출)
- **SQL 검증 노드**: 구문/스키마/보안 검증 (선택적)
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
│  ┌───────────────────────────────────┐                                 │
│  │ RAG 모드 (유지)                    │                                 │
│  │  • 정책/규정/가이드 문서 검색      │                                 │
│  └───────────────────────────────────┘                                 │
│                                                                         │
│  ┌───────────────────────────────────┐                                 │
│  │ NL2SQL 모드 (유지)                 │                                 │
│  │  • 단순 SQL 변환 (빠른 응답)       │                                 │
│  └───────────────────────────────────┘                                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Agent 모드 (확장)                                                  │ │
│  │  • 기존: ReAct 패턴 (agent → tools → agent 루프)                  │ │
│  │  • 추가: 의도 분석, Human 개입, SQL 검증                           │ │
│  │  • 추가 도구: context_search_tool (SQL 컨텍스트 통합 검색)         │ │
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

### 3.1 확장된 그래프 플로우 (v3.3)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     확장된 InsightAgentGraph v3.3                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐                                                              │
│  │   START      │                                                              │
│  └──────┬───────┘                                                              │
│         │                                                                       │
│         ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │   intent_analysis (의도 분석 노드)                                       │   │
│  │   • 질문 유형 분류 (SQL 질의 / 단순 질문 / 복합 질문)                    │   │
│  │   • 엔티티 추출: 테이블, 컬럼, 조건값                                    │   │
│  │   • 모호성 감지: 기간/범위/기준이 불명확한 경우                          │   │
│  │   • 신뢰도 점수 산출 (0.0 ~ 1.0)                                        │   │
│  └──────┬───────────────────────────────────────────────────────────────────┘   │
│         │                                                                       │
│         ▼                                                                       │
│  ┌──────────────┐         ┌───────────────────────────────────────────────┐    │
│  │ 명확화       │───YES──▶│  human_clarification (Human 명확화 노드)       │    │
│  │ 필요?        │         │  • interrupt 패턴으로 실행 중단                 │    │
│  │              │         │  • 사용자에게 선택지 제시                       │    │
│  └──────┬───────┘         └──────────────────────┬────────────────────────┘    │
│         │ NO                                      │ (사용자 선택 후 재개)       │
│         ▼                                         ▼                            │
│  ┌──────────────┐                                                              │
│  │    agent     │◀─────────────────────────────────────┐                       │
│  │  (LLM 결정)  │                                      │                       │
│  │  ※ 기존 유지 │                                      │                       │
│  │  ※ context_search_tool 사용 가능                   │                       │
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
│  ✅ context_search_tool (SQL 컨텍스트 통합 검색, usage_type='rag_action')      │
│     • context_type: "schema" | "example" | "glossary" | "all"                 │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 확장 요소 요약

| 구분 | 기존 | 추가 |
|------|------|------|
| **노드** | agent, tools | intent_analysis, human_clarification |
| **엣지** | agent↔tools 루프 | intent→human/agent |
| **도구** | 3개 | +1개 (context_search_tool) |
| **상태** | AgentState | ExtendedAgentState (기존 확장) |

### 3.3 usage_type 구분

| usage_type | 용도 | doc_type | 사용 도구 |
|------------|------|----------|----------|
| `rag_knowledge` | 문서 기반 답변 | policy, guide, faq, job_posting | search_documents_tool |
| `rag_action` | SQL 컨텍스트 | schema, query_example, glossary | context_search_tool |

### 3.4 Human in the Loop 개입 지점

| 개입 유형 | 트리거 노드 | 트리거 조건 | 후속 처리 |
|----------|------------|------------|----------|
| **명확화** | intent_analysis | 모호성 감지 (신뢰도 < 0.7) | agent로 진행 |
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

---

## 5. 추가 도구(Tools) 설계

### 5.1 도구 목록

| 도구 | 용도 | usage_type | 파일 |
|------|------|------------|------|
| **query_database_tool** (기존) | SQL 실행 | - | `app/tools/sql_tool.py` |
| **search_documents_tool** (기존) | RAG 검색 | `rag_knowledge` | `app/tools/rag_tool.py` |
| **calculate_tool** (기존) | 계산기 | - | `app/tools/calc_tool.py` |
| **context_search_tool** (신규) | SQL 컨텍스트 통합 검색 | `rag_action` | `app/tools/context_tool.py` |

### 5.2 SQL 컨텍스트 검색 도구 (통합)

> **설계 근거**: 스키마, Few-shot, 용어집 검색은 모두 동일한 `vector_store`와 `tb_docs` 테이블을 사용하므로 하나의 도구로 통합하여 LLM 도구 선택 복잡도를 낮추고 프롬프트 토큰을 절약합니다.
>
> **v3.3 변경**: context_retrieval 노드 대신 Agent가 직접 이 도구를 호출하여 필요한 컨텍스트를 검색합니다.

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
    # 구현 내용...
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
# app/graphs/agent_graph.py

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

(기존 내용 유지)

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

    # ===== Human in the Loop (신규) =====
    waiting_for_human: bool                  # Human 응답 대기 중
    human_intervention: Optional[Dict]       # Human 개입 요청 정보
    human_response: Optional[str]            # Human 응답
```

---

## 8. 에러 복구 전략

(기존 내용 유지)

---

## 9. 플러그인 아키텍처

(기존 내용 유지)

---

## 10. 구현 가이드

### 10.1 파일 구조

```
app/
├── graphs/
│   ├── agent_graph.py              # 수정 (확장된 그래프)
│   └── nodes/                      # 신규 폴더
│       ├── __init__.py
│       └── intent_analysis.py      # 의도 분석 노드
├── tools/
│   ├── sql_tool.py                 # 기존 유지
│   ├── rag_tool.py                 # 기존 유지 (usage_type='rag_knowledge')
│   ├── calc_tool.py                # 기존 유지
│   └── context_tool.py             # SQL 컨텍스트 통합 검색 (usage_type='rag_action')
├── models/
│   └── agent.py                    # 수정 (ExtendedAgentState)
├── core/
│   └── vector/
│       └── vector_store.py         # 기존 유지 (search_similar_documents 활용)
└── api/
    └── routes/
        └── agent.py                # 수정 (Human 응답 API)
```

### 10.2 구현 순서

1. **ExtendedAgentState 정의** (`app/models/agent.py`)
2. **context_search_tool 구현** (`app/tools/context_tool.py`, usage_type='rag_action')
3. **intent_analysis 노드 구현** (`app/graphs/nodes/intent_analysis.py`)
4. **agent_graph.py 수정** (노드/엣지 추가, 도구 등록)
5. **tb_docs 데이터 추가** (schema, query_example, glossary with usage_type='rag_action')
6. **API 수정** (Human 응답 처리)
7. **프론트엔드 Human 개입 UI**

### 10.3 _build_graph 수정 예시 (v3.3)

```python
# app/graphs/agent_graph.py

def _build_graph(self) -> CompiledStateGraph:
    """확장된 Agent 그래프 (v3.3)"""
    workflow = StateGraph(ExtendedAgentState)

    # ===== 노드 추가 =====
    workflow.add_node("intent_analysis", self._intent_analysis_wrapper)
    workflow.add_node("agent", self._agent_node)  # 기존
    workflow.add_node("tools", ToolNode(self.tools))  # 기존

    # ===== 진입점: intent_analysis =====
    workflow.set_entry_point("intent_analysis")

    # ===== 의도 분석 후 agent로 =====
    workflow.add_edge("intent_analysis", "agent")

    # ===== 기존 agent ↔ tools 루프 유지 =====
    workflow.add_conditional_edges(
        "agent",
        self._should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=self.checkpointer)
```

---

## 11. 2차 개발 로드맵

### 11.1 Phase 1: 핵심 기능 (2026 Q1)

| 항목 | 설명 | 상태 | 파일 |
|------|------|------|------|
| ExtendedAgentState | 확장된 상태 정의 | ✅ 구현 완료 | `app/graphs/agent_graph.py` |
| intent_analysis 노드 | 의도 분석 (query_type, intent, 모호성 감지) | ✅ 구현 완료 | `app/graphs/nodes/intent_analysis.py` |
| context_search_tool | 통합 컨텍스트 검색 도구 (usage_type='rag_action') | ✅ 구현 완료 | `app/tools/context_tool.py` |
| AgentConfig 확장 | enable_intent_analysis | ✅ 구현 완료 | `app/models/agent.py` |
| agent_graph.py 수정 | 노드/엣지 추가, 그래프 플로우 변경 | ✅ 구현 완료 | `app/graphs/agent_graph.py` |
| tb_docs 확장 | usage_type 컬럼 (rag_knowledge, rag_action) | ⏳ 데이터 준비 필요 | - |

### 11.2 Phase 2: Human in the Loop (2026 Q2)

| 항목 | 설명 | 상태 |
|------|------|------|
| human_clarification 노드 | 명확화 요청 | ⏳ 미구현 |
| sql_validate 노드 | SQL 검증 + 승인 | ⏳ 미구현 |
| API 확장 | /respond 엔드포인트 | ⏳ 미구현 |
| 프론트엔드 UI | Human 개입 UI 컴포넌트 | ⏳ 미구현 |

### 11.3 Phase 3: 플러그인 (2026 Q3)

| 항목 | 설명 | 상태 |
|------|------|------|
| Excel Export | openpyxl 기반 | ⏳ 미구현 |
| Chart Generator | matplotlib/plotly 기반 | ⏳ 미구현 |
| CSV Export | 간단한 CSV | ⏳ 미구현 |
| 플러그인 매니저 | 동적 로드/언로드 | ⏳ 미구현 |

### 11.4 Phase 4: 고급 기능 (2026 Q4)

| 항목 | 설명 | 상태 |
|------|------|------|
| 스트리밍 응답 | SSE 기반 | ⏳ 미구현 |
| WebSocket Human | 실시간 Human 개입 | ⏳ 미구현 |
| 캐싱 | Redis 기반 스키마/결과 캐시 | ⏳ 미구현 |

---

## 12. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v3.0 | 2026-01-28 | 초기 설계 문서 작성 |
| v3.1 | 2026-01-29 | usage_type 용어 정리 (rag_knowledge, rag_action) |
| v3.2 | 2026-01-29 | Phase 1 구현 완료: ExtendedAgentState, intent_analysis, context_retrieval, context_search_tool |
| v3.3 | 2026-01-30 | context_retrieval 노드 삭제, Agent가 context_search_tool 직접 호출 방식으로 변경 |

---

*— 문서 끝 (v3.3) —*
