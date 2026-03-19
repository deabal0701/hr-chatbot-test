# HR 분석 쿼리 커버리지 테스트 보고서

> 생성일시: 2026-03-19 14:48

## 요약

| 항목 | 건수 | 비율 |
|------|------|------|
| 전체 질의 | 39 | 100% |
| **PASS** (SQL생성+실행+답변) | **31** | **79%** |
| FAIL-SQL (SQL 미생성) | 0 | 0% |
| WARN (빈결과/답변없음) | 7 | 18% |
| FAIL-API (서버오류) | 0 | 0% |

## 상세 결과

| ID | 카테고리 | 질의 | 판정 | rows | ms | SQL (앞 120자) | 오류 |
|----|---------|------|------|------|----|---------------|------|
| A1 | 인력현황 | 부서별 재직자 수를 알려줘 | `PASS` | 74 | 497 | SELECT   DEPARTMENT,   COUNT(DISTINCT EMP_ID) AS emp_count FROM v_ai_employee WHERE WORK_STATUS = '재직' GROUP BY DEPARTME |  |
| A2 | 인력현황 | 최근 5년간 연도별 입사 퇴사 추이를 보여줘 | `WARN-EMPTY` | 0 | 175 | SELECT     year_val,     COUNT(DISTINCT CASE WHEN rec_type = 'HIRE' THEN emp_id END) AS hire_count,     COUNT(DISTINCT C |  |
| A3 | 인력현황 | 부서별 퇴직률을 계산해줘 | `PASS` | 148 | 1138 | WITH active AS (   SELECT     e.DEPARTMENT,     COUNT(DISTINCT e.EMP_ID) AS active_count   FROM v_ai_employee e   WHERE  |  |
| A4 | 인력현황 | 정규직과 기간제 비율 및 부서별 분포는? | `PASS` | 77 | 322 | SELECT     DEPARTMENT,     EMP_TYPE,     COUNT(DISTINCT EMP_ID) AS EMP_COUNT,     ROUND(         COUNT(DISTINCT EMP_ID)  |  |
| A5 | 인력현황 | 근속연수 구간별 인원 분포를 알려줘 (1년미만, 1~3… | `PASS` | 2 | 366 | SELECT     tenure_group,     COUNT(DISTINCT emp_id) AS employee_count FROM (     SELECT         EMP_ID AS emp_id,        |  |
| A6 | 인력현황 | 직급별 평균 근속연수는 얼마야? | `PASS` | 7 | 161 | SELECT   grade,   AVG(CAREER_YEARS) AS avg_career_years FROM v_ai_employee WHERE WORK_STATUS = '재직' GROUP BY grade ORDER |  |
| A7 | 인력현황 | 입사구분별 연도별 추이를 보여줘 | `PASS` | 54 | 340 | SELECT   NVL(e.HIRE_TYPE, '기타') AS hire_type,   TO_CHAR(e.HIRE_DATE, 'YYYY') AS hire_year,   COUNT(DISTINCT e.EMP_ID) AS |  |
| A8 | 인력현황 | 50대 이상 재직자 부서별 분포를 알려줘 | `PASS` | 47 | 328 | SELECT   NVL(DEPARTMENT, '미지정') AS department,   COUNT(DISTINCT EMP_ID) AS employee_count FROM v_ai_employee WHERE WORK_ |  |
| B1 | 급여분석 | 부서별 월평균 실수령액을 보여줘 | `PASS` | 72 | 452 | SELECT   monthly.DEPT AS department,   ROUND(AVG(monthly.DEPT_MONTH_NET_PAY), 0) AS monthly_avg_net_pay FROM (   SELECT  |  |
| B2 | 급여분석 | 직급별 급여 중위값과 상위 25% 하위 25%를 알려줘 | `PASS` | 1 | 965 | SELECT   job_grade_name,   MAX(median_pay) AS median_pay,   MAX(p75_pay) AS p75_pay,   MAX(p25_pay) AS p25_pay FROM (    |  |
| B3 | 급여분석 | 동일 직급 내 남녀 평균 급여 차이를 보여줘 | `PASS` | 32 | 426 | SELECT   p.PAY_GRADE_NAME AS 직급,   AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END) AS 남자_평균급여,   AVG(CASE WHEN |  |
| B4 | 급여분석 | 상여금 지급 총액 부서별 비교를 해줘 | `PASS` | 113 | 322 | SELECT   r.ORGANIZATION_NAME AS department_name,   SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS total_bonus_gross_pay_amount,   SU |  |
| B5 | 급여분석 | 최근 12개월 급여 총지급액 추이를 보여줘 | `WARN-EMPTY` | 0 | 23 | SELECT     r.PAY_YEAR_MONTH,     SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount FROM v_ai_pay_report r WHERE  |  |
| B6 | 급여분석 | 고정비 대비 변동비 비율 부서별 분석을 해줘 | `FAIL-EXEC` | -1 | -1 | SELECT   e.department,   SUM(NVL(p.fixed_cost_amt, 0)) AS fixed_cost_amt,   SUM(NVL(p.variable_cost_amt, 0)) AS variable |  |
| B7 | 급여분석 | 공제와 세금 비율을 직급별로 분석해줘 | `PASS` | 7 | 516 | SELECT   NVL(e.GRADE, '(미지정)') AS GRADE,   COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,   SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS G |  |
| C1 | 평가분석 | 부서별 평가등급 분포를 알려줘 | `PASS` | 25 | 289 | SELECT   dept,   appr_grade,   emp_count,   ROUND(emp_count * 100.0 / SUM(emp_count) OVER (PARTITION BY dept), 1) AS per |  |
| C2 | 평가분석 | 직급별 평균 평가점수를 보여줘 | `PASS` | 7 | 188 | SELECT   e.GRADE AS grade,   ROUND(AVG(f.APPR_SCORE), 2) AS avg_appr_score FROM v_ai_employee e LEFT JOIN v_ai_feedback  |  |
| C3 | 평가분석 | 최근 3년간 S등급을 2회 이상 받은 직원 목록을 알려… | `WARN-EMPTY` | 0 | 113 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   e.DUTY,   e.HIRE_DA |  |
| C4 | 평가분석 | 평가등급별 평균 급여를 보여줘 | `PASS` | 32 | 608 | SELECT   NVL(p.PAY_GRADE_NAME, '미지정') AS 평가등급,   ROUND(AVG(NVL(p.NET_PAY_AMOUNT, 0))) AS 평균_실지급액,   COUNT(DISTINCT e.EMP |  |
| C5 | 평가분석 | 평가등급이 C나 D인 직원의 근속연수 분포는? | `PASS` | 3 | 551 | WITH agg AS (   SELECT     e.CAREER_YEARS AS career_years,     COUNT(DISTINCT e.EMP_ID) AS emp_count   FROM v_ai_employe |  |
| C6 | 평가분석 | 부서별 평가점수 표준편차를 계산해줘 | `PASS` | 74 | 348 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(STDDEV_SAMP(f.APPR_SCORE), 2) AS score_stddev FR |  |
| D1 | 교육분석 | 부서별 1인당 평균 교육시간을 알려줘 | `PASS` | 74 | 377 | SELECT     e.DEPARTMENT,     ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_hour |  |
| D2 | 교육분석 | 부서별 1인당 교육비용을 보여줘 | `PASS` | 74 | 379 | SELECT e.DEPARTMENT,        COUNT(DISTINCT e.EMP_ID) AS emp_count,        ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(CO |  |
| D3 | 교육분석 | 올해 교육 미이수 재직자 목록을 알려줘 | `PASS` | 621 | 683 | SELECT e.EMP_NAME,        e.EMP_ID,        e.DEPARTMENT,        e.POSITION FROM v_ai_employee e WHERE e.WORK_STATUS = '재 |  |
| D4 | 교육분석 | 교육 유형별 집합교육과 사이버교육 참여율 추이를 보여줘 | `WARN-EMPTY` | 0 | 894 | SELECT   y.training_year,   tt.training_type,   NVL(a.participated_cnt, 0) AS participated_cnt,   ROUND(     NVL(a.parti |  |
| D5 | 교육분석 | 토익 800점 이상 직원의 부서별 분포를 알려줘 | `PASS` | 11 | 230 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_employee e INNER JOIN v_ai_language l   ON e.EM |  |
| D6 | 교육분석 | 자격증 보유 현황을 부서별로 분석해줘 | `PASS` | 74 | 208 | SELECT   NVL(e.department, '미지정') AS department,   COUNT(DISTINCT e.emp_id) AS total_employee_count,   COUNT(DISTINCT CA |  |
| D7 | 교육분석 | 대졸 석사 박사 학력 분포를 부서별로 알려줘 | `PASS` | 74 | 222 | SELECT   e.department AS department,   COUNT(DISTINCT CASE WHEN s.education_level = '고졸' THEN e.emp_id END) AS cnt_highs |  |
| E1 | 인사이동 | 최근 3년간 부서별 승진자 수 추이를 보여줘 | `WARN-EMPTY` | 0 | 393 | SELECT     e.department AS department,     TO_CHAR(h.assignment_date, 'YYYY') AS year,     COUNT(DISTINCT e.emp_id) AS p |  |
| E2 | 인사이동 | 직급별 평균 승진 소요연수를 알려줘 | `PASS` | 7 | 111 | SELECT   e.grade AS grade,   AVG(MONTHS_BETWEEN(e.grade_date, e.hire_date) / 12) AS avg_promotion_years FROM v_ai_employ |  |
| E3 | 인사이동 | 5년 이상 동일 직급에 있는 직원 목록을 알려줘 | `PASS` | 20 | 278 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   e.GRADE,   e.GRADE_ |  |
| E4 | 인사이동 | 휴직 유형별 육아휴직 병가 개인휴직 현황을 알려줘 | `PASS` | 3 | 460 | WITH latest_leave AS (     SELECT         h.emp_id,         CASE             WHEN NVL(h.assignment_reason_code, h.assign |  |
| E5 | 인사이동 | 부서 간 전보 빈도를 알려줘 | `WARN-EMPTY` | 0 | 487 | WITH hist AS (   SELECT     h.emp_id,     h.assignment_history_id,     h.assignment_type_code,     h.assignment_departme |  |
| F1 | 연차분석 | 부서별 연차 사용률을 알려줘 | `PASS` | 74 | 324 | SELECT   e.DEPARTMENT,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(AVG(NVL(d.TOTAL_LEAVE_DAYS, 0)), 1) AS avg_total |  |
| F2 | 연차분석 | 잔여연차가 10일 이상인 직원 목록을 알려줘 | `WARN-EMPTY` | 0 | 129 | SELECT e.EMP_NAME,        e.DEPARTMENT,        e.POSITION,        d.REFERENCE_YEAR,        d.TOTAL_LEAVE_DAYS,        d. |  |
| F3 | 연차분석 | 직급별 평균 연차 사용률을 보여줘 | `PASS` | 7 | 328 | SELECT   x.GRADE,   COUNT(DISTINCT x.EMP_ID) AS emp_count,   ROUND(AVG(x.usage_rate), 2) AS avg_usage_rate FROM (   SELE |  |
| G1 | ESG분석 | 직급별 여성 비율을 알려줘 | `PASS` | 7 | 154 | SELECT   e.GRADE AS grade,   COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) AS female_emp_count,   COUNT(DIS |  |
| G2 | ESG분석 | 과장 이상 관리직의 여성 비율은 얼마야? | `PASS` | 1 | 130 | SELECT   COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,   COUNT(DISTINCT EMP_ID) AS total_count |  |
| G3 | ESG분석 | 연령대별 부서 분포를 알려줘 | `PASS` | 138 | 502 | SELECT   age_group,   department,   COUNT(DISTINCT emp_id) AS employee_count FROM (   SELECT     CASE       WHEN TRUNC(M |  |

## 판정 기준

| 판정 | 의미 |
|------|------|
| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 |
| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 (데이터 없음) |
| `WARN-NOANSWER` | 결과는 있으나 LLM 답변 없음 |
| `FAIL-SQL` | SQL 미생성 (few-shot 부족 또는 intent 오류) |
| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 (문법/권한 오류) |
| `FAIL-API` | HTTP 오류 또는 서버 예외 |