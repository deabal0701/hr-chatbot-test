"""SQL 실행 및 검증 서비스

위치: app/core/database/sql_executor.py
- SQL Injection 방지
- DDL/DML 차단
- 테이블 화이트리스트 검증
- 타임아웃 및 LIMIT 적용
- 다중 DB 지원 (PostgreSQL, Oracle)
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import DML, DDL, Keyword

from app.config import settings
from app.models.rag import SQLResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_service = None
_external_db_manager = None


def _get_settings_service():
    global _settings_service
    if _settings_service is None:
        from app.core.config.settings_config import settings_config
        _settings_service = settings_config
    return _settings_service


def _get_external_db_manager():
    global _external_db_manager
    if _external_db_manager is None:
        from app.core.database.external import external_db_manager
        _external_db_manager = external_db_manager
    return _external_db_manager


class SQLExecutionError(Exception):
    """SQL 실행 오류 (쿼리 구문/실행 오류)"""
    pass


class SQLConnectionError(Exception):
    """SQL 연결 오류 (DB 접속 실패)"""
    pass


class SQLValidationError(Exception):
    """SQL 검증 오류"""
    pass


class SQLExecutorService:
    """비즈니스 데이터 SQL 실행 서비스 (NL2SQL용)"""

    # 허용되지 않는 키워드 (DDL/DML)
    FORBIDDEN_KEYWORDS = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'DECLARE', 'CURSOR'
    }

    # DB 시스템 테이블 (화이트리스트 검증 제외)
    SYSTEM_TABLES = {'dual'}

    def __init__(self):
        # 기본값 저장 (환경변수)
        self._default_timeout = settings.sql_timeout_seconds
        self._default_max_rows = settings.sql_max_rows
        self._default_read_only = settings.read_only_mode

    @property
    def timeout(self) -> int:
        """현재 타임아웃 설정 (DB 설정 우선)"""
        return _get_settings_service().get_value("nl2sql", "timeout_seconds", self._default_timeout)

    @property
    def max_rows(self) -> int:
        """현재 최대 행 수 설정 (DB 설정 우선)"""
        return _get_settings_service().get_value("nl2sql", "max_rows", self._default_max_rows)

    @property
    def read_only(self) -> bool:
        """현재 읽기 전용 모드 설정 (DB 설정 우선)"""
        return _get_settings_service().get_value("nl2sql", "read_only_mode", self._default_read_only)

    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        SQL 쿼리 검증
        Returns: (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "SQL이 비어있습니다"

        sql_upper = sql.upper()

        # 1. DDL/DML 키워드 체크
        for keyword in self.FORBIDDEN_KEYWORDS:
            # 단어 경계를 고려한 정규표현식
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                logger.warning(f"SQL 검증 실패: 금지 키워드 '{keyword}' 감지, sql={sql}")
                return False, "데이터 조회만 가능합니다. 데이터 변경이 포함된 질문은 처리할 수 없습니다."

        # 2. SQL 파싱
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "SQL 파싱 실패"

            # 2-1. 복수 SQL문 차단 (세미콜론으로 구분된 여러 쿼리)
            real_stmts = [s for s in parsed if s.get_type() is not None]
            if len(real_stmts) > 1:
                logger.warning(f"SQL 검증 실패: 복수 SQL문 감지 ({len(real_stmts)}개), sql={sql[:200]}")
                return False, "단일 쿼리만 실행 가능합니다. 여러 쿼리를 하나로 합쳐주세요."

            stmt: Statement = parsed[0]

            # 3. SELECT 문만 허용 (읽기 전용)
            if self.read_only:
                first_token = stmt.get_type()
                if first_token != 'SELECT':
                    logger.warning(f"SQL 검증 실패: SELECT 외 문 감지 (type={first_token}), sql={sql}")
                    return False, "데이터 조회만 가능합니다. 질문을 다시 확인해주세요."

        except Exception as e:
            return False, f"SQL 파싱 오류: {str(e)}"

        # 4. 테이블 이름 검증 (동적으로 allowed_tables에서 가져옴)
        external_db_manager = _get_external_db_manager()
        allowed_tables = external_db_manager.get_allowed_tables()
        table_names = self._extract_table_names(sql)
        for table in table_names:
            table_lower = table.lower()
            if table_lower not in allowed_tables:
                # DB 시스템 테이블 (DUAL 등)은 검증 제외
                if table_lower in self.SYSTEM_TABLES:
                    logger.debug(f"테이블 검증: '{table}'는 시스템 테이블로 간주하여 무시")
                    continue
                # 짧은 이름(3자 이하)은 서브쿼리/테이블 별칭으로 간주하여 무시
                if len(table) <= 3:
                    logger.debug(f"테이블 검증: '{table}'는 별칭으로 간주하여 무시")
                    continue
                logger.warning(f"테이블 검증 실패: '{table}' not in allowed_tables={allowed_tables}")
                return False, f"'{table}' 테이블은 조회할 수 없습니다. 질문을 다른 표현으로 다시 시도해주세요."

        # 5. LIMIT 절 체크 (권장) - DB 타입에 따라 다른 키워드 확인
        external_db_manager = _get_external_db_manager()
        db_type = external_db_manager.get_db_type()
        if db_type == "oracle":
            # Oracle: FETCH FIRST 또는 ROWNUM
            if 'FETCH' not in sql_upper and 'ROWNUM' not in sql_upper:
                logger.warning(f"Oracle 쿼리에 FETCH/ROWNUM 절이 없음: {sql}")
        else:
            # PostgreSQL: LIMIT
            if 'LIMIT' not in sql_upper:
                logger.warning(f"LIMIT 절이 없는 쿼리: {sql}")

        return True, None

    def _extract_cte_names(self, sql: str) -> set:
        """
        CTE(Common Table Expression) 이름 추출

        WITH emp_scores AS (...), dept_summary AS (...) SELECT ...
        → {'emp_scores', 'dept_summary'}

        WITH RECURSIVE tree AS (...) SELECT ...
        → {'tree'}
        """
        cte_names = set()
        sql_upper = sql.upper().strip()

        # WITH 절이 없으면 빈 집합 반환
        if not sql_upper.startswith('WITH'):
            return cte_names

        # 첫 번째 CTE: WITH [RECURSIVE] name AS (
        pattern = r'\bWITH\s+(?:RECURSIVE\s+)?(\w+)\s+AS\s*\('
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            cte_names.add(match.group(1).lower())

        # 다중 CTE: ), name AS (
        multi_pattern = r'\)\s*,\s*(\w+)\s+AS\s*\('
        for m in re.finditer(multi_pattern, sql, re.IGNORECASE):
            cte_names.add(m.group(1).lower())

        if cte_names:
            logger.debug(f"CTE 이름 감지: {cte_names}")

        return cte_names

    def _extract_table_names(self, sql: str) -> List[str]:
        """
        SQL에서 테이블 이름 추출 (CTE 이름 제외)

        sqlparse를 사용하여 정확하게 추출하며, 실패 시 정규식으로 fallback
        CTE에서 정의된 임시 테이블 이름은 제외됩니다.
        """
        # 1. CTE 이름 추출 (제외 대상)
        cte_names = self._extract_cte_names(sql)

        # 2. 테이블 추출
        try:
            table_names = self._extract_tables_with_sqlparse(sql)
        except Exception as e:
            logger.warning(f"sqlparse 테이블 추출 실패, regex fallback: {e}")
            table_names = self._extract_tables_with_regex(sql)

        # 3. CTE 이름 필터링
        if cte_names:
            original_count = len(table_names)
            table_names = [t for t in table_names if t.lower() not in cte_names]
            if len(table_names) < original_count:
                logger.debug(f"CTE 이름 필터링 완료: 제외={cte_names}, 남은 테이블={table_names}")

        return table_names

    def _extract_tables_with_sqlparse(self, sql: str) -> List[str]:
        """sqlparse를 사용한 테이블 추출 (정확도 높음)

        CTE, 서브쿼리 내부의 테이블도 추출합니다.
        괄호 닫힘 직후의 식별자는 서브쿼리 별칭으로 무시합니다.
        """
        parsed = sqlparse.parse(sql)
        if not parsed:
            return []

        stmt = parsed[0]
        table_names = set()
        from_seen = False
        parenthesis_depth = 0
        just_closed_paren = False  # 괄호가 방금 닫혔는지 (서브쿼리 별칭 감지용)

        for token in stmt.flatten():
            # 공백은 건너뛰기 (just_closed_paren 상태 유지)
            if token.ttype is sqlparse.tokens.Whitespace:
                continue

            # 괄호 깊이 추적
            if token.value == '(':
                parenthesis_depth += 1
                just_closed_paren = False
                from_seen = False  # 서브쿼리 시작 시 from_seen 리셋 (서브쿼리 내부 컬럼을 테이블로 잘못 인식 방지)
                continue
            elif token.value == ')':
                parenthesis_depth -= 1
                just_closed_paren = True  # 괄호가 닫힘 → 다음 식별자는 별칭
                continue
            elif just_closed_paren and token.ttype in (sqlparse.tokens.Name, None):
                # 괄호 직후의 식별자는 서브쿼리 별칭이므로 무시
                just_closed_paren = False
                from_seen = False
                continue
            elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
                'FROM', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL'
            ):
                from_seen = True
                just_closed_paren = False
            elif from_seen and token.ttype in (sqlparse.tokens.Name, None):
                value = token.value.strip()
                # 유효한 테이블명인 경우만 추가
                if self._is_valid_table_identifier(value):
                    table_names.add(value.lower())
                    from_seen = False
                just_closed_paren = False
            elif token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
                'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING'
            ):
                from_seen = False
                just_closed_paren = False
            else:
                just_closed_paren = False

        return list(table_names)

    def _extract_tables_with_regex(self, sql: str) -> List[str]:
        """정규식을 사용한 테이블 추출 (fallback)"""
        # 괄호 내부 제거 (함수, 서브쿼리 제외)
        sql_no_parens = re.sub(r'\([^)]*\)', '', sql)
        # FROM/JOIN 뒤의 식별자 추출
        pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql_no_parens, re.IGNORECASE)
        return [m.lower() for m in matches]

    def _is_valid_table_identifier(self, value: str) -> bool:
        """유효한 테이블 식별자인지 확인"""
        if not value:
            return False
        # 키워드나 특수문자 제외
        invalid_values = {'(', ')', ',', 'ON', 'AS', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'SELECT'}
        if value.upper() in invalid_values or '(' in value:
            return False
        # 식별자 패턴 확인
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value))

    def _add_limit_if_missing(self, sql: str) -> str:
        """LIMIT 절이 없으면 추가 (DB 타입에 따라 다른 문법 사용)"""
        external_db_manager = _get_external_db_manager()
        adapter = external_db_manager.get_adapter()
        return adapter.add_limit_clause(sql, self.max_rows)

    def execute_sql(self, sql: str, validate: bool = True) -> SQLResult:
        """
        SQL 실행
        Args:
            sql: 실행할 SQL 쿼리
            validate: 검증 여부
        Returns:
            SQLResult
        """
        # 1. 검증
        if validate:
            is_valid, error_msg = self.validate_sql(sql)
            if not is_valid:
                logger.error(f"SQL 검증 실패: {error_msg}")
                raise SQLValidationError(error_msg)

        # 2. LIMIT 추가
        sql = self._add_limit_if_missing(sql)

        # 3. 외부 DB에서 SQL 실행
        start_time = time.time()
        external_db_manager = _get_external_db_manager()
        adapter = external_db_manager.get_adapter()

        try:
            with external_db_manager.get_cursor() as cur:
                # 타임아웃 설정 (DB별 어댑터 사용)
                adapter.set_timeout(cur, self.timeout)

                # SQL 실행
                cur.execute(sql)

                # 결과 가져오기 (어댑터 사용)
                columns = adapter.get_column_names(cur)
                rows = cur.fetchall()  
                # rows는 튜플 리스트로 실제 값을 가짐
                # 예시들:
                # SELECT count(*) FROM emp        → [(42,)]          — 1행 1열
                # SELECT name, age FROM emp       → [('김철수', 30), ('이영희', 25)]  — 2행 2열
                # SELECT avg(score) FROM scores   → [(100,)]         — 1행 1열 (현재 케이스)
                
                execution_time_ms = int((time.time() - start_time) * 1000)

                # 결과 변환 (어댑터 사용)
                result_rows = [adapter.row_to_dict(row, columns) for row in rows]

                logger.debug(f"SQL 실행 완료: rows={len(result_rows)}, time={execution_time_ms}ms, sql={sql}")

                return SQLResult(
                    columns=columns,
                    rows=result_rows,
                    row_count=len(result_rows),
                    execution_time_ms=execution_time_ms
                )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"SQL 실행 실패: {e}, sql={sql}")
            # 연결 오류와 쿼리 오류 구분
            error_type = type(e).__name__
            error_str = str(e).lower()
            is_connection_error = (
                error_type in ("OperationalError", "InterfaceError", "ConnectionError", "PoolTimeout")
                or any(kw in error_str for kw in ("dpy-4011", "dpy-6005", "dpy-6000", "listener refused", "ora-12528", "ora-12541"))
            )
            if is_connection_error:
                raise SQLConnectionError(f"데이터베이스 연결 오류: {str(e)}")
            raise SQLExecutionError(f"SQL 실행 오류: {str(e)}")


# 싱글톤 인스턴스
sql_executor = SQLExecutorService()
