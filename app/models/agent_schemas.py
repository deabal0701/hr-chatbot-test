"""
Agent 전용 스키마

확장성:
- AgentMemory: 대화 메모리 (멀티턴 지원)
- AgentConfig: Agent 설정 (동적 조정)
- AgentMetrics: Agent 성능 메트릭
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class AgentStep(BaseModel):
    """Agent의 개별 실행 단계"""
    step_number: int = Field(..., description="단계 번호")
    thought: str = Field(..., description="LLM의 생각 (추론)")
    action: str = Field(..., description="선택한 도구 이름")
    action_input: Dict[str, Any] = Field(..., description="도구 입력 파라미터")
    observation: str = Field(..., description="도구 실행 결과")
    timestamp: datetime = Field(default_factory=datetime.now, description="실행 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "thought": "먼저 2024년 입사자를 조회해야 한다",
                "action": "query_database",
                "action_input": {"question": "2024년 입사자 수"},
                "observation": "27명 발견",
                "timestamp": "2024-01-04T10:30:00"
            }
        }


class AgentMemory(BaseModel):
    """
    [DEPRECATED] Agent 대화 메모리 (멀티턴 지원)

    이 클래스는 더 이상 사용되지 않습니다.
    InMemorySaver가 자동으로 대화 히스토리를 관리합니다.

    보존 이유: 기존 코드와의 호환성 유지
    """
    session_id: str = Field(..., description="세션 ID")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="메시지 히스토리")
    summary: Optional[str] = Field(None, description="대화 요약 (장기 메모리)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 N개 메시지 가져오기"""
        return self.messages[-limit:]

    def get_context_string(self, max_length: int = 2000) -> str:
        """
        컨텍스트 문자열 생성 (프롬프트에 포함용)

        확장: 토큰 수 기반 제한
        """
        recent = self.get_recent_messages(limit=5)
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in recent
        ])

        if len(context) > max_length:
            context = context[-max_length:]

        return context


class AgentConfig(BaseModel):
    """
    Agent 설정 (동적 조정 가능)

    확장 포인트:
    - 도구 선택 전략
    - LLM 모델 선택
    - 타임아웃 설정
    """
    max_iterations: int = Field(default=10, ge=1, le=20, description="최대 반복 횟수")
    llm_model: str = Field(default="gpt-4o", description="사용할 LLM 모델")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM 온도")
    enable_memory: bool = Field(default=True, description="메모리 활성화 여부")
    enable_streaming: bool = Field(default=False, description="스트리밍 응답 (확장)")
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
    """Agent 요청"""
    question: str = Field(..., min_length=1, max_length=1000, description="질문")
    session_id: Optional[str] = Field(None, description="세션 ID (멀티턴 대화)")
    config: Optional[AgentConfig] = Field(default_factory=AgentConfig, description="Agent 설정")
    verbose: bool = Field(default=False, description="상세 로그 출력")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "2024년 입사자 중 재택근무 정책을 준수하는 사람은 몇 명이고 평균 급여는?",
                "session_id": "user123-session456",
                "config": {
                    "max_iterations": 10,
                    "enable_memory": True
                },
                "verbose": True
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

    class Config:
        json_schema_extra = {
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


class AgentMetrics(BaseModel):
    """
    [DEPRECATED] Agent 성능 메트릭

    이 클래스는 더 이상 사용되지 않습니다.
    InMemorySaver는 자동 메트릭 추적을 제공하지 않습니다.

    상세 메트릭이 필요한 경우 Prometheus, OpenTelemetry 등 별도 시스템 사용 권장

    보존 이유: 기존 코드와의 호환성 유지
    """
    session_id: str
    total_requests: int = 0
    total_iterations: int = 0
    total_tools_called: int = 0
    avg_response_time_ms: float = 0.0
    success_rate: float = 0.0
    tool_usage: Dict[str, int] = Field(default_factory=dict)  # {tool_name: count}
    error_types: Dict[str, int] = Field(default_factory=dict)  # {error_type: count}

    def record_request(
        self,
        iterations: int,
        tools_used: List[str],
        response_time_ms: int,
        success: bool,
        error_type: Optional[str] = None
    ):
        """요청 메트릭 기록"""
        self.total_requests += 1
        self.total_iterations += iterations
        self.total_tools_called += len(tools_used)

        # 평균 응답 시간 업데이트
        total_time = self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms
        self.avg_response_time_ms = total_time / self.total_requests

        # 성공률 업데이트
        if success:
            success_count = int(self.success_rate * (self.total_requests - 1)) + 1
            self.success_rate = success_count / self.total_requests
        else:
            success_count = int(self.success_rate * (self.total_requests - 1))
            self.success_rate = success_count / self.total_requests

        # 도구 사용 통계
        for tool in tools_used:
            self.tool_usage[tool] = self.tool_usage.get(tool, 0) + 1

        # 에러 타입 통계
        if error_type:
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1


class SessionMemoryStore:
    """
    [DEPRECATED] 세션별 메모리 저장소 (싱글톤)

    이 클래스는 더 이상 사용되지 않습니다.
    InMemorySaver가 LangGraph의 checkpointer로 대화 히스토리를 관리합니다.

    보존 이유: 기존 코드와의 호환성 유지 (향후 제거 예정)

    마이그레이션:
    - LangGraph의 InMemorySaver 사용
    - thread_id를 통한 세션 관리
    - checkpointer.get(config) / checkpointer.storage로 접근
    """
    _instance = None
    _memories: Dict[str, AgentMemory] = {}
    _metrics: Dict[str, AgentMetrics] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_memory(self, session_id: str) -> AgentMemory:
        """[DEPRECATED] 메모리 가져오기 (없으면 생성)"""
        if session_id not in self._memories:
            self._memories[session_id] = AgentMemory(session_id=session_id)
        return self._memories[session_id]

    def clear_memory(self, session_id: str):
        """[DEPRECATED] 메모리 삭제"""
        if session_id in self._memories:
            del self._memories[session_id]

    def get_metrics(self, session_id: str) -> AgentMetrics:
        """[DEPRECATED] 메트릭 가져오기 (없으면 생성)"""
        if session_id not in self._metrics:
            self._metrics[session_id] = AgentMetrics(session_id=session_id)
        return self._metrics[session_id]

    def list_sessions(self) -> List[str]:
        """[DEPRECATED] 활성 세션 목록"""
        return list(self._memories.keys())

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        [DEPRECATED] 오래된 세션 정리
        """
        pass


# [DEPRECATED] 글로벌 메모리 저장소 인스턴스
# InMemorySaver로 마이그레이션됨
# 이 인스턴스는 하위 호환성을 위해서만 유지됨
session_memory_store = SessionMemoryStore()
