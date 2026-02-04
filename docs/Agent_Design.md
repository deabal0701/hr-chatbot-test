# Agent 아키텍처 설계서

**MUREUM AI Agent (ReAct 패턴)**

버전 4.0 | 2026년 2월 4일

---

## 목차

1. [개요](#1-개요)
2. [현재 Agent 구조](#2-현재-agent-구조)
3. [Agent 그래프 플로우](#3-agent-그래프-플로우)
4. [노드 설계](#4-노드-설계)
5. [도구(Tools) 설계](#5-도구tools-설계)
6. [상태(State) 설계](#6-상태state-설계)
7. [미들웨어](#7-미들웨어)
8. [서비스 계층](#8-서비스-계층)
9. [설정 관리](#9-설정-관리)
10. [에러 처리](#10-에러-처리)
11. [향후 계획](#11-향후-계획)

---

## 1. 개요

### 1.1 목적

MUREUM Agent는 ReAct (Reason + Act) 패턴을 사용하는 AI Agent입니다.
LLM이 자율적으로 Tool을 선택하고 실행하며, 결과를 관찰한 후 다음 행동을 결정하는 반복적인 패턴을 구현합니다.

### 1.2 핵심 기능

| 기능 | 설명 |
|------|------|
| **ReAct 패턴** | Think → Action → Observation 반복 |
| **Tool 자율 선택** | LLM이 상황에 맞는 Tool 결정 |
| **복합 질문 처리** | 여러 Tool 순차 호출 가능 |
| **멀티턴 대화** | InMemorySaver 기반 세션 관리 |
| **최종 답변 생성** | NL2SQL 응답 프롬프트 공유로 일관된 품질 |

### 1.3 모드 구성

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MUREUM 모드 구성 (3개)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────┐                                 │
│  │ RAG 모드                          │                                 │
│  │  • 정책/규정/가이드 문서 검색      │                                 │
│  └───────────────────────────────────┘                                 │
│                                                                         │
│  ┌───────────────────────────────────┐                                 │
│  │ NL2SQL 모드                       │                                 │
│  │  • 단순 SQL 변환 (빠른 응답)       │                                 │
│  └───────────────────────────────────┘                                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ Agent 모드 (ReAct)                                                │ │
│  │  • ReAct 패턴: agent → tools → agent (루프)                      │ │
│  │  • 복합 질문: SQL + RAG + 계산 조합                               │ │
│  │  • 멀티턴 대화: InMemorySaver 기반                                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 Agent 구조

### 2.1 파일 구조

```
app/
├── graphs/
│   └── agent/                         # Agent 모듈 (패키지)
│       ├── __init__.py
│       ├── graph.py                   # InsightAgentGraph 클래스
│       ├── state.py                   # AgentState 정의
│       ├── nodes/                     # 노드 모듈
│       │   ├── __init__.py
│       │   ├── agent_node.py          # Agent 노드 (LLM Think/Action)
│       │   ├── tools_node.py          # Tool 실행 노드
│       │   └── answer_node.py         # 최종 답변 생성 노드
│       ├── tools/                     # 도구 모듈
│       │   ├── __init__.py
│       │   ├── base.py                # BaseTool 추상 클래스
│       │   ├── sql_tool.py            # SQL 실행 도구
│       │   ├── rag_tool.py            # 문서 검색 도구
│       │   └── calc_tool.py           # 계산기 도구
│       └── middleware/                # 미들웨어 (확장)
│           ├── __init__.py
│           ├── base.py                # 미들웨어 기본 클래스
│           ├── chain.py               # 미들웨어 체인
│           └── pii.py                 # PII 마스킹 (껍데기)
├── api/
│   ├── routes/
│   │   └── agent.py                   # Agent API 라우트
│   └── services/
│       └── agent_service.py           # Agent 서비스 계층
└── models/
    └── agent.py                       # AgentConfig, AgentResponse 등
```

### 2.2 컴포넌트 역할

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| **InsightAgentGraph** | `graph.py` | 그래프 빌드 및 실행 |
| **AgentState** | `state.py` | 그래프 상태 타입 정의 |
| **agent_node** | `nodes/agent_node.py` | LLM Think/Action 결정 |
| **tools_node** | `nodes/tools_node.py` | Tool 실행 |
| **answer_node** | `nodes/answer_node.py` | 최종 답변 생성 |
| **AgentService** | `agent_service.py` | 비즈니스 로직, 설정 로딩 |

---

## 3. Agent 그래프 플로우

### 3.1 그래프 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     InsightAgentGraph (ReAct)                            │
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
│  │  • Think     │                                      │               │
│  │  • Action    │                                      │               │
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
│ [tools]   [answer]                                     │               │
│    │         │                                         │               │
│    │         ▼                                         │               │
│    │  ┌──────────────┐                                │               │
│    │  │   answer     │                                │               │
│    │  │ (답변 생성)   │                                │               │
│    │  └──────┬───────┘                                │               │
│    │         │                                         │               │
│    │         ▼                                         │               │
│    │       END                                         │               │
│    │                                                   │               │
│    ▼                                                   │               │
│  ┌──────────────┐                                      │               │
│  │    tools     │──────────────────────────────────────┘               │
│  │ (Tool 실행)  │                                                      │
│  └──────────────┘                                                      │
│                                                                         │
│  도구 목록:                                                             │
│  • query_database_tool (SQL 실행, NL2SQL 패턴 통합)                    │
│  • search_documents_tool (RAG 검색, usage_type='rag_knowledge')        │
│  • calculate_tool (계산기, AST 기반 안전 평가)                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 실행 흐름

```python
# 1. 사용자 요청
User → /api/v1/agent/search → AgentService

# 2. 설정 로딩
AgentService → settings_config (DB 로드) → AgentConfig

# 3. 그래프 실행
AgentService → InsightAgentGraph.ainvoke(inputs) → 그래프 실행

# 4. ReAct 루프
agent_node → should_continue → tools_node → agent_node (반복)

# 5. 최종 답변
should_continue("answer") → answer_node → END

# 6. 응답 반환
AgentResponse → User
```

### 3.3 조건부 분기 (should_continue)

```python
def should_continue(state: Dict[str, Any]) -> Literal["tools", "answer"]:
    """
    조건부 분기 함수

    - tool_calls가 있으면 "tools" → tools_node로 이동
    - 없으면 "answer" → answer_node로 이동 (최종 답변 생성)
    """
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage):
        has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
        if has_tool_calls:
            return "tools"

    return "answer"
```

---

## 4. 노드 설계

### 4.1 agent_node (LLM Think/Action)

**위치**: `app/graphs/agent/nodes/agent_node.py`

**역할**: LLM을 호출하여 다음 행동을 결정

```python
def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 노드 (ReAct Think/Action)

    흐름:
    1. 반복 횟수 체크 (max_iterations 초과 시 종료)
    2. LLM 인스턴스 생성 + Tool binding
    3. System prompt + messages로 LLM 호출
    4. Tool 호출 결정 또는 최종 답변 생성

    Returns:
        - tool_calls 포함 AIMessage (Tool 호출)
        - content 포함 AIMessage (최종 답변)
    """
```

**System Prompt**: `tb_app_settings`에서 `prompt.agent_system_prompt` 키로 로드

### 4.2 tools_node (Tool 실행)

**위치**: `app/graphs/agent/nodes/tools_node.py`

**역할**: AIMessage의 tool_calls를 실행하고 ToolMessage 반환

```python
TOOL_MAP = {
    "query_database_tool": query_database_tool,
    "search_documents_tool": search_documents_tool,
    "calculate_tool": calculate_tool,
}

def tools_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tools 노드

    흐름:
    1. 마지막 AIMessage에서 tool_calls 추출
    2. 각 tool_call에 대해:
       - TOOL_MAP에서 함수 조회
       - tool_func.invoke(tool_args) 실행
       - ToolMessage 생성
    3. 결과 저장 (generated_sql, sql_result, rag_sources)

    Returns:
        - messages: ToolMessage 리스트
        - tools_used: 사용된 Tool 목록
        - generated_sql, sql_result, rag_sources 등
    """
```

### 4.3 answer_node (최종 답변 생성)

**위치**: `app/graphs/agent/nodes/answer_node.py`

**역할**: Tool 실행 결과를 종합하여 사용자 친화적인 최종 답변 생성

```python
def answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 답변 생성 노드

    특징:
    - NL2SQL의 get_nl2sql_answer_prompt() 프롬프트 공유
    - Tool 결과를 수집하여 LLM에게 요약 요청
    - SQL Tool 결과는 JSON 파싱하여 실제 데이터 추출

    흐름:
    1. messages에서 ToolMessage 수집
    2. SQL Tool 결과는 sql_result 포맷팅
    3. NL2SQL 응답 프롬프트 + Tool 결과로 LLM 호출
    4. 최종 답변 반환
    """
```

**프롬프트 공유**:
- NL2SQL: `generate_answer_node` → `get_nl2sql_answer_prompt()`
- Agent: `answer_node` → `get_nl2sql_answer_prompt()` (동일 프롬프트 사용)

---

## 5. 도구(Tools) 설계

### 5.1 도구 목록

| 도구 | 파일 | 용도 |
|------|------|------|
| **query_database_tool** | `tools/sql_tool.py` | 자연어 → SQL 변환 및 실행 |
| **search_documents_tool** | `tools/rag_tool.py` | 문서/정책 검색 (RAG) |
| **calculate_tool** | `tools/calc_tool.py` | 수학 계산 (AST 기반) |

### 5.2 BaseTool 추상 클래스

**위치**: `app/graphs/agent/tools/base.py`

```python
class BaseTool(ABC):
    """도구 기본 클래스 (Hook 패턴)"""

    def execute(self, **kwargs) -> ToolResult:
        """실행 흐름: before → _execute → after"""
        kwargs = self.before_execute(**kwargs)
        result = self._execute(**kwargs)
        return self.after_execute(result)

    def before_execute(self, **kwargs) -> Dict[str, Any]:
        """전처리 Hook (캐싱, 파라미터 검증 등)"""
        return kwargs

    @abstractmethod
    def _execute(self, **kwargs) -> ToolResult:
        """실제 실행 로직 (서브클래스 구현)"""
        pass

    def after_execute(self, result: ToolResult) -> ToolResult:
        """후처리 Hook (캐싱 저장, 로깅 등)"""
        return result

class ToolResult(BaseModel):
    """도구 실행 결과"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 5.3 SQL 쿼리 도구 (SQLQueryTool)

**위치**: `app/graphs/agent/tools/sql_tool.py`

**특징**: NL2SQL 노드 패턴 통합

```python
class SQLQueryTool(BaseTool):
    """SQL 쿼리 도구 (Enhanced with NL2SQL Pattern)

    Enhanced 모드 흐름:
    1. Schema Retrieval (LLM으로 필요한 테이블 선택)
    2. Few-shot Retrieval (유사 쿼리 예제 검색)
    3. Prompt Build (컨텍스트 기반 프롬프트)
    4. SQL Generate (LLM 호출)
    5. Validate & Execute

    설정:
    - nl2sql.schema_retrieval_enabled: True (Enhanced 모드)
    - nl2sql.schema_retrieval_enabled: False (Legacy 모드)
    """
```

**사용 예시**:
```
"2024년 입사자 수는?" → SELECT COUNT(*) FROM employee WHERE YEAR(hire_date) = 2024
"김철수의 현재 급여는?" → SELECT salary FROM employee WHERE name = '김철수'
```

### 5.4 문서 검색 도구 (DocumentSearchTool)

**위치**: `app/graphs/agent/tools/rag_tool.py`

**특징**: usage_type='rag_knowledge'로 지식 문서만 검색

```python
class DocumentSearchTool(BaseTool):
    """문서 검색 도구 (RAG)

    검색 대상:
    - usage_type='rag_knowledge' (정책, 가이드, FAQ 등)
    - usage_type='rag_action' 문서는 제외 (SQL 컨텍스트용)

    흐름:
    1. 캐시 체크 (before_execute)
    2. vector_store.search_similar_documents() 호출
    3. 결과 포맷팅
    4. 캐시 저장 (after_execute)
    """
```

**사용 예시**:
```
"재택근무 정책이 뭐야?" → 재택근무 정책 문서 반환
"출장 규정은?" → 출장 정책 문서 반환
```

### 5.5 계산기 도구 (CalculatorTool)

**위치**: `app/graphs/agent/tools/calc_tool.py`

**특징**: AST 기반 안전한 수식 평가 (eval() 미사용)

```python
class CalculatorTool(BaseTool):
    """계산기 도구 (AST 기반)

    지원 연산:
    - 기본: +, -, *, /, //, %, **
    - 함수: abs, round, min, max, sum, len, pow, sqrt, ceil, floor

    보안:
    - 화이트리스트 기반 연산자/함수만 허용
    - eval(), exec() 미사용
    """
```

**사용 예시**:
```
"100 * 0.15" → 15.0
"sum([10, 20, 30])" → 60
```

---

## 6. 상태(State) 설계

### 6.1 AgentState

**위치**: `app/graphs/agent/state.py`

```python
class AgentState(TypedDict):
    """ReAct Agent State"""

    # ===== 기본 필드 =====
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 히스토리 (누적)
    question: str                                              # 원본 질문
    session_id: str                                            # 세션 ID (멀티턴)
    request_id: str                                            # 요청 추적 ID

    # ===== ReAct 제어 필드 =====
    iteration_count: int                                       # 현재 반복 횟수
    max_iterations: int                                        # 최대 반복 횟수
    final_answer: str                                          # 최종 답변

    # ===== 설정 =====
    config: AgentConfig                                        # Agent 설정

    # ===== Tool 결과 =====
    last_tool_name: str                                        # 마지막 사용 Tool
    last_tool_result: str                                      # 마지막 Tool 결과

    # ===== SQL Tool 결과 (프론트엔드 표시용) =====
    generated_sql: str                                         # 생성된 SQL
    sql_result: Optional[SQLResult]                            # SQL 실행 결과

    # ===== RAG Tool 결과 =====
    rag_sources: List[Dict]                                    # 검색된 문서 목록

    # ===== 메타데이터 =====
    tools_used: List[str]                                      # 사용된 Tool 목록
    start_time: float                                          # 시작 시간
```

### 6.2 초기 상태 생성

```python
def create_initial_state(
    question: str,
    session_id: str = "unknown",
    request_id: str = "unknown",
    config: AgentConfig = None,
    max_iterations: int = 10,
) -> AgentState:
    """초기 상태 생성"""
    return AgentState(
        messages=[],
        question=question,
        session_id=session_id,
        request_id=request_id,
        iteration_count=0,
        max_iterations=max_iterations,
        final_answer="",
        config=config or AgentConfig(),
        last_tool_name="",
        last_tool_result="",
        generated_sql="",
        sql_result=None,
        rag_sources=[],
        tools_used=[],
        start_time=time.time(),
    )
```

---

## 7. 미들웨어

### 7.1 미들웨어 체인

**위치**: `app/graphs/agent/middleware/`

```python
class MiddlewareChain:
    """미들웨어 체인 (파이프라인 패턴)"""

    async def process_input(self, data: Dict) -> Dict:
        """입력 처리 (순방향)"""
        for middleware in self.middlewares:
            data = await middleware.process_input(data)
        return data

    async def process_output(self, data: Dict) -> Dict:
        """출력 처리 (역방향)"""
        for middleware in reversed(self.middlewares):
            data = await middleware.process_output(data)
        return data
```

### 7.2 현재 미들웨어

| 미들웨어 | 상태 | 설명 |
|----------|------|------|
| **PIIMiddleware** | 껍데기 | PII 마스킹 (향후 구현) |

### 7.3 확장 포인트

```python
# 추가 가능한 미들웨어 예시
class AuditMiddleware(Middleware):
    """감사 로깅 미들웨어"""
    pass

class RateLimitMiddleware(Middleware):
    """요청 제한 미들웨어"""
    pass
```

---

## 8. 서비스 계층

### 8.1 AgentService

**위치**: `app/api/services/agent_service.py`

```python
class AgentService:
    """AI Agent 검색 서비스"""

    async def search(
        self,
        question: str,
        session_id: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        request_id: str = "unknown"
    ) -> AgentResponse:
        """
        Agent 검색 실행

        흐름:
        1. 세션 ID 자동 생성 (없으면)
        2. 설정 로딩 (_resolve_config)
        3. 입력 데이터 구성 (_prepare_inputs)
        4. agent_graph.ainvoke() 실행
        5. AgentResponse 반환
        """

    def _resolve_config(self, request_config, request_id) -> AgentConfig:
        """
        Agent 설정 결정

        보안 정책:
        - 사용자 API 요청의 config 값은 무시됨
        - 모든 설정은 DB(tb_app_settings) 또는 캐시에서만 로드
        - 관리자만 Admin UI를 통해 설정 변경 가능
        """
```

### 8.2 세션 관리 메서드

```python
def get_sessions(self) -> List[str]:
    """활성 세션 목록 조회"""

def get_session_memory(self, session_id: str) -> Optional[Dict]:
    """세션 메모리 조회"""

def delete_session(self, session_id: str) -> Dict:
    """세션 삭제"""

def get_session_metrics(self, session_id: str) -> Dict:
    """세션 메트릭 조회"""
```

---

## 9. 설정 관리

### 9.1 AgentConfig

**위치**: `app/models/agent.py`

```python
class AgentConfig(BaseModel):
    """Agent 설정"""

    max_iterations: int = 10           # 최대 반복 횟수 (1~20)
    llm_model: Optional[str] = None    # LLM 모델 (None=DB 설정 사용)
    llm_temperature: float = 0.0       # LLM 온도 (0.0~2.0)
    enable_memory: bool = True         # 메모리 활성화
    enable_streaming: bool = False     # 스트리밍 (향후)
    enable_intent_analysis: bool = True  # 의도 분석 (향후)
    tools_whitelist: Optional[List[str]] = None  # 허용 도구 목록
    tools_blacklist: Optional[List[str]] = None  # 금지 도구 목록
    timeout_seconds: int = 60          # 타임아웃 (10~300초)
```

### 9.2 DB 설정 (tb_app_settings)

| category | key | 설명 | 기본값 |
|----------|-----|------|--------|
| agent | max_iterations | 최대 반복 횟수 | 10 |
| agent | timeout_seconds | 타임아웃(초) | 60 |
| agent | llm_temperature | LLM 온도 | 0.0 |
| agent | enable_memory | 메모리 활성화 | true |
| agent | enable_streaming | 스트리밍 | false |
| agent | enable_intent_analysis | 의도 분석 | true |
| agent | enabled_tools | 사용 가능 도구 | query_database_tool,search_documents_tool,calculate_tool |
| llm | model | LLM 모델 | gpt-4o-mini |
| prompt | agent_system_prompt | Agent 시스템 프롬프트 | (별도) |

---

## 10. 에러 처리

### 10.1 반복 횟수 초과

```python
if iteration_count >= max_iterations:
    return {
        "messages": [AIMessage(content="죄송합니다. 질문에 대한 답변을 찾는 데 너무 오래 걸리고 있습니다.")],
        "final_answer": "최대 반복 횟수 초과",
    }
```

### 10.2 Tool 실행 오류

```python
try:
    result = tool_func.invoke(tool_args)
except Exception as e:
    tool_messages.append(ToolMessage(
        content=f"Tool execution error: {str(e)}",
        tool_call_id=tool_id,
        name=tool_name,
    ))
```

### 10.3 그래프 실행 오류

```python
try:
    result = await self.graph.ainvoke(initial_state, config=graph_config)
except Exception as e:
    return AgentResponse(
        answer=f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
        success=False,
        error=str(e),
    )
```

---

## 11. 향후 계획

### 11.1 Phase 1: 의도 분석 (미구현)

| 항목 | 설명 | 상태 |
|------|------|------|
| intent_analysis 노드 | 질문 유형 분류, 모호성 감지 | ⏳ 미구현 |
| context_retrieval 노드 | SQL 컨텍스트 자동 주입 | ⏳ 미구현 |
| context_search_tool | SQL 컨텍스트 통합 검색 도구 | ⏳ 미구현 |
| AgentState 확장 | intent_analysis, extracted_entities 필드 | ⏳ 미구현 |

**설계된 의도 분석 노드**:
```python
def intent_analysis_node(state: AgentState) -> AgentState:
    """
    의도 분석 노드 (향후 구현)

    기능:
    - query_type: sql_query | document_search | calculation | general
    - intent: select | aggregate | compare | trend | join | search | calculate
    - 모호성 감지: period | quantity | criteria | table | column
    - 신뢰도 점수 산출 (0.0 ~ 1.0)
    """
```

### 11.2 Phase 2: Human in the Loop (미구현)

| 항목 | 설명 | 상태 |
|------|------|------|
| human_clarification 노드 | 모호성 감지 시 사용자 확인 | ⏳ 미구현 |
| sql_validate 노드 | SQL 검증 + 승인 요청 | ⏳ 미구현 |
| /respond API | Human 응답 처리 | ⏳ 미구현 |
| 프론트엔드 UI | Human 개입 UI 컴포넌트 | ⏳ 미구현 |

**Human 개입 유형**:
| 유형 | 트리거 | 후속 처리 |
|------|--------|----------|
| 명확화 | 모호성 감지 (신뢰도 < 0.7) | 사용자 선택 후 agent 진행 |
| 보안 승인 | 민감 테이블 접근 | 승인 시 실행, 거부 시 종료 |
| 실행 승인 | 대량 조회, 복잡 쿼리 | 승인 시 실행 |
| 에스컬레이션 | 최대 재시도 초과 | 에러 응답 |

### 11.3 Phase 3: 플러그인 아키텍처 (미구현)

| 항목 | 설명 | 상태 |
|------|------|------|
| Excel Export | openpyxl 기반 | ⏳ 미구현 |
| Chart Generator | matplotlib/plotly 기반 | ⏳ 미구현 |
| CSV Export | 간단한 CSV 내보내기 | ⏳ 미구현 |
| 플러그인 매니저 | 동적 로드/언로드 | ⏳ 미구현 |

### 11.4 Phase 4: 고급 기능 (미구현)

| 항목 | 설명 | 상태 |
|------|------|------|
| 스트리밍 응답 | SSE 기반 | ⏳ 미구현 |
| WebSocket Human | 실시간 Human 개입 | ⏳ 미구현 |
| 캐싱 | Redis 기반 스키마/결과 캐시 | ⏳ 미구현 |
| PII 마스킹 | PIIMiddleware 완성 | ⏳ 미구현 |

### 11.5 확장된 AgentState (Phase 1 완료 시)

```python
class ExtendedAgentState(TypedDict):
    """확장된 Agent 상태 (향후)"""

    # 기존 필드 (유지)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    session_id: str
    # ...

    # ===== 의도 분석 (Phase 1) =====
    intent_analysis: Dict[str, Any]       # 의도 분석 결과 전체
    intent_confidence: float              # 신뢰도 (0.0 ~ 1.0)
    is_ambiguous: bool                    # 모호성 여부
    ambiguity_options: List[str]          # 명확화 선택지
    extracted_entities: Dict[str, Any]    # 추출된 엔티티

    # ===== 컨텍스트 검색 (Phase 1) =====
    relevant_schemas: List[Dict]          # 관련 테이블 스키마
    similar_queries: List[Dict]           # Few-shot 예제
    business_terms: List[Dict]            # 비즈니스 용어집
    context_prompt: str                   # Agent에 주입할 컨텍스트

    # ===== Human in the Loop (Phase 2) =====
    waiting_for_human: bool               # Human 응답 대기 중
    human_intervention: Dict[str, Any]    # Human 개입 요청 정보
    human_response: str                   # Human 응답
```

---

## 12. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v3.0 | 2026-01-28 | 초기 설계 문서 작성 |
| v3.1 | 2026-01-29 | usage_type 용어 정리 |
| v3.2 | 2026-01-29 | Phase 1 설계 (미구현) |
| v3.3 | 2026-01-30 | context_retrieval 노드 설계 변경 |
| v4.0 | 2026-02-04 | 현재 코드에 맞게 현행화 (Agent_Design.md 분리) |

### v4.0 주요 변경 사항

1. **파일 구조 업데이트**: `app/graphs/agent/` 패키지 구조 반영
2. **answer_node 추가**: NL2SQL 응답 프롬프트 공유로 최종 답변 생성
3. **SQL Tool 고도화**: NL2SQL 노드 패턴 통합 (Schema/Few-shot Retrieval)
4. **미들웨어 설명 추가**: PIIMiddleware (껍데기)
5. **미구현 기능 정리**: intent_analysis, context_search_tool, Human in the Loop → 향후 계획으로 이동
6. **보안 정책 명시**: AgentConfig는 DB에서만 로드, 사용자 입력 무시

---

*— 문서 끝 (v4.0) —*
