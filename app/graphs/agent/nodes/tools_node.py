"""
Tools Node (ReAct 패턴)

AIMessage의 tool_calls를 실행하고 결과를 ToolMessage로 반환합니다.
"""

import json
from typing import Any, Dict

from langchain_core.messages import AIMessage, ToolMessage

from app.graphs.agent.tools.sql_tool import query_database_tool
from app.graphs.agent.tools.rag_tool import search_documents_tool
from app.graphs.agent.tools.calc_tool import calculate_tool
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


# Tool 이름 → 함수 매핑
TOOL_MAP = {
    "query_database_tool": query_database_tool,
    "search_documents_tool": search_documents_tool,
    "calculate_tool": calculate_tool,
}


def tools_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tools 노드 (Tool 실행)

    마지막 AIMessage의 tool_calls를 실행하고
    결과를 ToolMessage로 반환합니다.

    Args:
        state: AgentState

    Returns:
        업데이트된 state (messages, tools_used, last_tool_name, last_tool_result 등)
    """
    request_id = state.get("request_id", "unknown")
    messages = state.get("messages", [])
    tools_used = list(state.get("tools_used", []))

    if not messages:
        log_step(logger, request_id, "TOOLS", "X", "ERROR", "메시지 없음", level="ERROR")
        return {"messages": []}

    last_message = messages[-1]

    # AIMessage가 아니거나 tool_calls가 없으면 패스
    if not isinstance(last_message, AIMessage):
        log_step(logger, request_id, "TOOLS", "X", "WARN", "마지막 메시지가 AIMessage가 아님", level="WARNING")
        return {"messages": []}

    tool_calls = getattr(last_message, 'tool_calls', None)
    if not tool_calls:
        log_step(logger, request_id, "TOOLS", "X", "WARN", "tool_calls 없음", level="WARNING")
        return {"messages": []}

    log_step(logger, request_id, "TOOLS", "X", "EXECUTE", f"Tool 실행 시작 | count={len(tool_calls)}")

    # Tool 실행 결과 저장
    tool_messages = []
    last_tool_name = ""
    last_tool_result = ""
    generated_sql = state.get("generated_sql", "")
    sql_result = state.get("sql_result")
    rag_sources = list(state.get("rag_sources", []))

    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_id = tool_call.get("id", "")
        tool_args = tool_call.get("args", {})

        log_step(logger, request_id, "TOOLS", tool_name, "CALL", "Tool 호출", args=truncate_text(str(tool_args), 100))

        try:
            # Tool 함수 조회
            tool_func = TOOL_MAP.get(tool_name)

            if tool_func is None:
                error_msg = f"Unknown tool: {tool_name}"
                log_step(logger, request_id, "TOOLS", tool_name, "ERROR", error_msg, level="ERROR")
                tool_messages.append(ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name,
                ))
                continue

            # Tool 실행
            result = tool_func.invoke(tool_args)

            # 결과 처리
            last_tool_name = tool_name
            last_tool_result = str(result)

            # Tool 사용 기록
            if tool_name not in tools_used:
                tools_used.append(tool_name)

            # SQL Tool 결과 처리 (프론트엔드 표시용)
            if tool_name == "query_database_tool":
                try:
                    result_json = json.loads(result)
                    sql_result_data = result_json.get("sql_result")
                    if sql_result_data:
                        generated_sql = sql_result_data.get("sql", "")
                        # SQLResult 객체로 변환은 생략 (Dict로 저장)
                        sql_result = sql_result_data
                except (json.JSONDecodeError, TypeError):
                    pass

            # RAG Tool 결과 처리
            if tool_name == "search_documents_tool":
                # 문서 검색 결과 저장 (간단히 텍스트로)
                rag_sources.append({
                    "query": tool_args.get("question", ""),
                    "result": truncate_text(result, 500),
                })

            log_step(logger, request_id, "TOOLS", tool_name, "RESULT", "Tool 결과", length=len(str(result)))

            tool_messages.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_id,
                name=tool_name,
            ))

        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            log_step(logger, request_id, "TOOLS", tool_name, "ERROR", error_msg, level="ERROR")
            tool_messages.append(ToolMessage(
                content=error_msg,
                tool_call_id=tool_id,
                name=tool_name,
            ))

    log_step(logger, request_id, "TOOLS", "X", "COMPLETE", "Tool 실행 완료", executed=len(tool_messages))

    return {
        "messages": tool_messages,
        "tools_used": tools_used,
        "last_tool_name": last_tool_name,
        "last_tool_result": last_tool_result,
        "generated_sql": generated_sql,
        "sql_result": sql_result,
        "rag_sources": rag_sources,
    }
