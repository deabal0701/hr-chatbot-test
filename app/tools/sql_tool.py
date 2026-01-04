"""
SQL 쿼리 도구

기능:
- 자연어 → SQL 변환
- SQL 검증 및 실행
- 결과 포맷팅

확장성:
- 캐싱: 동일 질문 재사용
- 보안: SQL Injection 방지, 테이블 접근 제어
- 성능: 쿼리 최적화 힌트
"""

from typing import Dict, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.tools.base import BaseTool, ToolResult
from app.services.sql_executor import sql_executor
from app.services.schema_loader import schema_loader
from app.services.settings_service import settings_service
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SQLQueryTool(BaseTool):
    """SQL 쿼리 실행 도구"""

    def __init__(self):
        super().__init__()
        self._schema_cache = None
        self._query_cache: Dict[str, Any] = {}  # 간단한 캐싱 (확장: Redis)

    @property
    def name(self) -> str:
        return "query_database"

    @property
    def description(self) -> str:
        return """Query the HR database using natural language.

Use this tool when you need to:
- Get employee counts, statistics, aggregations (e.g., "How many employees in 2024?")
- Find specific employee information (e.g., "List developers in Seoul")
- Analyze hiring/resignation trends (e.g., "Monthly hiring trend for 2024")
- Get department-wise data (e.g., "Average salary by department")
- Query structured data from tables: employee, department, salary, etc.

DO NOT use this tool for:
- Policy questions (use search_documents instead)
- Guidelines or regulations (use search_documents instead)
- Calculations only (use calculate instead)

Args:
    question: Natural language question about HR database

Returns:
    Query results formatted as natural language

Examples:
    - "2024년 입사자는 몇 명인가?" → Returns employee count
    - "개발팀 직원 목록을 보여줘" → Returns list of developers
    - "부서별 평균 급여는?" → Returns salary statistics by department
"""

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about HR database"
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
            logger.info(f"[{self.name}] Cache hit: {cache_key[:50]}")
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
            # 1. 스키마 로드 (캐싱)
            if self._schema_cache is None:
                self._schema_cache = schema_loader.generate_schema_description()
                logger.info(f"[{self.name}] Schema loaded and cached")

            # 2. SQL 생성 (LLM)
            sql = self._generate_sql(question, self._schema_cache)

            if not sql:
                return ToolResult(
                    success=False,
                    error="Failed to generate SQL from question",
                    metadata={"original_question": question}
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
                    "cached": False
                }
            )

        except Exception as e:
            logger.error(f"[{self.name}] SQL tool execution failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Database query failed: {str(e)}",
                metadata={"original_question": question}
            )

    def _generate_sql(self, question: str, schema_description: str) -> str:
        """
        자연어 → SQL 변환 (기존 nl2sql_graph 로직 재사용)

        확장 포인트:
        - Few-shot learning (예제 추가)
        - Chain-of-Thought prompting
        """
        llm_settings = {
            "api_key": settings_service.get_value("openai", "api_key", settings.openai_api_key),
            "model": settings_service.get_value("llm", "model", settings.llm_model),
        }

        llm = ChatOpenAI(
            model=llm_settings["model"],
            temperature=0,
            api_key=llm_settings["api_key"]
        )

        system_prompt = f"""당신은 PostgreSQL 전문가입니다.
사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요.

# 데이터베이스 스키마
{schema_description}

# 중요한 규칙
1. **반드시 SELECT 문만 생성하세요** (INSERT, UPDATE, DELETE, DROP 등은 절대 사용 금지)
2. **테이블명과 컬럼명은 정확하게 사용하세요**
3. **WHERE 절을 적절히 사용하여 결과를 필터링하세요**
4. **집계 함수 사용 시 GROUP BY를 정확히 지정하세요**
5. **날짜 비교 시 적절한 형변환을 사용하세요**
6. **JOIN 시 명확한 조인 조건을 지정하세요**
7. **SQL만 출력하고, 설명이나 마크다운 코드 블록은 포함하지 마세요**

# 사용자 의도 파악 규칙
- "표로 보여줘", "목록으로", "리스트로", "상세 정보" 등의 표현이 있으면 **개별 데이터를 조회**하세요 (COUNT 사용 금지)
- "몇 명", "총 수", "개수" 등의 표현이 있을 때만 COUNT를 사용하세요

# LIMIT 사용 규칙
- **COUNT, SUM, AVG, MAX, MIN 등 집계 함수 사용 시**: LIMIT 절 사용 금지
- **GROUP BY 사용 시**: LIMIT 절 사용 금지
- **개별 데이터 조회 시**: LIMIT 1000 사용

# 한국어 필드 매핑
- "입사일" = hire_date
- "직급" = position
- "직무" = job_family
- "부서" = department
- "근무지" = work_location
- "재직상태" = status
"""

        user_prompt = f"""질문: {question}

위 질문에 대한 PostgreSQL SELECT 쿼리를 생성해주세요.
SQL만 출력하세요 (설명 없이)."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = llm.invoke(messages)
        sql = response.content.strip()

        # 마크다운 코드 블록 제거
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
            sql = sql.replace("```sql", "").replace("```", "").strip()

        logger.info(f"[{self.name}] Generated SQL: {sql[:100]}")
        return sql

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


# LangChain tool 래퍼 (함수 형태)
@tool
def query_database(question: str) -> str:
    """
    Query the HR database using natural language.

    Use this for structured data queries about employees, departments, salaries, etc.

    Args:
        question: Natural language question about HR database

    Returns:
        Query results as formatted text
    """
    tool_instance = SQLQueryTool()
    result = tool_instance.execute(question=question)

    if result.success:
        return str(result.data)
    else:
        return f"Error: {result.error}"
