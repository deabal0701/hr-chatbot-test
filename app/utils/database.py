from contextlib import contextmanager
from typing import Generator, Optional
import sys

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """데이터베이스 연결 관리자"""

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None

    def _test_connection(self) -> bool:
        """시작 시 연결 테스트 (인증 오류 등 빠른 실패)"""
        try:
            with psycopg.connect(
                settings.database_url,
                connect_timeout=10
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True
        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            if "password authentication failed" in error_msg:
                logger.error("데이터베이스 인증 실패: 사용자명 또는 비밀번호가 올바르지 않습니다.")
            elif "does not exist" in error_msg:
                logger.error("데이터베이스가 존재하지 않습니다.")
            elif "connection refused" in error_msg:
                logger.error("데이터베이스 서버에 연결할 수 없습니다.")
            else:
                logger.error(f"데이터베이스 연결 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False

    def initialize(self, exit_on_failure: bool = True):
        """커넥션 풀 초기화"""
        if self.pool is None:
            # 먼저 연결 테스트
            logger.info("데이터베이스 연결 테스트 중...")
            if not self._test_connection():
                logger.error("데이터베이스 연결 테스트 실패. 설정을 확인하세요.")
                logger.error(f"  DATABASE_URL: {settings.database_url[:50]}...")
                if exit_on_failure:
                    sys.exit(1)
                raise ConnectionError("데이터베이스 연결 실패")

            logger.info("데이터베이스 연결 테스트 성공")

            self.pool = ConnectionPool(
                conninfo=settings.database_url,
                min_size=settings.db_pool_size // 2,
                max_size=settings.db_pool_size,
                max_idle=300,  # 5분
                max_lifetime=3600,  # 1시간
                timeout=30,
                num_workers=3,  # 연결 생성 워커 수 제한
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
