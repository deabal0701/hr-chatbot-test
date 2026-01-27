"""
SQL 쿼리 도구

기능:
- 자연어 → SQL 변환 (sql_generator 공통 모듈 사용)
- SQL 검증 및 실행
- 결과 포맷팅

확장성:
- 캐싱: 동일 질문 재사용
- 보안: SQL Injection 방지, 테이블 접근 제어
- 성능: 쿼리 최적화 힌트
"""

from typing import Dict, Any
from langchain_core.tools import tool

from app.tools.base import BaseTool, ToolResult
from app.core.database.sql_executor import sql_executor
from app.core.llm.sql_generator import sql_generator  # 공통 SQL 생성 모듈
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SQLQueryTool(BaseTool):
    """SQL 쿼리 실행 도구

    sql_generator 공통 모듈을 사용하여 SQL 생성
    - DB 타입 자동 감지 (PostgreSQL, Oracle)
    - Admin UI 프롬프트 설정 반영
    """

    def __init__(self):
        super().__init__()
        self._query_cache: Dict[str, Any] = {}  # 간단한 캐싱 (확장: Redis)

    @property
    def name(self) -> str:
        return "query_database"

    @property
    def description(self) -> str:
        return """Query the database using natural language.

Use this tool when you need to:
- Get counts, statistics, aggregations from structured tables
- Find specific record information (e.g., "List records by criteria")
- Analyze trends and patterns
- Get category-wise or group-wise data
- Query structured data from various database tables

DO NOT use this tool for:
- Policy questions (use search_documents instead)
- Guidelines or regulations (use search_documents instead)
- Calculations only (use calculate instead)

Args:
    question: Natural language question about the database

Returns:
    Query results formatted as natural language

Examples:
    - "2024년 총 매출은?" → Returns total sales
    - "서울 지역 고객 목록" → Returns list of customers in Seoul
    - "카테고리별 평균 가격은?" → Returns price statistics by category
"""

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about the database"
                }
            },
            "required": ["question"]
        }

    def before_execute(self, **kwargs) -> Dict[str, Any]:
        """
        전처리: 캐싱 체크

        확장 포인트:
        - Redis 캐싱
        - 유사 질문 검색 (임베딩 기반)
        """
        question = kwargs.get("question", "")

        # 캐시 체크 (간단한 구현)
        cache_key = question.lower().strip()
        if cache_key in self._query_cache:
            logger.debug(f"[{self.name}] Cache hit: {cache_key[:50]}")
            kwargs["_cached_result"] = self._query_cache[cache_key]

        return kwargs

    def after_execute(self, result: ToolResult) -> ToolResult:
        """
        후처리: 캐싱 저장

        확장 포인트:
        - 결과 마스킹 (민감 정보)
        - 알림 발송 (특정 조건)
        """
        # 성공한 결과만 캐싱
        if result.success and result.data:
            question = result.metadata.get("original_question", "")
            cache_key = question.lower().strip()
            self._query_cache[cache_key] = result.data

            # 캐시 크기 제한 (최근 100개)
            if len(self._query_cache) > 100:
                # 가장 오래된 항목 제거
                oldest_key = next(iter(self._query_cache))
                del self._query_cache[oldest_key]

        return result

    def _execute(self, question: str, _cached_result: Any = None, **kwargs) -> ToolResult:
        """실제 실행 로직"""

        # 캐시된 결과 반환
        if _cached_result is not None:
            return ToolResult(
                success=True,
                data=_cached_result,
                metadata={
                    "original_question": question,
                    "cached": True
                }
            )

        try:
            # 1. SQL 생성 (sql_generator 공통 모듈 사용)
            sql, gen_metadata = sql_generator.generate_sql(question)

            if not sql:
                error_msg = gen_metadata.get("error", "Failed to generate SQL from question")
                return ToolResult(
                    success=False,
                    error=error_msg,
                    metadata={"original_question": question, **gen_metadata}
                )

            # 3. SQL 실행 (보안 검증 포함)
            result = sql_executor.execute_sql(sql, validate=True)

            # 4. 결과 포맷팅
            if result.row_count == 0:
                formatted_result = "조회 결과가 없습니다."
            elif result.row_count == 1:
                # 단일 결과
                formatted_result = self._format_single_result(result)
            else:
                # 다중 결과
                formatted_result = self._format_multiple_results(result)

            return ToolResult(
                success=True,
                data=formatted_result,
                metadata={
                    "original_question": question,
                    "generated_sql": sql,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                    "cached": False,
                    "db_type": gen_metadata.get("db_type"),
                    "llm_model": gen_metadata.get("llm_model"),
                    # 구조화된 SQL 결과 (프론트엔드 테이블 표시용)
                    "sql_result": {
                        "sql": sql,
                        "columns": result.columns,
                        "rows": result.rows[:100],  # 최대 100개 행
                        "row_count": result.row_count,
                        "execution_time_ms": result.execution_time_ms
                    }
                }
            )

        except Exception as e:
            logger.error(f"[{self.name}] SQL tool execution failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Database query failed: {str(e)}",
                metadata={"original_question": question}
            )

    def _format_single_result(self, result) -> str:
        """단일 결과 포맷팅"""
        row = result.rows[0]

        # 단일 컬럼 (집계 결과 등)
        if len(result.columns) == 1:
            value = list(row.values())[0]
            return f"{value}"

        # 다중 컬럼
        parts = []
        for col, val in row.items():
            parts.append(f"{col}: {val}")
        return ", ".join(parts)

    def _format_multiple_results(self, result) -> str:
        """다중 결과 포맷팅"""
        # 최대 10개만 표시
        display_rows = result.rows[:10]

        formatted = f"총 {result.row_count}개 결과 발견 (상위 {len(display_rows)}개 표시):\n\n"

        for i, row in enumerate(display_rows, 1):
            row_parts = []
            for col, val in row.items():
                row_parts.append(f"{col}: {val}")
            formatted += f"{i}. {', '.join(row_parts)}\n"

        if result.row_count > 10:
            formatted += f"\n(나머지 {result.row_count - 10}개 결과 생략)"

        return formatted


