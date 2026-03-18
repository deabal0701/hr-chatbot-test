-- =============================================================
-- Few-shot INSERT SQL (뷰 11~14: FEEDBACK, HISTORY, PAY_REPORT, DTM_YY_REST)
-- 대상 테이블: hermesdb.tb_docs
-- =============================================================

-- ── 11. V_AI_FEEDBACK (3건) ──

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '평가등급 분포 조회', 'query_example', 'ko',
'평가등급 분포
등급별 직원 수
S등급 몇 명
A등급 직원
평가결과 현황
- V_AI_FEEDBACK
- APPR_GRADE GROUP BY',
'## SQL
```sql
SELECT b.APPR_GRADE, COUNT(DISTINCT b.EMP_ID) AS emp_count
FROM v_ai_feedback b
WHERE b.APPR_GRADE IS NOT NULL
  AND TO_CHAR(b.END_YMD, ''YYYY'') = '':연도''
GROUP BY b.APPR_GRADE
ORDER BY emp_count DESC
```

## 핵심 패턴
- COUNT(DISTINCT EMP_ID): 1인 다건 평가 → 직원 수 기준
- APPR_GRADE: S,A,B,C,D 등
- 연도 필터: END_YMD 기준');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 평균 평가점수 조회', 'query_example', 'ko',
'부서별 평균 평가점수
부서 평가 현황
부서별 평가 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_FEEDBACK
- DEPARTMENT GROUP BY + AVG(APPR_SCORE)',
'## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee a
LEFT JOIN v_ai_feedback b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = ''재직''
  AND b.APPR_SCORE > 0
GROUP BY a.DEPARTMENT
ORDER BY avg_score DESC
```

## 핵심 패턴
- AVG(APPR_SCORE): 평균 평가점수
- APPR_SCORE > 0: 유효 점수만
- 특정 연도: AND TO_CHAR(b.END_YMD, ''YYYY'') = '':연도'' 추가');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직원 평가 이력 조회', 'query_example', 'ko',
'직원 평가 이력
평가 결과 확인
인사평가 기록
평가 점수 확인
- V_AI_EMPLOYEE LEFT JOIN V_AI_FEEDBACK
- EMP_NAME 검색',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.APPR_NM, b.APPR_GRADE, b.APPR_SCORE,
       b.APPR_YMD, b.PEE_OPINION
FROM v_ai_employee a
LEFT JOIN v_ai_feedback b ON a.EMP_ID = b.EMP_ID
WHERE a.EMP_NAME LIKE ''%'' || '':이름'' || ''%''
ORDER BY b.APPR_YMD DESC
```

## 핵심 패턴
- EMP_NAME LIKE: 이름 부분 매칭
- ORDER BY APPR_YMD DESC: 최신 평가 우선');


-- ── 12. V_AI_HISTORY (3건) ──

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 연도 승진자 목록 조회', 'query_example', 'ko',
'올해 승진자
승진한 직원 목록
승진자 수
승진 현황
- V_AI_EMPLOYEE JOIN V_AI_HISTORY
- ASSIGNMENT_TYPE_CODE LIKE 승진',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION, a.GRADE,
       b.ASSIGNMENT_DATE, b.ASSIGNMENT_TYPE_CODE
FROM v_ai_employee a
JOIN v_ai_history b ON a.EMP_ID = b.EMP_ID
WHERE b.ASSIGNMENT_TYPE_CODE LIKE ''%승진%''
  AND TO_CHAR(b.ASSIGNMENT_DATE, ''YYYY'') = '':연도''
