# SSE 스트리밍 단계 그룹핑 구현 가이드

## 1. 문제점

현재 SSE 스트리밍은 **NL2SQL의 14개 노드를 모두 개별 이벤트**로 전송합니다.
사용자 입장에서는 단계가 너무 많아 오히려 혼란스럽습니다.

```
✓ 대화 이력 로드 완료      ← 0초 (즉시)
✓ 질문 분석 완료           ← 0초 (즉시)
✓ 스키마 검색 완료         ← 1초
✓ 유사 질문 검색 완료      ← 0초
✓ 프롬프트 구성 완료       ← 0초
✓ SQL 생성 완료           ← 2초
✓ SQL 검증 완료           ← 0초
✓ SQL 실행 완료           ← 0초
✓ 개인정보 필터링 완료     ← 0초
✓ 답변 생성 완료          ← 8초  ← 전체의 70%!
✓ 이력 저장 완료           ← 0초
처리 중...
```

**목표**: 이것을 **4단계**로 그룹핑하여, 사용자에게 의미 있는 진행 상태만 보여줍니다.

---

## 2. 서버 로그 시간 분석

실제 서버 로그에서 각 노드의 실행 시간을 분석한 결과입니다:

```
16:42:18.727 [load_history]       시작  →  0ms (즉시)
16:42:18.729 [intent_rewrite]     시작  →  LLM 호출 포함, ~0.6s
16:42:19.446 [schema_retrieval]   시작  →  벡터 검색, ~1.0s
16:42:20.420 [fewshot_retrieval]  시작  →  벡터 검색, ~0.1s
16:42:20.487 [prompt_build]       시작  →  문자열 조립, ~0ms
16:42:20.488 [sql_generate]       시작  →  ★ LLM 호출, ~2.0s
16:42:22.560 [validate_sql]       시작  →  파싱만, ~0ms
16:42:22.562 [execute_sql]        시작  →  DB 쿼리, ~0.1s
16:42:22.733 [pii_filter]         시작  →  정규식, ~0ms
16:42:22.735 [generate_answer]    시작  →  ★★ LLM 호출, ~8.0s (전체의 70%!)
16:42:30.794 [save_history]       시작  →  메모리 저장, ~0ms
16:42:30.795 완료
```

**핵심 발견**: LLM을 호출하는 3개 노드가 전체 시간의 95%를 차지합니다.
- `intent_rewrite`: ~0.6초 (LLM)
- `sql_generate`: ~2.0초 (LLM)
- `generate_answer`: ~8.0초 (LLM) ← 가장 오래 걸림

---

## 3. 제안하는 4단계 그룹핑

시간 분석을 기반으로, 14개 노드를 4개 스테이지로 묶습니다:

| 스테이지 | 노드 (포함) | 표시 레이블 | 예상 시간 |
|---------|------------|-----------|----------|
| **1단계** | `load_history`, `intent_rewrite` | 질문 분석 중... / 질문 분석 완료 | ~0.6초 |
| **2단계** | `schema_retrieval`, `fewshot_retrieval`, `prompt_build` | 데이터 검색 준비 중... / 데이터 검색 준비 완료 | ~1.0초 |
| **3단계** | `sql_generate`, `validate_sql`, `execute_sql`, `pii_filter`, `prepare_retry` | SQL 생성 및 실행 중... / SQL 생성 및 실행 완료 | ~2.5초 |
| **4단계** | `generate_answer`, `save_history`, `sql_not_needed`, `handle_error` | 답변 생성 중... / 답변 생성 완료 | ~8.0초 |

사용자가 보게 되는 화면:

```
✓ 질문 분석 완료
✓ 데이터 검색 준비 완료
✓ SQL 생성 및 실행 완료
● 답변 생성 중...          ← 현재 진행 중 (dots 애니메이션)
```

---

## 4. 수정 대상 파일 (총 4개)

| 파일 | 변경 내용 |
|-----|---------|
| `app/models/sse.py` | 스테이지 매핑/레이블 딕셔너리 추가 |
| `app/core/sse/stream_manager.py` | 스테이지 조회 함수 추가 + 불필요 코드 삭제 |
| `app/graphs/nl2sql/graph.py` | `astream_events()` 메서드를 스테이지 기반으로 재작성 |
| `app/graphs/agent/graph.py` | `astream_events()` 메서드를 스테이지 기반으로 재작성 |

> **프론트엔드 변경 없음!** 프론트엔드는 이미 `node_start`/`node_complete` 이벤트를 처리하고 있으므로, 백엔드에서 보내는 이벤트 수만 줄이면 됩니다.

