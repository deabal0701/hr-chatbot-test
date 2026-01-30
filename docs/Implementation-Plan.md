# Agent 모드 확장 구현 계획

**Cortex-Agent-Design.md v3.1 기반**

---

## 구현 원칙

1. **점진적 확장**: 기존 Agent 동작을 유지하면서 기능 추가
2. **독립적 단위**: 각 단계는 독립적으로 테스트 가능
3. **롤백 가능**: 문제 발생 시 이전 단계로 복구 가능
4. **하위 호환성**: 기존 API 응답 형식 유지

---

## Phase 1: 기반 구조 (1~2일)

### 1.1 ExtendedAgentState 정의

**목표**: 기존 AgentState를 확장하여 새로운 필드 추가

**파일**: `app/models/agent.py`

```python
# 기존 AgentState 유지 + 신규 필드 추가
class ExtendedAgentState(TypedDict):
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
    intent_analysis: Dict[str, Any]       # 의도 분석 결과
    intent_confidence: float              # 신뢰도 (0.0 ~ 1.0)
    is_ambiguous: bool                    # 모호성 여부

    # ===== 컨텍스트 (신규) =====
    context_prompt: str                   # 검색된 컨텍스트 문자열
```

**작업 내용**:
- [ ] ExtendedAgentState TypedDict 정의
- [ ] 기본값 초기화 함수 작성
- [ ] 기존 AgentState → ExtendedAgentState 마이그레이션 함수

**검증**:
- 기존 Agent 테스트 통과 확인
- 새 필드 접근 테스트

---

### 1.2 context_search_tool 구현

**목표**: SQL 컨텍스트 통합 검색 도구 구현

**파일**: `app/tools/context_tool.py`

```python
@tool
def context_search_tool(
    query: str,
    context_type: Literal["schema", "example", "glossary", "all"] = "all",
    top_k: int = 5
) -> str:
    """SQL 생성에 필요한 컨텍스트를 검색합니다."""
```

**작업 내용**:
- [ ] context_tool.py 파일 생성
- [ ] vector_store.search_similar_documents 호출
- [ ] usage_type='rag_action' 필터 적용
- [ ] 결과 포맷팅 함수 구현

**검증**:
- 단위 테스트: 각 context_type별 검색 결과 확인
- tb_docs에 테스트 데이터 필요 (schema, query_example, glossary)

---

### 1.3 도구 등록

**목표**: agent_graph.py에 context_search_tool 등록

**파일**: `app/graphs/agent_graph.py`

**작업 내용**:
- [ ] _get_tools()에 context_search_tool 추가
- [ ] 기존 도구 목록 유지

**검증**:
- Agent가 context_search_tool 호출 가능 확인
- 기존 도구 정상 동작 확인

---

## Phase 2: 의도 분석 노드 (2~3일)

### 2.1 intent_analysis 노드 구현

**목표**: 질문 의도 분석 및 모호성 감지

**파일**: `app/graphs/nodes/intent_analysis.py`

```python
def intent_analysis_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    의도 분석 노드
    - query_type: sql_query, document_search, calculation, general
    - intent: select, aggregate, compare, trend, join
    - confidence: 0.0 ~ 1.0
    - is_ambiguous: true/false
    """
```

**작업 내용**:
- [ ] nodes 폴더 생성 (`app/graphs/nodes/__init__.py`)
- [ ] intent_analysis.py 구현
- [ ] LLM 프롬프트 작성 (JSON 응답 형식)
- [ ] JSON 파싱 유틸리티 함수

**프롬프트 설계**:
```
당신은 자연어 질문을 분석하는 전문가입니다.
사용자 질문을 분석하여 다음 JSON 형식으로 응답하세요:
{
    "query_type": "sql_query | document_search | calculation | general",
    "intent": "select | aggregate | compare | trend | join",
    "confidence": 0.0~1.0,
    "is_ambiguous": true/false,
    "ambiguity_reason": "모호한 이유 (있을 경우)"
}
```

**검증**:
- 다양한 질문 유형 테스트
- 모호한 질문 감지 테스트 ("최근 입사자", "많은 직원" 등)

---

### 2.2 그래프에 노드 연결 (선택적 분기)

**목표**: intent_analysis 노드를 기존 그래프에 추가 (기존 플로우 유지)

