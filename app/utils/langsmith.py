"""
LangSmith 통합 유틸리티

LangSmith는 LangChain 애플리케이션의 디버깅, 모니터링, 평가를 위한 플랫폼입니다.
이 모듈은 LangSmith 트레이싱을 설정하고 관리합니다.

사용법:
    1. .env 파일에 LangSmith 환경 변수 설정
    2. 애플리케이션 시작 시 자동으로 초기화됨

환경 변수:
    - LANGCHAIN_TRACING_V2: true로 설정하여 트레이싱 활성화
    - LANGCHAIN_API_KEY: LangSmith API 키
    - LANGCHAIN_PROJECT: 프로젝트 이름 (선택사항)
    - LANGCHAIN_ENDPOINT: API 엔드포인트 (기본: https://api.smith.langchain.com)
"""

import os

from app.config import settings
from app.utils.logger import logger


def setup_langsmith() -> bool:
    """
    LangSmith 트레이싱 설정

    환경 변수가 올바르게 설정되어 있으면 LangSmith 트레이싱을 활성화합니다.
    LangChain은 환경 변수를 자동으로 인식하므로 별도의 SDK 호출이 필요 없습니다.

    Returns:
        bool: LangSmith 활성화 여부
    """
    try:
        # LangSmith 설정 확인
        if not settings.langsmith_enabled:
            logger.info("LangSmith 트레이싱이 비활성화되어 있습니다.")
            return False

        # 환경 변수 설정 (LangChain이 자동으로 읽음)
        if settings.langchain_tracing_v2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"

        if settings.langchain_api_key:
            os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key

        if settings.langchain_endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        else:
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

        if settings.langchain_project:
            os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        else:
            os.environ["LANGCHAIN_PROJECT"] = "chatbot-mureum"

        logger.info(
            f"=> LangSmith 트레이싱이 활성화되었습니다. "
            f"프로젝트: {os.environ.get('LANGCHAIN_PROJECT')}"
        )
        logger.info(
            f"   LangSmith 대시보드: https://smith.langchain.com/o/default/projects/{os.environ.get('LANGCHAIN_PROJECT')}"
        )
        return True

    except Exception as e:
        logger.warning(f"LangSmith 설정 중 오류 발생 (계속 진행): {e}")
        return False


# 애플리케이션 시작 시 자동 초기화
_langsmith_initialized = False

def init_langsmith():
    """LangSmith 초기화 (한 번만 실행)"""
    global _langsmith_initialized

    if _langsmith_initialized:
        return

    setup_langsmith()
    _langsmith_initialized = True
