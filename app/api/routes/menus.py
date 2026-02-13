"""메뉴 관리 API 라우터

위치: app/api/routes/menus.py
메뉴 트리 CRUD (MENU_MGMT 권한 필요)
"""
from fastapi import APIRouter, Depends, Request

from app.api.services.menu_service import menu_service
from app.core.errors import success_response
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.menu import MenuCreate, MenuUpdate

router = APIRouter(prefix="/api/admin/v1/menus", tags=["admin-menus"])


@router.get("")
async def get_menu_tree(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "read")),
):
    """메뉴 트리 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.get_menu_tree(request_id)
    return success_response(result)


@router.post("")
async def create_menu(
    data: MenuCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "create")),
):
    """메뉴 추가"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.create_menu(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{menu_id}")
async def get_menu(
    menu_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "read")),
):
    """메뉴 상세 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.get_menu(menu_id, request_id)
    return success_response(result)


@router.put("/{menu_id}")
async def update_menu(
    menu_id: int,
    data: MenuUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "update")),
):
    """메뉴 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.update_menu(menu_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "delete")),
):
    """메뉴 삭제 (하위 메뉴 존재 시 불가)"""
    request_id = getattr(request.state, "request_id", "")
    menu_service.delete_menu(menu_id, current_user, request_id)
    return success_response({"message": "메뉴가 삭제되었습니다"})
