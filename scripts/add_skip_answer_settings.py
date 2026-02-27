"""NL2SQL/Agent LLM 답변 생성 스킵 설정 DB 추가 스크립트"""
import psycopg
from psycopg.rows import dict_row

conn_str = 'postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb'

sql = '''
INSERT INTO tb_app_settings (category, "key", value, value_type, description, is_secret, tenant_id)
VALUES
    ('nl2sql', 'skip_answer_generation', 'false', 'bool', 'LLM 답변 생성 스킵 (SQL 결과만 반환)', false, '1'),
    ('agent', 'skip_answer_generation', 'false', 'bool', 'LLM 답변 생성 스킵 (도구 결과만 반환)', false, '1')
ON CONFLICT (category, "key", tenant_id) DO UPDATE SET
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
            WHERE "key" = 'skip_answer_generation'
            ORDER BY category
        """)
        rows = cur.fetchall()
        print('\n추가된 설정:')
        for row in rows:
            print(f"  {row['category']}.{row['key']} = {row['value']} ({row['value_type']}) - {row['description']}")
