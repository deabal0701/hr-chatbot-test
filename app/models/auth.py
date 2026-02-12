"""
인증(Authentication) 스키마

위치: app/models/auth.py
로그인, 토큰, 사용자 컨텍스트 관련 모델
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 로그인 요청/응답
# ===================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    login_id: str = Field(..., min_length=5, max_length=100, description="로그인 ID")
    password: str = Field(..., min_length=1, description="비밀번호")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "admin",
                "password": "admin123!"
            }
        }
    }


class UserInfo(BaseModel):
    """로그인 응답에 포함되는 사용자 정보 (JWT payload의 일부)"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    role_names: List[str] = Field(default_factory=list, description="역할 이름 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")


class TokenResponse(BaseModel):
    """로그인 성공 응답 (JWT 토큰 + 사용자 정보)"""
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")
    user: UserInfo = Field(..., description="사용자 정보")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 1800,
                "user": {
                    "user_id": 1,
                    "login_id": "admin",
                    "display_name": "시스템 관리자",
                    "tenant_id": None,
                    "scope_type": "GLOBAL",
                    "roles": ["SYSTEM_ADMIN"],
                    "permissions": ["nl2sql:execute", "admin:settings"]
                }
            }
        }
    }


# ===================================
# 토큰 갱신
# ===================================

class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., min_length=1, description="Refresh Token")


# ===================================
# 비밀번호 변경
# ===================================

class PasswordChangeRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., min_length=1, description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호 (8자 이상)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """새 비밀번호 복잡도 검증"""
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "oldPassword1!",
                "new_password": "newPassword2!"
            }
        }
    }


# ===================================
# 사용자 컨텍스트 (인증 미들웨어 → API 핸들러)
# ===================================

class UserContext(BaseModel):
    """
    인증된 사용자 컨텍스트

    인증 미들웨어가 JWT를 검증한 후 생성하여 request.state.current_user에 저장.
    모든 API 핸들러에서 현재 사용자 정보를 참조할 때 사용.
    """
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    scope_type: str = Field(default="USER", description="데이터 범위 (GLOBAL, TENANT, USER)")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")

    def has_permission(self, permission_code: str) -> bool:
        """특정 권한 보유 여부 확인"""
        if self.is_superuser:
            return True
        return permission_code in self.permissions

    def has_any_permission(self, *permission_codes: str) -> bool:
        """주어진 권한 중 하나라도 보유하는지 확인 (OR 조건)"""
        if self.is_superuser:
            return True
        return any(p in self.permissions for p in permission_codes)

    def has_all_permissions(self, *permission_codes: str) -> bool:
        """주어진 권한을 모두 보유하는지 확인 (AND 조건)"""
        if self.is_superuser:
            return True
        return all(p in self.permissions for p in permission_codes)

    @property
    def is_global(self) -> bool:
        """GLOBAL scope 여부 (전체 데이터 접근)"""
        return self.is_superuser or self.scope_type == "GLOBAL"

    @property
    def is_tenant_scope(self) -> bool:
        """TENANT scope 여부"""
        return self.scope_type == "TENANT"

    @property
    def is_user_scope(self) -> bool:
        """USER scope 여부"""
        return self.scope_type == "USER"