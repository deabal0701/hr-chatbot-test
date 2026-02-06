"""
HTTP Middleware 패키지

FastAPI/Starlette용 HTTP Middleware 모음.
Java Filter와 유사한 패턴으로 요청 전처리/응답 후처리를 담당합니다.

Usage:
    from app.middleware import LoggingMiddleware, register_middlewares

    # 개별 등록
    app.add_middleware(LoggingMiddleware)

    # 일괄 등록
    register_middlewares(app)
"""

from app.middleware.base import BaseMiddleware
from app.middleware.logging import LoggingMiddleware

__all__ = [
    "BaseMiddleware",
    "LoggingMiddleware",
    "register_middlewares",
]


def register_middlewares(app, *, enable_logging: bool = True):
    """
    모든 Middleware를 앱에 등록하는 헬퍼 함수

    Middleware는 역순으로 실행됩니다 (나중에 추가한 것이 먼저 실행).
    따라서 LoggingMiddleware를 마지막에 추가하여 가장 바깥에서 실행되도록 합니다.

    Args:
        app: FastAPI application instance
        enable_logging: LoggingMiddleware 활성화 여부 (기본: True)

    Example:
        from fastapi import FastAPI
        from app.middleware import register_middlewares

        app = FastAPI()
        register_middlewares(app)
    """
    # 역순 실행이므로 가장 바깥에서 실행할 것을 마지막에 추가
    # 추후 AuthMiddleware 등 추가 시 여기에 등록

    if enable_logging:
        app.add_middleware(LoggingMiddleware)
