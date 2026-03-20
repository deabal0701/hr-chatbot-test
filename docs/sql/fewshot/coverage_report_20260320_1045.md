# HR 분석 쿼리 커버리지 테스트 보고서

> 생성일시: 2026-03-20 10:45

## 요약

| 항목 | 건수 | 비율 |
|------|------|------|
| 전체 질의 | 39 | 100% |
| **PASS** (SQL생성+실행+답변) | **0** | **0%** |
| FAIL-SQL (SQL 미생성) | 0 | 0% |
| WARN (빈결과/답변없음) | 1 | 3% |
| FAIL-API (서버오류) | 19 | 49% |

## 상세 결과

| ID | 카테고리 | 질의 | 판정 | rows | ms | SQL (앞 120자) | 오류 |
|----|---------|------|------|------|----|---------------|------|
| A1 | 인력현황 | 부서별 재직자 수를 알려줘 | `PASS-INCONSISTENT` | 74 | 521 | SELECT DEPARTMENT, COUNT(DISTINCT EMP_ID) AS emp_count FROM v_ai_employee WHERE WORK_STATUS = '재직' GROUP BY DEPARTMENT O |  |
| A2 | 인력현황 | 최근 10년간 연도별 입사 퇴사 추이를 보여줘 | `PASS-INCONSISTENT` | 4 | 212 | SELECT   year_val,   SUM(hire_count) AS hire_count,   SUM(retire_count) AS retire_count FROM (   SELECT     TO_CHAR(HIRE |  |
| A3 | 인력현황 | 부서별 퇴직률을 계산해줘 | `PASS-INCONSISTENT` | 149 | 259 | SELECT   NVL(e.DEPARTMENT, '미지정') AS department,   COUNT(DISTINCT e.EMP_ID) AS total_emp_count,   COUNT(DISTINCT CASE WH |  |
| A4 | 인력현황 | 정규직과 기간제 비율 및 부서별 분포는? | `PASS-INCONSISTENT` | 75 | 55 | SELECT   CASE     WHEN GROUPING(e.department) = 1 THEN '전체'     ELSE e.department   END AS department,   COUNT(DISTINCT  |  |
| A5 | 인력현황 | 근속연수 구간별 인원 분포를 알려줘 (1년미만, 1~3… | `PASS-INCONSISTENT` | 2 | 407 | SELECT   tenure_group,   COUNT(DISTINCT emp_id) AS employee_count FROM (   SELECT     EMP_ID AS emp_id,     CASE       W |  |
| A6 | 인력현황 | 직급별 평균 근속연수는 얼마야? | `PASS-INCONSISTENT` | 7 | 163 | SELECT   e.GRADE AS grade,   AVG(e.CAREER_YEARS) AS avg_career_years FROM v_ai_employee e WHERE e.WORK_STATUS = '재직' GRO |  |
| A7 | 인력현황 | 입사구분별 연도별 추이를 보여줘 | `PASS-INCONSISTENT` | 54 | 341 | SELECT     TO_CHAR(e.HIRE_DATE, 'YYYY') AS hire_year,     NVL(e.HIRE_TYPE, '(미상)') AS hire_type,     COUNT(DISTINCT e.EM |  |
| A8 | 인력현황 | 50대 이상 재직자 부서별 분포를 알려줘 | `PASS-INCONSISTENT` | 47 | 337 | SELECT     e.DEPARTMENT,     COUNT(DISTINCT e.EMP_ID) AS employee_count FROM v_ai_employee e WHERE e.WORK_STATUS = '재직'  |  |
| B1 | 급여분석 | 부서별 월평균 실수령액을 보여줘 | `PASS-INCONSISTENT` | 72 | 4986 | SELECT     t.department,     ROUND(AVG(t.monthly_avg_net_pay)) AS dept_monthly_avg_net_pay FROM (     SELECT         e.d |  |
| B2 | 급여분석 | 직급별 급여 중위값과 상위 25% 하위 25%를 알려줘 | `PASS-INCONSISTENT` | 5 | 432 | SELECT   e.GRADE AS job_grade,   PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY p.NET_PAY_AMOUNT) AS median_net_pay,   PER |  |
| B3 | 급여분석 | 동일 직급 내 남녀 평균 급여 차이를 보여줘 | `PASS-INCONSISTENT` | 3 | 825 | SELECT   e.GRADE,   AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END) AS avg_male_net_pay,   AVG(CASE WHEN e.GENDE |  |
| B4 | 급여분석 | 상여금 지급 총액 부서별 비교를 해줘 | `PASS-INCONSISTENT` | 113 | 328 | SELECT   r.ORGANIZATION_NAME AS department_name,   SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS bonus_total_amount FROM v_ai_pay_r |  |
| B5 | 급여분석 | 최근 12개월 급여 총지급액 추이를 보여줘 | `WARN-EMPTY` | 0 | 24 | SELECT   r.PAY_YEAR_MONTH,   SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS TOTAL_GROSS_PAY_AMOUNT FROM v_ai_pay_report r WHERE r.PA |  |
| B6 | 급여분석 | 고정비 대비 변동비 비율 부서별 분석을 해줘 | `PASS-INCONSISTENT` | 132 | 417 | SELECT     p.ORGANIZATION_NAME AS department_name,     SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS fixed_pay_amount_sum,     SUM( |  |
| B7 | 급여분석 | 공제와 세금 비율을 직급별로 분석해줘 | `PASS-INCONSISTENT` | 32 | 726 | SELECT   NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS 직급,   SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 지급합계,   SUM(NVL(p.DEDUCTION |  |
| C1 | 평가분석 | 부서별 평가등급 분포를 알려줘 | `PASS-INCONSISTENT` | 33 | 486 | SELECT   dept_nm,   appr_grade,   emp_count,   ROUND(emp_count * 100.0 / NULLIF(SUM(emp_count) OVER (PARTITION BY dept_n |  |
| C2 | 평가분석 | 직급별 평균 평가점수를 보여줘 | `PASS-INCONSISTENT` | 3 | 113 | SELECT   e.GRADE AS emp_grade,   AVG(f.APPR_SCORE) AS avg_appr_score,   COUNT(DISTINCT e.EMP_ID) AS emp_count FROM v_ai_ |  |
| C3 | 평가분석 | 최근 10년간 S등급을 2회 이상 받은 직원 목록을 알… | `PASS-INCONSISTENT` | 4 | 249 | SELECT   e.EMP_ID,   e.EMP_NAME,   e.EMP_NAME_ENG,   e.COMPANY_CODE,   e.DEPARTMENT,   e.POSITION,   e.DUTY,   COUNT(DIS |  |
| C4 | 평가분석 | 평가등급별 평균 급여를 보여줘 | `PASS-INCONSISTENT` | 5 | 632 | SELECT   e.GRADE AS 평가등급,   COUNT(DISTINCT e.EMP_ID) AS 인원수,   AVG(p.NET_PAY_AMOUNT) AS 평균_실지급액,   AVG(p.GROSS_PAY_AMOUN |  |
| C5 | 평가분석 | 평가등급이 C나 D인 직원의 근속연수 분포는? | `PASS-INCONSISTENT` | 3 | 563 | SELECT   e.CAREER_YEARS AS career_years,   COUNT(DISTINCT e.EMP_ID) AS emp_count,   ROUND(     COUNT(DISTINCT e.EMP_ID)  |  |
| C6 | 평가분석 | 부서별 평가점수 표준편차를 계산해줘 | `FAIL-API` | -1 | -1 |  |  |
| D1 | 교육분석 | 부서별 1인당 평균 교육시간을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| D2 | 교육분석 | 부서별 1인당 교육비용을 보여줘 | `FAIL-API` | -1 | -1 |  |  |
| D3 | 교육분석 | 올해 교육 미이수 재직자 목록을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| D4 | 교육분석 | 교육 유형별 집합교육과 사이버교육 참여율 추이를 보여줘 | `FAIL-API` | -1 | -1 |  |  |
| D5 | 교육분석 | 토익 800점 이상 직원의 부서별 분포를 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| D6 | 교육분석 | 자격증 보유 현황을 부서별로 분석해줘 | `FAIL-API` | -1 | -1 |  |  |
| D7 | 교육분석 | 대졸 석사 박사 학력 분포를 부서별로 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| E1 | 인사이동 | 최근 10년간 부서별 승진자 수 추이를 보여줘 | `FAIL-API` | -1 | -1 |  |  |
| E2 | 인사이동 | 직급별 평균 승진 소요연수를 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| E3 | 인사이동 | 5년 이상 동일 직급에 있는 직원 목록을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| E4 | 인사이동 | 휴직 유형별 육아휴직 병가 개인휴직 현황을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| E5 | 인사이동 | 부서 간 전보 빈도를 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| F1 | 연차분석 | 부서별 연차 사용률을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| F2 | 연차분석 | 잔여연차가 10일 이상인 직원 목록을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| F3 | 연차분석 | 직급별 평균 연차 사용률을 보여줘 | `FAIL-API` | -1 | -1 |  |  |
| G1 | ESG분석 | 직급별 여성 비율을 알려줘 | `FAIL-API` | -1 | -1 |  |  |
| G2 | ESG분석 | 과장 이상 관리직의 여성 비율은 얼마야? | `FAIL-API` | -1 | -1 |  |  |
| G3 | ESG분석 | 연령대별 부서 분포를 알려줘 | `FAIL-API` | -1 | -1 |  |  |

## 판정 기준

| 판정 | 의미 |
|------|------|
| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 |
| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 (데이터 없음) |
| `WARN-NOANSWER` | 결과는 있으나 LLM 답변 없음 |
| `FAIL-SQL` | SQL 미생성 (few-shot 부족 또는 intent 오류) |
| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 (문법/권한 오류) |
| `FAIL-API` | HTTP 오류 또는 서버 예외 |