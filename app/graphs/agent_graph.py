"""
AI Agent Graph (ReAct 패턴)

기능:
- 자율적 도구 선택 및 실행
- 반복적 사고 (Thought → Action → Observation)
- 멀티턴 대화 메모리
- 동적 실행 계획

확장성:
- 메모리: 단기/장기 메모리 지원
- 스트리밍: 실시간 응답 (확장)
- 플래닝: 복잡한 작업 분해 (확장)
- 협업: Multi-Agent 협업 (확장)
"""

from typing import Literal, Dict, Any, List, Sequence, Annotated, TypedDict
import logging
import time
import uuid
from datetime import datetime
from langchain_core.messages import (HumanMessage, SystemMessage, AIMessage, BaseMessage, ToolMessage)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from app.models.agent import (AgentRequest, AgentResponse, AgentStep, AgentConfig, AgentSQLResult)
from app.tools.sql_tool import query_database_tool
from app.tools.rag_tool import search_documents_tool
from app.tools.calc_tool import calculate_tool
from app.graphs.nodes.agent_nodes import intent_analysis_node, context_retrieval_node
from app.core.config.settings_config import settings_config
from app.config import settings
from app.utils.logger import setup_logger, log_step  # 통합 로깅 유틸리티
from app.core.llm.llm_config import LLMConfigManager  # 통합 LLM 설정
from app.core.llm.prompt_service import prompt_service  # 프롬프트 서비스
from app.utils.common import truncate_text  # 디버그 모드 인식 텍스트 자르기

logger = setup_logger(__name__)


def _overwrite(_, new):
    """덮어쓰기 reducer - 새 값으로 대체"""
    return new


class AgentState(TypedDict):
    """
    Agent 상태 (LangGraph StateGraph용)

    LangGraph 상태 병합:
    - 각 필드에 reducer를 명시해야 노드 반환값이 상태에 병합됨
    - add_messages: 메시지 리스트에 추가 (누적)
    - _overwrite: 새 값으로 덮어쓰기
    """
    # ===== 기본 필드 =====
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: Annotated[str, _overwrite]
    session_id: Annotated[str, _overwrite]
    config: Annotated[AgentConfig, _overwrite]
    iteration_count: Annotated[int, _overwrite]
    final_answer: Annotated[str, _overwrite]
    request_id: Annotated[str, _overwrite]
    start_time: Annotated[float, _overwrite]

    # ===== 의도 분석 =====
    intent_analysis: Annotated[Dict[str, Any], _overwrite]
    intent_confidence: Annotated[float, _overwrite]
    is_ambiguous: Annotated[bool, _overwrite]
    ambiguity_options: Annotated[List[str], _overwrite]
    extracted_entities: Annotated[Dict[str, Any], _overwrite]

    # ===== 컨텍스트 검색 =====
    relevant_schemas: Annotated[List[Dict[str, Any]], _overwrite]
    similar_queries: Annotated[List[Dict[str, Any]], _overwrite]
    business_terms: Annotated[List[Dict[str, Any]], _overwrite]
    context_prompt: Annotated[str, _overwrite]

    # ===== Human in the Loop =====
    waiting_for_human: Annotated[bool, _overwrite]
    human_intervention: Annotated[Dict[str, Any], _overwrite]
    human_response: Annotated[str, _overwrite]


def create_state_defaults() -> Dict[str, Any]:
    """
    AgentState의 확장 필드 기본값

    의도 분석, 컨텍스트 검색, Human in the Loop 관련 필드의 기본값을 반환합니다.

    사용법:
        initial_state = {
            **create_state_defaults(),
            "messages": [...],
            "question": "...",
            ...
        }
    """
    return {
        # 의도 분석 기본값
        "intent_analysis": {},
        "intent_confidence": 1.0,
        "is_ambiguous": False,
        "ambiguity_options": [],
        "extracted_entities": {},
        # 컨텍스트 검색 기본값
        "relevant_schemas": [],
        "similar_queries": [],
        "business_terms": [],
        "context_prompt": "",
        # Human in the Loop 기본값
        "waiting_for_human": False,
        "human_intervention": {},
        "human_response": "",
    }


