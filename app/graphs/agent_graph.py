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

from typing import Literal, Dict, Any, List, Sequence, Annotated
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
from app.core.config.settings_config import settings_config
from app.config import settings
from app.utils.logger import setup_logger, log_step  # 통합 로깅 유틸리티
from app.core.llm.llm_config import LLMConfigManager  # 통합 LLM 설정
from app.core.llm.prompt_service import prompt_service  # 프롬프트 서비스

logger = setup_logger(__name__)


# AgentState TypedDict 정의
from typing import TypedDict


class AgentState(TypedDict):
    """Agent의 내부 상태"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    question: str
    session_id: str
    config: AgentConfig
    iteration_count: int
    final_answer: str
    request_id: str
    start_time: float


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

        logger.debug(f"[InsightAgentGraph] Initialized with {len(self.tools)} tools and InMemorySaver")

    def _get_tools(self) -> List:
        """
        사용 가능한 도구 목록

        확장 포인트:
        - 동적 도구 로딩 (플러그인)
        - 사용자별 권한 기반 도구 필터링
        - 컨텍스트별 도구 선택
        """
        return [
            query_database_tool,      # SQL Tool
            search_documents_tool,    # RAG Tool
            calculate_tool,           # Calculator Tool
        ]

    def _get_llm(self, config: AgentConfig):
        """
        LLM 인스턴스 생성 (Phase 1: init_chat_model 적용)

        확장 포인트:
        - 모델 선택 로직
        - 제공자 선택 로직 (Phase 2+에서 활성화)
        - 폴백 모델 (메인 모델 실패 시)
        - 비용 최적화 (간단한 질문은 저렴한 모델)
        """
        # Agent 설정에서 provider 가져오기 (Phase 1: openai만 지원)
        provider = getattr(config, 'llm_provider', None) or \
                   settings_config.get_value("agent", "llm_provider", "openai")

        logger.debug(f"[_get_llm] Creating LLM: model={config.llm_model}, provider={provider}, temperature={config.llm_temperature}")

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
        Agent 그래프 구성 (ReAct 패턴)

        플로우:
        1. agent (LLM 의사결정)
        2. should_continue (도구 호출 여부 판단)
           - continue → tools (도구 실행) → agent (반복)
           - end → END (종료)
        """
        workflow = StateGraph(AgentState)

        # 노드 추가
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # 진입점
        workflow.set_entry_point("agent")

        # 조건부 엣지: LLM이 도구 호출 여부 결정
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,      # _should_continue에 평가에 따라 분기
            {
                "continue": "tools",
                "end": END
            }
        )

        # 도구 실행 후 다시 agent로 (루프)
        workflow.add_edge("tools", "agent")

        return workflow.compile(checkpointer=self.checkpointer)

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
        validated_messages = self._validate_messages(current_messages)

        # 검증 후 메시지가 비어있으면 에러
        if not validated_messages:
            logger.error(f"[{request_id}] 검증 후 메시지가 비어있음. 원본 메시지 수: {len(state['messages'])}")
            error_msg = "메시지 검증 실패: 유효한 메시지가 없습니다."
            # add_messages reducer가 자동으로 추가하므로 새 메시지만 반환
            state["messages"] = [AIMessage(content=error_msg)]
            state["final_answer"] = error_msg
            return state

        # 2. 시스템 프롬프트를 LLM 호출용 메시지에만 추가 (state에는 저장하지 않음)
        # 이렇게 하면 InMemorySaver에 SystemMessage가 중복 저장되지 않음
        system_prompt = self._get_system_prompt()
        messages_for_llm = [SystemMessage(content=system_prompt)] + validated_messages
        log_step(request_id, "AGENT", str(iteration), "SYSTEM", "LLM 호출용 시스템 프롬프트 추가", total_messages=len(messages_for_llm))

        # 3. LLM 호출
        llm = self._get_llm(config)

        # 디버깅: LLM 입력 메시지 로그 (DEBUG 레벨)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[{request_id}] [AGENT-{iteration}] [LLM-INPUT] Messages to LLM ({len(messages_for_llm)} total):")
            for i, msg in enumerate(messages_for_llm):
                msg_type = type(msg).__name__
                content_preview = str(msg.content)[:100] if hasattr(msg, 'content') and msg.content else "(empty)"
                has_tool_calls = isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and bool(msg.tool_calls)
                logger.debug(f"  [{i}] {msg_type}: {content_preview}... | has_tool_calls={has_tool_calls}")

        try:
            response = llm.invoke(messages_for_llm)
            
            # 디버깅: LLM 출력 로그 (DEBUG 레벨)
            response_content = response.content if hasattr(response, 'content') else "(no content)"
            response_tool_calls = len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0
            logger.debug(f"[{request_id}] [AGENT-{iteration}] [LLM-OUTPUT] content_length={len(response_content)}, tool_calls={response_tool_calls}")

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

                # 디버깅: 최종 답변 내용 로그 (DEBUG 레벨, 비어있을 때만 WARNING)
                if response.content:
                    logger.debug(f"[{request_id}] [AGENT-{iteration}] [ANSWER] {response.content[:100]}")
                else:
                    logger.warning(f"[{request_id}] [AGENT-{iteration}] [ANSWER] 최종 답변이 비어있음!")

            return state

        except Exception as e:
            logger.error(f"[{request_id}] [AGENT-{iteration}] LLM 호출 실패: {e}", exc_info=True)

            # 에러 메시지 추가: add_messages reducer가 자동으로 기존 메시지에 추가
            error_msg = f"LLM 호출 중 오류가 발생했습니다: {str(e)}"
            state["messages"] = [AIMessage(content=error_msg)]
            state["final_answer"] = error_msg

            return state

    def _validate_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        메시지 순서 및 형식 검증

        OpenAI API 요구사항:
        - ToolMessage는 반드시 tool_calls가 있는 AIMessage 다음에만 올 수 있음
        - 모든 tool_call_id에 대한 응답이 있어야 함 (실패한 경우에도 에러 메시지 포함)
        """
        if not messages:
            logger.warning("_validate_messages: 입력 메시지가 비어있음")
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
                    logger.warning(f"[{i}] ToolMessage without preceding tool_calls (possibly error response): {msg.content[:50] if msg.content else 'empty'}...")
                    # continue를 제거하여 메시지를 유지
                logger.debug(f"[{i}] Keeping ToolMessage")

            # 다른 메시지 타입 로깅
            if isinstance(msg, AIMessage):
                has_tool_calls = hasattr(msg, "tool_calls") and bool(msg.tool_calls)
                logger.debug(f"[{i}] AIMessage, has_tool_calls={has_tool_calls}")
            else:
                logger.debug(f"[{i}] {msg_type}")

            validated.append(msg)

        logger.debug(f"_validate_messages: {len(messages)} -> {len(validated)} messages")
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
            
            # 디버깅: 최종 답변 내용 확인 (DEBUG 레벨, 비어있을 때만 WARNING)
            if final_content:
                logger.debug(f"[{request_id}] [DECISION] 최종 답변 저장: {final_content[:100]}")
            else:
                logger.warning(f"[{request_id}] [DECISION] 최종 답변이 비어있음! last_message type: {type(last_message).__name__}")
            
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
                logger.info(f"[{request_id}] [MULTI-TURN] 기존 세션 발견: session_id={session_id}, messages={len(existing_msgs)}")
                # DEBUG: 상세 히스토리
                if logger.isEnabledFor(logging.DEBUG):
                    for i, msg in enumerate(existing_msgs):
                        msg_type = type(msg).__name__
                        content = str(msg.content)[:100] if hasattr(msg, 'content') and msg.content else "(empty)"
                        has_tool_calls = isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and bool(msg.tool_calls)
                        tool_info = f", tool_calls={len(msg.tool_calls)}" if has_tool_calls else ""
                        logger.debug(f"[{request_id}] [MULTI-TURN]   [{i}] {msg_type}: {content}{tool_info}")
            else:
                logger.info(f"[{request_id}] [MULTI-TURN] 새 세션 시작: session_id={session_id}")
        except Exception as e:
            logger.warning(f"[{request_id}] [MULTI-TURN] 체크포인트 조회 실패: {e}")

    def _log_final_messages(self, request_id: str, session_id: str, messages: List[BaseMessage]) -> None:
        """
        멀티턴 디버깅: 실행 완료 후 전체 메시지 히스토리 로깅 (DEBUG 레벨)

        Args:
            request_id: 요청 추적 ID
            session_id: 세션 ID
            messages: 최종 메시지 리스트
        """
        # DEBUG 레벨에서만 상세 히스토리 출력
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[{request_id}] [MULTI-TURN] 실행 완료 후 전체 메시지 ({len(messages)}개), session_id={session_id}")
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content = str(msg.content)[:100] if hasattr(msg, 'content') and msg.content else "(empty)"
                tool_info = ""
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_info = f", tool_calls={len(msg.tool_calls)}"
                logger.debug(f"[{request_id}] [MULTI-TURN]   [{i}] {msg_type}: {content}{tool_info}")

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
        initial_state: AgentState = {
            "messages": [HumanMessage(content=question)],
            "question": question,
            "session_id": session_id,
            "config": config,
            "iteration_count": 0,
            "final_answer": "",
            "request_id": request_id,
            "start_time": start_time
        }

        log_step(request_id, "AGENT", "0", "INIT", "Agent 실행 시작", question=question[:50], session_id=session_id)

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
                        
            
            
            # 디버깅: 최종 답변 확인 (DEBUG 레벨)
            logger.debug(f"[{request_id}] [EXTRACT] Final answer extracted: length={len(final_answer)}, preview={final_answer[:100] if final_answer else '(empty)'}")

            log_step(request_id, "AGENT", "END", "COMPLETE", "Agent 실행 완료", iterations=result["iteration_count"], tools_count=len(tools_used), execution_time_ms=execution_time_ms, answer_length=len(final_answer))

            # 멀티턴 디버깅: 실행 완료 후 전체 메시지 히스토리 로깅
            self._log_final_messages(request_id, session_id, result["messages"])

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
                    "llm_model": config.llm_model
                },
                session_id=session_id
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"[{request_id}] Agent 실행 실패: {e}", exc_info=True)

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
                                    observation = str(parsed.get("answer", raw_content))[:500]

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
                                        logger.debug(f"[STEP {step_num}] SQL result extracted: {sql_result.row_count} rows, {len(sql_result.columns)} columns")
                                except json_module.JSONDecodeError:
                                    # JSON 파싱 실패 시 원본 사용
                                    observation = raw_content[:500]
                                    logger.warning(f"[STEP {step_num}] Failed to parse SQL tool response as JSON")
                            else:
                                observation = raw_content[:500]
                        else:
                            observation = str(next_msg.content)[:500]

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
