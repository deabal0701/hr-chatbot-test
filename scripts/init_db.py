import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

def init_database():
    """데이터베이스 초기화 스크립트"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL 환경 변수가 설정되지 않았습니다.")
        print(".env 파일을 생성하고 DATABASE_URL을 설정해주세요.")
        sys.exit(1)

    sql_file = project_root / "scripts" / "init_db.sql"

    if not sql_file.exists():
        print(f"ERROR: SQL 파일을 찾을 수 없습니다: {sql_file}")
        sys.exit(1)

    try:
        print(f"데이터베이스 연결 중: {database_url.split('@')[1] if '@' in database_url else database_url}")

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                print(f"\nSQL 파일 실행 중: {sql_file}")

                sql_content = sql_file.read_text(encoding='utf-8')

                # SQL 실행
                cur.execute(sql_content)
                conn.commit()

                print("\n데이터베이스 초기화 완료!")

                # 테이블 확인
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cur.fetchall()

                print("\n생성된 테이블 목록:")
                for table in tables:
                    print(f"  - {table[0]}")

                # hr_docs 테이블의 레코드 수 확인
                cur.execute("SELECT COUNT(*) FROM hr_docs;")
                doc_count = cur.fetchone()[0]
                print(f"\nhr_docs 테이블: {doc_count}개 문서")

                # employee 테이블의 레코드 수 확인
                cur.execute("SELECT COUNT(*) FROM employee;")
                emp_count = cur.fetchone()[0]
                print(f"employee 테이블: {emp_count}명")

                # department 테이블의 레코드 수 확인
                cur.execute("SELECT COUNT(*) FROM department;")
                dept_count = cur.fetchone()[0]
                print(f"department 테이블: {dept_count}개 부서")

    except psycopg.OperationalError as e:
        print(f"\nERROR: 데이터베이스 연결 실패")
        print(f"상세: {e}")
        print("\nPostgreSQL이 실행 중인지, DATABASE_URL이 올바른지 확인해주세요.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: 데이터베이스 초기화 실패")
        print(f"상세: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("HR Chatbot - 데이터베이스 초기화")
    print("=" * 60)
    init_database()
