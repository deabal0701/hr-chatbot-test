"""NL2SQL 검색 서비스

위치: app/api/services/nl2sql_service.py
- NL2SQL 검색 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층
- 멀티턴 대화 세션 관리
"""
from typing import Any, Dict, List, Optional

# 새 위치: app/graphs/nl2sql/
from app.graphs.nl2sql.graph import nl2sql_graph
from app.models.search import SearchResponse
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


class NL2SQLService:
    """NL2SQL 검색 서비스 (멀티턴 대화 지원)"""

    async def search(
        self,
        query: str,
        session_id: Optional[str] = None,
        request_id: str = "unknown"
    ) -> SearchResponse:
        """
        NL2SQL 검색 실행 (멀티턴 대화 지원)

        Args:
            query: 사용자 질문 (자연어)
            session_id: 세션 ID (멀티턴 대화용, 없으면 자동 생성)
            request_id: 요청 추적 ID

        Returns:
            SearchResponse: 검색 결과 (SQL, 실행 결과, 답변, session_id 포함)
        """
        log_step(request_id, "SERVICE", "NL2SQL", "START", "NL2SQL 서비스 시작", query=truncate_text(query, 50), session_id=session_id or "auto")

        # 입력 데이터 구성
        inputs = self._prepare_inputs(query, session_id, request_id)

        # NL2SQL 그래프 실행
        response = await nl2sql_graph.ainvoke(inputs)

        log_step(request_id, "SERVICE", "NL2SQL", "END", "NL2SQL 서비스 완료", sql_generated=bool(response.sql), answer_length=len(response.answer), session_id=response.session_id)

        return response

    def _prepare_inputs(
        self,
        query: str,
        session_id: Optional[str],
        request_id: str
    ) -> Dict[str, Any]:
        """
        그래프 입력 데이터 구성

        Args:
            query: 사용자 질문
            session_id: 세션 ID
            request_id: 요청 추적 ID

        Returns:
            Dict: 그래프 입력 데이터
        """
        return {
            "question": query,
            "session_id": session_id,
            "request_id": request_id
        }

    # =========================================================================
    # 세션 관리 메서드 (멀티턴 대화)
    # =========================================================================

    def get_sessions(self) -> List[str]:
        """
        활성 NL2SQL 세션 목록 조회

        Returns:
            List[str]: 세션 ID 목록
        """
        return nl2sql_graph.get_sessions()

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        세션 대화 이력 조회

        Args:
            session_id: 세션 ID

        Returns:
            List[Dict]: 대화 이력 [{question, sql, answer, timestamp}, ...]
        """
        return nl2sql_graph.get_session_history(session_id)

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 삭제 결과 {success, deleted_keys or error}
        """
        return nl2sql_graph.delete_session(session_id)


# 싱글톤 인스턴스
nl2sql_service = NL2SQLService()