---

## 5. 파일별 상세 변경 가이드

---

### 5-1. `app/models/sse.py` — 스테이지 매핑 추가

**현재 파일 끝 (74행 이후)에 아래 코드를 추가합니다.**

기존 `NL2SQL_NODE_LABELS`, `AGENT_NODE_LABELS` 딕셔너리는 그대로 유지합니다. (삭제하지 마세요. `extract_node_detail()` 등에서 사용할 수 있습니다.)

```python
# ============================================================
# 스테이지 그룹핑 (Stage Grouping)
# ============================================================
# 각 노드가 속하는 스테이지 번호를 정의합니다.
# 스테이지 번호가 같은 노드는 하나의 그룹으로 처리됩니다.

# NL2SQL: 노드 → 스테이지 번호 매핑
NL2SQL_NODE_STAGE = {
    "load_history": 1,       # 1단계: 질문 분석
    "intent_rewrite": 1,     # 1단계: 질문 분석
    "schema_retrieval": 2,   # 2단계: 데이터 검색 준비
    "fewshot_retrieval": 2,  # 2단계: 데이터 검색 준비
    "prompt_build": 2,       # 2단계: 데이터 검색 준비
    "sql_generate": 3,       # 3단계: SQL 생성 및 실행
    "validate_sql": 3,       # 3단계: SQL 생성 및 실행
    "execute_sql": 3,        # 3단계: SQL 생성 및 실행
    "pii_filter": 3,         # 3단계: SQL 생성 및 실행
    "prepare_retry": 3,      # 3단계: SQL 생성 및 실행 (재시도)
    "generate_answer": 4,    # 4단계: 답변 생성
    "save_history": 4,       # 4단계: 답변 생성
    "sql_not_needed": 4,     # 4단계: 답변 생성 (이전 결과 활용)
    "handle_error": 4,       # 4단계: 답변 생성 (에러 처리)
}

# NL2SQL: 스테이지 번호 → 표시 레이블 매핑
NL2SQL_STAGE_LABELS = {
    1: {"start": "질문 분석 중...", "complete": "질문 분석 완료"},
    2: {"start": "데이터 검색 준비 중...", "complete": "데이터 검색 준비 완료"},
    3: {"start": "SQL 생성 및 실행 중...", "complete": "SQL 생성 및 실행 완료"},
    4: {"start": "답변 생성 중...", "complete": "답변 생성 완료"},
}

# Agent: 노드 → 스테이지 번호 매핑
# Agent는 노드가 3개뿐이므로 각 노드 = 각 스테이지
AGENT_NODE_STAGE = {
    "agent": 1,   # 1단계: AI 추론
    "tools": 2,   # 2단계: 도구 실행
    "answer": 3,  # 3단계: 답변 생성
}

# Agent: 스테이지 번호 → 표시 레이블 매핑
AGENT_STAGE_LABELS = {
    1: {"start": "AI 추론 중...", "complete": "AI 추론 완료"},
    2: {"start": "도구 실행 중...", "complete": "도구 실행 완료"},
    3: {"start": "답변 생성 중...", "complete": "답변 생성 완료"},
}
```

#### 왜 이렇게 구현하는가?

- **딕셔너리 2개로 분리**: `NODE_STAGE`는 "이 노드가 몇 단계에 속하는가?"를 알려주고, `STAGE_LABELS`는 "이 단계를 사용자에게 뭐라고 보여줄까?"를 알려줍니다. 역할이 다르므로 분리합니다.
- **`prepare_retry`가 3단계**: SQL 생성이 실패하면 `prepare_retry → fewshot_retrieval → prompt_build → sql_generate` 루프가 돕니다. `prepare_retry`를 3단계에 넣으면, 재시도 중에도 "SQL 생성 및 실행 중..." 표시가 유지됩니다.
- **`sql_not_needed`가 4단계**: intent_rewrite에서 "이전 SQL 결과로 답변 가능"으로 판단하면, schema_retrieval~execute_sql을 건너뛰고 바로 sql_not_needed → save_history로 갑니다. 이때 1단계 → 4단계로 바로 넘어가며, 사용자에게는 "질문 분석 완료 ✓ → 답변 생성 중..."으로 표시됩니다.

---

### 5-2. `app/core/sse/stream_manager.py` — 스테이지 조회 함수 추가 + 불필요 코드 삭제

이 파일은 **추가와 삭제가 모두** 있습니다.

#### A. 삭제할 코드 (16행 ~ 45행)

