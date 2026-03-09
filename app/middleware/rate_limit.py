"""
RateLimitMiddleware - IP/User 기반 요청 속도 제한 Middleware

위치: app/middleware/rate_limit.py
- 인메모리 슬라이딩 윈도우 방식
- 미인증 → IP 기반, 인증됨 → User ID 기반
- 엔드포인트 그룹별 차등 제한
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.core.errors.error_codes import ErrorCode
from app.middleware.base import BaseMiddleware
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """
    요청 속도 제한 Middleware

    기능:
        - 슬라이딩 윈도우 기반 분당 요청 수 제한
        - 미인증 요청: client IP 기반
        - 인증된 요청: user_id 기반
        - 엔드포인트 그룹별 차등 제한 (로그인, AI, 관리자, 기본)
        - Retry-After 헤더로 대기 시간 안내
        - 만료된 기록 자동 정리

    실행 순서:
        CORS → Logging → Auth → RateLimit → History → Handler
        (Auth 이후 실행되므로 request.state.current_user 사용 가능)
    """

    # Rate Limit 제외 경로 (health check, docs 등은 BaseMiddleware에서 이미 제외)
    EXCLUDE_PREFIXES = {"/docs", "/redoc", "/openapi.json"}

    # 윈도우 크기 (초)
    WINDOW_SECONDS = 60

    # 만료 기록 정리 주기 (초)
    CLEANUP_INTERVAL = 300  # 5분

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)

        # 슬라이딩 윈도우 저장소: {key: [timestamp1, timestamp2, ...]}
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    # ==========================================================================
    # 엔드포인트 그룹별 RPM 설정
    # ==========================================================================

    def _get_rate_limit(self, path: str) -> int:
        """경로별 분당 요청 제한 수 반환"""
        # 로그인/인증 관련 (가장 엄격)
        if path in ("/api/v1/auth/login", "/api/v1/auth/refresh"):
            return settings.rate_limit_login_rpm

        # AI 검색 (LLM 비용 보호)
        if path.startswith("/api/v1/agent/search") or path.startswith("/api/v1/search"):
            return settings.rate_limit_ai_rpm

        # 관리자 API
        if path.startswith("/api/admin/v1/"):
            return settings.rate_limit_admin_rpm

        # 기본
        return settings.rate_limit_default_rpm

    # ==========================================================================
    # 식별 키 생성
    # ==========================================================================

    def _get_client_key(self, request: Request, path: str) -> str:
        """요청자 식별 키 생성 (인증됨 → user:{id}, 미인증 → ip:{addr})"""
        current_user = getattr(request.state, "current_user", None)
        if current_user and hasattr(current_user, "user_id"):
            identity = f"user:{current_user.user_id}"
        else:
            ip = request.client.host if request.client else "unknown"
            identity = f"ip:{ip}"

        # 엔드포인트 그룹별로 분리 (로그인 제한이 AI 제한에 영향 주지 않도록)
        group = self._get_path_group(path)
        return f"{identity}:{group}"

    def _get_path_group(self, path: str) -> str:
        """경로를 그룹으로 분류"""
        if path in ("/api/v1/auth/login", "/api/v1/auth/refresh"):
            return "auth"
        if path.startswith("/api/v1/agent/search") or path.startswith("/api/v1/search"):
            return "ai"
        if path.startswith("/api/admin/v1/"):
            return "admin"
        return "default"

    # ==========================================================================
    # 슬라이딩 윈도우 체크
    # ==========================================================================

    def _check_rate_limit(self, key: str, rpm: int) -> Tuple[bool, int, int]:
        """
        요청 허용 여부 확인 (슬라이딩 윈도우)

        Returns:
            (allowed, remaining, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.WINDOW_SECONDS

        with self._lock:
            # 윈도우 밖의 오래된 기록 제거
            timestamps = self._requests[key]
            self._requests[key] = [t for t in timestamps if t > window_start]
            timestamps = self._requests[key]

            current_count = len(timestamps)

            if current_count >= rpm:
                # 제한 초과 → 가장 오래된 요청이 윈도우에서 빠지는 시간 계산
                oldest = timestamps[0] if timestamps else now
                retry_after = int(oldest - window_start) + 1
                return False, 0, max(retry_after, 1)

            # 허용 → 현재 타임스탬프 기록
            self._requests[key].append(now)
            remaining = rpm - current_count - 1
            return True, remaining, 0

    # ==========================================================================
    # 만료 기록 정리
    # ==========================================================================

    def _cleanup_expired(self) -> None:
        """만료된 슬라이딩 윈도우 기록 정리"""
        now = time.time()
        if now - self._last_cleanup < self.CLEANUP_INTERVAL:
            return

        window_start = now - self.WINDOW_SECONDS
        with self._lock:
            expired_keys = [
                key for key, timestamps in self._requests.items()
                if not timestamps or all(t <= window_start for t in timestamps)
            ]
            for key in expired_keys:
                del self._requests[key]

            self._last_cleanup = now

            if expired_keys:
                logger.debug(f"[RATE-LIMIT] 만료 키 정리: {len(expired_keys)}건 삭제, 활성: {len(self._requests)}건")

    # ==========================================================================
    # 미들웨어 메인 로직
    # ==========================================================================

    async def process_request(self, request: Request, call_next) -> Response:
        """Rate Limit 체크 후 요청 처리"""
        # Rate Limiting 비활성화 시 바로 통과
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        request_id = getattr(request.state, "request_id", "unknown")

        # RPM 설정 조회
        rpm = self._get_rate_limit(path)
        client_key = self._get_client_key(request, path)

        # 슬라이딩 윈도우 체크
        allowed, remaining, retry_after = self._check_rate_limit(client_key, rpm)

        if not allowed:
            logger.warning(f"[{request_id}] [RATE-LIMIT] 제한 초과 | key={client_key} | rpm={rpm} | retry_after={retry_after}s")

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "error": {
                        "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                        "message": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요",
                        "detail": f"분당 {rpm}회 제한 초과. {retry_after}초 후 재시도"
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                }
            )

        # 요청 처리
        response = await call_next(request)

        # Rate Limit 헤더 추가
        response.headers["X-RateLimit-Limit"] = str(rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        # 주기적으로 만료 기록 정리
        self._cleanup_expired()

        return response
