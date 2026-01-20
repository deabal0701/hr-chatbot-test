"""문서 관리 서비스 (Document Service Layer)

위치: app/api/services/document_service.py

책임 분리:
- DocumentService: 문서 CRUD + 비즈니스 로직 (이 파일)
- VectorStoreService: 임베딩/벡터검색 전용 (app/core/vector/vector_store.py)

의존성 방향:
- DocumentService → VectorStoreService (단방향)
- DocumentService → DatabaseManager (직접 CRUD)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_db_manager = None
_vector_store = None
_text_chunker_module = None


def _get_db_manager():
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


def _get_vector_store():
    """VectorStoreService 지연 로드 (임베딩/벡터 관련 작업용)"""
    global _vector_store
    if _vector_store is None:
        from app.core.vector.vector_store import vector_store
        _vector_store = vector_store
    return _vector_store


def _get_text_chunker_module():
    global _text_chunker_module
    if _text_chunker_module is None:
        from app.core.vector import text_chunker as tc
        _text_chunker_module = tc
    return _text_chunker_module


class DocumentService:
    """문서 관리 서비스 (CRUD + 비즈니스 로직)

    VectorStoreService와의 역할 분리:
    - DocumentService: 문서 생명주기 관리 (저장, 조회, 수정, 삭제)
    - VectorStoreService: 임베딩 생성, 청킹 실행, 벡터 검색
    """

    # 청킹 기본값 (DB 설정 우선)
    DEFAULT_CHUNK_SIZE = 1000

    # ============================================
    # 문서 CRUD
    # ============================================

    @staticmethod
    def save_document(
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

        Args:
            title: 문서 제목
            doc_type: 문서 유형 (policy, job_posting, faq, guide 등)
            content: 문서 내용
            language: 언어 (기본: ko)
            metadata: 추가 메타데이터
            source_type: 소스 타입 (ui_input, pdf, web, api)
            source_file: 원본 파일명

        Returns:
            {
                "doc_id": 문서 ID,
                "title": 제목,
                "content_length": 내용 길이,
                "needs_chunking": 청킹 필요 여부,
                "recommended_chunks": 예상 청크 수
            }
        """
        tc = _get_text_chunker_module()
        content_hash = tc.TextChunker.calculate_hash(content)

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("""
                    INSERT INTO tb_docs (title, doc_type, language, content, metadata, indexed, source_type, source_file, content_hash, chunk_index, total_chunks)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    title, doc_type, language, content,
                    psycopg.types.json.Json(metadata or {}), # type: ignore
                    False,  # indexed = False (임베딩 없음)
                    source_type, source_file, content_hash,
                    0,  # chunk_index
                    1   # total_chunks (아직 청킹 안됨)
                ))

                result = cur.fetchone()
                doc_id = result['id'] # type: ignore

        except psycopg.errors.UniqueViolation as e:
            logger.error(f"문서 저장 실패 - 중복: {e}")
            raise ValueError(f"중복된 문서입니다: {title}")
        except psycopg.Error as e:
            logger.error(f"문서 저장 실패 - DB 오류: {e}")
            raise RuntimeError(f"문서 저장 중 데이터베이스 오류가 발생했습니다: {e}")

        # 청킹 필요 여부 및 예상 청크 수 계산
        content_length = len(content)
        needs_chunking = content_length > DocumentService.DEFAULT_CHUNK_SIZE
        recommended_chunks = max(1, (content_length // DocumentService.DEFAULT_CHUNK_SIZE) + (1 if content_length % DocumentService.DEFAULT_CHUNK_SIZE else 0))

        logger.info(f"문서 저장 완료 (임베딩 없음): ID={doc_id}, title='{title}', length={content_length}")

        return {
            "doc_id": doc_id,
            "title": title,
            "content_length": content_length,
            "needs_chunking": needs_chunking,
            "recommended_chunks": recommended_chunks
        }

    @staticmethod
    def get_document(doc_id: int) -> Optional[Dict[str, Any]]:
        """
        문서 상세 조회 (청크 포함)

        Args:
            doc_id: 문서 ID

        Returns:
            문서 정보 (청크 포함) 또는 None
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                # 문서 조회
                cur.execute("""
                    SELECT id, title, doc_type, language, content, original_content, metadata,
                           source_type, source_file, chunk_index, total_chunks,
                           parent_doc_id, indexed, embedded_at,
                           LENGTH(content) as content_length,
                           created_at, updated_at
                    FROM tb_docs
                    WHERE id = %s
                """, (doc_id,))

                doc = cur.fetchone()
                if not doc:
                    return None

                result = dict(doc)

                # 자식 청크 문서면 부모로 리다이렉트 정보 제공
                if doc['parent_doc_id'] is not None:
                    result['redirect_to_parent'] = doc['parent_doc_id']

                # 부모 문서 ID 결정
                parent_id = doc['parent_doc_id'] or doc['id']

                # 모든 청크 조회 (content 포함)
                cur.execute("""
                    SELECT id, title, chunk_index, content, LENGTH(content) as content_length
                    FROM tb_docs
                    WHERE id = %s OR parent_doc_id = %s
                    ORDER BY chunk_index
                """, (parent_id, parent_id))

                result['chunks'] = [dict(row) for row in cur.fetchall()]

                # 전체 원본 내용 가져오기
                if doc['parent_doc_id'] is None:
                    full_content = doc.get('original_content') or doc['content']
                else:
                    cur.execute("SELECT original_content, content FROM tb_docs WHERE id = %s", (parent_id,))
                    parent = cur.fetchone()
                    full_content = parent.get('original_content') or parent['content'] if parent else doc['content']

                result['full_content'] = full_content
                result['original_length'] = len(full_content) if full_content else 0

                return result

        except psycopg.Error as e:
            logger.error(f"문서 조회 실패 - DB 오류: doc_id={doc_id}, error={e}")
            raise RuntimeError(f"문서 조회 중 데이터베이스 오류가 발생했습니다: {e}")

    @staticmethod
    def list_documents(
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
                conditions.append("indexed = true")
            else:
                conditions.append("(indexed = false OR embedding IS NULL)")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                # 전체 카운트 조회
                cur.execute(f"SELECT COUNT(*) as total FROM tb_docs {where_clause}", params)
                total_count = cur.fetchone()['total']

                # 문서 목록 조회
                list_params = params + [limit, offset]
                cur.execute(f"""
                    SELECT id, title, doc_type, language,
                           LENGTH(content) as content_length,
                           COALESCE(LENGTH(original_content), LENGTH(content)) as original_length,
                           source_type, source_file, total_chunks, indexed,
                           embedded_at, created_at, updated_at
                    FROM tb_docs
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, list_params)

                documents = [dict(row) for row in cur.fetchall()]
                return documents, total_count

        except psycopg.Error as e:
            logger.error(f"문서 목록 조회 실패 - DB 오류: {e}")
            raise RuntimeError(f"문서 목록 조회 중 데이터베이스 오류가 발생했습니다: {e}")

    @staticmethod
    def update_document(
        doc_id: int,
        title: Optional[str] = None,
        doc_type: Optional[str] = None,
        content: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        문서 수정 (내용 변경 시 임베딩 무효화)

        Args:
            doc_id: 문서 ID
            title: 새 제목
            doc_type: 새 문서 유형
            content: 새 내용 (변경 시 임베딩 무효화)
            language: 새 언어
            metadata: 새 메타데이터

        Returns:
            {
                "doc_id": 문서 ID,
                "title": 제목,
                "content_length": 내용 길이,
                "embedding_invalidated": 임베딩 무효화 여부,
                "needs_reindex": 재인덱싱 필요 여부
            }

        Raises:
            ValueError: 문서 없음, 청크 문서 수정 시도
        """
        tc = _get_text_chunker_module()

        try:
            db_manager = _get_db_manager()

            # 기존 문서 조회
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT id, title, doc_type, language, content, metadata, indexed, parent_doc_id
                    FROM tb_docs
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
                params.append(tc.TextChunker.calculate_hash(content))

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
                sql = f"UPDATE tb_docs SET {', '.join(updates)} WHERE id = %s"
                cur.execute(sql, params)

                # 내용 변경 시 기존 청크 삭제
                if content_changed:
                    cur.execute("DELETE FROM tb_docs WHERE parent_doc_id = %s", (doc_id,))
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

        except ValueError:
            raise
        except psycopg.Error as e:
            logger.error(f"문서 수정 실패 - DB 오류: doc_id={doc_id}, error={e}")
            raise RuntimeError(f"문서 수정 중 데이터베이스 오류가 발생했습니다: {e}")

    @staticmethod
    def delete_document(doc_id: int) -> int:
        """
        문서 삭제 (청크 포함)

        Args:
            doc_id: 문서 ID

        Returns:
            삭제된 문서 수 (청크 포함)
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                # parent_doc_id가 doc_id인 청크들도 삭제
                cur.execute("""
                    DELETE FROM tb_docs
                    WHERE id = %s OR parent_doc_id = %s
                """, (doc_id, doc_id))

                deleted = cur.rowcount
                logger.info(f"문서 삭제 완료: doc_id={doc_id}, 삭제된 문서={deleted}개")
                return deleted

        except psycopg.Error as e:
            logger.error(f"문서 삭제 실패 - DB 오류: doc_id={doc_id}, error={e}")
            raise RuntimeError(f"문서 삭제 중 데이터베이스 오류가 발생했습니다: {e}")

    @staticmethod
    def bulk_delete_documents(doc_ids: List[int]) -> Dict[str, Any]:
        """
        문서 일괄 삭제

        Args:
            doc_ids: 삭제할 문서 ID 목록

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
                deleted = DocumentService.delete_document(doc_id)
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

    # ============================================
    # 임베딩/청킹 관련 (VectorStoreService 위임)
    # ============================================

    @staticmethod
    def preview_chunks(
        content: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        청킹 미리보기 (VectorStoreService 위임)

        Args:
            content: 미리보기할 내용
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 중복

        Returns:
            청크 미리보기 목록
        """
        return _get_vector_store().preview_chunks(
            content=content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    @staticmethod
    def execute_embedding(
        doc_ids: List[int],
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        delete_original: bool = False
    ) -> List[Dict[str, Any]]:
        """
        임베딩 실행 (VectorStoreService 위임)

        Args:
            doc_ids: 임베딩할 문서 ID 목록
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 중복
            delete_original: 원본 삭제 여부

        Returns:
            각 문서별 임베딩 결과 목록
        """
        return _get_vector_store().execute_chunking(
            doc_ids=doc_ids,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            delete_original=delete_original
        )


# 싱글톤 인스턴스
document_service = DocumentService()
