"""
공통 API 응답 스키마

위치: app/models/common.py
모든 API에서 공통으로 사용하는 기본 응답 모델

표준 응답 구조:
{
    "success": true/false,
    "data": { ... } or null,
    "error": { "code": "...", "message": "...", "detail": "..." } or null
}
"""
from typing import TypeVar, Generic, Optional, Any

from pydantic import BaseModel, Field

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """
    에러 상세 정보

    Attributes:
        code: 에러 코드 (VALIDATION_ERROR, NOT_FOUND 등)
        message: 사용자 친화적 에러 메시지
        detail: 개발자용 상세 정보 (선택)
    """
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="사용자 친화적 에러 메시지")
    detail: Optional[str] = Field(None, description="개발자용 상세 정보")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "입력값이 올바르지 않습니다",
                "detail": "query field is required"
            }
        }
    }


class APIResponse(BaseModel, Generic[T]):
    """
    통일된 API 응답 래퍼

    모든 API 응답을 일관된 구조로 래핑합니다.

    성공 응답:
        {
            "success": true,
            "data": { ... },
            "error": null
        }

    실패 응답:
        {
            "success": false,
            "data": null,
            "error": {
                "code": "ERROR_CODE",
                "message": "사용자 메시지",
                "detail": "개발자용 상세"
            }
        }
    """
    success: bool = Field(..., description="성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    error: Optional[ErrorDetail] = Field(None, description="에러 정보")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"query": "2024년 입사자 수", "answer": "27명입니다"},
                    "error": None
                },
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "SEARCH_FAILED",
                        "message": "검색에 실패했습니다",
                        "detail": "Database connection timeout"
                    }
                }
            ]
        }
    }


# ========== 레거시 호환용 (기존 코드 지원) ==========

class MessageResponse(BaseModel):
    """일반 메시지 응답 (레거시)"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """에러 응답 (레거시)"""
    error: str
    detail: Optional[str] = None
    success: bool = False
