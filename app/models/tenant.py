"""
테넌트(고객사) 관리 스키마

위치: app/models/tenant.py
테넌트 CRUD 관련 모델
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 테넌트 (Tenant)
# ===================================

class TenantBase(BaseModel):
    """테넌트 기본 필드"""
    tenant_code: str = Field(..., min_length=1, max_length=50, description="테넌트 코드")
    tenant_name: str = Field(..., min_length=1, max_length=200, description="테넌트명")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보 (업종, 계약정보 등)")

    @field_validator("tenant_code")
    @classmethod
    def validate_tenant_code(cls, v: str) -> str:
        """테넌트 코드: 영문 대문자 + 숫자 + 언더스코어만 허용"""
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("테넌트 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
        return v


class TenantCreate(TenantBase):
    """테넌트 생성 요청"""
    is_active: bool = Field(default=True, description="활성화 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_code": "COMPANY_A",
                "tenant_name": "A 주식회사",
                "metadata": {"industry": "IT", "contract_type": "enterprise"},
                "is_active": True
            }
        }
    }


class TenantUpdate(BaseModel):
    """테넌트 수정 요청 (모든 필드 Optional)"""
    tenant_name: Optional[str] = Field(None, max_length=200, description="테넌트명")
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_name": "A 주식회사 (수정)",
                "metadata": {"industry": "IT", "contract_type": "premium"}
            }
        }
    }


class TenantResponse(BaseModel):
    """테넌트 상세 응답"""
    tenant_id: int = Field(..., description="테넌트 ID")
    tenant_code: str = Field(..., description="테넌트 코드")
    tenant_name: str = Field(..., description="테넌트명")
    is_active: bool = Field(..., description="활성화 여부")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보")
    user_count: int = Field(default=0, description="소속 사용자 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_id": 1,
                "tenant_code": "SYSTEM",
                "tenant_name": "시스템",
                "is_active": True,
                "metadata": {"type": "internal"},
                "user_count": 1,
                "created_at": "2026-02-06T09:00:00+09:00",
                "updated_at": "2026-02-06T09:00:00+09:00"
            }
        }
    }


class TenantListResponse(BaseModel):
    """테넌트 목록 응답"""
    total: int = Field(..., description="전체 테넌트 수")
    items: List[TenantResponse] = Field(default_factory=list, description="테넌트 목록")
