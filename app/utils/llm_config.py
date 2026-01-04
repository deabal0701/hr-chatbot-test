"""LLM 설정 통합 관리
 
중복된 LLM 설정 로딩 로직을 통합하여 일관성 유지.
기존 코드에 영향 없이 신규 유틸리티로 제공.
"""
from typing import Dict, Optional

from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.settings_service import settings_service


class LLMConfigManager:
    """LLM 설정 통합 관리 클래스"""
    
    @staticmethod
    def get_llm_settings(temperature: Optional[float] = None) -> Dict[str, str]:
        """
        LLM 설정 가져오기 (DB → 환경변수 → 기본값 순서로 fallback)
        
        Args:
            temperature: 생성 온도 (None이면 DB 설정 사용)
        
        Returns:
            LLM 설정 딕셔너리
        """
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
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatOpenAI:
        """
        ChatOpenAI 인스턴스 생성
        
        Args:
            temperature: 생성 온도 (기본 0.0)
            model: 모델명 (None이면 DB 설정 사용)
            max_tokens: 최대 토큰 수 (None이면 기본값 사용)
            **kwargs: ChatOpenAI 추가 파라미터
        
        Returns:
            ChatOpenAI 인스턴스
        """
        config = LLMConfigManager.get_llm_settings(temperature)
        
        # 모델 오버라이드
        if model:
            config["model"] = model
        
        # 최대 토큰 수 설정
        if max_tokens is None:
            max_tokens = settings_service.get_value("llm", "max_tokens", 2000)
        
        return ChatOpenAI(
            model=config["model"],
            temperature=config["temperature"],
            api_key=config["api_key"],
            max_tokens=max_tokens,
            **kwargs
        )
    
    @staticmethod
    def get_embedding_settings() -> Dict[str, str]:
        """
        임베딩 설정 가져오기
        
        Returns:
            임베딩 설정 딕셔너리
        """
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
        return {
            "timeout_seconds": settings_service.get_value("nl2sql", "timeout_seconds", 30),
            "max_rows": settings_service.get_value("nl2sql", "max_rows", 1000),
            "read_only_mode": settings_service.get_value("nl2sql", "read_only_mode", True),
        }


# 하위 호환성을 위한 간편 함수들
def get_llm_settings(temperature: Optional[float] = None) -> Dict[str, str]:
    """
    LLM 설정 가져오기 (하위 호환)
    
    Note: LLMConfigManager.get_llm_settings() 사용 권장
    """
    return LLMConfigManager.get_llm_settings(temperature)


def get_rag_settings() -> Dict:
    """
    RAG 설정 가져오기 (하위 호환)
    
    Note: LLMConfigManager.get_rag_settings() 사용 권장
    """
    return LLMConfigManager.get_rag_settings()


def get_nl2sql_settings() -> Dict:
    """
    NL2SQL 설정 가져오기 (하위 호환)
    
    Note: LLMConfigManager.get_nl2sql_settings() 사용 권장
    """
    return LLMConfigManager.get_nl2sql_settings()

