"""PostgreSQL 데이터베이스 어댑터

위치: app/core/database/adapters/postgresql.py
- PostgreSQL 전용 연결 및 쿼리 처리
- psycopg3 드라이버 사용
"""
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.database.adapters.base import DatabaseAdapter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL 어댑터"""

    @property
    def db_type(self) -> str:
        return "postgresql"

    @property
    def default_port(self) -> int:
        return 5432

    def build_connection_url(self, config: Dict[str, Any]) -> str:
        """PostgreSQL 연결 URL 생성"""
        username = config.get('username', 'postgres')
        password = config.get('password', '')
        host = config.get('host', 'localhost')
        port = config.get('port', 5432)
        database = config.get('database', 'postgres')
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"

    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """PostgreSQL 연결 테스트"""
        try:
            url = self.build_connection_url(config)
            timeout = config.get('connection_timeout', 10)
            with psycopg.connect(url, connect_timeout=timeout) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return True, None
        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            if "password authentication failed" in error_msg:
                return False, "인증 실패: 사용자명 또는 비밀번호가 올바르지 않습니다."
            elif "does not exist" in error_msg:
                return False, "데이터베이스가 존재하지 않습니다."
            elif "connection refused" in error_msg or "could not connect" in error_msg:
                return False, f"서버에 연결할 수 없습니다: {config.get('host')}:{config.get('port')}"
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def create_pool(self, url: str, config: Dict[str, Any]) -> ConnectionPool:
        """PostgreSQL 연결 풀 생성"""
        pool_size = config.get('connection_pool_size', 5)
        schema = config.get('schema', 'public')
        return ConnectionPool(
            conninfo=url,
            min_size=max(1, pool_size // 2),
            max_size=pool_size,
            max_idle=300,
            max_lifetime=3600,
            timeout=30,
            num_workers=2,
            kwargs={
                "row_factory": dict_row,
                "options": f"-c search_path={schema},public"
            }
        )

    def close_pool(self, pool: Any) -> None:
        """연결 풀 종료"""
        if pool:
            pool.close()

    @contextmanager
    def get_connection(self, pool: Any, schema: str) -> Generator:
        """PostgreSQL 커넥션 가져오기"""
        with pool.connection() as conn:
            yield conn

    @contextmanager
    def get_cursor(self, connection: Any) -> Generator:
        """PostgreSQL 커서 가져오기"""
        with connection.cursor() as cur:
            yield cur

    # ==========================================================================
    # 스키마 조회 쿼리
    # ==========================================================================

    def get_tables_query(self, schema: str) -> Tuple[str, tuple]:
        """테이블 목록 조회 쿼리"""
        return ("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (schema,))

    def get_columns_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """컬럼 정보 조회 쿼리 (코멘트 포함)"""
        return ("""
            SELECT
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                pd.description AS column_comment
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_statio_all_tables st
                ON c.table_schema = st.schemaname AND c.table_name = st.relname
            LEFT JOIN pg_catalog.pg_description pd
                ON pd.objoid = st.relid AND pd.objsubid = c.ordinal_position
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (schema, table))

    def get_primary_key_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """기본 키 조회 쿼리"""
        return ("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = (%s || '.' || %s)::regclass AND i.indisprimary
        """, (schema, table))

    def get_foreign_keys_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """외래 키 조회 쿼리"""
        return ("""
            SELECT kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s AND tc.table_name = %s
        """, (schema, table))

    def get_indexes_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """인덱스 조회 쿼리"""
        return ("SELECT indexname FROM pg_indexes WHERE schemaname = %s AND tablename = %s", (schema, table))

    # ==========================================================================
    # SQL 실행 관련
    # ==========================================================================

    def set_timeout(self, cursor: Any, timeout_seconds: int) -> None:
        """쿼리 타임아웃 설정 (밀리초 단위)"""
        cursor.execute(f"SET statement_timeout = {timeout_seconds * 1000}")

    def add_limit_clause(self, sql: str, limit: int) -> str:
        """LIMIT 절 추가"""
        sql_upper = sql.upper()
        if 'LIMIT' not in sql_upper:
            return sql.rstrip(';').strip() + f' LIMIT {limit}'
        return sql

    def get_sample_query(self, table: str, limit: int, columns: Optional[List[str]] = None) -> str:
        """샘플 데이터 조회 쿼리"""
        cols = ', '.join(columns) if columns else '*'
        return f"SELECT {cols} FROM {table} LIMIT {limit}"

    def get_explain_query(self, sql: str) -> str:
        """EXPLAIN 쿼리"""
        return f"EXPLAIN (FORMAT JSON) {sql}"

    def get_sql_dialect_name(self) -> str:
        """SQL 방언 이름"""
        return "PostgreSQL"

    # ==========================================================================
    # 결과 변환
    # ==========================================================================

    def row_to_dict(self, row: Any, columns: List[str]) -> Dict[str, Any]:
        """행 데이터를 딕셔너리로 변환 (psycopg3 dict_row는 이미 dict 반환)

        datetime 객체는 ISO 문자열로 변환하여 JSON 직렬화 가능하게 합니다.
        """
        from datetime import datetime, date, time
        from decimal import Decimal

        if isinstance(row, dict):
            result = row.copy()
        else:
            result = dict(zip(columns, row))

        # datetime, date, time, Decimal 등 JSON 직렬화 불가능한 타입 변환
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, date):
                result[key] = value.isoformat()
            elif isinstance(value, time):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)

        return result

    def get_column_names(self, cursor: Any) -> List[str]:
        """커서에서 컬럼명 추출"""
        if cursor.description:
            return [desc[0] for desc in cursor.description]
        return []