아래 3개의 딕셔너리를 **전부 삭제**합니다. 더 이상 개별 노드 단위로 다음 노드를 예측하지 않기 때문입니다.

```python
# ===== 삭제 시작 (16행 ~ 45행) =====

# NL2SQL 다음 노드 매핑 (확정적 엣지만, 조건부 엣지는 None)
NL2SQL_NEXT_NODE = {
    "load_history": "intent_rewrite",
    "intent_rewrite": None,
    # ... (중략)
    "prepare_retry": "fewshot_retrieval",
}

# Agent 다음 노드 매핑
AGENT_NEXT_NODE = {
    "agent": None,
    "tools": "agent",
    "answer": None,
}

# 그래프 엔트리 포인트
ENTRY_NODES = {
    "nl2sql": "load_history",
    "agent": "agent",
}

# ===== 삭제 끝 =====
```

#### B. 삭제할 함수 2개 (78행 ~ 94행)

`get_entry_node()`과 `get_next_node()` 함수를 **삭제**합니다. 스테이지 기반에서는 사용하지 않습니다.

```python
# ===== 삭제 시작 (78행 ~ 94행) =====

def get_entry_node(mode: str) -> str:
    """그래프 엔트리 포인트 노드 이름 반환"""
    return ENTRY_NODES.get(mode, "")


def get_next_node(node_name: str, mode: str) -> Optional[str]:
    """현재 노드 완료 후 다음 노드 예측 (확정적 엣지만)"""
    next_map = AGENT_NEXT_NODE if mode == "agent" else NL2SQL_NEXT_NODE
    return next_map.get(node_name)

# ===== 삭제 끝 =====
```

#### C. 추가할 함수 2개 (import 아래에 추가)

14행의 import에 새 딕셔너리를 추가하고, 함수 2개를 추가합니다.

**14행 변경 (import 확장)**:

```python
# 변경 전:
from app.models.sse import AGENT_NODE_LABELS, NL2SQL_NODE_LABELS

# 변경 후:
from app.models.sse import (
    AGENT_NODE_LABELS, NL2SQL_NODE_LABELS,
    NL2SQL_NODE_STAGE, NL2SQL_STAGE_LABELS,
    AGENT_NODE_STAGE, AGENT_STAGE_LABELS,
)
```

**삭제한 딕셔너리/함수 자리에 새 함수 2개 추가**:

```python
def get_node_stage(node_name: str, mode: str) -> int:
    """노드가 속하는 스테이지 번호를 반환합니다.

    Args:
        node_name: LangGraph 노드 이름 (예: "schema_retrieval")
        mode: "agent" 또는 "nl2sql"

    Returns:
        스테이지 번호 (1, 2, 3, 4)
        매핑에 없는 노드이면 0을 반환합니다.

    예시:
        get_node_stage("load_history", "nl2sql")    → 1
        get_node_stage("sql_generate", "nl2sql")    → 3
        get_node_stage("tools", "agent")            → 2
    """
    stage_map = AGENT_NODE_STAGE if mode == "agent" else NL2SQL_NODE_STAGE
    return stage_map.get(node_name, 0)


def get_stage_label(stage: int, phase: str, mode: str) -> str:
    """스테이지 번호에 대한 표시 레이블을 반환합니다.

    Args:
        stage: 스테이지 번호 (1, 2, 3, 4)
        phase: "start" 또는 "complete"
        mode: "agent" 또는 "nl2sql"

    Returns:
        한글 표시 레이블

    예시:
        get_stage_label(1, "start", "nl2sql")     → "질문 분석 중..."
        get_stage_label(3, "complete", "nl2sql")   → "SQL 생성 및 실행 완료"
        get_stage_label(2, "start", "agent")       → "도구 실행 중..."
    """
    labels = AGENT_STAGE_LABELS if mode == "agent" else NL2SQL_STAGE_LABELS
    stage_info = labels.get(stage, {"start": f"단계 {stage} 처리 중...", "complete": f"단계 {stage} 완료"})
    return stage_info.get(phase, f"단계 {stage}")
```

#### 변경 후 `stream_manager.py` 전체 구조

```
import json
from typing import ...
from app.models.sse import (
    AGENT_NODE_LABELS, NL2SQL_NODE_LABELS,
    NL2SQL_NODE_STAGE, NL2SQL_STAGE_LABELS,
    AGENT_NODE_STAGE, AGENT_STAGE_LABELS,
)

def format_sse(...)           # 기존 유지
def get_node_label(...)       # 기존 유지
def get_node_stage(...)       # ★ 새로 추가
def get_stage_label(...)      # ★ 새로 추가
def extract_node_detail(...)  # 기존 유지
```

