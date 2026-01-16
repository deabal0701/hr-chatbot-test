"""벡터 검색 쿼리 테스트"""
import sys
sys.path.insert(0, "d:/900.develop/02.dev/30.python/12.chatbot-mureum")

import numpy as np
from langchain_openai import OpenAIEmbeddings
from app.config import settings
from app.core.database.connection import db_manager

def test_vector_search():
    """벡터 검색 쿼리 테스트"""

    # 1. 테스트 질문
    test_query = "재택근무 정책이 뭐야?"

    # 2. 질문을 벡터로 임베딩
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,  # text-embedding-3-small
        openai_api_key=settings.openai_api_key
    )
    query_embedding = embeddings.embed_query(test_query)
    query_embedding_array = np.array(query_embedding)

    print(f"질문: {test_query}")
    print(f"임베딩 차원: {len(query_embedding)}")
    print(f"임베딩 샘플 (처음 5개): {query_embedding[:5]}")

    # 3. 벡터 검색 쿼리 실행
    top_k = 5
    where_clause = ""  # 필터 없음

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

    # 파라미터: [query_embedding, query_embedding, top_k]
    query_params = [query_embedding_array, query_embedding_array, top_k]

    print(f"\n=== SQL 쿼리 ===")
    print(query_sql)
    print(f"\n=== 파라미터 ===")
    print(f"- embedding 벡터 (2개): {len(query_embedding_array)}차원 배열")
    print(f"- LIMIT: {top_k}")

    # 4. DB 실행
    with db_manager.get_cursor() as cur:
        cur.execute(query_sql, query_params)
        rows = cur.fetchall()

        print(f"\n=== 검색 결과: {len(rows)}개 ===")
        for row in rows:
            distance = row.get('distance', 0)
            similarity = 1.0 - float(distance)  # 유사도 = 1 - 거리

            print(f"\n[ID: {row['id']}]")
            print(f"  제목: {row['title']}")
            print(f"  유형: {row['doc_type']}")
            print(f"  거리(distance): {distance:.4f}")
            print(f"  유사도(similarity): {similarity:.4f}")
            print(f"  내용 미리보기: {row['content'][:100]}...")


if __name__ == "__main__":
    test_vector_search()
