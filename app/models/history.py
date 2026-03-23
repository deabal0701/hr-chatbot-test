"""
API 요청 이력 스키마

위치: app/models/history.py
API 요청 이력 및 실행 추적 관련 모델 (멀티테넌트/사용자별 지원)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HistoryTraceAgent(BaseModel):
    """Agent 실행 추적 데이터"""
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="실행 단계들")
    tools_used: List[str] = Field(default_factory=list, description="사용된 도구 목록")
    iteration_count: int = Field(0, description="반복 횟수")
    intent_analysis: Optional[Dict[str, Any]] = Field(None, description="의도 분석 결과")


class HistoryTraceNL2SQL(BaseModel):
    """NL2SQL 실행 추적 데이터"""
    sql: Optional[str] = Field(None, description="생성된 SQL")
    sql_result: Optional[Dict[str, Any]] = Field(None, description="SQL 실행 결과")
    current_turn: int = Field(1, description="현재 턴 번호")
    validation_passed: bool = Field(True, description="검증 통과 여부")
    validation_errors: Optional[List[str]] = Field(None, description="검증 오류 목록")


class HistoryTraceRAG(BaseModel):
    """RAG 실행 추적 데이터"""
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="참조 문서 목록")
    sources_count: int = Field(0, description="참조 문서 수")
    top_similarity: Optional[float] = Field(None, description="최고 유사도 점수")


class HistoryRecord(BaseModel):
    """API 요청 이력 레코드"""
    id: int = Field(..., description="레코드 ID")

    # 멀티테넌트 및 사용자
    tenant_id: Optional[str] = Field(None, description="테넌트 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    user_name: Optional[str] = Field(None, description="사용자 표시명")

    # 요청 식별
    request_id: str = Field(..., description="요청 ID (8자 UUID)")
    session_id: Optional[str] = Field(None, description="세션 ID")

    # 요청 분류
    request_type: str = Field(..., description="요청 타입 (agent/nl2sql/rag)")
    endpoint: str = Field(..., description="API 엔드포인트")

    # 요청/응답
    question: str = Field(..., description="원본 질문")
    answer: Optional[str] = Field(None, description="최종 답변")
    response_code: int = Field(200, description="HTTP 상태 코드")
    success: bool = Field(True, description="성공 여부")
    error_message: Optional[str] = Field(None, description="에러 메시지")

    # 추적 데이터
    trace_data: Optional[Dict[str, Any]] = Field(None, description="실행 추적 데이터")

    # 성능
    response_time_ms: int = Field(0, description="응답 시간 (ms)")
    llm_calls_count: Optional[int] = Field(None, description="LLM 호출 횟수")
    tokens_used: Optional[int] = Field(None, description="사용된 토큰 수")

    # 클라이언트
    client_ip: Optional[str] = Field(None, description="클라이언트 IP")

    # 타임스탬프
    created_at: datetime = Field(..., description="생성 시각")
    completed_at: Optional[datetime] = Field(None, description="완료 시각")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "tenant_id": "company_a",
                "user_id": "user123",
                "user_name": "홍길동",
                "request_id": "abc12345",
                "session_id": "session-abc12345",
                "request_type": "agent",
                "endpoint": "/api/v1/agent/search",
                "question": "2024년 입사자 수는?",
                "answer": "2024년 입사자는 총 27명입니다.",
                "response_code": 200,
                "success": True,
                "trace_data": {
                    "steps": [{"step": 1, "action": "query_database_tool"}],
                    "tools_used": ["query_database_tool"],
                    "iteration_count": 1
                },
                "response_time_ms": 1523,
                "created_at": "2024-01-04T10:30:00+09:00"
            }
        }
    }


class HistoryListRequest(BaseModel):
    """이력 조회 요청 파라미터"""
    # 멀티테넌트/사용자 필터
    tenant_id: Optional[str] = Field(None, description="테넌트 ID 필터")
    user_id: Optional[str] = Field(None, description="사용자 ID 필터 (내 이력 조회)")

    # 기본 필터
    request_type: Optional[str] = Field(None, description="요청 타입 (agent/nl2sql/rag)")
    title: Optional[str] = Field(None, description="제목(질문) 검색")
    success_only: Optional[bool] = Field(None, description="성공한 요청만 조회")

    # 날짜 필터
    from_date: Optional[datetime] = Field(None, description="시작일")
    to_date: Optional[datetime] = Field(None, description="종료일")

    # 페이징
    limit: int = Field(100, ge=1, le=1000, description="조회 개수")
    offset: int = Field(0, ge=0, description="오프셋")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_id": "company_a",
                "user_id": "user123",
                "request_type": "agent",
                "from_date": "2024-01-01T00:00:00",
                "limit": 50,
                "offset": 0
            }
        }
    }


class HistoryListResponse(BaseModel):
    """이력 목록 조회 응답"""
    total: int = Field(..., description="전체 레코드 수")
    items: List[HistoryRecord] = Field(default_factory=list, description="이력 레코드 목록")

    # 페이징 정보
    limit: int = Field(..., description="요청된 limit")
    offset: int = Field(..., description="요청된 offset")
    has_more: bool = Field(False, description="추가 데이터 존재 여부")


class HistoryStatistics(BaseModel):
    """이력 통계"""
    # 전체 통계
    total_requests: int = Field(0, description="총 요청 수")
    success_count: int = Field(0, description="성공 요청 수")
    error_count: int = Field(0, description="실패 요청 수")
    success_rate: float = Field(0.0, description="성공률 (%)")

    # 타입별 통계
    agent_count: int = Field(0, description="Agent 요청 수")
    nl2sql_count: int = Field(0, description="NL2SQL 요청 수")
    rag_count: int = Field(0, description="RAG 요청 수")

    # 성능 통계
    avg_response_time_ms: float = Field(0.0, description="평균 응답 시간 (ms)")
    min_response_time_ms: Optional[int] = Field(None, description="최소 응답 시간 (ms)")
    max_response_time_ms: Optional[int] = Field(None, description="최대 응답 시간 (ms)")

    # 기간 정보
    from_date: Optional[datetime] = Field(None, description="통계 시작일")
    to_date: Optional[datetime] = Field(None, description="통계 종료일")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_requests": 1523,
                "success_count": 1498,
                "error_count": 25,
                "success_rate": 98.36,
                "agent_count": 523,
                "nl2sql_count": 678,
                "rag_count": 322,
                "avg_response_time_ms": 1245.5,
                "min_response_time_ms": 234,
                "max_response_time_ms": 8756
            }
        }
    }


class HistoryUserSummary(BaseModel):
    """사용자별 이력 요약 (내 이력)"""
    user_id: str = Field(..., description="사용자 ID")
    user_name: Optional[str] = Field(None, description="사용자 표시명")

    # 사용 통계
    total_requests: int = Field(0, description="총 요청 수")
    recent_requests: List[HistoryRecord] = Field(default_factory=list, description="최근 요청 목록")

    # 타입별 사용량
    agent_count: int = Field(0, description="Agent 사용 횟수")
    nl2sql_count: int = Field(0, description="NL2SQL 사용 횟수")
    rag_count: int = Field(0, description="RAG 사용 횟수")

    # 기간
    first_request_at: Optional[datetime] = Field(None, description="첫 요청 시각")
    last_request_at: Optional[datetime] = Field(None, description="마지막 요청 시각")
