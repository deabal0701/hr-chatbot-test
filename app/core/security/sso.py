"""
SSO 토큰 검증 모듈 (RS256)

위치: app/core/security/sso.py
용도: 메인 시스템에서 서명한 SSO JWT 토큰을 RS256 공개키로 검증
"""
import time
from typing import Optional

import jwt

from app.config import settings
from app.core.errors.error_codes import ErrorCode
from app.core.errors.handlers import APIException
from app.models.auth import SSOTokenPayload
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 모듈 레벨 공개키 캐시
_sso_public_key: Optional[str] = None


def load_sso_public_key() -> None:
    """SSO RS256 공개키를 파일에서 로드하여 모듈 캐시에 저장"""
    global _sso_public_key

    if not settings.sso_enabled:
        logger.info("SSO 비활성화 상태 — 공개키 로드 건너뜀")
        return

    key_path = settings.sso_public_key_path
    try:
        with open(key_path, "r") as f:
            _sso_public_key = f.read()
        logger.info(f"SSO 공개키 로드 완료: {key_path}")
    except FileNotFoundError:
        logger.warning(f"SSO 공개키 파일 없음: {key_path} — SSO 로그인 불가")
        _sso_public_key = None
    except Exception as e:
        logger.error(f"SSO 공개키 로드 실패: {e}")
        _sso_public_key = None


def verify_sso_token(token: str) -> SSOTokenPayload:
    """
    SSO JWT 토큰 검증 및 페이로드 반환

    검증 항목:
    1. RS256 서명 검증 (공개키)
    2. 발급자 (iss) 허용 목록 검증
    3. 토큰 최대 유효 시간 검증 (iat + sso_token_max_age)
    """
    if _sso_public_key is None:
        raise APIException(ErrorCode.SSO_NOT_CONFIGURED, "SSO가 설정되지 않았습니다. 공개키를 확인해주세요.")

    logger.debug(f"[SSO] 토큰 검증 시작 | algorithm={settings.sso_algorithm}, token_length={len(token)}")

    # 1. JWT 디코딩 + 서명 검증
    try:
        payload = jwt.decode(
            token,
            _sso_public_key,
            algorithms=[settings.sso_algorithm],
            options={"require": ["sub", "name", "iss", "iat"], "verify_exp": False},
        )
        logger.debug(f"[SSO] 서명 검증 통과 | sub={payload.get('sub')}, iss={payload.get('iss')}, iat={payload.get('iat')}")
    except jwt.InvalidSignatureError:
        logger.debug("[SSO] 서명 검증 실패 — 공개키와 토큰 서명 불일치")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "SSO 토큰 서명이 유효하지 않습니다")
    except jwt.DecodeError as e:
        logger.debug(f"[SSO] 토큰 디코딩 실패 | error={e}")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "SSO 토큰 형식이 올바르지 않습니다")
    except jwt.MissingRequiredClaimError as e:
        logger.debug(f"[SSO] 필수 클레임 누락 | error={e}")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, f"SSO 토큰에 필수 클레임이 없습니다: {e}")
    except Exception as e:
        logger.debug(f"[SSO] 토큰 검증 예외 | type={type(e).__name__}, error={e}")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, f"SSO 토큰 검증 실패: {e}")

    # 2. 발급자 검증
    allowed_issuers = [iss.strip() for iss in settings.sso_allowed_issuers.split(",")]
    token_iss = payload.get("iss")
    if token_iss not in allowed_issuers:
        logger.debug(f"[SSO] 발급자 불일치 | token_iss={token_iss}, allowed={allowed_issuers}")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, f"허용되지 않은 SSO 발급자: {token_iss}")

    # 3. 토큰 시간 검증 (iat 기반)
    iat = payload["iat"]
    age = time.time() - iat
    if age < -30:
        logger.debug(f"[SSO] 미래 시점 토큰 | iat={iat}, age={age:.1f}s")
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "SSO 토큰 발급 시간이 미래입니다")
    if age > settings.sso_token_max_age:
        logger.debug(f"[SSO] 토큰 만료 | iat={iat}, age={age:.1f}s, max_age={settings.sso_token_max_age}s")
        raise APIException(ErrorCode.SSO_TOKEN_EXPIRED, "SSO 토큰이 최대 유효 시간을 초과했습니다")

    # 4. 페이로드 파싱
    return SSOTokenPayload(
        sub=payload["sub"],
        name=payload["name"],
        email=payload.get("email"),
        tenant_code=payload.get("tenant_code"),
        dept_code=payload.get("dept_code"),
        dept_name=payload.get("dept_name"),
        position=payload.get("position"),
        iss=payload["iss"],
        iat=payload["iat"],
    )
