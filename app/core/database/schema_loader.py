"""스키마 메타데이터 로더

위치: app/core/database/schema_loader.py
- 비즈니스 DB 스키마 조회
- 테이블/컬럼/키/인덱스 정보
- LLM용 스키마 설명 생성
- 다중 DB 지원 (어댑터 패턴)
"""
from typing import Any, Dict, List

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_external_db_manager = None


def _get_external_db_manager():
    global _external_db_manager
    if _external_db_manager is None:
        from app.core.database.external import external_db_manager
        _external_db_manager = external_db_manager
    return _external_db_manager


class SchemaLoaderService:
    """비즈니스 데이터베이스 스키마 메타데이터 로더 (NL2SQL용)"""

    def __init__(self):
        self._schema_cache: Dict[str, Any] = {}

    def load_schema_metadata(self, refresh: bool = False) -> Dict[str, Any]:
        """
        비즈니스 DB 스키마 메타데이터 로드
        Args:
            refresh: 캐시 무시하고 새로 로드
        Returns:
            스키마 정보 딕셔너리
        """
        if not refresh and self._schema_cache:
            return self._schema_cache

        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        db_type = external_db_manager.get_db_type()

        schema = {
            "database": "business_data",
            "schema": schema_name,
            "db_type": db_type,
            "tables": []
        }

        # 테이블 목록 가져오기
        tables = self._get_tables()

        for table_name in tables:
            table_info = {
                "name": table_name,
                "columns": self._get_columns(table_name),
                "primary_key": self._get_primary_key(table_name),
                "foreign_keys": self._get_foreign_keys(table_name),
                "indexes": self._get_indexes(table_name),
                "sample_data": self._get_sample_data(table_name, limit=3)
            }
            schema["tables"].append(table_info)

        self._schema_cache = schema
        logger.info(f"스키마 메타데이터 로드 완료: {schema_name}.* {len(tables)}개 테이블 (DB: {db_type})")
        return schema

    def _get_tables(self) -> List[str]:
        """비즈니스 스키마의 테이블 목록 조회 (allowed_tables 설정으로 필터링)"""
        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        allowed_tables = external_db_manager.get_allowed_tables()
        adapter = external_db_manager.get_adapter()

        with external_db_manager.get_cursor() as cur:
            query, params = adapter.get_tables_query(schema_name)
            cur.execute(query, params)

            # 결과 처리 (어댑터별 row 형식 차이 처리)
            columns = adapter.get_column_names(cur)
            all_tables = []
            for row in cur.fetchall():
                row_dict = adapter.row_to_dict(row, columns)
                table_name = row_dict.get('table_name', '').lower()
                if table_name:
                    all_tables.append(table_name)

            # allowed_tables 설정으로 필터링 (보안)
            if allowed_tables:
                filtered_tables = [t for t in all_tables if t in allowed_tables]
                logger.info(f"테이블 필터링: {len(all_tables)}개 → {len(filtered_tables)}개 (허용: {allowed_tables})")
                return filtered_tables

            return all_tables

    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """테이블의 컬럼 정보 조회"""
        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        adapter = external_db_manager.get_adapter()

        with external_db_manager.get_cursor() as cur:
            query, params = adapter.get_columns_query(schema_name, table_name)
            cur.execute(query, params)

            columns_meta = adapter.get_column_names(cur)
            columns = []
            for row in cur.fetchall():
                row_dict = adapter.row_to_dict(row, columns_meta)
                col = {
                    "name": row_dict.get('column_name', ''),
                    "type": row_dict.get('data_type', ''),
                    "nullable": str(row_dict.get('is_nullable', 'YES')).upper() in ('YES', 'Y'),
                    "default": row_dict.get('column_default')
                }
                max_length = row_dict.get('character_maximum_length')
                if max_length:
                    col['max_length'] = max_length
                # 컬럼 코멘트 (Oracle: ALL_COL_COMMENTS, PostgreSQL: pg_description)
                comment = row_dict.get('column_comment')
                if comment:
                    col['comment'] = comment
                columns.append(col)

            return columns

    def _get_primary_key(self, table_name: str) -> List[str]:
        """테이블의 기본 키 조회"""
        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        adapter = external_db_manager.get_adapter()

        try:
            with external_db_manager.get_cursor() as cur:
                query, params = adapter.get_primary_key_query(schema_name, table_name)
                cur.execute(query, params)

                columns_meta = adapter.get_column_names(cur)
                pk_columns = []
                for row in cur.fetchall():
                    row_dict = adapter.row_to_dict(row, columns_meta)
                    # PostgreSQL: attname, Oracle: column_name
                    col_name = row_dict.get('attname') or row_dict.get('column_name', '')
                    if col_name:
                        pk_columns.append(col_name)
                return pk_columns
        except Exception as e:
            logger.warning(f"기본 키 조회 실패 ({table_name}): {e}")
            return []

    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """테이블의 외래 키 조회"""
        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        adapter = external_db_manager.get_adapter()

        try:
            with external_db_manager.get_cursor() as cur:
                query, params = adapter.get_foreign_keys_query(schema_name, table_name)
                cur.execute(query, params)

                columns_meta = adapter.get_column_names(cur)
                fks = []
                for row in cur.fetchall():
                    row_dict = adapter.row_to_dict(row, columns_meta)
                    fks.append({
                        "column": row_dict.get('column_name', ''),
                        "references_table": row_dict.get('foreign_table_name', ''),
                        "references_column": row_dict.get('foreign_column_name', '')
                    })
                return fks
        except Exception as e:
            logger.warning(f"외래 키 조회 실패 ({table_name}): {e}")
            return []

    def _get_indexes(self, table_name: str) -> List[str]:
        """테이블의 인덱스 조회"""
        external_db_manager = _get_external_db_manager()
        schema_name = external_db_manager.get_schema_name()
        adapter = external_db_manager.get_adapter()

        try:
            with external_db_manager.get_cursor() as cur:
                query, params = adapter.get_indexes_query(schema_name, table_name)
                cur.execute(query, params)

                columns_meta = adapter.get_column_names(cur)
                indexes = []
                for row in cur.fetchall():
                    row_dict = adapter.row_to_dict(row, columns_meta)
                    # PostgreSQL: indexname, Oracle: index_name
                    idx_name = row_dict.get('indexname') or row_dict.get('index_name', '')
                    if idx_name:
                        indexes.append(idx_name)
                return indexes
        except Exception as e:
            logger.warning(f"인덱스 조회 실패 ({table_name}): {e}")
            return []

    def _get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """테이블의 샘플 데이터 조회"""
        external_db_manager = _get_external_db_manager()
        adapter = external_db_manager.get_adapter()

        try:
            with external_db_manager.get_cursor() as cur:
                # 민감한 정보는 마스킹
                if table_name.lower() == 'salary':
                    # 민감 컬럼 마스킹 쿼리 직접 생성
                    query = adapter.get_sample_query(table_name, limit)
                    # salary 테이블은 base_salary를 마스킹하여 별도 쿼리
                    query = query.replace('*', "id, emp_id, effective_date, '***' as base_salary, currency")
                else:
                    query = adapter.get_sample_query(table_name, limit)

                cur.execute(query)

                columns_meta = adapter.get_column_names(cur)
                result = []
                for row in cur.fetchall():
                    result.append(adapter.row_to_dict(row, columns_meta))
                return result
        except Exception as e:
            logger.warning(f"샘플 데이터 조회 실패 ({table_name}): {e}")
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블의 스키마 정보만 조회"""
        full_schema = self.load_schema_metadata()
        for table in full_schema['tables']:
            if table['name'].lower() == table_name.lower():
                return table
        return {}

    def generate_schema_description(self) -> str:
        """
        LLM용 스키마 설명 생성 (자연어 형태)
        NL2SQL에서 프롬프트에 포함할 텍스트
        """
        schema = self.load_schema_metadata()
        db_type = schema.get('db_type', 'postgresql')

        description = f"# 데이터베이스 스키마 ({db_type.upper()})\n\n"

        for table in schema['tables']:
            description += f"## 테이블: {table['name']}\n"

            # 컬럼 정보
            description += "컬럼:\n"
            for col in table['columns']:
                nullable = "NULL 가능" if col['nullable'] else "NOT NULL"
                comment = col.get('comment', '')
                if comment:
                    description += f"  - {col['name']}: {col['type']} ({nullable}) - {comment}\n"
                else:
                    description += f"  - {col['name']}: {col['type']} ({nullable})\n"

            # 기본 키
            if table['primary_key']:
                description += f"기본 키: {', '.join(table['primary_key'])}\n"

            # 외래 키
            if table['foreign_keys']:
                description += "외래 키:\n"
                for fk in table['foreign_keys']:
                    description += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"

            # 샘플 데이터
            if table['sample_data']:
                description += "샘플 데이터 (예시):\n"
                for i, row in enumerate(table['sample_data'][:2], 1):
                    description += f"  {i}. {row}\n"

            description += "\n"

        return description


# 싱글톤 인스턴스
schema_loader = SchemaLoaderService()
