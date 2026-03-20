# HR 분석 쿼리 커버리지 테스트 보고서

> 생성일시: 2026-03-20 14:29

## 요약

| 항목 | 건수 | 비율 |
|------|------|------|
| 전체 질의 | 39 | 100% |
| **PASS** (SQL생성+실행+답변) | **2** | **5%** |
| FAIL-SQL (SQL 미생성) | 0 | 0% |
| WARN (빈결과/답변없음) | 6 | 15% |
| FAIL-API (서버오류) | 0 | 0% |

## 상세 결과

| ID | 카테고리 | 질의 | 판정 | rows | ms | SQL (앞 120자) | 오류 |
|----|---------|------|------|------|----|---------------|------|
| A1 | 인력현황 | 부서별 재직자 수를 알려줘 | `PASS` | 74 | 23 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_employee e WHERE e.WORK_STATUS = '재직' GROUP BY  |  |
| A2 | 인력현황 | 최근 10년간 연도별 입사 퇴사 추이를 보여줘 | `PASS-INCONSISTENT` | 4 | 359 | SELECT   year_val,   SUM(hire_count) AS hire_count,   SUM(retire_count) AS retire_count FROM (   SELECT     TO_CHAR(e.HI |  |
| A3 | 인력현황 | 부서별 퇴직률을 계산해줘 | `PASS-INCONSISTENT` | 149 | 255 | SELECT   NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMPLOYEES,   COUNT(DISTINCT CASE WH |  |
| A4 | 인력현황 | 정규직과 기간제 비율 및 부서별 분포는? | `PASS-INCONSISTENT` | 79 | 140 | WITH base AS (     SELECT         CASE             WHEN GROUPING(department) = 1 THEN '전체'             ELSE department   |  |
| A5 | 인력현황 | 근속연수 구간별 인원 분포를 알려줘 (1년미만, 1~3… | `PASS-INCONSISTENT` | 2 | 380 | SELECT     tenure_group,     COUNT(DISTINCT emp_id) AS employee_count FROM (     SELECT         CASE             WHEN CA |  |
| A6 | 인력현황 | 직급별 평균 근속연수는 얼마야? | `PASS-INCONSISTENT` | 7 | 159 | SELECT   GRADE,   AVG(CAREER_YEARS) AS AVG_CAREER_YEARS FROM v_ai_employee WHERE WORK_STATUS = '재직' GROUP BY GRADE ORDER |  |
| A7 | 인력현황 | 입사구분별 연도별 추이를 보여줘 | `PASS-INCONSISTENT` | 54 | 336 | SELECT   TO_CHAR(e.HIRE_DATE, 'YYYY') AS hire_year,   e.HIRE_TYPE AS hire_type,   COUNT(DISTINCT e.EMP_ID) AS hire_count |  |
| A8 | 인력현황 | 50대 이상 재직자 부서별 분포를 알려줘 | `PASS-INCONSISTENT` | 47 | 335 | SELECT   NVL(DEPARTMENT, '미분류') AS department,   COUNT(DISTINCT EMP_ID) AS employee_count FROM v_ai_employee WHERE WORK_ |  |
| B1 | 급여분석 | 부서별 월평균 실수령액을 보여줘 | `PASS-INCONSISTENT` | 74 | 419 | SELECT     e.DEPARTMENT,     COUNT(DISTINCT e.EMP_ID) AS emp_count,     ROUND(         SUM(NVL(p.NET_PAY_AMOUNT, 0)) / N |  |
| B2 | 급여분석 | 직급별 급여 중위값과 상위 25% 하위 25%를 알려줘 | `PASS-INCONSISTENT` | 32 | 464 | SELECT   NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS GRADE_NAME,   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY NVL(p.NET_ |  |
| B3 | 급여분석 | 동일 직급 내 남녀 평균 급여 차이를 보여줘 | `PASS-INCONSISTENT` | 7 | 522 | WITH salary_per_emp AS (     SELECT         EMP_ID,         AVG(NET_PAY_AMOUNT) AS avg_net_pay     FROM v_ai_pay_report  |  |
| B4 | 급여분석 | 상여금 지급 총액 부서별 비교를 해줘 | `PASS-INCONSISTENT` | 113 | 337 | SELECT NVL(p.ORGANIZATION_NAME, '미상') AS DEPARTMENT_NAME,        SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS TOTAL_BONUS_GROSS_AM |  |
| B5 | 급여분석 | 최근 12개월 급여 총지급액 추이를 보여줘 | `WARN-EMPTY` | 0 | 24 | SELECT     r.PAY_YEAR_MONTH,     SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount FROM v_ai_pay_report r WHERE  |  |
| B6 | 급여분석 | 고정비 대비 변동비 비율 부서별 분석을 해줘 | `PASS-INCONSISTENT` | 74 | 234 | SELECT   e.department,   COUNT(DISTINCT CASE WHEN e.emp_type = '정규직' THEN e.emp_id END) AS fixed_cost_emp_cnt,   COUNT(D |  |
| B7 | 급여분석 | 공제와 세금 비율을 직급별로 분석해줘 | `FAIL-EXEC` | -1 | -1 | SELECT   NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS 직급,   SUM(p.GROSS_PAY_AMOUNT) AS 지급합계,   SUM(p.DEDUCTION_AMOUNT) AS  |  |
| C1 | 평가분석 | 부서별 평가등급 분포를 알려줘 | `PASS-INCONSISTENT` | 25 | 508 | SELECT dept,        grade AS appr_grade,        emp_count,        ROUND(emp_count * 100.0 / SUM(emp_count) OVER (PARTITI |  |
| C2 | 평가분석 | 직급별 평균 평가점수를 보여줘 | `PASS-INCONSISTENT` | 7 | 188 | SELECT     e.GRADE AS 직급,     AVG(f.APPR_SCORE) AS 평균평가점수 FROM v_ai_employee e LEFT JOIN v_ai_feedback f     ON e.EMP_ID |  |
| C3 | 평가분석 | 최근 10년간 S등급을 2회 이상 받은 직원 목록을 알… | `PASS-INCONSISTENT` | 4 | 235 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   COUNT(DISTINCT f.APPR_ID) AS s_gr |  |
| C4 | 평가분석 | 평가등급별 평균 급여를 보여줘 | `PASS-INCONSISTENT` | 5 | 541 | SELECT   g.appr_grade,   COUNT(*) AS emp_count,   ROUND(AVG(s.avg_net_pay_amount), 0) AS avg_net_pay_amount FROM (   SEL |  |
| C5 | 평가분석 | 평가등급이 C나 D인 직원의 근속연수 분포는? | `PASS-INCONSISTENT` | 3 | 596 | SELECT   NVL(e.CAREER_YEARS, 0) AS career_years,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(     COUNT(DISTINCT e. |  |
| C6 | 평가분석 | 부서별 평가점수 표준편차를 계산해줘 | `PASS-INCONSISTENT` | 74 | 220 | SELECT e.DEPARTMENT,        ROUND(STDDEV_SAMP(f.APPR_SCORE), 4) AS score_stddev FROM v_ai_employee e LEFT JOIN v_ai_feed |  |
| D1 | 교육분석 | 부서별 1인당 평균 교육시간을 알려줘 | `PASS-INCONSISTENT` | 74 | 385 | SELECT e.DEPARTMENT,        COUNT(DISTINCT e.EMP_ID) AS emp_count,        ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF |  |
| D2 | 교육분석 | 부서별 1인당 교육비용을 보여줘 | `PASS-INCONSISTENT` | 74 | 393 | SELECT e.DEPARTMENT,        COUNT(DISTINCT e.EMP_ID) AS emp_count,        ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(CO |  |
| D3 | 교육분석 | 올해 교육 미이수 재직자 목록을 알려줘 | `PASS-INCONSISTENT` | 621 | 707 | SELECT e.EMP_NAME,        e.DEPARTMENT,        e.POSITION,        e.COMPANY_CODE FROM v_ai_employee e WHERE e.WORK_STATU |  |
| D4 | 교육분석 | 교육 유형별 집합교육과 사이버교육 참여율 추이를 보여줘 | `WARN-EMPTY` | 0 | 467 | WITH base_years AS (   SELECT DISTINCT t.TRAINING_YEAR AS training_year   FROM v_ai_training t   WHERE t.TRAINING_TYPE I |  |
| D5 | 교육분석 | 토익 800점 이상 직원의 부서별 분포를 알려줘 | `PASS-INCONSISTENT` | 11 | 243 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_employee e JOIN v_ai_language l   ON e.EMP_ID = |  |
| D6 | 교육분석 | 자격증 보유 현황을 부서별로 분석해줘 | `PASS-INCONSISTENT` | 74 | 210 | SELECT   NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMP_COUNT,   COUNT(DISTINCT CASE WH |  |
| D7 | 교육분석 | 대졸 석사 박사 학력 분포를 부서별로 알려줘 | `PASS-INCONSISTENT` | 222 | 767 | WITH depts AS (   SELECT DISTINCT e.department   FROM v_ai_employee e   WHERE e.work_status = '재직' ), edu_levels AS (    |  |
| E1 | 인사이동 | 최근 10년간 부서별 승진자 수 추이를 보여줘 | `WARN-EMPTY` | 0 | 277 | SELECT   TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS PROMO_YEAR,   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS PROMOTION_COUNT |  |
| E2 | 인사이동 | 직급별 평균 승진 소요연수를 알려줘 | `WARN-EMPTY` | 0 | 140 | SELECT   h.ASSIGNMENT_GRADE_CODE AS GRADE_CODE,   ROUND(AVG(MONTHS_BETWEEN(h.ASSIGNMENT_DATE, e.HIRE_DATE) / 12), 2) AS  |  |
| E3 | 인사이동 | 5년 이상 동일 직급에 있는 직원 목록을 알려줘 | `PASS-INCONSISTENT` | 621 | 148 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   e.GRADE,   e.GRADE_ |  |
| E4 | 인사이동 | 휴직 유형별 육아휴직 병가 개인휴직 현황을 알려줘 | `PASS-INCONSISTENT` | 3 | 298 | SELECT   c.leave_type,   COUNT(DISTINCT e.emp_id) AS emp_count FROM (   SELECT '육아휴직' AS leave_type FROM DUAL   UNION AL |  |
| E5 | 인사이동 | 부서 간 전보 빈도를 알려줘 | `WARN-EMPTY` | 0 | 281 | WITH hist AS (     SELECT         h.emp_id,         h.assignment_date,         h.assignment_sequence,         h.assignme |  |
| F1 | 연차분석 | 부서별 연차 사용률을 알려줘 | `PASS-INCONSISTENT` | 74 | 331 | SELECT     e.DEPARTMENT,     COUNT(DISTINCT e.EMP_ID) AS emp_count,     ROUND(AVG(NVL(d.TOTAL_LEAVE_DAYS, 0)), 1) AS avg |  |
| F2 | 연차분석 | 잔여연차가 10일 이상인 직원 목록을 알려줘 | `WARN-EMPTY` | 0 | 134 | SELECT e.EMP_ID,        e.EMP_NAME,        e.DEPARTMENT,        e.POSITION,        d.REFERENCE_YEAR,        d.TOTAL_LEAV |  |
| F3 | 연차분석 | 직급별 평균 연차 사용률을 보여줘 | `PASS` | 7 | 301 | SELECT   e.GRADE,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(AVG(     CASE       WHEN NVL(d.TOTAL_LEAVE_DAYS, 0) > |  |
| G1 | ESG분석 | 직급별 여성 비율을 알려줘 | `PASS-INCONSISTENT` | 7 | 157 | SELECT   NVL(GRADE, '(미정)') AS grade,   COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,   COUNT( |  |
| G2 | ESG분석 | 과장 이상 관리직의 여성 비율은 얼마야? | `PASS-INCONSISTENT` | 1 | 121 | SELECT   ROUND(     COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0     / NULLIF(COUNT(DISTINCT EMP_ID),  |  |
| G3 | ESG분석 | 연령대별 부서 분포를 알려줘 | `FAIL-EXEC` | -1 | -1 | SELECT   age_group,   department,   COUNT(DISTINCT emp_id) AS employee_count FROM (   SELECT     emp_id,     department, |  |

## 판정 기준

| 판정 | 의미 |
|------|------|
| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 |
| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 (데이터 없음) |
| `WARN-NOANSWER` | 결과는 있으나 LLM 답변 없음 |
| `FAIL-SQL` | SQL 미생성 (few-shot 부족 또는 intent 오류) |
| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 (문법/권한 오류) |
| `FAIL-API` | HTTP 오류 또는 서버 예외 |