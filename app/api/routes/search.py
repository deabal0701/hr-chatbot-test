"""검색 API 엔드포인트

위치: app/api/routes/search.py
- 통합 검색 엔드포인트 (RAG/NL2SQL)
- NL2SQL 멀티턴 대화 세션 관리
- 비즈니스 로직은 서비스 계층에 위임
"""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status, Request

from app.api.services.rag_service import rag_service
from app.api.services.nl2sql_service import nl2sql_service
from app.models.search import SearchRequest, SearchResponse
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(search_request: SearchRequest, request: Request):
    """
    통합 검색 엔드포인트

    - mode='auto': 자동으로 RAG/NL2SQL 선택 (기본값)
    - mode='rag': RAG 검색 (문서 기반)
    - mode='nl2sql': NL2SQL 검색 (데이터베이스 쿼리)
    """
    # Middleware에서 생성된 request_id 사용 (없으면 새로 생성)
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    logger.info(f"[{request_id}] ========== 검색 요청 처리 시작 ==========")

    try:
        # STEP 1: 사용자 요청 수신
        log_step(logger, request_id, "API", "1", "REQUEST", "사용자 요청 수신", query=search_request.query, mode=search_request.mode)

        # STEP 2: 모드 결정
        if search_request.mode == "auto":
            query_type = _classify_query_intent(search_request.query)
            log_step(logger, request_id, "API", "2", "CLASSIFY", f"자동 분류 완료 → {query_type.upper()}", original_mode="auto", detected_type=query_type)
        else:
            query_type = search_request.mode
            log_step(logger, request_id, "API", "2", "CLASSIFY", f"사용자 지정 모드 사용 → {query_type.upper()}")

        # STEP 3: 서비스 호출
        if query_type == "nl2sql":
            response = await nl2sql_service.search(
                query=search_request.query,
                session_id=search_request.session_id,  # 멀티턴 대화 지원
                request_id=request_id
            )
        else:  # rag
            response = await rag_service.search(query=search_request.query, filters=search_request.filters, request_id=request_id)

        # STEP 4: 응답 완료
        log_step(logger, request_id, "API", "4", "RESPONSE", "응답 생성 완료", query_type=response.query_type, response_time_ms=response.response_time_ms, answer_length=len(response.answer))
        logger.info(f"[{request_id}] ========== 검색 요청 처리 완료 ==========")

        return response

    except Exception as e:
        logger.error(f"[{request_id}] [ERROR] 검색 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


def _classify_query_intent(query: str) -> str:
    """
    쿼리 의도 분류 (간단한 휴리스틱)
    실제로는 LLM을 사용하거나 더 정교한 분류기를 사용할 수 있음
    """
    query_lower = query.lower()

    # NL2SQL 키워드
    nl2sql_keywords = [
        "몇 명", "몇명", "수", "통계", "집계", "평균", "합계", "최대", "최소",
        "count", "avg", "sum", "max", "min",
        "입사자", "퇴사자", "직원", "사원",
        "월별", "연도별", "부서별", "직급별"
    ]

    # RAG 키워드
    rag_keywords = [
        "정책", "규정", "가이드", "안내", "공고",
        "설명", "요약", "무엇", "어떻게",
        "재택", "연차", "평가", "채용", "복지"
    ]

    nl2sql_score = sum(1 for keyword in nl2sql_keywords if keyword in query_lower)
    rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)

    # 숫자나 연도가 포함되어 있으면 NL2SQL 가능성 높음
    if any(year in query for year in ["2020", "2021", "2022", "2023", "2024"]):
        nl2sql_score += 2

    if nl2sql_score > rag_score:
        return "nl2sql"
    else:
        return "rag"


# =============================================================================
# NL2SQL 세션 관리 API (멀티턴 대화)
# =============================================================================


@router.get("/nl2sql/sessions", response_model=List[str])
async def get_nl2sql_sessions():
    """
    NL2SQL 활성 세션 목록 조회

    Returns:
        List[str]: 세션 ID 목록
    """
    try:
        sessions = nl2sql_service.get_sessions()
        return sessions
    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 목록 조회 실패: {str(e)}"
        )


@router.get("/nl2sql/sessions/{session_id}/history", response_model=List[Dict[str, Any]])
async def get_nl2sql_session_history(session_id: str):
    """
    NL2SQL 세션 대화 이력 조회

    Args:
        session_id: 세션 ID

    Returns:
        List[Dict]: 대화 이력 [{question, sql, answer, timestamp}, ...]
    """
    try:
        history = nl2sql_service.get_session_history(session_id)
        return history
    except Exception as e:
        logger.error(f"세션 이력 조회 실패: {session_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 이력 조회 실패: {str(e)}"
        )


@router.delete("/nl2sql/sessions/{session_id}", response_model=Dict[str, Any])
async def delete_nl2sql_session(session_id: str):
    """
    NL2SQL 세션 삭제

    Args:
        session_id: 세션 ID

    Returns:
        Dict: 삭제 결과 {success, deleted_keys or error}
    """
    try:
        result = nl2sql_service.delete_session(session_id)
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "세션 삭제 실패")
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 삭제 실패: {session_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 삭제 실패: {str(e)}"
        )
