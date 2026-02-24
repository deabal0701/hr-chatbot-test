"""
JWT 토큰 생성 및 검증 유틸리티 (v2.0 - 메뉴 기반)

위치: app/core/security/jwt.py
python-jose를 사용한 Access/Refresh Token 관리
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings
from app.core.errors.handlers import APIException
from app.core.errors.error_codes import ErrorCode


# ===================================
# JWT 페이로드 모델 (내부 전용)
# ===================================

class TokenPayload(BaseModel):
    """JWT 토큰 디코딩 결과 (v4.0 - scope_level 기반)"""
    sub: str = Field(..., description="Subject (user_id 문자열)")
    login_id: str = Field(default="", description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="테넌트 ID")
    dept_id: Optional[int] = Field(None, description="부서 ID")
    role_code: str = Field(default="USER", description="역할 코드 (GLOBAL, TENANT, DEPT, USER)")
    scope_level: int = Field(default=3, description="데이터 범위 (0=전체, 1=테넌트, 2=부서, 3=본인)")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    exp: Optional[int] = Field(None, description="만료 시간 (Unix timestamp)")
    iat: Optional[int] = Field(None, description="발급 시간 (Unix timestamp)")
    token_type: str = Field(default="access", description="토큰 타입 (access, refresh)")
    session_id: Optional[str] = Field(None, description="세션 ID (refresh token only)")


# ===================================
# 토큰 생성
# ===================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Access Token 생성"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": now, "token_type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Refresh Token 생성 (minimal payload: sub + session_id)"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))
    to_encode.update({"exp": expire, "iat": now, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


# ===================================
# 토큰 검증
# ===================================

def verify_token(token: str) -> TokenPayload:
    """JWT 토큰 검증 및 페이로드 반환"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str = payload.get("sub")
        if sub is None:
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
        return TokenPayload(**payload)
    except JWTError:
        raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
