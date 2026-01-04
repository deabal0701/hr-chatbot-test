from typing import Any, Dict, List

from app.utils.database import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchemaLoaderService:
    """데이터베이스 스키마 메타데이터 로더"""

    # 테스트용: LLM에 전달할 테이블 제한 (None이면 전체 테이블 사용)
    # 최소한의 스키마만 LLM에 전달하여 토큰 사용량 및 처리 시간 감소
    # 프로덕션에서는 None으로 설정하거나 필요한 테이블만 지정
    ALLOWED_TABLES = ['employee', 'department']

    def __init__(self):
        self._schema_cache: Dict[str, Any] = {}

    def load_schema_metadata(self, refresh: bool = False) -> Dict[str, Any]:
        """
        스키마 메타데이터 로드
        Args:
            refresh: 캐시 무시하고 새로 로드
        Returns:
            스키마 정보 딕셔너리
        """
        if not refresh and self._schema_cache:
            return self._schema_cache

        schema = {
            "database": "hr_chatbot",
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
        logger.info(f"스키마 메타데이터 로드 완료: {len(tables)}개 테이블")
        return schema

    def _get_tables(self) -> List[str]:
        """public 스키마의 테이블 목록 조회 (ALLOWED_TABLES로 필터링)"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            all_tables = [row['table_name'] for row in cur.fetchall()]
            
            # ALLOWED_TABLES가 설정되어 있으면 필터링
            if self.ALLOWED_TABLES:
                filtered_tables = [t for t in all_tables if t in self.ALLOWED_TABLES]
                logger.info(f"테이블 필터링: {len(all_tables)}개 → {len(filtered_tables)}개 (허용: {self.ALLOWED_TABLES})")
                return filtered_tables
            
            return all_tables

    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """테이블의 컬럼 정보 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))

            columns = []
            for row in cur.fetchall():
                col = {
                    "name": row['column_name'],
                    "type": row['data_type'],
                    "nullable": row['is_nullable'] == 'YES',
                    "default": row['column_default']
                }
                if row['character_maximum_length']:
                    col['max_length'] = row['character_maximum_length']
                columns.append(col)

            return columns

    def _get_primary_key(self, table_name: str) -> List[str]:
        """테이블의 기본 키 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                  AND i.indisprimary
            """, (table_name,))

            return [row['attname'] for row in cur.fetchall()]

    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """테이블의 외래 키 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = %s
            """, (table_name,))

            fks = []
            for row in cur.fetchall():
                fks.append({
                    "column": row['column_name'],
                    "references_table": row['foreign_table_name'],
                    "references_column": row['foreign_column_name']
                })
            return fks

    def _get_indexes(self, table_name: str) -> List[str]:
        """테이블의 인덱스 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = %s
            """, (table_name,))

            return [row['indexname'] for row in cur.fetchall()]

    def _get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """테이블의 샘플 데이터 조회"""
        try:
            with db_manager.get_cursor() as cur:
                # 민감한 정보는 마스킹
                if table_name == 'salary':
                    cur.execute(f"""
                        SELECT id, emp_id, effective_date, '***' as base_salary, currency
                        FROM {table_name}
                        LIMIT %s
                    """, (limit,))
                else:
                    cur.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))

                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"샘플 데이터 조회 실패 ({table_name}): {e}")
            return []

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블의 스키마 정보만 조회"""
        full_schema = self.load_schema_metadata()
        for table in full_schema['tables']:
            if table['name'] == table_name:
                return table
        return {}

    def generate_schema_description(self) -> str:
        """
        LLM용 스키마 설명 생성 (자연어 형태)
        NL2SQL에서 프롬프트에 포함할 텍스트
        """
        schema = self.load_schema_metadata()

        description = "# 데이터베이스 스키마\n\n"

        for table in schema['tables']:
            description += f"## 테이블: {table['name']}\n"

            # 컬럼 정보
            description += "컬럼:\n"
            for col in table['columns']:
                nullable = "NULL 가능" if col['nullable'] else "NOT NULL"
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
