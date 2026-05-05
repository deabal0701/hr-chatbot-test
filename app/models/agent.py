"""
Agent 전용 스키마

Agent 요청/응답 및 실행 단계 관련 모델
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSQLResult(BaseModel):
    """Agent에서 사용하는 SQL 결과 (NL2SQL과 유사한 구조)"""
    sql: Optional[str] = Field(None, description="실행된 SQL 쿼리")
    columns: List[str] = Field(default_factory=list, description="컬럼명 목록")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="결과 행들")
    row_count: int = Field(0, description="전체 행 수")
    execution_time_ms: Optional[int] = Field(None, description="실행 시간(ms)")


class AgentStep(BaseModel):
    """Agent의 개별 실행 단계"""
    step_number: int = Field(..., description="단계 번호")
    thought: str = Field(..., description="LLM의 생각 (추론)")
    action: str = Field(..., description="선택한 도구 이름")
    action_input: Dict[str, Any] = Field(..., description="도구 입력 파라미터")
    observation: str = Field(..., description="도구 실행 결과")
    timestamp: datetime = Field(default_factory=datetime.now, description="실행 시각")
    sql_result: Optional[AgentSQLResult] = Field(None, description="SQL 도구 실행 시 상세 결과")

    model_config = {
        "json_schema_extra": {
            "example": {
                "step_number": 1,
                "thought": "먼저 2024년 입사자를 조회해야 한다",
                "action": "query_database",
                "action_input": {"question": "2024년 입사자 수"},
                "observation": "27명 발견",
                "timestamp": "2024-01-04T10:30:00"
            }
        }
    }


class AgentConfig(BaseModel):
    """
    Agent 설정 (동적 조정 가능)

    확장 포인트:
    - 도구 선택 전략
    - 타임아웃 설정

    LLM 모델/제공자는 전역 설정(llm.model, llm.provider)을 사용하며, Agent 별도 설정은 없습니다.
    """
    max_iterations: int = Field(default=10, ge=1, le=20, description="최대 반복 횟수")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM 온도")
    enable_memory: bool = Field(default=True, description="메모리 활성화 여부")
    enable_streaming: bool = Field(default=False, description="스트리밍 응답 (확장)")
    enable_intent_analysis: bool = Field(default=True, description="의도 분석 노드 활성화 (Phase 2)")
    tools_whitelist: Optional[List[str]] = Field(None, description="사용 가능한 도구 목록 (None=전체)")
    tools_blacklist: Optional[List[str]] = Field(None, description="사용 금지 도구 목록")
    timeout_seconds: int = Field(default=60, ge=10, le=300, description="전체 타임아웃(초)")

    def is_tool_allowed(self, tool_name: str) -> bool:
        """도구 사용 가능 여부 확인"""
        if self.tools_blacklist and tool_name in self.tools_blacklist:
            return False
        if self.tools_whitelist and tool_name not in self.tools_whitelist:
            return False
        return True


class AgentRequest(BaseModel):
    """Agent 요청

    사용법:
    - 첫 요청: session_id를 생략하거나 None으로 전송 → 서버가 생성하여 응답에 포함
    - 멀티턴: 응답받은 session_id를 재사용

    Note: Agent 설정(max_iterations, timeout 등)은 서버 DB에서 관리됩니다.
    """
    question: str = Field(..., min_length=1, max_length=1000, description="질문")
    session_id: Optional[str] = Field(None, description="세션 ID (멀티턴 대화, 첫 요청시 생략)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "2024년 입사자 중 재택근무 정책을 준수하는 사람은 몇 명이고 평균 급여는?",
                "session_id": None
            }
        }
    }


class AgentResponse(BaseModel):
    """Agent 응답"""
    answer: str = Field(..., description="최종 답변")
    steps: List[AgentStep] = Field(default_factory=list, description="실행 단계들")
    total_iterations: int = Field(..., description="총 반복 횟수")
    tools_used: List[str] = Field(default_factory=list, description="사용된 도구 목록")
    success: bool = Field(..., description="성공 여부")
    error: Optional[str] = Field(None, description="에러 메시지")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    session_id: Optional[str] = Field(None, description="세션 ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "2024년 입사자는 총 27명이며, 재택근무 정책(주 2회 이상 출근)을 준수하는 사람은 15명입니다. 평균 급여는 5,400만원입니다.",
                "steps": [
                    {
                        "step_number": 1,
                        "thought": "먼저 2024년 입사자를 조회해야 한다",
                        "action": "query_database",
                        "action_input": {"question": "2024년 입사자 수"},
                        "observation": "27명 발견",
                        "timestamp": "2024-01-04T10:30:00"
                    }
                ],
                "total_iterations": 5,
                "tools_used": ["query_database", "search_documents", "calculate"],
                "success": True,
                "session_id": "user123-session456"
            }
        }
    }