---

### 5-3. `app/graphs/nl2sql/graph.py` — `astream_events()` 메서드 재작성

**변경 범위**: `astream_events()` 메서드 전체 (266행 ~ 347행)

기존 메서드를 **통째로 교체**합니다. 그 외 코드(`__init__`, `_build_graph`, `ainvoke` 등)는 변경 없습니다.

#### 변경 전 (삭제할 코드): 266행 ~ 347행

```python
    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        NL2SQL SSE 스트리밍 실행
        ...
        """
        from app.core.sse.stream_manager import format_sse, get_node_label, get_entry_node, get_next_node, extract_node_detail
        from app.models.sse import NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent

        start_time = time.time()
        request_id = inputs.get("request_id", "unknown")
        session_id = inputs.get("session_id")
        if not session_id:
            session_id = f"nl2sql-{request_id}"
            inputs["session_id"] = session_id

        initial_state = self._prepare_initial_state(inputs, session_id)

        log_step(logger, request_id, "NL2SQL", "0", "INIT", "NL2SQL SSE 스트리밍 시작", question=inputs["question"], session_id=session_id)

        try:
            config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "run_name": inputs["question"],
            }

            # 엔트리 포인트 node_start 이벤트 전송
            step_count = 0
            entry_node = get_entry_node("nl2sql")
            if entry_node:
                start_label = get_node_label(entry_node, "start", "nl2sql")
                start_event = NodeStartEvent(node=entry_node, message=start_label, step=1)
                yield format_sse("node_start", start_event.model_dump())
                await asyncio.sleep(0)

            # astream으로 노드별 이벤트 스트리밍
            async for chunk in self.graph.astream(initial_state, config=config):
                for node_name, state_update in chunk.items():
                    if node_name.startswith("__"):
                        continue

                    step_count += 1
                    # 노드 완료 이벤트
                    label = get_node_label(node_name, "complete", "nl2sql")
                    detail = extract_node_detail(node_name, state_update, "nl2sql")
                    event = NodeCompleteEvent(node=node_name, message=label, step=step_count, detail=detail)
                    log_step(logger, request_id, "NL2SQL", str(step_count), "SSE", f"노드 완료: {node_name}")
                    yield format_sse("node_complete", event.model_dump())
                    await asyncio.sleep(0)

                    # 다음 노드 시작 이벤트 (확정적 엣지인 경우)
                    next_node = get_next_node(node_name, "nl2sql")
                    if next_node:
                        next_label = get_node_label(next_node, "start", "nl2sql")
                        next_event = NodeStartEvent(node=next_node, message=next_label, step=step_count + 1)
                        yield format_sse("node_start", next_event.model_dump())
                        await asyncio.sleep(0)

            # 최종 상태를 checkpointer에서 가져오기 (reducer 안전 처리)
            final_checkpoint = await self.graph.aget_state(config)
            result = final_checkpoint.values

            response_time_ms = int((time.time() - start_time) * 1000)
            response = self._build_response(result, session_id, response_time_ms)

            log_step(logger, request_id, "NL2SQL", "END", "COMPLETE", "NL2SQL SSE 완료", time_ms=response_time_ms)

            complete_event = CompleteEvent(data=response.model_dump())
            yield format_sse("complete", complete_event.model_dump())

        except Exception as e:
            log_step(logger, request_id, "NL2SQL", "ERR", "SSE", f"NL2SQL SSE 실패: {str(e)}", level="ERROR")

            error_event = ErrorEvent(code="NL2SQL_FAILED", message=f"NL2SQL 실행 중 오류: {str(e)}", detail=str(e))
            yield format_sse("error", error_event.model_dump())
```

#### 변경 후 (새로 넣을 코드): 같은 위치 (266행~)

