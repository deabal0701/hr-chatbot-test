"""검색 API 엔드포인트

위치: app/api/routes/search.py
- 통합 검색 엔드포인트 (RAG/NL2SQL)
- NL2SQL 멀티턴 대화 세션 관리
- 비즈니스 로직은 서비스 계층에 위임
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.services.rag_service import rag_service
from app.api.services.nl2sql_service import nl2sql_service
from app.core.errors import APIException, ErrorCode, success_response
from app.core.security.dependencies import get_optional_user
from app.models.auth import UserContext
from app.models.search import SearchRequest
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search")
async def search(search_request: SearchRequest, request: Request, current_user: Optional[UserContext] = Depends(get_optional_user)):
    """
    통합 검색 엔드포인트

    - mode='auto': 자동으로 RAG/NL2SQL 선택 (기본값)
    - mode='rag': RAG 검색 (문서 기반)
    - mode='nl2sql': NL2SQL 검색 (데이터베이스 쿼리)

    인증 시 권한 검증: rag:search (RAG), nl2sql:execute (NL2SQL)
    Phase 3a: 미인증 허용 (하위호환)
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    logger.info(f"[{request_id}] ========== 검색 요청 처리 시작 ==========")

    try:
        log_step(logger, request_id, "API", "1", "REQUEST", "사용자 요청 수신", query=search_request.query, mode=search_request.mode)

        # 모드 결정
        if search_request.mode == "auto":
            query_type = _classify_query_intent(search_request.query)
            log_step(logger, request_id, "API", "2", "CLASSIFY", f"자동 분류 완료 → {query_type.upper()}", original_mode="auto", detected_type=query_type)
        else:
            query_type = search_request.mode
            log_step(logger, request_id, "API", "2", "CLASSIFY", f"사용자 지정 모드 사용 → {query_type.upper()}")

        # 인증 사용자 권한 검증 (Phase 3a: 미인증 시 skip, 인증 시 활성 사용자 확인)

        # 서비스 호출
        if query_type == "nl2sql":
            response = await nl2sql_service.search(query=search_request.query, session_id=search_request.session_id, request_id=request_id)
        else:
            response = await rag_service.search(query=search_request.query, filters=search_request.filters, request_id=request_id)

        log_step(logger, request_id, "API", "4", "RESPONSE", "응답 생성 완료", query_type=response.query_type, response_time_ms=response.response_time_ms, answer_length=len(response.answer))
        logger.info(f"[{request_id}] ========== 검색 요청 처리 완료 ==========")

        return success_response(response.model_dump())

    except APIException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] [ERROR] 검색 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.SEARCH_FAILED, detail=str(e))


@router.post("/search/stream")
async def search_stream(search_request: SearchRequest, request: Request, current_user: Optional[UserContext] = Depends(get_optional_user)):
    """
    통합 검색 SSE 스트리밍 엔드포인트

    NL2SQL 모드에서만 SSE 스트리밍을 지원합니다.
    RAG 모드는 지원하지 않으며 요청 시 에러를 반환합니다.

    Response: text/event-stream (SSE)
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    # 모드 결정
    if search_request.mode == "auto":
        query_type = _classify_query_intent(search_request.query)
    else:
        query_type = search_request.mode

    # 인증 사용자 권한 검증 (Phase 3a: 미인증 시 skip, 인증 시 활성 사용자 확인)

    # RAG 모드는 SSE 미지원
    if query_type == "rag":
        raise APIException(error_code=ErrorCode.BAD_REQUEST, message="RAG 모드는 SSE 스트리밍을 지원하지 않습니다. 기존 /api/v1/search 엔드포인트를 사용하세요.")

    log_step(logger, request_id, "API", "1", "SSE", "NL2SQL SSE 검색 요청", query=search_request.query)

    async def event_generator():
        async for event in nl2sql_service.search_stream(
            query=search_request.query,
            session_id=search_request.session_id,
            request_id=request_id,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
        },
    )


def _classify_query_intent(query: str) -> str:
    """쿼리 의도 분류 (간단한 휴리스틱)"""
    query_lower = query.lower()

    nl2sql_keywords = [
        "몇 명", "몇명", "수", "통계", "집계", "평균", "합계", "최대", "최소",
        "count", "avg", "sum", "max", "min",
        "입사자", "퇴사자", "직원", "사원",
        "월별", "연도별", "부서별", "직급별"
    ]

    rag_keywords = [
        "정책", "규정", "가이드", "안내", "공고",
        "설명", "요약", "무엇", "어떻게",
        "재택", "연차", "평가", "채용", "복지"
    ]

    nl2sql_score = sum(1 for keyword in nl2sql_keywords if keyword in query_lower)
    rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)

    if any(year in query for year in ["2020", "2021", "2022", "2023", "2024"]):
        nl2sql_score += 2

    return "nl2sql" if nl2sql_score > rag_score else "rag"


# =============================================================================
# NL2SQL 세션 관리 API (멀티턴 대화)
# =============================================================================


@router.get("/nl2sql/sessions")
async def get_nl2sql_sessions(current_user: Optional[UserContext] = Depends(get_optional_user)):
    """NL2SQL 활성 세션 목록 조회"""
    try:
        sessions = nl2sql_service.get_sessions()
        return success_response(sessions)
    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/nl2sql/sessions/{session_id}/history")
async def get_nl2sql_session_history(session_id: str, current_user: Optional[UserContext] = Depends(get_optional_user)):
    """NL2SQL 세션 대화 이력 조회"""
    try:
        history = nl2sql_service.get_session_history(session_id)
        return success_response(history)
    except Exception as e:
        logger.error(f"세션 이력 조회 실패: {session_id} - {e}")
        raise APIException(error_code=ErrorCode.SESSION_NOT_FOUND, detail=str(e))


@router.delete("/nl2sql/sessions/{session_id}")
async def delete_nl2sql_session(session_id: str, current_user: Optional[UserContext] = Depends(get_optional_user)):
    """NL2SQL 세션 삭제"""
    try:
        result = nl2sql_service.delete_session(session_id)
        if not result.get("success"):
            raise APIException(error_code=ErrorCode.SESSION_NOT_FOUND, message=result.get("error", "세션 삭제 실패"))
        return success_response(result)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"세션 삭제 실패: {session_id} - {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
