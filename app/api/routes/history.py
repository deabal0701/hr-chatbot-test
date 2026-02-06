"""API 요청 이력 엔드포인트

위치: app/api/routes/history.py
- API 요청 이력 조회
- 멀티테넌트 및 사용자별 이력 지원
- 통계 및 정리 기능
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.api.services.history_service import history_service
from app.core.errors import APIException, ErrorCode, success_response
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("")
async def list_history(
    tenant_id: Optional[str] = Query(None, description="테넌트 ID 필터"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터 (내 이력)"),
    request_type: Optional[str] = Query(None, description="요청 타입 (agent/nl2sql/rag)"),
    session_id: Optional[str] = Query(None, description="세션 ID 필터"),
    success_only: Optional[bool] = Query(None, description="성공한 요청만 조회"),
    from_date: Optional[datetime] = Query(None, description="시작일 (YYYY-MM-DDTHH:MM:SS)"),
    to_date: Optional[datetime] = Query(None, description="종료일 (YYYY-MM-DDTHH:MM:SS)"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """
    API 요청 이력 조회

    멀티테넌트 및 사용자별 필터링 지원:
    - tenant_id: 특정 고객사의 이력만 조회
    - user_id: 특정 사용자의 이력만 조회 (내 이력)
    """
    try:
        items = history_service.get_history(
            tenant_id=tenant_id,
            user_id=user_id,
            request_type=request_type,
            session_id=session_id,
            success_only=success_only,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

        total = history_service.get_history_count(
            tenant_id=tenant_id,
            user_id=user_id,
            request_type=request_type,
            session_id=session_id,
            success_only=success_only,
            from_date=from_date,
            to_date=to_date,
        )

        return success_response({
            "total": total,
            "items": items,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total
        })

    except Exception as e:
        logger.error(f"[HISTORY] List failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/statistics")
async def get_statistics(
    tenant_id: Optional[str] = Query(None, description="테넌트 ID 필터"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    from_date: Optional[datetime] = Query(None, description="시작일"),
    to_date: Optional[datetime] = Query(None, description="종료일"),
):
    """
    이력 통계 조회

    테넌트 또는 사용자별 통계 지원
    """
    try:
        stats = history_service.get_statistics(
            tenant_id=tenant_id,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
        )
        return success_response(stats)

    except Exception as e:
        logger.error(f"[HISTORY] Statistics failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/users/{user_id}")
async def get_user_summary(
    user_id: str,
    tenant_id: Optional[str] = Query(None, description="테넌트 ID"),
):
    """
    사용자별 이력 요약 (내 이력 요약)

    특정 사용자의 사용 통계 및 최근 요청 목록 조회
    """
    try:
        summary = history_service.get_user_summary(user_id=user_id, tenant_id=tenant_id)
        return success_response(summary)

    except Exception as e:
        logger.error(f"[HISTORY] User summary failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/users/{user_id}/history")
async def get_user_history(
    user_id: str,
    tenant_id: Optional[str] = Query(None, description="테넌트 ID"),
    request_type: Optional[str] = Query(None, description="요청 타입 필터"),
    from_date: Optional[datetime] = Query(None, description="시작일"),
    to_date: Optional[datetime] = Query(None, description="종료일"),
    limit: int = Query(100, ge=1, le=1000, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    """
    사용자별 이력 상세 조회 (내 이력)

    특정 사용자의 전체 요청 이력 조회
    """
    try:
        items = history_service.get_history(
            tenant_id=tenant_id,
            user_id=user_id,
            request_type=request_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

        total = history_service.get_history_count(
            tenant_id=tenant_id,
            user_id=user_id,
            request_type=request_type,
            from_date=from_date,
            to_date=to_date,
        )

        return success_response({
            "user_id": user_id,
            "total": total,
            "items": items,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total
        })

    except Exception as e:
        logger.error(f"[HISTORY] User history failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """
    세션별 이력 조회

    멀티턴 대화 세션의 전체 이력 조회
    """
    try:
        items = history_service.get_session_history(session_id)
        return success_response({
            "session_id": session_id,
            "total": len(items),
            "items": items
        })

    except Exception as e:
        logger.error(f"[HISTORY] Session history failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/{request_id}")
async def get_history_detail(request_id: str):
    """
    단일 요청 상세 조회

    request_id로 특정 요청의 상세 정보 조회
    """
    try:
        record = history_service.get_by_request_id(request_id)
        if not record:
            raise APIException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"Request {request_id} not found"
            )
        return success_response(record)

    except APIException:
        raise
    except Exception as e:
        logger.error(f"[HISTORY] Detail failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_records(
    days: int = Query(90, ge=7, le=365, description="보관 기간 (일)"),
    tenant_id: Optional[str] = Query(None, description="테넌트 ID (지정 시 해당 테넌트만 정리)"),
):
    """
    오래된 이력 정리 (관리자용)

    지정된 기간보다 오래된 이력 삭제
    - 기본 보관 기간: 90일
    - tenant_id 지정 시 해당 테넌트만 정리
    """
    try:
        deleted_count = history_service.cleanup_old_records(days=days, tenant_id=tenant_id)
        return success_response({
            "message": f"Deleted {deleted_count} records older than {days} days",
            "deleted_count": deleted_count,
            "retention_days": days,
            "tenant_id": tenant_id
        })

    except Exception as e:
        logger.error(f"[HISTORY] Cleanup failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
