"""사용자 관리 API 라우터 (v2.0 - 메뉴 기반)

위치: app/api/routes/users.py
사용자 CRUD + 메뉴 권한 할당/조회
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.api.services.user_service import user_service
from app.core.errors import APIException, ErrorCode, success_response
from app.core.security.dependencies import get_current_active_user
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.menu import UserMenuAssign
from app.models.user import UserCreate, UserUpdate

router = APIRouter(prefix="/api/admin/v1/users", tags=["admin-users"])


@router.get("/options/roles")
async def get_role_options(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """역할 선택 옵션 (사용자 생성/수정 폼용, USER_MGMT:read 권한으로 접근)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_role_options(current_user, request_id)
    return success_response(result)


@router.get("/options/tenants")
async def get_tenant_options(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """테넌트 선택 옵션 (사용자 생성/수정 폼용, USER_MGMT:read 권한으로 접근)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_tenant_options(current_user, request_id)
    return success_response(result)


@router.get("/options/menus")
async def get_menu_options(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """메뉴 선택 옵션 (사용자 메뉴 권한 할당용, USER_MGMT:read 권한으로 접근)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_menu_options(current_user, request_id)
    return success_response(result)


@router.get("")
async def list_users(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    tenant_id: Optional[int] = Query(None, description="테넌트 필터 (GLOBAL만)"),
    is_active: Optional[bool] = Query(None, description="활성화 필터"),
    keyword: Optional[str] = Query(None, description="이름/로그인ID 검색"),
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """사용자 목록 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.list_users(current_user, request_id, limit, offset, tenant_id, is_active, keyword)
    return success_response(result)


@router.post("")
async def create_user(
    data: UserCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "create")),
):
    """사용자 생성"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.create_user(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(get_current_active_user),
):
    """사용자 상세 조회 (본인 또는 USER_MGMT:read 권한)"""
    if current_user.user_id != user_id and not current_user.is_superuser:
        raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user(user_id, current_user, request_id)
    return success_response(result)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "update")),
):
    """사용자 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.update_user(user_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "delete")),
):
    """사용자 삭제"""
    request_id = getattr(request.state, "request_id", "")
    user_service.delete_user(user_id, current_user, request_id)
    return success_response({"message": "사용자가 삭제되었습니다"})


@router.put("/{user_id}/menus")
async def assign_menus(
    user_id: int,
    data: UserMenuAssign,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "update")),
):
    """사용자 메뉴 권한 할당 (replace 방식)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.assign_menus(user_id, data.menus, current_user, request_id)
    return success_response(result)


@router.get("/{user_id}/menus")
async def get_user_menus(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """사용자 메뉴 권한 조회 (USER_MGMT:read 권한)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user_menus(user_id, current_user, request_id)
    return success_response(result)
