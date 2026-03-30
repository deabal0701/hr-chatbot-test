"""
인증(Authentication) 스키마 (v2.0 - 메뉴 기반)

위치: app/models/auth.py
로그인, 토큰, 사용자 컨텍스트 관련 모델
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 메뉴 권한 (로그인 응답용)
# ===================================

class MenuPermission(BaseModel):
    """사용자가 접근 가능한 메뉴 + CRUD 권한 (로그인 응답에 포함)"""
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    menu_type: str = Field(..., description="메뉴 타입 (DIRECTORY, PAGE, API)")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    parent_menu_code: Optional[str] = Field(None, description="상위 메뉴 코드")
    depth: int = Field(default=0, description="트리 깊이")
    sort_order: int = Field(default=0, description="정렬 순서")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")


# ===================================
# 로그인 요청/응답
# ===================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
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
    """로그인 응답에 포함되는 사용자 정보"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    role_code: str = Field(..., description="역할 코드 (GLOBAL, TENANT, USER)")
    role_name: str = Field(default="", description="역할 표시명 (시스템 관리자, 테넌트 관리자 등)")
    landing_page: str = Field(..., description="로그인 후 랜딩 페이지")
    menus: List[MenuPermission] = Field(default_factory=list, description="접근 가능 메뉴 + CRUD 권한")


class TokenResponse(BaseModel):
    """로그인 성공 응답 (JWT 토큰 + 사용자 정보 + 메뉴 목록)"""
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")
    user: UserInfo = Field(..., description="사용자 정보 + 메뉴 권한")

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
                    "role_code": "GLOBAL",
                    "role_name": "시스템 관리자",
                    "landing_page": "/admin/dashboard",
                    "menus": [
                        {
                            "menu_code": "DASHBOARD",
                            "menu_name": "대시보드",
                            "menu_path": "/admin/dashboard",
                            "menu_type": "PAGE",
                            "icon": "dashboard",
                            "depth": 1,
                            "sort_order": 1,
                            "can_create": False,
                            "can_read": True,
                            "can_update": False,
                            "can_delete": False,
                            "can_export": False
                        }
                    ]
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
    인증된 사용자 컨텍스트 (v4.0 - scope_level 기반)

    인증 미들웨어가 JWT를 검증한 후 생성하여 request.state.current_user에 저장.
    모든 API 핸들러에서 현재 사용자 정보를 참조할 때 사용.

    v4.0 변경: scope_level로 데이터 범위 결정 (0=전체, 1=테넌트, 2=부서, 3=본인).
    role_code는 식별/표시 용도로 유지. 메뉴 권한 체크는 require_menu_permission()에서 DB 조회.
    """
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    dept_id: Optional[int] = Field(None, description="소속 부서 ID")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    role_code: str = Field(default="USER", description="역할 코드 (GLOBAL, TENANT, DEPT, USER)")
    scope_level: int = Field(default=3, description="데이터 범위 (0=전체, 1=테넌트, 2=부서, 3=본인)")

    @property
    def is_sso_user(self) -> bool:
        """SSO 사용자 여부"""
        return hasattr(self, '_sso_provider') and self._sso_provider is not None

    @property
    def is_global(self) -> bool:
        """전체 데이터 접근 여부"""
        return self.is_superuser or self.scope_level == 0

    @property
    def is_tenant_scope(self) -> bool:
        """테넌트 범위 여부"""
        return self.scope_level == 1

    @property
    def is_dept_scope(self) -> bool:
        """부서 범위 여부"""
        return self.scope_level == 2

    @property
    def is_user_scope(self) -> bool:
        """본인 범위 여부"""
        return self.scope_level == 3


# ===================================
# SSO 인증
# ===================================

class SSOLoginRequest(BaseModel):
    """SSO 로그인 요청 (프론트엔드 → 백엔드)"""
    sso_token: str = Field(..., min_length=1, description="SSO JWT 토큰 (RS256 서명)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "sso_token": "eyJhbGciOiJSUzI1NiIs..."
            }
        }
    }


class SSOTokenPayload(BaseModel):
    """SSO JWT 토큰 페이로드 (메인 시스템이 서명)"""
    sub: str = Field(..., description="사번 (win-AI login_id로 매핑)")
    name: str = Field(..., description="사용자 이름")
    email: Optional[str] = Field(None, description="이메일")
    tenant_code: Optional[str] = Field(None, description="테넌트 코드")
    dept_code: Optional[str] = Field(None, description="부서 코드")
    dept_name: Optional[str] = Field(None, description="부서명")
    position: Optional[str] = Field(None, description="직위/직급")
    iss: str = Field(..., description="토큰 발급자")
    iat: int = Field(..., description="발급 시간 (Unix timestamp)")
