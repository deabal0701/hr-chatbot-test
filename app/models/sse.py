"""
SSE 이벤트 모델

위치: app/models/sse.py
- SSE 스트리밍 이벤트의 Pydantic 모델 정의
- Agent, NL2SQL 모드의 노드 진행 이벤트
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from datetime import datetime


class SSEEvent(BaseModel):
    """SSE 이벤트 기본 모델"""
    type: str = Field(..., description="이벤트 타입 (node_complete, complete, error)")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO 8601 타임스탬프")


class NodeStartEvent(SSEEvent):
    """노드 실행 시작 이벤트 (진행 중 표시)"""
    type: str = "node_start"
    node: str = Field(..., description="노드 이름")
    message: str = Field(..., description="사용자 표시 메시지 (예: 'SQL 생성 중...')")
    step: int = Field(..., description="현재 단계 번호")


class NodeCompleteEvent(SSEEvent):
    """노드 실행 완료 이벤트"""
    type: str = "node_complete"
    node: str = Field(..., description="노드 이름")
    message: str = Field(..., description="사용자 표시 메시지")
    step: int = Field(..., description="현재 단계 번호")
    detail: Optional[Dict[str, Any]] = Field(None, description="노드 결과 요약")


class CompleteEvent(SSEEvent):
    """최종 완료 이벤트 (전체 응답 포함)"""
    type: str = "complete"
    data: Dict[str, Any] = Field(..., description="전체 응답 데이터")


class ErrorEvent(SSEEvent):
    """오류 이벤트"""
    type: str = "error"
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="에러 상세")


# Agent 노드 표시 레이블
AGENT_NODE_LABELS = {
    "agent": {"start": "AI 추론 중...", "complete": "AI 추론 완료"},
    "tools": {"start": "도구 실행 중...", "complete": "도구 실행 완료"},
    "answer": {"start": "답변 생성 중...", "complete": "답변 생성 완료"},
}

# NL2SQL 노드 표시 레이블
NL2SQL_NODE_LABELS = {
    "load_history": {"start": "대화 이력 로드 중...", "complete": "대화 이력 로드 완료"},
    "intent_rewrite": {"start": "질문 분석 중...", "complete": "질문 분석 완료"},
    "sql_not_needed": {"start": "이전 결과에서 답변 생성 중...", "complete": "이전 결과에서 답변 생성 완료"},
    "schema_retrieval": {"start": "스키마 검색 중...", "complete": "스키마 검색 완료"},
    "fewshot_retrieval": {"start": "유사 질문 검색 중...", "complete": "유사 질문 검색 완료"},
    "prompt_build": {"start": "프롬프트 구성 중...", "complete": "프롬프트 구성 완료"},
    "sql_generate": {"start": "SQL 생성 중...", "complete": "SQL 생성 완료"},
    "validate_sql": {"start": "SQL 검증 중...", "complete": "SQL 검증 완료"},
    "execute_sql": {"start": "SQL 실행 중...", "complete": "SQL 실행 완료"},
    "pii_filter": {"start": "개인정보 필터링 중...", "complete": "개인정보 필터링 완료"},
    "generate_answer": {"start": "답변 생성 중...", "complete": "답변 생성 완료"},
    "save_history": {"start": "이력 저장 중...", "complete": "이력 저장 완료"},
    "handle_error": {"start": "오류 처리 중...", "complete": "오류 처리 완료"},
    "prepare_retry": {"start": "재시도 준비 중...", "complete": "재시도 준비 완료"},
}
