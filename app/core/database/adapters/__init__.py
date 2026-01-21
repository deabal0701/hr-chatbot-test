"""데이터베이스 어댑터 패키지

위치: app/core/database/adapters/__init__.py
- DB 어댑터 팩토리 제공
- 지원 DB: PostgreSQL, Oracle
"""
from typing import Dict, Type

from app.core.database.adapters.base import DatabaseAdapter
from app.core.database.adapters.postgresql import PostgreSQLAdapter
from app.core.database.adapters.oracle import OracleAdapter

# 지원 DB 어댑터 레지스트리
_ADAPTERS: Dict[str, Type[DatabaseAdapter]] = {
    "postgresql": PostgreSQLAdapter,
    "oracle": OracleAdapter,
}

# 기본 포트 매핑
DEFAULT_PORTS: Dict[str, int] = {
    "postgresql": 5432,
    "oracle": 1521,
    "mysql": 3306,
    "mssql": 1433,
}


def get_adapter(db_type: str) -> DatabaseAdapter:
    """
    DB 타입에 맞는 어댑터 인스턴스 반환

    Args:
        db_type: 데이터베이스 타입 (postgresql, oracle 등)

    Returns:
        DatabaseAdapter 구현체

    Raises:
        ValueError: 지원하지 않는 DB 타입
    """
    adapter_class = _ADAPTERS.get(db_type.lower())
    if not adapter_class:
        supported = list(_ADAPTERS.keys())
        raise ValueError(f"지원하지 않는 DB 타입: {db_type} (지원: {supported})")
    return adapter_class()


def get_default_port(db_type: str) -> int:
    """
    DB 타입별 기본 포트 반환

    Args:
        db_type: 데이터베이스 타입

    Returns:
        기본 포트 번호
    """
    return DEFAULT_PORTS.get(db_type.lower(), 5432)


def get_supported_db_types() -> list:
    """지원되는 DB 타입 목록 반환"""
    return list(_ADAPTERS.keys())


def is_supported_db_type(db_type: str) -> bool:
    """지원되는 DB 타입인지 확인"""
    return db_type.lower() in _ADAPTERS


__all__ = [
    "DatabaseAdapter",
    "PostgreSQLAdapter",
    "OracleAdapter",
    "get_adapter",
    "get_default_port",
    "get_supported_db_types",
    "is_supported_db_type",
    "DEFAULT_PORTS",
]
