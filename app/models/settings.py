"""
시스템 설정 스키마

설정 조회/수정, API 키 검증 관련 모델
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===================================
# 설정 조회
# ===================================

class SettingItem(BaseModel):
    """개별 설정 항목"""
    category: str
    key: str
    value: str
    value_type: str = "string"
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: Optional[datetime] = None


class SettingItemResponse(BaseModel):
    """설정 항목 응답 (마스킹 처리)"""
    category: str
    key: str
    value: str  # is_secret=True인 경우 마스킹됨
    value_type: str
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: Optional[datetime] = None


class SettingsCategoryResponse(BaseModel):
    """카테고리별 설정 응답"""
    category: str
    settings: List[SettingItemResponse]


class AllSettingsResponse(BaseModel):
    """전체 설정 응답"""
    categories: List[SettingsCategoryResponse]


# ===================================
# 설정 수정
# ===================================

class SettingUpdateRequest(BaseModel):
    """단일 설정 수정 요청"""
    value: str = Field(..., description="설정 값")

    model_config = {
        "json_schema_extra": {
            "example": {
                "value": "gpt-4-turbo"
            }
        }
    }


class SettingsBulkUpdateRequest(BaseModel):
    """카테고리별 설정 일괄 수정 요청"""
    settings: Dict[str, str] = Field(..., description="key-value 쌍")

    model_config = {
        "json_schema_extra": {
            "example": {
                "settings": {
                    "model": "gpt-4-turbo",
                    "temperature": "0.2",
                    "max_tokens": "3000"
                }
            }
        }
    }


class SettingsUpdateResponse(BaseModel):
    """설정 수정 응답"""
    success: bool
    message: str
    updated_count: int = 0


# ===================================
# API 키 검증
# ===================================

class ApiKeyValidationRequest(BaseModel):
    """API 키 검증 요청"""
    api_key: str = Field(..., min_length=1, description="검증할 API Key")


class ApiKeyValidationResponse(BaseModel):
    """API 키 검증 응답"""
    valid: bool
    message: str
    models: Optional[List[str]] = None  # 사용 가능한 모델 목록