import json

# LangChain tool 래퍼 (함수 형태)
@tool
def query_database_tool(question: str) -> str:
    """
    자연어로 회사 데이터베이스를 조회합니다.

    이 도구를 사용하는 경우:
    - 직원 수, 통계 (예: "2024년 입사자 수", "서울 근무 직원 몇 명")
    - 직원 정보 (이름, 직급, 부서, 입사일)
    - 급여 정보 및 변경 이력
    - 인사 이력 및 승진 기록
    - 성과 평가 데이터
    - 부서 정보

    이 도구를 사용하지 않는 경우:
    - 회사 정책이나 규정 (search_documents_tool 사용)
    - 이미 조회한 데이터의 계산 (calculate_tool 사용)

    Args:
        question: 데이터베이스 테이블에 대한 자연어 질문 (employee, department, salary, job_history, performance_review)

    Returns:
        데이터베이스 테이블에서 조회한 포맷된 결과 (JSON 형태로 sql_result 포함)

    예시:
        - "2024년에 입사한 직원은 몇 명?" → 2024년 입사자 수 반환
        - "김철수의 현재 급여는?" → 직원의 현재 급여 반환
        - "개발팀에 몇 명 있어?" → 개발팀 직원 수 반환
    """
    tool_instance = SQLQueryTool()
    result = tool_instance.execute(question=question)

    if result.success:
        # SQL 결과를 JSON 형태로 반환 (프론트엔드에서 테이블 표시용)
        sql_result = result.metadata.get("sql_result") if result.metadata else None
        response = {
            "answer": str(result.data),
            "sql_result": sql_result
        }
        return json.dumps(response, ensure_ascii=False, default=str)
    else:
        return json.dumps({"answer": f"Error: {result.error}", "sql_result": None}, ensure_ascii=False)
