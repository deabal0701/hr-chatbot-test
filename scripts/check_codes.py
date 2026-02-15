"""코드 테이블 데이터 확인"""
import psycopg

conn = psycopg.connect("postgresql://hermesuser:hermesuser123!@115.68.223.220:5432/hermesdb")
cur = conn.cursor()
cur.execute("SELECT code_group, COUNT(*) as cnt FROM tb_code GROUP BY code_group ORDER BY code_group")
rows = cur.fetchall()
print(f"Total groups: {len(rows)}")
for row in rows:
    print(f"  {row[0]}: {row[1]} codes")
cur.execute("SELECT COUNT(*) FROM tb_code")
total = cur.fetchone()[0]
print(f"\nTotal codes: {total}")
conn.close()
