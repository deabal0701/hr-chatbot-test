from typing import Any, Dict, List, Optional

import numpy as np
import psycopg
from openai import OpenAI

from app.config import settings
from app.models.schemas import DocumentSource, SearchFilters
from app.utils.database import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStoreService:
    """벡터 검색 서비스 (pgvector 기반)"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 임베딩"""
        try:
            response = self.client.embeddings.create(
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
            response = self.client.embeddings.create(
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

        # 유사도 임계값
        similarity_threshold = similarity_threshold or settings.rag_similarity_threshold

        # 벡터 검색 쿼리 (L2 거리 사용)
        # L2 거리가 작을수록 유사함. 0에 가까울수록 유사
        # similarity_score는 distance를 역수로 변환 (작은 거리 = 높은 유사도)
        query_sql = f"""
            SELECT
                id,
                title,
                doc_type,
                content,
                metadata,
                language,
                embedding <-> %s AS distance
            FROM hr_docs
            {where_clause}
            ORDER BY embedding <-> %s
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
                # L2 distance를 유사도로 변환
                # 거리 0 = 완전 일치 = 유사도 1.0
                # 거리가 클수록 유사도 낮음
                distance = row.get('distance')

                if distance is None:
                    similarity = 0.0
                else:
                    # distance를 0-1 스케일의 유사도로 변환
                    # 1 / (1 + distance) 공식 사용 (거리 0 -> 유사도 1, 거리 무한대 -> 유사도 0)
                    similarity = 1.0 / (1.0 + float(distance))

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


# 싱글톤 인스턴스
vector_store = VectorStoreService()
