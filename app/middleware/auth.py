"""인증 미들웨어

위치: app/middleware/auth.py
HTTP 요청의 Bearer 토큰을 검증하고 request.state.current_user에 UserContext를 저장합니다.
Phase 3a: 선택적 모드 — 토큰 없어도 차단하지 않음 (기존 API 하위호환)
"""
from typing import Set

from starlette.requests import Request
from starlette.responses import Response

from app.core.security.jwt import verify_token
from app.middleware.base import BaseMiddleware
from app.models.auth import UserContext
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """인증 미들웨어 (선택적 모드 — Phase 3a)"""

    EXCLUDE_PATHS: Set[str] = {
        "/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico",
        "/api/v1/auth/login", "/api/v1/auth/refresh",
    }

    EXCLUDE_PREFIXES: Set[str] = {"/static/"}

    async def process_request(self, request: Request, call_next) -> Response:
        """Bearer 토큰 추출 → UserContext 생성 → request.state에 저장"""
        request.state.current_user = None

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = verify_token(token)
                if payload.token_type == "access":
                    request.state.current_user = UserContext(
                        user_id=int(payload.sub),
                        login_id=payload.login_id,
                        display_name=payload.display_name,
                        tenant_id=payload.tenant_id,
                        is_superuser=payload.is_superuser,
                        scope_type=payload.scope_type,
                        role_code=payload.role_code,
                    )
            except Exception:
                pass

        return await call_next(request)