ORDER BY b.ASSIGNMENT_DATE DESC
```

## 핵심 패턴
- ASSIGNMENT_TYPE_CODE LIKE ''%승진%'': 승진 발령만
- TO_CHAR(ASSIGNMENT_DATE, ''YYYY''): 연도 필터
- 승진 수: COUNT(DISTINCT b.EMP_ID)');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '휴직 직원 조회', 'query_example', 'ko',
'휴직 중인 직원
현재 휴직자
휴직 현황
육아휴직 직원
- V_AI_EMPLOYEE JOIN V_AI_HISTORY
- LEAVE_OF_ABSENCE_YN = Y',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.ASSIGNMENT_TYPE_CODE, b.ASSIGNMENT_REASON_CODE,
       b.ASSIGNMENT_START_DATE, b.EXPECTED_RETURN_FROM_LEAVE_DATE
FROM v_ai_employee a
JOIN v_ai_history b ON a.EMP_ID = b.EMP_ID
WHERE b.LEAVE_OF_ABSENCE_YN = ''Y''
  AND b.ASSIGNMENT_START_DATE = (
      SELECT MAX(b2.ASSIGNMENT_START_DATE)
      FROM v_ai_history b2
      WHERE b2.EMP_ID = b.EMP_ID
        AND b2.LEAVE_OF_ABSENCE_YN = ''Y''
  )
  AND a.WORK_STATUS = ''재직''
ORDER BY b.ASSIGNMENT_START_DATE DESC
```

## 핵심 패턴
- LEAVE_OF_ABSENCE_YN = ''Y'': 휴직 발령
- MAX(ASSIGNMENT_START_DATE): 최신 휴직 발령
- 육아휴직: ASSIGNMENT_REASON_CODE LIKE ''%육아%'' 추가');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '발령유형별 통계 조회', 'query_example', 'ko',
'발령유형별 현황
인사이동 통계
발령 종류별 건수
전보 승진 휴직 건수
- V_AI_HISTORY
- ASSIGNMENT_TYPE_CODE GROUP BY',
'## SQL
```sql
SELECT b.ASSIGNMENT_TYPE_CODE,
       COUNT(*) AS total_count,
       COUNT(DISTINCT b.EMP_ID) AS emp_count
FROM v_ai_history b
WHERE TO_CHAR(b.ASSIGNMENT_DATE, ''YYYY'') = '':연도''
GROUP BY b.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC
```

## 핵심 패턴
- ASSIGNMENT_TYPE_CODE: 승진, 전보, 전직, 휴직, 복직, 퇴직 등
- COUNT(*): 발령 총 건수
- COUNT(DISTINCT EMP_ID): 대상 직원 수');


-- ── 13. V_AI_PAY_REPORT (3건) ──

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 년월 급여 통계 조회', 'query_example', 'ko',
'이번 달 급여 현황
급여 통계
급여 지급 현황
월별 급여 합계
- V_AI_PAY_REPORT
- PAY_YEAR_MONTH 필터 + SUM',
'## SQL
```sql
SELECT PAYMENT_TYPE_NAME,
       COUNT(*) AS emp_count,
       SUM(GROSS_PAY_AMOUNT) AS total_gross,
       SUM(NET_PAY_AMOUNT) AS total_net,
       ROUND(AVG(NET_PAY_AMOUNT)) AS avg_net
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = '':년월''
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_gross DESC
```

## 핵심 패턴
- PAY_YEAR_MONTH: YYYYMM 형식 (예: 202601)
- PAYMENT_TYPE_NAME: 정기급여, 연차수당, 격려금, 상여 등
- 금액 단위: 원');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 평균 급여 조회', 'query_example', 'ko',
'부서별 평균 급여
부서별 급여 현황
부서 평균 연봉
부서별 실수령액
- V_AI_EMPLOYEE JOIN V_AI_PAY_REPORT
- DEPARTMENT GROUP BY + AVG(NET_PAY_AMOUNT)',
'## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.NET_PAY_AMOUNT)) AS avg_net_pay
FROM v_ai_employee a
JOIN v_ai_pay_report b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = ''재직''
  AND b.PAY_YEAR_MONTH = '':년월''
  AND b.PAYMENT_TYPE_NAME = ''정기급여''
