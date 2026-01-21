"""데이터베이스 어댑터 추상 클래스

위치: app/core/database/adapters/base.py
- 다중 DB 지원을 위한 추상화 계층
- PostgreSQL, Oracle 등 DB별 구현체의 인터페이스 정의
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple


class DatabaseAdapter(ABC):
    """데이터베이스 어댑터 추상 클래스"""

    @property
    @abstractmethod
    def db_type(self) -> str:
        """DB 타입 반환 (postgresql, oracle, mysql 등)"""
        pass

    @property
    @abstractmethod
    def default_port(self) -> int:
        """기본 포트 반환"""
        pass

    @abstractmethod
    def build_connection_url(self, config: Dict[str, Any]) -> str:
        """연결 URL 생성"""
        pass

    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """연결 테스트 (성공여부, 에러메시지)"""
        pass

    @abstractmethod
    def create_pool(self, url: str, config: Dict[str, Any]) -> Any:
        """연결 풀 생성"""
        pass

    @abstractmethod
    def close_pool(self, pool: Any) -> None:
        """연결 풀 종료"""
        pass

    @abstractmethod
    @contextmanager
    def get_connection(self, pool: Any, schema: str) -> Generator:
        """커넥션 가져오기 (스키마 설정 포함)"""
        pass

    @abstractmethod
    @contextmanager
    def get_cursor(self, connection: Any) -> Generator:
        """커서 가져오기"""
        pass

    # ==========================================================================
    # 스키마 조회 쿼리
    # ==========================================================================

    @abstractmethod
    def get_tables_query(self, schema: str) -> Tuple[str, tuple]:
        """테이블 목록 조회 쿼리와 파라미터 반환"""
        pass

    @abstractmethod
    def get_columns_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """컬럼 정보 조회 쿼리와 파라미터 반환"""
        pass

    @abstractmethod
    def get_primary_key_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """기본 키 조회 쿼리와 파라미터 반환"""
        pass

    @abstractmethod
    def get_foreign_keys_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """외래 키 조회 쿼리와 파라미터 반환"""
        pass

    @abstractmethod
    def get_indexes_query(self, schema: str, table: str) -> Tuple[str, tuple]:
        """인덱스 조회 쿼리와 파라미터 반환"""
        pass

    # ==========================================================================
    # SQL 실행 관련
    # ==========================================================================

    @abstractmethod
    def set_timeout(self, cursor: Any, timeout_seconds: int) -> None:
        """쿼리 타임아웃 설정"""
        pass

    @abstractmethod
    def add_limit_clause(self, sql: str, limit: int) -> str:
        """LIMIT 절 추가 (DB별 문법)"""
        pass

    @abstractmethod
    def get_sample_query(self, table: str, limit: int, columns: Optional[List[str]] = None) -> str:
        """샘플 데이터 조회 쿼리"""
        pass

    @abstractmethod
    def get_explain_query(self, sql: str) -> str:
        """EXPLAIN 쿼리"""
        pass

    @abstractmethod
    def get_sql_dialect_name(self) -> str:
        """LLM 프롬프트용 SQL 방언 이름 (예: PostgreSQL, Oracle)"""
        pass

    # ==========================================================================
    # 결과 변환
    # ==========================================================================

    @abstractmethod
    def row_to_dict(self, row: Any, columns: List[str]) -> Dict[str, Any]:
        """행 데이터를 딕셔너리로 변환"""
        pass

    @abstractmethod
    def get_column_names(self, cursor: Any) -> List[str]:
        """커서에서 컬럼명 추출"""
        pass
