"""데이터베이스 연결 관리

위치: app/core/database/connection.py
- PostgreSQL 연결 풀 관리
- pgvector 등록
- 커넥션/커서 컨텍스트 매니저
- 시작 시 exponential backoff 재시도
"""
from contextlib import contextmanager
from typing import Generator, Optional
import time

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 재시도 설정
DB_RETRY_MAX_ATTEMPTS = 5       # 최대 재시도 횟수
DB_RETRY_INITIAL_DELAY = 2     # 초기 대기 시간 (초)
DB_RETRY_MAX_DELAY = 30        # 최대 대기 시간 (초)
DB_RETRY_BACKOFF_FACTOR = 2    # 대기 시간 증가 배수


class DatabaseManager:
    """데이터베이스 연결 관리자"""

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None

    def _test_connection(self) -> bool:
        """시작 시 연결 테스트 (인증 오류 등 빠른 실패)"""
        try:
            with psycopg.connect(settings.database_url, connect_timeout=10) as conn:
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

    def _is_retryable_error(self, error: Exception) -> bool:
        """재시도 가능한 오류인지 판별 (인증/DB 미존재 등은 재시도 불필요)"""
        error_msg = str(error).lower()
        non_retryable = [
            "password authentication failed",
            "does not exist",
            "no pg_hba.conf entry",
            "ssl required",
        ]
        return not any(keyword in error_msg for keyword in non_retryable)

    def _test_connection_with_retry(self) -> bool:
        """Exponential backoff로 DB 연결 재시도"""
        delay = DB_RETRY_INITIAL_DELAY

        for attempt in range(1, DB_RETRY_MAX_ATTEMPTS + 1):
            logger.info(f"데이터베이스 연결 시도 {attempt}/{DB_RETRY_MAX_ATTEMPTS}...")

            try:
                with psycopg.connect(settings.database_url, connect_timeout=10) as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                logger.info(f"데이터베이스 연결 성공 (시도 {attempt}/{DB_RETRY_MAX_ATTEMPTS})")
                return True
            except Exception as e:
                logger.warning(f"데이터베이스 연결 실패 (시도 {attempt}/{DB_RETRY_MAX_ATTEMPTS}): {e}")

                # 재시도 불가능한 오류는 즉시 중단
                if not self._is_retryable_error(e):
                    logger.error("재시도 불가능한 오류입니다. 연결 설정을 확인하세요.")
                    return False

                # 마지막 시도가 아니면 대기 후 재시도
                if attempt < DB_RETRY_MAX_ATTEMPTS:
                    logger.info(f"  {delay}초 후 재시도합니다...")
                    time.sleep(delay)
                    delay = min(delay * DB_RETRY_BACKOFF_FACTOR, DB_RETRY_MAX_DELAY)

        logger.error(f"데이터베이스 연결 실패: {DB_RETRY_MAX_ATTEMPTS}회 시도 후 포기")
        return False

    def initialize(self):
        """커넥션 풀 초기화 (exponential backoff 재시도)"""
        if self.pool is None:
            logger.info("데이터베이스 연결 테스트 중...")
            if not self._test_connection_with_retry():
                logger.error(f"  DATABASE_URL: {settings.database_url[:50]}...")
                raise ConnectionError("데이터베이스 연결 실패: 모든 재시도 소진")

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
        """각 connection에 pgvector 등록 및 타임존 설정"""
        register_vector(conn)
        # 세션 타임존을 한국시간으로 설정
        conn.execute("SET timezone = 'Asia/Seoul'")
        conn.commit()

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