```python
    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        NL2SQL SSE 스트리밍 실행 (스테이지 그룹핑 방식)

        14개 노드를 4개 스테이지로 그룹핑하여 SSE 이벤트를 전송합니다.
        스테이지가 변경될 때만 node_complete/node_start 이벤트를 보내므로,
        사용자에게는 최대 4단계만 표시됩니다.

        스테이지 전환 알고리즘:
        1. 각 노드가 완료될 때마다 해당 노드의 스테이지 번호를 조회
        2. 현재 스테이지보다 큰 경우에만 이벤트 전송 (forward-only)
        3. forward-only 규칙으로 재시도 루프 시 중복 이벤트 방지

        Args:
            inputs: 요청 데이터 (question, session_id, request_id)

        Yields:
            SSE 포맷 문자열
        """
        from app.core.sse.stream_manager import format_sse, get_node_stage, get_stage_label
        from app.models.sse import NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent

        start_time = time.time()
        request_id = inputs.get("request_id", "unknown")
        session_id = inputs.get("session_id")
        if not session_id:
            session_id = f"nl2sql-{request_id}"
            inputs["session_id"] = session_id

        initial_state = self._prepare_initial_state(inputs, session_id)

        log_step(logger, request_id, "NL2SQL", "0", "INIT", "NL2SQL SSE 스트리밍 시작", question=inputs["question"], session_id=session_id)

        try:
            config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "run_name": inputs["question"],
            }

            # ── 스테이지 추적 변수 ──
            # current_stage: 현재 진행 중인 스테이지 번호 (0 = 아직 시작 전)
            current_stage = 0

            # ── 1단계 node_start 이벤트 전송 (그래프 실행 전) ──
            start_label = get_stage_label(1, "start", "nl2sql")
            start_event = NodeStartEvent(node="stage_1", message=start_label, step=1)
            yield format_sse("node_start", start_event.model_dump())
            await asyncio.sleep(0)
            current_stage = 1

            # ── astream으로 노드별 이벤트 스트리밍 ──
            async for chunk in self.graph.astream(initial_state, config=config):
                for node_name, state_update in chunk.items():
                    # LangGraph 내부 노드 무시 (__start__, __end__ 등)
                    if node_name.startswith("__"):
                        continue

                    # 이 노드가 속하는 스테이지 번호 조회
                    node_stage = get_node_stage(node_name, "nl2sql")

                    # 스테이지가 0이면 매핑에 없는 알 수 없는 노드 → 무시
                    if node_stage == 0:
                        continue

                    # ── forward-only 규칙: 현재보다 큰 스테이지일 때만 이벤트 전송 ──
                    # 왜 forward-only인가?
                    # - prepare_retry → fewshot_retrieval 루프 시,
                    #   fewshot_retrieval(2단계)가 다시 실행됨
                    # - 이때 current_stage는 이미 3 이므로 2 < 3 → 이벤트 전송 안 함
                    # - 사용자에게는 "SQL 생성 및 실행 중..."이 유지됨
                    if node_stage > current_stage:
                        # 현재 스테이지 완료 이벤트
                        complete_label = get_stage_label(current_stage, "complete", "nl2sql")
                        complete_event = NodeCompleteEvent(
                            node=f"stage_{current_stage}",
                            message=complete_label,
                            step=current_stage
                        )
                        yield format_sse("node_complete", complete_event.model_dump())
                        await asyncio.sleep(0)

                        # 새 스테이지 시작 이벤트
                        start_label = get_stage_label(node_stage, "start", "nl2sql")
                        start_event = NodeStartEvent(
                            node=f"stage_{node_stage}",
                            message=start_label,
                            step=node_stage
                        )
                        yield format_sse("node_start", start_event.model_dump())
                        await asyncio.sleep(0)

                        # 현재 스테이지 갱신
                        current_stage = node_stage

                    log_step(logger, request_id, "NL2SQL", str(current_stage), "SSE", f"노드 완료: {node_name} (stage {node_stage})")

            # ── 마지막 스테이지 완료 이벤트 ──
            if current_stage > 0:
                final_label = get_stage_label(current_stage, "complete", "nl2sql")
                final_event = NodeCompleteEvent(
                    node=f"stage_{current_stage}",
                    message=final_label,
                    step=current_stage
                )
                yield format_sse("node_complete", final_event.model_dump())
                await asyncio.sleep(0)

            # ── 최종 상태를 checkpointer에서 가져오기 ──
            # 왜 aget_state를 사용하는가?
            # astream()은 노드별 partial state를 yield하지만,
            # messages 필드는 add_messages reducer를 사용하므로 수동 병합이 위험합니다.
            # aget_state(config)는 InMemorySaver에서 최종 완전한 상태를 가져옵니다.
            final_checkpoint = await self.graph.aget_state(config)
            result = final_checkpoint.values

            response_time_ms = int((time.time() - start_time) * 1000)
            response = self._build_response(result, session_id, response_time_ms)

            log_step(logger, request_id, "NL2SQL", "END", "COMPLETE", "NL2SQL SSE 완료", time_ms=response_time_ms)

            complete_event = CompleteEvent(data=response.model_dump())
            yield format_sse("complete", complete_event.model_dump())

        except Exception as e:
            log_step(logger, request_id, "NL2SQL", "ERR", "SSE", f"NL2SQL SSE 실패: {str(e)}", level="ERROR")

            error_event = ErrorEvent(code="NL2SQL_FAILED", message=f"NL2SQL 실행 중 오류: {str(e)}", detail=str(e))
            yield format_sse("error", error_event.model_dump())
```

