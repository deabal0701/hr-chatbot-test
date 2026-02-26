"""
하이브리드 검색 엔진 (Vector + pg_trgm + RRF)

위치: app/core/vector/hybrid_search.py

기능:
- search_mode 설정에 따라 벡터 전용 또는 하이브리드 검색 수행
- 하이브리드: 벡터 + pg_trgm 각각 fetch_k개 후보 → RRF 융합 → top_k 반환
- direct_lookup: Doc ID 패턴 감지 시 ILIKE 직접 조회 (벡터/키워드 생략)
- 키워드 검색 실패 시 벡터 검색 결과로 자동 폴백

RRF (Reciprocal Rank Fusion):
  score(d) = 1/(k + rank_vector) + 1/(k + rank_keyword)
  k=60 (논문·산업 표준값)
"""
from typing import Dict, List, Optional

from app.models.rag import DocumentSource
from app.models.search import SearchFilters
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_config = None
_vector_store = None


def _get_settings_config():
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from app.core.vector.vector_store import vector_store
        _vector_store = vector_store
    return _vector_store


class HybridSearchEngine:
    """하이브리드 검색 엔진 (Vector + pg_trgm + RRF)"""

    def search(
        self,
        vector_query: str,
        keyword_query: str,
        top_k: int,
        filters: Optional[SearchFilters],
        similarity_threshold: float,
        tenant_id: Optional[str],
        search_type: str = "normal",
        doc_pattern: Optional[str] = None,
        request_id: str = "unknown",
    ) -> List[DocumentSource]:
        """
        하이브리드 검색 실행

        Args:
            vector_query:        벡터 검색용 쿼리 (원본 질의)
            keyword_query:       pg_trgm 검색용 쿼리 (추출 키워드)
            top_k:               최종 반환 문서 수
            filters:             검색 필터
            similarity_threshold: 벡터 검색 유사도 임계값
            tenant_id:           테넌트 격리
            search_type:         "normal" | "direct_lookup"
            doc_pattern:         direct_lookup 시 식별자 패턴 (예: "HR-001")
            request_id:          로그용 요청 ID

        Returns:
            검색 결과 DocumentSource 리스트 (최대 top_k개)
        """
        vs = _get_vector_store()
        sc = _get_settings_config()

        # 1. 직접 조회 (Doc ID 패턴 감지됨)
        if search_type == "direct_lookup" and doc_pattern:
            log_step(logger, request_id, "RAG", "1", "RETRIEVE", "직접 조회", pattern=doc_pattern)
            return vs.search_by_pattern(doc_pattern, filters, tenant_id)

        # 2. 검색 모드 확인 (DB 설정, 기본값 "hybrid")
        search_mode = sc.get_value("rag", "search_mode", "hybrid")

        if search_mode == "vector":
            log_step(logger, request_id, "RAG", "1", "RETRIEVE", "벡터 검색 전용 모드")
            return vs.search_similar_documents(vector_query, top_k, filters, similarity_threshold, tenant_id)

        # 3. 하이브리드 검색
        fetch_k_factor = int(sc.get_value("rag", "hybrid_fetch_k_factor", 2))
        rrf_k = int(sc.get_value("rag", "hybrid_rrf_k", 60))
        fetch_k = top_k * fetch_k_factor

        log_step(logger, request_id, "RAG", "1", "RETRIEVE", "하이브리드 검색 시작",
                 vector_query=vector_query[:40], keyword_query=keyword_query[:40], fetch_k=fetch_k)

        # 벡터 검색
        vector_docs = vs.search_similar_documents(
            vector_query, fetch_k, filters, similarity_threshold, tenant_id
        )

        # 키워드 검색 (pg_trgm 미활성화 등 오류 시 빈 리스트로 폴백)
        keyword_docs: List[DocumentSource] = []
        try:
            keyword_docs = vs.search_by_keyword(keyword_query, fetch_k, filters, tenant_id)
        except Exception as e:
            log_step(logger, request_id, "RAG", "1", "RETRIEVE",
                     f"키워드 검색 실패 → 벡터 결과만 사용: {e}", level="WARNING")

        log_step(logger, request_id, "RAG", "1", "RETRIEVE", "RRF 병합",
                 vector_docs=len(vector_docs), keyword_docs=len(keyword_docs), top_k=top_k)

        return self._rrf_merge(vector_docs, keyword_docs, top_k, rrf_k)

    def _rrf_merge(
        self,
        vector_docs: List[DocumentSource],
        keyword_docs: List[DocumentSource],
        top_k: int,
        rrf_k: int,
    ) -> List[DocumentSource]:
        """
        RRF (Reciprocal Rank Fusion) 점수 계산 및 병합

        score(d) = 1/(k + rank_vector) + 1/(k + rank_keyword)
        두 검색 결과의 합집합 대상으로 점수 합산 후 상위 top_k 반환.
        """
        scores: Dict[int, float] = {}
        doc_map: Dict[int, DocumentSource] = {}

        for rank, doc in enumerate(vector_docs, 1):
            scores[doc.id] = scores.get(doc.id, 0.0) + 1.0 / (rrf_k + rank)
            doc_map[doc.id] = doc

        for rank, doc in enumerate(keyword_docs, 1):
            scores[doc.id] = scores.get(doc.id, 0.0) + 1.0 / (rrf_k + rank)
            if doc.id not in doc_map:
                doc_map[doc.id] = doc

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

        # RRF는 정렬(순서 결정)에만 사용, similarity_score는 원본 벡터 유사도 유지
        result = []
        for doc_id in sorted_ids:
            result.append(doc_map[doc_id])

        return result


# 싱글톤 인스턴스
hybrid_search = HybridSearchEngine()
