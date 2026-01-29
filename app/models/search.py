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
    top_k: Optional[int] = Field(default=None, ge=1, le=50, description="상위 K개 결과 (None이면 DB 설정 사용)")

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
                }
            }
        }
    }


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
                "metadata": {"model": "gpt-4o"}
            }
        }
    }
