"""
RAG State 정의

RAG 그래프에서 사용하는 상태(State) 타입을 정의합니다.
"""

from typing import Any, Dict, List, Optional, TypedDict

from app.models.rag import DocumentSource


class RAGState(TypedDict):
    """RAG Graph 상태"""

    # ===== 기본 필드 =====
    question: str
    filters: Dict[str, Any]
    top_k: int
    retrieved_docs: List[DocumentSource]
    answer: str
    metadata: Dict[str, Any]
    request_id: str

    # ===== 테넌트 격리 (Phase 3) =====
    tenant_id: Optional[str]

    # ===== 하이브리드 검색 (query_analysis_node 출력) =====
    vector_query: Optional[str]   # 벡터 검색용 (= 원본 question)
    keyword_query: Optional[str]  # pg_trgm 검색용 (추출 키워드)
    search_type: Optional[str]    # "normal" | "direct_lookup"
    doc_pattern: Optional[str]    # direct_lookup 시 식별자 (예: "HR-001")


def create_initial_state(
    question: str,
    request_id: str = "unknown",
    filters: Dict[str, Any] = None,
    top_k: int = None,
    tenant_id: Optional[str] = None,
) -> RAGState:
    """
    초기 상태 생성

    Args:
        question: 사용자 질문
        request_id: 요청 ID
        filters: 검색 필터
        top_k: 검색 문서 수

    Returns:
        초기화된 RAGState
    """
    from app.core.llm.llm_config import LLMConfigManager
    rag_settings = LLMConfigManager.get_rag_settings()

    return RAGState(
        question=question,
        filters=filters or {},
        top_k=top_k or rag_settings["top_k"],
        retrieved_docs=[],
        answer="",
        metadata={},
        request_id=request_id,
        tenant_id=tenant_id,
        vector_query=None,
        keyword_query=None,
        search_type=None,
        doc_pattern=None,
    )
