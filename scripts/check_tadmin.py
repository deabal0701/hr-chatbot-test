import psycopg
conn = psycopg.connect('postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb')
cur = conn.cursor(row_factory=psycopg.rows.dict_row)

# tb_role 구조 확인
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tb_role' ORDER BY ordinal_position")
print('tb_role columns:', [r['column_name'] for r in cur.fetchall()])

# tadmin 사용자 조회
cur.execute("SELECT u.user_id, u.login_id, u.display_name, u.is_superuser, u.tenant_id, u.role_id, r.role_code FROM tb_user u LEFT JOIN tb_role r ON u.role_id = r.role_id WHERE u.login_id = 'tadmin'")
row = cur.fetchone()
print('tadmin user:', row)

# 전체 사용자 목록
cur.execute("SELECT u.login_id, u.is_superuser, u.tenant_id, r.role_code FROM tb_user u LEFT JOIN tb_role r ON u.role_id = r.role_id ORDER BY u.login_id")
for r in cur.fetchall():
    print('user:', r)

# 문서 테넌트 분포
cur.execute("SELECT tenant_id, COUNT(*) as doc_count FROM tb_docs GROUP BY tenant_id ORDER BY tenant_id")
for r in cur.fetchall():
    print('tenant docs:', r)

conn.close()
