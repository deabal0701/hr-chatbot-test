# -*- coding: utf-8 -*-
import psycopg

conn = psycopg.connect('postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb')
cur = conn.cursor()

# 곽훈도 사원의 평가 데이터 확인
print('=== 곽훈도 사원 평가 데이터 ===')
cur.execute('''
    SELECT f.*
    FROM v_ai_feedback f
    WHERE f.emp_id IN (SELECT emp_id FROM v_ai_employee WHERE emp_name = '곽훈도')
    ORDER BY eval_year DESC
''')
rows = cur.fetchall()
cols = [desc[0] for desc in cur.description]
print('컬럼:', cols)
for row in rows:
    print(row)

print()
print('=== 전체 평가 등급 종류 ===')
cur.execute('SELECT DISTINCT eval_grade FROM v_ai_feedback ORDER BY eval_grade')
grades = cur.fetchall()
for g in grades:
    print(g)

print()
print('=== 곽훈도 S등급 개수 ===')
cur.execute('''
    SELECT COUNT(*)
    FROM v_ai_feedback f
    WHERE f.emp_id IN (SELECT emp_id FROM v_ai_employee WHERE emp_name = '곽훈도')
    AND f.eval_grade = 'S'
''')
print('S등급 횟수:', cur.fetchone()[0])

conn.close()
