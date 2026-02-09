"""
Agent Graph (ReAct 패턴)

ReAct (Reason + Act) 패턴을 사용하는 AI Agent 그래프입니다.
LLM이 자율적으로 Tool을 선택하고 실행하며, 결과를 관찰한 후
다음 행동을 결정하는 반복적인 패턴을 구현합니다.

그래프 흐름:
    START → agent_node → should_continue?
                            ├─ "tools" → tools_node → agent_node (loop)
                            └─ "answer" → answer_node → END

노드:
- agent_node: LLM Think/Action (Tool 선택 또는 추론)
- tools_node: Tool 실행 및 결과 반환
- answer_node: 최종 답변 생성 (NL2SQL 응답 프롬프트 사용)
"""

import asyncio
import time
import uuid
from typing import Any, AsyncGenerator, Dict

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import InMemorySaver

from app.graphs.agent.state import AgentState, create_initial_state
from app.graphs.agent.nodes.agent_node import agent_node, should_continue
from app.graphs.agent.nodes.tools_node import tools_node
from app.graphs.agent.nodes.answer_node import answer_node
from app.graphs.agent.middleware.chain import MiddlewareChain
from app.graphs.agent.middleware.pii import PIIMiddleware
from app.models.agent import AgentResponse, AgentConfig, AgentStep, AgentSQLResult
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

# LangSmith traceable (조건부 import)
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    traceable = None

logger = setup_logger(__name__)


