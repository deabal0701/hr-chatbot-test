"""
JWT 토큰 생성 및 검증 유틸리티

위치: app/core/security/jwt.py
python-jose를 사용한 Access/Refresh Token 관리
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings
from app.core.errors import APIException, ErrorCode


# ===================================
# JWT 페이로드 모델 (내부 전용)
# ===================================

class TokenPayload(BaseModel):
    """JWT 토큰 디코딩 결과"""
    sub: str = Field(..., description="Subject (user_id 문자열)")
    login_id: str = Field(default="", description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="테넌트 ID")
    scope_type: str = Field(default="USER", description="데이터 범위")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")
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
