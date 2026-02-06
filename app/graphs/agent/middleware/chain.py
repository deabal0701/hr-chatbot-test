"""
Middleware Chain

미들웨어 체인을 관리하고 순차적으로 실행합니다.
"""

from typing import Any, Dict, List

from app.graphs.agent.middleware.base import Middleware
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class MiddlewareChain:
    """
    미들웨어 체인 관리자

    여러 미들웨어를 등록하고 순차적으로 실행합니다.
    - process_input: 등록 순서대로 실행
    - process_output: 등록 역순으로 실행

    사용법:
        chain = MiddlewareChain()
        chain.add(PIIMiddleware())
        chain.add(AuditMiddleware())

        # 입력 처리
        processed_input = await chain.process_input(request_data)

        # 출력 처리
        processed_output = await chain.process_output(response_data)
    """

    def __init__(self):
        self.middlewares: List[Middleware] = []

    def add(self, middleware: Middleware) -> "MiddlewareChain":
        """
        미들웨어 추가

        Args:
            middleware: 추가할 미들웨어

        Returns:
            self (체이닝 지원)
        """
        self.middlewares.append(middleware)
        return self

    def remove(self, middleware: Middleware) -> "MiddlewareChain":
        """
        미들웨어 제거

        Args:
            middleware: 제거할 미들웨어

        Returns:
            self (체이닝 지원)
        """
        if middleware in self.middlewares:
            self.middlewares.remove(middleware)
        return self

    def clear(self) -> "MiddlewareChain":
        """
        모든 미들웨어 제거

        Returns:
            self (체이닝 지원)
        """
        self.middlewares.clear()
        return self

    async def process_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        입력 처리 (등록 순서대로)

        Args:
            data: 요청 데이터

        Returns:
            모든 미들웨어를 거친 요청 데이터
        """
        request_id = data.get("request_id", "unknown")

        for mw in self.middlewares:
            mw_name = type(mw).__name__
            try:
                data = await mw.process_input(data)
                log_step(logger, request_id, "MIDDLEWARE", mw_name, "INPUT", "입력 처리 완료", level="DEBUG")
            except Exception as e:
                log_step(logger, request_id, "MIDDLEWARE", mw_name, "INPUT", f"입력 처리 실패: {e}", level="ERROR")
                # 미들웨어 실패 시 데이터 그대로 전달 (fail-safe)

        return data

    async def process_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        출력 처리 (등록 역순으로)

        Args:
            data: 응답 데이터

        Returns:
            모든 미들웨어를 거친 응답 데이터
        """
        request_id = data.get("request_id", "unknown")

        # 역순으로 처리
        for mw in reversed(self.middlewares):
            mw_name = type(mw).__name__
            try:
                data = await mw.process_output(data)
                log_step(logger, request_id, "MIDDLEWARE", mw_name, "OUTPUT", "출력 처리 완료", level="DEBUG")
            except Exception as e:
                log_step(logger, request_id, "MIDDLEWARE", mw_name, "OUTPUT", f"출력 처리 실패: {e}", level="ERROR")
                # 미들웨어 실패 시 데이터 그대로 전달 (fail-safe)

        return data

    def __len__(self) -> int:
        """등록된 미들웨어 개수"""
        return len(self.middlewares)

    def __iter__(self):
        """미들웨어 순회"""
        return iter(self.middlewares)
