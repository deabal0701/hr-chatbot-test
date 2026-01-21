"""Oracle 스키마 확인 스크립트

설정된 Oracle DB에서 테이블/뷰/Synonym 목록을 확인합니다.
"""
import sys
sys.path.insert(0, 'd:/900.develop/02.dev/30.python/12.chatbot-mureum')

import oracledb
from app.core.config.settings_config import settings_config

try:
    host = settings_config.get_value('external_database', 'host', '')
    port = settings_config.get_value('external_database', 'port', 1521)
    database = settings_config.get_value('external_database', 'database', '')
    username = settings_config.get_value('external_database', 'username', '')
    password = settings_config.get_value('external_database', 'password', '')
    schema = settings_config.get_value('external_database', 'schema', '')

    print(f'설정된 스키마(Owner): {schema}')
    print(f'연결 정보: {host}:{port}/{database}')
    print(f'사용자: {username}')
    print()

    dsn = f'{host}:{port}/{database}'

    with oracledb.connect(user=username, password=password, dsn=dsn) as conn:
        with conn.cursor() as cur:
            # 1. 해당 Owner의 테이블/뷰 수 확인
            cur.execute('''
                SELECT 'TABLES' as type, COUNT(*) as cnt FROM all_tables WHERE owner = UPPER(:1)
                UNION ALL
                SELECT 'VIEWS' as type, COUNT(*) as cnt FROM all_views WHERE owner = UPPER(:1)
            ''', (schema, schema))
            print('=== Owner 별 객체 수 (UPPER 적용) ===')
            for row in cur.fetchall():
                print(f'  {row[0]}: {row[1]}개')

            # 2. USER_SYNONYMS (현재 사용자의 Synonym 목록)
            cur.execute('''
                SELECT synonym_name, table_owner, table_name
                FROM user_synonyms
                ORDER BY synonym_name
            ''')
            print('\n=== USER_SYNONYMS (현재 사용자의 Synonym) ===')
            synonyms = cur.fetchall()
            for row in synonyms:
                print(f'  {row[0]} -> {row[1]}.{row[2]}')
            print(f'  총 {len(synonyms)}개 Synonym')

            # 3. V_AI로 시작하는 Synonym
            cur.execute('''
                SELECT synonym_name, table_owner, table_name
                FROM user_synonyms
                WHERE synonym_name LIKE 'V_AI%'
                ORDER BY synonym_name
            ''')
            print('\n=== V_AI%로 시작하는 Synonym ===')
            v_ai_synonyms = cur.fetchall()
            for row in v_ai_synonyms:
                print(f'  {row[0]} -> {row[1]}.{row[2]}')
            print(f'  총 {len(v_ai_synonyms)}개')

            # 4. 실제 NL2SQL에서 사용할 쿼리 테스트 (수정된 쿼리)
            cur.execute('''
                SELECT table_name FROM all_tables WHERE owner = UPPER(:1)
                UNION
                SELECT view_name AS table_name FROM all_views WHERE owner = UPPER(:1)
                UNION
                SELECT synonym_name AS table_name FROM user_synonyms
                ORDER BY table_name
            ''', (schema, schema))
            print('\n=== 수정된 get_tables_query 결과 (Tables + Views + Synonyms) ===')
            all_objects = cur.fetchall()
            for row in all_objects[:30]:  # 상위 30개만
                print(f'  - {row[0]}')
            print(f'  ... 총 {len(all_objects)}개 객체')

            # 5. 현재 사용자의 기본 스키마 확인
            cur.execute("SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM DUAL")
            current_schema = cur.fetchone()[0]
            print(f'\n=== 현재 사용자 기본 스키마 ===')
            print(f'  CURRENT_SCHEMA: {current_schema}')

except Exception as e:
    print(f'오류: {e}')
    import traceback
    traceback.print_exc()
