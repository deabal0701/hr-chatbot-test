"""
Middleware 기본 인터페이스

Agent 전용 미들웨어의 기본 클래스를 정의합니다.
추후 PII, Audit 등 구현 시 이 인터페이스를 따릅니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Middleware(ABC):
    """
    미들웨어 기본 인터페이스

    모든 미들웨어는 이 클래스를 상속하여 구현합니다.

    사용법:
        class MyMiddleware(Middleware):
            async def process_input(self, data: Dict) -> Dict:
                # 입력 전처리
                return data

            async def process_output(self, data: Dict) -> Dict:
                # 출력 후처리
                return data
    """

    @abstractmethod
    async def process_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        입력 전처리

        Agent 실행 전에 호출됩니다.
        요청 데이터를 변환하거나 검증할 수 있습니다.

        Args:
            data: 요청 데이터

        Returns:
            처리된 요청 데이터
        """
        pass

    @abstractmethod
    async def process_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        출력 후처리

        Agent 실행 후에 호출됩니다.
        응답 데이터를 변환하거나 로깅할 수 있습니다.

        Args:
            data: 응답 데이터

        Returns:
            처리된 응답 데이터
        """
        pass


class PassThroughMiddleware(Middleware):
    """
    아무것도 하지 않는 기본 미들웨어 (개발용)

    미들웨어 테스트나 비활성화 시 사용합니다.
    """

    async def process_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """입력을 그대로 반환"""
        return data

    async def process_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """출력을 그대로 반환"""
        return data
