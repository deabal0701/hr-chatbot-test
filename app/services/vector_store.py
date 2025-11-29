from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psycopg
from openai import OpenAI

from app.config import settings
from app.models.schemas import DocumentSource, SearchFilters
from app.services.settings_service import settings_service
from app.utils.database import db_manager
from app.utils.logger import setup_logger
from app.utils.text_chunker import TextChunker, chunk_text

logger = setup_logger(__name__)


def get_chunking_settings():
    """DB 설정에서 청킹 관련 설정 가져오기 (DB → 기본값)"""
    return {
        "chunk_size": settings_service.get_value("chunking", "default_chunk_size", 1000),
        "chunk_overlap": settings_service.get_value("chunking", "default_overlap", 100),
    }


class VectorStoreService:
    """벡터 검색 서비스 (pgvector 기반)"""

    def __init__(self):
        # 기본값 저장 (초기화 시점)
        self._default_api_key = settings.openai_api_key
        self._default_embedding_model = settings.embedding_model
        self._default_embedding_dimension = settings.embedding_dimension

    def _get_openai_client(self) -> OpenAI:
        """매 요청 시 DB 설정을 반영한 OpenAI 클라이언트 생성"""
        api_key = settings_service.get_value("openai", "api_key", self._default_api_key)
        return OpenAI(api_key=api_key)

    @property
    def embedding_model(self) -> str:
        """현재 임베딩 모델 (DB 설정 우선)"""
        return settings_service.get_value("embedding", "model", self._default_embedding_model)

    @property
    def embedding_dimension(self) -> int:
        """현재 임베딩 차원 (DB 설정 우선)"""
        return settings_service.get_value("embedding", "dimension", self._default_embedding_dimension)

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 임베딩"""
        try:
            client = self._get_openai_client()
            response = client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """여러 텍스트를 벡터로 임베딩 (배치)"""
        try:
            client = self._get_openai_client()
            response = client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            raise

    def insert_document(
        self,
        title: str,
        doc_type: str,
        content: str,
        language: str = "ko",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """문서 삽입 (임베딩 포함)"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO hr_docs (title, doc_type, language, content, metadata, embedding, embedding_model, indexed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title,
                doc_type,
                language,
                content,
                psycopg.types.json.Json(metadata or {}),
                embedding_array,
                self.embedding_model,
                True
            ))

            result = cur.fetchone()
            doc_id = result['id']

            logger.info(f"문서 삽입 완료: ID={doc_id}, title='{title}'")
            return doc_id

    def search_similar_documents(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[SearchFilters] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[DocumentSource]:
        """유사 문서 검색 (벡터 유사도 기반)"""
        # 쿼리를 벡터로 변환
        query_embedding = self.embed_text(query)
        query_embedding_array = np.array(query_embedding)

        # 필터 조건 구성
        filter_conditions = []
        filter_params = []

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
            similarity_threshold = settings_service.get_value("rag", "similarity_threshold", settings.rag_similarity_threshold)

        # 벡터 검색 쿼리 (코사인 거리 사용)
        # <=> 연산자: 코사인 거리 (0 = 동일, 2 = 정반대)
        # 코사인 유사도 = 1 - 코사인 거리 (범위: -1 ~ 1, 보통 0 ~ 1)
        query_sql = f"""
            SELECT
                id,
                title,
                doc_type,
                content,
                metadata,
                language,
                embedding <=> %s AS distance
            FROM hr_docs
            {where_clause}
            ORDER BY embedding <=> %s
            LIMIT %s
        """

        # 파라미터 순서: SELECT의 embedding 1번 + WHERE 필터들 + ORDER BY embedding + LIMIT
        query_params = [query_embedding_array] + filter_params + [query_embedding_array, top_k]

        with db_manager.get_cursor() as cur:
            cur.execute(query_sql, query_params)
            rows = cur.fetchall()

            logger.info(f"벡터 검색 원시 결과: {len(rows)}개 행 반환, 임계값={similarity_threshold}")

            documents = []
            filtered_count = 0
            for row in rows:
                # 코사인 거리를 유사도로 변환
                # 코사인 거리 0 = 완전 일치 = 유사도 1.0
                # 코사인 거리 2 = 정반대 = 유사도 -1.0
                distance = row.get('distance')

                if distance is None:
                    similarity = 0.0
                else:
                    # 코사인 유사도 = 1 - 코사인 거리
                    # 범위: -1 ~ 1 (보통 텍스트는 0 ~ 1)
                    similarity = 1.0 - float(distance)

                logger.info(f"문서 ID={row['id']}, title='{row['title'][:30]}...', distance={distance}, similarity={similarity:.4f}")

                # 임계값 체크
                if similarity < similarity_threshold:
                    filtered_count += 1
                    logger.info(f"  -> 임계값 미달로 제외됨 (similarity={similarity:.4f} < {similarity_threshold})")
                    continue

                # 컨텐츠 스니펫 생성 (처음 200자)
                content = row.get('content', '')
                snippet = content[:200] + "..." if len(content) > 200 else content

                doc = DocumentSource(
                    id=row['id'],
                    title=row['title'],
                    doc_type=row['doc_type'],
                    content_snippet=snippet,
                    metadata=row.get('metadata', {}),
                    similarity_score=round(similarity, 4)
                )
                documents.append(doc)

            if filtered_count > 0:
                logger.info(f"임계값으로 필터링된 문서: {filtered_count}개")
            logger.info(f"벡터 검색 완료: query='{query[:50]}...', found={len(documents)}")
            return documents

    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """ID로 문서 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT id, title, doc_type, language, content, metadata, created_at, updated_at
                FROM hr_docs
                WHERE id = %s
            """, (doc_id,))

            row = cur.fetchone()
            return dict(row) if row else None

    def delete_document(self, doc_id: int) -> bool:
        """문서 삭제"""
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM hr_docs WHERE id = %s", (doc_id,))
            affected = cur.rowcount
            return affected > 0

    def update_document_embedding(self, doc_id: int, content: str) -> bool:
        """문서 임베딩 업데이트"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE hr_docs
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
        """
        문서 삽입 (자동 청킹 지원)

        Args:
            title: 문서 제목
            doc_type: 문서 유형
            content: 문서 내용
            language: 언어
            metadata: 메타데이터
            auto_chunk: 자동 청킹 여부
            chunk_size: 청크 크기 (None이면 DB 설정 사용)
            chunk_overlap: 청크 간 중복 (None이면 DB 설정 사용)
            source_type: 소스 타입 (ui_input, pdf, web, api)
            source_file: 원본 파일명

        Returns:
            {
                "parent_id": 원본 문서 ID,
                "chunk_ids": [청크 ID 리스트],
                "total_chunks": 청크 수,
                "total_chars": 전체 문자 수
            }
        """
        # DB 설정에서 청킹 파라미터 가져오기
        chunking_settings = get_chunking_settings()
        chunk_size = chunk_size or chunking_settings["chunk_size"]
        chunk_overlap = chunk_overlap or chunking_settings["chunk_overlap"]

        content_hash = TextChunker.calculate_hash(content)

        # 자동 청킹 비활성화 또는 짧은 텍스트면 단일 문서로 저장
        if not auto_chunk or len(content) <= chunk_size:
            doc_id = self._insert_single_document(
                title=title,
                doc_type=doc_type,
                content=content,
                language=language,
                metadata=metadata,
                source_type=source_type,
                source_file=source_file,
                content_hash=content_hash,
                chunk_index=0,
                total_chunks=1,
                parent_doc_id=None
            )
            return {
                "parent_id": doc_id,
                "chunk_ids": [doc_id],
                "total_chunks": 1,
                "total_chars": len(content)
            }

        # 텍스트 청킹
        chunks = chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("청킹 결과가 비어있습니다.")

        # 첫 번째 청크를 부모 문서로 저장
        parent_id = self._insert_single_document(
            title=f"{title} (1/{total_chunks})",
            doc_type=doc_type,
            content=chunks[0].content,
            language=language,
            metadata=metadata,
            source_type=source_type,
            source_file=source_file,
            content_hash=content_hash,
            chunk_index=0,
            total_chunks=total_chunks,
            parent_doc_id=None
        )

        chunk_ids = [parent_id]

        # 나머지 청크 저장 (parent_doc_id 설정)
        for chunk in chunks[1:]:
            chunk_id = self._insert_single_document(
                title=f"{title} ({chunk.chunk_index + 1}/{total_chunks})",
                doc_type=doc_type,
                content=chunk.content,
                language=language,
                metadata=metadata,
                source_type=source_type,
                source_file=source_file,
                content_hash=None,  # 청크는 해시 없음
                chunk_index=chunk.chunk_index,
                total_chunks=total_chunks,
                parent_doc_id=parent_id
            )
            chunk_ids.append(chunk_id)

        logger.info(f"청킹 문서 삽입 완료: parent_id={parent_id}, chunks={total_chunks}")

        return {
            "parent_id": parent_id,
            "chunk_ids": chunk_ids,
            "total_chunks": total_chunks,
            "total_chars": len(content)
        }

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
        parent_doc_id: Optional[int]
    ) -> int:
        """단일 문서 삽입 (내부용)"""
        embedding = self.embed_text(content)
        embedding_array = np.array(embedding)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO hr_docs (
                    title, doc_type, language, content, metadata,
                    embedding, embedding_model, indexed,
                    source_type, source_file, content_hash,
                    chunk_index, total_chunks, parent_doc_id, embedded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title,
                doc_type,
                language,
                content,
                psycopg.types.json.Json(metadata or {}),
                embedding_array,
                self.embedding_model,
                True,
                source_type,
                source_file,
                content_hash,
                chunk_index,
                total_chunks,
                parent_doc_id,
                datetime.now()
            ))

            result = cur.fetchone()
            return result['id']

    def preview_chunks(
        self,
        content: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """청킹 미리보기 (DB 설정 사용)"""
        chunking_settings = get_chunking_settings()
        chunk_size = chunk_size or chunking_settings["chunk_size"]
        chunk_overlap = chunk_overlap or chunking_settings["chunk_overlap"]

        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunker.preview_chunks(content)

    def get_document_with_chunks(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """문서와 모든 청크 조회"""
        with db_manager.get_cursor() as cur:
            # 문서 조회
            cur.execute("""
                SELECT id, title, doc_type, language, content, metadata,
                       source_type, source_file, chunk_index, total_chunks,
                       parent_doc_id, indexed, embedded_at,
                       LENGTH(content) as content_length,
                       created_at, updated_at
                FROM hr_docs
                WHERE id = %s
            """, (doc_id,))

            doc = cur.fetchone()
            if not doc:
                return None

            result = dict(doc)

            # 청킹된 문서면 모든 청크 조회
            parent_id = doc['parent_doc_id'] or doc['id']
            cur.execute("""
                SELECT id, title, chunk_index, LENGTH(content) as content_length
                FROM hr_docs
                WHERE id = %s OR parent_doc_id = %s
                ORDER BY chunk_index
            """, (parent_id, parent_id))

            result['chunks'] = [dict(row) for row in cur.fetchall()]

            return result

    def delete_document_with_chunks(self, doc_id: int) -> int:
        """문서와 모든 청크 삭제"""
        with db_manager.get_cursor(commit=True) as cur:
            # parent_doc_id가 doc_id인 청크들도 삭제 (CASCADE로 자동 삭제되지만 명시적으로)
            cur.execute("""
                DELETE FROM hr_docs
                WHERE id = %s OR parent_doc_id = %s
            """, (doc_id, doc_id))

            deleted = cur.rowcount
            logger.info(f"문서 삭제 완료: doc_id={doc_id}, 삭제된 문서={deleted}개")
            return deleted

    def list_documents(
        self,
        doc_type: Optional[str] = None,
        source_type: Optional[str] = None,
        indexed: Optional[bool] = None,
        include_chunks: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        문서 목록 조회

        Args:
            doc_type: 문서 유형 필터
            source_type: 소스 타입 필터
            indexed: 임베딩 여부 필터 (True: 임베딩됨, False: 미임베딩, None: 전체)
            include_chunks: 청크 포함 여부
            limit: 최대 결과 수
            offset: 시작 위치

        Returns:
            (문서 목록, 전체 카운트) 튜플
        """
        conditions = []
        params = []

        # 청크 제외 (원본 문서만)
        if not include_chunks:
            conditions.append("(parent_doc_id IS NULL OR chunk_index = 0)")

        if doc_type:
            conditions.append("doc_type = %s")
            params.append(doc_type)

        if source_type:
            conditions.append("source_type = %s")
            params.append(source_type)

        # 임베딩 여부 필터
        if indexed is not None:
            if indexed:
                # 임베딩된 문서
                conditions.append("indexed = true")
            else:
                # 미임베딩 문서
                conditions.append("(indexed = false OR embedding IS NULL)")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with db_manager.get_cursor() as cur:
            # 전체 카운트 조회
            cur.execute(f"""
                SELECT COUNT(*) as total
                FROM hr_docs
                {where_clause}
            """, params)
            total_count = cur.fetchone()['total']

            # 문서 목록 조회
            list_params = params + [limit, offset]
            cur.execute(f"""
                SELECT id, title, doc_type, language,
                       LENGTH(content) as content_length,
                       source_type, source_file, total_chunks, indexed,
                       embedded_at, created_at, updated_at
                FROM hr_docs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, list_params)

            documents = [dict(row) for row in cur.fetchall()]
            return documents, total_count

    # ============================================
    # 문서 저장 (임베딩 없이) / 청킹 실행 분리
    # ============================================

    def save_document_without_embedding(
        self,
        title: str,
        doc_type: str,
        content: str,
        language: str = "ko",
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "ui_input",
        source_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문서 저장 (임베딩 없이)

        1차적으로 문서를 저장하고, 청킹은 별도 API로 실행
        """
        content_hash = TextChunker.calculate_hash(content)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO hr_docs (
                    title, doc_type, language, content, metadata,
                    indexed, source_type, source_file, content_hash,
                    chunk_index, total_chunks
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                title,
                doc_type,
                language,
                content,
                psycopg.types.json.Json(metadata or {}),
                False,  # indexed = False (임베딩 없음)
                source_type,
                source_file,
                content_hash,
                0,  # chunk_index
                1   # total_chunks (아직 청킹 안됨)
            ))

            result = cur.fetchone()
            doc_id = result['id']

        # 청킹 필요 여부 및 예상 청크 수 계산
        content_length = len(content)
        default_chunk_size = 1000
        needs_chunking = content_length > default_chunk_size
        recommended_chunks = max(1, (content_length // default_chunk_size) + (1 if content_length % default_chunk_size else 0))

        logger.info(f"문서 저장 완료 (임베딩 없음): ID={doc_id}, title='{title}', length={content_length}")

        return {
            "doc_id": doc_id,
            "title": title,
            "content_length": content_length,
            "needs_chunking": needs_chunking,
            "recommended_chunks": recommended_chunks
        }

    def execute_chunking(
        self,
        doc_ids: List[int],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        delete_original: bool = False
    ) -> List[Dict[str, Any]]:
        """
        저장된 문서들에 대해 청킹 실행

        Args:
            doc_ids: 청킹할 문서 ID 목록
            chunk_size: 청크 크기 (None이면 DB 설정 사용)
            chunk_overlap: 청크 간 중복 (None이면 DB 설정 사용)
            delete_original: 원본 문서 삭제 여부

        Returns:
            각 문서별 청킹 결과 목록
        """
        # DB 설정에서 청킹 파라미터 가져오기
        chunking_settings = get_chunking_settings()
        chunk_size = chunk_size or chunking_settings["chunk_size"]
        chunk_overlap = chunk_overlap or chunking_settings["chunk_overlap"]

        results = []

        for doc_id in doc_ids:
            try:
                result = self._execute_single_chunking(
                    doc_id=doc_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    delete_original=delete_original
                )
                results.append(result)
            except Exception as e:
                logger.error(f"청킹 실행 실패: doc_id={doc_id}, error={e}")
                results.append({
                    "original_doc_id": doc_id,
                    "original_title": "",
                    "success": False,
                    "error": str(e),
                    "parent_id": None,
                    "chunk_ids": [],
                    "total_chunks": 0,
                    "original_chars": 0
                })

        return results

    def _execute_single_chunking(
        self,
        doc_id: int,
        chunk_size: int,
        chunk_overlap: int,
        delete_original: bool
    ) -> Dict[str, Any]:
        """단일 문서 청킹 실행"""
        # 원본 문서 조회
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT id, title, doc_type, language, content, metadata,
                       source_type, source_file, content_hash
                FROM hr_docs
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
            # 임베딩만 생성하고 업데이트
            embedding = self.embed_text(content)
            embedding_array = np.array(embedding)

            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE hr_docs
                    SET embedding = %s, embedding_model = %s, indexed = true, embedded_at = %s
                    WHERE id = %s
                """, (embedding_array, self.embedding_model, datetime.now(), doc_id))

            logger.info(f"짧은 문서 임베딩 완료: doc_id={doc_id}")

            return {
                "original_doc_id": doc_id,
                "original_title": original_title,
                "success": True,
                "error": None,
                "parent_id": doc_id,
                "chunk_ids": [doc_id],
                "total_chunks": 1,
                "original_chars": content_length
            }

        # 텍스트 청킹
        chunks = chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        total_chunks = len(chunks)

        if total_chunks == 0:
            raise ValueError("청킹 결과가 비어있습니다.")

        # 배치 임베딩 생성
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(chunk_contents)

        chunk_ids = []

        with db_manager.get_cursor(commit=True) as cur:
            # 첫 번째 청크: 원본 문서 업데이트
            first_embedding = np.array(embeddings[0])
            cur.execute("""
                UPDATE hr_docs
                SET title = %s, content = %s, embedding = %s, embedding_model = %s,
                    indexed = true, chunk_index = 0, total_chunks = %s, embedded_at = %s
                WHERE id = %s
            """, (
                f"{original_title} (1/{total_chunks})",
                chunks[0].content,
                first_embedding,
                self.embedding_model,
                total_chunks,
                datetime.now(),
                doc_id
            ))
            parent_id = doc_id
            chunk_ids.append(doc_id)

            # 나머지 청크: 새 문서로 삽입
            for i, chunk in enumerate(chunks[1:], start=1):
                embedding_array = np.array(embeddings[i])
                cur.execute("""
                    INSERT INTO hr_docs (
                        title, doc_type, language, content, metadata,
                        embedding, embedding_model, indexed,
                        source_type, source_file, content_hash,
                        chunk_index, total_chunks, parent_doc_id, embedded_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"{original_title} ({i + 1}/{total_chunks})",
                    doc['doc_type'],
                    doc['language'],
                    chunk.content,
                    psycopg.types.json.Json(doc['metadata'] or {}),
                    embedding_array,
                    self.embedding_model,
                    True,
                    doc['source_type'],
                    doc['source_file'],
                    None,  # 청크는 해시 없음
                    chunk.chunk_index,
                    total_chunks,
                    parent_id,
                    datetime.now()
                ))
                chunk_id = cur.fetchone()['id']
                chunk_ids.append(chunk_id)

        logger.info(f"청킹 실행 완료: doc_id={doc_id}, parent_id={parent_id}, chunks={total_chunks}")

        return {
            "original_doc_id": doc_id,
            "original_title": original_title,
            "success": True,
            "error": None,
            "parent_id": parent_id,
            "chunk_ids": chunk_ids,
            "total_chunks": total_chunks,
            "original_chars": content_length
        }

    # ============================================
    # 문서 수정
    # ============================================

    def update_document(
        self,
        doc_id: int,
        title: Optional[str] = None,
        doc_type: Optional[str] = None,
        content: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        문서 수정 (내용 변경 시 임베딩 무효화)

        Returns:
            {
                "doc_id": 문서 ID,
                "title": 제목,
                "content_length": 내용 길이,
                "embedding_invalidated": 임베딩 무효화 여부,
                "needs_reindex": 재인덱싱 필요 여부
            }
        """
        # 기존 문서 조회
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT id, title, doc_type, language, content, metadata, indexed, parent_doc_id
                FROM hr_docs
                WHERE id = %s
            """, (doc_id,))

            doc = cur.fetchone()
            if not doc:
                raise ValueError(f"문서를 찾을 수 없습니다: ID={doc_id}")

            # 청크 문서는 수정 불가
            if doc['parent_doc_id'] is not None:
                raise ValueError(f"청크 문서는 직접 수정할 수 없습니다. 원본 문서(ID={doc['parent_doc_id']})를 수정하세요.")

        # 변경할 필드 준비
        updates = []
        params = []
        content_changed = False

        if title is not None:
            updates.append("title = %s")
            params.append(title)

        if doc_type is not None:
            updates.append("doc_type = %s")
            params.append(doc_type)

        if content is not None:
            updates.append("content = %s")
            params.append(content)
            content_changed = True
            # 내용 변경 시 임베딩 무효화
            updates.append("embedding = NULL")
            updates.append("indexed = false")
            updates.append("content_hash = %s")
            params.append(TextChunker.calculate_hash(content))

        if language is not None:
            updates.append("language = %s")
            params.append(language)

        if metadata is not None:
            updates.append("metadata = %s")
            params.append(psycopg.types.json.Json(metadata))

        if not updates:
            # 변경 사항 없음
            return {
                "doc_id": doc_id,
                "title": doc['title'],
                "content_length": len(doc['content']),
                "embedding_invalidated": False,
                "needs_reindex": False
            }

        updates.append("updated_at = now()")
        params.append(doc_id)

        # 업데이트 실행
        with db_manager.get_cursor(commit=True) as cur:
            sql = f"UPDATE hr_docs SET {', '.join(updates)} WHERE id = %s"
            cur.execute(sql, params)

            # 내용 변경 시 기존 청크 삭제
            if content_changed:
                cur.execute("""
                    DELETE FROM hr_docs WHERE parent_doc_id = %s
                """, (doc_id,))
                deleted_chunks = cur.rowcount
                if deleted_chunks > 0:
                    logger.info(f"기존 청크 삭제: doc_id={doc_id}, chunks={deleted_chunks}")

        final_title = title if title is not None else doc['title']
        final_content_length = len(content) if content is not None else len(doc['content'])

        logger.info(f"문서 수정 완료: doc_id={doc_id}, content_changed={content_changed}")

        return {
            "doc_id": doc_id,
            "title": final_title,
            "content_length": final_content_length,
            "embedding_invalidated": content_changed,
            "needs_reindex": content_changed
        }

    def bulk_delete_documents(self, doc_ids: List[int]) -> Dict[str, Any]:
        """
        문서 일괄 삭제

        Returns:
            {
                "total_requested": 요청 개수,
                "total_deleted": 삭제 개수,
                "failed_ids": 실패한 ID 목록
            }
        """
        total_deleted = 0
        failed_ids = []

        for doc_id in doc_ids:
            try:
                deleted = self.delete_document_with_chunks(doc_id)
                if deleted > 0:
                    total_deleted += deleted
                else:
                    failed_ids.append(doc_id)
            except Exception as e:
                logger.error(f"문서 삭제 실패: doc_id={doc_id}, error={e}")
                failed_ids.append(doc_id)

        return {
            "total_requested": len(doc_ids),
            "total_deleted": total_deleted,
            "failed_ids": failed_ids
        }


# 싱글톤 인스턴스
vector_store = VectorStoreService()
