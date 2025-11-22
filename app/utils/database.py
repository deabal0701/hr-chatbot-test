from contextlib import contextmanager
from typing import Generator, Optional

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings


class DatabaseManager:
    """데이터베이스 연결 관리자"""

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None

    def initialize(self):
        """커넥션 풀 초기화"""
        if self.pool is None:
            self.pool = ConnectionPool(
                conninfo=settings.database_url,
                min_size=settings.db_pool_size // 2,
                max_size=settings.db_pool_size,
                max_idle=300,  # 5분
                max_lifetime=3600,  # 1시간
                timeout=30,
                kwargs={"row_factory": dict_row},
                configure=self._configure_connection
            )

    @staticmethod
    def _configure_connection(conn: psycopg.Connection):
        """각 connection에 pgvector 등록"""
        register_vector(conn)

    def close(self):
        """커넥션 풀 종료"""
        if self.pool:
            self.pool.close()
            self.pool = None

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """커넥션 가져오기 (컨텍스트 매니저)"""
        if not self.pool:
            self.initialize()

        with self.pool.connection() as conn:
            yield conn

    @contextmanager
    def get_cursor(self, commit: bool = False) -> Generator[psycopg.Cursor, None, None]:
        """커서 가져오기 (컨텍스트 매니저)"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    yield cur
                    if commit:
                        conn.commit()
                except Exception:
                    conn.rollback()
                    raise


# 글로벌 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """의존성 주입용 커넥션 제공"""
    with db_manager.get_connection() as conn:
        yield conn


def get_db_cursor(commit: bool = False) -> Generator[psycopg.Cursor, None, None]:
    """의존성 주입용 커서 제공"""
    with db_manager.get_cursor(commit=commit) as cur:
        yield cur
