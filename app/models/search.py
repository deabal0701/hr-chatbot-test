"""
검색 API 스키마

통합 검색 요청/응답 및 필터 관련 모델
RAG, NL2SQL, Auto 모드 모두 지원
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .rag import DocumentSource, SQLResult


class SearchFilters(BaseModel):
    """검색 필터"""
    usage_type: Optional[str] = Field(default="rag_knowledge", description="문서 용도 (rag_knowledge/rag_action)")
    from_date: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    department: Optional[str] = Field(None, description="부서")
    location: Optional[str] = Field(None, description="근무지")
    language: Optional[str] = Field(default="ko", description="언어 (ko/en)")
    doc_type: Optional[str] = Field(None, description="문서 타입")


class SearchRequest(BaseModel):
    """검색 요청"""
    query: str = Field(..., min_length=1, description="검색 질의")
    mode: str = Field(default="auto", description="검색 모드 (auto/rag/nl2sql)")
    filters: Optional[SearchFilters] = Field(default_factory=SearchFilters)
    session_id: Optional[str] = Field(None, description="세션 ID (멀티턴 대화용, 없으면 자동 생성)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "2024년에 서울에서 근무하는 개발자 입사자 수는?",
                "mode": "auto",
                "filters": {
                    "from_date": "2024-01-01",
                    "to_date": "2024-12-31",
                    "department": "개발",
                    "location": "서울"
                },
                "session_id": "nl2sql-abc123"
            }
        }
    }


class ExcelExportRequest(BaseModel):
    """Excel 내보내기 요청"""
    columns: List[str] = Field(..., description="컬럼 목록")
    rows: List[Dict[str, Any]] = Field(..., description="데이터 행 목록")
    question: Optional[str] = Field(default="", description="사용자 질문")
    sql: Optional[str] = Field(default="", description="실행된 SQL")
    answer: Optional[str] = Field(default="", description="AI 답변")
    execution_time_ms: Optional[int] = Field(default=0, description="SQL 실행 시간(ms)")


class SearchResponse(BaseModel):
    """
    통합 검색 응답

    모든 검색 모드(rag, nl2sql, auto)에서 동일한 응답 구조를 사용.
    query_type에 따라 관련 필드만 값이 채워짐.
    """
    # ========== 공통 필드 (항상 존재) ==========
    query: str = Field(..., description="원본 검색 질의")
    answer: str = Field(..., description="자연어 답변")
    query_type: str = Field(..., description="검색 타입 (rag, nl2sql, auto)")
    response_time_ms: int = Field(..., description="응답 시간 (밀리초)")

    # ========== NL2SQL 전용 (nl2sql일 때만 값 존재) ==========
    sql: Optional[str] = Field(None, description="생성된 SQL 쿼리")
    sql_result: Optional[SQLResult] = Field(None, description="SQL 실행 결과")

    # ========== RAG 전용 (rag일 때만 값 존재) ==========
    sources: Optional[List[DocumentSource]] = Field(None, description="참고 문서 목록")

    # ========== 멀티턴 대화 ==========
    session_id: Optional[str] = Field(None, description="세션 ID (멀티턴 대화용)")

    # ========== 메타데이터 ==========
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "2024년 입사자 수는?",
                "answer": "2024년에 총 27명이 입사했습니다.",
                "query_type": "nl2sql",
                "response_time_ms": 1523,
                "sql": "SELECT COUNT(*) FROM employee WHERE YEAR(hire_date) = 2024",
                "sql_result": {
                    "columns": ["count"],
                    "rows": [{"count": 27}],
                    "row_count": 1,
                    "execution_time_ms": 45
                },
                "sources": None,
                "session_id": "nl2sql-abc123",
                "metadata": {"model": "gpt-4o", "current_turn": 1, "max_turns": 5}
            }
        }
    }
