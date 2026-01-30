"""RAG 검색 서비스

위치: app/api/services/rag_service.py
- RAG 검색 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층

보안 정책:
- 사용자가 API 요청으로 전달한 top_k 등의 설정값은 무시됨
- 모든 설정은 DB(tb_app_settings) 또는 캐시에서만 로드
- 관리자만 Admin UI를 통해 설정 변경 가능
"""
from typing import Any, Dict, Optional

from app.graphs.rag_graph import rag_graph
from app.models.search import SearchFilters, SearchResponse
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


class RAGService:
    """RAG 검색 서비스"""

    async def search(self, query: str, filters: Optional[SearchFilters] = None, top_k: Optional[int] = None, request_id: str = "unknown") -> SearchResponse:
        """
        RAG 검색 실행

        Args:
            query: 사용자 질문
            filters: 검색 필터 (선택, 보안상 제한적 허용)
            top_k: 검색할 문서 수 (보안상 무시됨, DB 설정 사용)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과
        """
        log_step(request_id, "SERVICE", "RAG", "START", "RAG 서비스 시작", query=truncate_text(query, 50))

        # 입력 데이터 구성 (보안: top_k 무시)
        inputs = self._prepare_inputs(query, filters, top_k, request_id)

        # RAG 그래프 실행
        response = await rag_graph.ainvoke(inputs)

        log_step(request_id, "SERVICE", "RAG", "END", "RAG 서비스 완료", sources_count=len(response.sources) if response.sources else 0, answer_length=len(response.answer))

        return response

    def _prepare_inputs(self, query: str, filters: Optional[SearchFilters], top_k: Optional[int], request_id: str) -> Dict[str, Any]:
        """
        그래프 입력 데이터 구성 (보안: 사용자 입력 top_k 무시)

        보안 정책:
        - top_k: 사용자 입력 무시, Graph에서 DB 설정 사용
        - filters: 제한적 허용 (doc_type, category 등 필터링 용도)

        Args:
            query: 사용자 질문
            filters: 검색 필터 (제한적 허용)
            top_k: 검색할 문서 수 (보안상 무시됨)
            request_id: 요청 추적 ID

        Returns:
            Dict: 그래프 입력 데이터
        """
        # 보안: top_k 사용자 입력 무시 (Graph에서 DB 설정 사용)
        _ = top_k  # 명시적으로 무시 (보안 정책)

        return {
            "question": query,
            "filters": filters.model_dump() if filters else {},
            "request_id": request_id
            # top_k는 포함하지 않음 → Graph에서 DB 설정 사용
        }


# 싱글톤 인스턴스
rag_service = RAGService()