#### 핵심 알고리즘 설명 (forward-only 규칙)

```
current_stage = 0

[그래프 시작 전]
  → node_start(stage=1, "질문 분석 중...")
  → current_stage = 1

[load_history 완료] → node_stage = 1, current_stage = 1 → 1 > 1? NO → 이벤트 없음
[intent_rewrite 완료] → node_stage = 1, current_stage = 1 → 1 > 1? NO → 이벤트 없음
[schema_retrieval 완료] → node_stage = 2, current_stage = 1 → 2 > 1? YES!
  → node_complete(stage=1, "질문 분석 완료")      ← 이전 스테이지 완료
  → node_start(stage=2, "데이터 검색 준비 중...")   ← 새 스테이지 시작
  → current_stage = 2

[fewshot_retrieval 완료] → node_stage = 2, current_stage = 2 → 2 > 2? NO → 이벤트 없음
[prompt_build 완료] → node_stage = 2, current_stage = 2 → 2 > 2? NO → 이벤트 없음
[sql_generate 완료] → node_stage = 3, current_stage = 2 → 3 > 2? YES!
  → node_complete(stage=2, "데이터 검색 준비 완료")
  → node_start(stage=3, "SQL 생성 및 실행 중...")
  → current_stage = 3

... (이하 동일 패턴) ...

[그래프 종료 후]
  → node_complete(stage=4, "답변 생성 완료")  ← 마지막 스테이지 완료
```

#### 재시도 루프가 발생하는 경우

```
[sql_generate 완료] → stage 3, current=2 → 3>2 YES → 이벤트 전송, current=3
[validate_sql 완료] → stage 3, current=3 → 3>3 NO → 이벤트 없음
[prepare_retry 완료] → stage 3, current=3 → 3>3 NO → 이벤트 없음  ← 재시도!
[fewshot_retrieval 완료] → stage 2, current=3 → 2>3 NO → 이벤트 없음  ← 뒤로 안 감!
[prompt_build 완료] → stage 2, current=3 → 2>3 NO → 이벤트 없음
[sql_generate 완료] → stage 3, current=3 → 3>3 NO → 이벤트 없음  ← 두 번째 시도
[validate_sql 완료] → stage 3, current=3 → 3>3 NO → 이벤트 없음
[execute_sql 완료] → stage 3, current=3 → 3>3 NO → 이벤트 없음
[generate_answer 완료] → stage 4, current=3 → 4>3 YES → 이벤트 전송, current=4
```

`forward-only` 덕분에 재시도 루프에서 스테이지가 뒤로 돌아가지 않습니다.
사용자에게는 "SQL 생성 및 실행 중..."이 계속 표시되어 자연스럽습니다.

---

### 5-4. `app/graphs/agent/graph.py` — `astream_events()` 메서드 재작성

**변경 범위**: `astream_events()` 메서드 전체 (163행 ~ 285행)

NL2SQL과 동일한 패턴이지만, mode가 `"agent"`이고 전/후처리(미들웨어, 초기상태 생성)가 다릅니다.

#### 변경 전 (삭제할 코드): 163행 ~ 285행

```python
    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Agent SSE 스트리밍 실행
        ...
        """
        from app.core.sse.stream_manager import format_sse, get_node_label, get_entry_node, get_next_node, extract_node_detail
        from app.models.sse import NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent
        # ... (기존 코드 전체)
```

#### 변경 후 (새로 넣을 코드): 같은 위치 (163행~)

