"""
문서 관리 스키마

문서 CRUD, 청킹, 임베딩 관련 모든 모델
Inner class를 사용하여 관련 스키마를 그룹화
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===================================
# 문서 생성/저장
# ===================================

class DocumentCreate(BaseModel):
    """문서 생성 (기본)"""
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


class DocumentSaveRequest(BaseModel):
    """문서 저장 요청 (임베딩 없이 저장)"""
    title: str = Field(..., min_length=1, max_length=500, description="문서 제목")
    doc_type: str = Field(..., description="문서 유형 (policy, guide, faq, notice)")
    content: str = Field(..., min_length=1, description="문서 내용")
    language: str = Field(default="ko", description="언어 (ko, en)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")
    context_data: Optional[str] = Field(default=None, description="임베딩 제외 컨텍스트 데이터 (SQL, 스키마 등 Agent 참조용)")
    source_type: str = Field(default="ui_input", description="소스 타입 (ui_input, pdf, web, api)")
    source_file: Optional[str] = Field(default=None, description="원본 파일명")
    usage_type: str = Field(default="rag_knowledge", description="문서 용도 (rag_knowledge, rag_action)")
    tenant_id: Optional[str] = Field(default=None, description="소속 테넌트 ID (GLOBAL: 선택, TENANT: 자동 부여)")

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


# ===================================
# 문서 조회/응답
# ===================================

class DocumentResponse(BaseModel):
    """문서 상세 응답"""
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
    usage_type: str = "rag_knowledge"  # 문서 용도 (rag_knowledge, rag_action)
    language: str
    content_length: int
    original_length: Optional[int] = None  # 원본 문서 전체 길이 (청킹된 경우 원본 길이)
    source_type: Optional[str] = None
    source_file: Optional[str] = None
    total_chunks: Optional[int] = None
    indexed: bool = False
    embedded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tenant_id: Optional[str] = None  # 소속 테넌트 ID ('1'=공용)


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""
    total: int
    items: List[DocumentListItem]


# ===================================
# 문서 수정/삭제
# ===================================

class DocumentUpdateRequest(BaseModel):
    """문서 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="문서 제목")
    doc_type: Optional[str] = Field(None, description="문서 유형")
    content: Optional[str] = Field(None, min_length=1, description="문서 내용")
    language: Optional[str] = Field(None, description="언어 (ko, en)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    context_data: Optional[str] = Field(None, description="임베딩 제외 컨텍스트 데이터 (SQL, 스키마 등 Agent 참조용)")

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


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답"""
    success: bool
    message: str
    deleted_count: int


class BulkDelete:
    """일괄 삭제 관련 스키마 그룹 (Inner Class 패턴)"""

    class Request(BaseModel):
        """일괄 삭제 요청"""
        doc_ids: List[int] = Field(..., min_length=1, description="삭제할 문서 ID 목록")

        model_config = {
            "json_schema_extra": {
                "example": {
                    "doc_ids": [1, 2, 3]
                }
            }
        }

    class Response(BaseModel):
        """일괄 삭제 응답"""
        success: bool
        message: str
        total_requested: int
        total_deleted: int
        failed_ids: List[int] = Field(default_factory=list)


# ===================================
# 청킹(Chunking) 관련
# ===================================

class Chunking:
    """청킹 관련 스키마 그룹 (Inner Class 패턴)"""

    class PreviewRequest(BaseModel):
        """청킹 미리보기 요청"""
        content: str = Field(..., min_length=1, description="문서 내용")
        chunk_size: int = Field(default=1000, ge=100, le=5000, description="청크 크기")
        chunk_overlap: int = Field(default=100, ge=0, le=500, description="청크 간 중복")

    class PreviewItem(BaseModel):
        """청킹 미리보기 항목"""
        index: int
        length: int
        preview: str

    class PreviewResponse(BaseModel):
        """청킹 미리보기 응답"""
        original_length: int
        total_chunks: int
        chunks: List["Chunking.PreviewItem"]

    class ExecuteRequest(BaseModel):
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

    class ExecuteResultItem(BaseModel):
        """청킹 실행 결과 항목"""
        original_doc_id: int
        original_title: str
        success: bool
        error: Optional[str] = None
        parent_id: Optional[int] = None
        chunk_ids: List[int] = Field(default_factory=list)
        total_chunks: int = 0
        original_chars: int = 0

    class ExecuteResponse(BaseModel):
        """청킹 실행 응답"""
        success: bool
        message: str
        total_requested: int
        total_success: int
        total_failed: int
        results: List["Chunking.ExecuteResultItem"]


# Pydantic v2에서 forward reference 해결
Chunking.PreviewResponse.model_rebuild()
Chunking.ExecuteResponse.model_rebuild()
