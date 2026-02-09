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

# NL2SQL 노드 표시 레이블(전체 노드를 모두 표시하는 경우)
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

# NL2SQL 노드 표시 레이블(스테이지별 표시하는 경우)
# NL2SQL: 노드 → 스테이지 번호 매핑
NL2SQL_NODE_STAGE = {
    "load_history": 1,       # 1단계: 질문 분석
    "intent_rewrite": 1,     # 1단계: 질문 분석
    "schema_retrieval": 2,   # 2단계: 데이터 검색 준비
    "fewshot_retrieval": 2,  # 2단계: 데이터 검색 준비
    "prompt_build": 2,       # 2단계: 데이터 검색 준비
    "sql_generate": 3,       # 3단계: SQL 생성 및 실행
    "validate_sql": 3,       # 3단계: SQL 생성 및 실행
    "execute_sql": 3,        # 3단계: SQL 생성 및 실행
    "pii_filter": 3,         # 3단계: SQL 생성 및 실행
    "prepare_retry": 3,      # 3단계: SQL 생성 및 실행 (재시도)
    "generate_answer": 4,    # 4단계: 답변 생성
    "save_history": 4,       # 4단계: 답변 생성
    "sql_not_needed": 4,     # 4단계: 답변 생성 (이전 결과 활용)
    "handle_error": 4,       # 4단계: 답변 생성 (에러 처리)
}

# NL2SQL: 스테이지 번호 → 표시 레이블 매핑
NL2SQL_STAGE_LABELS = {
    1: {"start": "질문을 분석하고 의도를 파악하고 있습니다...", "complete": "질문 분석 및 의도 파악 완료"},
    2: {"start": "관련 테이블 스키마와 유사 질문을 검색하고 있습니다...", "complete": "테이블 스키마 및 유사 질문 검색 완료"},
    3: {"start": "SQL을 생성하고 검증 후 실행하고 있습니다...", "complete": "SQL 생성, 검증 및 실행 완료"},
    4: {"start": "조회 결과를 바탕으로 답변을 생성하고 있습니다...", "complete": "답변 생성 완료"},
}

# Agent: 노드 → 스테이지 번호 매핑
# Agent는 노드가 3개뿐이므로 각 노드 = 각 스테이지
AGENT_NODE_STAGE = {
    "agent": 1,   # 1단계: AI 추론
    "tools": 2,   # 2단계: 도구 실행
    "answer": 3,  # 3단계: 답변 생성
}

# Agent: 스테이지 번호 → 표시 레이블 매핑
AGENT_STAGE_LABELS = {
    1: {"start": "AI가 질문을 분석하고 실행 계획을 수립하고 있습니다...", "complete": "질문 분석 및 실행 계획 수립 완료"},
    2: {"start": "데이터베이스 조회 및 문서 검색 도구를 실행하고 있습니다...", "complete": "도구 실행 및 결과 수집 완료"},
    3: {"start": "수집된 결과를 종합하여 최종 답변을 생성하고 있습니다...", "complete": "최종 답변 생성 완료"},
}