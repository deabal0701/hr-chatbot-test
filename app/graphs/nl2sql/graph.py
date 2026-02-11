"""
NL2SQL 검색 그래프 (LangGraph)

위치: app/graphs/nl2sql/graph.py

그래프 흐름 (멀티턴 대화 + 의도 분석 + PII 필터 지원):
    load_history → intent_rewrite → should_route_after_intent
                                     ├─ sql_needed → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                     │                                                                                      ├─ execute → execute_sql → should_continue_after_execute
                                     │                                                                                      │                            ├─ answer → pii_filter → generate_answer → save_history → END
                                     │                                                                                      │                            ├─ retry → prepare_retry → fewshot_retrieval
                                     │                                                                                      │                            └─ error → handle_error → END
                                     │                                                                                      ├─ retry → prepare_retry → fewshot_retrieval
                                     │                                                                                      └─ error → handle_error → END
                                     └─ sql_not_needed → answer_from_history_node → save_history → END

노드:
- load_history: 이전 대화 이력 로드 (멀티턴)
- intent_rewrite: 의도 분석 + 질문 재작성 (멀티턴 핵심 노드)
- sql_not_needed: 이전 SQL 결과에서 답변 생성 (SQL 실행 없이)
- schema_retrieval: 질문 분석하여 필요한 테이블 스키마만 로드
- fewshot_retrieval: Few-shot 예제 검색
- prompt_build: 스키마 + Few-shot + 이전 대화 이력 + DB 가이드라인 조합
- sql_generate: LLM 호출만 수행
- validate_sql: SQL 안전성 및 유효성 검증
- execute_sql: SQL 실행
- pii_filter: SQL 결과에서 PII 감지/마스킹 (LLM 전송 전 개인정보 보호)
- generate_answer: 결과를 자연어 답변으로 변환
- save_history: 현재 대화를 이력에 저장 (멀티턴, sql_result_summary 포함)
- handle_error: 오류 처리
- prepare_retry: 재시도 상태 업데이트 (retry_count 증가)
"""
from typing import Any, AsyncGenerator, Dict, List, Optional
import asyncio
import time

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

from app.models.search import SearchResponse
from app.utils.logger import setup_logger, log_step

# LangSmith traceable (조건부 import)
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    traceable = None

# State import (로컬 모듈)
from app.graphs.nl2sql.state import NL2SQLState, create_initial_state

# 노드 함수 import (로컬 모듈)
from app.graphs.nl2sql.nodes import (
    schema_retrieval_node,
    fewshot_retrieval_node,
    prompt_build_node,
    sql_generate_node,
    validate_sql_node,
    execute_sql_node,
    pii_filter_node,
    generate_answer_node,
    handle_error_node,
    prepare_retry_node,
    should_execute,
    should_continue_after_execute,
    load_history_node,
    save_history_node,
    # 의도 분석 + 질문 재작성 노드
    intent_rewrite_node,
    answer_from_history_node,
    should_route_after_intent,
)

logger = setup_logger(__name__)


