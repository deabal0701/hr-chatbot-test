"""코드 관리 API 라우터 (Phase A: 코드 관리 시스템)

LLM 제공자, 모델, 임베딩 모델 등 코드성 데이터 관리를 위한 REST API
"""
from fastapi import APIRouter, Depends, status

from app.core.security.permission import require_menu_permission
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext
from app.models.codes import (
    CodeItem,
    CodeGroupItem,
    CodeGroupResponse,
    CodeCreateRequest,
    CodeUpdateRequest,
    CodeReorderRequest,
)
from app.api.services.code_service import code_service
from app.core.errors import APIException, ErrorCode, success_response
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# 공개 코드 조회 라우터 (인증만 필요, CODE_MGMT 권한 불필요)
lookup_router = APIRouter(prefix="/api/v1/codes", tags=["codes-lookup"])


@lookup_router.get("/{code_group}")
async def lookup_codes(code_group: str, _current_user: UserContext = Depends(get_current_active_user)):
    """코드 조회 (공통 - 인증만 필요, 메뉴 권한 불필요)"""
    try:
        codes = code_service.get_codes_by_group(code_group, include_inactive=False)
        response = CodeGroupResponse(
            code_group=code_group,
            items=[CodeItem(**code) for code in codes],
            total=len(codes)
        )
        return success_response(response.model_dump())
    except Exception as e:
        logger.error(f"코드 조회 실패 ({code_group}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/codes/groups", tags=["codes"])
async def get_code_groups(current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "read"))):
    """모든 코드 그룹 목록 조회"""
    try:
        groups = code_service.get_code_groups()
        items = [CodeGroupItem(**group).model_dump() for group in groups]
        return success_response({"items": items, "total": len(items)})
    except Exception as e:
        logger.error(f"코드 그룹 조회 API 실패: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/codes/{code_group}", tags=["codes"])
async def get_codes(code_group: str, include_inactive: bool = False, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "read"))):
    """특정 그룹의 코드 목록 조회"""
    try:
        codes = code_service.get_codes_by_group(code_group, include_inactive)
        response = CodeGroupResponse(
            code_group=code_group,
            items=[CodeItem(**code) for code in codes],
            total=len(codes)
        )
        return success_response(response.model_dump())
    except Exception as e:
        logger.error(f"코드 조회 API 실패 (그룹: {code_group}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/codes/item/{code_id}", tags=["codes"])
async def get_code(code_id: int, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "read"))):
    """코드 단건 조회"""
    try:
        code = code_service.get_code_by_id(code_id)
        if not code:
            raise APIException(error_code=ErrorCode.CODE_NOT_FOUND, message=f"코드를 찾을 수 없습니다: {code_id}")
        response = CodeItem(**code)
        return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"코드 조회 API 실패 (ID: {code_id}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/codes", status_code=status.HTTP_201_CREATED, tags=["codes"])
async def create_code(request: CodeCreateRequest, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "create"))):
    """코드 생성 (사용자 코드만, is_system=False)"""
    try:
        code_data = request.model_dump(exclude_none=True)
        created_code = code_service.create_code(code_data)
        response = CodeItem(**created_code)
        return success_response(response.model_dump())
    except ValueError as e:
        logger.warning(f"코드 생성 검증 실패: {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"코드 생성 API 실패: {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/codes/{code_id}", tags=["codes"])
async def update_code(code_id: int, request: CodeUpdateRequest, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "update"))):
    """코드 수정"""
    try:
        code_data = request.model_dump(exclude_none=True)
        updated_code = code_service.update_code(code_id, code_data)
        response = CodeItem(**updated_code)
        return success_response(response.model_dump())
    except ValueError as e:
        logger.warning(f"코드 수정 검증 실패 (ID: {code_id}): {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"코드 수정 API 실패 (ID: {code_id}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/codes/{code_id}", tags=["codes"])
async def delete_code(code_id: int, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "delete"))):
    """코드 삭제 (시스템 코드는 삭제 불가)"""
    try:
        code_service.delete_code(code_id)
        return success_response({"message": f"코드가 삭제되었습니다: {code_id}", "deleted_count": 1})
    except ValueError as e:
        logger.warning(f"코드 삭제 검증 실패 (ID: {code_id}): {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"코드 삭제 API 실패 (ID: {code_id}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/codes/{code_group}/reorder", tags=["codes"])
async def reorder_codes(code_group: str, request: CodeReorderRequest, current_user: UserContext = Depends(require_menu_permission("CODE_MGMT", "update"))):
    """코드 순서 변경 (일괄 업데이트)"""
    try:
        code_service.reorder_codes(code_group, request.code_ids)
        return success_response({"message": f"코드 순서 변경 완료: {code_group}", "updated_count": len(request.code_ids)})
    except ValueError as e:
        logger.warning(f"코드 순서 변경 검증 실패 (그룹: {code_group}): {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"코드 순서 변경 API 실패 (그룹: {code_group}): {e}")
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