class InsightAgentGraph:
    """
    Corporate AI Agent (ReAct Pattern)
    """

    def __init__(self):
        # 도구 등록
        self.tools = self._get_tools()

        # Checkpointer 초기화 (InMemorySaver)
        self.checkpointer = InMemorySaver()

        # 그래프 빌드
        self.graph = self._build_graph()

        log_step("SYSTEM", "AGENT", "INIT", "SETUP", "InsightAgentGraph 초기화 완료", level="DEBUG", tools_count=len(self.tools))

    def _get_tools(self) -> List:
        """
        사용 가능한 도구 목록

        확장 포인트:
        - 동적 도구 로딩 (플러그인)
        - 사용자별 권한 기반 도구 필터링
        - 컨텍스트별 도구 선택

        Note:
        SQL 컨텍스트(스키마, Few-shot, 용어집)는 context_retrieval_node에서
        자동으로 검색되어 Agent System Prompt에 주입됩니다.
        """
        return [
            query_database_tool,      # SQL 실행 (context가 System Prompt에 주입됨)
            search_documents_tool,    # RAG 검색 (usage_type='rag_knowledge')
            calculate_tool,           # 계산기
        ]

    def _get_llm(self, config: AgentConfig):
        """
        LLM 인스턴스 생성

        확장 포인트:
        - 모델 선택 로직
        - 제공자 선택 로직
        - 폴백 모델 (메인 모델 실패 시)
        - 비용 최적화 (간단한 질문은 저렴한 모델)
        """
        provider = getattr(config, 'llm_provider', None) or \
                   settings_config.get_value("agent", "llm_provider", "openai")

        log_step("SYSTEM", "AGENT", "LLM", "CREATE", "LLM 인스턴스 생성", level="DEBUG", model=config.llm_model, provider=provider, temperature=config.llm_temperature)

        # LLMConfigManager를 통해 LLM 생성 (init_chat_model 사용)
        llm = LLMConfigManager.create_llm(
            temperature=config.llm_temperature,
            model=config.llm_model,
            provider=provider
        )

        # 도구 바인딩 (제공자 무관하게 동작)
        return llm.bind_tools(self.tools)

    def _build_graph(self) -> CompiledStateGraph:
        """
        Agent 그래프 구성 (ReAct 패턴 + 의도 분석 + 컨텍스트 주입)

        플로우:
        1. intent_analysis (의도 분석, 선택적 - config.enable_intent_analysis)
        2. context_retrieval (SQL 컨텍스트 검색 - query_type 기반)
        3. agent (LLM 의사결정 - context가 System Prompt에 주입됨)
        4. should_continue (도구 호출 여부 판단)
           - continue → tools (도구 실행) → agent (반복)
           - end → END (종료)

        Context 주입 방식:
        - context_retrieval_node에서 스키마/Few-shot/용어집 검색
        - 결과가 state["context_prompt"]에 저장됨
        - _agent_node에서 System Prompt에 자동 주입
        - Agent는 query_database_tool로 SQL 실행 (컨텍스트는 자동 주입됨)
        """
        workflow = StateGraph(AgentState)

        # 노드 추가
        workflow.add_node("intent_analysis", self._intent_analysis_wrapper)
        workflow.add_node("context_retrieval", self._context_retrieval_wrapper)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # 진입점: intent_analysis
        workflow.set_entry_point("intent_analysis")

        # intent_analysis → context_retrieval → agent
        workflow.add_edge("intent_analysis", "context_retrieval")
        workflow.add_edge("context_retrieval", "agent")

        # 조건부 엣지: LLM이 도구 호출 여부 결정
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )

        # 도구 실행 후 다시 agent로 (루프)
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=self.checkpointer)

    def _intent_analysis_wrapper(self, state: AgentState) -> Dict[str, Any]:
        """
        의도 분석 노드 래퍼

        config.enable_intent_analysis=True일 때만 실제 분석 수행
        False이면 패스스루 (기존 동작 유지)

        Returns:
            업데이트할 필드만 포함된 dict (LangGraph 상태 병합용)
        """
        request_id = state.get("request_id", "unknown")
        config = state.get("config")  # type: ignore

        # enable_intent_analysis 확인
        enable = getattr(config, 'enable_intent_analysis', False) if config else False

        if not enable:
            # 패스스루: 빈 dict 반환 (상태 변경 없음)
            log_step(request_id, "AGENT", "INTENT", "SKIP", "의도 분석 비활성화 (패스스루)", level="DEBUG")
            return {}

        # 의도 분석 실행 (업데이트 dict 반환)
        updates = intent_analysis_node(state)  # type: ignore
        return updates

    def _context_retrieval_wrapper(self, state: AgentState) -> Dict[str, Any]:
        """
        컨텍스트 검색 노드 래퍼

        의도 분석 결과를 기반으로 SQL 컨텍스트(스키마, Few-shot, 용어집)를 검색합니다.
        검색 결과는 state["context_prompt"]에 저장되어 Agent System Prompt에 주입됩니다.

        조건:
        - query_type이 sql_query 또는 hybrid인 경우만 검색
        - 의도 분석이 비활성화된 경우 기본적으로 sql_query로 간주하여 검색

        Returns:
            업데이트할 필드만 포함된 dict (LangGraph 상태 병합용)
        """
        request_id = state.get("request_id", "unknown")
        intent_analysis = state.get("intent_analysis", {})

        # 반환할 업데이트 딕셔너리
        updates: Dict[str, Any] = {}

        # 의도 분석이 비활성화된 경우 (intent_analysis가 비어있음)
        # Agent가 자율적으로 판단하도록 컨텍스트 검색 수행
        if not intent_analysis:
            # 기본적으로 SQL 컨텍스트 검색 수행 (Agent의 도구 선택 지원)
            log_step(request_id, "AGENT", "CONTEXT", "DEFAULT", "의도 분석 미수행 - 기본 컨텍스트 검색", level="DEBUG")
            # query_type을 sql_query로 설정하여 컨텍스트 검색 트리거
            intent_analysis = {"query_type": "sql_query"}
            updates["intent_analysis"] = intent_analysis

        # 컨텍스트 검색용 임시 state 구성 (intent_analysis 포함)
        state_for_context = dict(state)
        state_for_context["intent_analysis"] = intent_analysis

        # 컨텍스트 검색 실행 (업데이트 dict 반환)
        context_updates = context_retrieval_node(state_for_context)

        # 두 업데이트 병합 (LangGraph가 state에 자동 병합)
        updates.update(context_updates)
        return updates

    def _agent_node(self, state: AgentState) -> AgentState:
        """
        Agent 노드: LLM이 다음 행동 결정

        확장 포인트:
        - 메모리 로딩 (이전 대화 컨텍스트)
        - 동적 프롬프트 (사용자별, 시나리오별)
        - 스트리밍 응답
        """
        request_id = state.get("request_id", "unknown")
        iteration = state.get("iteration_count", 0)
        session_id = state.get("session_id", "")
        config = state.get("config", AgentConfig()) # type: ignore

        log_step(request_id, "AGENT", str(iteration), "THINK", "LLM 의사결정 시작", messages_count=len(state["messages"]))

        # 1. 메시지 준비: state["messages"]는 checkpointer + add_messages reducer가 자동 관리
        # SystemMessage를 제외하고 LLM에 전달할 메시지 준비
        current_messages = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
        validated_messages = self._validate_messages(current_messages, request_id, iteration)

        # 검증 후 메시지가 비어있으면 에러
        if not validated_messages:
            log_step(request_id, "AGENT", str(iteration), "ERROR", "검증 후 메시지가 비어있음", level="ERROR", original_count=len(state['messages']))
            error_msg = "메시지 검증 실패: 유효한 메시지가 없습니다."
            # add_messages reducer가 자동으로 추가하므로 새 메시지만 반환
            state["messages"] = [AIMessage(content=error_msg)]
            state["final_answer"] = error_msg
            return state

        # 2. 시스템 프롬프트를 LLM 호출용 메시지에만 추가 (state에는 저장하지 않음)
        # 이렇게 하면 InMemorySaver에 SystemMessage가 중복 저장되지 않음
        system_prompt = self._get_system_prompt()

        # 컨텍스트 프롬프트 주입 (LangGraph 상태에서 읽음)
        context_prompt = state.get("context_prompt", "")  # type: ignore
        if context_prompt:
            system_prompt = f"{system_prompt}\n\n---\n# SQL 컨텍스트 (자동 주입됨)\n{context_prompt}"
            log_step(request_id, "AGENT", str(iteration), "CONTEXT-INJECT", f"컨텍스트 프롬프트 주입 | length={len(context_prompt)}")
        else:
            log_step(request_id, "AGENT", str(iteration), "CONTEXT-INJECT", "컨텍스트 프롬프트 없음", level="DEBUG")

        messages_for_llm = [SystemMessage(content=system_prompt)] + validated_messages
        log_step(request_id, "AGENT", str(iteration), "SYSTEM", "LLM 호출용 시스템 프롬프트 추가", total_messages=len(messages_for_llm))

        # 3. LLM 호출
        llm = self._get_llm(config)

        # 디버깅: LLM 입력 메시지 로그 (DEBUG 레벨, 전문 출력)
        if logger.isEnabledFor(logging.DEBUG):
            log_step(request_id, "AGENT", str(iteration), "LLM-INPUT", f"LLM 입력 메시지 ({len(messages_for_llm)}개)", level="DEBUG")
            for i, msg in enumerate(messages_for_llm):
                msg_type = type(msg).__name__
                msg_content = str(msg.content) if hasattr(msg, 'content') and msg.content else "(empty)"
                tool_info = ""
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_info = f", tool_calls={len(msg.tool_calls)}"
                log_step(request_id, "AGENT", str(iteration), "LLM-INPUT", f"[{i}] {msg_type}{tool_info}", level="DEBUG", content=msg_content)
                # AIMessage의 tool_calls 상세 내용 출력 (content가 비어있을 때)
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        log_step(request_id, "AGENT", str(iteration), "LLM-INPUT", f"  └─ TOOL_CALL: {tc['name']}", level="DEBUG", args=tc.get('args', {}))

        try:
            response = llm.invoke(messages_for_llm)
            
            # 디버깅: LLM 출력 로그 (DEBUG 레벨, 전문 출력)
            if logger.isEnabledFor(logging.DEBUG):
                response_content = response.content if hasattr(response, 'content') else "(no content)"
                response_tool_calls = len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0
                log_step(request_id, "AGENT", str(iteration), "LLM-OUTPUT", "LLM 응답", level="DEBUG", content_length=len(response_content), tool_calls=response_tool_calls)
                if response_content:
                    log_step(request_id, "AGENT", str(iteration), "LLM-OUTPUT", "응답 내용", level="DEBUG", content=response_content)
                if response_tool_calls > 0:
                    for tc in response.tool_calls:
                        log_step(request_id, "AGENT", str(iteration), "LLM-OUTPUT", f"TOOL_CALL: {tc['name']}", level="DEBUG", args=tc['args'])

            # 4. 메시지 추가: add_messages reducer가 자동으로 기존 메시지에 추가
            # 새로 추가된 response만 반환하면 reducer가 기존 메시지와 merge
            state["messages"] = [response]
            state["iteration_count"] = iteration + 1

            # 5. 도구 호출 로그
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_names = [tc["name"] for tc in response.tool_calls]
                log_step(request_id, "AGENT", str(iteration), "ACTION",
                        f"도구 호출 결정: {', '.join(tool_names)}")

                # 도구 필터링 (whitelist/blacklist)
                filtered_calls = []
                for tc in response.tool_calls:
                    if config.is_tool_allowed(tc["name"]):
                        filtered_calls.append(tc)
                    else:
                        log_step(request_id, "AGENT", str(iteration), "BLOCKED",
                                f"도구 호출 차단: {tc['name']}")

                # 필터링된 도구만 유지
                if filtered_calls != response.tool_calls:
                    response.tool_calls = filtered_calls
                    state["messages"][-1] = response

            else:
                log_step(request_id, "AGENT", str(iteration), "FINISH", "최종 답변 생성",  answer_length=len(response.content) if response.content else 0)

                # 디버깅: 최종 답변 내용 로그 (DEBUG 레벨, 전문 출력)
                if response.content:
                    log_step(request_id, "AGENT", str(iteration), "ANSWER", "최종 답변", level="DEBUG", content=response.content)
                else:
                    log_step(request_id, "AGENT", str(iteration), "ANSWER", "최종 답변이 비어있음!", level="WARNING")

            return state

        except Exception as e:
            log_step(request_id, "AGENT", str(iteration), "ERROR", f"LLM 호출 실패: {e}", level="ERROR")

            # 에러 메시지 추가: add_messages reducer가 자동으로 기존 메시지에 추가
            error_msg = f"LLM 호출 중 오류가 발생했습니다: {str(e)}"
            state["messages"] = [AIMessage(content=error_msg)]
            state["final_answer"] = error_msg

            return state

    def _validate_messages(self, messages: List[BaseMessage], request_id: str = "SYSTEM", iteration: int = 0) -> List[BaseMessage]:
        """
        메시지 순서 및 형식 검증

        OpenAI API 요구사항:
        - ToolMessage는 반드시 tool_calls가 있는 AIMessage 다음에만 올 수 있음
        - 모든 tool_call_id에 대한 응답이 있어야 함 (실패한 경우에도 에러 메시지 포함)
        """
        if not messages:
            log_step(request_id, "AGENT", str(iteration), "VALIDATE", "입력 메시지가 비어있음", level="WARNING")
            return messages

        validated = []

        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__

            # ToolMessage 검증
            if isinstance(msg, ToolMessage):
                # validated 리스트의 마지막 메시지가 tool_calls를 가진 AIMessage인지 확인
                last_has_tool_calls = False
                if validated:
                    last_msg = validated[-1]
                    if isinstance(last_msg, AIMessage):
                        last_has_tool_calls = hasattr(last_msg, "tool_calls") and bool(last_msg.tool_calls)

                if not last_has_tool_calls:
                    # CRITICAL: 고아 ToolMessage도 유지해야 함 (OpenAI API 요구사항)
                    # 실패한 도구 호출에 대한 응답도 포함되어야 함
                    content_preview = truncate_text(str(msg.content), 50) if msg.content else "empty"
                    log_step(request_id, "AGENT", str(iteration), "VALIDATE", f"[{i}] ToolMessage without preceding tool_calls", level="WARNING", content=content_preview)
                log_step(request_id, "AGENT", str(iteration), "VALIDATE", f"[{i}] Keeping ToolMessage", level="DEBUG")

            # 다른 메시지 타입 로깅
            if isinstance(msg, AIMessage):
                has_tool_calls = hasattr(msg, "tool_calls") and bool(msg.tool_calls)
                log_step(request_id, "AGENT", str(iteration), "VALIDATE", f"[{i}] AIMessage", level="DEBUG", has_tool_calls=has_tool_calls)
            else:
                log_step(request_id, "AGENT", str(iteration), "VALIDATE", f"[{i}] {msg_type}", level="DEBUG")

            validated.append(msg)

        log_step(request_id, "AGENT", str(iteration), "VALIDATE", f"메시지 검증 완료: {len(messages)} -> {len(validated)}", level="DEBUG")
        return validated

    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """
        조건부 분기: 도구 호출 여부 확인

        확장 포인트:
        - 커스텀 종료 조건 (예: 특정 도구 호출 후 종료)
        - 비용 제한 (LLM 호출 횟수 제한)
        - 시간 제한
        """
        request_id = state.get("request_id", "unknown")
        config = state.get("config", AgentConfig()) # type: ignore
        start_time = state.get("start_time", time.time())

        # 1. 최대 반복 체크
        if state["iteration_count"] >= config.max_iterations:
            log_step(request_id, "AGENT", "LIMIT", "STOP", "최대 반복 횟수 도달", max_iterations=config.max_iterations)
            state["final_answer"] = "최대 반복 횟수에 도달했습니다. 질문을 더 구체적으로 작성해주세요."
            return "end"

        # 2. 타임아웃 체크
        elapsed = time.time() - start_time
        if elapsed > config.timeout_seconds:
            log_step(request_id, "AGENT", "TIMEOUT", "STOP", "타임아웃 도달", elapsed_seconds=int(elapsed))
            state["final_answer"] = "요청 처리 시간이 초과되었습니다."
            return "end"

        # 3. Function call 확인
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls: # type: ignore  # tool_calls가 존재한다면 계속 진행
            return "continue"
        else:
            # 최종 답변 저장
            final_content = last_message.content if hasattr(last_message, "content") else ""
            state["final_answer"] = final_content # type: ignore
            
            # 디버깅: 최종 답변 내용 확인 (DEBUG 레벨, 전문 출력)
            if final_content:
                log_step(request_id, "AGENT", "DECISION", "END", "최종 답변 저장", level="DEBUG", content=final_content)
            else:
                log_step(request_id, "AGENT", "DECISION", "END", "최종 답변이 비어있음!", level="WARNING", last_message_type=type(last_message).__name__)
            
            return "end"

    def _get_system_prompt(self) -> str:
        """
        시스템 프롬프트 생성 (DB에서 조회)

        조회 우선순위:
        1. DB (tb_app_settings: category='prompt', key='agent_system_prompt')
        2. prompt_service 내장 기본값
        """
        return prompt_service.get_agent_system_prompt()

    def _log_existing_checkpoint(self, request_id: str, session_id: str, graph_config: RunnableConfig) -> None:
        """
        멀티턴 디버깅: 기존 체크포인트의 메시지 히스토리 로깅 (DEBUG 레벨)

        Args:
            request_id: 요청 추적 ID
            session_id: 세션 ID
            graph_config: 그래프 설정 (thread_id 포함)
        """
        try:
            existing_checkpoint = self.checkpointer.get(graph_config)
            if existing_checkpoint:
                existing_msgs = existing_checkpoint.get("channel_values", {}).get("messages", [])
                # INFO: 요약만 출력
                log_step(request_id, "AGENT", "MULTI-TURN", "SESSION", "기존 세션 발견", session_id=session_id, messages=len(existing_msgs))
                # DEBUG: 상세 히스토리 (전문 출력)
                if logger.isEnabledFor(logging.DEBUG):
                    for i, msg in enumerate(existing_msgs):
                        msg_type = type(msg).__name__
                        msg_content = str(msg.content) if hasattr(msg, 'content') and msg.content else "(empty)"
                        tool_info = ""
                        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            tool_info = f", tool_calls={len(msg.tool_calls)}"
                        log_step(request_id, "AGENT", "MULTI-TURN", "HISTORY", f"[{i}] {msg_type}{tool_info}", level="DEBUG", content=msg_content)
            else:
                log_step(request_id, "AGENT", "MULTI-TURN", "SESSION", "새 세션 시작", session_id=session_id)
        except Exception as e:
            log_step(request_id, "AGENT", "MULTI-TURN", "ERROR", f"체크포인트 조회 실패: {e}", level="WARNING")

    def _log_final_messages(self, request_id: str, session_id: str, messages: List[BaseMessage]) -> None:
        """
        멀티턴 디버깅: 실행 완료 후 전체 메시지 히스토리 로깅 (DEBUG 레벨)

        Args:
            request_id: 요청 추적 ID
            session_id: 세션 ID
            messages: 최종 메시지 리스트
        """
        # DEBUG 레벨에서만 상세 히스토리 출력 (전문 출력)
        if logger.isEnabledFor(logging.DEBUG):
            log_step(request_id, "AGENT", "MULTI-TURN", "COMPLETE", f"실행 완료 후 전체 메시지 ({len(messages)}개)", level="DEBUG", session_id=session_id)
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                msg_content = str(msg.content) if hasattr(msg, 'content') and msg.content else "(empty)"
                tool_info = ""
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_info = f", tool_calls={len(msg.tool_calls)}"
                log_step(request_id, "AGENT", "MULTI-TURN", "HISTORY", f"[{i}] {msg_type}{tool_info}", level="DEBUG", content=msg_content)

    async def ainvoke(self, inputs: Dict[str, Any]) -> AgentResponse:
        """
        Agent 비동기 실행 (InMemorySaver 사용)

        확장 포인트:
        - 스트리밍 응답
        - 중간 결과 콜백
        - 진행률 표시
        """
        request_id = inputs.get("request_id", str(uuid.uuid4())[:8])
        question = inputs["question"]
        session_id = inputs.get("session_id", f"session-{request_id}")
        config = inputs.get("config", AgentConfig()) # type: ignore

        start_time = time.time()

        # 초기 상태
        initial_state: AgentState = {  # type: ignore
            # 기본 필드
            "messages": [HumanMessage(content=question)],
            "question": question,
            "session_id": session_id,
            "config": config,
            "iteration_count": 0,
            "final_answer": "",
            "request_id": request_id,
            "start_time": start_time,
            # 확장 필드 기본값
            **create_state_defaults()
        }

        # 의도 분석 활성화 여부 로깅
        enable_intent = getattr(config, 'enable_intent_analysis', False)
        log_step(request_id, "AGENT", "0", "INIT", "Agent 실행 시작", question=truncate_text(question, 50), session_id=session_id, intent_analysis=enable_intent)

        try:
            # 그래프 실행 (InMemorySaver가 thread_id를 통해 대화 히스토리 관리)
            graph_config: RunnableConfig = {"configurable": {"thread_id": session_id}}

            # 멀티턴 디버깅: 기존 체크포인트 확인
            self._log_existing_checkpoint(request_id, session_id, graph_config)

            result = await self.graph.ainvoke(initial_state, config=graph_config) 

            # 실행 시간 계산
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 응답 구성
            steps = self._extract_steps(result["messages"])
            tools_used = self._extract_tools_used(result["messages"])
            
            # 최종 답변 추출 (마지막 AIMessage의 content)
            final_answer: str = ""
            if result.get("messages"):
                for message in reversed(result["messages"]):
                    if isinstance(message, AIMessage) and message.content:
                        # AIMessage.content는 str | list 타입이므로 str로 변환
                        content = message.content
                        final_answer = content if isinstance(content, str) else str(content)
                        break
                        
            
            
            # 디버깅: 최종 답변 확인 (DEBUG 레벨, 전문 출력)
            if logger.isEnabledFor(logging.DEBUG):
                log_step(request_id, "AGENT", "EXTRACT", "RESULT", "최종 답변 추출 완료", level="DEBUG", length=len(final_answer))
                if final_answer:
                    log_step(request_id, "AGENT", "EXTRACT", "ANSWER", "추출된 답변", level="DEBUG", content=final_answer)

            log_step(request_id, "AGENT", "END", "COMPLETE", "Agent 실행 완료", iterations=result["iteration_count"], tools_count=len(tools_used), execution_time_ms=execution_time_ms, answer_length=len(final_answer))

            # 멀티턴 디버깅: 실행 완료 후 전체 메시지 히스토리 로깅
            self._log_final_messages(request_id, session_id, result["messages"])

            # 의도분석 결과 추출 (디버깅 및 검증용)
            intent_analysis = result.get("intent_analysis", {})
            intent_metadata = {
                "query_type": intent_analysis.get("query_type"),
                "intent": intent_analysis.get("intent"),
                "confidence": intent_analysis.get("confidence"),
                "is_ambiguous": result.get("is_ambiguous", False),
                "ambiguity_type": intent_analysis.get("ambiguity_type"),
            } if intent_analysis else None

            return AgentResponse(
                answer=final_answer,
                steps=steps,
                total_iterations=result["iteration_count"],
                tools_used=tools_used,
                success=True,
                error=None,  # 성공 시 에러 없음
                metadata={
                    "request_id": request_id,
                    "session_id": session_id,
                    "execution_time_ms": execution_time_ms,
                    "llm_model": config.llm_model,
                    "intent_analysis": intent_metadata
                },
                session_id=session_id
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_step(request_id, "AGENT", "END", "ERROR", f"Agent 실행 실패: {e}", level="ERROR")

            return AgentResponse(
                answer=f"Agent 실행 중 오류가 발생했습니다: {str(e)}",
                steps=[],
                total_iterations=0,
                tools_used=[],
                success=False,
                error=str(e),
                metadata={
                    "request_id": request_id,
                    "execution_time_ms": execution_time_ms,
                    "error_type": type(e).__name__
                },
                session_id=session_id
            )

    def _extract_steps(self, messages: List[BaseMessage]) -> List[AgentStep]:
        """
        메시지에서 실행 단계 추출

        확장 포인트:
        - Thought 추출 (LLM의 내부 추론)
        - 타임스탬프 정확도 향상
        - SQL 결과 구조화 데이터 추출 (프론트엔드 테이블 표시용)
        """
        import json as json_module

        steps = []
        step_num = 0

        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    step_num += 1

                    # 다음 메시지에서 observation 찾기
                    observation = ""
                    sql_result = None

                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        if isinstance(next_msg, ToolMessage):
                            raw_content = str(next_msg.content)

                            # SQL 도구인 경우 JSON 파싱하여 sql_result 추출
                            if tool_call["name"] == "query_database_tool":
                                try:
                                    parsed = json_module.loads(raw_content)
                                    # answer 부분만 observation으로 사용
                                    observation = truncate_text(str(parsed.get("answer", raw_content)), 500)

                                    # sql_result 추출
                                    sql_data = parsed.get("sql_result")
                                    if sql_data:
                                        sql_result = AgentSQLResult(
                                            sql=sql_data.get("sql"),
                                            columns=sql_data.get("columns", []),
                                            rows=sql_data.get("rows", []),
                                            row_count=sql_data.get("row_count", 0),
                                            execution_time_ms=sql_data.get("execution_time_ms")
                                        )
                                        log_step("SYSTEM", "AGENT", str(step_num), "EXTRACT", "SQL 결과 추출", level="DEBUG", row_count=sql_result.row_count, columns=len(sql_result.columns))
                                except json_module.JSONDecodeError:
                                    # JSON 파싱 실패 시 원본 사용
                                    observation = truncate_text(raw_content, 500)
                                    log_step("SYSTEM", "AGENT", str(step_num), "EXTRACT", "SQL 도구 응답 JSON 파싱 실패", level="WARNING")
                            else:
                                observation = truncate_text(raw_content, 500)
                        else:
                            observation = truncate_text(str(next_msg.content), 500)

                    # Thought 추출 (간단 버전)
                    thought = f"도구 선택: {tool_call['name']}"

                    steps.append(AgentStep(
                        step_number=step_num,
                        thought=thought,
                        action=tool_call["name"],
                        action_input=tool_call["args"],
                        observation=observation,
                        timestamp=datetime.now(),
                        sql_result=sql_result
                    ))

        return steps

    def _extract_tools_used(self, messages: List[BaseMessage]) -> List[str]:
        """사용된 도구 목록 추출"""
        tools = set()
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tools.add(tool_call["name"])
        return sorted(list(tools))


# 싱글톤 인스턴스
agent_graph = InsightAgentGraph()
