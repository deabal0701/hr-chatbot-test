"""
Agent Node (ReAct 패턴)

LLM을 호출하여 Think/Action을 결정하는 핵심 노드입니다.
Tool 호출이 필요하면 tool_calls를 포함한 AIMessage를 반환하고,
최종 답변이 준비되면 content에 답변을 포함합니다.
"""

from typing import Any, Dict, List, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.llm.llm_config import LLMConfigManager
from app.core.config.settings_config import settings_config
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


# Tool 함수들 import
from app.graphs.agent.tools.sql_tool import query_database_tool
from app.graphs.agent.tools.rag_tool import search_documents_tool
from app.graphs.agent.tools.calc_tool import calculate_tool


def _get_tools() -> List:
    """사용 가능한 Tool 목록 반환"""
    return [
        query_database_tool,
        search_documents_tool,
        calculate_tool,
    ]


def _get_system_prompt() -> str:
    """
    Agent System Prompt 반환 (DB에서 로드)

    DB의 tb_app_settings 테이블에서 'prompt' 카테고리의
    'agent_system_prompt' 키로 저장된 프롬프트를 사용합니다.
    """
    from app.core.llm.prompt_service import prompt_service
    return prompt_service.get_agent_system_prompt()


def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 노드 (ReAct Think/Action)

    LLM을 호출하여 다음 행동을 결정합니다:
    - Tool 호출이 필요하면 tool_calls 포함한 AIMessage 반환
    - 최종 답변이 준비되면 content에 답변 포함

    Args:
        state: AgentState

    Returns:
        업데이트된 state (messages, iteration_count)
    """
    request_id = state.get("request_id", "unknown")
    messages = state.get("messages", [])
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)

    log_step(logger, request_id, "AGENT", str(iteration_count), "THINK",
             f"Agent 노드 실행 | iteration={iteration_count}/{max_iterations}")

    # 반복 횟수 체크
    if iteration_count >= max_iterations:
        log_step(logger, request_id, "AGENT", str(iteration_count), "WARN",
                 "최대 반복 횟수 도달", level="WARNING")
        return {
            "messages": [AIMessage(content="죄송합니다. 질문에 대한 답변을 찾는 데 너무 오래 걸리고 있습니다. 질문을 더 구체적으로 해주시겠어요?")],
            "iteration_count": iteration_count + 1,
            "final_answer": "최대 반복 횟수 초과",
        }

    # LLM 인스턴스 생성 (Tool binding 포함)
    temperature = settings_config.get_value("agent", "llm_temperature", 0.0)
    llm = LLMConfigManager.create_llm(temperature=temperature)

    # Tool binding
    tools = _get_tools()
    llm_with_tools = llm.bind_tools(tools)

    # System prompt 추가 (첫 번째 메시지가 아닌 경우)
    system_prompt = _get_system_prompt()

    # 메시지 구성
    prompt_messages = [SystemMessage(content=system_prompt)] + list(messages)

    log_step(logger, request_id, "AGENT", str(iteration_count), "LLM-INPUT",
             f"LLM 호출 | messages={len(prompt_messages)}")

    try:
        # LLM 호출
        response = llm_with_tools.invoke(prompt_messages)

        # Tool 호출 여부 확인
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls

        if has_tool_calls:
            tool_names = [tc.get('name', 'unknown') for tc in response.tool_calls]
            log_step(logger, request_id, "AGENT", str(iteration_count), "ACTION",
                     f"Tool 호출 결정 | tools={tool_names}")
        else:
            answer_preview = truncate_text(response.content, 100) if response.content else "(empty)"
            log_step(logger, request_id, "AGENT", str(iteration_count), "ANSWER",
                     f"최종 답변 생성 | preview={answer_preview}")

        return {
            "messages": [response],
            "iteration_count": iteration_count + 1,
        }

    except Exception as e:
        log_step(logger, request_id, "AGENT", str(iteration_count), "ERROR",
                 f"LLM 호출 실패: {e}", level="ERROR")
        return {
            "messages": [AIMessage(content=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}")],
            "iteration_count": iteration_count + 1,
            "final_answer": f"오류: {str(e)}",
        }


def should_continue(state: Dict[str, Any]) -> Literal["tools", "answer"]:
    """
    조건부 분기 함수

    마지막 메시지를 확인하여:
    - tool_calls가 있으면 "tools" → tools_node로 이동
    - 없으면 "answer" → answer_node로 이동 (최종 답변 생성)

    Args:
        state: AgentState

    Returns:
        "tools" 또는 "answer"
    """
    request_id = state.get("request_id", "unknown")
    messages = state.get("messages", [])

    if not messages:
        log_step(logger, request_id, "AGENT", "X", "BRANCH", "메시지 없음 → ANSWER")
        return "answer"

    last_message = messages[-1]

    # AIMessage이고 tool_calls가 있는지 확인
    if isinstance(last_message, AIMessage):
        has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls

        if has_tool_calls:
            log_step(logger, request_id, "AGENT", "X", "BRANCH", "Tool 호출 있음 → TOOLS")
            return "tools"

    log_step(logger, request_id, "AGENT", "X", "BRANCH", "Tool 호출 없음 → ANSWER")
    return "answer"
