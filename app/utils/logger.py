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
logger = setup_logger("chatbot_mureum")


def log_step(request_id: str, module: str, step: str, stage: str, message: str, **kwargs):
    """
    통합 로깅 함수

    모든 그래프(AGENT, RAG, NL2SQL) 및 API에서 사용하는 단일 로깅 함수.

    Args:
        request_id: 요청 고유 ID (8자리)
        module: 모듈명 (AGENT, RAG, NL2SQL, API 등)
        step: 단계 번호 또는 식별자 (0, 1, 2, INIT, END, ERR 등)
        stage: 처리 스테이지 (INIT, THINK, ACTION, GENERATE, COMPLETE 등)
        message: 로그 메시지
        **kwargs: 추가 정보 (key=value 형태로 출력, 값이 잘리지 않음)

    출력 형식:
        [request_id] [MODULE-step] [STAGE] message | key1=value1 | key2=value2

    Example:
        >>> log_step("abc123", "AGENT", "0", "INIT", "Agent 실행 시작", max_iter=10, model="gpt-4o")
        [abc123] [AGENT-0] [INIT] Agent 실행 시작 | max_iter=10 | model=gpt-4o

        >>> log_step("abc123", "NL2SQL", "1", "GENERATE", "SQL 생성 완료", sql="SELECT * FROM employee WHERE ...")
        [abc123] [NL2SQL-1] [GENERATE] SQL 생성 완료 | sql=SELECT * FROM employee WHERE ...

        >>> log_step("abc123", "RAG", "2", "LLM-OUTPUT", "답변 생성 완료", answer="재택근무 정책은...")
        [abc123] [RAG-2] [LLM-OUTPUT] 답변 생성 완료 | answer=재택근무 정책은...
    """
    # 추가 정보를 key=value 형태로 포맷팅 (값을 자르지 않음)
    extra_parts = []
    for key, value in kwargs.items():
        extra_parts.append(f"{key}={value}")

    extra_info = " | ".join(extra_parts) if extra_parts else ""

    # 로그 메시지 구성
    log_message = f"[{request_id}] [{module}-{step}] [{stage}] {message}"
    if extra_info:
        log_message += f" | {extra_info}"

    logger.info(log_message)
