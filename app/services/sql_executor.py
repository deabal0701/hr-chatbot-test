import re
import time
from typing import Any, Dict, List, Optional, Tuple

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import DML, DDL, Keyword

from app.config import settings
from app.models.schemas import SQLResult
from app.services.settings_service import settings_service
from app.utils.database import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SQLExecutionError(Exception):
    """SQL 실행 오류"""
    pass


class SQLValidationError(Exception):
    """SQL 검증 오류"""
    pass


class SQLExecutorService:
    """SQL 실행 서비스 (NL2SQL용)"""

    # 허용된 테이블 목록 (스키마 로더와 일치)
    # 테스트 환경: employee, department만 허용
    # 프로덕션: 모든 테이블 추가 또는 None으로 설정하여 제한 해제
    ALLOWED_TABLES = {
        'employee', 'department'
        # 'job_history', 'salary', 'performance_review', 
        # 'attendance', 'leave_request', 'hr_docs'
    }

    # 허용되지 않는 키워드 (DDL/DML)
    FORBIDDEN_KEYWORDS = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'DECLARE', 'CURSOR'
    }

    def __init__(self):
        # 기본값 저장 (환경변수)
        self._default_timeout = settings.sql_timeout_seconds
        self._default_max_rows = settings.sql_max_rows
        self._default_read_only = settings.read_only_mode

    @property
    def timeout(self) -> int:
        """현재 타임아웃 설정 (DB 설정 우선)"""
        return settings_service.get_value("nl2sql", "timeout_seconds", self._default_timeout)

    @property
    def max_rows(self) -> int:
        """현재 최대 행 수 설정 (DB 설정 우선)"""
        return settings_service.get_value("nl2sql", "max_rows", self._default_max_rows)

    @property
    def read_only(self) -> bool:
        """현재 읽기 전용 모드 설정 (DB 설정 우선)"""
        return settings_service.get_value("nl2sql", "read_only_mode", self._default_read_only)

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
                return False, f"허용되지 않은 키워드: {keyword}"

        # 2. SQL 파싱
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "SQL 파싱 실패"

            stmt: Statement = parsed[0]

            # 3. SELECT 문만 허용 (읽기 전용)
            if self.read_only:
                first_token = stmt.get_type()
                if first_token != 'SELECT':
                    return False, f"SELECT 문만 허용됩니다 (현재: {first_token})"

        except Exception as e:
            return False, f"SQL 파싱 오류: {str(e)}"

        # 4. 테이블 이름 검증
        table_names = self._extract_table_names(sql)
        for table in table_names:
            if table.lower() not in self.ALLOWED_TABLES:
                return False, f"허용되지 않은 테이블: {table}"

        # 5. LIMIT 절 체크 (권장)
        if 'LIMIT' not in sql_upper:
            logger.warning(f"LIMIT 절이 없는 쿼리: {sql[:100]}")
            # 경고만 하고 통과 (자동으로 LIMIT 추가 가능)

        return True, None

    def _extract_table_names(self, sql: str) -> List[str]:
        """
        SQL에서 테이블 이름 추출
        
        sqlparse를 사용하여 정확하게 추출
        """
        table_names = set()
        
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return []
            
            stmt = parsed[0]
            
            # Token을 순회하며 FROM/JOIN 절의 테이블만 추출
            from_seen = False
            join_seen = False
            parenthesis_depth = 0  # 괄호 깊이 추적
            
            for token in stmt.flatten():
                # 괄호 깊이 추적 (함수 내부 FROM 무시용)
                if token.value == '(':
                    parenthesis_depth += 1
                    continue
                elif token.value == ')':
                    parenthesis_depth -= 1
                    continue
                
                # 괄호 안(함수 내부)에서는 FROM을 테이블 구문으로 간주하지 않음
                if parenthesis_depth > 0:
                    continue
                
                # FROM 또는 JOIN 키워드 감지 (괄호 밖에서만)
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ('FROM', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'):
                    from_seen = True
                    join_seen = True
                    continue
                
                # FROM/JOIN 다음의 식별자(테이블명) 추출
                if (from_seen or join_seen) and token.ttype in (sqlparse.tokens.Name, None):
                    value = token.value.strip()
                    # 괄호나 쉼표가 아닌 경우만 (서브쿼리 제외)
                    if value and value not in ('(', ')', ',', 'ON', 'AS') and not value.upper() in ('WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'SELECT'):
                        # 괄호가 포함되지 않은 경우만 (함수 호출 제외)
                        if '(' not in value:
                            table_names.add(value.lower())
                            from_seen = False
                            join_seen = False
                
                # WHERE, GROUP BY 등을 만나면 리셋
                if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ('WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING'):
                    from_seen = False
                    join_seen = False
            
            return list(table_names)
            
        except Exception as e:
            logger.warning(f"테이블 추출 실패, 간단한 정규식 사용: {e}")
            # Fallback: 간단한 정규식 (함수 내부 제외)
            # FROM/JOIN 뒤의 단어를 추출하되, 괄호 안은 제외
            sql_no_parens = re.sub(r'\([^)]*\)', '', sql)  # 괄호 내부 제거
            pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            matches = re.findall(pattern, sql_no_parens, re.IGNORECASE)
            return [m.lower() for m in matches]

    def _add_limit_if_missing(self, sql: str) -> str:
        """LIMIT 절이 없으면 추가"""
        sql_upper = sql.upper()
        if 'LIMIT' not in sql_upper:
            sql = sql.rstrip(';').strip() + f' LIMIT {self.max_rows}'
        return sql

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

        # 3. SQL 실행
        start_time = time.time()

        try:
            with db_manager.get_cursor() as cur:
                # 타임아웃 설정
                cur.execute(f"SET statement_timeout = {self.timeout * 1000}")

                # SQL 실행
                cur.execute(sql)

                # 결과 가져오기
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []

                execution_time_ms = int((time.time() - start_time) * 1000)

                # 결과 변환
                result_rows = [dict(row) for row in rows]

                logger.info(
                    f"SQL 실행 완료: rows={len(result_rows)}, "
                    f"time={execution_time_ms}ms, sql={sql[:100]}"
                )

                return SQLResult(
                    columns=columns,
                    rows=result_rows,
                    row_count=len(result_rows),
                    execution_time_ms=execution_time_ms
                )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"SQL 실행 실패: {e}, sql={sql}")
            raise SQLExecutionError(f"SQL 실행 오류: {str(e)}")

    def explain_sql(self, sql: str) -> Dict[str, Any]:
        """SQL EXPLAIN 분석"""
        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"EXPLAIN (FORMAT JSON) {sql}")
                result = cur.fetchone()
                return result[0] if result else {}
        except Exception as e:
            logger.error(f"EXPLAIN 실패: {e}")
            return {"error": str(e)}

    def get_query_cost(self, sql: str) -> Optional[float]:
        """쿼리 비용 추정"""
        explain_result = self.explain_sql(sql)
        if 'error' in explain_result:
            return None

        try:
            plan = explain_result[0]['Plan']
            return plan.get('Total Cost')
        except (KeyError, IndexError):
            return None


# 싱글톤 인스턴스
sql_executor = SQLExecutorService()
