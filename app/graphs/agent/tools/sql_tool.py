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
        return """Query the HR database using natural language.

Use this tool when you need to:
- Employee info: name, department, position, grade, hire/retire date, work status, employment type
- Employee statistics: headcount, hires, resignations by department/year
- Salary: gross pay, net pay, fixed/variable pay, deductions
- Performance reviews: grade (S/A/B/C/D), score, feedback
- Address/residence: region, city, regional distribution
- Education: school, major, graduation year
- Language scores: TOEIC, TOEFL, JLPT scores and grades
- Certifications: license name, issuing org, validity
- Career history: previous company, work months/years
- Family info: relations, dependents
- Military service: branch, rank, service status
- Rewards/penalties: type, reason, amount
- Training: course name, institution, completion status, cost
- Leave/vacation: accrued, used, additional, carried-over days

DO NOT use this tool for:
- Policy questions (use search_documents instead)
- Guidelines or regulations (use search_documents instead)
- Calculations only (use calculate instead)

Args:
    question: Natural language question about HR database

Returns:
    Query results formatted as natural language

Examples:
    - "2024년 입사자 수는?" → Returns hire count for 2024
    - "서울 거주 직원 목록" → Returns employees living in Seoul
    - "부서별 평균 급여는?" → Returns average salary by department
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
            log_step(logger, "SYSTEM", "TOOL", self.name, "CACHE", "캐시 히트", level="DEBUG")
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
            log_step(logger, "SYSTEM", "TOOL", self.name, "START", f"SQL 도구 실행 | question={truncate_text(question, 50)}")

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
            log_step(logger, "SYSTEM", "TOOL", self.name, "ERROR", f"SQL 도구 실행 실패: {e}", level="ERROR")
            return ToolResult(
                success=False,
                error=f"Database query failed: {str(e)}",
                metadata={"original_question": question}
            )

    def _execute_enhanced(self, question: str) -> ToolResult:
        """
        Enhanced 모드: NL2SQL 노드 패턴 사용 (validate + retry 포함)

        흐름:
        1. Schema Retrieval (1회만)
        2~6. retry 루프 (max_retries까지):
            2. Few-shot Retrieval (retry 시 enhanced=True)
            3. Prompt Build (retry 시 이전 오류 컨텍스트 주입)
            4. SQL Generate
            5. Validate SQL
            6. Execute SQL
        """
        from app.graphs.nl2sql.nodes import (
            schema_retrieval_node,
            fewshot_retrieval_node,
            prompt_build_node,
            sql_generate_node,
            validate_sql_node,
            prepare_retry_node,
            _is_retryable_error,
        )

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

        log_step(logger, "SYSTEM", "TOOL", self.name, "SCHEMA", "Schema Retrieval 시작")

        # 1. Schema Retrieval (1회만 - 스키마는 변하지 않음)
        state.update(schema_retrieval_node(state))
        log_step(logger, "SYSTEM", "TOOL", self.name, "SCHEMA", "테이블 선택 완료", tables=state.get('selected_tables', []))

        # 설정에서 max_retries 로드
        settings_config = _get_settings_config()
        max_retries = settings_config.get_value("nl2sql", "max_retries", 2)

        last_error = "SQL 생성 실패"

        # retry 루프: fewshot → prompt → generate → validate → execute
        for attempt in range(max_retries + 1):
            # 2. Few-shot Retrieval (retry 시 enhanced=True로 2배 검색)
            state.update(fewshot_retrieval_node(state))
            if attempt == 0:
                log_step(logger, "SYSTEM", "TOOL", self.name, "FEWSHOT", "Few-shot 검색 완료", count=state.get('fewshot_count', 0))

            # 3. Prompt Build (retry 시 이전 오류 컨텍스트 자동 포함)
            state.update(prompt_build_node(state))

            # 4. SQL Generate
            state.update(sql_generate_node(state))

            sql = state.get("generated_sql", "")
            if not sql:
                last_error = state.get("validation_error", "SQL 생성 실패")
                if attempt < max_retries:
                    state["validation_error"] = last_error
                    state.update(prepare_retry_node(state))
                    log_step(logger, "SYSTEM", "TOOL", self.name, "RETRY", f"SQL 생성 실패 → 재시도 #{attempt + 1}")
                    continue
                return ToolResult(success=False, error=last_error, metadata={"original_question": question, "selected_tables": state.get("selected_tables", []), "fewshot_count": state.get("fewshot_count", 0)})

            log_step(logger, "SYSTEM", "TOOL", self.name, "SQL", f"SQL 생성 완료 | length={len(sql)}" + (f" | attempt={attempt + 1}" if attempt > 0 else ""))

            # 5. Validate SQL (NL2SQL과 동일한 검증)
            state.update(validate_sql_node(state))

            if not state.get("validated", False):
                validation_error = state.get("validation_error", "")
                last_error = validation_error
                if attempt < max_retries and _is_retryable_error(validation_error):
                    state.update(prepare_retry_node(state))
                    log_step(logger, "SYSTEM", "TOOL", self.name, "RETRY", f"검증 실패 → 재시도 #{attempt + 1} | error={truncate_text(validation_error, 80)}")
                    continue
                return ToolResult(success=False, error=validation_error, metadata={"original_question": question, "generated_sql": sql, "selected_tables": state.get("selected_tables", [])})

            # 6. Execute SQL (validate=False: 이미 validate_sql_node에서 검증 완료)
            try:
                result = sql_executor.execute_sql(sql, validate=False)
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                if attempt < max_retries and _is_retryable_error(error_str):
                    state["validation_error"] = error_str
                    state.update(prepare_retry_node(state))
                    log_step(logger, "SYSTEM", "TOOL", self.name, "RETRY", f"실행 실패 → 재시도 #{attempt + 1} | error={truncate_text(error_str, 80)}")
                    continue
                return ToolResult(success=False, error=f"SQL 실행 오류: {error_str}", metadata={"original_question": question, "generated_sql": sql, "selected_tables": state.get("selected_tables", [])})

            # 7. PII 마스킹 (NL2SQL pii_filter_node와 동일한 보호)
            from app.core.pii.pii_service import pii_service
            if pii_service.enabled and result.rows:
                result.rows, pii_count = pii_service.mask_sql_rows(result.rows)
                if pii_count > 0:
                    log_step(logger, "SYSTEM", "TOOL", self.name, "PII", f"PII 마스킹 완료 | detected={pii_count}, rows={len(result.rows)}")

            # 8. 결과 포맷팅
            if result.row_count == 0:
                formatted_result = "조회 결과가 없습니다."
            elif result.row_count == 1:
                formatted_result = self._format_single_result(result)
            else:
                formatted_result = self._format_multiple_results(result)

            log_step(logger, "SYSTEM", "TOOL", self.name, "COMPLETE", "SQL 도구 완료", rows=result.row_count, time_ms=result.execution_time_ms, retries=attempt)

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
                    "retry_count": attempt,
                    "sql_result": {
                        "sql": sql,
                        "columns": result.columns,
                        "rows": result.rows[:100],
                        "row_count": result.row_count,
                        "execution_time_ms": result.execution_time_ms
                    }
                }
            )

        # 모든 재시도 실패
        return ToolResult(success=False, error=f"최대 재시도 횟수({max_retries}) 초과: {last_error}", metadata={"original_question": question, "selected_tables": state.get("selected_tables", [])})

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

        # 2.5. PII 마스킹 (NL2SQL pii_filter_node와 동일한 보호)
        from app.core.pii.pii_service import pii_service
        if pii_service.enabled and result.rows:
            result.rows, pii_count = pii_service.mask_sql_rows(result.rows)
            if pii_count > 0:
                log_step(logger, "SYSTEM", "TOOL", self.name, "PII", f"PII 마스킹 완료 | detected={pii_count}, rows={len(result.rows)}")

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
    자연어로 회사 인사 데이터베이스를 조회합니다.

    이 도구를 사용하는 경우:
    - 직원 기본정보: 이름, 부서, 직위, 직급, 입사일, 퇴사일, 재직상태, 고용형태, 성별, 채용유형
    - 직원 수/통계: 입사자 수, 퇴사자 수, 부서별 인원, 재직자 수
    - 급여 정보: 지급합계, 실지급액, 고정비, 변동비, 공제합계
    - 인사평가: 평가등급(S/A/B/C/D), 평가점수, 평가의견
    - 주소/거주지: 거주 시/도, 지역별 직원 분포
    - 학력 정보: 학교명, 전공, 졸업연도
    - 어학 성적: TOEIC, TOEFL, JLPT 등 시험종류, 점수, 등급
    - 자격증 정보: 자격증명, 발급기관, 취득일, 유효상태
    - 경력 정보: 전 직장명, 근무 개월수/연수
    - 가족 정보: 가족관계, 부양가족 수
    - 병역 정보: 군종류, 최종계급, 군필여부
    - 상벌 정보: 포상/징계 구분, 포상금액
    - 교육/훈련 이력: 과정명, 교육기관, 수료여부, 교육비용
    - 연차 정보: 발생연차, 사용연차, 추가연차, 이월연차

    이 도구를 사용하지 않는 경우:
    - 회사 정책이나 규정 (search_documents_tool 사용)
    - 이미 조회한 데이터의 계산 (calculate_tool 사용)

    Args:
        question: 인사 데이터베이스에 대한 자연어 질문

    Returns:
        데이터베이스 테이블에서 조회한 포맷된 결과 (JSON 형태로 sql_result 포함)

    예시:
        - "2024년에 입사한 직원은 몇 명?" → 입사자 수 반환
        - "개발팀에 몇 명 있어?" → 부서별 직원 수 반환
        - "서울 거주 직원 목록" → 지역별 직원 조회
        - "TOEIC 900점 이상 직원은?" → 어학 성적 조회
        - "정보처리기사 보유자" → 자격증 정보 조회
        - "평가등급 S등급 직원" → 인사평가 데이터 조회
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
