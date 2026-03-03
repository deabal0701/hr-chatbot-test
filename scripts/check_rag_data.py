"""RAG 데이터 상태 확인 스크립트"""
import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host='115.68.223.220', port=5432, dbname='hermesdb',
    user='hermesuser', password='hermesuser123!'
)
conn.autocommit = True
cur = conn.cursor(row_factory=dict_row)

# 1. tenant_id별 분포
cur.execute(
    "SELECT tenant_id, COUNT(*) as cnt, "
    "SUM(CASE WHEN indexed THEN 1 ELSE 0 END) as indexed_cnt, "
    "SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_cnt "
    "FROM tb_docs WHERE usage_type = 'rag_knowledge' "
    "GROUP BY tenant_id ORDER BY tenant_id"
)
print('=== tenant_id distribution ===')
for r in cur.fetchall():
    print(r)

# 2. 테넌트 목록
cur.execute('SELECT * FROM tb_tenant ORDER BY tenant_id LIMIT 10')
print('\n=== tenants ===')
for r in cur.fetchall():
    print(dict(r))

# 3. 사용자 목록
cur.execute(
    "SELECT u.user_id, u.login_id, u.tenant_id, r.role_code, u.is_superuser "
    "FROM tb_user u JOIN tb_role r ON u.role_id = r.role_id "
    "ORDER BY u.user_id LIMIT 10"
)
print('\n=== users ===')
for r in cur.fetchall():
    print(r)

conn.close()
