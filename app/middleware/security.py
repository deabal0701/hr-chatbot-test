"""
SecurityHeadersMiddleware - HTTP 응답 보안 헤더 Middleware

모든 응답에 보안 헤더를 추가합니다.
- X-Content-Type-Options: MIME 스니핑 방지
- X-Frame-Options: 클릭재킹 방지
- Referrer-Policy: Referer 헤더 누출 방지
- Permissions-Policy: 불필요한 브라우저 API 차단
- Strict-Transport-Security: HTTPS 강제 (production만)
"""

from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.middleware.base import BaseMiddleware


class SecurityHeadersMiddleware(BaseMiddleware):
    """
    HTTP 응답 보안 헤더 Middleware

    모든 응답(API, 정적 리소스 포함)에 보안 헤더를 추가합니다.
    제외 경로 없이 전체 적용합니다.
    """

    # 보안 헤더는 모든 경로에 적용 (제외 없음)
    EXCLUDE_PATHS = set()
    EXCLUDE_PREFIXES = set()

    async def process_request(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 공통 보안 헤더 (모든 환경)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["X-XSS-Protection"] = "0"

        # Production 전용 헤더
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
