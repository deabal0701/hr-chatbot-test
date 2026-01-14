"""LLM 설정 통합 관리 (Phase 2: 다중 제공자 지원)

위치: app/core/llm/llm_config.py
- LLM 설정 로딩 (DB → 환경변수 → 기본값)
- 다중 제공자 지원 (OpenAI, Anthropic)
- init_chat_model 기반 통합 인터페이스
"""
from typing import Dict, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_service = None


def _get_settings_service():
    global _settings_service
    if _settings_service is None:
        from app.core.config.settings_service import settings_service
        _settings_service = settings_service
    return _settings_service


class LLMConfigManager:
    """LLM 설정 통합 관리 클래스 (Phase 2: 다중 제공자 지원)"""

    # 제공자별 기본 모델 매핑 (더 이상 사용되지 않음, DB 설정 우선)
    # 이 값들은 DB/env에 아무 설정도 없을 때만 최후의 fallback으로 사용됨
    DEFAULT_MODELS = {
        "openai": "gpt-4o-mini",  # 비용 효율적인 기본값
        "anthropic": "claude-3-5-sonnet-20241022",
    }

    @staticmethod
    def _get_api_key(provider: str) -> str:
        """
        제공자별 API 키 가져오기

        Args:
            provider: 제공자명 ('openai' | 'anthropic')

        Returns:
            API 키

        Raises:
            ValueError: API 키가 설정되지 않은 경우
        """
        settings_service = _get_settings_service()

        if provider == "openai":
            api_key = settings_service.get_value("openai", "api_key", settings.openai_api_key)
        elif provider == "anthropic":
            # DB 설정 → 환경변수 순으로 fallback
            api_key = settings_service.get_value(
                "anthropic", "api_key",
                getattr(settings, "anthropic_api_key", None)
            )
            if not api_key:
                raise ValueError(
                    "Anthropic API 키가 설정되지 않았습니다. "
                    "Admin UI에서 'anthropic.api_key'를 설정하거나 "
                    ".env에 ANTHROPIC_API_KEY를 추가하세요."
                )
        else:
            raise ValueError(f"지원하지 않는 provider: {provider}")

        if not api_key:
            raise ValueError(f"{provider} API 키가 설정되지 않았습니다.")

        return api_key

    @staticmethod
    def get_llm_settings(temperature: Optional[float] = None) -> Dict[str, str]:
        """
        LLM 설정 가져오기 (DB → 환경변수 → 기본값 순서로 fallback)

        Args:
            temperature: 생성 온도 (None이면 DB 설정 사용)

        Returns:
            LLM 설정 딕셔너리
        """
        settings_service = _get_settings_service()

        config = {
            "api_key": settings_service.get_value("openai", "api_key", settings.openai_api_key),
            "model": settings_service.get_value("llm", "model", settings.llm_model),
        }

        if temperature is not None:
            config["temperature"] = temperature
        else:
            config["temperature"] = settings_service.get_value("llm", "temperature", 0.1)

        return config

    @staticmethod
    def create_llm(
        temperature: float = 0.0,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        LLM 인스턴스 생성 (init_chat_model 사용)

        Phase 2: OpenAI + Anthropic 지원

        Args:
            temperature: 생성 온도 (기본 0.0)
            model: 모델명 (None이면 DB 설정 또는 provider 기본 모델 사용)
            provider: 제공자명 (None이면 DB 설정 사용, 'openai' | 'anthropic')
            max_tokens: 최대 토큰 수 (None이면 기본값 사용)
            **kwargs: 제공자별 추가 파라미터

        Returns:
            BaseChatModel 인스턴스 (제공자 독립적)
        """
        settings_service = _get_settings_service()

        # 1. Provider 결정 (파라미터 → DB → 환경변수 → 기본값)
        if provider is None:
            provider = settings_service.get_value("llm", "provider", settings.llm_provider)

        # Provider 검증 (Phase 2: openai, anthropic만 허용)
        if provider not in ["openai", "anthropic"]:
            logger.warning(f"지원하지 않는 provider='{provider}'. 'openai'로 fallback")
            provider = "openai"

        # 2. 모델 결정
        if model is None:
            # DB 설정 → .env → Provider별 기본 모델 순서로 fallback
            model = settings_service.get_value(
                "llm",
                "model",
                settings.llm_model  # .env의 llm_model 값 사용 (기본: gpt-4-turbo-preview)
            )
            logger.debug(f"모델 미지정, DB/설정 기본 모델 사용: {model}")

        # 3. 최대 토큰 수
        if max_tokens is None:
            max_tokens = settings_service.get_value("llm", "max_tokens", 2000)

        # 4. API 키 가져오기 (제공자별)
        api_key = LLMConfigManager._get_api_key(provider)

        # 5. init_chat_model 호출 (제공자 독립적 인터페이스)
        try:
            llm = init_chat_model(
                model=model,
                model_provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key,
                **kwargs
            )

            logger.info(f"LLM 초기화 성공: provider={provider}, model={model}, temperature={temperature}")
            return llm

        except Exception as e:
            logger.error(f"LLM 초기화 실패 ({provider}/{model}): {e}", exc_info=True)

            # Fallback: OpenAI로 전환 (안전망)
            if provider != "openai":
                logger.warning(f"{provider} 실패, OpenAI로 fallback 시도")
                try:
                    fallback_api_key = settings_service.get_value("openai", "api_key", settings.openai_api_key)
                    # Fallback 모델도 DB 설정 사용
                    fallback_model = settings_service.get_value("llm", "model", settings.llm_model)
                    return ChatOpenAI(
                        model=fallback_model,
                        temperature=temperature,
                        api_key=fallback_api_key,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback도 실패: {fallback_error}")
                    raise

            # OpenAI도 실패한 경우 예외 전파
            raise

    @staticmethod
    def get_embedding_settings() -> Dict[str, str]:
        """
        임베딩 설정 가져오기

        Returns:
            임베딩 설정 딕셔너리
        """
        settings_service = _get_settings_service()

        return {
            "api_key": settings_service.get_value("openai", "api_key", settings.openai_api_key),
            "model": settings_service.get_value("embedding", "model", settings.embedding_model),
            "dimension": settings_service.get_value("embedding", "dimension", settings.embedding_dimension),
        }

    @staticmethod
    def get_rag_settings() -> Dict:
        """
        RAG 관련 설정 가져오기

        Returns:
            RAG 설정 딕셔너리
        """
        settings_service = _get_settings_service()

        return {
            "top_k": settings_service.get_value("rag", "top_k", 10),
            "similarity_threshold": settings_service.get_value("rag", "similarity_threshold", 0.7),
            "max_context_length": settings_service.get_value("rag", "max_context_length", 4000),
        }

    @staticmethod
    def get_nl2sql_settings() -> Dict:
        """
        NL2SQL 관련 설정 가져오기

        Returns:
            NL2SQL 설정 딕셔너리
        """
        settings_service = _get_settings_service()

        return {
            "timeout_seconds": settings_service.get_value("nl2sql", "timeout_seconds", 30),
            "max_rows": settings_service.get_value("nl2sql", "max_rows", 1000),
            "read_only_mode": settings_service.get_value("nl2sql", "read_only_mode", True),
        }
