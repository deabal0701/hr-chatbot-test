# HR 분석 쿼리 커버리지 테스트 보고서

> 생성일시: 2026-03-20 11:54

## 요약

| 항목 | 건수 | 비율 |
|------|------|------|
| 전체 질의 | 39 | 100% |
| **PASS** (SQL생성+실행+답변) | **1** | **3%** |
| FAIL-SQL (SQL 미생성) | 0 | 0% |
| WARN (빈결과/답변없음) | 6 | 15% |
| FAIL-API (서버오류) | 0 | 0% |

## 상세 결과

| ID | 카테고리 | 질의 | 판정 | rows | ms | SQL (앞 120자) | 오류 |
|----|---------|------|------|------|----|---------------|------|
| A1 | 인력현황 | 부서별 재직자 수를 알려줘 | `PASS-INCONSISTENT` | 74 | 569 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_employee e WHERE e.WORK_STATUS = '재직' GROUP BY  |  |
| A2 | 인력현황 | 최근 10년간 연도별 입사 퇴사 추이를 보여줘 | `PASS-INCONSISTENT` | 5 | 359 | SELECT     year_val,     NVL(SUM(hire_count), 0) AS hire_count,     NVL(SUM(retire_count), 0) AS retire_count FROM (     |  |
| A3 | 인력현황 | 부서별 퇴직률을 계산해줘 | `PASS-INCONSISTENT` | 149 | 275 | SELECT   NVL(e.department, '미지정') AS department,   COUNT(DISTINCT e.emp_id) AS total_employee_cnt,   COUNT(DISTINCT CASE |  |
| A4 | 인력현황 | 정규직과 기간제 비율 및 부서별 분포는? | `PASS-INCONSISTENT` | 77 | 366 | SELECT   department,   emp_type,   emp_count,   ROUND(emp_count / NULLIF(SUM(emp_count) OVER (), 0), 4) AS ratio_overall |  |
| A5 | 인력현황 | 근속연수 구간별 인원 분포를 알려줘 (1년미만, 1~3… | `PASS-INCONSISTENT` | 3 | 393 | SELECT   tenure_group,   COUNT(DISTINCT EMP_ID) AS employee_count FROM (   SELECT     CASE       WHEN CAREER_YEARS < 1 T |  |
| A6 | 인력현황 | 직급별 평균 근속연수는 얼마야? | `PASS-INCONSISTENT` | 7 | 158 | SELECT   e.GRADE AS GRADE,   AVG(e.CAREER_YEARS) AS AVG_CAREER_YEARS FROM v_ai_employee e WHERE e.WORK_STATUS = '재직' GRO |  |
| A7 | 인력현황 | 입사구분별 연도별 추이를 보여줘 | `PASS-INCONSISTENT` | 54 | 337 | SELECT   TO_CHAR(e.HIRE_DATE, 'YYYY') AS HIRE_YEAR,   e.HIRE_TYPE AS HIRE_TYPE,   COUNT(DISTINCT e.EMP_ID) AS HIRE_COUNT |  |
| A8 | 인력현황 | 50대 이상 재직자 부서별 분포를 알려줘 | `PASS-INCONSISTENT` | 47 | 335 | SELECT   NVL(DEPARTMENT, '미지정') AS department,   COUNT(DISTINCT EMP_ID) AS employee_count FROM v_ai_employee WHERE WORK_ |  |
| B1 | 급여분석 | 부서별 월평균 실수령액을 보여줘 | `PASS-INCONSISTENT` | 71 | 2141 | SELECT   e.DEPARTMENT,   ROUND(AVG(m.monthly_net_pay_amount)) AS dept_monthly_avg_net_pay FROM v_ai_employee e LEFT JOIN |  |
| B2 | 급여분석 | 직급별 급여 중위값과 상위 25% 하위 25%를 알려줘 | `PASS-INCONSISTENT` | 1 | 391 | SELECT   p.JOB_GRADE_NAME AS job_grade_name,   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY NVL(p.NET_PAY_AMOUNT, 0)) AS  |  |
| B3 | 급여분석 | 동일 직급 내 남녀 평균 급여 차이를 보여줘 | `PASS-INCONSISTENT` | 1 | 446 | SELECT   NVL(p.JOB_GRADE_NAME, '(미등록)') AS JOB_GRADE_NAME,   ROUND(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT  |  |
| B4 | 급여분석 | 상여금 지급 총액 부서별 비교를 해줘 | `PASS-INCONSISTENT` | 113 | 318 | SELECT   p.ORGANIZATION_NAME AS DEPARTMENT_NAME,   SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS BONUS_GROSS_TOTAL_AMOUNT FROM v_ai |  |
| B5 | 급여분석 | 최근 12개월 급여 총지급액 추이를 보여줘 | `WARN-EMPTY` | 0 | 25 | SELECT   r.PAY_YEAR_MONTH,   SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount FROM v_ai_pay_report r WHERE r.PA |  |
| B6 | 급여분석 | 고정비 대비 변동비 비율 부서별 분석을 해줘 | `PASS-INCONSISTENT` | 182 | 665 | SELECT   NVL(p.ORGANIZATION_NAME, e.DEPARTMENT) AS department_name,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   SUM(NVL(p |  |
| B7 | 급여분석 | 공제와 세금 비율을 직급별로 분석해줘 | `PASS-INCONSISTENT` | 5 | 666 | SELECT   NVL(e.GRADE, '미지정') AS grade,   COUNT(DISTINCT p.EMP_ID) AS emp_count,   SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS tot |  |
| C1 | 평가분석 | 부서별 평가등급 분포를 알려줘 | `PASS-INCONSISTENT` | 25 | 526 | WITH base AS (   SELECT     NVL(e.DEPARTMENT, '미분류') AS DEPARTMENT,     f.APPR_GRADE AS APPR_GRADE,     COUNT(DISTINCT f |  |
| C2 | 평가분석 | 직급별 평균 평가점수를 보여줘 | `PASS-INCONSISTENT` | 3 | 110 | SELECT   e.GRADE AS position_grade,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   AVG(f.APPR_SCORE) AS avg_appr_score FROM  |  |
| C3 | 평가분석 | 최근 10년간 S등급을 2회 이상 받은 직원 목록을 알… | `PASS-INCONSISTENT` | 4 | 247 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   COUNT(DISTINCT f.APPR_ID) AS s_grade_ |  |
| C4 | 평가분석 | 평가등급별 평균 급여를 보여줘 | `PASS-INCONSISTENT` | 4 | 612 | WITH latest_feedback AS (     SELECT emp_id,            company_cd,            appr_grade     FROM (         SELECT fb.E |  |
| C5 | 평가분석 | 평가등급이 C나 D인 직원의 근속연수 분포는? | `PASS-INCONSISTENT` | 3 | 591 | WITH grp AS (   SELECT     e.CAREER_YEARS,     COUNT(DISTINCT e.EMP_ID) AS emp_count   FROM v_ai_feedback f   JOIN v_ai_ |  |
| C6 | 평가분석 | 부서별 평가점수 표준편차를 계산해줘 | `PASS-INCONSISTENT` | 74 | 352 | SELECT e.DEPARTMENT,        COUNT(DISTINCT e.EMP_ID) AS emp_count,        NVL(ROUND(STDDEV_POP(f.APPR_SCORE), 4), 0) AS  |  |
| D1 | 교육분석 | 부서별 1인당 평균 교육시간을 알려줘 | `PASS` | 74 | 383 | SELECT     e.DEPARTMENT,     COUNT(DISTINCT e.EMP_ID) AS emp_count,     ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(C |  |
| D2 | 교육분석 | 부서별 1인당 교육비용을 보여줘 | `PASS-INCONSISTENT` | 74 | 395 | SELECT e.DEPARTMENT AS department,        COUNT(DISTINCT e.EMP_ID) AS emp_count,        SUM(NVL(t.TRAINING_COST, 0)) AS  |  |
| D3 | 교육분석 | 올해 교육 미이수 재직자 목록을 알려줘 | `PASS-INCONSISTENT` | 621 | 707 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.DEPARTMENT,   e.POSITION FROM v_ai_employee e WHERE e.WORK_STATUS = '재직'   AND NOT  |  |
| D4 | 교육분석 | 교육 유형별 집합교육과 사이버교육 참여율 추이를 보여줘 | `WARN-EMPTY` | 0 | 877 | WITH total_active AS (   SELECT COUNT(DISTINCT e.EMP_ID) AS total_emp_count   FROM v_ai_employee e   WHERE e.WORK_STATUS |  |
| D5 | 교육분석 | 토익 800점 이상 직원의 부서별 분포를 알려줘 | `PASS-INCONSISTENT` | 11 | 239 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_employee e JOIN v_ai_language l   ON l.EMP_ID = |  |
| D6 | 교육분석 | 자격증 보유 현황을 부서별로 분석해줘 | `PASS-INCONSISTENT` | 74 | 225 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS dept_employee_count,   COUNT(DISTINCT CASE WHEN l.EMP_ID IS NOT NUL |  |
| D7 | 교육분석 | 대졸 석사 박사 학력 분포를 부서별로 알려줘 | `PASS-INCONSISTENT` | 89 | 342 | SELECT   e.DEPARTMENT,   s.EDUCATION_LEVEL,   COUNT(DISTINCT CASE WHEN s.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS emp_co |  |
| E1 | 인사이동 | 최근 10년간 부서별 승진자 수 추이를 보여줘 | `WARN-EMPTY` | 0 | 389 | SELECT     e.department AS department,     TO_CHAR(h.assignment_date, 'YYYY') AS promotion_year,     COUNT(DISTINCT h.em |  |
| E2 | 인사이동 | 직급별 평균 승진 소요연수를 알려줘 | `WARN-EMPTY` | 0 | 145 | WITH promo AS (     SELECT         e.emp_id,         h.assignment_grade_code,         h.assignment_date,         LAG(h.a |  |
| E3 | 인사이동 | 5년 이상 동일 직급에 있는 직원 목록을 알려줘 | `PASS-INCONSISTENT` | 621 | 148 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   e.GRADE,   FLOOR(MO |  |
| E4 | 인사이동 | 휴직 유형별 육아휴직 병가 개인휴직 현황을 알려줘 | `PASS-INCONSISTENT` | 3 | 238 | WITH latest AS (   SELECT h1.*   FROM v_ai_history h1   JOIN (     SELECT emp_id, MAX(assignment_start_date) AS max_star |  |
| E5 | 인사이동 | 부서 간 전보 빈도를 알려줘 | `WARN-EMPTY` | 0 | 144 | SELECT   src_department_id AS from_department_id,   dest_department_id AS to_department_id,   COUNT(*) AS transfer_frequ |  |
| F1 | 연차분석 | 부서별 연차 사용률을 알려줘 | `PASS-INCONSISTENT` | 74 | 339 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(AVG(NVL(d.TOTAL_LEAVE_DAYS, 0)), 1) AS avg_total |  |
| F2 | 연차분석 | 잔여연차가 10일 이상인 직원 목록을 알려줘 | `WARN-EMPTY` | 0 | 125 | SELECT e.EMP_ID,        e.EMP_NAME,        e.DEPARTMENT,        e.POSITION,        d.REFERENCE_YEAR,        d.REMAINING_ |  |
| F3 | 연차분석 | 직급별 평균 연차 사용률을 보여줘 | `PASS-INCONSISTENT` | 7 | 330 | WITH emp_leave AS (   SELECT       e.EMP_ID,       NVL(e.GRADE, '(미지정)') AS GRADE,       SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) |  |
| G1 | ESG분석 | 직급별 여성 비율을 알려줘 | `PASS-INCONSISTENT` | 7 | 174 | SELECT   NVL(GRADE, '(미정)') AS grade,   COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,   COUNT( |  |
| G2 | ESG분석 | 과장 이상 관리직의 여성 비율은 얼마야? | `PASS-INCONSISTENT` | 1 | 260 | WITH target AS (   SELECT EMP_ID, GENDER   FROM v_ai_employee   WHERE WORK_STATUS = '재직'     AND (       POSITION IN ('과 |  |
| G3 | ESG분석 | 연령대별 부서 분포를 알려줘 | `PASS-INCONSISTENT` | 138 | 514 | SELECT     age_group,     department,     employee_count FROM (     SELECT         CASE             WHEN TRUNC(MONTHS_BE |  |

## 판정 기준

| 판정 | 의미 |
|------|------|
| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 |
| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 (데이터 없음) |
| `WARN-NOANSWER` | 결과는 있으나 LLM 답변 없음 |
| `FAIL-SQL` | SQL 미생성 (few-shot 부족 또는 intent 오류) |
| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 (문법/권한 오류) |
| `FAIL-API` | HTTP 오류 또는 서버 예외 |