**파일**: `app/graphs/agent_graph.py`

**방식 A: 선택적 활성화** (권장)
```python
def _build_graph(self) -> CompiledStateGraph:
    workflow = StateGraph(ExtendedAgentState)

    # 노드 추가
    workflow.add_node("intent_analysis", intent_analysis_node)
    workflow.add_node("agent", self._agent_node)
    workflow.add_node("tools", ToolNode(self.tools))

    # 설정에 따라 진입점 변경
    if self.config.enable_intent_analysis:
        workflow.set_entry_point("intent_analysis")
        workflow.add_edge("intent_analysis", "agent")
    else:
        workflow.set_entry_point("agent")  # 기존 방식

    # 기존 agent ↔ tools 루프 유지
    workflow.add_conditional_edges("agent", self._should_continue, {...})
    workflow.add_edge("tools", "agent")
```

**작업 내용**:
- [ ] AgentConfig에 `enable_intent_analysis: bool = False` 추가
- [ ] intent_analysis 노드 등록
- [ ] 조건부 진입점 설정
- [ ] intent_analysis → agent 엣지 추가

**검증**:
- `enable_intent_analysis=False`: 기존 동작과 동일
- `enable_intent_analysis=True`: 의도 분석 후 agent 실행
- 로그에서 INTENT 단계 확인

---

## Phase 3: 컨텍스트 검색 노드 (2~3일)

### 3.1 context_retrieval 노드 구현

**목표**: 의도 분석 결과 기반 컨텍스트 자동 검색

**파일**: `app/graphs/nodes/context_retrieval.py`

```python
def context_retrieval_node(state: ExtendedAgentState) -> ExtendedAgentState:
    """
    컨텍스트 검색 노드
    - 의도 기반 검색 전략 결정
    - 스키마/예제/용어집 검색
    - 결과를 context_prompt에 저장
    """
```

**작업 내용**:
- [ ] context_retrieval.py 구현
- [ ] 의도별 검색 전략 매핑
- [ ] 검색 결과를 프롬프트 문자열로 변환
- [ ] state["context_prompt"] 업데이트

**검증**:
- 다양한 의도에 대한 검색 전략 확인
- context_prompt 내용 검증

---

### 3.2 Agent 프롬프트에 컨텍스트 주입

**목표**: 검색된 컨텍스트를 agent 노드 프롬프트에 포함

**파일**: `app/graphs/agent_graph.py`

**작업 내용**:
- [ ] _agent_node에서 state["context_prompt"] 활용
- [ ] 시스템 프롬프트에 컨텍스트 추가

```python
def _agent_node(self, state: ExtendedAgentState) -> ExtendedAgentState:
    context = state.get("context_prompt", "")

    system_prompt = f"""당신은 AI 어시스턴트입니다.

{context if context else ""}

사용 가능한 도구: ...
"""
```

**검증**:
- 컨텍스트가 포함된 프롬프트로 더 정확한 SQL 생성 확인

---

### 3.3 그래프 연결 업데이트

**목표**: intent → context → agent 플로우 완성

```
START → intent_analysis → context_retrieval → agent ↔ tools → END
```

**작업 내용**:
- [ ] context_retrieval 노드 등록
- [ ] intent_analysis → context_retrieval 엣지
- [ ] context_retrieval → agent 엣지

---

## Phase 4: tb_docs 데이터 준비 (1~2일)

### 4.1 테스트 데이터 삽입 스크립트

**목표**: schema, query_example, glossary 데이터 준비

**파일**: `scripts/sql/insert_rag_action_data.sql`

**작업 내용**:
- [ ] 스키마 데이터 (usage_type='rag_action', doc_type='schema')
  - employee 테이블 설명
  - department 테이블 설명
  - 테이블 관계 설명

- [ ] 쿼리 예제 데이터 (usage_type='rag_action', doc_type='query_example')
  - "부서별 직원 수" → GROUP BY 예제
  - "최근 입사자" → DATE 조건 예제
  - "급여 합계" → SUM 예제

- [ ] 용어집 데이터 (usage_type='rag_action', doc_type='glossary')
  - "재직자" → status = 'active'
  - "신입" → hire_date >= CURRENT_DATE - INTERVAL '1 year'
  - "퇴직자" → status = 'resigned'

