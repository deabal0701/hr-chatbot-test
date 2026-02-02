"""
Agent State 정의 (ReAct 패턴)

ReAct Agent 그래프에서 사용하는 상태(State) 타입을 정의합니다.
LangGraph의 messages 기반 상태 관리를 사용합니다.
"""

from typing import Any, Annotated, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.models.agent import AgentConfig
from app.models.rag import SQLResult


def _overwrite(left: Any, right: Any) -> Any:
    """오른쪽 값으로 덮어쓰기 (reducer)"""
    return right if right is not None else left


class AgentState(TypedDict):
    """ReAct Agent State

    LangGraph의 messages 기반 상태 관리를 사용합니다.
    Agent는 Think → Action → Observation 사이클을 반복합니다.
    """

    # ===== 기본 필드 =====
    messages: Annotated[Sequence[BaseMessage], add_messages]  # 대화 히스토리 (누적)
    question: str                                              # 원본 질문
    session_id: str                                            # 세션 ID (멀티턴)
    request_id: str                                            # 요청 추적 ID

    # ===== ReAct 제어 필드 =====
    iteration_count: int                                       # 현재 반복 횟수
    max_iterations: int                                        # 최대 반복 횟수
    final_answer: str                                          # 최종 답변 (루프 종료 시)

    # ===== 설정 =====
    config: AgentConfig                                        # Agent 설정

    # ===== Tool 결과 (선택) =====
    last_tool_name: str                                        # 마지막 사용 Tool
    last_tool_result: str                                      # 마지막 Tool 결과

    # ===== SQL Tool 결과 (프론트엔드 표시용) =====
    generated_sql: str                                         # 생성된 SQL
    sql_result: Optional[SQLResult]                            # SQL 실행 결과

    # ===== RAG Tool 결과 =====
    rag_sources: List[Dict]                                    # 검색된 문서 목록

    # ===== 메타데이터 =====
    tools_used: List[str]                                      # 사용된 Tool 목록
    start_time: float                                          # 시작 시간


def create_initial_state(
    question: str,
    session_id: str = "unknown",
    request_id: str = "unknown",
    config: AgentConfig = None,
    max_iterations: int = 10,
) -> AgentState:
    """
    초기 상태 생성

    Args:
        question: 사용자 질문
        session_id: 세션 ID
        request_id: 요청 ID
        config: Agent 설정
        max_iterations: 최대 반복 횟수

    Returns:
        초기화된 AgentState
    """
    import time

    if config is None:
        config = AgentConfig()

    return AgentState(
        # 기본 필드
        messages=[],
        question=question,
        session_id=session_id,
        request_id=request_id,

        # ReAct 제어
        iteration_count=0,
        max_iterations=max_iterations,
        final_answer="",

        # 설정
        config=config,

        # Tool 결과
        last_tool_name="",
        last_tool_result="",

        # SQL 결과
        generated_sql="",
        sql_result=None,

        # RAG 결과
        rag_sources=[],

        # 메타데이터
        tools_used=[],
        start_time=time.time(),
    )
