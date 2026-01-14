"""
범용 외부 데이터베이스 연결 관리자

위치: app/core/database/external.py
NL2SQL 쿼리 대상이 되는 비즈니스 데이터베이스 연결을 관리합니다.
- 로컬 business 스키마 또는 원격 DB 지원
- PostgreSQL, Oracle, MySQL, MS SQL Server 등 확장 가능
- 동적 설정 (app_settings의 external_database 카테고리)
"""

from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
import sys

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_service = None


def _get_settings_service():
    """settings_service 지연 로딩"""
    global _settings_service
    if _settings_service is None:
        from app.core.config.settings_service import settings_service
        _settings_service = settings_service
    return _settings_service


class ExternalDatabaseManager:
    """비즈니스 데이터 전용 DB 연결 관리자 (NL2SQL용)"""

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self._config_cache: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """설정에서 DB 연결 정보 로드"""
        settings_service = _get_settings_service()
        config = {
            "enabled": settings_service.get_value("external_database", "enabled", True),
            "db_type": settings_service.get_value("external_database", "db_type", "postgresql"),
            "host": settings_service.get_value("external_database", "host", "localhost"),
            "port": settings_service.get_value("external_database", "port", 5432),
            "database": settings_service.get_value("external_database", "database", "chatbot_system"),
            "username": settings_service.get_value("external_database", "username", "postgres"),
            "password": settings_service.get_value("external_database", "password", ""),
            "schema": settings_service.get_value("external_database", "schema", "business"),
            "allowed_tables": settings_service.get_value(
                "external_database", "allowed_tables",
                "employee,department,job_history,performance_review,salary"
            ),
            "connection_pool_size": settings_service.get_value("external_database", "connection_pool_size", 5),
            "connection_timeout": settings_service.get_value("external_database", "connection_timeout", 10),
        }
        self._config_cache = config
        return config

    def _build_connection_url(self) -> str:
        """연결 URL 생성 (DB 타입별)"""
        config = self._load_config()

        db_type = config["db_type"].lower()
        host = config["host"]
        port = config["port"]
        database = config["database"]
        username = config["username"]
        password = config["password"]

        if db_type == "postgresql":
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            # MySQL 지원 (psycopg3는 PostgreSQL 전용이므로 다른 드라이버 필요)
            raise NotImplementedError("MySQL 지원은 추후 구현 예정 (mysql-connector-python 필요)")
        elif db_type == "oracle":
            raise NotImplementedError("Oracle 지원은 추후 구현 예정 (oracledb 필요)")
        elif db_type == "mssql":
            raise NotImplementedError("MS SQL Server 지원은 추후 구현 예정 (pyodbc 필요)")
        else:
            raise ValueError(f"지원하지 않는 DB 타입: {db_type}")

    def _test_connection(self) -> bool:
        """연결 테스트 (초기화 전 검증)"""
        try:
            config = self._load_config()
            url = self._build_connection_url()
            timeout = config["connection_timeout"]

            with psycopg.connect(url, connect_timeout=timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            logger.info("외부 DB 연결 테스트 성공")
            return True

        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            if "password authentication failed" in error_msg:
                logger.error("외부 DB 인증 실패: 사용자명 또는 비밀번호 확인 필요")
            elif "does not exist" in error_msg:
                logger.error("외부 DB가 존재하지 않습니다.")
            elif "connection refused" in error_msg:
                logger.error("외부 DB 서버에 연결할 수 없습니다.")
            else:
                logger.error(f"외부 DB 연결 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"외부 DB 연결 테스트 중 예외 발생: {e}")
            return False

    def initialize(self, exit_on_failure: bool = False):
        """외부 DB 연결 풀 초기화"""
        if self.pool is not None:
            logger.info("외부 DB 연결 풀이 이미 초기화되어 있습니다.")
            return

        config = self._load_config()

        # enabled=false인 경우 초기화하지 않음 (로컬 business 스키마 사용)
        if not config["enabled"]:
            logger.info("외부 DB 비활성화 상태 (enabled=false). 로컬 business 스키마를 사용합니다.")
            return

        # 연결 테스트
        logger.info("외부 DB 연결 테스트 중...")
        if not self._test_connection():
            logger.error("외부 DB 연결 테스트 실패. 설정을 확인하세요.")
            logger.error(f"  Host: {config['host']}:{config['port']}")
            logger.error(f"  Database: {config['database']}")
            logger.error(f"  Schema: {config['schema']}")
            if exit_on_failure:
                sys.exit(1)
            raise ConnectionError("외부 데이터베이스 연결 실패")

        # 연결 풀 생성
        try:
            url = self._build_connection_url()
            pool_size = config["connection_pool_size"]

            self.pool = ConnectionPool(
                conninfo=url,
                min_size=max(1, pool_size // 2),
                max_size=pool_size,
                max_idle=300,  # 5분
                max_lifetime=3600,  # 1시간
                timeout=30,
                num_workers=2,
                kwargs={
                    "row_factory": dict_row,
                    "options": f"-c search_path={config['schema']},public"  # 스키마 설정
                }
            )
            logger.info(f"외부 DB 연결 풀 초기화 완료 (스키마: {config['schema']}, 풀 크기: {pool_size})")

        except Exception as e:
            logger.error(f"외부 DB 연결 풀 생성 실패: {e}")
            if exit_on_failure:
                sys.exit(1)
            raise

    def close(self):
        """연결 풀 종료"""
        if self.pool:
            self.pool.close()
            self.pool = None
            logger.info("외부 DB 연결 풀 종료")

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """외부 DB 커넥션 가져오기 (컨텍스트 매니저)"""
        if not self.pool:
            self.initialize()

        # enabled=false인 경우 로컬 DB의 business 스키마 사용
        config = self._config_cache or self._load_config()
        if not config["enabled"]:
            # 로컬 DB 사용
            from app.core.database.connection import db_manager
            with db_manager.get_connection() as conn:
                # search_path를 business 스키마로 설정
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {config['schema']}, public")
                yield conn
            return

        # 외부 DB 사용
        with self.pool.connection() as conn:
            yield conn

    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[psycopg.Cursor, None, None]:
        """외부 DB 커서 가져오기 (컨텍스트 매니저)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    yield cur
                    if commit:
                        conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    def get_allowed_tables(self) -> set:
        """NL2SQL에서 쿼리 가능한 테이블 목록 (보안 화이트리스트)"""
        config = self._config_cache or self._load_config()
        tables_str = config["allowed_tables"]
        return set(t.strip() for t in tables_str.split(',') if t.strip())

    def get_schema_name(self) -> str:
        """현재 사용 중인 스키마명 반환"""
        config = self._config_cache or self._load_config()
        return config["schema"]

    def is_enabled(self) -> bool:
        """외부 DB 사용 여부"""
        config = self._config_cache or self._load_config()
        return config["enabled"]

    def reload_config(self):
        """설정 다시 로드 (UI에서 설정 변경 후 호출)"""
        self._config_cache.clear()
        if self.pool:
            logger.info("외부 DB 설정 변경 감지. 연결 풀을 재초기화합니다.")
            self.close()
            self.initialize()


# 싱글톤 인스턴스
external_db_manager = ExternalDatabaseManager()


# 의존성 주입용 헬퍼 함수
def get_external_db_connection() -> Generator[psycopg.Connection, None, None]:
    """FastAPI 의존성 주입용 커넥션 제공"""
    with external_db_manager.get_connection() as conn:
        yield conn


def get_external_db_cursor(commit: bool = False) -> Generator[psycopg.Cursor, None, None]:
    """FastAPI 의존성 주입용 커서 제공"""
    with external_db_manager.get_cursor(commit=commit) as cur:
        yield cur
