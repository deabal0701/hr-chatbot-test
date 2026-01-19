"""RAG 검색 서비스

위치: app/api/services/rag_service.py
- RAG 검색 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층
"""
from typing import Any, Dict, Optional

from app.graphs.rag_graph import rag_graph
from app.models.search import SearchFilters, SearchResponse
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class RAGService:
    """RAG 검색 서비스"""

    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: Optional[int] = None,
        request_id: str = "unknown"
    ) -> SearchResponse:
        """
        RAG 검색 실행

        Args:
            query: 사용자 질문
            filters: 검색 필터 (선택)
            top_k: 검색할 문서 수 (선택, 미지정시 DB 설정 사용)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과
        """
        log_step(request_id, "SERVICE", "RAG", "START", "RAG 서비스 시작", query=query[:50])

        # 입력 데이터 구성
        inputs = self._prepare_inputs(query, filters, top_k, request_id)

        # RAG 그래프 실행
        response = await rag_graph.ainvoke(inputs)

        log_step(
            request_id, "SERVICE", "RAG", "END", "RAG 서비스 완료",
            sources_count=len(response.sources) if response.sources else 0,
            answer_length=len(response.answer)
        )

        return response

    def search_sync(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: Optional[int] = None,
        request_id: str = "unknown"
    ) -> SearchResponse:
        """
        RAG 검색 동기 실행

        Args:
            query: 사용자 질문
            filters: 검색 필터 (선택)
            top_k: 검색할 문서 수 (선택, 미지정시 DB 설정 사용)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과
        """
        log_step(request_id, "SERVICE", "RAG", "START", "RAG 서비스 시작 (동기)", query=query[:50])

        # 입력 데이터 구성
        inputs = self._prepare_inputs(query, filters, top_k, request_id)

        # RAG 그래프 실행 (동기)
        response = rag_graph.invoke(inputs)

        log_step(
            request_id, "SERVICE", "RAG", "END", "RAG 서비스 완료 (동기)",
            sources_count=len(response.sources) if response.sources else 0,
            answer_length=len(response.answer)
        )

        return response

    def _prepare_inputs(
        self,
        query: str,
        filters: Optional[SearchFilters],
        top_k: Optional[int],
        request_id: str
    ) -> Dict[str, Any]:
        """
        그래프 입력 데이터 구성

        Args:
            query: 사용자 질문
            filters: 검색 필터
            top_k: 검색할 문서 수
            request_id: 요청 추적 ID

        Returns:
            Dict: 그래프 입력 데이터
        """
        inputs = {
            "question": query,
            "filters": filters.model_dump() if filters else {},
            "request_id": request_id
        }

        # top_k가 명시적으로 지정된 경우에만 포함 (None이면 그래프에서 DB 설정 사용)
        if top_k is not None:
            inputs["top_k"] = top_k

        return inputs


# 싱글톤 인스턴스
rag_service = RAGService()
