"""개인 대시보드 API 엔드포인트

위치: app/api/routes/personal_dashboard.py
- 대시보드 CRUD + 공유 (6개 엔드포인트)
- 위젯 CRUD + SQL 실행 (7개 엔드포인트)
- user_id 기반 본인 데이터 접근 (개인 대시보드)
- 공유 대시보드 읽기 전용 접근 지원
- 인증: get_current_active_user (로그인 필수, 메뉴 권한 불필요)
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.services.personal_dashboard_service import personal_dashboard_service
from app.core.database.sql_executor import SQLValidationError, SQLExecutionError
from app.core.errors.handlers import APIException
from app.core.errors.error_codes import ErrorCode
from app.core.errors.response import success_response
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext
from app.models.personal_dashboard import (
    DashboardCreate, DashboardUpdate, DashboardShareRequest,
    WidgetCreate, WidgetUpdate, LayoutSaveRequest, ExecuteSqlRequest,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["personal-dashboard"])


# ============================================
# 대시보드 CRUD
# ============================================

@router.get("/dashboards")
async def list_dashboards(
    current_user: UserContext = Depends(get_current_active_user),
):
    """내 대시보드 + 공유 대시보드 목록 조회"""
    try:
        data = personal_dashboard_service.list_dashboards(
            current_user.user_id, current_user.tenant_id, current_user.role_code
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[DASHBOARD] 대시보드 목록 조회 실패: user_id={current_user.user_id}, error={e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/dashboards", status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    data: DashboardCreate,
    current_user: UserContext = Depends(get_current_active_user),
):
    """대시보드 생성"""
    try:
        result = personal_dashboard_service.create_dashboard(
            current_user.user_id, current_user.tenant_id, data
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 대시보드 생성 실패: user_id={current_user.user_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: int,
    data: DashboardUpdate,
    current_user: UserContext = Depends(get_current_active_user),
):
    """대시보드 이름/설명 수정"""
    try:
        result = personal_dashboard_service.update_dashboard(
            current_user.user_id, dashboard_id, data
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 대시보드 수정 실패: dashboard_id={dashboard_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    current_user: UserContext = Depends(get_current_active_user),
):
    """대시보드 삭제 (기본 대시보드 불가)"""
    try:
        result = personal_dashboard_service.delete_dashboard(
            current_user.user_id, dashboard_id
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 대시보드 삭제 실패: dashboard_id={dashboard_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/dashboards/{dashboard_id}/default")
async def set_default_dashboard(
    dashboard_id: int,
    current_user: UserContext = Depends(get_current_active_user),
):
    """기본 대시보드 설정"""
    try:
        result = personal_dashboard_service.set_default_dashboard(
            current_user.user_id, dashboard_id
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 기본 대시보드 설정 실패: dashboard_id={dashboard_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/dashboards/{dashboard_id}/share")
async def share_dashboard(
    dashboard_id: int,
    data: DashboardShareRequest,
    current_user: UserContext = Depends(get_current_active_user),
):
    """대시보드 공유 설정 (GLOBAL/TENANT 관리자만)"""
    try:
        result = personal_dashboard_service.share_dashboard(
            current_user.user_id, dashboard_id, current_user.role_code, data
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 공유 설정 실패: dashboard_id={dashboard_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 위젯 CRUD
# ============================================

@router.get("/widgets")
async def list_widgets(
    dashboard_id: Optional[int] = Query(None, description="대시보드 ID (미지정시 기본 대시보드)"),
    current_user: UserContext = Depends(get_current_active_user),
):
    """대시보드 위젯 목록 조회"""
    try:
        data = personal_dashboard_service.list_widgets(
            current_user.user_id, dashboard_id, current_user.tenant_id
        )
        return success_response(data)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 위젯 목록 조회 실패: user_id={current_user.user_id}, error={e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/widgets", status_code=status.HTTP_201_CREATED)
async def create_widget(
    data: WidgetCreate,
    current_user: UserContext = Depends(get_current_active_user),
):
    """위젯 생성"""
    try:
        result = personal_dashboard_service.create_widget(current_user.user_id, current_user.tenant_id, data)
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 위젯 생성 실패: user_id={current_user.user_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/widgets/{widget_id}")
async def update_widget(
    widget_id: int,
    data: WidgetUpdate,
    current_user: UserContext = Depends(get_current_active_user),
):
    """위젯 수정"""
    try:
        result = personal_dashboard_service.update_widget(current_user.user_id, widget_id, data)
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 위젯 수정 실패: widget_id={widget_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/widgets/{widget_id}")
async def delete_widget(
    widget_id: int,
    current_user: UserContext = Depends(get_current_active_user),
):
    """위젯 삭제"""
    try:
        result = personal_dashboard_service.delete_widget(current_user.user_id, widget_id)
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 위젯 삭제 실패: widget_id={widget_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/layout")
async def save_layout(
    data: LayoutSaveRequest,
    current_user: UserContext = Depends(get_current_active_user),
):
    """레이아웃 일괄 저장"""
    try:
        result = personal_dashboard_service.save_layout(
            current_user.user_id, data.layout, data.dashboard_id, current_user.tenant_id
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 레이아웃 저장 실패: user_id={current_user.user_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/widgets/{widget_id}/refresh")
async def refresh_widget(
    widget_id: int,
    current_user: UserContext = Depends(get_current_active_user),
):
    """위젯 데이터 새로고침 (저장된 SQL 재실행)"""
    try:
        result = personal_dashboard_service.refresh_widget(
            current_user.user_id, widget_id, current_user.tenant_id
        )
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except SQLValidationError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except SQLExecutionError as e:
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] 위젯 새로고침 실패: widget_id={widget_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/execute-sql")
async def execute_sql(
    data: ExecuteSqlRequest,
    current_user: UserContext = Depends(get_current_active_user),
):
    """SQL 테스트 실행 (미리보기용, 저장 안함)"""
    try:
        result = personal_dashboard_service.execute_sql(data.sql)
        return success_response(result)
    except SQLValidationError as e:
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except SQLExecutionError as e:
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"[DASHBOARD] SQL 실행 실패: user_id={current_user.user_id}, error={e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
