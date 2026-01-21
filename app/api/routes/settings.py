"""시스템 설정 관리 API 라우터 (Admin API)

위치: app/api/routes/settings.py
- HTTP 요청/응답 처리
- 예외 변환
- 비즈니스 로직은 settings_service에 위임
"""
from fastapi import APIRouter, HTTPException, status

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
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin/v1/settings", tags=["admin-settings"])


# ============================================
# 설정 조회
# ============================================

@router.get("", response_model=AllSettingsResponse)
async def get_all_settings():
    """전체 설정 조회 (마스킹 적용)"""
    try:
        all_settings = settings_service.get_all_settings_masked()
        categories = [
            SettingsCategoryResponse(category=cat, settings=[SettingItemResponse(**s) for s in settings_list])
            for cat, settings_list in all_settings.items()
        ]
        return AllSettingsResponse(categories=categories)
    except Exception as e:
        logger.error(f"전체 설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{category}", response_model=SettingsCategoryResponse)
async def get_category_settings(category: str):
    """카테고리별 설정 조회 (마스킹 적용)"""
    try:
        if not settings_service.is_valid_category(category):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"알 수 없는 카테고리: {category}")

        settings_list = settings_service.get_category_settings_masked(category)
        return SettingsCategoryResponse(category=category, settings=[SettingItemResponse(**s) for s in settings_list])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}")


# ============================================
# 프롬프트 이력 관리
# ============================================

@router.get("/prompt/history")
async def get_prompt_history(limit: int = 100):
    """전체 프롬프트 변경 이력 조회"""
    try:
        history = settings_service.get_prompt_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"프롬프트 이력 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"프롬프트 이력 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/prompt/history/{category}/{key}")
async def get_prompt_history_by_key(category: str, key: str, limit: int = 50):
    """특정 프롬프트의 변경 이력 조회"""
    try:
        history = settings_service.get_prompt_history_by_key(category, key, limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"프롬프트 이력 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"프롬프트 이력 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/prompt/restore/{history_id}")
async def restore_prompt_from_history(history_id: int):
    """프롬프트 원복"""
    try:
        success = settings_service.restore_prompt_from_history(history_id, changed_by='admin')
        if success:
            return {"success": True, "message": "프롬프트가 복원되었습니다."}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="복원할 이력을 찾을 수 없습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프롬프트 복원 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"프롬프트 복원 중 오류가 발생했습니다: {str(e)}")


@router.get("/{category}/{key}", response_model=SettingItemResponse)
async def get_setting(category: str, key: str):
    """단일 설정 조회 (마스킹 적용)"""
    try:
        setting = settings_service.get_setting(category, key, masked=True)
        if not setting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"설정을 찾을 수 없습니다: {category}.{key}")
        return SettingItemResponse(**setting)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{category}/{key}/reveal", response_model=SettingItemResponse)
async def reveal_setting(category: str, key: str):
    """단일 설정 조회 (마스킹 없이)"""
    try:
        setting = settings_service.get_setting(category, key, masked=False)
        if not setting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"설정을 찾을 수 없습니다: {category}.{key}")
        return SettingItemResponse(**setting)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}")


# ============================================
# 설정 수정
# ============================================

@router.put("/{category}/{key}", response_model=SettingsUpdateResponse)
async def update_setting(category: str, key: str, request: SettingUpdateRequest):
    """단일 설정 수정"""
    try:
        if not settings_service.is_valid_category(category):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"알 수 없는 카테고리: {category}")
        if not settings_service.is_valid_key(category, key):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"알 수 없는 설정 키: {category}.{key}")

        success = settings_service.update_setting(category, key, request.value)
        if success:
            logger.info(f"설정 수정 완료: {category}.{key}")
            return SettingsUpdateResponse(success=True, message=f"설정이 수정되었습니다: {category}.{key}", updated_count=1)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="설정 수정에 실패했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 수정 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 수정 중 오류가 발생했습니다: {str(e)}")


@router.put("/{category}", response_model=SettingsUpdateResponse)
async def update_category_settings(category: str, request: SettingsBulkUpdateRequest):
    """카테고리별 설정 일괄 수정"""
    try:
        if not settings_service.is_valid_category(category):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"알 수 없는 카테고리: {category}")

        success_count, failed_keys = settings_service.update_category_settings(category, request.settings)

        if failed_keys:
            return SettingsUpdateResponse(success=False, message=f"{success_count}개 수정, {len(failed_keys)}개 실패: {', '.join(failed_keys)}", updated_count=success_count)
        else:
            return SettingsUpdateResponse(success=True, message=f"{success_count}개 설정이 수정되었습니다.", updated_count=success_count)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 수정 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 수정 중 오류가 발생했습니다: {str(e)}")


# ============================================
# 설정 초기화
# ============================================

@router.post("/{category}/reset", response_model=SettingsUpdateResponse)
async def reset_category_settings(category: str):
    """카테고리 설정 초기화"""
    try:
        if not settings_service.is_valid_category(category):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"알 수 없는 카테고리: {category}")

        success = settings_service.reset_category(category)
        if success:
            return SettingsUpdateResponse(success=True, message=f"{category} 카테고리가 기본값으로 초기화되었습니다.", updated_count=settings_service.get_category_key_count(category))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="설정 초기화에 실패했습니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 초기화 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"설정 초기화 중 오류가 발생했습니다: {str(e)}")


# ============================================
# API 키 검증
# ============================================

@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(request: ApiKeyValidationRequest):
    """OpenAI API 키 검증"""
    result = await settings_service.validate_openai_api_key(request.api_key)
    return ApiKeyValidationResponse(**result)


# ============================================
# 캐시 관리
# ============================================

@router.post("/refresh-cache", response_model=SettingsUpdateResponse)
async def refresh_settings_cache():
    """설정 캐시 새로고침"""
    try:
        settings_service.refresh_cache()
        return SettingsUpdateResponse(success=True, message="설정 캐시가 새로고침되었습니다.", updated_count=0)
    except Exception as e:
        logger.error(f"캐시 새로고침 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"캐시 새로고침 중 오류가 발생했습니다: {str(e)}")


# ============================================
# 외부 데이터베이스 연결 테스트
# ============================================

@router.post("/external-database/test")
async def test_external_database_connection(request: dict):
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
    return result
