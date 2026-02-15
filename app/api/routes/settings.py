"""시스템 설정 관리 API 라우터 (Admin API)

위치: app/api/routes/settings.py
- HTTP 요청/응답 처리
- 예외 변환
- 비즈니스 로직은 settings_service에 위임
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.settings import (
    SettingItemResponse,
    SettingsCategoryResponse,
    AllSettingsResponse,
    SettingUpdateRequest,
    SettingsBulkUpdateRequest,
    SettingsUpdateResponse,
    ApiKeyValidationRequest,
    ApiKeyValidationResponse,
)
from app.api.services.settings_service import settings_service
from app.core.errors import APIException, ErrorCode, success_response
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin/v1/settings", tags=["admin-settings"])


# ============================================
# 설정 조회
# ============================================

@router.get("")
async def get_all_settings(
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))
):
    """전체 설정 조회 (마스킹 적용)"""
    try:
        # TENANT 역할: 자기 테넌트 강제
        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        if tenant_id == '1':
            all_settings = settings_service.get_all_settings_masked()
        else:
            all_settings = settings_service.get_tenant_settings_merged(tenant_id)

        categories = [
            SettingsCategoryResponse(category=cat, settings=[SettingItemResponse(**s) for s in settings_list])
            for cat, settings_list in all_settings.items()
        ]
        response = AllSettingsResponse(categories=categories)
        return success_response(response.model_dump())
    except Exception as e:
        logger.error(f"전체 설정 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/{category}")
async def get_category_settings(
    category: str,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))
):
    """카테고리별 설정 조회 (마스킹 적용)"""
    try:
        if not settings_service.is_valid_category(category):
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"알 수 없는 카테고리: {category}")

        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        settings_list = settings_service.get_category_settings_masked(category, tenant_id=tenant_id)
        response = SettingsCategoryResponse(category=category, settings=[SettingItemResponse(**s) for s in settings_list])
        return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 프롬프트 이력 관리
# ============================================

@router.get("/prompt/history")
async def get_prompt_history(limit: int = 100, current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))):
    """전체 프롬프트 변경 이력 조회"""
    try:
        history = settings_service.get_prompt_history(limit)
        return success_response({"history": history})
    except Exception as e:
        logger.error(f"프롬프트 이력 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/prompt/history/{category}/{key}")
async def get_prompt_history_by_key(category: str, key: str, limit: int = 50, current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))):
    """특정 프롬프트의 변경 이력 조회"""
    try:
        history = settings_service.get_prompt_history_by_key(category, key, limit)
        return success_response({"history": history})
    except Exception as e:
        logger.error(f"프롬프트 이력 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/prompt/restore/{history_id}")
async def restore_prompt_from_history(history_id: int, current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))):
    """프롬프트 원복"""
    try:
        success = settings_service.restore_prompt_from_history(history_id, changed_by='admin')
        if success:
            return success_response({"message": "프롬프트가 복원되었습니다."})
        else:
            raise APIException(error_code=ErrorCode.NOT_FOUND, message="복원할 이력을 찾을 수 없습니다.")
    except APIException:
        raise
    except Exception as e:
        logger.error(f"프롬프트 복원 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/{category}/{key}")
async def get_setting(
    category: str, key: str,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))
):
    """단일 설정 조회 (마스킹 적용)"""
    try:
        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        setting = settings_service.get_setting(category, key, masked=True, tenant_id=tenant_id)
        if not setting:
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"설정을 찾을 수 없습니다: {category}.{key}")
        response = SettingItemResponse(**setting)
        return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/{category}/{key}/reveal")
async def reveal_setting(
    category: str, key: str,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))
):
    """단일 설정 조회 (마스킹 없이)"""
    try:
        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        setting = settings_service.get_setting(category, key, masked=False, tenant_id=tenant_id)
        if not setting:
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"설정을 찾을 수 없습니다: {category}.{key}")
        response = SettingItemResponse(**setting)
        return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 설정 수정
# ============================================

@router.put("/{category}/{key}")
async def update_setting(
    category: str, key: str, request: SettingUpdateRequest,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))
):
    """단일 설정 수정"""
    try:
        if not settings_service.is_valid_category(category):
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"알 수 없는 카테고리: {category}")
        if not settings_service.is_valid_key(category, key):
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"알 수 없는 설정 키: {category}.{key}")

        # TENANT 역할: 자기 테넌트 강제
        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        success = settings_service.update_setting(category, key, request.value, tenant_id=tenant_id)
        if success:
            logger.info(f"설정 수정 완료: {category}.{key} (tenant_id={tenant_id})")
            response = SettingsUpdateResponse(success=True, message=f"설정이 수정되었습니다: {category}.{key}", updated_count=1)
            return success_response(response.model_dump())
        else:
            raise APIException(error_code=ErrorCode.INTERNAL_ERROR, message="설정 수정에 실패했습니다.")
    except APIException:
        raise
    except Exception as e:
        logger.error(f"설정 수정 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/{category}")
async def update_category_settings(
    category: str, request: SettingsBulkUpdateRequest,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))
):
    """카테고리별 설정 일괄 수정"""
    try:
        if not settings_service.is_valid_category(category):
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"알 수 없는 카테고리: {category}")

        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        success_count, failed_keys = settings_service.update_category_settings(category, request.settings, tenant_id=tenant_id)

        if failed_keys:
            response = SettingsUpdateResponse(success=False, message=f"{success_count}개 수정, {len(failed_keys)}개 실패: {', '.join(failed_keys)}", updated_count=success_count)
        else:
            response = SettingsUpdateResponse(success=True, message=f"{success_count}개 설정이 수정되었습니다.", updated_count=success_count)
        return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 수정 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 설정 초기화
# ============================================

@router.post("/{category}/reset")
async def reset_category_settings(
    category: str,
    tenant_id: Optional[str] = Query('1', description="테넌트 ID"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))
):
    """카테고리 설정 초기화"""
    try:
        if not settings_service.is_valid_category(category):
            raise APIException(error_code=ErrorCode.SETTING_NOT_FOUND, message=f"알 수 없는 카테고리: {category}")

        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        if tenant_id != '1':
            # 테넌트 오버라이드 전체 삭제
            deleted = settings_service.reset_tenant_category(category, tenant_id)
            response = SettingsUpdateResponse(success=True, message=f"테넌트 오버라이드 {deleted}개가 삭제되었습니다.", updated_count=deleted)
            return success_response(response.model_dump())
        else:
            # 기존 로직: 공용 설정 기본값 복원
            success = settings_service.reset_category(category)
            if success:
                response = SettingsUpdateResponse(success=True, message=f"{category} 카테고리가 기본값으로 초기화되었습니다.", updated_count=settings_service.get_category_key_count(category))
                return success_response(response.model_dump())
            else:
                raise APIException(error_code=ErrorCode.INTERNAL_ERROR, message="설정 초기화에 실패했습니다.")
    except APIException:
        raise
    except Exception as e:
        logger.error(f"설정 초기화 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 테넌트 오버라이드 삭제
# ============================================

@router.delete("/{category}/{key}")
async def delete_tenant_override(
    category: str, key: str,
    tenant_id: str = Query(..., description="테넌트 ID (필수)"),
    current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))
):
    """테넌트 설정 오버라이드 삭제 (공용 기본값으로 복원)"""
    try:
        if tenant_id == '1':
            raise APIException(error_code=ErrorCode.VALIDATION_ERROR, message="공용 설정은 삭제할 수 없습니다")

        if not current_user.is_global:
            tenant_id = str(current_user.tenant_id)

        success = settings_service.delete_tenant_override(category, key, tenant_id)
        if success:
            logger.info(f"테넌트 오버라이드 삭제: {category}.{key} (tenant_id={tenant_id})")
            response = SettingsUpdateResponse(success=True, message=f"오버라이드가 삭제되었습니다: {category}.{key}", updated_count=1)
            return success_response(response.model_dump())
        else:
            response = SettingsUpdateResponse(success=True, message="삭제할 오버라이드가 없습니다.", updated_count=0)
            return success_response(response.model_dump())
    except APIException:
        raise
    except Exception as e:
        logger.error(f"오버라이드 삭제 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# API 키 검증
# ============================================

@router.post("/validate-api-key")
async def validate_api_key(request: ApiKeyValidationRequest, current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))):
    """OpenAI API 키 검증"""
    result = await settings_service.validate_openai_api_key(request.api_key)
    response = ApiKeyValidationResponse(**result)
    return success_response(response.model_dump())


# ============================================
# 캐시 관리
# ============================================

@router.post("/refresh-cache")
async def refresh_settings_cache(current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "update"))):
    """설정 캐시 새로고침"""
    try:
        settings_service.refresh_cache()
        response = SettingsUpdateResponse(success=True, message="설정 캐시가 새로고침되었습니다.", updated_count=0)
        return success_response(response.model_dump())
    except Exception as e:
        logger.error(f"캐시 새로고침 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 외부 데이터베이스 연결 테스트
# ============================================

@router.post("/external-database/test")
async def test_external_database_connection(request: dict, current_user: UserContext = Depends(require_menu_permission("SYS_SETTING", "read"))):
    """외부 비즈니스 데이터베이스 연결 테스트"""
    result = settings_service.test_external_db_connection(
        db_type=request.get("db_type", "postgresql"),
        host=request.get("host", ""),
        port=request.get("port", 5432),
        database=request.get("database", ""),
        username=request.get("username", ""),
        password=request.get("password", ""),
        schema=request.get("schema", "business")
    )
    return success_response(result)
