"""Oracle 데이터베이스 어댑터

위치: app/core/database/adapters/oracle.py
- Oracle 전용 연결 및 쿼리 처리
- oracledb 드라이버 사용 (thin 모드)
"""
import re
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

from app.core.database.adapters.base import DatabaseAdapter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# oracledb는 선택적 의존성 (설치 안 된 경우 예외 처리)
try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False
    oracledb = None


class OracleAdapter(DatabaseAdapter):
    """Oracle 어댑터"""

    def __init__(self):
        if not ORACLEDB_AVAILABLE:
            logger.warning("oracledb 패키지가 설치되지 않았습니다. Oracle 지원을 위해 'pip install oracledb'를 실행하세요.")

    def _check_driver(self):
        """드라이버 설치 여부 확인"""
        if not ORACLEDB_AVAILABLE:
            raise ImportError("Oracle 지원을 위해 oracledb 패키지를 설치하세요: pip install oracledb")

    @property
    def db_type(self) -> str:
        return "oracle"

    @property
    def default_port(self) -> int:
        return 1521

    def build_connection_url(self, config: Dict[str, Any]) -> str:
        """Oracle DSN 생성 (thin 모드)"""
        host = config.get('host', 'localhost')
        port = config.get('port', 1521)
        database = config.get('database', 'ORCL')  # service_name 또는 SID
        # Oracle thin 모드 DSN: host:port/service_name
        return f"{host}:{port}/{database}"

    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Oracle 연결 테스트"""
        self._check_driver()
        try:
            dsn = self.build_connection_url(config)
            with oracledb.connect(
                user=config.get('username', ''),
                password=config.get('password', ''),
                dsn=dsn
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM DUAL")
            return True, None
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            error_msg = str(error_obj.message).lower() if hasattr(error_obj, 'message') else str(e).lower()
            if "ora-01017" in error_msg or "invalid username/password" in error_msg:
                return False, "인증 실패: 사용자명 또는 비밀번호가 올바르지 않습니다."
            elif "ora-12541" in error_msg or "no listener" in error_msg:
                return False, f"리스너에 연결할 수 없습니다: {config.get('host')}:{config.get('port')}"
            elif "ora-12514" in error_msg or "service" in error_msg:
                return False, f"서비스를 찾을 수 없습니다: {config.get('database')}"
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def create_pool(self, url: str, config: Dict[str, Any]) -> Any:
        """Oracle 연결 풀 생성"""
        self._check_driver()
        pool_size = config.get('connection_pool_size', 5)
        return oracledb.create_pool(
            user=config.get('username', ''),
            password=config.get('password', ''),
            dsn=url,
            min=max(1, pool_size // 2),
            max=pool_size,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            timeout=30
        )

    def close_pool(self, pool: Any) -> None:
        """연결 풀 종료"""
        if pool:
            pool.close()

    @contextmanager
    def get_connection(self, pool: Any, schema: str) -> Generator:
        """Oracle 커넥션 가져오기 (스키마 = CURRENT_SCHEMA)"""
        # 스키마명 검증: 영문자/숫자/언더스코어만 허용 (SQL 인젝션 방지)
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', schema):
            raise ValueError(f"유효하지 않은 스키마명: {schema}")

        conn = pool.acquire()
        try:
            with conn.cursor() as cur:
                cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {schema}")
            yield conn
        finally:
            pool.release(conn)

    @contextmanager
    def get_cursor(self, connection: Any) -> Generator:
        """Oracle 커서 가져오기"""
        with connection.cursor() as cur:
            yield cur

    # ==========================================================================
    # 스키마 조회 쿼리 (Oracle 카탈로그 뷰 사용)
    # ==========================================================================

    def get_tables_query(self, schema: str) -> Tuple[str, tuple]:
        """테이블 및 뷰 목록 조회 쿼리 (Oracle: ALL_TABLES + ALL_VIEWS + USER_SYNONYMS)

        NL2SQL에서는 테이블뿐 아니라 뷰도 쿼리 대상이 되므로 둘 다 조회합니다.
        또한 Synonym을 통해 다른 스키마의 객체에 접근하는 경우도 지원합니다.
        """
        return ("""
            SELECT table_name FROM all_tables WHERE owner = UPPER(:1)
            UNION
            SELECT view_name AS table_name FROM all_views WHERE owner = UPPER(:1)
            UNION
            SELECT synonym_name AS table_name FROM user_synonyms
            ORDER BY table_name
        """, (schema, schema))

    def get_columns_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """컬럼 정보 조회 쿼리 (Oracle: ALL_TAB_COLUMNS + ALL_COL_COMMENTS, Synonym 지원)

        Synonym을 통해 접근하는 경우 실제 테이블/뷰의 컬럼 정보를 조회합니다.
        컬럼 코멘트도 함께 조회하여 LLM에 더 풍부한 스키마 정보를 제공합니다.
        """
        return ("""
            SELECT
                c.column_name,
                c.data_type,
                c.nullable AS is_nullable,
                c.data_default AS column_default,
                c.char_length AS character_maximum_length,
                cc.comments AS column_comment
            FROM all_tab_columns c
            LEFT JOIN all_col_comments cc
                ON c.owner = cc.owner
                AND c.table_name = cc.table_name
                AND c.column_name = cc.column_name
            WHERE (c.owner = UPPER(:1) AND c.table_name = UPPER(:2))
               OR (c.owner, c.table_name) IN (
                   SELECT table_owner, table_name FROM user_synonyms
                   WHERE synonym_name = UPPER(:2)
               )
            ORDER BY c.column_id
        """, (schema, table, table))

    def get_primary_key_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """기본 키 조회 쿼리 (Oracle: ALL_CONSTRAINTS + ALL_CONS_COLUMNS, Synonym 지원)"""
        return ("""
            SELECT cols.column_name
            FROM all_constraints cons
            JOIN all_cons_columns cols
                ON cons.constraint_name = cols.constraint_name AND cons.owner = cols.owner
            WHERE ((cons.owner = UPPER(:1) AND cons.table_name = UPPER(:2))
                   OR (cons.owner, cons.table_name) IN (
                       SELECT table_owner, table_name FROM user_synonyms
                       WHERE synonym_name = UPPER(:2)
                   ))
                AND cons.constraint_type = 'P'
            ORDER BY cols.position
        """, (schema, table, table))

    def get_foreign_keys_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """외래 키 조회 쿼리 (Oracle, Synonym 지원)"""
        return ("""
            SELECT
                a.column_name,
                c_pk.table_name AS foreign_table_name,
                b.column_name AS foreign_column_name
            FROM all_cons_columns a
            JOIN all_constraints c ON a.constraint_name = c.constraint_name AND a.owner = c.owner
            JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name AND c.r_owner = c_pk.owner
            JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name AND c_pk.owner = b.owner
            WHERE ((c.owner = UPPER(:1) AND c.table_name = UPPER(:2))
                   OR (c.owner, c.table_name) IN (
                       SELECT table_owner, table_name FROM user_synonyms
                       WHERE synonym_name = UPPER(:2)
                   ))
                AND c.constraint_type = 'R'
        """, (schema, table, table))

    def get_indexes_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """인덱스 조회 쿼리 (Oracle: ALL_INDEXES, Synonym 지원)"""
        return ("""
            SELECT index_name
            FROM all_indexes
            WHERE (owner = UPPER(:1) AND table_name = UPPER(:2))
               OR (owner, table_name) IN (
                   SELECT table_owner, table_name FROM user_synonyms
                   WHERE synonym_name = UPPER(:2)
               )
        """, (schema, table, table))

    # ==========================================================================
    # SQL 실행 관련
    # ==========================================================================

    def set_timeout(self, cursor: Any, timeout_seconds: int) -> None:
        """쿼리 타임아웃 설정 (Oracle: 직접 지원 안 함, Resource Manager 사용 권장)"""
        # Oracle에서는 세션 레벨 타임아웃이 직접 지원되지 않음
        # 운영 환경에서는 Resource Manager나 Profile의 IDLE_TIME/CONNECT_TIME 사용
        # 여기서는 로깅만 수행
        logger.debug(f"Oracle 타임아웃 설정 요청: {timeout_seconds}초 (직접 지원 안 함)")

    def add_limit_clause(self, sql: str, limit: int) -> str:
        """LIMIT 절 추가 (Oracle 12c+: FETCH FIRST ... ROWS ONLY)

        LLM이 PostgreSQL 스타일의 LIMIT을 생성할 수 있으므로,
        LIMIT 절이 있으면 FETCH FIRST로 변환합니다.

        주의:
        1. GROUP BY가 있는 집계 쿼리에는 FETCH FIRST를 추가하지 않습니다.
        2. 외부 SELECT에 FROM 절이 없는 경우(스칼라 서브쿼리만 있는 경우)
           FROM DUAL을 추가합니다.
        """
        sql_upper = sql.upper()

        # 이미 FETCH 또는 ROWNUM이 있으면 세미콜론만 제거하고 반환
        if 'FETCH' in sql_upper or 'ROWNUM' in sql_upper:
            return sql.rstrip(';').strip()

        # GROUP BY가 있는 집계 쿼리에는 FETCH FIRST를 추가하지 않음
        if 'GROUP BY' in sql_upper:
            logger.debug("GROUP BY 쿼리에는 FETCH FIRST를 추가하지 않습니다.")
            limit_pattern = re.compile(r'\s+LIMIT\s+\d+\s*;?\s*$', re.IGNORECASE)
            return limit_pattern.sub('', sql).rstrip(';').strip()

        # PostgreSQL 스타일 LIMIT이 있으면 FETCH FIRST로 변환
        limit_pattern = re.compile(r'\s+LIMIT\s+(\d+)\s*;?\s*$', re.IGNORECASE)
        match = limit_pattern.search(sql)
        if match:
            existing_limit = int(match.group(1))
            effective_limit = min(existing_limit, limit)
            sql = limit_pattern.sub('', sql).rstrip(';').strip()
            sql = self._ensure_from_dual(sql)
            return sql + f' FETCH FIRST {effective_limit} ROWS ONLY'

        # LIMIT이 없으면 FETCH FIRST 추가
        sql = sql.rstrip(';').strip()
        sql = self._ensure_from_dual(sql)
        return sql + f' FETCH FIRST {limit} ROWS ONLY'

    def _ensure_from_dual(self, sql: str) -> str:
        """외부 SELECT에 FROM 절이 없으면 FROM DUAL 추가

        Oracle에서 스칼라 서브쿼리만 있는 SELECT 문은 FROM DUAL이 필수입니다.
        예: SELECT (SELECT COUNT(*) FROM emp) AS cnt; → 오류
            SELECT (SELECT COUNT(*) FROM emp) AS cnt FROM DUAL; → 정상
        """
        sql_upper = sql.upper()

        # 이미 FROM DUAL이 있으면 그대로 반환
        if 'FROM DUAL' in sql_upper:
            return sql

        # 외부 SELECT의 FROM 절 존재 여부 확인
        # 서브쿼리 내부의 FROM은 제외해야 함
        if self._has_outer_from_clause(sql):
            return sql

        # FROM 절이 없으면 FROM DUAL 추가
        logger.debug("외부 SELECT에 FROM 절이 없어 FROM DUAL을 추가합니다.")
        return sql + ' FROM DUAL'

    def _has_outer_from_clause(self, sql: str) -> bool:
        """외부 SELECT 레벨에서 FROM 절이 있는지 확인

        괄호 레벨을 추적하여 서브쿼리 내부의 FROM은 무시합니다.
        """
        depth = 0
        sql_upper = sql.upper()
        i = 0

        while i < len(sql_upper):
            char = sql_upper[i]

            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0:
                # 괄호 밖에서 FROM 키워드 찾기 (단어 경계 확인)
                if sql_upper[i:i+4] == 'FROM':
                    # 앞이 공백/시작이고 뒤가 공백인 경우만 FROM 키워드로 인식
                    before_ok = (i == 0 or not sql_upper[i-1].isalnum())
                    after_ok = (i + 4 >= len(sql_upper) or not sql_upper[i+4].isalnum())
                    if before_ok and after_ok:
                        return True

            i += 1

        return False

    def get_sample_query(self, table: str, limit: int, columns: Optional[List[str]] = None) -> str:
        """샘플 데이터 조회 쿼리 (Oracle)"""
        cols = ', '.join(columns) if columns else '*'
        return f"SELECT {cols} FROM {table} FETCH FIRST {limit} ROWS ONLY"

    def get_explain_query(self, sql: str) -> str:
        """EXPLAIN 쿼리 (Oracle: EXPLAIN PLAN FOR)"""
        # Oracle의 EXPLAIN PLAN은 결과를 PLAN_TABLE에 저장함
        # 실제 사용 시 별도 처리 필요
        return f"EXPLAIN PLAN FOR {sql}"

    def get_sql_dialect_name(self) -> str:
        """SQL 방언 이름"""
        return "Oracle"

    # ==========================================================================
    # 결과 변환
    # ==========================================================================

    def row_to_dict(self, row: Any, columns: List[str]) -> Dict[str, Any]:
        """행 데이터를 딕셔너리로 변환 (Oracle은 튜플 반환)

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
            return [desc[0].lower() for desc in cursor.description]  # Oracle은 대문자, 소문자로 변환
        return []
