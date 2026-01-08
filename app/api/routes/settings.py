"""시스템 설정 관리 API 라우터 (Admin API)

시스템 설정을 조회하고 수정할 수 있는 API.
API Key, 모델 설정, RAG/NL2SQL 파라미터 등을 관리.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
import httpx

from app.models.schemas import (
    SettingItemResponse,
    SettingsCategoryResponse,
    AllSettingsResponse,
    SettingUpdateRequest,
    SettingsBulkUpdateRequest,
    SettingsUpdateResponse,
    ApiKeyValidationRequest,
    ApiKeyValidationResponse,
)
from app.services.settings_service import settings_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin/v1/settings", tags=["admin-settings"])


# ============================================
# 설정 조회
# ============================================

@router.get("", response_model=AllSettingsResponse)
async def get_all_settings():
    """
    전체 설정 조회

    모든 카테고리의 설정을 조회합니다.
    비밀 값(API Key 등)은 마스킹 처리되어 반환됩니다.
    """
    try:
        all_settings = settings_service.get_all_masked_settings()

        categories = []
        for category, settings in all_settings.items():
            categories.append(SettingsCategoryResponse(
                category=category,
                settings=[SettingItemResponse(**s) for s in settings]
            ))

        return AllSettingsResponse(categories=categories)

    except Exception as e:
        logger.error(f"전체 설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{category}", response_model=SettingsCategoryResponse)
async def get_category_settings(category: str):
    """
    카테고리별 설정 조회

    특정 카테고리의 모든 설정을 조회합니다.

    카테고리:
    - openai: OpenAI API 설정
    - embedding: 임베딩 모델 설정
    - llm: LLM 모델 설정
    - rag: RAG 검색 설정
    - nl2sql: NL2SQL 설정
    - chunking: 청킹 설정
    """
    try:
        # 유효한 카테고리 확인
        if category not in settings_service.DEFAULTS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알 수 없는 카테고리: {category}"
            )

        settings = settings_service.get_masked_settings(category)

        return SettingsCategoryResponse(
            category=category,
            settings=[SettingItemResponse(**s) for s in settings]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{category}/{key}", response_model=SettingItemResponse)
async def get_setting(category: str, key: str):
    """
    단일 설정 조회

    특정 카테고리의 특정 키 설정을 조회합니다.
    """
    try:
        setting = settings_service.get_setting(category, key)

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"설정을 찾을 수 없습니다: {category}.{key}"
            )

        # 마스킹 처리
        value = setting['value']
        if setting.get('is_secret') and value:
            value = settings_service.mask_secret_value(value)

        return SettingItemResponse(
            category=category,
            key=key,
            value=value,
            value_type=setting.get('value_type', 'string'),
            description=setting.get('description'),
            is_secret=setting.get('is_secret', False),
            updated_at=setting.get('updated_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{category}/{key}/reveal", response_model=SettingItemResponse)
async def reveal_setting(category: str, key: str):
    """
    단일 설정 조회 (마스킹 없이)

    특정 카테고리의 특정 키 설정을 마스킹 없이 조회합니다.
    주의: 민감한 정보(API 키 등)를 노출하므로 보안에 주의해야 합니다.
    """
    try:
        setting = settings_service.get_setting(category, key)

        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"설정을 찾을 수 없습니다: {category}.{key}"
            )

        # 마스킹 처리 없이 원본 값 반환
        return SettingItemResponse(
            category=category,
            key=key,
            value=setting['value'],
            value_type=setting.get('value_type', 'string'),
            description=setting.get('description'),
            is_secret=setting.get('is_secret', False),
            updated_at=setting.get('updated_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# 설정 수정
# ============================================

@router.put("/{category}/{key}", response_model=SettingsUpdateResponse)
async def update_setting(category: str, key: str, request: SettingUpdateRequest):
    """
    단일 설정 수정

    특정 카테고리의 특정 키 값을 수정합니다.
    """
    try:
        # 유효한 설정 키인지 확인
        if category not in settings_service.DEFAULTS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알 수 없는 카테고리: {category}"
            )

        if key not in settings_service.DEFAULTS[category]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알 수 없는 설정 키: {category}.{key}"
            )

        success = settings_service.set_setting(category, key, request.value)

        if success:
            logger.info(f"설정 수정 완료: {category}.{key}")
            return SettingsUpdateResponse(
                success=True,
                message=f"설정이 수정되었습니다: {category}.{key}",
                updated_count=1
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="설정 수정에 실패했습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 수정 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{category}", response_model=SettingsUpdateResponse)
async def update_category_settings(category: str, request: SettingsBulkUpdateRequest):
    """
    카테고리별 설정 일괄 수정

    특정 카테고리의 여러 설정을 한 번에 수정합니다.
    """
    try:
        # 유효한 카테고리 확인
        if category not in settings_service.DEFAULTS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알 수 없는 카테고리: {category}"
            )

        success_count, failed_keys = settings_service.set_category_settings(
            category, request.settings
        )

        if failed_keys:
            return SettingsUpdateResponse(
                success=False,
                message=f"{success_count}개 수정, {len(failed_keys)}개 실패: {', '.join(failed_keys)}",
                updated_count=success_count
            )
        else:
            return SettingsUpdateResponse(
                success=True,
                message=f"{success_count}개 설정이 수정되었습니다.",
                updated_count=success_count
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카테고리 설정 수정 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 수정 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# 설정 초기화
# ============================================

@router.post("/{category}/reset", response_model=SettingsUpdateResponse)
async def reset_category_settings(category: str):
    """
    카테고리 설정 초기화

    특정 카테고리의 모든 설정을 기본값으로 초기화합니다.
    """
    try:
        if category not in settings_service.DEFAULTS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알 수 없는 카테고리: {category}"
            )

        success = settings_service.reset_category(category)

        if success:
            return SettingsUpdateResponse(
                success=True,
                message=f"{category} 카테고리가 기본값으로 초기화되었습니다.",
                updated_count=len(settings_service.DEFAULTS[category])
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="설정 초기화에 실패했습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"설정 초기화 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 초기화 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# API 키 검증
# ============================================

@router.post("/validate-api-key", response_model=ApiKeyValidationResponse)
async def validate_api_key(request: ApiKeyValidationRequest):
    """
    OpenAI API 키 검증

    제공된 API 키가 유효한지 확인합니다.
    유효한 경우 사용 가능한 모델 목록도 반환합니다.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={
                    "Authorization": f"Bearer {request.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]

                # 주요 모델만 필터링
                important_models = [
                    m for m in models
                    if any(key in m for key in ["gpt-4", "gpt-3.5", "text-embedding"])
                ]

                return ApiKeyValidationResponse(
                    valid=True,
                    message="API 키가 유효합니다.",
                    models=sorted(important_models)
                )

            elif response.status_code == 401:
                return ApiKeyValidationResponse(
                    valid=False,
                    message="API 키가 유효하지 않습니다."
                )

            else:
                return ApiKeyValidationResponse(
                    valid=False,
                    message=f"API 검증 실패: {response.status_code}"
                )

    except httpx.TimeoutException:
        return ApiKeyValidationResponse(
            valid=False,
            message="API 서버 응답 시간 초과"
        )
    except Exception as e:
        logger.error(f"API 키 검증 실패: {e}", exc_info=True)
        return ApiKeyValidationResponse(
            valid=False,
            message=f"검증 중 오류 발생: {str(e)}"
        )


# ============================================
# 캐시 관리
# ============================================

@router.post("/refresh-cache", response_model=SettingsUpdateResponse)
async def refresh_settings_cache():
    """
    설정 캐시 새로고침

    메모리에 캐시된 설정을 DB에서 다시 로드합니다.
    """
    try:
        settings_service.refresh_cache()
        return SettingsUpdateResponse(
            success=True,
            message="설정 캐시가 새로고침되었습니다.",
            updated_count=0
        )

    except Exception as e:
        logger.error(f"캐시 새로고침 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐시 새로고침 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# 외부 데이터베이스 연결 테스트
# ============================================

@router.post("/external-database/test")
async def test_external_database_connection(request: dict):
    """
    외부 비즈니스 데이터베이스 연결 테스트

    NL2SQL에서 사용할 외부 DB 연결 정보가 유효한지 테스트합니다.
    """
    try:
        import psycopg

        db_type = request.get("db_type", "postgresql")
        host = request.get("host")
        port = request.get("port", 5432)
        database = request.get("database")
        username = request.get("username")
        password = request.get("password")
        schema = request.get("schema", "business")

        # 필수 파라미터 검증
        if not all([host, database, username]):
            return {
                "success": False,
                "message": "호스트, 데이터베이스, 사용자명은 필수입니다."
            }

        # PostgreSQL만 지원
        if db_type != "postgresql":
            return {
                "success": False,
                "message": f"지원하지 않는 DB 타입: {db_type} (현재 PostgreSQL만 지원)"
            }

        # 연결 URL 생성
        connection_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        # 연결 테스트
        with psycopg.connect(connection_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                # 기본 연결 확인
                cur.execute("SELECT 1")

                # 스키마 존재 확인
                cur.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                """, (schema,))

                if not cur.fetchone():
                    return {
                        "success": False,
                        "message": f"스키마 '{schema}'가 존재하지 않습니다."
                    }

                # 스키마 내 테이블 개수 확인
                cur.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                """, (schema,))

                table_count = cur.fetchone()[0]

        return {
            "success": True,
            "message": f"연결 성공! (스키마: {schema}, 테이블 수: {table_count})"
        }

    except psycopg.OperationalError as e:
        error_msg = str(e).lower()
        if "password authentication failed" in error_msg:
            message = "인증 실패: 사용자명 또는 비밀번호가 올바르지 않습니다."
        elif "does not exist" in error_msg:
            message = "데이터베이스가 존재하지 않습니다."
        elif "connection refused" in error_msg or "could not connect" in error_msg:
            message = f"서버에 연결할 수 없습니다: {host}:{port}"
        else:
            message = f"연결 오류: {str(e)}"

        logger.error(f"외부 DB 연결 테스트 실패: {message}")
        return {
            "success": False,
            "message": message
        }

    except Exception as e:
        logger.error(f"외부 DB 연결 테스트 중 예외 발생: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"연결 테스트 실패: {str(e)}"
        }
