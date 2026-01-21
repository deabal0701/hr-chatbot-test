"""
범용 외부 데이터베이스 연결 관리자

위치: app/core/database/external.py
NL2SQL 쿼리 대상이 되는 비즈니스 데이터베이스 연결을 관리합니다.
- 로컬 business 스키마 또는 원격 DB 지원
- PostgreSQL, Oracle 지원 (어댑터 패턴)
- 동적 설정 (tb_app_settings의 external_database 카테고리)
"""

from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
import sys

from app.core.database.adapters import get_adapter, DatabaseAdapter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    """settings_config 지연 로딩"""
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


class ExternalDatabaseManager:
    """비즈니스 데이터 전용 DB 연결 관리자 (NL2SQL용)"""

    def __init__(self):
        self.pool: Optional[Any] = None
        self._adapter: Optional[DatabaseAdapter] = None
        self._config_cache: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """설정에서 DB 연결 정보 로드"""
        settings_config = _get_settings_config()
        config = {
            "enabled": settings_config.get_value("external_database", "enabled", True),
            "db_type": settings_config.get_value("external_database", "db_type", "postgresql"),
            "host": settings_config.get_value("external_database", "host", "localhost"),
            "port": settings_config.get_value("external_database", "port", 5432),
            "database": settings_config.get_value("external_database", "database", "chatbot_system"),
            "username": settings_config.get_value("external_database", "username", "postgres"),
            "password": settings_config.get_value("external_database", "password", ""),
            "schema": settings_config.get_value("external_database", "schema", "business"),
            "allowed_tables": settings_config.get_value(
                "external_database", "allowed_tables",
                "employee,department,job_history,performance_review,salary"
            ),
            "connection_pool_size": settings_config.get_value("external_database", "connection_pool_size", 5),
            "connection_timeout": settings_config.get_value("external_database", "connection_timeout", 10),
        }
        self._config_cache = config
        return config

    def _get_adapter(self) -> DatabaseAdapter:
        """현재 DB 타입에 맞는 어댑터 반환"""
        config = self._config_cache or self._load_config()
        db_type = config["db_type"]
        if self._adapter is None or self._adapter.db_type != db_type:
            self._adapter = get_adapter(db_type)
        return self._adapter

    def _test_connection(self) -> bool:
        """연결 테스트 (초기화 전 검증)"""
        try:
            config = self._load_config()
            adapter = self._get_adapter()
            success, error_msg = adapter.test_connection(config)
            if success:
                logger.info("외부 DB 연결 테스트 성공")
                return True
            else:
                logger.error(f"외부 DB 연결 테스트 실패: {error_msg}")
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
            logger.error(f"  DB Type: {config['db_type']}")
            logger.error(f"  Host: {config['host']}:{config['port']}")
            logger.error(f"  Database: {config['database']}")
            logger.error(f"  Schema: {config['schema']}")
            if exit_on_failure:
                sys.exit(1)
            raise ConnectionError("외부 데이터베이스 연결 실패")

        # 연결 풀 생성
        try:
            adapter = self._get_adapter()
            url = adapter.build_connection_url(config)
            self.pool = adapter.create_pool(url, config)
            logger.info(f"외부 DB 연결 풀 초기화 완료 (타입: {config['db_type']}, 스키마: {config['schema']}, 풀 크기: {config['connection_pool_size']})")

        except Exception as e:
            logger.error(f"외부 DB 연결 풀 생성 실패: {e}")
            if exit_on_failure:
                sys.exit(1)
            raise

    def close(self):
        """연결 풀 종료"""
        if self.pool and self._adapter:
            self._adapter.close_pool(self.pool)
            self.pool = None
            logger.info("외부 DB 연결 풀 종료")

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """외부 DB 커넥션 가져오기 (컨텍스트 매니저)"""
        if not self.pool:
            self.initialize()

        # enabled=false인 경우 로컬 DB의 business 스키마 사용
        config = self._config_cache or self._load_config()
        if not config["enabled"]:
            # 로컬 DB 사용 (PostgreSQL)
            from app.core.database.connection import db_manager
            with db_manager.get_connection() as conn:
                # search_path를 business 스키마로 설정
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {config['schema']}, public")
                yield conn
            return

        # 외부 DB 사용 (어댑터 통해)
        adapter = self._get_adapter()
        with adapter.get_connection(self.pool, config['schema']) as conn:
            yield conn

    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[Any, None, None]:
        """외부 DB 커서 가져오기 (컨텍스트 매니저)"""
        with self.get_connection() as conn:
            adapter = self._get_adapter()
            with adapter.get_cursor(conn) as cur:
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
        return set(t.strip().lower() for t in tables_str.split(',') if t.strip())

    def get_schema_name(self) -> str:
        """현재 사용 중인 스키마명 반환"""
        config = self._config_cache or self._load_config()
        return config["schema"]

    def get_db_type(self) -> str:
        """현재 DB 타입 반환"""
        config = self._config_cache or self._load_config()
        return config["db_type"]

    def is_enabled(self) -> bool:
        """외부 DB 사용 여부"""
        config = self._config_cache or self._load_config()
        return config["enabled"]

    def get_adapter(self) -> DatabaseAdapter:
        """현재 어댑터 인스턴스 반환 (외부 접근용)"""
        return self._get_adapter()

    def reload_config(self):
        """설정 다시 로드 (UI에서 설정 변경 후 호출)"""
        old_db_type = self._config_cache.get("db_type") if self._config_cache else None
        self._config_cache.clear()
        new_config = self._load_config()

        # DB 타입이 변경된 경우 어댑터도 갱신
        if old_db_type and old_db_type != new_config["db_type"]:
            self._adapter = None

        if self.pool:
            logger.info("외부 DB 설정 변경 감지. 연결 풀을 재초기화합니다.")
            self.close()
            self.initialize()


# 싱글톤 인스턴스
external_db_manager = ExternalDatabaseManager()


# 의존성 주입용 헬퍼 함수
def get_external_db_connection() -> Generator[Any, None, None]:
    """FastAPI 의존성 주입용 커넥션 제공"""
    with external_db_manager.get_connection() as conn:
        yield conn


def get_external_db_cursor(commit: bool = False) -> Generator[Any, None, None]:
    """FastAPI 의존성 주입용 커서 제공"""
    with external_db_manager.get_cursor(commit=commit) as cur:
        yield cur
