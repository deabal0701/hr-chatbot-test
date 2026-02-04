"""NL2SQL 멀티턴 설정 DB 추가 스크립트"""
import psycopg
from psycopg.rows import dict_row

conn_str = 'postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb'

sql = '''
INSERT INTO tb_app_settings (category, "key", value, value_type, description, is_secret)
VALUES
    ('nl2sql', 'multiturn_enabled', 'true', 'bool', '멀티턴 대화 활성화', false),
    ('nl2sql', 'multiturn_max_turns', '5', 'int', '최대 대화 턴 수 (1-20, 기본 5)', false)
ON CONFLICT (category, "key") DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = now();
'''

with psycopg.connect(conn_str, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
        print('INSERT 완료')

        # 확인
        cur.execute("""
            SELECT category, "key", value, value_type, description
            FROM tb_app_settings
            WHERE category = 'nl2sql' AND "key" LIKE 'multiturn%'
            ORDER BY "key"
        """)
        rows = cur.fetchall()
        print('\n추가된 설정:')
        for row in rows:
            print(f"  {row['category']}.{row['key']} = {row['value']} ({row['value_type']}) - {row['description']}")