GROUP BY a.DEPARTMENT
ORDER BY avg_net_pay DESC
```

## 핵심 패턴
- JOIN 키: a.EMP_ID = b.EMP_ID
- PAYMENT_TYPE_NAME = ''정기급여'': 상여 제외
- AVG(NET_PAY_AMOUNT): 실지급액 평균');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직원 연간 급여 합계 조회', 'query_example', 'ko',
'연간 급여 합계
올해 급여 총액
직원별 연봉
연간 실수령액
- V_AI_EMPLOYEE JOIN V_AI_PAY_REPORT
- PAY_YEAR 필터 + GROUP BY EMP_ID + SUM',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       SUM(b.GROSS_PAY_AMOUNT) AS annual_gross,
       SUM(b.NET_PAY_AMOUNT) AS annual_net
FROM v_ai_employee a
JOIN v_ai_pay_report b ON a.EMP_ID = b.EMP_ID
WHERE b.PAY_YEAR = '':연도''
  AND a.WORK_STATUS = ''재직''
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT, a.POSITION
ORDER BY annual_gross DESC
```

## 핵심 패턴
- PAY_YEAR: 연간 집계 (YYYY 형식)
- SUM(GROSS_PAY_AMOUNT): 연간 총 지급액
- SUM(NET_PAY_AMOUNT): 연간 실수령액');


-- ── 14. V_AI_DTM_YY_REST (3건) ──

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '올해 잔여연차 조회', 'query_example', 'ko',
'올해 남은 연차
잔여연차 현황
남은 휴가 일수
연차 잔여일
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- REFERENCE_YEAR = 올해 + REMAINING_LEAVE_DAYS',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.TOTAL_LEAVE_DAYS, b.USED_LEAVE_DAYS_PAST,
       b.REMAINING_LEAVE_DAYS
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND a.WORK_STATUS = ''재직''
ORDER BY b.REMAINING_LEAVE_DAYS ASC
```

## 핵심 패턴
- REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY''): 올해 연차
- TOTAL_LEAVE_DAYS: 총 년월차일수
- REMAINING_LEAVE_DAYS: 잔여연차일수
- ORDER BY ASC: 잔여연차 적은 직원 우선');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 연차 사용률 조회', 'query_example', 'ko',
'연차 사용률
부서별 연차 사용 현황
연차 소진률
휴가 사용 통계
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- USED / TOTAL * 100',
'## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.TOTAL_LEAVE_DAYS), 1) AS avg_total,
       ROUND(AVG(b.USED_LEAVE_DAYS_PAST), 1) AS avg_used,
       ROUND(AVG(
           CASE WHEN b.TOTAL_LEAVE_DAYS > 0
                THEN b.USED_LEAVE_DAYS_PAST * 100.0 / b.TOTAL_LEAVE_DAYS
                ELSE 0
           END
       ), 1) AS avg_usage_rate
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND a.WORK_STATUS = ''재직''
GROUP BY a.DEPARTMENT
ORDER BY avg_usage_rate DESC
```

## 핵심 패턴
- 사용률 = USED / TOTAL * 100
- CASE WHEN 0 방어: 총 일수 0인 경우 division by zero 방지
- 부서별: GROUP BY DEPARTMENT');

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '잔여연차 부족 직원 조회', 'query_example', 'ko',
'잔여연차 5일 미만
남은 연차 적은 직원
연차 소진 임박 직원
연차 부족자
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- REMAINING_LEAVE_DAYS < N',
'## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.TOTAL_LEAVE_DAYS,
       b.USED_LEAVE_DAYS_PAST,
       b.REMAINING_LEAVE_DAYS
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND b.REMAINING_LEAVE_DAYS < :일수
  AND a.WORK_STATUS = ''재직''
ORDER BY b.REMAINING_LEAVE_DAYS ASC
```

## 핵심 패턴
- REMAINING_LEAVE_DAYS < :일수 (5 → 5일 미만, 0 → 소진 직원)
- 부서별 수: GROUP BY a.DEPARTMENT + COUNT(*)');


-- ── 기존 few-shot EMPLOYEE_ID → EMP_ID 수정 (3건) ──

UPDATE tb_docs SET
    context_data = REPLACE(context_data, 'EMPLOYEE_ID', 'EMP_ID')
WHERE id IN (954, 955, 979)
  AND doc_type = 'query_example'
  AND context_data LIKE '%EMPLOYEE_ID%';
