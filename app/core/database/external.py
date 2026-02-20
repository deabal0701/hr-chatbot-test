"""
범용 외부 데이터베이스 연결 관리자 (멀티테넌트 + Lazy 초기화)

위치: app/core/database/external.py
NL2SQL 쿼리 대상이 되는 비즈니스 데이터베이스 연결을 관리합니다.
- 테넌트별 연결 풀 관리 (자체 설정 테넌트: 별도 풀, 미설정 테넌트: 공용 풀)
- Lazy 초기화 (기동 시 연결 안 함, 최초 요청 시 연결)
- PostgreSQL, Oracle 지원 (어댑터 패턴)
- 동적 설정 (tb_app_settings의 external_database 카테고리)
"""

import threading
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any

from app.core.database.adapters.factory import get_adapter
from app.core.database.adapters.base import DatabaseAdapter
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


def _get_tenant_id():
    """현재 요청의 tenant_id 조회 (지연 import)"""
    from app.core.security.tenant_context import get_tenant_id
    return get_tenant_id()


class ExternalDatabaseManager:
    """비즈니스 데이터 전용 DB 연결 관리자 (NL2SQL용, 멀티테넌트)

    - 테넌트별 연결 풀: 자체 external_database 설정이 있는 테넌트만 별도 풀 생성
    - 미설정 테넌트: 공용 테넌트('1')의 풀을 공유
    - Lazy 초기화: 앱 기동 시 연결하지 않고, 최초 NL2SQL/Agent 요청 시 연결
    """

    def __init__(self):
        self._pools: Dict[str, Any] = {}                    # tenant_id → connection pool
        self._adapters: Dict[str, DatabaseAdapter] = {}      # tenant_id → adapter
        self._config_caches: Dict[str, Dict[str, Any]] = {}  # tenant_id → config dict
        self._disabled_tenants: set = set()                   # enabled=false 테넌트 캐시
        self._lock = threading.Lock()

    # =========================================================================
    # 내부 유틸리티
    # =========================================================================

    def _resolve_tenant_id(self, tenant_id: Optional[str] = None) -> str:
        """tenant_id 해석: 명시 → contextvars → '1' (하위 호환)"""
        if tenant_id is not None:
            return str(tenant_id)
        ctx_tid = _get_tenant_id()
        if ctx_tid:
            return str(ctx_tid)
        return '1'

    def _get_pool_tenant_id(self, tenant_id: str) -> str:
        """풀 키 결정: 자체 external_database 설정 있으면 tenant_id, 없으면 '1' (공용)"""
        if tenant_id == '1':
            return '1'
        settings_config = _get_settings_config()
        settings_config._load_cache()
        tenant_ext = settings_config._cache.get(tenant_id, {}).get('external_database', {})
        return tenant_id if tenant_ext else '1'

    def _load_config(self, tenant_id: str = '1') -> Dict[str, Any]:
        """설정에서 DB 연결 정보 로드 (테넌트별)"""
        settings_config = _get_settings_config()
        config = {
            "enabled": settings_config.get_value("external_database", "enabled", True, tenant_id=tenant_id),
            "db_type": settings_config.get_value("external_database", "db_type", "postgresql", tenant_id=tenant_id),
            "host": settings_config.get_value("external_database", "host", "localhost", tenant_id=tenant_id),
            "port": settings_config.get_value("external_database", "port", 5432, tenant_id=tenant_id),
            "database": settings_config.get_value("external_database", "database", "chatbot_system", tenant_id=tenant_id),
            "username": settings_config.get_value("external_database", "username", "postgres", tenant_id=tenant_id),
            "password": settings_config.get_value("external_database", "password", "", tenant_id=tenant_id),
            "schema": settings_config.get_value("external_database", "schema", "business", tenant_id=tenant_id),
            "allowed_tables": settings_config.get_value("external_database", "allowed_tables", "employee,department,job_history,performance_review,salary", tenant_id=tenant_id),
            "connection_pool_size": settings_config.get_value("external_database", "connection_pool_size", 5, tenant_id=tenant_id),
            "connection_timeout": settings_config.get_value("external_database", "connection_timeout", 10, tenant_id=tenant_id),
        }
        self._config_caches[tenant_id] = config
        return config

    def _get_adapter(self, tenant_id: str = '1') -> DatabaseAdapter:
        """테넌트별 DB 타입에 맞는 어댑터 반환"""
        config = self._config_caches.get(tenant_id) or self._load_config(tenant_id)
        db_type = config["db_type"]
        existing = self._adapters.get(tenant_id)
        if existing is None or existing.db_type != db_type:
            self._adapters[tenant_id] = get_adapter(db_type)
        return self._adapters[tenant_id]

    def _test_connection(self, tenant_id: str = '1') -> bool:
        """연결 테스트 (초기화 전 검증)"""
        try:
            config = self._config_caches.get(tenant_id) or self._load_config(tenant_id)
            adapter = self._get_adapter(tenant_id)
            success, error_msg = adapter.test_connection(config)
            if success:
                logger.info(f"외부 DB 연결 테스트 성공 (테넌트: {tenant_id})")
                return True
            else:
                logger.error(f"외부 DB 연결 테스트 실패 (테넌트: {tenant_id}): {error_msg}")
                return False
        except Exception as e:
            logger.error(f"외부 DB 연결 테스트 중 예외 발생 (테넌트: {tenant_id}): {e}")
            return False

    def _ensure_pool(self, tenant_id: str) -> None:
        """테넌트별 연결 풀 lazy 생성 (thread-safe)"""
        pool_tid = self._get_pool_tenant_id(tenant_id)

        # 빠른 경로: 이미 풀이 있거나 disabled로 확인됨
        if pool_tid in self._pools or pool_tid in self._disabled_tenants:
            return

        with self._lock:
            # double-checked locking
            if pool_tid in self._pools or pool_tid in self._disabled_tenants:
                return

            config = self._load_config(pool_tid)

            if not config["enabled"]:
                self._disabled_tenants.add(pool_tid)
                logger.info(f"테넌트 {pool_tid}: 외부 DB 비활성화 (enabled=false)")
                return

            # 연결 테스트
            logger.info(f"테넌트 {pool_tid}: 외부 DB 연결 테스트 중...")
            if not self._test_connection(pool_tid):
                logger.error(f"테넌트 {pool_tid}: 외부 DB 연결 실패 - {config['db_type']}://{config['host']}:{config['port']}/{config['database']}")
                raise ConnectionError(f"외부 데이터베이스 연결 실패 (테넌트: {pool_tid})")

            # 연결 풀 생성
            try:
                adapter = self._get_adapter(pool_tid)
                url = adapter.build_connection_url(config)
                self._pools[pool_tid] = adapter.create_pool(url, config)
                logger.info(f"테넌트 {pool_tid}: 외부 DB 연결 풀 생성 완료 (타입: {config['db_type']}, 스키마: {config['schema']}, 풀 크기: {config['connection_pool_size']})")
            except Exception as e:
                logger.error(f"테넌트 {pool_tid}: 외부 DB 연결 풀 생성 실패: {e}")
                raise

    # =========================================================================
    # 라이프사이클
    # =========================================================================

    def initialize(self, exit_on_failure: bool = False):
        """Lazy 초기화 모드 (기동 시 연결하지 않음, 최초 요청 시 테넌트별 연결)"""
        logger.info("외부 DB lazy 초기화 모드 (최초 요청 시 테넌트별 연결)")

    def close(self):
        """모든 테넌트의 연결 풀 종료"""
        closed_count = 0
        for tid, pool in list(self._pools.items()):
            adapter = self._adapters.get(tid)
            if pool and adapter:
                try:
                    adapter.close_pool(pool)
                    closed_count += 1
                except Exception as e:
                    logger.warning(f"테넌트 {tid} 풀 종료 실패: {e}")

        self._pools.clear()
        self._adapters.clear()
        self._config_caches.clear()
        self._disabled_tenants.clear()
        if closed_count > 0:
            logger.info(f"외부 DB 연결 풀 종료 완료 ({closed_count}개 테넌트)")

    def close_tenant(self, tenant_id: str):
        """특정 테넌트의 연결 풀만 종료"""
        pool = self._pools.pop(tenant_id, None)
        adapter = self._adapters.get(tenant_id)
        if pool and adapter:
            try:
                adapter.close_pool(pool)
                logger.info(f"테넌트 {tenant_id}: 외부 DB 연결 풀 종료")
            except Exception as e:
                logger.warning(f"테넌트 {tenant_id} 풀 종료 실패: {e}")

    # =========================================================================
    # 커넥션/커서
    # =========================================================================

    @contextmanager
    def get_connection(self, tenant_id: Optional[str] = None) -> Generator[Any, None, None]:
        """외부 DB 커넥션 가져오기 (테넌트별, lazy 초기화)"""
        tid = self._resolve_tenant_id(tenant_id)
        pool_tid = self._get_pool_tenant_id(tid)
        self._ensure_pool(pool_tid)

        config = self._config_caches.get(pool_tid) or self._load_config(pool_tid)
        if not config["enabled"]:
            raise ConnectionError("외부 데이터베이스가 설정되지 않았습니다. 관리자에게 문의하세요.")

        adapter = self._get_adapter(pool_tid)
        with adapter.get_connection(self._pools[pool_tid], config['schema']) as conn:
            yield conn

    @contextmanager
    def get_cursor(self, commit: bool = False, tenant_id: Optional[str] = None) -> Generator[Any, None, None]:
        """외부 DB 커서 가져오기 (테넌트별, lazy 초기화)"""
        tid = self._resolve_tenant_id(tenant_id)
        pool_tid = self._get_pool_tenant_id(tid)
        with self.get_connection(tenant_id=pool_tid) as conn:
            adapter = self._get_adapter(pool_tid)
            with adapter.get_cursor(conn) as cur:
                try:
                    yield cur
                    if commit:
                        conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    # =========================================================================
    # 설정 조회 (테넌트별)
    # =========================================================================

    def _get_config(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """테넌트별 config 조회 (내부 헬퍼)"""
        tid = self._resolve_tenant_id(tenant_id)
        pool_tid = self._get_pool_tenant_id(tid)
        return self._config_caches.get(pool_tid) or self._load_config(pool_tid)

    def get_allowed_tables(self, tenant_id: Optional[str] = None) -> set:
        """NL2SQL에서 쿼리 가능한 테이블 목록 (보안 화이트리스트)"""
        config = self._get_config(tenant_id)
        tables_str = config["allowed_tables"]
        return set(t.strip().lower() for t in tables_str.split(',') if t.strip())

    def get_schema_name(self, tenant_id: Optional[str] = None) -> str:
        """현재 사용 중인 스키마명 반환"""
        return self._get_config(tenant_id)["schema"]

    def get_db_type(self, tenant_id: Optional[str] = None) -> str:
        """현재 DB 타입 반환"""
        return self._get_config(tenant_id)["db_type"]

    def is_enabled(self, tenant_id: Optional[str] = None) -> bool:
        """외부 DB 사용 여부"""
        return self._get_config(tenant_id)["enabled"]

    def get_adapter(self, tenant_id: Optional[str] = None) -> DatabaseAdapter:
        """현재 어댑터 인스턴스 반환 (외부 접근용)"""
        tid = self._resolve_tenant_id(tenant_id)
        pool_tid = self._get_pool_tenant_id(tid)
        return self._get_adapter(pool_tid)

    # =========================================================================
    # 설정 갱신
    # =========================================================================

    def reload_config(self, tenant_id: Optional[str] = None):
        """설정 다시 로드 (UI에서 설정 변경 후 호출)"""
        tid = self._resolve_tenant_id(tenant_id)

        # disabled 캐시에서 제거 → 다음 요청에서 재체크 허용
        self._disabled_tenants.discard(tid)

        # 해당 테넌트 캐시 클리어
        self._config_caches.pop(tid, None)
        self._adapters.pop(tid, None)

        # 해당 테넌트 풀 종료
        self.close_tenant(tid)

        # 관련 스키마 캐시 클리어
        try:
            from app.core.database.schema_loader import schema_loader
            schema_loader.clear_tenant_cache(tid)
        except Exception:
            pass
        try:
            from app.core.llm.sql_generator import sql_generator
            sql_generator.clear_tenant_cache(tid)
        except Exception:
            pass

        logger.info(f"테넌트 {tid}: 외부 DB 설정 캐시 갱신 완료 (다음 요청 시 재연결)")

    # =========================================================================
    # 하위 호환
    # =========================================================================

    @property
    def pool(self):
        """하위 호환: 현재 테넌트의 풀 반환"""
        tid = self._resolve_tenant_id()
        pool_tid = self._get_pool_tenant_id(tid)
        return self._pools.get(pool_tid)


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
