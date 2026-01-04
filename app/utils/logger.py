import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """커스텀 JSON 로거 포맷터"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['env'] = settings.app_env


def setup_logger(name: str) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 스킵
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level))

    # 콘솔 핸들러
    handler = logging.StreamHandler(sys.stdout)

    # 프로덕션 환경에서는 JSON 포맷 사용
    if settings.is_production:
        formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(logger)s %(message)s', timestamp=True)
    else:
        # 개발 환경에서는 일반 포맷 사용
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 상위 로거로 전파하지 않음
    logger.propagate = False

    return logger


# 기본 로거
logger = setup_logger("hr_chatbot")


def log_structured_step(
    request_id: str,
    module: str,  # "AGENT", "RAG", "NL2SQL", "API"
    step: str,
    stage: str,
    message: str,
    **kwargs
):
    """
    구조화된 로깅 헬퍼 (통합)
    
    모든 그래프 및 API 라우트에서 사용 가능한 통합 로깅 함수.
    기존 log_*_step 함수들을 대체하며, 호환성 유지.
    
    Args:
        request_id: 요청 고유 ID
        module: 모듈명 (AGENT, RAG, NL2SQL, API 등)
        step: 단계 (0, 1, 2 또는 INIT, END 등)
        stage: 스테이지 (THINK, ACTION, FINISH 등)
        message: 로그 메시지
        **kwargs: 추가 정보 (key=value 형태로 출력)
    
    Example:
        >>> log_structured_step("abc123", "AGENT", "0", "INIT", "시작", max_iter=10)
        [abc123] [AGENT-0] [INIT] 시작 | max_iter=10
    """
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
    log_message = f"[{request_id}] [{module}-{step}] [{stage}] {message}"
    if extra_info:
        log_message += f" | {extra_info}"
    
    logger.info(log_message)


# 하위 호환성을 위한 별칭 함수들 (Deprecated)
def log_agent_step(request_id: str, step: str, stage: str, message: str, **kwargs):
    """[Deprecated] log_structured_step 사용 권장"""
    log_structured_step(request_id, "AGENT", step, stage, message, **kwargs)


def log_rag_step(request_id: str, step: str, stage: str, message: str, **kwargs):
    """[Deprecated] log_structured_step 사용 권장"""
    log_structured_step(request_id, "RAG", step, stage, message, **kwargs)


def log_nl2sql_step(request_id: str, step: str, stage: str, message: str, **kwargs):
    """[Deprecated] log_structured_step 사용 권장"""
    log_structured_step(request_id, "NL2SQL", step, stage, message, **kwargs)


def log_api_step(request_id: str, step: str, stage: str, message: str, **kwargs):
    """[Deprecated] log_structured_step 사용 권장"""
    log_structured_step(request_id, "API", step, stage, message, **kwargs)
