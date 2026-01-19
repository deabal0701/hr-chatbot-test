"""NL2SQL 검색 서비스

위치: app/api/services/nl2sql_service.py
- NL2SQL 검색 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층
"""
from typing import Any, Dict

from app.graphs.nl2sql_graph import nl2sql_graph
from app.models.search import SearchResponse
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class NL2SQLService:
    """NL2SQL 검색 서비스"""

    async def search(self, query: str, request_id: str = "unknown") -> SearchResponse:
        """
        NL2SQL 검색 실행

        Args:
            query: 사용자 질문 (자연어)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과 (SQL, 실행 결과, 답변 포함)
        """
        log_step(request_id, "SERVICE", "NL2SQL", "START", "NL2SQL 서비스 시작", query=query[:50])

        # 입력 데이터 구성
        inputs = self._prepare_inputs(query, request_id)

        # NL2SQL 그래프 실행
        response = await nl2sql_graph.ainvoke(inputs)

        log_step(request_id, "SERVICE", "NL2SQL", "END", "NL2SQL 서비스 완료", sql_generated=bool(response.sql), answer_length=len(response.answer))

        return response

    def _prepare_inputs(self, query: str, request_id: str) -> Dict[str, Any]:
        """
        그래프 입력 데이터 구성

        Args:
            query: 사용자 질문
            request_id: 요청 추적 ID

        Returns:
            Dict: 그래프 입력 데이터
        """
        return {
            "question": query,
            "request_id": request_id
        }


# 싱글톤 인스턴스
nl2sql_service = NL2SQLService()
