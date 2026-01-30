"""
NL2SQL 노드 (NL2SQL Nodes)

기능:
- SQL 생성 (generate_sql_node)
- SQL 검증 (validate_sql_node)
- SQL 실행 (execute_sql_node)
- 답변 생성 (generate_answer_node)
- 에러 처리 (handle_error_node)
- 분기 판단 (should_execute)

사용:
- NL2SQLGraph 클래스의 노드로 사용
- generate_sql → validate_sql → should_execute 분기 → execute_sql → generate_answer 순서로 실행
"""
from typing import Dict, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.core.llm.llm_config import LLMConfigManager
from app.core.llm.prompt_service import prompt_service
from app.core.llm.sql_generator import sql_generator
from app.core.database.sql_executor import SQLExecutionError, SQLValidationError, sql_executor
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


def _get_llm():
    """
    매 요청 시 DB 설정을 반영한 LLM 인스턴스 생성

    NL2SQL은 temperature=0으로 고정하여 deterministic한 SQL 생성
    """
    return LLMConfigManager.create_llm(temperature=0)


def generate_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 생성 노드

    사용자 질문을 SQL 쿼리로 변환합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (generated_sql, schema_description, metadata 필드 채움)
    """
    question = state["question"]
    request_id = state.get("request_id", "unknown")

    log_step(request_id, "NL2SQL", "1", "GENERATE", "SQL 생성 시작", question=truncate_text(question, 40))

    try:
        sql, gen_metadata = sql_generator.generate_sql(question, request_id)

        if sql:
            state["generated_sql"] = sql
            state["schema_description"] = sql_generator.get_schema_description()
            state["metadata"] = {
                "llm_model": gen_metadata.get("llm_model"),
                "db_type": gen_metadata.get("db_type"),
                "sql_dialect": gen_metadata.get("sql_dialect")
            }
            log_step(request_id, "NL2SQL", "1b", "LLM-OUTPUT", "SQL 생성 완료", sql_length=len(sql))
            log_step(request_id, "NL2SQL", "1b", "SQL", "생성된 SQL", level="DEBUG", content=sql)
        else:
            error_msg = gen_metadata.get("error", "SQL 생성 실패")
            state["generated_sql"] = ""
            state["validation_error"] = f"SQL 생성 오류: {error_msg}"
            state["validated"] = False
            log_step(request_id, "NL2SQL", "1", "ERROR", f"SQL 생성 실패: {error_msg}", level="ERROR")

    except Exception as e:
        log_step(request_id, "NL2SQL", "1", "ERROR", f"SQL 생성 실패: {e}", level="ERROR")
        state["generated_sql"] = ""
        state["validation_error"] = f"SQL 생성 오류: {str(e)}"
        state["validated"] = False

    return state


def validate_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 검증 노드

    생성된 SQL의 안전성과 유효성을 검증합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (validated, validation_error 필드 채움)
    """
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")

    if not sql:
        log_step(request_id, "NL2SQL", "2", "VALIDATE", "검증 실패 - SQL 없음")
        state["validated"] = False
        state["validation_error"] = "생성된 SQL이 없습니다"
        return state

    log_step(request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 시작")

    try:
        is_valid, error_msg = sql_executor.validate_sql(sql)

        if is_valid:
            state["validated"] = True
            state["validation_error"] = ""
            log_step(request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 성공")
        else:
            state["validated"] = False
            state["validation_error"] = error_msg
            log_step(request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 실패", error=error_msg)

    except Exception as e:
        state["validated"] = False
        state["validation_error"] = str(e)
        log_step(request_id, "NL2SQL", "2", "ERROR", f"SQL 검증 중 오류: {e}", level="ERROR")

    return state


def should_execute(state: Dict[str, Any]) -> str:
    """
    조건부 분기 함수

    SQL 검증 성공 여부에 따라 다음 노드를 결정합니다.

    Args:
        state: NL2SQLState

    Returns:
        "execute" (검증 성공) 또는 "error" (검증 실패)
    """
    request_id = state.get("request_id", "unknown")
    decision = "execute" if state["validated"] else "error"
    log_step(request_id, "NL2SQL", "2x", "BRANCH", f"분기 결정 → {decision.upper()}")
    return decision


def execute_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 실행 노드

    검증된 SQL을 데이터베이스에서 실행합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (sql_result, metadata 필드 채움)
    """
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")

    log_step(request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 시작")

    try:
        result = sql_executor.execute_sql(sql, validate=False)
        state["sql_result"] = result
        state["metadata"]["execution_time_ms"] = result.execution_time_ms
        state["metadata"]["row_count"] = result.row_count

        log_step(request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 완료", row_count=result.row_count, execution_time_ms=result.execution_time_ms)

    except (SQLExecutionError, SQLValidationError) as e:
        log_step(request_id, "NL2SQL", "3", "ERROR", f"SQL 실행 실패: {e}", level="ERROR")
        state["validation_error"] = str(e)
        state["validated"] = False

    return state


def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    답변 생성 노드

    SQL 실행 결과를 기반으로 자연어 답변을 생성합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (answer 필드 채움)
    """
    question = state["question"]
    sql = state["generated_sql"]
    result = state.get("sql_result")
    request_id = state.get("request_id", "unknown")

    if not result or result.row_count == 0:
        log_step(request_id, "NL2SQL", "4", "ANSWER", "결과 없음 - 기본 응답 반환")
        state["answer"] = "조회된 결과가 없습니다."
        return state

    log_step(request_id, "NL2SQL", "4", "ANSWER", "답변 생성 시작", row_count=result.row_count)

    system_prompt = prompt_service.get_nl2sql_answer_prompt()

    max_rows = 100
    rows_summary = result.rows[:max_rows] if len(result.rows) > max_rows else result.rows
    is_truncated = len(result.rows) > max_rows

    numeric_totals: dict[str, float] = {}
    for col in result.columns:
        try:
            total = 0.0
            has_numeric = False
            for row in result.rows:
                val = row.get(col)
                if val is not None and isinstance(val, (int, float)):
                    total += float(val)
                    has_numeric = True
            if has_numeric:
                numeric_totals[col] = total
        except (TypeError, ValueError):
            pass

    totals_info = ""
    if numeric_totals:
        totals_str = ", ".join([f"{k}={v}" for k, v in numeric_totals.items()])
        totals_info = f"\n\n숫자 컬럼 총합 (전체 {result.row_count}개 행 기준): {totals_str}"

    truncation_note = f"\n(※ 전체 {result.row_count}개 행 중 {max_rows}개만 표시)" if is_truncated else ""

    user_prompt = f"""질문: {question}

실행된 SQL:
{sql}

조회 결과 ({result.row_count}개 행):{truncation_note}
컬럼: {', '.join(result.columns)}
실제 데이터 :
{rows_summary}{totals_info}

위 결과를 바탕으로 질문에 대한 답변을 자연어/표/리스트등 사용자가 원하는 형태로 작성하라."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm = _get_llm()

    log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", "LLM 호출 시작 (답변 생성)",
            system_prompt_length=len(system_prompt),
            user_prompt_length=len(user_prompt),
            data_rows=len(rows_summary))

    if logger.isEnabledFor(logging.DEBUG):
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", "SYSTEM_PROMPT", level="DEBUG", content=system_prompt)
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", "USER_PROMPT", level="DEBUG", content=user_prompt)
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", "DATA_ROWS", level="DEBUG", content=str(rows_summary))

    try:
        response = llm.invoke(messages)

        if logger.isEnabledFor(logging.DEBUG):
            log_step(request_id, "NL2SQL", "4b", "LLM-OUTPUT", "LLM 응답", level="DEBUG", content=response.content)

        answer = response.content

        state["answer"] = answer
        log_step(request_id, "NL2SQL", "4b", "LLM-OUTPUT", "답변 생성 완료", answer_length=len(answer))

        if logger.isEnabledFor(logging.DEBUG):
            log_step(request_id, "NL2SQL", "4b", "ANSWER", "생성된 답변", level="DEBUG", content=answer)

    except Exception as e:
        log_step(request_id, "NL2SQL", "4", "ERROR", f"답변 생성 실패: {e}", level="ERROR")
        state["answer"] = f"조회 결과: {result.row_count}개 행이 발견되었습니다."

    return state


def handle_error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    에러 처리 노드

    SQL 생성/검증/실행 실패 시 사용자에게 안내 메시지를 생성합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (answer 필드 채움)
    """
    error_msg = state.get("validation_error", "알 수 없는 오류")
    request_id = state.get("request_id", "unknown")

    state["answer"] = f"""SQL 생성 또는 실행 중 오류가 발생했습니다.

오류 내용: {error_msg}

다음 사항을 확인해주세요:
1. 질문이 데이터베이스 스키마에 맞는지 확인
2. 테이블명과 컬럼명이 정확한지 확인
3. 질문을 더 구체적으로 작성
"""

    log_step(request_id, "NL2SQL", "ERR", "ERROR", "오류 처리 완료", error=error_msg)
    return state
