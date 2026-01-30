"""
RAG/LLM 전용 스키마

LLM에 전달되는 문서 정보 및 SQL 결과 등
RAG 파이프라인에서 사용되는 데이터 모델
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DocumentSource(BaseModel):
    """
    RAG 검색 결과 문서

    LLM 컨텍스트 구성에 사용되는 문서 정보.
    content는 전체 내용, content_snippet은 미리보기용.
    context_data는 임베딩 제외 데이터 (SQL, 스키마 등 Agent 참조용).
    """
    id: int
    title: str
    doc_type: str
    content: str  # RAG 전체 내용 (LLM에 전달)
    content_snippet: str  # 미리보기용 스니펫 (API 응답, UI 표시)
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None
    context_data: Optional[str] = None  # 임베딩 제외 컨텍스트 (SQL, 패턴 등)


class SQLResult(BaseModel):
    """
    SQL 실행 결과

    NL2SQL에서 생성된 쿼리 실행 결과.
    RAG 응답과 함께 사용될 수 있음.
    """
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int
