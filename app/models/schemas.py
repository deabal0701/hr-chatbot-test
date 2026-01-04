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


class DocumentCreateWithChunking(BaseModel):
    """문서 생성 (자동 청킹 지원)"""
    title: str = Field(..., min_length=1, max_length=500, description="문서 제목")
    doc_type: str = Field(..., description="문서 유형 (policy, guide, faq, notice)")
    content: str = Field(..., min_length=1, description="문서 내용")
    language: str = Field(default="ko", description="언어 (ko, en)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")
    auto_chunk: bool = Field(default=True, description="자동 청킹 여부")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="청크 크기 (문자 수)")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="청크 간 중복 (문자 수)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "2024년 보안 규정",
                "doc_type": "policy",
                "content": "제1조 목적... (긴 텍스트를 입력하세요)",
                "language": "ko",
                "metadata": {"year": 2024, "department": "Security"},
                "auto_chunk": True,
                "chunk_size": 1000,
                "chunk_overlap": 100
            }
        }
    }


class DocumentCreateResponse(BaseModel):
    """문서 생성 응답 (청킹 지원)"""
    success: bool
    message: str
    parent_id: int
    chunk_ids: List[int]
    total_chunks: int
    total_chars: int


class ChunkPreviewRequest(BaseModel):
    """청킹 미리보기 요청"""
    content: str = Field(..., min_length=1, description="문서 내용")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="청크 크기")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="청크 간 중복")


class ChunkPreviewItem(BaseModel):
    """청킹 미리보기 항목"""
    index: int
    length: int
    preview: str


class ChunkPreviewResponse(BaseModel):
    """청킹 미리보기 응답"""
    original_length: int
    total_chunks: int
    chunks: List[ChunkPreviewItem]


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


class DocumentListItem(BaseModel):
    """문서 목록 항목"""
    id: int
    title: str
    doc_type: str
    language: str
    content_length: int
    source_type: Optional[str] = None
    source_file: Optional[str] = None
    total_chunks: Optional[int] = None
    indexed: bool = False
    embedded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    total: int
    documents: List[DocumentListItem]


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답"""
    success: bool
    message: str
    deleted_count: int


# ===================================
# 청킹 실행 관련 스키마
# ===================================

class ChunkExecuteRequest(BaseModel):
    """청킹 실행 요청"""
    doc_ids: List[int] = Field(..., min_length=1, description="청킹할 문서 ID 목록")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="청크 크기 (문자 수)")
    chunk_overlap: int = Field(default=100, ge=0, le=500, description="청크 간 중복 (문자 수)")
    delete_original: bool = Field(default=False, description="원본 문서 삭제 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "doc_ids": [1, 2, 3],
                "chunk_size": 1000,
                "chunk_overlap": 100,
                "delete_original": False
            }
        }
    }


class ChunkExecuteResultItem(BaseModel):
    """청킹 실행 결과 항목"""
    original_doc_id: int
    original_title: str
    success: bool
    error: Optional[str] = None
    parent_id: Optional[int] = None
    chunk_ids: List[int] = Field(default_factory=list)
    total_chunks: int = 0
    original_chars: int = 0


class ChunkExecuteResponse(BaseModel):
    """청킹 실행 응답"""
    success: bool
    message: str
    total_requested: int
    total_success: int
    total_failed: int
    results: List[ChunkExecuteResultItem]


class DocumentSaveRequest(BaseModel):
    """문서 저장 요청 (임베딩 없이 저장)"""
    title: str = Field(..., min_length=1, max_length=500, description="문서 제목")
    doc_type: str = Field(..., description="문서 유형 (policy, guide, faq, notice)")
    content: str = Field(..., min_length=1, description="문서 내용")
    language: str = Field(default="ko", description="언어 (ko, en)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")
    source_type: str = Field(default="ui_input", description="소스 타입 (ui_input, pdf, web, api)")
    source_file: Optional[str] = Field(default=None, description="원본 파일명")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "2024년 운영 가이드",
                "doc_type": "guide",
                "content": "본 가이드는 시스템 운영 절차를 설명합니다...",
                "language": "ko",
                "metadata": {"year": 2024, "department": "IT"},
                "source_type": "ui_input"
            }
        }
    }


class DocumentSaveResponse(BaseModel):
    """문서 저장 응답"""
    success: bool
    message: str
    doc_id: int
    title: str
    content_length: int
    needs_chunking: bool
    recommended_chunks: int


class DocumentUpdateRequest(BaseModel):
    """문서 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="문서 제목")
    doc_type: Optional[str] = Field(None, description="문서 유형")
    content: Optional[str] = Field(None, min_length=1, description="문서 내용")
    language: Optional[str] = Field(None, description="언어 (ko, en)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "2024년 인사규정 (수정)",
                "content": "제1조 목적... (수정된 내용)"
            }
        }
    }


class DocumentUpdateResponse(BaseModel):
    """문서 수정 응답"""
    success: bool
    message: str
    doc_id: int
    title: str
    content_length: int
    embedding_invalidated: bool
    needs_reindex: bool


class BulkDeleteRequest(BaseModel):
    """일괄 삭제 요청"""
    doc_ids: List[int] = Field(..., min_length=1, description="삭제할 문서 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "doc_ids": [1, 2, 3]
            }
        }
    }


class BulkDeleteResponse(BaseModel):
    """일괄 삭제 응답"""
    success: bool
    message: str
    total_requested: int
    total_deleted: int
    failed_ids: List[int] = Field(default_factory=list)


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


# ===================================
# 시스템 설정 관련 스키마
# ===================================

class SettingItem(BaseModel):
    """개별 설정 항목"""
    category: str
    key: str
    value: str
    value_type: str = "string"
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: Optional[datetime] = None


class SettingItemResponse(BaseModel):
    """설정 항목 응답 (마스킹 처리)"""
    category: str
    key: str
    value: str  # is_secret=True인 경우 마스킹됨
    value_type: str
    description: Optional[str] = None
    is_secret: bool = False
    updated_at: Optional[datetime] = None


class SettingsCategoryResponse(BaseModel):
    """카테고리별 설정 응답"""
    category: str
    settings: List[SettingItemResponse]


class AllSettingsResponse(BaseModel):
    """전체 설정 응답"""
    categories: List[SettingsCategoryResponse]


class SettingUpdateRequest(BaseModel):
    """단일 설정 수정 요청"""
    value: str = Field(..., description="설정 값")

    model_config = {
        "json_schema_extra": {
            "example": {
                "value": "gpt-4-turbo"
            }
        }
    }


class SettingsBulkUpdateRequest(BaseModel):
    """카테고리별 설정 일괄 수정 요청"""
    settings: Dict[str, str] = Field(..., description="key-value 쌍")

    model_config = {
        "json_schema_extra": {
            "example": {
                "settings": {
                    "model": "gpt-4-turbo",
                    "temperature": "0.2",
                    "max_tokens": "3000"
                }
            }
        }
    }


class SettingsUpdateResponse(BaseModel):
    """설정 수정 응답"""
    success: bool
    message: str
    updated_count: int = 0


class ApiKeyValidationRequest(BaseModel):
    """API 키 검증 요청"""
    api_key: str = Field(..., min_length=1, description="검증할 API Key")


class ApiKeyValidationResponse(BaseModel):
    """API 키 검증 응답"""
    valid: bool
    message: str
    models: Optional[List[str]] = None  # 사용 가능한 모델 목록
