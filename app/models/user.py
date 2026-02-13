"""
사용자/역할 관리 스키마 (v2.0 - 메뉴 기반)

위치: app/models/user.py
사용자 CRUD, 역할 관리 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.menu import UserMenuPermission


# ===================================
# 역할 (Role)
# ===================================

class RoleSimple(BaseModel):
    """역할 간략 정보 (UserResponse에 포함용)"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    scope_type: str = Field(..., description="데이터 범위")
    landing_page: str = Field(..., description="랜딩 페이지")


class RoleCreate(BaseModel):
    """역할 생성 요청"""
    role_code: str = Field(..., min_length=1, max_length=50, description="역할 코드")
    role_name: str = Field(..., min_length=1, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    landing_page: str = Field(default="/chat", max_length=200, description="로그인 후 랜딩 페이지")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        valid = ["GLOBAL", "TENANT", "USER"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_code": "DEPT_ADMIN",
                "role_name": "부서 관리자",
                "description": "부서 내 데이터만 접근",
                "scope_type": "TENANT",
                "landing_page": "/admin/dashboard"
            }
        }
    }


class RoleUpdate(BaseModel):
    """역할 수정 요청 (모든 필드 Optional)"""
    role_name: Optional[str] = Field(None, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: Optional[str] = Field(None, description="데이터 범위")
    landing_page: Optional[str] = Field(None, max_length=200, description="랜딩 페이지")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ["GLOBAL", "TENANT", "USER"]
            v = v.upper()
            if v not in valid:
                raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class RoleResponse(BaseModel):
    """역할 상세 응답"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위")
    landing_page: str = Field(..., description="랜딩 페이지")
    is_system: bool = Field(..., description="시스템 기본 역할 여부")
    sort_order: int = Field(0, description="정렬 순서")
    user_count: int = Field(default=0, description="소속 사용자 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_id": 1,
                "role_code": "SYSTEM_ADMIN",
                "role_name": "시스템 관리자",
                "scope_type": "GLOBAL",
                "landing_page": "/admin/dashboard",
                "is_system": True,
                "user_count": 1,
                "sort_order": 1
            }
        }
    }


class RoleListResponse(BaseModel):
    """역할 목록 응답"""
    total: int = Field(..., description="전체 역할 수")
    items: List[RoleResponse] = Field(default_factory=list, description="역할 목록")


# ===================================
# 사용자 (User)
# ===================================

class UserBase(BaseModel):
    """사용자 기본 필드"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    email: str = Field(..., max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v.lower().strip()


class UserCreate(UserBase):
    """사용자 생성 요청 (역할 + 메뉴 권한 포함)"""
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")
    role_id: int = Field(..., description="역할 ID (사용자는 하나의 역할에 소속)")
    is_active: bool = Field(default=True, description="활성화 여부")
    menus: List[UserMenuPermission] = Field(default_factory=list, description="메뉴 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "user02",
                "email": "user02@company.com",
                "display_name": "김철수",
                "password": "Password1!",
                "tenant_id": 2,
                "role_id": 3,
                "is_active": True,
                "menus": [
                    {"menu_id": 14, "can_create": True, "can_read": True}
                ]
            }
        }
    }


class UserUpdate(BaseModel):
    """사용자 수정 요청 (모든 필드 Optional)"""
    email: Optional[str] = Field(None, max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    role_id: Optional[int] = Field(None, description="역할 ID")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("올바른 이메일 형식이 아닙니다")
            return v.lower().strip()
        return v


class UserResponse(BaseModel):
    """사용자 상세 응답"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    email: str = Field(..., description="이메일")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    tenant_name: Optional[str] = Field(None, description="소속 테넌트명")
    role: RoleSimple = Field(..., description="역할 정보")
    is_active: bool = Field(..., description="활성화 여부")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    menu_count: int = Field(default=0, description="접근 가능 메뉴 수")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 일시")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "login_id": "admin",
                "email": "admin@system.local",
                "display_name": "시스템 관리자",
                "tenant_id": None,
                "tenant_name": None,
                "role": {
                    "role_id": 1,
                    "role_code": "SYSTEM_ADMIN",
                    "role_name": "시스템 관리자",
                    "scope_type": "GLOBAL",
                    "landing_page": "/admin/dashboard"
                },
                "is_active": True,
                "is_superuser": True,
                "menu_count": 14,
                "last_login_at": "2026-02-12T10:00:00+09:00"
            }
        }
    }


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    total: int = Field(..., description="전체 사용자 수")
    items: List[UserResponse] = Field(default_factory=list, description="사용자 목록")
    limit: int = Field(..., description="요청된 limit")
    offset: int = Field(..., description="요청된 offset")
