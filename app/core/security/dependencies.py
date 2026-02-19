"""
FastAPI 인증 의존성 주입

위치: app/core/security/dependencies.py
HTTP 요청의 Bearer 토큰에서 UserContext를 추출하는 Depends 함수
"""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import APIException, ErrorCode
from app.core.security.jwt import verify_token
from app.models.auth import UserContext


# Bearer 토큰 추출기(HTTPBearer는 HTTP Authorization 헤더에서 Bearer 토큰을 추출하는 보안 스키마 클래스)
#
# FastAPI 내부적으로는 다음을 수행:
#
# Authorization 헤더 존재 여부 확인
# "Bearer <token>" 형식 검증
# token 부분만 분리
# HTTPAuthorizationCredentials 객체로 감싸 반환
_bearer_scheme = HTTPBearer(auto_error=True)            # 인증값 없으면 Exception 발생
_bearer_scheme_optional = HTTPBearer(auto_error=False)  # 인증값 없어도 None 반환

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserContext:
    """Bearer 토큰에서 현재 사용자 추출 (필수 인증)"""
    payload = verify_token(credentials.credentials)

    if payload.token_type != "access":
        raise APIException(ErrorCode.UNAUTHORIZED, "Access Token이 필요합니다")

    return UserContext(
        user_id=int(payload.sub),
        login_id=payload.login_id,
        display_name=payload.display_name,
        tenant_id=payload.tenant_id,
        is_superuser=payload.is_superuser,
        role_code=payload.role_code,
    )


async def get_current_active_user(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    """활성 사용자 검증"""
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme_optional),
) -> Optional[UserContext]:
    """선택적 인증 (토큰 없으면 None, 유효하지 않아도 None)"""
    if credentials is None:
        return None
    try:
        payload = verify_token(credentials.credentials)
        if payload.token_type != "access":
            return None
        return UserContext(
            user_id=int(payload.sub),
            login_id=payload.login_id,
            display_name=payload.display_name,
            tenant_id=payload.tenant_id,
            is_superuser=payload.is_superuser,
            role_code=payload.role_code,
        )
    except Exception:
        return None
