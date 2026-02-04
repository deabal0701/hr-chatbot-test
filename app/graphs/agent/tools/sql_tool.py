"""
SQL 쿼리 도구 (Enhanced with NL2SQL Pattern)

기능:
- 자연어 → SQL 변환 (NL2SQL 노드 패턴 통합)
- Schema Retrieval: 필요한 테이블만 선택
- Few-shot Retrieval: 유사 쿼리 예제 검색
- SQL 검증 및 실행
- 결과 포맷팅

확장성:
- 캐싱: 동일 질문 재사용
- 보안: SQL Injection 방지, 테이블 접근 제어
- 성능: 쿼리 최적화 힌트
"""

import json
from typing import Dict, Any
from langchain_core.tools import tool

from app.graphs.agent.tools.base import BaseTool, ToolResult
from app.core.database.sql_executor import sql_executor
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    """settings_config 지연 로드"""
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


class SQLQueryTool(BaseTool):
    """SQL 쿼리 실행 도구 (Enhanced with NL2SQL Pattern)

    NL2SQL 노드 패턴을 통합하여 더 정확한 SQL 생성:
    - Schema Retrieval: LLM으로 필요한 테이블 선택
    - Few-shot Retrieval: 유사 쿼리 예제 검색
    - Prompt Build: 컨텍스트 기반 프롬프트 구성
    """

    def __init__(self):
        super().__init__()
        self._query_cache: Dict[str, Any] = {}

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
        """전처리: 캐싱 체크"""
        question = kwargs.get("question", "")

        cache_key = question.lower().strip()
        if cache_key in self._query_cache:
            log_step("SYSTEM", "TOOL", self.name, "CACHE", "캐시 히트", level="DEBUG")
            kwargs["_cached_result"] = self._query_cache[cache_key]

        return kwargs

    def after_execute(self, result: ToolResult) -> ToolResult:
        """후처리: 캐싱 저장"""
        if result.success and result.data:
            question = result.metadata.get("original_question", "")
            cache_key = question.lower().strip()
            self._query_cache[cache_key] = result.data

            if len(self._query_cache) > 100:
                oldest_key = next(iter(self._query_cache))
                del self._query_cache[oldest_key]

        return result

    def _execute(self, question: str, _cached_result: Any = None, **kwargs) -> ToolResult:
        """
        실제 실행 로직 (NL2SQL 노드 패턴 통합)

        흐름:
        1. Schema Retrieval (필요한 테이블 선택)
        2. Few-shot Retrieval (유사 예제 검색)
        3. Prompt Build (컨텍스트 기반 프롬프트)
        4. SQL Generate (LLM 호출)
        5. Validate & Execute
        """

        if _cached_result is not None:
            return ToolResult(
                success=True,
                data=_cached_result,
                metadata={"original_question": question, "cached": True}
            )

        try:
            log_step("SYSTEM", "TOOL", self.name, "START", f"SQL 도구 실행 | question={truncate_text(question, 50)}")

            # NL2SQL 노드 패턴 활용 여부 확인
            settings_config = _get_settings_config()
            use_enhanced = settings_config.get_value("nl2sql", "schema_retrieval_enabled", True)

            if use_enhanced:
                # Enhanced 모드: NL2SQL 노드 패턴 사용
                return self._execute_enhanced(question)
            else:
                # Legacy 모드: 기존 sql_generator 사용
                return self._execute_legacy(question)

        except Exception as e:
            log_step("SYSTEM", "TOOL", self.name, "ERROR", f"SQL 도구 실행 실패: {e}", level="ERROR")
            return ToolResult(
                success=False,
                error=f"Database query failed: {str(e)}",
                metadata={"original_question": question}
            )

    def _execute_enhanced(self, question: str) -> ToolResult:
        """
        Enhanced 모드: NL2SQL 노드 패턴 사용

        1. Schema Retrieval
        2. Few-shot Retrieval
        3. Prompt Build
        4. SQL Generate
        5. Execute
        """
        from app.graphs.nl2sql.nodes import (
            schema_retrieval_node,
            fewshot_retrieval_node,
            prompt_build_node,
            sql_generate_node,
        )
        from app.utils.common import strip_markdown_code_block

        # 상태 초기화
        state = {
            "question": question,
            "request_id": "tool",
            "schema_description": "",
            "selected_tables": [],
            "schema_retrieval_confidence": 0.0,
            "fewshot_context": "",
            "fewshot_examples": [],
            "fewshot_count": 0,
            "sql_prompt": "",
            "user_prompt": "",
            "prompt_metadata": {},
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "metadata": {},
            "retry_count": 0,
            "enhanced_fewshot": False,
            "previous_sql": "",
            "previous_error": "",
        }

        log_step("SYSTEM", "TOOL", self.name, "SCHEMA", "Schema Retrieval 시작")

        # 1. Schema Retrieval
        state.update(schema_retrieval_node(state))
        log_step("SYSTEM", "TOOL", self.name, "SCHEMA", "테이블 선택 완료", tables=state.get('selected_tables', []))

        # 2. Few-shot Retrieval
        state.update(fewshot_retrieval_node(state))
        log_step("SYSTEM", "TOOL", self.name, "FEWSHOT", "Few-shot 검색 완료", count=state.get('fewshot_count', 0))

        # 3. Prompt Build
        state.update(prompt_build_node(state))

        # 4. SQL Generate
        state.update(sql_generate_node(state))

        sql = state.get("generated_sql", "")
        if not sql:
            error_msg = state.get("validation_error", "SQL 생성 실패")
            return ToolResult(
                success=False,
                error=error_msg,
                metadata={
                    "original_question": question,
                    "selected_tables": state.get("selected_tables", []),
                    "fewshot_count": state.get("fewshot_count", 0),
                }
            )

        log_step("SYSTEM", "TOOL", self.name, "SQL", f"SQL 생성 완료 | length={len(sql)}")

        # 5. SQL 실행
        try:
            result = sql_executor.execute_sql(sql, validate=True)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"SQL 실행 오류: {str(e)}",
                metadata={
                    "original_question": question,
                    "generated_sql": sql,
                    "selected_tables": state.get("selected_tables", []),
                }
            )

        # 6. 결과 포맷팅
        if result.row_count == 0:
            formatted_result = "조회 결과가 없습니다."
        elif result.row_count == 1:
            formatted_result = self._format_single_result(result)
        else:
            formatted_result = self._format_multiple_results(result)

        log_step("SYSTEM", "TOOL", self.name, "COMPLETE", "SQL 도구 완료", rows=result.row_count, time_ms=result.execution_time_ms)

        return ToolResult(
            success=True,
            data=formatted_result,
            metadata={
                "original_question": question,
                "generated_sql": sql,
                "row_count": result.row_count,
                "execution_time_ms": result.execution_time_ms,
                "cached": False,
                "selected_tables": state.get("selected_tables", []),
                "fewshot_count": state.get("fewshot_count", 0),
                "sql_result": {
                    "sql": sql,
                    "columns": result.columns,
                    "rows": result.rows[:100],
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms
                }
            }
        )

    def _execute_legacy(self, question: str) -> ToolResult:
        """Legacy 모드: 기존 sql_generator 사용"""
        from app.core.llm.sql_generator import sql_generator

        # 1. SQL 생성
        sql, gen_metadata = sql_generator.generate_sql(question)

        if not sql:
            error_msg = gen_metadata.get("error", "Failed to generate SQL")
            return ToolResult(
                success=False,
                error=error_msg,
                metadata={"original_question": question, **gen_metadata}
            )

        # 2. SQL 실행
        result = sql_executor.execute_sql(sql, validate=True)

        # 3. 결과 포맷팅
        if result.row_count == 0:
            formatted_result = "조회 결과가 없습니다."
        elif result.row_count == 1:
            formatted_result = self._format_single_result(result)
        else:
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
                "sql_result": {
                    "sql": sql,
                    "columns": result.columns,
                    "rows": result.rows[:100],
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms
                }
            }
        )

    def _format_single_result(self, result) -> str:
        """단일 결과 포맷팅"""
        row = result.rows[0]

        if len(result.columns) == 1:
            value = list(row.values())[0]
            return f"{value}"

        parts = []
        for col, val in row.items():
            parts.append(f"{col}: {val}")
        return ", ".join(parts)

    def _format_multiple_results(self, result) -> str:
        """다중 결과 포맷팅"""
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
        question: 데이터베이스 테이블에 대한 자연어 질문

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
        sql_result = result.metadata.get("sql_result") if result.metadata else None
        response = {
            "answer": str(result.data),
            "sql_result": sql_result
        }
        return json.dumps(response, ensure_ascii=False, default=str)
    else:
        return json.dumps({"answer": f"Error: {result.error}", "sql_result": None}, ensure_ascii=False)
