"""
Agent 전용 스키마

Agent 요청/응답 및 실행 단계 관련 모델
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


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


class AgentConfig(BaseModel):
    """
    Agent 설정 (동적 조정 가능)

    확장 포인트:
    - 도구 선택 전략
    - LLM 모델 선택
    - 타임아웃 설정

    주의: llm_model은 None일 경우 DB 설정(tb_app_settings)에서 자동 로드됩니다.
    """
    max_iterations: int = Field(default=10, ge=1, le=20, description="최대 반복 횟수")
    llm_model: Optional[str] = Field(default=None, description="사용할 LLM 모델 (None=DB 설정 사용)")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM 온도")
    enable_memory: bool = Field(default=True, description="메모리 활성화 여부")
    enable_streaming: bool = Field(default=False, description="스트리밍 응답 (확장)")
    tools_whitelist: Optional[List[str]] = Field(None, description="사용 가능한 도구 목록 (None=전체)")
    tools_blacklist: Optional[List[str]] = Field(None, description="사용 금지 도구 목록")
    timeout_seconds: int = Field(default=60, ge=10, le=300, description="전체 타임아웃(초)")

    @model_validator(mode='after')
    def set_default_llm_model(self) -> 'AgentConfig':
        """llm_model이 None이면 DB 설정에서 로드"""
        if self.llm_model is None:
            # 순환 import 방지를 위해 함수 내부에서 import
            from app.core.config.settings_service import settings_service
            from app.config import settings
            from app.utils.logger import logger

            # DB 설정 → .env → 하드코딩 순서로 fallback
            self.llm_model = settings_service.get_value("llm", "model", settings.llm_model)
            logger.info(f"[AgentConfig] @model_validator: llm_model loaded from DB/env: {self.llm_model}")
        else:
            from app.utils.logger import logger
            logger.info(f"[AgentConfig] @model_validator: llm_model already set: {self.llm_model}")

        return self

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
