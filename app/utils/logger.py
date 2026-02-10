import logging
import sys
import os
import inspect
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from app.config import settings

# 파일 핸들러 초기화 여부 플래그
_file_handler_initialized = False


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """커스텀 JSON 로거 포맷터"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['env'] = settings.app_env


def _get_formatter():
    """로그 포맷터 생성"""
    log_format = getattr(settings, 'log_format', 'text').lower()

    if log_format == 'json':
        return CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s',
            timestamp=True,
            json_ensure_ascii=False
        )
    else:
        return logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def _setup_file_handler():
    """
    루트 로거(app)에 파일 핸들러를 한 번만 설정.
    여러 모듈에서 setup_logger()를 호출해도 파일 핸들러는 단일 인스턴스만 존재하여
    Windows에서 TimedRotatingFileHandler의 rename 충돌(WinError 32)을 방지한다.
    """
    global _file_handler_initialized
    if _file_handler_initialized:
        return
    _file_handler_initialized = True

    log_file = getattr(settings, 'log_file', None)
    if not log_file:
        return

    try:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        backup_count = getattr(settings, 'log_backup_count', 30)
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(_get_formatter())

        # 'app' 루트 로거에 파일 핸들러를 한 번만 등록
        root_app_logger = logging.getLogger('app')
        root_app_logger.addHandler(file_handler)
    except Exception as e:
        logging.getLogger('app').warning(f"로그 파일 핸들러 설정 실패: {e}")


def _setup_root_app_logger():
    """
    'app' 루트 로거에 콘솔 + 파일 핸들러를 한 번만 설정.
    하위 로거(app.main, app.core.* 등)는 핸들러 없이 propagate로 이 로거를 통해 출력한다.
    """
    root_app_logger = logging.getLogger('app')
    if root_app_logger.handlers:
        return

    root_app_logger.setLevel(getattr(logging, settings.log_level))

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_get_formatter())
    root_app_logger.addHandler(console_handler)

    # 파일 핸들러
    _setup_file_handler()

    # Python 최상위 root 로거로 전파하지 않음
    root_app_logger.propagate = False


def setup_logger(name: str) -> logging.Logger:
    """
    로거 설정.

    'app' 루트 로거에만 콘솔/파일 핸들러를 설정하고,
    하위 로거(app.main, app.core.* 등)는 핸들러 없이 propagate=True로
    'app' 루트를 통해 출력한다. 이렇게 하면 파일 핸들러가 단일 인스턴스만 존재하여
    Windows에서 TimedRotatingFileHandler의 rename 충돌(WinError 32)을 방지한다.
    """
    # 'app' 루트 로거 초기화 (최초 1회)
    _setup_root_app_logger()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))

    # 하위 로거는 핸들러를 직접 갖지 않고, 'app' 루트로 전파 (propagate=True가 기본값)
    # 'app' 자체인 경우 _setup_root_app_logger()에서 이미 설정됨
    return logger


def log_step(
    logger: logging.Logger,
    request_id: str,
    module: str,
    step: str,
    stage: str,
    message: str,
    level: str = "INFO",
    **kwargs
):
    """
    통합 로깅 함수

    모든 그래프(AGENT, RAG, NL2SQL) 및 API에서 사용하는 단일 로깅 함수.
    호출 위치(파일명:라인)를 자동으로 포함합니다.

    Args:
        logger: 로거 인스턴스 (setup_logger(__name__)로 생성)
        request_id: 요청 고유 ID (8자리)
        module: 모듈명 (AGENT, RAG, NL2SQL, API 등)
        step: 단계 번호 또는 식별자 (0, 1, 2, INIT, END, ERR 등)
        stage: 처리 스테이지 (INIT, THINK, ACTION, GENERATE, COMPLETE 등)
        message: 로그 메시지
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR). 기본값 INFO
        **kwargs: 추가 정보 (key=value 형태로 출력, 값이 잘리지 않음)
                  특수 키: content - 여러 줄 내용을 별도 줄에 출력

    출력 형식:
        [request_id] [MODULE-step] [STAGE] [file:line] message | key1=value1 | key2=value2

    Example:
        >>> logger = setup_logger(__name__)
        >>> log_step(logger, "abc123", "AGENT", "0", "INIT", "Agent 실행 시작", max_iter=10, model="gpt-4o")
        [abc123] [AGENT-0] [INIT] [agent_graph.py:50] Agent 실행 시작 | max_iter=10 | model=gpt-4o
    """
    # 호출 위치 추출 (caller의 파일명과 라인 번호)
    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame else None
    if caller_frame:
        filename = os.path.basename(caller_frame.f_code.co_filename)
        lineno = caller_frame.f_lineno
        location = f"[{filename}:{lineno}]"
    else:
        location = "[unknown]"

    # content 키는 별도 처리 (여러 줄 내용)
    content = kwargs.pop("content", None)

    # 추가 정보를 key=value 형태로 포맷팅 (값을 자르지 않음)
    extra_parts = [f"{k}={v}" for k, v in kwargs.items()]
    extra_info = " | ".join(extra_parts) if extra_parts else ""

    # 로그 메시지 구성: [request_id] [MODULE-step] [STAGE] [file:line] message
    log_message = f"[{request_id}] [{module}-{step}] [{stage}] {location} {message}"
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