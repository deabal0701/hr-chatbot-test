"""
BaseMiddleware - 모든 HTTP Middleware의 기반 클래스

Java의 Filter 인터페이스와 유사한 역할을 합니다.
공통 설정(제외 경로, 설정 로딩 등)을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Set, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BaseMiddleware(BaseHTTPMiddleware, ABC):
    """
    모든 HTTP Middleware의 기반 추상 클래스

    Java Filter 패턴:
        - doFilter(request, response, chain) → dispatch(request, call_next)
        - chain.doFilter() → await call_next(request)

    Attributes:
        EXCLUDE_PATHS: 처리를 건너뛸 경로들
        EXCLUDE_PREFIXES: 처리를 건너뛸 경로 접두사들
    """

    # 기본 제외 경로 (서브클래스에서 오버라이드 가능)
    EXCLUDE_PATHS: Set[str] = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    # 기본 제외 접두사 (서브클래스에서 오버라이드 가능)
    EXCLUDE_PREFIXES: Set[str] = set()

    def __init__(self, app, exclude_paths: Optional[Set[str]] = None, exclude_prefixes: Optional[Set[str]] = None):
        """
        Args:
            app: ASGI application
            exclude_paths: 추가 제외 경로 (기본 제외 경로에 합쳐짐)
            exclude_prefixes: 추가 제외 접두사 (기본 제외 접두사에 합쳐짐)
        """
        super().__init__(app)

        # 기본값과 사용자 지정값 병합
        self._exclude_paths = self.EXCLUDE_PATHS.copy()
        if exclude_paths:
            self._exclude_paths.update(exclude_paths)

        self._exclude_prefixes = self.EXCLUDE_PREFIXES.copy()
        if exclude_prefixes:
            self._exclude_prefixes.update(exclude_prefixes)

    def should_skip(self, request: Request) -> bool:
        """
        해당 요청을 처리하지 않고 건너뛸지 결정

        Args:
            request: HTTP 요청 객체

        Returns:
            True면 middleware 처리를 건너뜀
        """
        path = request.url.path

        # 정확한 경로 매칭
        if path in self._exclude_paths:
            return True

        # 접두사 매칭
        for prefix in self._exclude_prefixes:
            if path.startswith(prefix):
                return True

        return False

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Middleware 메인 로직 (Java Filter의 doFilter에 해당)

        서브클래스에서 이 메서드를 오버라이드하여 구현합니다.
        기본 구현은 should_skip 체크 후 process_request를 호출합니다.

        Args:
            request: HTTP 요청 객체
            call_next: 다음 middleware/handler를 호출하는 함수

        Returns:
            HTTP 응답 객체
        """
        # 제외 경로면 바로 다음으로 전달
        if self.should_skip(request):
            return await call_next(request)

        # 실제 처리 로직 (서브클래스에서 구현)
        return await self.process_request(request, call_next)

    @abstractmethod
    async def process_request(self, request: Request, call_next) -> Response:
        """
        실제 Middleware 처리 로직 (서브클래스에서 구현 필수)

        Args:
            request: HTTP 요청 객체
            call_next: 다음 middleware/handler를 호출하는 함수

        Returns:
            HTTP 응답 객체
        """
        pass