```python
    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Agent SSE 스트리밍 실행 (스테이지 그룹핑 방식)

        Agent 노드(agent, tools, answer)를 스테이지로 그룹핑하여 SSE 이벤트를 전송합니다.
        Agent는 agent → tools → agent 루프가 있으므로, forward-only 규칙 대신
        tools→agent 전환 시에도 이벤트를 보내야 합니다.

        Args:
            inputs: 요청 데이터 (question, session_id, request_id, config)

        Yields:
            SSE 포맷 문자열
        """
        from app.core.sse.stream_manager import format_sse, get_node_stage, get_stage_label
        from app.models.sse import NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent

        request_id = inputs.get("request_id", str(uuid.uuid4())[:8])
        question = inputs["question"]
        session_id = inputs.get("session_id", f"session-{request_id}")
        config = inputs.get("config", AgentConfig())
        max_iterations = inputs.get("max_iterations", config.max_iterations or 10)
        start_time = time.time()

        log_step(logger, request_id, "AGENT", "0", "INIT", "ReAct Agent SSE 스트리밍 시작", question=truncate_text(question, 50))

        # 미들웨어 입력 처리
        middleware_input = {"question": question, "session_id": session_id, "request_id": request_id, "config": config}
        processed_input = await self.middleware.process_input(middleware_input)

        # 초기 상태 생성
        initial_state = create_initial_state(
            question=processed_input["question"],
            session_id=processed_input["session_id"],
            request_id=processed_input["request_id"],
            config=processed_input.get("config", config),
            max_iterations=max_iterations,
        )
        initial_state["messages"] = [HumanMessage(content=question)]

        try:
            graph_config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "run_name": question,
            }

            # ── 스테이지 추적 변수 ──
            current_stage = 0

            # ── 1단계 node_start 이벤트 전송 ──
            start_label = get_stage_label(1, "start", "agent")
            start_event = NodeStartEvent(node="stage_1", message=start_label, step=1)
            yield format_sse("node_start", start_event.model_dump())
            await asyncio.sleep(0)
            current_stage = 1

            # ── astream으로 노드별 이벤트 스트리밍 ──
            async for chunk in self.graph.astream(initial_state, config=graph_config):
                for node_name, state_update in chunk.items():
                    if node_name.startswith("__"):
                        continue

                    node_stage = get_node_stage(node_name, "agent")
                    if node_stage == 0:
                        continue

                    # Agent는 루프(agent→tools→agent)가 있으므로
                    # 스테이지가 다르면 항상 이벤트 전송 (forward-only 아님)
                    if node_stage != current_stage:
                        # 현재 스테이지 완료
                        complete_label = get_stage_label(current_stage, "complete", "agent")
                        complete_event = NodeCompleteEvent(
                            node=f"stage_{current_stage}",
                            message=complete_label,
                            step=current_stage
                        )
                        yield format_sse("node_complete", complete_event.model_dump())
                        await asyncio.sleep(0)

                        # 새 스테이지 시작
                        start_label = get_stage_label(node_stage, "start", "agent")
                        start_event = NodeStartEvent(
                            node=f"stage_{node_stage}",
                            message=start_label,
                            step=node_stage
                        )
                        yield format_sse("node_start", start_event.model_dump())
                        await asyncio.sleep(0)

                        current_stage = node_stage

                    log_step(logger, request_id, "AGENT", str(current_stage), "SSE", f"노드 완료: {node_name} (stage {node_stage})")

            # ── 마지막 스테이지 완료 이벤트 ──
            if current_stage > 0:
                final_label = get_stage_label(current_stage, "complete", "agent")
                final_event = NodeCompleteEvent(
                    node=f"stage_{current_stage}",
                    message=final_label,
                    step=current_stage
                )
                yield format_sse("node_complete", final_event.model_dump())
                await asyncio.sleep(0)

            # ── 최종 상태 가져오기 ──
            final_checkpoint = await self.graph.aget_state(graph_config)
            result = final_checkpoint.values

            execution_time_ms = int((time.time() - start_time) * 1000)
            final_answer = self._extract_final_answer(result)

            # 미들웨어 출력 처리
            middleware_output = {
                "request_id": request_id,
                "answer": final_answer,
                "generated_sql": result.get("generated_sql", ""),
                "sql_result": result.get("sql_result"),
                "rag_sources": result.get("rag_sources", []),
            }
            processed_output = await self.middleware.process_output(middleware_output)

            response = AgentResponse(
                answer=processed_output.get("answer", final_answer),
                steps=self._extract_steps(result),
                total_iterations=result.get("iteration_count", 0),
                tools_used=result.get("tools_used", []),
                success=True,
                error=None,
                metadata={
                    "request_id": request_id,
                    "session_id": session_id,
                    "execution_time_ms": execution_time_ms,
                    "generated_sql": result.get("generated_sql", ""),
                    "sql_result": result.get("sql_result"),
                },
                session_id=session_id,
            )

            log_step(logger, request_id, "AGENT", "END", "COMPLETE", "ReAct Agent SSE 완료", iterations=result.get('iteration_count', 0), time_ms=execution_time_ms)

            complete_event = CompleteEvent(data=response.model_dump())
            yield format_sse("complete", complete_event.model_dump())

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_step(logger, request_id, "AGENT", "END", "ERROR", "ReAct Agent SSE 실패", level="ERROR", error=str(e))

            error_event = ErrorEvent(code="AGENT_FAILED", message=f"Agent 실행 중 오류: {str(e)}", detail=str(e))
            yield format_sse("error", error_event.model_dump())
```

