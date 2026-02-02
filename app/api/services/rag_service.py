"""RAG 검색 서비스

위치: app/api/services/rag_service.py
- RAG 검색 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층
"""
from typing import Optional

# 새 위치: app/graphs/rag/
from app.graphs.rag.graph import rag_graph
from app.models.search import SearchFilters, SearchResponse
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


class RAGService:
    """RAG 검색 서비스"""

    async def search(self, query: str, filters: Optional[SearchFilters] = None, request_id: str = "unknown") -> SearchResponse:
        """
        RAG 검색 실행

        Args:
            query: 사용자 질문
            filters: 검색 필터 (선택)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과
        """
        log_step(request_id, "SERVICE", "RAG", "START", "RAG 서비스 시작", query=truncate_text(query, 50))

        inputs = {
            "question": query,
            "filters": filters.model_dump() if filters else {},
            "request_id": request_id
        }

        response = await rag_graph.ainvoke(inputs)

        log_step(request_id, "SERVICE", "RAG", "END", "RAG 서비스 완료", sources_count=len(response.sources) if response.sources else 0, answer_length=len(response.answer))

        return response


# 싱글톤 인스턴스
rag_service = RAGService()
