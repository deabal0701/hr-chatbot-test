"""역할 관리 API 라우터 (v2.0 - 메뉴 기반)

위치: app/api/routes/roles.py
역할 CRUD + 역할별 기본 메뉴 조회 (ROLE_MGMT 권한 필요)
"""
from fastapi import APIRouter, Depends, Request

from app.api.services.role_service import role_service
from app.core.errors import success_response
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.user import RoleCreate, RoleUpdate

router = APIRouter(prefix="/api/admin/v1/roles", tags=["admin-roles"])


# 고정 경로를 파라미터 경로보다 먼저 배치
@router.get("/default-menus/{role_code}")
async def get_default_menus(
    role_code: str,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "read")),
):
    """역할별 기본 메뉴 권한 목록 (사용자 생성 시 자동 체크용)"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.get_default_menus(role_code.upper(), request_id)
    return success_response(result)


@router.get("")
async def list_roles(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "read")),
):
    """역할 목록 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.list_roles(request_id)
    return success_response(result)


@router.post("")
async def create_role(
    data: RoleCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "create")),
):
    """역할 생성"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.create_role(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{role_id}")
async def get_role(
    role_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "read")),
):
    """역할 상세 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.get_role(role_id, request_id)
    return success_response(result)


@router.put("/{role_id}")
async def update_role(
    role_id: int,
    data: RoleUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "update")),
):
    """역할 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.update_role(role_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "delete")),
):
    """역할 삭제 (시스템 역할 불가)"""
    request_id = getattr(request.state, "request_id", "")
    role_service.delete_role(role_id, current_user, request_id)
    return success_response({"message": "역할이 삭제되었습니다"})
