from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===================================
# 공통 스키마
# ===================================

class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    success: bool = False


# ===================================
# 검색 관련 스키마
# ===================================

class SearchFilters(BaseModel):
    """검색 필터"""
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
    top_k: Optional[int] = Field(default=10, ge=1, le=50, description="상위 K개 결과")

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


class DocumentSource(BaseModel):
    """문서 출처"""
    id: int
    title: str
    doc_type: str
    content_snippet: str
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None


class RAGResponse(BaseModel):
    """RAG 검색 응답"""
    answer: str = Field(..., description="자연어 답변")
    sources: List[DocumentSource] = Field(default_factory=list, description="근거 문서")
    query_type: str = "rag"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SQLResult(BaseModel):
    """SQL 실행 결과"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int


class NL2SQLResponse(BaseModel):
    """NL2SQL 검색 응답"""
    answer: str = Field(..., description="자연어 요약")
    sql: str = Field(..., description="실행된 SQL")
    result: Optional[SQLResult] = None
    query_type: str = "nl2sql"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """통합 검색 응답"""
    query: str
    answer: str
    query_type: str  # 'rag', 'nl2sql', 'hybrid'
    rag_result: Optional[RAGResponse] = None
    nl2sql_result: Optional[NL2SQLResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    response_time_ms: int


# ===================================
# 문서 관련 스키마
# ===================================

class DocumentCreate(BaseModel):
    """문서 생성"""
    title: str
    doc_type: str
    language: str = "ko"
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    """문서 응답"""
    id: int
    title: str
    doc_type: str
    language: str
    content: str
    metadata: Dict[str, Any]
    indexed: bool
    created_at: datetime
    updated_at: datetime


# ===================================
# 로그 관련 스키마
# ===================================

class QueryLogCreate(BaseModel):
    """쿼리 로그 생성"""
    user_id: Optional[str] = None
    query_text: str
    query_type: str
    intent: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    response_time_ms: int
    success: bool = True
    error_message: Optional[str] = None


class QueryLogResponse(BaseModel):
    """쿼리 로그 응답"""
    id: int
    user_id: Optional[str]
    query_text: str
    query_type: str
    response_time_ms: int
    success: bool
    created_at: datetime


# ===================================
# HR 데이터 관련 스키마
# ===================================

class EmployeeInfo(BaseModel):
    """직원 정보"""
    emp_id: int
    emp_no: str
    name: str
    position: Optional[str] = None
    job_family: Optional[str] = None
    department_id: Optional[int] = None
    work_location: Optional[str] = None
    hire_date: Optional[str] = None
    status: str


class DepartmentInfo(BaseModel):
    """부서 정보"""
    dept_id: int
    dept_name: str
    dept_code: Optional[str] = None
    region: Optional[str] = None


# ===================================
# 통계 관련 스키마
# ===================================

class StatisticsRequest(BaseModel):
    """통계 요청"""
    metric: str = Field(..., description="통계 지표 (hire_count, resignation_count, etc)")
    group_by: Optional[str] = Field(None, description="그룹화 기준 (month, department, location)")
    filters: Optional[SearchFilters] = Field(default_factory=SearchFilters)


class StatisticsResponse(BaseModel):
    """통계 응답"""
    metric: str
    data: List[Dict[str, Any]]
    total: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
