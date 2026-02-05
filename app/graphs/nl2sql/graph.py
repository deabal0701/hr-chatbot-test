"""
NL2SQL 검색 그래프 (LangGraph)

위치: app/graphs/nl2sql/graph.py

그래프 흐름 (멀티턴 대화 + 질문 재작성):
    load_history → intent_rewrite → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                                                                                          ├─ execute → execute_sql → should_continue_after_execute
                                                                                                          │                            ├─ answer → generate_answer → save_history → END
                                                                                                          │                            ├─ retry → prepare_retry → fewshot_retrieval
                                                                                                          │                            └─ error → handle_error → END
                                                                                                          ├─ retry → prepare_retry → fewshot_retrieval
                                                                                                          └─ error → handle_error → END

노드:
- load_history: 이전 대화 이력 로드 (멀티턴)
- intent_rewrite: 이전 대화 컨텍스트를 포함한 완전한 질문 재작성 (멀티턴 핵심 노드)
- schema_retrieval: 질문 분석하여 필요한 테이블 스키마만 로드
- fewshot_retrieval: Few-shot 예제 검색
- prompt_build: 스키마 + Few-shot + 이전 대화 이력 + DB 가이드라인 조합
- sql_generate: LLM 호출만 수행
- validate_sql: SQL 안전성 및 유효성 검증
- execute_sql: SQL 실행
- generate_answer: 결과를 자연어 답변으로 변환
- save_history: 현재 대화를 이력에 저장 (멀티턴, sql_result_summary 포함)
- handle_error: 오류 처리
- prepare_retry: 재시도 상태 업데이트 (retry_count 증가)
"""
from typing import Any, Dict, List, Optional
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
    generate_answer_node,
    handle_error_node,
    prepare_retry_node,
    should_execute,
    should_continue_after_execute,
    load_history_node,
    save_history_node,
    # 질문 재작성 노드 (멀티턴 대화 컨텍스트 포함)
    intent_rewrite_node,
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

        log_step("SYSTEM", "NL2SQL", "INIT", "SETUP", "NL2SQLGraph 초기화 완료 (멀티턴 지원)", level="DEBUG")

    def _build_graph(self) -> CompiledStateGraph:
        """그래프 구성

        흐름 (멀티턴 대화 + 질문 재작성):
        load_history → intent_rewrite → schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                                                                                              ├─ execute → execute_sql → should_continue_after_execute
                                                                                                              │                            ├─ answer → generate_answer → save_history → END
                                                                                                              │                            ├─ retry → prepare_retry → fewshot_retrieval
                                                                                                              │                            └─ error → handle_error → END
                                                                                                              ├─ retry → prepare_retry → fewshot_retrieval
                                                                                                              └─ error → handle_error → END
        """
        workflow = StateGraph(NL2SQLState)

        # 노드 등록 (멀티턴 노드 포함)
        workflow.add_node("load_history", load_history_node)
        workflow.add_node("intent_rewrite", intent_rewrite_node)  # 이전 대화 컨텍스트 포함 질문 재작성
        workflow.add_node("schema_retrieval", schema_retrieval_node)
        workflow.add_node("fewshot_retrieval", fewshot_retrieval_node)
        workflow.add_node("prompt_build", prompt_build_node)
        workflow.add_node("sql_generate", sql_generate_node)
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("generate_answer", generate_answer_node)
        workflow.add_node("save_history", save_history_node)
        workflow.add_node("handle_error", handle_error_node)
        workflow.add_node("prepare_retry", prepare_retry_node)

        # 순차 실행 흐름 정의 (load_history로 시작)
        workflow.set_entry_point("load_history")
        workflow.add_edge("load_history", "intent_rewrite")
        workflow.add_edge("intent_rewrite", "schema_retrieval")  # 항상 SQL 생성 흐름

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
                "answer": "generate_answer",
                "retry": "prepare_retry",  # 실행 오류 → 재시도 준비 → fewshot
                "error": "handle_error"
            }
        )

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
            log_step(request_id, "NL2SQL", "0", "CHECKPOINT", "checkpoint 조회", level="DEBUG", session_id=session_id, exists=checkpoint is not None)

            if checkpoint:
                log_step(request_id, "NL2SQL", "0", "CHECKPOINT", "checkpoint keys", level="DEBUG", keys=list(checkpoint.keys()) if checkpoint else None)

                if "channel_values" in checkpoint:
                    channel_values = checkpoint["channel_values"]
                    log_step(request_id, "NL2SQL", "0", "CHECKPOINT", "channel_values keys", level="DEBUG", keys=list(channel_values.keys()) if channel_values else None)

                    existing_history = channel_values.get("conversation_history", [])
                    log_step(request_id, "NL2SQL", "0", "CHECKPOINT", "existing_history 로드 완료", level="DEBUG", count=len(existing_history))
        except Exception as e:
            log_step(request_id, "NL2SQL", "0", "INIT", "checkpoint 조회 실패", level="WARNING", error=str(e))

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

        log_step(request_id, "NL2SQL", "0", "INIT", "NL2SQL 그래프 실행 시작 (멀티턴)", question=inputs["question"], session_id=session_id)

        # 그래프 실행 (thread_id로 세션 관리, run_name으로 LangSmith에 질문 표시)
        config: RunnableConfig = {
            "configurable": {"thread_id": session_id},
            "run_name": inputs["question"],  # LangGraph 트레이스 Name 컬럼에 표시
        }
        result = await self.graph.ainvoke(initial_state, config=config)

        response_time_ms = int((time.time() - start_time) * 1000)

        log_step(request_id, "NL2SQL", "5", "COMPLETE", "NL2SQL 그래프 실행 완료", has_sql=bool(result.get("generated_sql", "")), answer_length=len(result.get("answer", "")), session_id=session_id, current_turn=result.get("current_turn", 1))

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