class NL2SQLGraph:
    """NL2SQL 검색 그래프 (LangGraph)

    엔터프라이즈급 NL2SQL 시스템
    - SRP 준수: 각 노드가 단일 책임
    - Few-shot 예제 검색
    - 쿼리 오류 시 재시도 기능
    - DB 타입 자동 감지 (PostgreSQL, Oracle)
    - Admin UI 프롬프트 설정 반영
    - 멀티턴 대화 지원 (InMemorySaver)
    """

    def __init__(self):
        # Checkpointer (멀티턴 대화)
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

        log_step(logger, "SYSTEM", "NL2SQL", "INIT", "SETUP", "NL2SQLGraph 초기화 완료 (멀티턴 지원)", level="DEBUG")

    def _build_graph(self) -> CompiledStateGraph:
        """그래프 구성

        흐름 (멀티턴 대화 + 의도 분석 + PII 필터 지원):
        load_history → intent_rewrite → should_route_after_intent
                                         ├─ sql_needed → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                         │                                                                                       ├─ execute → execute_sql → should_continue_after_execute
                                         │                                                                                       │                            ├─ answer → pii_filter → generate_answer → save_history → END
                                         │                                                                                       │                            ├─ retry → prepare_retry → fewshot_retrieval
                                         │                                                                                       │                            └─ error → handle_error → END
                                         │                                                                                       ├─ retry → prepare_retry → fewshot_retrieval
                                         │                                                                                       └─ error → handle_error → END
                                         └─ sql_not_needed → answer_from_history_node → save_history → END
        """
        workflow = StateGraph(NL2SQLState)

        # 노드 등록 (멀티턴 노드 + 의도 분석 노드 포함)
        workflow.add_node("load_history", load_history_node)
        workflow.add_node("intent_rewrite", intent_rewrite_node)  # 의도 분석 + 질문 재작성
        workflow.add_node("sql_not_needed", answer_from_history_node)  # 이전 결과에서 답변 (SQL 불필요)
        workflow.add_node("schema_retrieval", schema_retrieval_node)
        workflow.add_node("fewshot_retrieval", fewshot_retrieval_node)
        workflow.add_node("prompt_build", prompt_build_node)
        workflow.add_node("sql_generate", sql_generate_node)
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("pii_filter", pii_filter_node)
        workflow.add_node("generate_answer", generate_answer_node)
        workflow.add_node("save_history", save_history_node)
        workflow.add_node("handle_error", handle_error_node)
        workflow.add_node("prepare_retry", prepare_retry_node)

        # 순차 실행 흐름 정의 (load_history로 시작)
        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "intent_rewrite")

        # 조건부 분기 0: 의도 분석 후 (SQL 필요 vs SQL 불필요)
        workflow.add_conditional_edges(
            "intent_rewrite",
            should_route_after_intent,
            {
                "sql_needed": "schema_retrieval",  # SQL 실행 필요 → 기존 흐름
                "sql_not_needed": "sql_not_needed"  # 이전 결과에서 답변 가능
            }
        )

        # sql_not_needed → save_history → END
        workflow.add_edge("sql_not_needed", "save_history")

        # SQL 실행 흐름 (기존)
        workflow.add_edge("schema_retrieval", "fewshot_retrieval")
        workflow.add_edge("fewshot_retrieval", "prompt_build")
        workflow.add_edge("prompt_build", "sql_generate")
        workflow.add_edge("sql_generate", "validate_sql")

        # 조건부 분기 1: SQL 검증 후 (재시도 포함)
        workflow.add_conditional_edges(
            "validate_sql",
            should_execute,
            {
                "execute": "execute_sql",
                "retry": "prepare_retry",  # 검증 실패 → 재시도 준비 → fewshot
                "error": "handle_error"
            }
        )

        # 조건부 분기 2: SQL 실행 후 (실행 오류 재시도)
        workflow.add_conditional_edges(
            "execute_sql",
            should_continue_after_execute,
            {
                "answer": "pii_filter",    # 실행 성공 → PII 필터 → 답변 생성
                "retry": "prepare_retry",  # 실행 오류 → 재시도 준비 → fewshot
                "error": "handle_error"
            }
        )

        # pii_filter → generate_answer (PII 마스킹 후 LLM 호출)
        workflow.add_edge("pii_filter", "generate_answer")

        # prepare_retry → fewshot_retrieval
        workflow.add_edge("prepare_retry", "fewshot_retrieval")

        # generate_answer → save_history → END (멀티턴)
        workflow.add_edge("generate_answer", "save_history")
        workflow.add_edge("save_history", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=self.checkpointer)

    def _prepare_initial_state(self, inputs: Dict[str, Any], session_id: str) -> NL2SQLState:
        """초기 상태 준비 (멀티턴 대화 지원)

        checkpoint에서 이전 conversation_history를 로드하여 멀티턴 대화 유지
        """
        # 설정에서 max_turns 로드
        from app.core.config.settings_config import settings_config
        max_turns = settings_config.get_value("nl2sql", "multiturn_max_turns", 5)

        # checkpoint에서 이전 conversation_history 로드
        existing_history = []
        request_id = inputs.get("request_id", "unknown")
        try:
            config: RunnableConfig = {"configurable": {"thread_id": session_id}}
            checkpoint = self.checkpointer.get(config)

            # 디버그: checkpoint 구조 확인
            log_step(logger, request_id, "NL2SQL", "0", "CHECKPOINT", "checkpoint 조회", level="DEBUG", session_id=session_id, exists=checkpoint is not None)

            if checkpoint:
                log_step(logger, request_id, "NL2SQL", "0", "CHECKPOINT", "checkpoint keys", level="DEBUG", keys=list(checkpoint.keys()) if checkpoint else None)

                if "channel_values" in checkpoint:
                    channel_values = checkpoint["channel_values"]
                    log_step(logger, request_id, "NL2SQL", "0", "CHECKPOINT", "channel_values keys", level="DEBUG", keys=list(channel_values.keys()) if channel_values else None)

                    existing_history = channel_values.get("conversation_history", [])
                    log_step(logger, request_id, "NL2SQL", "0", "CHECKPOINT", "existing_history 로드 완료", level="DEBUG", count=len(existing_history))
        except Exception as e:
            log_step(logger, request_id, "NL2SQL", "0", "INIT", "checkpoint 조회 실패", level="WARNING", error=str(e))

        # 초기 상태 생성
        initial_state = create_initial_state(
            question=inputs["question"],
            request_id=inputs.get("request_id", "unknown"),
            max_retries=inputs.get("max_retries", 2),
            session_id=session_id,
            max_turns=max_turns,
        )

        # 기존 conversation_history 복원
        initial_state["conversation_history"] = existing_history

        return initial_state

    def _build_response(self, result: Dict[str, Any], session_id: str, response_time_ms: int = 0) -> SearchResponse:
        """실행 결과를 SearchResponse로 변환 (멀티턴 지원)"""
        answer = result.get("answer", "")
        history_truncated = result.get("history_truncated", False)
        max_turns = result.get("max_turns", 5)
        current_turn = result.get("current_turn", 1)

        # 세션 한도 도달 여부 (현재 턴 >= max_turns이면 다음 질문 시 이력 잘림)
        session_limit_reached = current_turn >= max_turns

        # 메타데이터에 멀티턴 정보 추가
        metadata = result.get("metadata", {})
        metadata.update({
            "current_turn": current_turn,
            "max_turns": max_turns,
            "history_truncated": history_truncated,
            "session_limit_reached": session_limit_reached,  # 프론트엔드에서 버튼 표시용
        })

        return SearchResponse(
            query=result.get("question", ""),
            answer=answer,
            query_type="nl2sql",
            response_time_ms=response_time_ms,
            sql=result.get("generated_sql", ""),
            sql_result=result.get("sql_result"),
            sources=None,
            session_id=session_id,
            metadata=metadata
        )

    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        NL2SQL SSE 스트리밍 실행 (LangSmith 트레이싱 포함)

        LangSmith가 활성화되면 @traceable 래퍼로 감싸서
        Name/Input/Output이 올바르게 표시되도록 합니다.
        """
        if LANGSMITH_AVAILABLE and traceable:
            async for event in self._traced_astream_events(inputs):
                yield event
        else:
            async for event in self._raw_astream_events(inputs):
                yield event

    async def _traced_astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """LangSmith 트레이싱이 적용된 SSE 스트리밍

        @traceable로 감싸서 LangSmith에 아래와 같이 표시:
        - Name: "NL2SQL"
        - Input: {"question": "사용자 질문"}
        - Output: SSE 이벤트 목록
        """
        @traceable(name="NL2SQL")  # type: ignore
        async def traced_stream(question: str):  # noqa: ARG001
            async for event in self._raw_astream_events(inputs):
                yield event
        async for event in traced_stream(inputs["question"]):
            yield event

    async def _raw_astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        NL2SQL SSE 스트리밍 실행 (스테이지 그룹핑 방식)

        14개 노드를 4개 스테이지로 그룹핑하여 SSE 이벤트를 전송합니다.
        스테이지가 변경될 때만 node_complete/node_start 이벤트를 보내므로,
        사용자에게는 최대 4단계만 표시됩니다.

        forward-only 규칙: 현재 스테이지보다 큰 경우에만 전환
        (재시도 루프 시 스테이지가 뒤로 돌아가지 않음)

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
            }

            # 스테이지 추적 변수
            current_stage = 0

            # 1단계 node_start 이벤트 전송 (그래프 실행 전)
            start_label = get_stage_label(1, "start", "nl2sql")
            start_event = NodeStartEvent(node="stage_1", message=start_label, step=1)
            yield format_sse("node_start", start_event.model_dump())
            await asyncio.sleep(0)
            current_stage = 1

            # astream으로 노드별 이벤트 스트리밍
            async for chunk in self.graph.astream(initial_state, config=config):
                for node_name, _state_update in chunk.items():
                    if node_name.startswith("__"):
                        continue

                    node_stage = get_node_stage(node_name, "nl2sql")
                    if node_stage == 0:
                        continue

                    # forward-only: 현재보다 큰 스테이지일 때만 이벤트 전송
                    # (재시도 루프에서 스테이지가 뒤로 돌아가지 않음)
                    if node_stage > current_stage:
                        # 현재 스테이지 완료 이벤트
                        complete_label = get_stage_label(current_stage, "complete", "nl2sql")
                        complete_event = NodeCompleteEvent(
                            node=f"stage_{current_stage}",
                            message=complete_label,
                            step=current_stage,
                        )
                        yield format_sse("node_complete", complete_event.model_dump())
                        await asyncio.sleep(0)

                        # 새 스테이지 시작 이벤트
                        new_start_label = get_stage_label(node_stage, "start", "nl2sql")
                        new_start_event = NodeStartEvent(
                            node=f"stage_{node_stage}",
                            message=new_start_label,
                            step=node_stage,
                        )
                        yield format_sse("node_start", new_start_event.model_dump())
                        await asyncio.sleep(0)

                        current_stage = node_stage

                    log_step(logger, request_id, "NL2SQL", str(current_stage), "SSE", f"노드 완료: {node_name} (stage {node_stage})")

            # 마지막 스테이지 완료 이벤트
            if current_stage > 0:
                final_label = get_stage_label(current_stage, "complete", "nl2sql")
                final_event = NodeCompleteEvent(
                    node=f"stage_{current_stage}",
                    message=final_label,
                    step=current_stage,
                )
                yield format_sse("node_complete", final_event.model_dump())
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

    async def ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 비동기 실행 (멀티턴 대화 지원)"""
        # LangSmith 트레이싱: question을 Input으로 표시
        if LANGSMITH_AVAILABLE and traceable:
            return await self._traced_ainvoke(inputs)
        return await self._run_graph(inputs)

    async def _traced_ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """LangSmith 트레이싱이 적용된 실행"""
        @traceable(name="NL2SQL")  # type: ignore
        async def traced_run(question: str) -> SearchResponse:  # noqa: ARG001
            return await self._run_graph(inputs)
        return await traced_run(inputs["question"])

    async def _run_graph(self, inputs: Dict[str, Any]) -> SearchResponse:
        """실제 그래프 실행 로직"""
        start_time = time.time()

        # 세션 ID 처리 (없으면 자동 생성)
        request_id = inputs.get("request_id", "unknown")
        session_id = inputs.get("session_id")
        if not session_id:
            session_id = f"nl2sql-{request_id}"
            inputs["session_id"] = session_id

        initial_state = self._prepare_initial_state(inputs, session_id)

        log_step(logger, request_id, "NL2SQL", "0", "INIT", "NL2SQL 그래프 실행 시작 (멀티턴)", question=inputs["question"], session_id=session_id)

        # 그래프 실행 (thread_id로 세션 관리, LangSmith 트레이싱은 @traceable에서 처리)
        config: RunnableConfig = {
            "configurable": {"thread_id": session_id},
        }
        result = await self.graph.ainvoke(initial_state, config=config)

        response_time_ms = int((time.time() - start_time) * 1000)

        log_step(logger, request_id, "NL2SQL", "5", "COMPLETE", "NL2SQL 그래프 실행 완료", has_sql=bool(result.get("generated_sql", "")), answer_length=len(result.get("answer", "")), session_id=session_id, current_turn=result.get("current_turn", 1))

        return self._build_response(result, session_id, response_time_ms)

    # =========================================================================
    # 세션 관리 메서드 (멀티턴 대화)
    # =========================================================================

    def get_sessions(self) -> List[str]:
        """활성 세션 목록 조회"""
        try:
            if hasattr(self.checkpointer, 'storage'):
                # InMemorySaver의 storage에서 thread_id 추출
                sessions = set()
                for key in self.checkpointer.storage.keys():
                    if isinstance(key, tuple) and len(key) >= 1:
                        thread_id = key[0]
                        if isinstance(thread_id, str) and thread_id.startswith("nl2sql-"):
                            sessions.add(thread_id)
                return sorted(list(sessions))
        except Exception as e:
            logger.error(f"세션 목록 조회 실패: {e}")
        return []

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """세션 대화 이력 조회"""
        try:
            config: RunnableConfig = {"configurable": {"thread_id": session_id}}
            checkpoint = self.checkpointer.get(config)
            if checkpoint and "channel_values" in checkpoint:
                state = checkpoint["channel_values"]
                return state.get("conversation_history", [])
        except Exception as e:
            logger.error(f"세션 이력 조회 실패: {session_id} - {e}")
        return []

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """세션 삭제"""
        try:
            if hasattr(self.checkpointer, 'storage'):
                # storage에서 해당 session_id 관련 항목 삭제
                keys_to_delete = [
                    key for key in self.checkpointer.storage.keys()
                    if isinstance(key, tuple) and len(key) >= 1 and key[0] == session_id
                ]
                for key in keys_to_delete:
                    del self.checkpointer.storage[key]
                return {"success": True, "deleted_keys": len(keys_to_delete)}
        except Exception as e:
            logger.error(f"세션 삭제 실패: {session_id} - {e}")
            return {"success": False, "error": str(e)}
        return {"success": False, "error": "Unknown error"}


# 싱글톤 인스턴스
nl2sql_graph = NL2SQLGraph()
