# AI Agent 구현 가이드

## 📋 개요

HR Chatbot에 **AI Agent (ReAct 패턴)** 기능을 추가했습니다. 이를 통해 복잡한 멀티스텝 질문을 자율적으로 처리할 수 있습니다.

### 기존 시스템 vs AI Agent

| 기능 | 기존 (NL2SQL/RAG) | AI Agent |
|------|------------------|----------|
| **질문 유형** | 단일 질문만 처리 | 멀티스텝 질문 처리 |
| **도구 선택** | 사전 정의된 분기 | LLM이 자율적으로 선택 |
| **실행 흐름** | 고정된 파이프라인 | 동적 계획 및 실행 |
| **멀티턴 대화** | 미지원 | 세션 기반 메모리 지원 |
| **예시** | "2024년 입사자 수는?" | "2024년 입사자 중 재택근무 정책 준수자의 평균 급여는?" |

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────┐
│         POST /api/v1/agent/search               │
│         (AgentRequest)                          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          HRAgentGraph (ReAct Pattern)           │
│                                                  │
│  ┌──────────┐      ┌──────────────┐            │
│  │  Agent   │──┬──▶│ Should       │            │
│  │  (LLM)   │  │   │ Continue?    │            │
│  └──────────┘  │   └──────┬───────┘            │
│       ▲        │          │                     │
│       │        │          ├─continue─┐          │
│       │        │          │          ▼          │
│       │        │          │   ┌──────────┐     │
│       │        │          │   │  Tools   │     │
│       │        │          │   │ Executor │     │
│       │        │          │   └────┬─────┘     │
│       │        │          │        │           │
│       └────────┴──────────┴────────┘           │
│                            │                     │
│                            └─end──▶ END         │
└─────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│               Tool Registry                      │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ SQL Tool     │  │ RAG Tool     │            │
│  │ (재사용)     │  │ (재사용)     │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  ┌──────────────┐                               │
│  │ Calculator   │                               │
│  │ Tool (신규)  │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

---

## 📂 파일 구조

### 신규 추가된 파일

```
app/
├── tools/                              # 🆕 Tool 레이어
│   ├── __init__.py                     # Tool 레지스트리
│   ├── base.py                         # BaseTool, Validator, Metrics
│   ├── sql_tool.py                     # SQL 쿼리 도구 (기존 재사용)
│   ├── rag_tool.py                     # 문서 검색 도구 (기존 재사용)
│   └── calculator_tool.py              # 계산기 도구 (신규)
│
├── graphs/
│   └── agent_graph.py                  # 🆕 AI Agent Graph (ReAct)
│
├── models/
│   └── agent_schemas.py                # 🆕 Agent 전용 스키마 (Memory, Config)
│
├── api/routes/
│   └── agent.py                        # 🆕 Agent API 엔드포인트
│
└── main.py                             # ✏️ Agent 라우터 등록

tests/
└── test_agent.py                       # 🆕 Agent 테스트
```

---

## 🚀 사용 방법

### 1. 간단한 질문 (기존과 동일)

```bash
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024년 입사자는 몇 명인가?"
  }'
```

**응답:**
```json
{
  "answer": "2024년 입사자는 총 27명입니다.",
  "steps": [
    {
      "step_number": 1,
      "thought": "도구 선택: query_database",
      "action": "query_database",
      "action_input": {"question": "2024년 입사자 수"},
      "observation": "27명 발견"
    }
  ],
  "total_iterations": 1,
  "tools_used": ["query_database"],
  "success": true
}
```

### 2. 복잡한 멀티스텝 질문 (Agent 전용)

```bash
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024년 입사자 중 재택근무 정책을 준수하는 사람은 몇 명이고 평균 급여는?",
    "config": {
      "max_iterations": 15,
      "enable_memory": true
    }
  }'
```

**Agent 실행 과정:**
```
Step 1: query_database("2024년 입사자")
  → 27명 발견

Step 2: search_documents("재택근무 정책")
  → 주 2회 이상 출근 필요

Step 3: query_database("2024년 입사자 중 주 2회 이상 출근자")
  → 15명 발견

Step 4: query_database("해당 15명의 급여")
  → [5000, 5500, 5200, ...]

Step 5: calculate("평균")
  → 5400

Final Answer: "2024년 입사자는 총 27명이며, 재택근무 정책(주 2회 이상 출근)을 준수하는 사람은 15명입니다. 평균 급여는 5,400만원입니다."
```

### 3. 멀티턴 대화

```bash
# 첫 번째 질문
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024년 입사자를 보여줘",
    "session_id": "user123-session456"
  }'

# 후속 질문 (이전 컨텍스트 활용)
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "그 중에서 개발팀만 보여줘",
    "session_id": "user123-session456"
  }'
```

---

## 🔧 확장 포인트

### 1. 새로운 도구 추가

```python
# app/tools/custom_tool.py

from langchain_core.tools import tool
from app.tools.base import BaseTool, ToolResult

class CustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "custom_tool"

    @property
    def description(self) -> str:
        return "Custom tool description for LLM"

    def _execute(self, param: str, **kwargs) -> ToolResult:
        # 실제 로직
        result = do_something(param)

        return ToolResult(
            success=True,
            data=result,
            metadata={"source": "custom"}
        )

# LangChain tool 래퍼
@tool
def custom_tool(param: str) -> str:
    """Custom tool for Agent."""
    tool_instance = CustomTool()
    result = tool_instance.execute(param=param)
    return str(result.data) if result.success else f"Error: {result.error}"
```

