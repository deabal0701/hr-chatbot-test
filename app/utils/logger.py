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
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s',
            timestamp=True
        )
    else:
        # 개발 환경에서는 일반 포맷 사용
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 상위 로거로 전파하지 않음
    logger.propagate = False

    return logger


# 기본 로거
logger = setup_logger("hr_chatbot")
