"""벡터 검색 서비스 (pgvector 기반)

위치: app/core/vector/vector_store.py

책임 분리:
- VectorStoreService: 임베딩 생성, 청킹 실행, 벡터 검색 (이 파일)
- DocumentService: 문서 CRUD (app/api/services/document_service.py)

주요 기능:
- 임베딩 생성 (OpenAI text-embedding-3-small)
- 벡터 검색 (코사인 유사도)
- 청킹 실행 (문서 분할 + 임베딩)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

import numpy as np
import psycopg
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.models.rag import DocumentSource
from app.models.search import SearchFilters
from app.utils.logger import setup_logger
from app.utils.common import truncate_text

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_service = None
_db_manager = None
_text_chunker_module = None


def _get_settings_service():
    global _settings_service
    if _settings_service is None:
        from app.core.config.settings_config import settings_config
        _settings_service = settings_config
    return _settings_service


def _get_db_manager():
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


def _get_text_chunker_module():
    global _text_chunker_module
    if _text_chunker_module is None:
        from app.core.vector import text_chunker as tc
        _text_chunker_module = tc
    return _text_chunker_module


def get_chunking_settings():
    """DB 설정에서 청킹 관련 설정 가져오기 (DB → 기본값)"""
    return {
        "chunk_size": _get_settings_service().get_value("chunking", "default_chunk_size", 1000),
        "chunk_overlap": _get_settings_service().get_value("chunking", "default_overlap", 100),
    }


class VectorStoreService:
    """벡터 검색 서비스 (pgvector 기반)

    책임:
    - 임베딩 생성 (embed_text, embed_texts)
    - 벡터 검색 (search_similar_documents)
    - 청킹 실행 (execute_chunking, preview_chunks)

    CRUD 작업은 DocumentService (app/api/services/document_service.py)에서 처리
    """

    # 스니펫 관련 상수
    DEFAULT_SNIPPET_LENGTH = 200  # 문서 스니펫 기본 길이 (문자)

    # 청킹 기본값 (fallback, DB 설정 우선)
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 100

    def __init__(self):
        # 기본값 저장 (초기화 시점)
        self._default_api_key = settings.openai_api_key
        self._default_embedding_model = settings.embedding_model
        self._default_embedding_dimension = settings.embedding_dimension

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """매 요청 시 DB 설정을 반영한 OpenAIEmbeddings 인스턴스 생성"""
        api_key = _get_settings_service().get_value("openai", "api_key", self._default_api_key)
        model = self.embedding_model
        return OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key
        )

    @property
    def embedding_model(self) -> str:
        """현재 임베딩 모델 (DB 설정 우선)"""
        return _get_settings_service().get_value("embedding", "model", self._default_embedding_model)

    @property
    def embedding_dimension(self) -> int:
        """현재 임베딩 차원 (DB 설정 우선)"""
        return _get_settings_service().get_value("embedding", "dimension", self._default_embedding_dimension)

    def _create_snippet(self, content: str, max_length: Optional[int] = None) -> str:
        """컨텐츠 스니펫 생성"""
        length = max_length or self.DEFAULT_SNIPPET_LENGTH
        if len(content) <= length:
            return content
        return content[:length] + "..."

    # ============================================
    # 임베딩 생성
    # ============================================

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 임베딩 (LangChain OpenAIEmbeddings 사용)"""
        try:
            embeddings = self._get_embeddings()
            return embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 벡터로 임베딩 (배치, LangChain OpenAIEmbeddings 사용)"""
        try:
            embeddings = self._get_embeddings()
            return embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            raise

    # ============================================
    # 벡터 검색
    # ============================================

    def search_similar_documents(self, query: str, top_k: int = 10, filters: Optional[SearchFilters] = None, similarity_threshold: Optional[float] = None) -> List[DocumentSource]:
        """유사 문서 검색 (벡터 유사도 기반)"""
        # 쿼리를 벡터로 변환
        query_embedding = self.embed_text(query)
        query_embedding_array = np.array(query_embedding)

        # 필터 조건 구성
        filter_conditions = []
        filter_params = []

        # usage_type 필터 (기본값: 'rag_knowledge' - Action 문서 제외)
        usage_type = "rag_knowledge"
        if filters and filters.usage_type:
            usage_type = filters.usage_type
        filter_conditions.append("usage_type = %s")
        filter_params.append(usage_type)

        if filters:
            if filters.doc_type:
                filter_conditions.append("doc_type = %s")
                filter_params.append(filters.doc_type)

            if filters.language:
                filter_conditions.append("language = %s")
                filter_params.append(filters.language)

            if filters.department and filters.department in ['개발', '기획', 'HR', '마케팅']:
                filter_conditions.append("metadata->>'department' = %s")
                filter_params.append(filters.department)

        where_clause = ""
        if filter_conditions:
            where_clause = "WHERE " + " AND ".join(filter_conditions)

        # 유사도 임계값 (DB 설정 우선)
        if similarity_threshold is None:
            similarity_threshold = _get_settings_service().get_value("rag", "similarity_threshold", settings.rag_similarity_threshold)

        # 거리 측정 방식 (DB 설정 우선, 기본값: cosine)
        distance_metric = _get_settings_service().get_value("rag", "distance_metric", getattr(settings, "rag_distance_metric", "cosine"))

        # 거리 연산자 선택: cosine(<=>), l2(<->)
        if distance_metric == "l2":
            distance_operator = "<->"  # L2 (유클리드) 거리
        else:
            distance_operator = "<=>"  # 코사인 거리 (기본값)

        # 벡터 검색 쿼리 (서브쿼리로 거리 계산 1회만 수행)
        query_sql = f"""
            SELECT id, title, doc_type, content, context_data, metadata, language, distance
            FROM (
                SELECT id, title, doc_type, content, context_data, metadata, language, embedding {distance_operator} %s AS distance
                FROM tb_docs
                {where_clause}
            ) subq
            ORDER BY distance
            LIMIT %s
        """

        query_params = [query_embedding_array] + filter_params + [top_k]

        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute(query_sql, query_params)
            rows = cur.fetchall()

            logger.info(f"벡터 검색 원시 결과: {len(rows)}개 행 반환, 임계값={similarity_threshold}, 거리측정={distance_metric}")

            documents = []
            filtered_count = 0
            for row in rows:
                distance = row.get('distance')
                # 거리 측정 방식에 따라 유사도 계산
                if distance is not None:
                    if distance_metric == "l2":
                        # L2 거리: 0~∞ → 유사도 0~1로 변환
                        similarity = 1.0 / (1.0 + float(distance))
                    else:
                        # 코사인 거리: 0~2 → 유사도 -1~1로 변환 (정규화된 벡터의 경우 0~1)
                        similarity = 1.0 - float(distance)
                else:
                    similarity = 0.0

                # DEBUG: 문서별 상세 로그
                logger.debug(f"문서 ID={row['id']}, title='{truncate_text(row['title'], 30)}...', similarity={similarity:.4f}")

                if similarity < similarity_threshold:
                    filtered_count += 1
                    logger.debug(f"  -> 임계값 미달로 제외됨 (similarity={similarity:.4f} < {similarity_threshold})")
                    continue

                content = row.get('content', '')
                snippet = self._create_snippet(content)

                doc = DocumentSource(
                    id=row['id'],
                    title=row['title'],
                    doc_type=row['doc_type'],
                    content=content,
                    content_snippet=snippet,
                    metadata=row.get('metadata', {}),
                    similarity_score=round(similarity, 4),
                    context_data=row.get('context_data')
                )
                documents.append(doc)

            if filtered_count > 0:
                logger.debug(f"임계값으로 필터링된 문서: {filtered_count}개")
            logger.debug(f"벡터 검색 완료: query='{truncate_text(query, 30)}...', found={len(documents)}, filtered={filtered_count}")
            return documents

    # ============================================
    # 문서 삽입 (임베딩 포함)
    # ============================================

    def insert_document(self, title: str, doc_type: str, content: str, language: str = "ko", metadata: Optional[Dict[str, Any]] = None) -> int:
        """문서 삽입 (임베딩 포함)"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO tb_docs (title, doc_type, language, content, metadata, embedding, embedding_model, indexed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (title, doc_type, language, content, psycopg.types.json.Json(metadata or {}), embedding_array, self.embedding_model, True))

            result = cur.fetchone()
            doc_id = result['id']

            logger.info(f"문서 삽입 완료: ID={doc_id}, title='{title}'")
            return doc_id

    def update_document_embedding(self, doc_id: int, content: str) -> bool:
        """문서 임베딩 업데이트"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE tb_docs
                SET content = %s, embedding = %s, updated_at = now(), indexed = true
                WHERE id = %s
            """, (content, embedding_array, doc_id))

            return cur.rowcount > 0

    def insert_document_with_chunking(
        self,
        title: str,
        doc_type: str,
        content: str,
        language: str = "ko",
        metadata: Optional[Dict[str, Any]] = None,
        auto_chunk: bool = True,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        source_type: str = "ui_input",
        source_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """문서 삽입 (자동 청킹 지원)"""
        tc = _get_text_chunker_module()

        chunking_settings = get_chunking_settings()
        chunk_size = chunk_size or chunking_settings["chunk_size"]
        chunk_overlap = chunk_overlap or chunking_settings["chunk_overlap"]

        content_hash = tc.TextChunker.calculate_hash(content)

        # 자동 청킹 비활성화 또는 짧은 텍스트면 단일 문서로 저장
        if not auto_chunk or len(content) <= chunk_size:
            doc_id = self._insert_single_document(
                title=title, doc_type=doc_type, content=content, language=language,
                metadata=metadata, source_type=source_type, source_file=source_file,
                content_hash=content_hash, chunk_index=0, total_chunks=1, parent_doc_id=None
            )
            return {"parent_id": doc_id, "chunk_ids": [doc_id], "total_chunks": 1, "total_chars": len(content)}

        # 텍스트 청킹
        chunks = tc.chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("청킹 결과가 비어있습니다.")

        # 첫 번째 청크를 부모 문서로 저장
        parent_id = self._insert_single_document(
            title=f"{title} (1/{total_chunks})", doc_type=doc_type, content=chunks[0].content,
            language=language, metadata=metadata, source_type=source_type, source_file=source_file,
            content_hash=content_hash, chunk_index=0, total_chunks=total_chunks, parent_doc_id=None
        )

        chunk_ids = [parent_id]

        # 나머지 청크 저장
        for chunk in chunks[1:]:
            chunk_id = self._insert_single_document(
                title=f"{title} ({chunk.chunk_index + 1}/{total_chunks})", doc_type=doc_type,
                content=chunk.content, language=language, metadata=metadata, source_type=source_type,
                source_file=source_file, content_hash=None, chunk_index=chunk.chunk_index,
                total_chunks=total_chunks, parent_doc_id=parent_id
            )
            chunk_ids.append(chunk_id)

        logger.info(f"청킹 문서 삽입 완료: parent_id={parent_id}, chunks={total_chunks}")

        return {"parent_id": parent_id, "chunk_ids": chunk_ids, "total_chunks": total_chunks, "total_chars": len(content)}

    def _insert_single_document(
        self,
        title: str,
        doc_type: str,
        content: str,
        language: str,
        metadata: Optional[Dict[str, Any]],
        source_type: str,
        source_file: Optional[str],
        content_hash: Optional[str],
        chunk_index: int,
        total_chunks: int,
        parent_doc_id: Optional[int],
        usage_type: str = "rag_knowledge"
    ) -> int:
        """단일 문서 삽입 (내부용)"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO tb_docs (
                    title, doc_type, language, content, metadata,
                    embedding, embedding_model, indexed,
                    source_type, source_file, content_hash,
                    chunk_index, total_chunks, parent_doc_id, embedded_at,
                    usage_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title, doc_type, language, content, psycopg.types.json.Json(metadata or {}),
                embedding_array, self.embedding_model, True, source_type, source_file, content_hash,
                chunk_index, total_chunks, parent_doc_id, datetime.now(),
                usage_type
            ))

            result = cur.fetchone()
            return result['id']

    # ============================================
    # 청킹 미리보기 / 실행
    # ============================================

    def preview_chunks(self, content: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> List[Dict[str, Any]]:
        """청킹 미리보기 (DB 설정 사용)"""
        tc = _get_text_chunker_module()

        chunking_settings = get_chunking_settings()
        chunk_size = chunk_size or chunking_settings["chunk_size"]
        chunk_overlap = chunk_overlap or chunking_settings["chunk_overlap"]

        chunker = tc.TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.preview_chunks(content)

    def execute_chunking(self, doc_ids: List[int], chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None, delete_original: bool = False) -> List[Dict[str, Any]]:
        """저장된 문서들에 대해 청킹 실행"""
        chunking_settings = get_chunking_settings()
        effective_chunk_size: int = chunk_size or chunking_settings["chunk_size"]
        effective_chunk_overlap: int = chunk_overlap or chunking_settings["chunk_overlap"]

        results = []

        for doc_id in doc_ids:
            try:
                result = self._execute_single_chunking(doc_id=doc_id, chunk_size=effective_chunk_size, chunk_overlap=effective_chunk_overlap, delete_original=delete_original)
                results.append(result)
            except Exception as e:
                logger.error(f"청킹 실행 실패: doc_id={doc_id}, error={e}")
                results.append({
                    "original_doc_id": doc_id, "original_title": "", "success": False, "error": str(e),
                    "parent_id": None, "chunk_ids": [], "total_chunks": 0, "original_chars": 0
                })

        return results

    def _execute_single_chunking(self, doc_id: int, chunk_size: int, chunk_overlap: int, delete_original: bool) -> Dict[str, Any]:
        """단일 문서 청킹 실행"""
        tc = _get_text_chunker_module()
        db_manager = _get_db_manager()

        # 원본 문서 조회
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT id, title, doc_type, language, content, metadata, source_type, source_file, content_hash
                FROM tb_docs
                WHERE id = %s
            """, (doc_id,))

            doc = cur.fetchone()
            if not doc:
                raise ValueError(f"문서를 찾을 수 없습니다: ID={doc_id}")

        original_title = doc['title']
        content = doc['content']
        content_length = len(content)

        # 청킹이 필요없는 짧은 문서
        if content_length <= chunk_size:
            embedding = self.embed_text(content)
            embedding_array = np.array(embedding)

            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE tb_docs
                    SET embedding = %s, embedding_model = %s, indexed = true, embedded_at = %s
                    WHERE id = %s
                """, (embedding_array, self.embedding_model, datetime.now(), doc_id))

            logger.info(f"짧은 문서 임베딩 완료: doc_id={doc_id}")

            return {
                "original_doc_id": doc_id, "original_title": original_title, "success": True, "error": None,
                "parent_id": doc_id, "chunk_ids": [doc_id], "total_chunks": 1, "original_chars": content_length
            }

        # 텍스트 청킹
        chunks = tc.chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("청킹 결과가 비어있습니다.")

        # 배치 임베딩 생성
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(chunk_contents)

        chunk_ids = []

        with db_manager.get_cursor(commit=True) as cur:
            # 첫 번째 청크: 원본 문서 업데이트 (usage_type도 rag_knowledge로 보장)
            first_embedding = np.array(embeddings[0])
            cur.execute("""
                UPDATE tb_docs
                SET title = %s, content = %s, original_content = %s, embedding = %s, embedding_model = %s,
                    indexed = true, chunk_index = 0, total_chunks = %s, embedded_at = %s, usage_type = 'rag_knowledge'
                WHERE id = %s
            """, (
                f"{original_title} (1/{total_chunks})", chunks[0].content, content,
                first_embedding, self.embedding_model, total_chunks, datetime.now(), doc_id
            ))
            parent_id = doc_id
            chunk_ids.append(doc_id)

            # 나머지 청크: 새 문서로 삽입 (usage_type = 'rag_knowledge'로 통일)
            for i, chunk in enumerate(chunks[1:], start=1):
                embedding_array = np.array(embeddings[i])
                cur.execute("""
                    INSERT INTO tb_docs (
                        title, doc_type, language, content, metadata,
                        embedding, embedding_model, indexed,
                        source_type, source_file, content_hash,
                        chunk_index, total_chunks, parent_doc_id, embedded_at,
                        usage_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"{original_title} ({i + 1}/{total_chunks})", doc['doc_type'], doc['language'],
                    chunk.content, psycopg.types.json.Json(doc['metadata'] or {}),
                    embedding_array, self.embedding_model, True, doc['source_type'], doc['source_file'],
                    None, chunk.chunk_index, total_chunks, parent_id, datetime.now(),
                    'rag_knowledge'
                ))
                chunk_id = cur.fetchone()['id']
                chunk_ids.append(chunk_id)

        logger.info(f"청킹 실행 완료: doc_id={doc_id}, parent_id={parent_id}, chunks={total_chunks}")

        return {
            "original_doc_id": doc_id, "original_title": original_title, "success": True, "error": None,
            "parent_id": parent_id, "chunk_ids": chunk_ids, "total_chunks": total_chunks, "original_chars": content_length
        }


# 싱글톤 인스턴스
vector_store = VectorStoreService()
