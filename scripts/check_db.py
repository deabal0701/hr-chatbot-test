"""데이터베이스 확인 및 정리 스크립트"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.database import db_manager
from dotenv import load_dotenv

load_dotenv()

def check_documents():
    """문서 상태 확인"""
    db_manager.initialize()

    with db_manager.get_cursor() as cur:
        # 전체 문서 개수
        cur.execute("SELECT COUNT(*) FROM hr_docs")
        total_count = cur.fetchone()['count']
        print(f"\n총 문서 개수: {total_count}")

        # 임베딩 없는 문서
        cur.execute("SELECT COUNT(*) FROM hr_docs WHERE embedding IS NULL")
        no_embedding = cur.fetchone()['count']
        print(f"임베딩 없는 문서: {no_embedding}개")

        # 중복 문서 찾기 (title과 content가 같은 것)
        cur.execute("""
            SELECT title, COUNT(*) as cnt, array_agg(id ORDER BY id) as ids
            FROM hr_docs
            GROUP BY title, content
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print(f"\n중복 문서 발견: {len(duplicates)}개 그룹")
            for dup in duplicates:
                print(f"  Title: '{dup['title'][:50]}...', Count: {dup['cnt']}, IDs: {dup['ids']}")

        # 모든 문서 목록
        cur.execute("""
            SELECT id, title, doc_type, language,
                   LENGTH(content) as content_length,
                   CASE WHEN embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding
            FROM hr_docs
            ORDER BY id
        """)

        print("\n전체 문서 목록:")
        print("-" * 120)
        for row in cur.fetchall():
            print(f"ID: {row['id']:3d}, Title: {row['title'][:50]:50s}, Type: {row['doc_type']:10s}, "
                  f"Lang: {row['language']}, Content: {row['content_length']:5d}자, Embedding: {row['has_embedding']}")

def delete_duplicates():
    """중복 문서 삭제 (ID가 큰 것만 남기고 삭제)"""
    db_manager.initialize()

    with db_manager.get_cursor(commit=True) as cur:
        # 중복 문서 찾기
        cur.execute("""
            SELECT array_agg(id ORDER BY id) as ids
            FROM hr_docs
            GROUP BY title, content
            HAVING COUNT(*) > 1
        """)

        deleted_count = 0
        for row in cur.fetchall():
            ids = row['ids']
            # 첫 번째 ID 제외하고 모두 삭제
            ids_to_delete = ids[1:]
            for doc_id in ids_to_delete:
                cur.execute("DELETE FROM hr_docs WHERE id = %s", (doc_id,))
                deleted_count += 1
                print(f"문서 ID {doc_id} 삭제됨")

        print(f"\n총 {deleted_count}개 중복 문서 삭제 완료")

if __name__ == "__main__":
    print("=" * 120)
    print("HR Chatbot 데이터베이스 확인")
    print("=" * 120)

    check_documents()

    print("\n" + "=" * 120)
    response = input("\n중복 문서를 삭제하시겠습니까? (yes/no): ")
    if response.lower() == 'yes':
        delete_duplicates()
        print("\n정리 후 상태:")
        check_documents()

    db_manager.close()
