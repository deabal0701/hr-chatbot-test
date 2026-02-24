"""부서(조직) 관리 API 라우터

위치: app/api/routes/departments.py
부서 트리 CRUD + 순서 변경 (DEPT_MGMT 권한 필요)
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.services.department_service import department_service
from app.core.errors.response import success_response
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.department import DeptCreate, DeptReorderRequest, DeptUpdate

router = APIRouter(prefix="/api/admin/v1/departments", tags=["admin-departments"])


@router.get("")
async def get_department_tree(
    request: Request,
    tenant_id: Optional[int] = Query(None, description="테넌트 ID 필터 (GLOBAL만 사용)"),
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "read")),
):
    """부서 트리 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = department_service.get_department_tree(tenant_id, current_user, request_id)
    return success_response(result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DeptCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "create")),
):
    """부서 추가"""
    request_id = getattr(request.state, "request_id", "")
    result = department_service.create_department(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.put("/reorder")
async def reorder_departments(
    data: DeptReorderRequest,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "update")),
):
    """부서 순서 일괄 변경 (드래그앤드롭용)"""
    request_id = getattr(request.state, "request_id", "")
    result = department_service.reorder_departments(data.items, request_id)
    return success_response(result)


@router.get("/{dept_id}")
async def get_department(
    dept_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "read")),
):
    """부서 상세 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = department_service.get_department(dept_id, request_id)
    return success_response(result)


@router.put("/{dept_id}")
async def update_department(
    dept_id: int,
    data: DeptUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "update")),
):
    """부서 수정 (parent_dept_id 변경 시 depth 자동 재계산)"""
    request_id = getattr(request.state, "request_id", "")
    result = department_service.update_department(dept_id, data.model_dump(exclude_unset=True), current_user, request_id)
    return success_response(result)


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("DEPT_MGMT", "delete")),
):
    """부서 삭제 (하위 부서 또는 소속 사용자 있으면 불가)"""
    request_id = getattr(request.state, "request_id", "")
    department_service.delete_department(dept_id, current_user, request_id)
    return success_response({"message": "부서가 삭제되었습니다", "deleted_count": 1})
