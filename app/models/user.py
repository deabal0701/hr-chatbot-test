"""
사용자/역할/권한 관리 스키마

위치: app/models/user.py
사용자 CRUD, 역할 관리, 권한 조회 관련 모델
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 사용자 (User)
# ===================================

class UserBase(BaseModel):
    """사용자 기본 필드 (Create/Update의 공통 부모)"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    email: str = Field(..., max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """이메일 형식 간단 검증"""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v.lower().strip()


class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")
    is_active: bool = Field(default=True, description="활성화 여부")
    role_ids: List[int] = Field(default_factory=list, description="부여할 역할 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "user01",
                "email": "user01@company.com",
                "display_name": "홍길동",
                "password": "Password1!",
                "tenant_id": 2,
                "is_active": True,
                "role_ids": [3]
            }
        }
    }


class UserUpdate(BaseModel):
    """사용자 수정 요청 (모든 필드 Optional — 부분 수정 지원)"""
    email: Optional[str] = Field(None, max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("올바른 이메일 형식이 아닙니다")
            return v.lower().strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "display_name": "홍길동 (수정)",
                "is_active": True
            }
        }
    }


class RoleSimple(BaseModel):
    """역할 간략 정보 (UserResponse에 포함용)"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    scope_type: str = Field(..., description="데이터 범위")


class UserResponse(BaseModel):
    """사용자 상세 응답"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    email: str = Field(..., description="이메일")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    tenant_name: Optional[str] = Field(None, description="소속 테넌트명")
    is_active: bool = Field(..., description="활성화 여부")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 일시")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    roles: List[RoleSimple] = Field(default_factory=list, description="보유 역할 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "login_id": "admin",
                "email": "admin@system.local",
                "display_name": "시스템 관리자",
                "tenant_id": None,
                "tenant_name": None,
                "is_active": True,
                "is_superuser": True,
                "last_login_at": "2026-02-12T10:00:00+09:00",
                "created_at": "2026-02-06T09:00:00+09:00",
                "updated_at": "2026-02-06T09:00:00+09:00",
                "roles": [
                    {"role_id": 1, "role_code": "SYSTEM_ADMIN", "role_name": "시스템 관리자", "scope_type": "GLOBAL"}
                ]
            }
        }
    }


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    total: int = Field(..., description="전체 사용자 수")
    items: List[UserResponse] = Field(default_factory=list, description="사용자 목록")
    limit: int = Field(..., description="요청된 limit")
    offset: int = Field(..., description="요청된 offset")


# ===================================
# 역할 (Role)
# ===================================

class RoleBase(BaseModel):
    """역할 기본 필드"""
    role_code: str = Field(..., min_length=1, max_length=50, description="역할 코드")
    role_name: str = Field(..., min_length=1, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        valid = ["GLOBAL", "TENANT", "USER"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class RoleCreate(RoleBase):
    """역할 생성 요청"""
    permission_ids: List[int] = Field(default_factory=list, description="부여할 권한 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_code": "DEPT_ADMIN",
                "role_name": "부서 관리자",
                "description": "부서 내 데이터만 접근",
                "scope_type": "TENANT",
                "permission_ids": [1, 3, 4]
            }
        }
    }


class RoleUpdate(BaseModel):
    """역할 수정 요청 (모든 필드 Optional)"""
    role_name: Optional[str] = Field(None, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: Optional[str] = Field(None, description="데이터 범위")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ["GLOBAL", "TENANT", "USER"]
            v = v.upper()
            if v not in valid:
                raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class PermissionSimple(BaseModel):
    """권한 간략 정보 (RoleResponse에 포함용)"""
    permission_id: int = Field(..., description="권한 ID")
    permission_code: str = Field(..., description="권한 코드")
    permission_name: str = Field(..., description="권한명")
    category: str = Field(..., description="카테고리")


class RoleResponse(BaseModel):
    """역할 상세 응답"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위")
    is_system: bool = Field(..., description="시스템 기본 역할 여부")
    sort_order: int = Field(0, description="정렬 순서")
    created_at: datetime = Field(..., description="생성일시")
    permissions: List[PermissionSimple] = Field(default_factory=list, description="보유 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_id": 1,
                "role_code": "SYSTEM_ADMIN",
                "role_name": "시스템 관리자",
                "description": "전체 시스템 관리 권한",
                "scope_type": "GLOBAL",
                "is_system": True,
                "sort_order": 1,
                "created_at": "2026-02-06T09:00:00+09:00",
                "permissions": [
                    {"permission_id": 1, "permission_code": "nl2sql:execute", "permission_name": "NL2SQL 실행", "category": "nl2sql"}
                ]
            }
        }
    }


class RoleListResponse(BaseModel):
    """역할 목록 응답"""
    total: int = Field(..., description="전체 역할 수")
    items: List[RoleResponse] = Field(default_factory=list, description="역할 목록")


# ===================================
# 권한 (Permission)
# ===================================

class PermissionResponse(BaseModel):
    """권한 응답"""
    permission_id: int = Field(..., description="권한 ID")
    permission_code: str = Field(..., description="권한 코드")
    permission_name: str = Field(..., description="권한명")
    category: str = Field(..., description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    is_system: bool = Field(default=False, description="시스템 기본 권한 여부")


# ===================================
# 역할 할당
# ===================================

class UserRoleAssign(BaseModel):
    """사용자에게 역할 할당 요청"""
    role_ids: List[int] = Field(..., min_length=1, description="할당할 역할 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_ids": [2, 3]
            }
        }
    }


class RolePermissionAssign(BaseModel):
    """역할에 권한 할당 요청"""
    permission_ids: List[int] = Field(..., min_length=1, description="할당할 권한 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "permission_ids": [1, 3, 4, 5]
            }
        }
    }


# ===================================
# 데이터 필터
# ===================================

class DataFilterResponse(BaseModel):
    """데이터 필터 응답"""
    filter_id: int = Field(..., description="필터 ID")
    role_id: int = Field(..., description="역할 ID")
    target_table: str = Field(..., description="대상 테이블")
    filter_column: str = Field(..., description="필터 컬럼")
    filter_type: str = Field(..., description="필터 유형 (TENANT, USER, CUSTOM)")
    filter_sql: Optional[str] = Field(None, description="커스텀 SQL 조건")
    is_active: bool = Field(default=True, description="활성화 여부")