class InsightAgentGraph:
    """
    ReAct Agent Graph

    LLM이 자율적으로 Tool을 선택하고 실행하는 ReAct 패턴 Agent입니다.

    특징:
    - ReAct 패턴: Think → Action → Observation 반복
    - Tool 자율 선택: LLM이 상황에 맞는 Tool 결정
    - 복합 질문 처리: 여러 Tool 순차 호출 가능
    - 멀티턴: InMemorySaver 사용

    사용법:
        agent = InsightAgentGraph()
        response = await agent.ainvoke({
            "question": "2024년 입사자 수는 몇 명이고 재택근무 정책은 뭐야?",
            "session_id": "session-123",
        })
    """

    def __init__(self):
        """Agent 그래프 초기화"""
        # Checkpointer (멀티턴 대화)
        self.checkpointer = InMemorySaver()

        # 미들웨어 체인
        self.middleware = self._init_middleware()

        # 그래프 빌드
        self.graph = self._build_graph()

        log_step(logger, "SYSTEM", "AGENT", "INIT", "SETUP", "InsightAgentGraph 초기화 완료 (ReAct)", level="DEBUG")

    def _init_middleware(self) -> MiddlewareChain:
        """
        미들웨어 체인 초기화

        현재는 PII 미들웨어만 등록 (껍데기).
        추후 Audit, RateLimit 등 추가 가능.
        """
        chain = MiddlewareChain()
        chain.add(PIIMiddleware())
        return chain

    def _build_graph(self) -> CompiledStateGraph:
        """
        ReAct Agent 그래프 빌드

        흐름:
            START → agent_node → should_continue?
                                    ├─ "tools" → tools_node → agent_node (loop)
                                    └─ "answer" → answer_node → END

        Returns:
            컴파일된 StateGraph
        """
        workflow = StateGraph(AgentState)

        # ===== 노드 등록 =====
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)
        workflow.add_node("answer", answer_node)

        # ===== 흐름 정의 =====

        # Entry Point: agent 노드
        workflow.set_entry_point("agent")

        # 조건부 분기: agent → tools 또는 answer
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "answer": "answer",
            }
        )

        # tools → agent (루프)
        workflow.add_edge("tools", "agent")

        # answer → END
        workflow.add_edge("answer", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def ainvoke(self, inputs: Dict[str, Any]) -> AgentResponse:
        """
        Agent 비동기 실행

        Args:
            inputs: 요청 데이터
                - question: str (필수)
                - session_id: str (선택, 멀티턴용)
                - request_id: str (선택, 추적용)
                - config: AgentConfig (선택)

        Returns:
            AgentResponse
        """
        # LangSmith 트레이싱: question을 Input으로 표시
        if LANGSMITH_AVAILABLE and traceable:
            return await self._traced_ainvoke(inputs)
        return await self._run_graph(inputs)

    async def _traced_ainvoke(self, inputs: Dict[str, Any]) -> AgentResponse:
        """LangSmith 트레이싱이 적용된 실행"""
        @traceable(name="Agent")  # type: ignore
        async def traced_run(question: str) -> AgentResponse:  # noqa: ARG001
            return await self._run_graph(inputs)
        return await traced_run(inputs["question"])

    async def astream_events(self, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Agent SSE 스트리밍 실행 (스테이지 그룹핑 방식)

        Agent 노드(agent, tools, answer)를 스테이지로 그룹핑하여 SSE 이벤트를 전송합니다.
        Agent는 agent→tools→agent 루프가 있으므로, 스테이지가 다르면 항상 이벤트를 전송합니다.

        Args:
            inputs: 요청 데이터 (question, session_id, request_id, config)

        Yields:
            SSE 포맷 문자열
        """
        from app.core.sse.stream_manager import format_sse, get_node_stage, get_stage_label
        from app.models.sse import NodeStartEvent, NodeCompleteEvent, CompleteEvent, ErrorEvent

        request_id = inputs.get("request_id", str(uuid.uuid4())[:8])
        question = inputs["question"]
        session_id = inputs.get("session_id", f"session-{request_id}")
        config = inputs.get("config", AgentConfig())
        max_iterations = inputs.get("max_iterations", config.max_iterations or 10)
        start_time = time.time()

        log_step(logger, request_id, "AGENT", "0", "INIT", "ReAct Agent SSE 스트리밍 시작", question=truncate_text(question, 50))

        # 미들웨어 입력 처리
        middleware_input = {"question": question, "session_id": session_id, "request_id": request_id, "config": config}
        processed_input = await self.middleware.process_input(middleware_input)

        # 초기 상태 생성
        initial_state = create_initial_state(
            question=processed_input["question"],
            session_id=processed_input["session_id"],
            request_id=processed_input["request_id"],
            config=processed_input.get("config", config),
            max_iterations=max_iterations,
        )
        initial_state["messages"] = [HumanMessage(content=question)]

        try:
            graph_config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "run_name": question,
            }

            # 스테이지 추적 변수
            current_stage = 0

            # 1단계 node_start 이벤트 전송 (그래프 실행 전)
            start_label = get_stage_label(1, "start", "agent")
            start_event = NodeStartEvent(node="stage_1", message=start_label, step=1)
            yield format_sse("node_start", start_event.model_dump())
            await asyncio.sleep(0)
            current_stage = 1

            # astream으로 노드별 이벤트 스트리밍
            async for chunk in self.graph.astream(initial_state, config=graph_config):
                for node_name, _state_update in chunk.items():
                    if node_name.startswith("__"):
                        continue

                    node_stage = get_node_stage(node_name, "agent")
                    if node_stage == 0:
                        continue

                    # Agent는 루프(agent→tools→agent)가 있으므로
                    # 스테이지가 다르면 항상 이벤트 전송 (양방향)
                    if node_stage != current_stage:
                        # 현재 스테이지 완료 이벤트
                        complete_label = get_stage_label(current_stage, "complete", "agent")
                        complete_event = NodeCompleteEvent(
                            node=f"stage_{current_stage}",
                            message=complete_label,
                            step=current_stage,
                        )
                        yield format_sse("node_complete", complete_event.model_dump())
                        await asyncio.sleep(0)

                        # 새 스테이지 시작 이벤트
                        new_start_label = get_stage_label(node_stage, "start", "agent")
                        new_start_event = NodeStartEvent(
                            node=f"stage_{node_stage}",
                            message=new_start_label,
                            step=node_stage,
                        )
                        yield format_sse("node_start", new_start_event.model_dump())
                        await asyncio.sleep(0)

                        current_stage = node_stage

                    log_step(logger, request_id, "AGENT", str(current_stage), "SSE", f"노드 완료: {node_name} (stage {node_stage})")

            # 마지막 스테이지 완료 이벤트
            if current_stage > 0:
                final_label = get_stage_label(current_stage, "complete", "agent")
                final_event = NodeCompleteEvent(
                    node=f"stage_{current_stage}",
                    message=final_label,
                    step=current_stage,
                )
                yield format_sse("node_complete", final_event.model_dump())
                await asyncio.sleep(0)

            # 최종 상태를 checkpointer에서 가져오기 (add_messages reducer 안전 처리)
            final_checkpoint = await self.graph.aget_state(graph_config)
            result = final_checkpoint.values

            execution_time_ms = int((time.time() - start_time) * 1000)
            final_answer = self._extract_final_answer(result)

            # 미들웨어 출력 처리
            middleware_output = {
                "request_id": request_id,
                "answer": final_answer,
                "generated_sql": result.get("generated_sql", ""),
                "sql_result": result.get("sql_result"),
                "rag_sources": result.get("rag_sources", []),
            }
            processed_output = await self.middleware.process_output(middleware_output)

            response = AgentResponse(
                answer=processed_output.get("answer", final_answer),
                steps=self._extract_steps(result),
                total_iterations=result.get("iteration_count", 0),
                tools_used=result.get("tools_used", []),
                success=True,
                error=None,
                metadata={
                    "request_id": request_id,
                    "session_id": session_id,
                    "execution_time_ms": execution_time_ms,
                    "generated_sql": result.get("generated_sql", ""),
                    "sql_result": result.get("sql_result"),
                },
                session_id=session_id,
            )

            log_step(logger, request_id, "AGENT", "END", "COMPLETE", "ReAct Agent SSE 완료", iterations=result.get('iteration_count', 0), time_ms=execution_time_ms)

            complete_event = CompleteEvent(data=response.model_dump())
            yield format_sse("complete", complete_event.model_dump())

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_step(logger, request_id, "AGENT", "END", "ERROR", "ReAct Agent SSE 실패", level="ERROR", error=str(e))

            error_event = ErrorEvent(code="AGENT_FAILED", message=f"Agent 실행 중 오류: {str(e)}", detail=str(e))
            yield format_sse("error", error_event.model_dump())

    async def _run_graph(self, inputs: Dict[str, Any]) -> AgentResponse:
        """실제 그래프 실행 로직"""
        # 1. 입력 준비
        request_id = inputs.get("request_id", str(uuid.uuid4())[:8])
        question = inputs["question"]
        session_id = inputs.get("session_id", f"session-{request_id}")
        config = inputs.get("config", AgentConfig())
        max_iterations = inputs.get("max_iterations", config.max_iterations or 10)

        start_time = time.time()

        log_step(logger, request_id, "AGENT", "0", "INIT", "ReAct Agent 실행 시작", question=truncate_text(question, 50), session_id=session_id)

        # 2. 미들웨어 입력 처리
        middleware_input = {
            "question": question,
            "session_id": session_id,
            "request_id": request_id,
            "config": config,
        }
        processed_input = await self.middleware.process_input(middleware_input)

        # 3. 초기 상태 생성
        initial_state = create_initial_state(
            question=processed_input["question"],
            session_id=processed_input["session_id"],
            request_id=processed_input["request_id"],
            config=processed_input.get("config", config),
            max_iterations=max_iterations,
        )

        # HumanMessage 추가
        initial_state["messages"] = [HumanMessage(content=question)]

        try:
            # 4. 그래프 실행 (run_name으로 LangSmith에 질문 표시)
            graph_config: RunnableConfig = {
                "configurable": {"thread_id": session_id},
                "run_name": question,  # LangGraph 트레이스 Name 컬럼에 표시
            }
            result = await self.graph.ainvoke(initial_state, config=graph_config)

            # 5. 실행 시간 계산
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 6. 최종 답변 추출
            final_answer = self._extract_final_answer(result)

            # 7. 미들웨어 출력 처리
            middleware_output = {
                "request_id": request_id,
                "answer": final_answer,
                "generated_sql": result.get("generated_sql", ""),
                "sql_result": result.get("sql_result"),
                "rag_sources": result.get("rag_sources", []),
            }
            processed_output = await self.middleware.process_output(middleware_output)

            # 8. 응답 구성
            log_step(logger, request_id, "AGENT", "END", "COMPLETE", "ReAct Agent 완료", iterations=result.get('iteration_count', 0), tools=result.get('tools_used', []), time_ms=execution_time_ms)

            return AgentResponse(
                answer=processed_output.get("answer", final_answer),
                steps=self._extract_steps(result),
                total_iterations=result.get("iteration_count", 0),
                tools_used=result.get("tools_used", []),
                success=True,
                error=None,
                metadata={
                    "request_id": request_id,
                    "session_id": session_id,
                    "execution_time_ms": execution_time_ms,
                    "generated_sql": result.get("generated_sql", ""),
                    "sql_result": result.get("sql_result"),
                },
                session_id=session_id,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_step(logger, request_id, "AGENT", "END", "ERROR", "ReAct Agent 실패", level="ERROR", error=str(e))

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
                    "error_type": type(e).__name__,
                },
                session_id=session_id,
            )

    def _extract_final_answer(self, result: Dict[str, Any]) -> str:
        """
        최종 답변 추출

        마지막 AIMessage의 content를 추출합니다.

        Args:
            result: 그래프 실행 결과

        Returns:
            최종 답변 문자열
        """
        messages = result.get("messages", [])

        # 역순으로 순회하며 AIMessage 찾기
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                # tool_calls가 없는 AIMessage가 최종 답변
                has_tool_calls = hasattr(msg, 'tool_calls') and msg.tool_calls
                if not has_tool_calls:
                    content = msg.content
                    # content가 list인 경우 문자열로 변환
                    if isinstance(content, list):
                        return " ".join(str(item) for item in content)
                    return str(content)

        # 못 찾으면 final_answer 필드 확인
        if result.get("final_answer"):
            return result["final_answer"]

        return "답변을 생성하지 못했습니다."

    def _extract_steps(self, result: Dict[str, Any]) -> list:
        """
        실행 단계 추출

        messages에서 Tool 호출 및 결과를 추출하여
        AgentStep 리스트로 반환합니다.

        Args:
            result: 그래프 실행 결과

        Returns:
            AgentStep 리스트
        """
        from langchain_core.messages import ToolMessage

        steps = []
        messages = result.get("messages", [])
        step_number = 0

        logger.debug(f"[EXTRACT_STEPS] messages 수: {len(messages)}")

        i = 0
        while i < len(messages):
            msg = messages[i]

            # AIMessage with tool_calls
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                logger.debug(f"[EXTRACT_STEPS] AIMessage[{i}] tool_calls 수: {len(msg.tool_calls)}")
                for tool_call in msg.tool_calls:
                    step_number += 1
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", "")

                    # 다음 메시지에서 결과 찾기
                    observation = ""
                    sql_result = None

                    for j in range(i + 1, len(messages)):
                        if isinstance(messages[j], ToolMessage):
                            if messages[j].tool_call_id == tool_id:
                                raw_content = messages[j].content
                                observation = truncate_text(raw_content, 500)

                                # SQL Tool인 경우 sql_result 추출 (관리자 UI 표시용)
                                if tool_name == "query_database_tool":
                                    sql_result = self._extract_sql_result(raw_content)

                                break

                    steps.append(AgentStep(
                        step_number=step_number,
                        thought=f"Tool 호출: {tool_name}",
                        action=tool_name,
                        action_input=tool_args,
                        observation=observation,
                        sql_result=sql_result,
                    ))
                    logger.debug(f"[EXTRACT_STEPS] step 추가: {step_number}. {tool_name}")

            i += 1

        logger.debug(f"[EXTRACT_STEPS] 총 steps 수: {len(steps)}")
        return steps

    def _extract_sql_result(self, content: str) -> AgentSQLResult | None:
        """
        ToolMessage content에서 SQL 결과 추출

        query_database_tool의 JSON 응답에서 sql_result를 파싱합니다.

        Args:
            content: ToolMessage의 raw content (JSON 문자열)

        Returns:
            AgentSQLResult 또는 None
        """
        import json

        try:
            data = json.loads(content)
            sql_result = data.get("sql_result")

            if sql_result:
                return AgentSQLResult(
                    sql=sql_result.get("sql", ""),
                    columns=sql_result.get("columns", []),
                    rows=sql_result.get("rows", [])[:100],  # 최대 100행
                    row_count=sql_result.get("row_count", 0),
                    execution_time_ms=sql_result.get("execution_time_ms"),
                )
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

        return None


# 싱글톤 인스턴스
agent_graph = InsightAgentGraph()
