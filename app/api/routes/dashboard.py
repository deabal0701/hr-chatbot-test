"""대시보드 API 엔드포인트

위치: app/api/routes/dashboard.py
- 대시보드 통합 요약 데이터 제공 (KPI, 차트, 최근 활동, 시스템 현황)
- NL2SQL + RAG 대상 (Agent 제외)
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.services.dashboard_service import dashboard_service
from app.core.errors import APIException, ErrorCode, success_response
from app.core.security.dependencies import get_optional_user
from app.models.auth import UserContext
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _apply_scope_filter(current_user: Optional[UserContext], tenant_id: Optional[str], user_id: Optional[str]):
    """role_code에 따라 tenant_id/user_id 필터를 강제 적용"""
    if not current_user:
        return tenant_id, user_id
    if current_user.role_code == "TENANT":
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else tenant_id
    elif current_user.role_code == "USER":
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else tenant_id
        user_id = str(current_user.user_id)
    return tenant_id, user_id


@router.get("/summary")
async def get_dashboard_summary(
    period: str = Query("today", description="기간 필터 (today|week|month)"),
    tenant_id: Optional[str] = Query(None, description="테넌트 ID 필터"),
    current_user: Optional[UserContext] = Depends(get_optional_user),
):
    """대시보드 요약 데이터 (단일 호출로 KPI + 차트 + 최근 활동 + 시스템 현황 제공)

    - period: today(오늘), week(이번 주), month(이번 달)
    - scope 기반 필터: GLOBAL=전체, TENANT=자기 테넌트, USER=본인
    """
    if period not in ("today", "week", "month"):
        period = "today"

    tenant_id, user_id = _apply_scope_filter(current_user, tenant_id, None)

    try:
        data = dashboard_service.get_summary(
            period=period,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[DASHBOARD] Summary API failed: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