**검증**:
- 데이터 삽입 후 context_search_tool 테스트

---

## Phase 5: Human in the Loop - 명확화 (3~4일)

### 5.1 human_clarification 노드 구현

**목표**: 모호한 질문에 대해 사용자 선택지 제시

**파일**: `app/graphs/nodes/human_clarification.py`

**작업 내용**:
- [ ] human_clarification_node 구현
- [ ] LangGraph interrupt 패턴 적용
- [ ] human_intervention 응답 구조 정의

---

### 5.2 조건부 분기 구현

**목표**: 모호성 감지 시 human_clarification으로 분기

```python
def should_clarify(state: ExtendedAgentState) -> str:
    if state.get("is_ambiguous") and state.get("intent_confidence", 1.0) < 0.7:
        return "need_clarification"
    return "proceed"
```

**작업 내용**:
- [ ] should_clarify 함수 구현
- [ ] add_conditional_edges 설정
- [ ] human_clarification → context_retrieval 엣지

---

### 5.3 API 확장

**목표**: Human 응답 처리 API 추가

**파일**: `app/api/routes/agent.py`

**작업 내용**:
- [ ] AgentResponse에 waiting_for_human, human_intervention 필드 추가
- [ ] POST /api/v1/agent/respond 엔드포인트 추가
- [ ] resume_with_response 서비스 메서드 구현

---

## Phase 6: SQL 검증 노드 (2~3일) - 선택적

### 6.1 sql_validate 노드 구현

**목표**: SQL 실행 전 보안/대량조회 검증

**파일**: `app/graphs/nodes/sql_validate.py`

**작업 내용**:
- [ ] 민감 테이블 접근 감지
- [ ] LIMIT 없는 SELECT 감지
- [ ] Human 승인 요청 트리거

---

## Phase 7: 플러그인 (별도 일정)

### 7.1 Excel Export 플러그인
### 7.2 Chart Generator 플러그인

---

## 구현 일정 요약

| Phase | 내용 | 예상 기간 | 의존성 |
|-------|------|----------|--------|
| **Phase 1** | 기반 구조 (State, Tool, 등록) | 1~2일 | 없음 |
| **Phase 2** | 의도 분석 노드 | 2~3일 | Phase 1 |
| **Phase 3** | 컨텍스트 검색 노드 | 2~3일 | Phase 2 |
| **Phase 4** | tb_docs 데이터 준비 | 1~2일 | Phase 1 |
| **Phase 5** | Human in the Loop | 3~4일 | Phase 3 |
| **Phase 6** | SQL 검증 노드 | 2~3일 | Phase 5 (선택적) |
| **Phase 7** | 플러그인 | 별도 | Phase 3 이후 |

**총 예상**: Phase 1~4 (핵심): 6~10일 / Phase 5~6 (확장): 5~7일

---

## 검증 체크리스트

### Phase 1 완료 조건
- [ ] 기존 Agent 테스트 모두 통과
- [ ] context_search_tool 단독 호출 성공
- [ ] Agent가 context_search_tool 사용 가능

### Phase 2 완료 조건
- [ ] `enable_intent_analysis=False`일 때 기존 동작과 동일
- [ ] `enable_intent_analysis=True`일 때 의도 분석 로그 출력
- [ ] 모호한 질문에 대해 is_ambiguous=True 반환

### Phase 3 완료 조건
- [ ] 의도별로 다른 검색 전략 적용 확인
- [ ] context_prompt가 Agent 프롬프트에 포함됨
- [ ] SQL 생성 품질 향상 확인 (Few-shot 효과)

### Phase 4 완료 조건
- [ ] tb_docs에 schema/query_example/glossary 데이터 존재
- [ ] usage_type='rag_action' 필터로 검색 가능
- [ ] 임베딩 생성 완료 (indexed=true)

---

## 롤백 계획

각 Phase 완료 후 git tag 생성:
```bash
git tag -a v1.1-phase1 -m "Phase 1: 기반 구조 완료"
git tag -a v1.1-phase2 -m "Phase 2: 의도 분석 노드"
git tag -a v1.1-phase3 -m "Phase 3: 컨텍스트 검색 노드"
```

문제 발생 시:
```bash
git checkout v1.1-phase1  # 이전 안정 버전으로 복구
```

---

*— 구현 계획 v1.0 —*
