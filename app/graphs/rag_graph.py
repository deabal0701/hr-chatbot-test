"""
RAG 검색 그래프 (LangGraph)

위치: app/graphs/rag_graph.py

그래프 흐름:
    retrieve → generate_answer → END

노드:
- retrieve: 벡터 검색으로 유사 문서 검색
- generate_answer: LLM을 사용하여 답변 생성
"""
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from app.models.rag import DocumentSource
from app.models.search import SearchResponse
from app.core.llm.llm_config import LLMConfigManager
from app.utils.logger import setup_logger, log_step

# 노드 함수 import
from app.graphs.nodes.rag_nodes import (
    retrieve_documents_node,
    generate_answer_node,
)

logger = setup_logger(__name__)


class RAGState(TypedDict):
    """RAG Graph 상태"""
    question: str
    filters: Dict[str, Any]
    top_k: int
    retrieved_docs: List[DocumentSource]
    answer: str
    metadata: Dict[str, Any]
    request_id: str


class RAGGraph:
    """RAG 검색 그래프 (LangGraph)"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        workflow = StateGraph(RAGState)

        # 외부 노드 함수 사용
        workflow.add_node("retrieve", retrieve_documents_node)
        workflow.add_node("generate_answer", generate_answer_node)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    def _prepare_initial_state(self, inputs: Dict[str, Any]) -> RAGState:
        """초기 상태 준비"""
        request_id = inputs.get("request_id", "unknown")
        rag_settings = LLMConfigManager.get_rag_settings()

        return {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k") or rag_settings["top_k"],
            "retrieved_docs": [],
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

    def _build_response(self, result: RAGState, response_time_ms: int = 0) -> SearchResponse:
        """실행 결과를 SearchResponse로 변환"""
        return SearchResponse(
            query=result["question"],
            answer=result["answer"],
            query_type="rag",
            response_time_ms=response_time_ms,
            sql=None,
            sql_result=None,
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )

    async def ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 비동기 실행"""
        import time
        start_time = time.time()

        initial_state = self._prepare_initial_state(inputs)
        request_id = initial_state["request_id"]

        log_step(request_id, "RAG", "0", "INIT", "RAG 그래프 실행 시작", question=inputs["question"], top_k=initial_state["top_k"])

        result = await self.graph.ainvoke(initial_state)
        response_time_ms = int((time.time() - start_time) * 1000)
        log_step(request_id, "RAG", "3", "COMPLETE", "RAG 그래프 실행 완료", docs_found=len(result["retrieved_docs"]), answer_length=len(result["answer"]))

        return self._build_response(result, response_time_ms)


# 싱글톤 인스턴스
rag_graph = RAGGraph()
