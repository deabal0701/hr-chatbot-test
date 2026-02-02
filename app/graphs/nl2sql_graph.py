"""
NL2SQL 검색 그래프 (LangGraph) - 방안 C

위치: app/graphs/nl2sql_graph.py

그래프 흐름 (방안 C):
    schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql → should_execute 분기
                                                                                          ├─ "execute" → execute_sql → generate_answer → END
                                                                                          ├─ "retry" → fewshot_retrieval (enhanced mode)
                                                                                          └─ "error" → handle_error → END

노드:
- schema_retrieval: 질문 분석하여 필요한 테이블 스키마만 로드
- fewshot_retrieval: Few-shot 예제 검색 (NEW)
- prompt_build: 스키마 + Few-shot + DB 가이드라인 조합 (NEW)
- sql_generate: LLM 호출만 수행 (리팩토링)
- validate_sql: SQL 안전성 및 유효성 검증
- execute_sql: SQL 실행
- generate_answer: 결과를 자연어 답변으로 변환
- handle_error: 오류 처리
"""
from typing import Any, Dict, List, Optional, TypedDict
import time

from langgraph.graph import END, StateGraph

from app.models.search import SearchResponse
from app.models.rag import SQLResult
from app.utils.logger import setup_logger, log_step

# 노드 함수 import
from app.graphs.nodes.nl2sql_nodes import (
    schema_retrieval_node,
    fewshot_retrieval_node,   # NEW
    prompt_build_node,        # NEW
    sql_generate_node,        # 리팩토링됨
    validate_sql_node,
    execute_sql_node,
    generate_answer_node,
    handle_error_node,
    should_execute,
)

logger = setup_logger(__name__)


class NL2SQLState(TypedDict):
    """NL2SQL Graph 상태 (방안 C 확장)"""
    # ===== 기본 필드 =====
    question: str
    schema_description: str
    generated_sql: str
    validated: bool
    validation_error: str
    sql_result: Optional[SQLResult]
    answer: str
    metadata: Dict[str, Any]
    request_id: str

    # ===== schema_retrieval_node 필드 =====
    selected_tables: List[str]           # 선택된 테이블 목록
    schema_retrieval_confidence: float   # 테이블 선택 신뢰도

    # ===== fewshot_retrieval_node 필드 (NEW) =====
    fewshot_context: str                 # 포맷된 Few-shot 예제 문자열
    fewshot_examples: List[Dict]         # 원본 예제 데이터 목록
    fewshot_count: int                   # 검색된 예제 수

    # ===== prompt_build_node 필드 (NEW) =====
    sql_prompt: str                      # 완성된 System Prompt
    user_prompt: str                     # User Prompt
    prompt_metadata: Dict[str, Any]      # 프롬프트 메타데이터

    # ===== 재시도 관련 필드 (NEW) =====
    retry_count: int                     # 현재 재시도 횟수
    max_retries: int                     # 최대 재시도 횟수
    previous_sql: str                    # 이전 시도 SQL
    previous_error: str                  # 이전 오류 메시지
    enhanced_fewshot: bool               # 강화된 Few-shot 모드 플래그


class NL2SQLGraph:
    """NL2SQL 검색 그래프 (LangGraph) - 방안 C

    엔터프라이즈급 NL2SQL 시스템
    - SRP 준수: 각 노드가 단일 책임
    - Few-shot 예제 검색
    - 쿼리 오류 시 재시도 기능
    - DB 타입 자동 감지 (PostgreSQL, Oracle)
    - Admin UI 프롬프트 설정 반영
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """그래프 구성 (방안 C)

        흐름:
        schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql
                                                                                ├─ execute → execute_sql → generate_answer → END
                                                                                ├─ retry → fewshot_retrieval (enhanced)
                                                                                └─ error → handle_error → END
        """
        workflow = StateGraph(NL2SQLState)

        # 노드 등록
        workflow.add_node("schema_retrieval", schema_retrieval_node)
        workflow.add_node("fewshot_retrieval", fewshot_retrieval_node)  # NEW
        workflow.add_node("prompt_build", prompt_build_node)            # NEW
        workflow.add_node("sql_generate", sql_generate_node)            # 리팩토링됨
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("generate_answer", generate_answer_node)
        workflow.add_node("handle_error", handle_error_node)

        # 순차 실행 흐름 정의
        workflow.set_entry_point("schema_retrieval")
        workflow.add_edge("schema_retrieval", "fewshot_retrieval")
        workflow.add_edge("fewshot_retrieval", "prompt_build")
        workflow.add_edge("prompt_build", "sql_generate")
        workflow.add_edge("sql_generate", "validate_sql")

        # 조건부 분기 (재시도 포함)
        workflow.add_conditional_edges(
            "validate_sql",
            should_execute,
            {
                "execute": "execute_sql",
                "retry": "fewshot_retrieval",  # 재시도: enhanced fewshot으로 다시 시도
                "error": "handle_error"
            }
        )

        workflow.add_edge("execute_sql", "generate_answer")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _prepare_initial_state(self, inputs: Dict[str, Any]) -> NL2SQLState:
        """초기 상태 준비 (방안 C 확장)"""
        return {
            # 기본 필드
            "question": inputs["question"],
            "schema_description": "",
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "sql_result": None,
            "answer": "",
            "metadata": {},
            "request_id": inputs.get("request_id", "unknown"),
            # schema_retrieval_node 필드
            "selected_tables": [],
            "schema_retrieval_confidence": 0.0,
            # fewshot_retrieval_node 필드 (NEW)
            "fewshot_context": "",
            "fewshot_examples": [],
            "fewshot_count": 0,
            # prompt_build_node 필드 (NEW)
            "sql_prompt": "",
            "user_prompt": "",
            "prompt_metadata": {},
            # 재시도 관련 필드 (NEW)
            "retry_count": 0,
            "max_retries": inputs.get("max_retries", 2),
            "previous_sql": "",
            "previous_error": "",
            "enhanced_fewshot": False,
        }

    def _build_response(self, result: NL2SQLState, response_time_ms: int = 0) -> SearchResponse:
        """실행 결과를 SearchResponse로 변환"""
        return SearchResponse(
            query=result["question"],
            answer=result["answer"],
            query_type="nl2sql",
            response_time_ms=response_time_ms,
            sql=result["generated_sql"],
            sql_result=result.get("sql_result"),
            sources=None,
            metadata=result["metadata"]
        )

    async def ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 비동기 실행"""
        start_time = time.time()

        initial_state = self._prepare_initial_state(inputs)
        request_id = initial_state["request_id"]

        log_step(request_id, "NL2SQL", "0", "INIT", "NL2SQL 그래프 실행 시작", question=inputs["question"])

        result = await self.graph.ainvoke(initial_state)

        response_time_ms = int((time.time() - start_time) * 1000)

        log_step(request_id, "NL2SQL", "5", "COMPLETE", "NL2SQL 그래프 실행 완료", has_sql=bool(result["generated_sql"]), answer_length=len(result["answer"]))

        return self._build_response(result, response_time_ms)


# 싱글톤 인스턴스
nl2sql_graph = NL2SQLGraph()
