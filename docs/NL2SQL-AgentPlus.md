# 엔터프라이즈 NL2SQL 시스템 기술 설계서

**LangChain 1.x & LangGraph 기반 아키텍처**

버전 1.0 | 2026년 1월

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 설계](#2-아키텍처-설계)
3. [에이전트 상세 설계](#3-에이전트-상세-설계)
4. [LangGraph 워크플로우 설계](#4-langgraph-워크플로우-설계)
5. [상태 관리 및 데이터 모델](#5-상태-관리-및-데이터-모델)
6. [API 명세](#6-api-명세)
7. [보안 및 확장성](#7-보안-및-확장성)
8. [구현 가이드](#8-구현-가이드)

---

## 1. 시스템 개요

### 1.1 목적

본 문서는 엔터프라이즈급 자연어-SQL 변환(NL2SQL) 시스템의 기술 설계를 기술합니다. 이 시스템은 비즈니스 사용자가 자연어로 데이터베이스를 조회할 수 있게 하며, 최적화된 SQL 쿼리를 자동 생성하고 결과를 사람이 읽기 쉬운 형태로 제공합니다.

### 1.2 설계 원칙

- **에이전틱 아키텍처**: 전문화된 역할을 가진 멀티 에이전트 협업 구조
- **자가 수정**: 반복적 검증 및 자동 오류 수정 루프
- **확장성**: 무상태(Stateless) 에이전트 설계를 통한 수평 확장
- **보안**: 행 수준 보안(RLS), 쿼리 인젝션 방지, 감사 로깅
- **확장 가능성**: 커스텀 데이터베이스 어댑터 및 LLM 제공자를 위한 플러그인 아키텍처

### 1.3 기술 스택

| 구성요소 | 기술 |
|---------|------|
| 프레임워크 | LangChain 1.x, LangGraph 0.2+ |
| LLM 제공자 | Claude 3.5 Sonnet (주), GPT-4o (대체) |
| 벡터 저장소 | Chroma / Pinecone / Weaviate |
| 캐시 | Redis 클러스터 (쿼리 캐시, 세션 상태) |
| 메시지 큐 | Apache Kafka (이벤트 스트리밍) |
| 모니터링 | LangSmith, Prometheus, Grafana |

---

## 2. 아키텍처 설계

### 2.1 상위 수준 아키텍처

본 시스템은 LangGraph로 오케스트레이션되는 6개의 전문화된 에이전트로 구성된 멀티 에이전트 에이전틱 워크플로우 패턴을 따릅니다. 각 에이전트는 NL2SQL 파이프라인의 특정 단계를 담당합니다.

#### 2.1.1 에이전트 파이프라인 흐름

워크플로우는 오류 수정을 위한 피드백 루프와 함께 다음 순서로 진행됩니다:

1. 질문 이해 / 의도 분석 에이전트
2. 컨텍스트 및 스키마 검색 에이전트
3. SQL 생성 에이전트
4. SQL 검증 및 수정 에이전트 (#3과 반복 루프)
5. 실행 에이전트
6. 결과 해석 에이전트

```
┌─────────────────────────────────────────────────────────────────┐
│                           Agents                                 │
│  ┌──────────┐    ┌─────────────────────────────────────────┐    │
│  │          │    │  질문 이해 / 의도 분석 에이전트          │    │
│  │  User    │───▶│                                         │    │
│  │  Input   │    └─────────────────┬───────────────────────┘    │
│  └──────────┘                      │                             │
│                                    ▼                             │
│               ┌─────────────────────────────────────────┐       │
│               │  컨텍스트 & 스키마 검색 에이전트         │◀──┐  │
│               └─────────────────┬───────────────────────┘   │  │
│                                 │                            │  │
│                                 ▼                            │  │
│               ┌─────────────────────────────────────────┐   │  │
│               │       SQL 생성 에이전트                  │   │  │
│               └─────────────────┬───────────────────────┘   │  │
│                                 │                            │  │
│                                 ▼                            │  │
│               ┌─────────────────────────────────────────┐   │  │
│               │   SQL 검증 & 수정 에이전트              │───┘  │
│               └─────────────────┬───────────────────────┘      │
│                                 │                               │
│                                 ▼                               │
│               ┌─────────────────────────────────────────┐      │
│               │         실행 에이전트                    │      │
│               └─────────────────┬───────────────────────┘      │
│                                 │          ┌────────────┐      │
│                                 │          │   결과     │      │
│                                 └─────────▶│   해석     │─▶End │
│                                            │  에이전트  │      │
│                                            └────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 컴포넌트 아키텍처

| 레이어 | 컴포넌트 | 책임 |
|-------|---------|------|
| API 레이어 | FastAPI, WebSocket | 요청 처리, 스트리밍 |
| 오케스트레이션 | LangGraph StateGraph | 워크플로우 관리 |
| 에이전트 레이어 | 6개 전문 에이전트 | NL2SQL 처리 |
| 데이터 레이어 | 벡터 DB, RDBMS | 스키마, 쿼리 저장 |
| 인프라 | Redis, Kafka, K8s | 캐싱, 메시징, 스케일링 |

---

## 3. 에이전트 상세 설계

### 3.1 질문 이해 / 의도 분석 에이전트

**목적:** 사용자 자연어 입력을 분석하여 의도, 엔티티, 쿼리 요구사항을 추출합니다.

#### 입출력 명세

| 방향 | 필드 | 설명 |
|-----|------|------|
| 입력 | `user_query: str` | 자연어 질문 |
| 입력 | `conversation_history: List` | 이전 대화 컨텍스트 |
| 출력 | `intent: IntentType` | QUERY/AGGREGATE/JOIN/DDL |
| 출력 | `entities: List[Entity]` | 추출된 테이블/컬럼 참조 |
| 출력 | `filters: List[Filter]` | WHERE 조건 |
| 출력 | `aggregations: List[Agg]` | GROUP BY, ORDER BY |

#### 주요 책임

- 의도 분류 (SELECT, INSERT, UPDATE, 집계, 조인)
- 테이블/컬럼 식별을 위한 개체명 인식(NER)
- 시간 표현 파싱 (예: "지난 달" → 날짜 범위)
- 모호성 감지 및 명확화 요청 생성

### 3.2 컨텍스트 및 스키마 검색 에이전트

**목적:** RAG를 사용하여 관련 데이터베이스 스키마 및 컨텍스트 정보를 검색합니다.

#### RAG 전략

- 하이브리드 검색: Dense 임베딩 + BM25 희소 검색
- 관련 테이블 탐색을 위한 스키마 그래프 순회
- Few-shot 예제를 위한 쿼리 이력 유사도 매칭
- 비즈니스 용어집 용어 해석

#### 벡터 인덱스 구조

| 인덱스명 | 콘텐츠 | 임베딩 모델 |
|---------|-------|------------|
| schema_index | 테이블/컬럼 DDL | text-embedding-3-large |
| query_history_index | 자연어-SQL 쌍 | text-embedding-3-large |
| glossary_index | 비즈니스 용어 | text-embedding-3-large |

### 3.3 SQL 생성 에이전트

**목적:** 분석된 의도와 검색된 스키마 컨텍스트를 기반으로 SQL 쿼리를 생성합니다.

#### 생성 전략

- 유사 쿼리 예제를 활용한 Few-shot 프롬프팅
- 복잡한 조인을 위한 Chain-of-thought 추론
- 데이터베이스 방언별 SQL 생성 (MySQL, PostgreSQL, Oracle)
- 쿼리 최적화 힌트 주입

### 3.4 SQL 검증 및 수정 에이전트

**목적:** 생성된 SQL을 검증하고 피드백 루프를 통해 자동 수정을 제공합니다.

#### 검증 항목

| 검증 유형 | 설명 | 조치 |
|----------|------|------|
| 구문 검증 | SQL 파서 검증 | 자동 수정 |
| 스키마 검증 | 테이블/컬럼 존재 여부 확인 | 대안 제안 |
| 보안 스캔 | 인젝션 패턴 탐지 | 거부 및 로깅 |
| 성능 검사 | EXPLAIN 플랜 분석 | 힌트/인덱스 추가 |
| 권한 검사 | 사용자 접근 권한 검증 | 거부 시 차단 |

#### 수정 루프 로직

SQL 수정을 위한 최대 3회 반복. 3회 시도 후에도 검증 실패 시 사람의 검토로 에스컬레이션하거나 사용자에게 상세 오류 메시지를 반환합니다.

### 3.5 실행 에이전트

**목적:** 검증된 SQL 쿼리를 대상 데이터베이스에 안전하게 실행합니다.

#### 안전 메커니즘

- 쿼리 타임아웃 강제 (설정 가능, 기본값 30초)
- 행 제한 강제 (기본값 10,000행)
- SELECT 쿼리에 대한 읽기 전용 트랜잭션 모드
- 서킷 브레이커 패턴을 적용한 커넥션 풀링
- 모든 실행 쿼리에 대한 감사 로깅

### 3.6 결과 해석 에이전트

**목적:** 원시 쿼리 결과를 사람이 읽기 쉬운 인사이트와 시각화로 변환합니다.

#### 출력 형식

- 결과의 자연어 요약
- 구조화된 데이터 테이블 (JSON, CSV 내보내기)
- 데이터 특성에 기반한 차트 추천
- 이상 탐지 및 인사이트 강조

---

## 4. LangGraph 워크플로우 설계

### 4.1 StateGraph 정의

LangGraph 워크플로우는 타입화된 상태 관리와 검증 루프를 위한 조건부 엣지를 가진 StateGraph로 구현됩니다.

#### 그래프 상태 스키마

```python
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class NL2SQLState(TypedDict):
    # 입력
    user_query: str
    conversation_history: Annotated[list, add_messages]
    
    # 의도 분석 출력
    intent: Optional[str]
    entities: List[dict]
    filters: List[dict]
    
    # 스키마 검색 출력
    relevant_schemas: List[dict]
    similar_queries: List[dict]
    
    # SQL 생성 출력
    generated_sql: Optional[str]
    sql_dialect: str
    
    # 검증 출력
    is_valid: bool
    validation_errors: List[str]
    correction_count: int
    
    # 실행 출력
    query_results: Optional[List[dict]]
    execution_time_ms: int
    
    # 해석 출력
    natural_response: str
    visualization_config: Optional[dict]
```

### 4.2 그래프 구성

```python
def create_nl2sql_graph() -> StateGraph:
    graph = StateGraph(NL2SQLState)
    
    # 노드 추가
    graph.add_node("intent_analysis", intent_analysis_agent)
    graph.add_node("schema_retrieval", schema_retrieval_agent)
    graph.add_node("sql_generation", sql_generation_agent)
    graph.add_node("sql_validation", sql_validation_agent)
    graph.add_node("sql_execution", sql_execution_agent)
    graph.add_node("result_interpretation", result_interpretation_agent)
    
    # 엣지 정의
    graph.add_edge(START, "intent_analysis")
    graph.add_edge("intent_analysis", "schema_retrieval")
    graph.add_edge("schema_retrieval", "sql_generation")
    graph.add_edge("sql_generation", "sql_validation")
    
    # 검증 루프를 위한 조건부 엣지
    graph.add_conditional_edges(
        "sql_validation",
        validation_router,
        {
            "regenerate": "sql_generation",
            "execute": "sql_execution",
            "fail": END
        }
    )
    
    graph.add_edge("sql_execution", "result_interpretation")
    graph.add_edge("result_interpretation", END)
    
    return graph.compile()
```

### 4.3 조건부 라우팅 로직

```python
def validation_router(state: NL2SQLState) -> str:
    """검증 결과에 따른 라우팅."""
    if state["is_valid"]:
        return "execute"
    
    if state["correction_count"] >= 3:
        # 최대 재시도 횟수 초과
        return "fail"
    
    # 수정 횟수 증가 및 재생성
    return "regenerate"
```

### 4.4 체크포인팅 및 영속성

LangGraph는 장시간 실행 워크플로우와 대화 연속성을 위한 영구적 체크포인팅을 지원합니다.

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 체크포인트 저장소 설정
checkpointer = PostgresSaver.from_conn_string(
    conn_string="postgresql://user:pass@host:5432/nl2sql"
)

# 체크포인팅으로 그래프 컴파일
app = graph.compile(checkpointer=checkpointer)

# 대화 추적을 위한 thread_id로 실행
config = {"configurable": {"thread_id": "user_session_123"}}
result = app.invoke(initial_state, config)
```

---

## 5. 상태 관리 및 데이터 모델

### 5.1 핵심 데이터 모델

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class IntentType(str, Enum):
    SELECT = "SELECT"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    SUBQUERY = "SUBQUERY"
    DDL = "DDL"

class Entity(BaseModel):
    name: str
    entity_type: str  # TABLE, COLUMN, VALUE
    confidence: float = Field(ge=0.0, le=1.0)
    resolved_name: Optional[str] = None

class Filter(BaseModel):
    column: str
    operator: str  # =, >, <, LIKE, IN, BETWEEN
    value: Any
    is_temporal: bool = False

class QueryResult(BaseModel):
    sql: str
    columns: List[str]
    rows: List[dict]
    row_count: int
    execution_time_ms: int
    cached: bool = False

class AuditLog(BaseModel):
    timestamp: datetime
    user_id: str
    session_id: str
    natural_query: str
    generated_sql: str
    execution_status: str
    response_time_ms: int
```

### 5.2 스키마 메타데이터 모델

```python
class TableMetadata(BaseModel):
    table_name: str
    schema_name: str
    description: str
    columns: List["ColumnMetadata"]
    primary_keys: List[str]
    foreign_keys: List["ForeignKey"]
    row_count_estimate: int
    last_analyzed: datetime

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    is_nullable: bool
    description: str
    sample_values: List[str]
    business_terms: List[str]  # 연결된 용어집 용어
```

### 5.3 캐싱 전략

| 캐시 유형 | 저장소 | TTL | 무효화 |
|----------|-------|-----|-------|
| 스키마 캐시 | Redis Hash | 1시간 | DDL 변경 이벤트 |
| 쿼리 결과 캐시 | Redis String | 5분 | 테이블 업데이트 이벤트 |
| 임베딩 캐시 | Redis Hash | 24시간 | 스키마 변경 |
| 세션 상태 | Redis Hash | 30분 | 명시적 로그아웃 |

---

## 6. API 명세

### 6.1 REST API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|-------|-----------|------|
| POST | `/api/v1/query` | NL2SQL 쿼리 실행 |
| POST | `/api/v1/query/stream` | 쿼리 결과 스트리밍 (SSE) |
| GET | `/api/v1/schema/{db_id}` | 데이터베이스 스키마 조회 |
| GET | `/api/v1/history` | 쿼리 이력 조회 |
| POST | `/api/v1/feedback` | 쿼리 피드백 제출 |
| WS | `/ws/v1/chat` | 채팅용 WebSocket |

### 6.2 요청/응답 형식

#### 쿼리 요청

```json
{
  "query": "2024년 4분기 지역별 총 매출을 보여줘",
  "database_id": "sales_db",
  "options": {
    "max_rows": 1000,
    "timeout_seconds": 30,
    "include_sql": true,
    "visualization": true
  },
  "context": {
    "session_id": "sess_abc123",
    "user_timezone": "Asia/Seoul"
  }
}
```

#### 쿼리 응답

```json
{
  "request_id": "req_xyz789",
  "status": "success",
  "natural_response": "2024년 4분기 지역별 총 매출은...",
  "generated_sql": "SELECT region, SUM(amount)...",
  "data": {
    "columns": ["region", "total_sales"],
    "rows": [{"region": "APAC", "total_sales": 1250000}],
    "row_count": 5
  },
  "visualization": {
    "type": "bar_chart",
    "config": {}
  },
  "metadata": {
    "execution_time_ms": 245,
    "cache_hit": false
  }
}
```

---

## 7. 보안 및 확장성

### 7.1 보안 아키텍처

#### 인증 및 인가

- 엔터프라이즈 IdP와 OAuth 2.0 / OIDC 연동
- 리프레시 토큰을 사용한 JWT 기반 세션 관리
- 데이터베이스 수준 권한 상속이 있는 RBAC
- 행 수준 보안(RLS) 정책 적용

#### SQL 인젝션 방지

- 파라미터화된 쿼리 생성 (문자열 연결 금지)
- 실행 전 SQL AST 검증
- 블랙리스트 패턴 (DROP, TRUNCATE, 시스템 테이블)
- 쿼리 복잡도 제한 (조인 깊이, 서브쿼리 중첩)

### 7.2 확장성 설계

#### 수평 확장 전략

| 컴포넌트 | 확장 방법 | 메트릭 트리거 |
|---------|----------|--------------|
| API 서버 | K8s HPA (CPU/메모리) | CPU > 70% |
| 에이전트 워커 | KEDA (큐 길이) | 큐 > 100 메시지 |
| 벡터 DB | 테넌트별 샤딩 | 인덱스 크기 > 10GB |
| Redis 캐시 | Redis 클러스터 모드 | 메모리 > 80% |

#### 성능 목표

| 메트릭 | 목표 | SLA |
|-------|------|-----|
| 종단간 지연시간 (P95) | < 3초 | 99.5% |
| 쿼리 정확도 | > 90% | 월간 |
| 시스템 가용성 | 99.9% | 연간 |
| 동시 사용자 | 1,000명 이상 | 피크 부하 |

---

## 8. 구현 가이드

### 8.1 프로젝트 구조

```
nl2sql-enterprise/
├── src/
│   ├── agents/
│   │   ├── intent_analysis.py
│   │   ├── schema_retrieval.py
│   │   ├── sql_generation.py
│   │   ├── sql_validation.py
│   │   ├── sql_execution.py
│   │   └── result_interpretation.py
│   ├── graph/
│   │   ├── workflow.py
│   │   ├── state.py
│   │   └── routers.py
│   ├── models/
│   │   ├── schema.py
│   │   ├── query.py
│   │   └── response.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── vector_store.py
│   │   ├── database_connector.py
│   │   └── cache_service.py
│   ├── api/
│   │   ├── routes.py
│   │   └── websocket.py
│   └── config/
│       └── settings.py
├── tests/
├── docker/
├── k8s/
└── docs/
```

### 8.2 주요 의존성

```txt
# requirements.txt
langchain>=0.3.0
langgraph>=0.2.0
langchain-anthropic>=0.2.0
langchain-openai>=0.2.0
langchain-chroma>=0.1.0
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.9.0
sqlalchemy>=2.0.0
redis>=5.0.0
sqlparse>=0.5.0
asyncpg>=0.29.0
```

### 8.3 에이전트 구현 예제

```python
# src/agents/intent_analysis.py
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ..models.schema import IntentAnalysisResult

class IntentAnalysisAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0
        )
        self.parser = PydanticOutputParser(
            pydantic_object=IntentAnalysisResult
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_SYSTEM_PROMPT),
            ("human", "{query}")
        ])
        self.chain = self.prompt | self.llm | self.parser
    
    async def analyze(self, state: NL2SQLState) -> NL2SQLState:
        result = await self.chain.ainvoke({
            "query": state["user_query"]
        })
        return {
            **state,
            "intent": result.intent,
            "entities": result.entities,
            "filters": result.filters
        }
```

### 8.4 배포 구성

```yaml
# docker-compose.yml (개발 환경)
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://...
    depends_on:
      - redis
      - chroma
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
```

### 8.5 모니터링 및 관측성

LLM 관측성을 위해 LangSmith를 통합하고, 인프라 모니터링을 위해 표준 Prometheus/Grafana 스택을 사용합니다.

```python
# LangSmith 추적 활성화
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "nl2sql-production"

# 커스텀 메트릭
from prometheus_client import Counter, Histogram

query_counter = Counter(
    'nl2sql_queries_total',
    '총 NL2SQL 쿼리 수',
    ['status', 'intent_type']
)

latency_histogram = Histogram(
    'nl2sql_latency_seconds',
    '쿼리 지연시간 분포',
    buckets=[0.5, 1, 2, 3, 5, 10]
)
```

---

## 부록 A: 용어집

| 용어 | 정의 |
|-----|------|
| NL2SQL | 자연어를 SQL로 변환 - 사람의 언어를 데이터베이스 쿼리로 변환 |
| LangGraph | 상태 기반 멀티 액터 워크플로우 구축을 위한 LangChain 라이브러리 |
| RAG | 검색 증강 생성 - 외부 지식으로 LLM을 강화하는 기법 |
| StateGraph | 타입화된 상태 관리가 있는 LangGraph 그래프 유형 |
| 에이전틱 | 목표 달성을 위해 자율적으로 행동할 수 있는 AI 시스템 |

---

## 부록 B: 참조 아키텍처 다이어그램

본 시스템 아키텍처는 다음 에이전트 파이프라인을 갖춘 AWS Text2SQL 에이전틱 워크플로우 패턴을 따릅니다:

```
사용자 입력 → 질문 이해 에이전트 → 컨텍스트 및 스키마 검색 에이전트 
    → SQL 생성 에이전트 ↔ SQL 검증 및 수정 에이전트 (루프) 
    → 실행 에이전트 → 결과 해석 에이전트 → 종료
```

핵심 설계 요소는 SQL 생성과 검증 에이전트 간의 반복적 피드백 루프를 포함하며, 이는 엔터프라이즈급 정확도 요구사항에 필수적인 자가 수정 기능을 구현합니다.

---

*— 문서 끝 —*
