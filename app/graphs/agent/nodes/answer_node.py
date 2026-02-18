"""
Answer Node (최종 답변 생성)

Tool 실행 결과를 종합하여 사용자 친화적인 최종 답변을 생성합니다.
NL2SQL의 응답 프롬프트(get_nl2sql_answer_prompt)를 사용하여 일관된 답변 품질을 보장합니다.

프롬프트 공유:
- NL2SQL: generate_answer_node → get_nl2sql_answer_prompt()
- Agent: answer_node → get_nl2sql_answer_prompt() (동일 프롬프트 사용)
"""

import json
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.core.llm.llm_config import LLMConfigManager
from app.core.llm.prompt_service import prompt_service
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text, extract_llm_text_content

logger = setup_logger(__name__)


def answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 답변 생성 노드

    Tool 실행 결과를 종합하여 사용자 친화적인 최종 답변을 생성합니다.
    NL2SQL의 응답 프롬프트를 사용하여 일관된 답변 품질을 보장합니다.

    Args:
        state: AgentState

    Returns:
        업데이트된 state (messages, final_answer)
    """
    request_id = state.get("request_id", "unknown")
    question = state.get("question", "")
    messages = state.get("messages", [])

    log_step(logger, request_id, "AGENT", "ANSWER", "START", "최종 답변 생성 시작")

    # Tool 결과 수집
    tool_results = _extract_tool_results(messages)

    if not tool_results:
        log_step(logger, request_id, "AGENT", "ANSWER", "WARN", "Tool 결과 없음 - 기존 답변 유지", level="WARNING")
        # Tool 결과가 없으면 마지막 AIMessage 내용을 그대로 사용
        return _use_last_ai_message(state, messages)

    # NL2SQL의 응답 프롬프트 사용 (프롬프트 공유)
    system_prompt = prompt_service.get_nl2sql_answer_prompt()

    # User Prompt 구성
    user_prompt = f"""## 사용자 질문
{question}

## 도구 실행 결과
{tool_results}

위 정보를 바탕으로 사용자 질문에 대한 최종 답변을 작성하세요."""

    log_step(logger, request_id, "AGENT", "ANSWER", "LLM-INPUT", "LLM 호출", system_len=len(system_prompt), user_len=len(user_prompt))

    try:
        # LLM 호출 (temperature=0.1로 약간의 창의성 허용)
        llm = LLMConfigManager.create_llm(temperature=0.1)

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        answer = extract_llm_text_content(response.content)

        log_step(logger, request_id, "AGENT", "ANSWER", "COMPLETE", "최종 답변 생성 완료", length=len(answer))

        return {
            "messages": [AIMessage(content=answer)],
            "final_answer": answer,
        }

    except Exception as e:
        log_step(logger, request_id, "AGENT", "ANSWER", "ERROR", "답변 생성 실패", level="ERROR", error=str(e))
        # 오류 시 Tool 결과를 그대로 반환
        fallback_answer = f"수집된 정보:\n{tool_results}"
        return {
            "messages": [AIMessage(content=fallback_answer)],
            "final_answer": fallback_answer,
        }


def _extract_tool_results(messages) -> str:
    """
    메시지에서 Tool 결과 추출

    SQL Tool의 경우 JSON을 파싱하여 sql_result의 실제 데이터를 추출합니다.

    Args:
        messages: 대화 메시지 리스트

    Returns:
        포맷된 Tool 결과 문자열
    """
    results = []

    for msg in messages:
        if isinstance(msg, ToolMessage):
            tool_name = getattr(msg, 'name', 'unknown')
            content = msg.content

            # Tool 이름을 한글로 변환
            tool_name_kr = _get_tool_name_kr(tool_name)

            content = extract_llm_text_content(content)

            # SQL Tool 결과는 JSON 파싱하여 실제 데이터 추출
            if tool_name == "query_database_tool" and isinstance(content, str):
                formatted_content = _format_sql_tool_result(content)
            else:
                formatted_content = str(content) if content else ""

            results.append(f"### {tool_name_kr}\n{formatted_content}")

    return "\n\n".join(results) if results else ""


def _format_sql_tool_result(content: str) -> str:
    """
    SQL Tool 결과를 LLM이 이해하기 쉬운 형식으로 변환

    Args:
        content: SQL Tool의 JSON 응답 문자열

    Returns:
        포맷된 SQL 결과 문자열
    """
    try:
        data = json.loads(content)
        sql_result = data.get("sql_result")

        if not sql_result:
            # sql_result가 없으면 answer 필드 사용
            return data.get("answer", content)

        # SQL 결과 포맷팅
        sql = sql_result.get("sql", "")
        columns = sql_result.get("columns", [])
        rows = sql_result.get("rows", [])
        row_count = sql_result.get("row_count", 0)

        # NL2SQL generate_answer_node와 유사한 형식으로 구성
        lines = []
        lines.append(f"실행된 SQL:\n{sql}")
        lines.append(f"\n조회 결과 ({row_count}개 행):")
        lines.append(f"컬럼: {', '.join(columns)}")

        # 데이터 포맷팅 (최대 100개)
        display_rows = rows[:100]
        lines.append(f"데이터:")
        for row in display_rows:
            lines.append(str(row))

        if row_count > 100:
            lines.append(f"(나머지 {row_count - 100}개 행 생략)")

        return "\n".join(lines)

    except (json.JSONDecodeError, TypeError, KeyError):
        # JSON 파싱 실패 시 원본 반환
        return content


def _get_tool_name_kr(tool_name: str) -> str:
    """Tool 이름을 한글로 변환"""
    name_map = {
        "query_database_tool": "데이터베이스 조회 결과",
        "search_documents_tool": "문서 검색 결과",
        "calculate_tool": "계산 결과",
    }
    return name_map.get(tool_name, tool_name)


def _use_last_ai_message(state: Dict[str, Any], messages) -> Dict[str, Any]:
    """
    Tool 결과가 없는 경우 마지막 AIMessage 사용

    Args:
        state: AgentState
        messages: 대화 메시지 리스트

    Returns:
        업데이트된 state
    """
    # 역순으로 AIMessage 찾기
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls
            if not has_tool_calls:
                return {
                    "final_answer": extract_llm_text_content(msg.content),
                }

    return {
        "final_answer": "답변을 생성하지 못했습니다.",
    }
