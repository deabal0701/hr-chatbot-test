"""
간단한 설정 테스트 스크립트
전체 시스템이 올바르게 설정되었는지 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """필수 모듈 임포트 테스트"""
    print("=" * 60)
    print("1. 모듈 임포트 테스트")
    print("=" * 60)

    try:
        # 외부 의존성
        import fastapi
        import psycopg
        import openai
        from langchain_openai import ChatOpenAI
        from langgraph.graph import StateGraph
        from pgvector.psycopg import register_vector
        print("✅ 외부 의존성 임포트 성공")

        # 내부 모듈
        from app.config import settings
        from app.models.schemas import SearchRequest
        from app.utils.database import db_manager
        from app.services.vector_store import vector_store
        from app.services.sql_executor import sql_executor
        from app.services.schema_loader import schema_loader
        from app.graphs.rag_graph import rag_graph
        from app.graphs.nl2sql_graph import nl2sql_graph
        print("✅ 내부 모듈 임포트 성공")

        return True
    except Exception as e:
        print(f"❌ 임포트 실패: {e}")
        return False


def test_config():
    """설정 테스트"""
    print("\n" + "=" * 60)
    print("2. 설정 테스트")
    print("=" * 60)

    try:
        from app.config import settings

        print(f"APP_ENV: {settings.app_env}")
        print(f"LOG_LEVEL: {settings.log_level}")
        print(f"EMBEDDING_MODEL: {settings.embedding_model}")
        print(f"LLM_MODEL: {settings.llm_model}")
        print(f"RAG_TOP_K: {settings.rag_top_k}")
        print(f"SQL_MAX_ROWS: {settings.sql_max_rows}")

        # 필수 설정 확인
        assert settings.database_url, "DATABASE_URL이 설정되지 않았습니다"
        assert settings.openai_api_key, "OPENAI_API_KEY가 설정되지 않았습니다"
        assert settings.secret_key, "SECRET_KEY가 설정되지 않았습니다"

        print("✅ 모든 필수 설정 확인 완료")
        return True
    except AssertionError as e:
        print(f"❌ 설정 오류: {e}")
        print("\n.env 파일을 확인하고 필수 값을 설정해주세요:")
        print("  - DATABASE_URL")
        print("  - OPENAI_API_KEY")
        print("  - SECRET_KEY")
        return False
    except Exception as e:
        print(f"❌ 설정 테스트 실패: {e}")
        return False


def test_database():
    """데이터베이스 연결 테스트"""
    print("\n" + "=" * 60)
    print("3. 데이터베이스 연결 테스트")
    print("=" * 60)

    try:
        from app.utils.database import db_manager

        # DB 초기화
        db_manager.initialize()
        print("✅ 커넥션 풀 초기화 성공")

        # 간단한 쿼리 실행
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT version()")
            result = cur.fetchone()
            print(f"PostgreSQL 버전: {result['version'][:50]}...")

            # pgvector 확장 확인
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            vector_ext = cur.fetchone()
            if vector_ext:
                print(f"✅ pgvector 확장 설치됨 (버전: {vector_ext.get('extversion', 'unknown')})")
            else:
                print("⚠️  pgvector 확장이 설치되지 않았습니다")
                print("   설치 방법: scripts/init_db.py 실행")

            # 테이블 확인
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()

            if tables:
                print(f"\n생성된 테이블 ({len(tables)}개):")
                for table in tables:
                    print(f"  - {table['table_name']}")
            else:
                print("\n⚠️  테이블이 생성되지 않았습니다")
                print("   초기화 방법: python scripts/init_db.py")

        db_manager.close()
        print("\n✅ 데이터베이스 연결 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("\n다음을 확인해주세요:")
        print("  1. PostgreSQL이 실행 중인지 확인")
        print("  2. DATABASE_URL이 올바른지 확인")
        print("  3. 데이터베이스가 생성되었는지 확인")
        return False


def test_pydantic_models():
    """Pydantic 모델 테스트"""
    print("\n" + "=" * 60)
    print("4. Pydantic 모델 테스트")
    print("=" * 60)

    try:
        from app.models.schemas import SearchRequest, SearchFilters

        # SearchRequest 생성
        request = SearchRequest(
            query="테스트 질문",
            mode="auto",
            top_k=5
        )

        # model_dump() 테스트 (Pydantic V2)
        data = request.model_dump()
        assert "query" in data
        assert data["query"] == "테스트 질문"

        print("✅ Pydantic V2 호환성 확인")
        print(f"   SearchRequest 생성 성공: {request.query}")

        # SearchFilters 테스트
        filters = SearchFilters(
            department="개발",
            language="ko"
        )
        filter_data = filters.model_dump()
        assert filter_data["department"] == "개발"

        print("✅ Pydantic 모델 테스트 성공")
        return True

    except Exception as e:
        print(f"❌ Pydantic 모델 테스트 실패: {e}")
        return False


def test_type_hints():
    """타입 힌팅 테스트"""
    print("\n" + "=" * 60)
    print("5. 타입 힌팅 테스트")
    print("=" * 60)

    try:
        import sys
        print(f"Python 버전: {sys.version}")

        from app.utils.database import DatabaseManager

        # Optional 타입 힌팅 사용 확인
        db = DatabaseManager()
        assert db.pool is None

        print("✅ 타입 힌팅 호환성 확인 (Python 3.9+ 호환)")
        return True

    except Exception as e:
        print(f"❌ 타입 힌팅 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "HR Chatbot 설정 테스트" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # 1. 임포트 테스트
    results.append(("모듈 임포트", test_imports()))

    # 2. 설정 테스트
    results.append(("설정", test_config()))

    # 3. DB 연결 테스트
    results.append(("데이터베이스", test_database()))

    # 4. Pydantic 테스트
    results.append(("Pydantic 모델", test_pydantic_models()))

    # 5. 타입 힌팅 테스트
    results.append(("타입 힌팅", test_type_hints()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 성공" if passed else "❌ 실패"
        print(f"{name:20s}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n총 {total}개 테스트 중 {passed}개 성공 ({passed * 100 // total}%)")

    if passed == total:
        print("\n🎉 모든 테스트 통과! 시스템이 정상적으로 설정되었습니다.")
        print("\n다음 단계:")
        print("  1. 문서 임베딩: python scripts/embed_documents.py --sample")
        print("  2. 서버 실행: uvicorn app.main:app --reload")
        print("  3. API 문서: http://localhost:8000/docs")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다. 위의 오류 메시지를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
