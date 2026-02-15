"""테넌트 관리 API 라우터

위치: app/api/routes/tenants.py
테넌트 CRUD (GLOBAL 전용 — admin:tenants 권한 필요)
"""
from fastapi import APIRouter, Depends, Request, status

from app.api.services.tenant_service import tenant_service
from app.core.errors import success_response
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.tenant import TenantCreate, TenantUpdate

router = APIRouter(prefix="/api/admin/v1/tenants", tags=["admin-tenants"])


@router.get("")
async def list_tenants(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("TENANT_MGMT", "read")),
):
    """테넌트 목록 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = tenant_service.list_tenants(request_id)
    return success_response(result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("TENANT_MGMT", "create")),
):
    """테넌트 생성"""
    request_id = getattr(request.state, "request_id", "")
    result = tenant_service.create_tenant(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("TENANT_MGMT", "read")),
):
    """테넌트 상세 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = tenant_service.get_tenant(tenant_id, request_id)
    return success_response(result)


@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("TENANT_MGMT", "update")),
):
    """테넌트 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = tenant_service.update_tenant(tenant_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("TENANT_MGMT", "delete")),
):
    """테넌트 삭제 (소속 사용자 있으면 비활성화)"""
    request_id = getattr(request.state, "request_id", "")
    tenant_service.delete_tenant(tenant_id, current_user, request_id)
    return success_response({"message": "테넌트가 삭제(또는 비활성화)되었습니다", "deleted_count": 1})
