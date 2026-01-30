import logging
import sys
import os
from logging.handlers import RotatingFileHandler
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

    # 로그 포맷 설정: LOG_FORMAT 환경변수로 제어 (기본값: text)
    # json: ELK/Datadog 등 로그 수집 시스템 연동 시 사용
    # text: 콘솔에서 직접 확인 시 사용 (기본값)
    log_format = getattr(settings, 'log_format', 'text').lower()

    if log_format == 'json':
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s',
            timestamp=True,
            json_ensure_ascii=False  # 한글 등 비-ASCII 문자를 그대로 출력
        )
    else:
        # 텍스트 포맷 (기본값) - 개발/프로덕션 모두 동일
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 파일 핸들러 (log_file 설정 시)
    log_file = getattr(settings, 'log_file', None)
    if log_file:
        try:
            # 디렉토리가 없으면 생성
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # RotatingFileHandler: 10MB, 최대 5개 백업
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, settings.log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"로그 파일 핸들러 설정 실패: {e}")

    # 상위 로거로 전파하지 않음
    logger.propagate = False

    return logger


# 기본 로거
logger = setup_logger("chatbot_mureum")


def log_step(request_id: str, module: str, step: str, stage: str, message: str, level: str = "INFO", **kwargs):
    """
    통합 로깅 함수

    모든 그래프(AGENT, RAG, NL2SQL) 및 API에서 사용하는 단일 로깅 함수.

    Args:
        request_id: 요청 고유 ID (8자리)
        module: 모듈명 (AGENT, RAG, NL2SQL, API 등)
        step: 단계 번호 또는 식별자 (0, 1, 2, INIT, END, ERR 등)
        stage: 처리 스테이지 (INIT, THINK, ACTION, GENERATE, COMPLETE 등)
        message: 로그 메시지
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR). 기본값 INFO
        **kwargs: 추가 정보 (key=value 형태로 출력, 값이 잘리지 않음)
                  특수 키: content - 여러 줄 내용을 별도 줄에 출력

    출력 형식:
        [request_id] [MODULE-step] [STAGE] message | key1=value1 | key2=value2
        content가 있는 경우:
        [request_id] [MODULE-step] [STAGE] message | key1=value1
        <content 내용>

    Example:
        >>> log_step("abc123", "AGENT", "0", "INIT", "Agent 실행 시작", max_iter=10, model="gpt-4o")
        [abc123] [AGENT-0] [INIT] Agent 실행 시작 | max_iter=10 | model=gpt-4o

        >>> log_step("abc123", "NL2SQL", "1", "GENERATE", "SQL 생성 완료", level="DEBUG", sql="SELECT ...")
        [abc123] [NL2SQL-1] [GENERATE] SQL 생성 완료 | sql=SELECT ...

        >>> log_step("abc123", "AGENT", "1", "LLM-OUTPUT", "LLM 응답", level="DEBUG", content="긴 응답 내용...")
        [abc123] [AGENT-1] [LLM-OUTPUT] LLM 응답
        긴 응답 내용...
    """
    # content 키는 별도 처리 (여러 줄 내용)
    content = kwargs.pop("content", None)

    # 추가 정보를 key=value 형태로 포맷팅 (값을 자르지 않음)
    extra_parts = []
    for key, value in kwargs.items():
        extra_parts.append(f"{key}={value}")

    extra_info = " | ".join(extra_parts) if extra_parts else ""

    # 로그 메시지 구성
    log_message = f"[{request_id}] [{module}-{step}] [{stage}] {message}"
    if extra_info:
        log_message += f" | {extra_info}"

    # content가 있으면 별도 줄에 추가
    if content:
        log_message += f"\n{content}"

    # 로그 레벨에 따라 출력
    level_upper = level.upper()
    if level_upper == "DEBUG":
        logger.debug(log_message)
    elif level_upper == "WARNING":
        logger.warning(log_message)
    elif level_upper == "ERROR":
        logger.error(log_message)
    else:
        logger.info(log_message)