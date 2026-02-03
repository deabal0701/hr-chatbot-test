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

import time
import uuid
from typing import Any, Dict

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
from app.models.agent import AgentResponse, AgentConfig, AgentStep
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

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

        log_step("SYSTEM", "AGENT", "INIT", "SETUP", "InsightAgentGraph 초기화 완료 (ReAct)", level="DEBUG")

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
        # 1. 입력 준비
        request_id = inputs.get("request_id", str(uuid.uuid4())[:8])
        question = inputs["question"]
        session_id = inputs.get("session_id", f"session-{request_id}")
        config = inputs.get("config", AgentConfig())
        max_iterations = inputs.get("max_iterations", config.max_iterations or 10)

        start_time = time.time()

        log_step(request_id, "AGENT", "0", "INIT",
                 f"ReAct Agent 실행 시작 | question={truncate_text(question, 50)}",
                 session_id=session_id)

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
            # 4. 그래프 실행
            graph_config: RunnableConfig = {"configurable": {"thread_id": session_id}}
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
            log_step(request_id, "AGENT", "END", "COMPLETE",
                     f"ReAct Agent 완료 | iterations={result.get('iteration_count', 0)}, "
                     f"tools={result.get('tools_used', [])}, time={execution_time_ms}ms")

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
            log_step(request_id, "AGENT", "END", "ERROR",
                     f"ReAct Agent 실패: {e}", level="ERROR")

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

        i = 0
        while i < len(messages):
            msg = messages[i]

            # AIMessage with tool_calls
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    step_number += 1
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id", "")

                    # 다음 메시지에서 결과 찾기
                    observation = ""
                    for j in range(i + 1, len(messages)):
                        if isinstance(messages[j], ToolMessage):
                            if messages[j].tool_call_id == tool_id:
                                observation = truncate_text(messages[j].content, 500)
                                break

                    steps.append(AgentStep(
                        step_number=step_number,
                        thought=f"Tool 호출: {tool_name}",
                        action=tool_name,
                        action_input=tool_args,
                        observation=observation,
                        sql_result=None,
                    ))

            i += 1

        return steps


# 싱글톤 인스턴스
agent_graph = InsightAgentGraph()
