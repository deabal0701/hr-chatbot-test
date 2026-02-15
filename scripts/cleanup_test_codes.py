"""잔여 테스트 코드 데이터 정리"""
import psycopg

conn = psycopg.connect("postgresql://hermesuser:hermesuser123!@115.68.223.220:5432/hermesdb")
cur = conn.cursor()
cur.execute("DELETE FROM tb_code WHERE code_group IN ('PYTEST_GROUP', 'PYTEST_ORD', 'PYTEST_PUB')")
print(f"Deleted {cur.rowcount} residual test codes")
conn.commit()
conn.close()
