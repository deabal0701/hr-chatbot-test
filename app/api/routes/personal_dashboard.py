"""개인 대시보드 API 엔드포인트

위치: app/api/routes/personal_dashboard.py
- 개인 대시보드 위젯 CRUD (7개 엔드포인트)
- user_id 기반 본인 위젯만 접근 (개인 대시보드)
- 인증: get_current_active_user (로그인 필수, 메뉴 권한 불필요)
"""
from fastapi import APIRouter, Depends, status

from app.api.services.personal_dashboard_service import personal_dashboard_service
from app.core.database.sql_executor import SQLValidationError, SQLExecutionError
from app.core.errors.handlers import APIException
from app.core.errors.error_codes import ErrorCode
from app.core.errors.response import success_response
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext
from app.models.personal_dashboard import (
    WidgetCreate, WidgetUpdate, LayoutSaveRequest, ExecuteSqlRequest,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["personal-dashboard"])


@router.get("/widgets")
async def list_widgets(
    current_user: UserContext = Depends(get_current_active_user),
):
    """내 위젯 목록 조회"""
    try:
        data = personal_dashboard_service.list_widgets(current_user.user_id)
        return success_response(data)
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
        result = personal_dashboard_service.save_layout(current_user.user_id, data.layout)
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
        result = personal_dashboard_service.refresh_widget(current_user.user_id, widget_id)
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