**등록:**
```python
# app/tools/__init__.py
from app.tools.custom_tool import CustomTool, custom_tool

AVAILABLE_TOOLS = [
    SQLQueryTool,
    DocumentSearchTool,
    CalculatorTool,
    CustomTool,  # 추가
]
```

**Agent에 추가:**
```python
# app/graphs/agent_graph.py
from app.tools.custom_tool import custom_tool

def _get_tools(self):
    return [
        query_database,
        search_documents,
        calculate,
        custom_tool,  # 추가
    ]
```

### 2. 메모리 영속화 (Redis)

```python
# app/models/agent_schemas.py (수정)

import redis
import json

class SessionMemoryStore:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

    def get_memory(self, session_id: str) -> AgentMemory:
        """Redis에서 메모리 로드"""
        cached = self.redis_client.get(f"session:{session_id}")

        if cached:
            data = json.loads(cached)
            return AgentMemory(**data)
        else:
            memory = AgentMemory(session_id=session_id)
            self._save_memory(memory)
            return memory

    def _save_memory(self, memory: AgentMemory):
        """Redis에 메모리 저장"""
        self.redis_client.setex(
            f"session:{memory.session_id}",
            86400,  # 24시간 TTL
            memory.model_dump_json()
        )
```

### 3. 스트리밍 응답 (SSE)

```python
# app/api/routes/agent.py (추가)

from fastapi.responses import StreamingResponse
import asyncio

@router.post("/search/stream")
async def agent_search_stream(request: AgentRequest):
    """스트리밍 응답"""

    async def generate():
        # Agent 실행 중간 결과를 실시간 전송
        async for event in agent_graph.astream(inputs):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

### 4. 커스텀 Validator

```python
# app/tools/base.py (수정)

class CustomValidator(ToolValidator):
    @staticmethod
    def validate_input(tool_name: str, **kwargs):
        """커스텀 검증 로직"""

        # 예: 민감 정보 필터링
        if tool_name == "SQLQueryTool":
            question = kwargs.get("question", "")
            sensitive_keywords = ["password", "ssn", "secret"]

            for keyword in sensitive_keywords:
                if keyword in question.lower():
                    return False, f"Sensitive keyword detected: {keyword}"

        return True, None
```

---

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/test_agent.py::TestCalculatorTool -v

# 통합 테스트 (DB 필요)
pytest tests/test_agent.py::TestAgentGraph -v

# 전체 테스트
pytest tests/test_agent.py -v
```

---

## 📊 모니터링

### 메트릭 조회

```bash
# 세션별 메트릭
curl "http://localhost:8000/api/v1/agent/sessions/user123-session456/metrics"
```

**응답:**
```json
{
  "session_id": "user123-session456",
  "total_requests": 10,
  "total_iterations": 35,
  "total_tools_called": 42,
  "avg_response_time_ms": 3542.5,
  "success_rate": 0.95,
  "tool_usage": {
    "query_database": 25,
    "search_documents": 12,
    "calculate": 5
  },
  "error_types": {
    "SQLValidationError": 1
  }
}
```

### 도구 통계

```bash
curl "http://localhost:8000/api/v1/agent/tools"
```

---

## 🔒 보안

### SQL Injection 방지

- **ToolValidator**: 입력 검증
- **sql_executor**: 키워드 블랙리스트, 테이블 화이트리스트
- **AST 파싱**: 안전한 계산 (calculator_tool)

### Rate Limiting (확장)

```python
# app/main.py (추가)

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/search")
@limiter.limit("10/minute")  # IP당 분당 10회
async def agent_search(request: AgentRequest):
    ...
```

---

## 📈 성능 최적화

### 1. 캐싱

- **SQL Tool**: 동일 질문 재사용
- **RAG Tool**: 검색 결과 캐싱
- **Schema**: 스키마 설명 캐싱

### 2. 타임아웃

```python
config = AgentConfig(
    timeout_seconds=60,  # 전체 타임아웃
    max_iterations=10    # 최대 반복
)
```

### 3. LLM 모델 선택

```python
# 간단한 질문은 저렴한 모델 사용
config = AgentConfig(
    llm_model="gpt-4o-mini",  # 저렴
    llm_temperature=0.0
)

# 복잡한 질문은 고성능 모델
config = AgentConfig(
    llm_model="gpt-4o",  # 고성능
    llm_temperature=0.0
)
```

---

## 🎯 다음 단계

1. **프로덕션 배포**
   - 환경변수 설정
   - Rate Limiting 추가
   - 모니터링 대시보드

2. **추가 기능**
   - 스트리밍 응답
   - Multi-Agent 협업
   - 플래닝 Agent (복잡한 작업 분해)

3. **성능 개선**
   - Redis 캐싱
   - LLM 응답 캐싱
   - 병렬 도구 실행

---

## 💡 FAQ

**Q: 기존 `/api/v1/search` API는 계속 사용할 수 있나요?**
A: 네, 하위 호환성을 위해 유지됩니다. Agent는 `/api/v1/agent/search`로 별도 제공됩니다.

**Q: Agent가 무한 루프에 빠질 수 있나요?**
A: `max_iterations`와 `timeout_seconds`로 안전장치가 있습니다.

**Q: 비용은 얼마나 증가하나요?**
A: 멀티스텝 질문의 경우 LLM 호출이 증가하므로 비용이 늘어날 수 있습니다. 캐싱과 적절한 모델 선택으로 최적화 가능합니다.

**Q: 새로운 도구를 추가하려면?**
A: `BaseTool`을 상속하여 구현 → `AVAILABLE_TOOLS`에 등록 → Agent Graph에 추가

---

## 📚 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [ReAct 논문](https://arxiv.org/abs/2210.03629)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
