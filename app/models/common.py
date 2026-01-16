"""
공통 API 응답 스키마

모든 API에서 공통으로 사용하는 기본 응답 모델
"""
from typing import Optional

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    success: bool = False
