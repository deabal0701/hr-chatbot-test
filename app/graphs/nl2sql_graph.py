"""
NL2SQL 검색 그래프 (LangGraph)

위치: app/graphs/nl2sql_graph.py

그래프 흐름:
    generate_sql → validate_sql → should_execute 분기
                                  ├─ "execute" → execute_sql → generate_answer → END
                                  └─ "error" → handle_error → END

노드:
- generate_sql: 자연어 질문을 SQL로 변환
- validate_sql: SQL 안전성 및 유효성 검증
- execute_sql: SQL 실행
- generate_answer: 결과를 자연어 답변으로 변환
- handle_error: 오류 처리
"""
from typing import Any, Dict, TypedDict
import time

from langgraph.graph import END, StateGraph

from app.models.search import SearchResponse
from app.models.rag import SQLResult
from app.utils.logger import setup_logger, log_step

# 노드 함수 import
from app.graphs.nodes.nl2sql_nodes import (
    generate_sql_node,
    validate_sql_node,
    execute_sql_node,
    generate_answer_node,
    handle_error_node,
    should_execute,
)

logger = setup_logger(__name__)


class NL2SQLState(TypedDict):
    """NL2SQL Graph 상태"""
    question: str
    schema_description: str
    generated_sql: str
    validated: bool
    validation_error: str
    sql_result: SQLResult
    answer: str
    metadata: Dict[str, Any]
    request_id: str


class NL2SQLGraph:
    """NL2SQL 검색 그래프 (LangGraph)

    sql_generator 공통 모듈을 사용하여 SQL 생성
    - DB 타입 자동 감지 (PostgreSQL, Oracle)
    - Admin UI 프롬프트 설정 반영
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        workflow = StateGraph(NL2SQLState)

        # 외부 노드 함수 사용
        workflow.add_node("generate_sql", generate_sql_node)
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("generate_answer", generate_answer_node)
        workflow.add_node("handle_error", handle_error_node)

        workflow.set_entry_point("generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")

        workflow.add_conditional_edges(
            "validate_sql",
            should_execute,
            {
                "execute": "execute_sql",
                "error": "handle_error"
            }
        )

        workflow.add_edge("execute_sql", "generate_answer")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _prepare_initial_state(self, inputs: Dict[str, Any]) -> NL2SQLState:
        """초기 상태 준비"""
        return {
            "question": inputs["question"],
            "schema_description": "",
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "sql_result": None,
            "answer": "",
            "metadata": {},
            "request_id": inputs.get("request_id", "unknown")
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