#### NL2SQL과 Agent의 차이점

| 항목 | NL2SQL | Agent |
|-----|--------|-------|
| 스테이지 전환 조건 | `node_stage > current_stage` (forward-only) | `node_stage != current_stage` (양방향) |
| 이유 | 재시도 루프에서 뒤로 돌아가면 안 됨 | agent→tools→agent 루프에서 매번 표시 필요 |
| 스테이지 수 | 4개 | 3개 |

---

## 6. 변경하지 않는 파일들

다음 파일들은 **변경이 필요 없습니다**:

| 파일 | 이유 |
|-----|-----|
| `app/api/routes/agent.py` | SSE endpoint가 이미 있음. `astream_events()`를 호출할 뿐 |
| `app/api/routes/search.py` | 위와 동일 |
| `app/api/services/agent_service.py` | `search_stream()`이 이미 `astream_events()` 위임 |
| `app/api/services/nl2sql_service.py` | 위와 동일 |
| `frontend/src/api/sse.js` | `node_start`/`node_complete` 이벤트 처리 이미 구현 |
| `frontend/src/store/modules/chat.js` | `onNodeStart`/`onNodeComplete` 콜백 이미 구현 |
| `frontend/src/components/user/UserChatMessage.vue` | 스트리밍 UI 이미 구현 |
| `app/middleware/history.py` | SSE 스트리밍 히스토리 저장 이미 구현 |

**핵심**: 프론트엔드는 이벤트 이름(`node_start`, `node_complete`)이 동일하므로, 백엔드에서 보내는 이벤트 수만 줄어들 뿐 프론트엔드 코드 변경이 필요 없습니다.

---

## 7. 검증 방법

### Backend 검증 (curl)

```bash
# NL2SQL SSE 테스트
curl -X POST "http://localhost:19090/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "부서별 직원 수는?", "mode": "nl2sql"}' \
  --no-buffer
```

**기대 출력** (4단계만 표시):

```
event: node_start
data: {"type":"node_start","node":"stage_1","message":"질문 분석 중...","step":1,...}

event: node_complete
data: {"type":"node_complete","node":"stage_1","message":"질문 분석 완료","step":1,...}

event: node_start
data: {"type":"node_start","node":"stage_2","message":"데이터 검색 준비 중...","step":2,...}

event: node_complete
data: {"type":"node_complete","node":"stage_2","message":"데이터 검색 준비 완료","step":2,...}

event: node_start
data: {"type":"node_start","node":"stage_3","message":"SQL 생성 및 실행 중...","step":3,...}

event: node_complete
data: {"type":"node_complete","node":"stage_3","message":"SQL 생성 및 실행 완료","step":3,...}

event: node_start
data: {"type":"node_start","node":"stage_4","message":"답변 생성 중...","step":4,...}

event: node_complete
data: {"type":"node_complete","node":"stage_4","message":"답변 생성 완료","step":4,...}

event: complete
data: {"type":"complete","data":{"query":"...","answer":"...","query_type":"nl2sql",...}}
```

### Frontend 검증

NL2SQL 모드로 질문을 보내면 화면에 아래와 같이 표시됩니다:

```
✓ 질문 분석 완료
✓ 데이터 검색 준비 완료
✓ SQL 생성 및 실행 완료
● 답변 생성 중...          ← typing dots 애니메이션
```

### 기존 endpoint 동작 확인

기존 non-streaming endpoint가 정상 동작하는지도 반드시 확인하세요:

```bash
# 기존 endpoint (변경 없음)
curl -X POST "http://localhost:19090/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "부서별 직원 수는?", "mode": "nl2sql"}'
```

---

## 8. 변경 요약 체크리스트

- [ ] `app/models/sse.py` — 파일 끝에 스테이지 매핑 4개 딕셔너리 추가
- [ ] `app/core/sse/stream_manager.py` — import 확장 + 함수 2개 추가 + 딕셔너리 3개 삭제 + 함수 2개 삭제
- [ ] `app/graphs/nl2sql/graph.py` — `astream_events()` 메서드 전체 교체
- [ ] `app/graphs/agent/graph.py` — `astream_events()` 메서드 전체 교체
- [ ] curl로 SSE 스트리밍 테스트
- [ ] 프론트엔드 화면 확인 (4단계 표시)
- [ ] 기존 non-streaming endpoint 동작 확인
