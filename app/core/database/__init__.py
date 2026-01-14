"""
Database 모듈 - 데이터베이스 연결 및 실행

위치: app/core/database/

- connection: DB 연결 풀 관리 (db_manager)
- external: 외부 비즈니스 DB 연결 (external_db_manager)
- sql_executor: SQL 실행 및 검증
- schema_loader: 스키마 메타데이터 로드
"""
from app.core.database.connection import db_manager, DatabaseManager
from app.core.database.external import external_db_manager, ExternalDatabaseManager
from app.core.database.sql_executor import (
    sql_executor,
    SQLExecutorService,
    SQLExecutionError,
    SQLValidationError,
)
from app.core.database.schema_loader import schema_loader, SchemaLoaderService

__all__ = [
    "db_manager",
    "DatabaseManager",
    "external_db_manager",
    "ExternalDatabaseManager",
    "sql_executor",
    "SQLExecutorService",
    "SQLExecutionError",
    "SQLValidationError",
    "schema_loader",
    "SchemaLoaderService",
]
