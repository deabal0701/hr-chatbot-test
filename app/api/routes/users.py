"""사용자 관리 API 라우터

위치: app/api/routes/users.py
사용자 CRUD + 역할 할당 + 권한 조회
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.api.services.user_service import user_service
from app.core.errors import APIException, ErrorCode, success_response
from app.core.security.dependencies import get_current_active_user
from app.core.security.permission import require_permission
from app.models.auth import UserContext
from app.models.user import UserCreate, UserUpdate, UserRoleAssign

router = APIRouter(prefix="/api/admin/v1/users", tags=["admin-users"])


@router.get("")
async def list_users(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    tenant_id: Optional[int] = Query(None, description="테넌트 필터 (GLOBAL만)"),
    is_active: Optional[bool] = Query(None, description="활성화 필터"),
    keyword: Optional[str] = Query(None, description="이름/로그인ID 검색"),
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """사용자 목록 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.list_users(current_user, request_id, limit, offset, tenant_id, is_active, keyword)
    return success_response(result)


@router.post("")
async def create_user(
    data: UserCreate,
    request: Request,
    current_user: UserContext = Depends(require_permission("admin:users")),
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
    """사용자 상세 조회 (본인 또는 admin:users 권한)"""
    if current_user.user_id != user_id and not current_user.has_permission("admin:users"):
        raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user(user_id, current_user, request_id)
    return success_response(result)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """사용자 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.update_user(user_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """사용자 삭제"""
    request_id = getattr(request.state, "request_id", "")
    user_service.delete_user(user_id, current_user, request_id)
    return success_response({"message": "사용자가 삭제되었습니다"})


@router.put("/{user_id}/roles")
async def assign_roles(
    user_id: int,
    data: UserRoleAssign,
    request: Request,
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """역할 할당 (GLOBAL만 가능)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.assign_roles(user_id, data.role_ids, current_user, request_id)
    return success_response(result)


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(get_current_active_user),
):
    """사용자 권한 조회 (본인 또는 admin:users 권한)"""
    if current_user.user_id != user_id and not current_user.has_permission("admin:users"):
        raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user_permissions(user_id, current_user, request_id)
    return success_response(result)
