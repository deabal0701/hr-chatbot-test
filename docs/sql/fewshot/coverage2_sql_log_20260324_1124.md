# SQL 비교 로그 (실시간)

> 시작: 2026-03-24 11:24:48
> 반복횟수: 2회

## S01 [PASS] 일치
**현재 재직 중인 전체 직원 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS active_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS active_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```

---

## S02 [PASS-INCONSISTENT] **불일치**
**퇴직한 직원은 총 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retired_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
```

---

## S03 [PASS-INCONSISTENT] **불일치**
**남자 직원과 여자 직원 수를 각각 알려줘**

**Run #1**
```sql
SELECT
  GENDER,
  COUNT(DISTINCT EMP_ID) AS EMP_COUNT
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND GENDER IN ('남', '여')
GROUP BY GENDER
ORDER BY EMP_COUNT DESC, GENDER
```

**Run #2**
```sql
SELECT
  GENDER,
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY GENDER
ORDER BY
  CASE GENDER WHEN '남' THEN 1 WHEN '여' THEN 2 ELSE 3 END
```

---

## S04 [PASS] 일치
**2017년에 입사한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2017'
```

**Run #2**
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2017'
```

---

## S05 [PASS-INCONSISTENT] **불일치**
**부서별 직원 수를 알려줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY emp_count DESC
```

---

## S06 [PASS-INCONSISTENT] **불일치**
**직급별 재직자 수는?**

**Run #1**
```sql
SELECT
  e.GRADE,
  COUNT(DISTINCT e.EMP_ID) AS employed_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY employed_count DESC, e.GRADE
```

**Run #2**
```sql
SELECT
  e.GRADE AS grade,
  COUNT(DISTINCT e.EMP_ID) AS active_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY active_emp_count DESC, grade DESC
```

---

## S07 [PASS-INCONSISTENT] **불일치**
**정규직 직원은 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS 정규직_인원
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND EMP_TYPE = '정규직'
```

**Run #2**
```sql
SELECT COUNT(*) AS regular_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND EMP_TYPE = '정규직'
```

---

## S08 [PASS-INCONSISTENT] **불일치**
**계약직 직원 명단을 보여줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.HIRE_DATE,
  e.GRADE,
  e.GENDER,
  e.EMP_TYPE,
  e.WORK_STATUS
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '기간제'
ORDER BY NVL(e.CAREER_MONTHS, 0) DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.DUTY,
  e.HIRE_DATE,
  e.GRADE,
  e.GENDER
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE LIKE '%기간제%'
ORDER BY e.EMP_ID DESC
```

---

## S09 [PASS-INCONSISTENT] **불일치**
**2020년에 입사한 직원 이름과 부서를 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = '2020'
```

**Run #2**
```sql
SELECT
  e.EMP_NAME AS emp_name,
  e.DEPARTMENT AS department
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = '2020'
ORDER BY e.EMP_ID DESC
```

---

## S10 [PASS-INCONSISTENT] **불일치**
**경영지원부 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS active_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND DEPARTMENT = '경영지원부'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.emp_id) AS dept_active_count
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND e.department = '경영지원부'
```

---

## S11 [FAIL-EXEC] **불일치**
**근속연수가 10년 이상인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND CAREER_YEARS >= 10
ORDER BY CAREER_YEARS DESC
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND CAREER_YEARS >= 10
```

---

## S12 [PASS] 일치
**40대 직원은 몇 명이야?**

**Run #1**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49
```

---

## S13 [PASS-INCONSISTENT] **불일치**
**직책별 재직자 수를 알려줘**

**Run #1**
```sql
SELECT
  DUTY,
  COUNT(DISTINCT EMP_ID) AS active_emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DUTY
ORDER BY
  COUNT(DISTINCT EMP_ID) DESC,
  DUTY ASC
```

**Run #2**
```sql
SELECT
  DUTY,
  COUNT(DISTINCT EMP_ID) AS active_emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DUTY
ORDER BY
  CASE DUTY
    WHEN '대표이사' THEN 1
    WHEN '전무이사' THEN 2
    WHEN '상무이사' THEN 3
    WHEN '이사' THEN 4
    WHEN '팀장' THEN 5
    WHEN '부서장' THEN 6
    WHEN '팀원' THEN 7
    WHEN '사원' THEN 8
    ELSE 99
  END,
  COUNT(DISTINCT EMP_ID) DESC
```

---

## S14 [PASS-INCONSISTENT] **불일치**
**2018년에 퇴직한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, 'YYYY') = '2018'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, 'YYYY') = '2018'
```

---

## S15 [PASS-INCONSISTENT] **불일치**
**경력사원으로 입사한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.HIRE_TYPE LIKE '%경력%'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS career_hire_emp_count
FROM v_ai_employee e
WHERE e.HIRE_TYPE LIKE '%경력%'
```

---

## S16 [PASS-INCONSISTENT] **불일치**
**군필자 수는 몇 명이야?**

**Run #1**
```sql
SELECT
  COUNT(DISTINCT e.EMP_ID) AS 군필자_수
FROM v_ai_employee e
JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
 AND m.SERVICE_STATUS = '군필'
WHERE e.WORK_STATUS = '재직'
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT e.EMP_ID) AS 군필자_수
FROM v_ai_employee e
JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND m.SERVICE_STATUS = '군필'
```

---

## S17 [PASS-INCONSISTENT] **불일치**
**2017년 포상을 받은 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_YEAR = '2017'
  AND r.REWARD_TYPE = '포상'
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_reward
WHERE REWARD_TYPE IS NOT NULL
  AND REWARD_YEAR = '2017'
```

---

## S18 [PASS-INCONSISTENT] **불일치**
**2018년 기준 잔여연차가 0인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT d.EMP_ID) AS EMP_COUNT
FROM v_ai_dtm_yy_rest d
JOIN v_ai_employee e
  ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = '2018'
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) = 0
  AND e.WORK_STATUS = '재직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT d.EMP_ID) AS 직원수
FROM v_ai_dtm_yy_rest d
JOIN v_ai_employee e
  ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = '2018'
  AND d.REMAINING_LEAVE_DAYS = 0
  AND e.WORK_STATUS = '재직'
```

---

## S19 [PASS-INCONSISTENT] **불일치**
**2017년 교육을 수료한 건수는?**

**Run #1**
```sql
SELECT COUNT(*) AS completed_count
FROM v_ai_employee e
INNER JOIN v_ai_training t
    ON e.emp_id = t.emp_id
   AND t.training_year = '2017'
   AND t.completion_status = '수료'
WHERE e.work_status = '재직'
```

**Run #2**
```sql
SELECT COUNT(*) AS completion_count
FROM v_ai_employee e
INNER JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.TRAINING_YEAR = '2017'
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
```

---

## S20 [PASS-INCONSISTENT] **불일치**
**S등급을 받은 건수는 총 몇 건이야?**

**Run #1**
```sql
SELECT COUNT(*) AS s_grade_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
```

**Run #2**
```sql
SELECT COUNT(*) AS s_grade_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
```

---

## S21 [PASS-INCONSISTENT] **불일치**
**부서별 평균 근속연수를 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(e.CAREER_YEARS), 2) AS avg_career_years
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_career_years DESC, emp_count DESC
```

**Run #2**
```sql
SELECT
    e.DEPARTMENT,
    ROUND(AVG(e.CAREER_YEARS), 2) AS avg_career_years
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_career_years DESC
```

---

## S22 [PASS] 일치
**연도별 입사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
  COUNT(DISTINCT EMP_ID) AS hire_count
FROM v_ai_employee
WHERE HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
ORDER BY TO_CHAR(HIRE_DATE, 'YYYY') DESC
```

**Run #2**
```sql
SELECT
  TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
  COUNT(DISTINCT EMP_ID) AS hire_count
FROM v_ai_employee
WHERE HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
ORDER BY TO_CHAR(HIRE_DATE, 'YYYY') DESC
```

---

## S23 [PASS-INCONSISTENT] **불일치**
**연도별 퇴사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(RETIRE_DATE, 'YYYY') AS retire_year,
  COUNT(DISTINCT EMP_ID) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(RETIRE_DATE, 'YYYY')
ORDER BY TO_CHAR(RETIRE_DATE, 'YYYY') DESC
```

**Run #2**
```sql
SELECT
  TO_CHAR(e.RETIRE_DATE, 'YYYY') AS retire_year,
  COUNT(DISTINCT e.EMP_ID) AS retire_count
FROM v_ai_employee e
WHERE e.RETIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(e.RETIRE_DATE, 'YYYY')
ORDER BY TO_CHAR(e.RETIRE_DATE, 'YYYY') DESC
```

---

## S24 [PASS-INCONSISTENT] **불일치**
**직급별 남녀 비율을 보여줘**

**Run #1**
```sql
SELECT
  grade,
  gender,
  emp_count,
  ROUND(emp_count * 100.0 / SUM(emp_count) OVER (PARTITION BY grade), 1) AS ratio_pct
FROM (
  SELECT
    NVL(grade, '(미정)') AS grade,
    NVL(gender, '(미정)') AS gender,
    COUNT(DISTINCT emp_id) AS emp_count
  FROM v_ai_employee
  WHERE work_status = '재직'
  GROUP BY
    NVL(grade, '(미정)'),
    NVL(gender, '(미정)')
)
ORDER BY emp_count DESC, grade, gender
```

**Run #2**
```sql
SELECT
  GRADE,
  GENDER,
  COUNT(DISTINCT EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT EMP_ID) * 100.0
    / SUM(COUNT(DISTINCT EMP_ID)) OVER (PARTITION BY GRADE),
    1
  ) AS percentage
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY GRADE, GENDER
ORDER BY emp_count DESC, GRADE, GENDER
```

---

## S25 [PASS-INCONSISTENT] **불일치**
**연령대별 직원 분포를 알려줘**

**Run #1**
```sql
SELECT
  age_group,
  employee_count
FROM (
  SELECT
    CASE
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
      ELSE '기타'
    END AS age_group,
    COUNT(DISTINCT EMP_ID) AS employee_count
  FROM v_ai_employee
  WHERE WORK_STATUS = '재직'
    AND BIRTH_DATE IS NOT NULL
  GROUP BY
    CASE
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
      ELSE '기타'
    END
)
ORDER BY employee_count DESC, age_group
```

**Run #2**
```sql
SELECT
  age_group,
  employee_count
FROM (
  SELECT
    CASE
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
      ELSE '기타'
    END AS age_group,
    COUNT(DISTINCT e.EMP_ID) AS employee_count
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
    AND e.BIRTH_DATE IS NOT NULL
  GROUP BY
    CASE
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
      WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
      ELSE '기타'
    END
)
ORDER BY
  CASE age_group
    WHEN '20대' THEN 1
    WHEN '30대' THEN 2
    WHEN '40대' THEN 3
    WHEN '50대' THEN 4
    WHEN '60대 이상' THEN 5
    ELSE 6
  END,
  employee_count DESC
```

---

## S26 [PASS-INCONSISTENT] **불일치**
**근속연수 구간별 인원 분포를 보여줘**

**Run #1**
```sql
SELECT
  tenure_group,
  employee_count
FROM (
  SELECT
    CASE
      WHEN NVL(CAREER_YEARS, 0) < 1 THEN '1년 미만'
      WHEN NVL(CAREER_YEARS, 0) < 3 THEN '1~3년'
      WHEN NVL(CAREER_YEARS, 0) < 5 THEN '3~5년'
      WHEN NVL(CAREER_YEARS, 0) < 10 THEN '5~10년'
      ELSE '10년 이상'
    END AS tenure_group,
    COUNT(DISTINCT EMP_ID) AS employee_count
  FROM v_ai_employee
  WHERE WORK_STATUS = '재직'
  GROUP BY
    CASE
      WHEN NVL(CAREER_YEARS, 0) < 1 THEN '1년 미만'
      WHEN NVL(CAREER_YEARS, 0) < 3 THEN '1~3년'
      WHEN NVL(CAREER_YEARS, 0) < 5 THEN '3~5년'
      WHEN NVL(CAREER_YEARS, 0) < 10 THEN '5~10년'
      ELSE '10년 이상'
    END
)
ORDER BY
  CASE tenure_group
    WHEN '1년 미만' THEN 1
    WHEN '1~3년' THEN 2
    WHEN '3~5년' THEN 3
    WHEN '5~10년' THEN 4
    WHEN '10년 이상' THEN 5
    ELSE 99
  END
```

**Run #2**
```sql
SELECT
    tenure_group,
    employee_count
FROM (
    SELECT
        CASE
            WHEN e.CAREER_YEARS < 1 THEN '1년 미만'
            WHEN e.CAREER_YEARS < 3 THEN '1~3년'
            WHEN e.CAREER_YEARS < 5 THEN '3~5년'
            WHEN e.CAREER_YEARS < 10 THEN '5~10년'
            ELSE '10년 이상'
        END AS tenure_group,
        CASE
            WHEN e.CAREER_YEARS < 1 THEN 1
            WHEN e.CAREER_YEARS < 3 THEN 2
            WHEN e.CAREER_YEARS < 5 THEN 3
            WHEN e.CAREER_YEARS < 10 THEN 4
            ELSE 5
        END AS tenure_rank,
        COUNT(DISTINCT e.EMP_ID) AS employee_count
    FROM v_ai_employee e
    WHERE e.WORK_STATUS = '재직'
    GROUP BY
        CASE
            WHEN e.CAREER_YEARS < 1 THEN '1년 미만'
            WHEN e.CAREER_YEARS < 3 THEN '1~3년'
            WHEN e.CAREER_YEARS < 5 THEN '3~5년'
            WHEN e.CAREER_YEARS < 10 THEN '5~10년'
            ELSE '10년 이상'
        END,
        CASE
            WHEN e.CAREER_YEARS < 1 THEN 1
            WHEN e.CAREER_YEARS < 3 THEN 2
            WHEN e.CAREER_YEARS < 5 THEN 3
            WHEN e.CAREER_YEARS < 10 THEN 4
            ELSE 5
        END
)
ORDER BY tenure_rank DESC
```

---

## S27 [PASS] 일치
**10명 이상인 부서만 보여줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
HAVING COUNT(DISTINCT e.EMP_ID) >= 10
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
HAVING COUNT(DISTINCT e.EMP_ID) >= 10
ORDER BY emp_count DESC
```

---

## S28 [PASS] 일치
**입사구분별 직원 수를 보여줘**

**Run #1**
```sql
SELECT
  HIRE_TYPE,
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
GROUP BY HIRE_TYPE
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT HIRE_TYPE, COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
GROUP BY HIRE_TYPE
ORDER BY emp_count DESC
```

---

## S29 [PASS-INCONSISTENT] **불일치**
**부서별 최근 입사자 입사일을 알려줘**

**Run #1**
```sql
SELECT
  department,
  emp_id,
  emp_name,
  position,
  hire_date,
  hire_type
FROM (
  SELECT
    e.department,
    e.emp_id,
    e.emp_name,
    e.position,
    e.hire_date,
    e.hire_type,
    ROW_NUMBER() OVER (
      PARTITION BY e.department
      ORDER BY e.hire_date DESC, e.emp_id DESC
    ) AS rn
  FROM v_ai_employee e
  WHERE e.work_status = '재직'
)
WHERE rn = 1
ORDER BY hire_date DESC, emp_id DESC
```

**Run #2**
```sql
SELECT department,
       emp_id,
       emp_name,
       hire_date
FROM (
    SELECT e.department,
           e.emp_id,
           e.emp_name,
           e.hire_date,
           ROW_NUMBER() OVER (
               PARTITION BY e.department
               ORDER BY e.hire_date DESC, e.emp_id DESC
           ) AS rn
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
)
WHERE rn = 1
ORDER BY hire_date DESC, emp_id DESC
```

---

## S30 [PASS-INCONSISTENT] **불일치**
**지급유형별 총 지급액을 보여줘**

**Run #1**
```sql
SELECT
  p.PAYMENT_TYPE_NAME,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_pay_report p
GROUP BY p.PAYMENT_TYPE_NAME
ORDER BY total_gross_pay_amount DESC
```

**Run #2**
```sql
SELECT
  p.PAYMENT_TYPE_NAME,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY p.PAYMENT_TYPE_NAME
ORDER BY total_gross_pay_amount DESC
```

---

## S31 [PASS-INCONSISTENT] **불일치**
**평가등급별 인원 수를 보여줘**

**Run #1**
```sql
SELECT
  f.APPR_GRADE,
  COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IS NOT NULL
GROUP BY f.APPR_GRADE
ORDER BY CASE f.APPR_GRADE
  WHEN 'S' THEN 1
  WHEN 'A' THEN 2
  WHEN 'B' THEN 3
  WHEN 'C' THEN 4
  WHEN 'D' THEN 5
  ELSE 6
END
```

**Run #2**
```sql
SELECT
  f.APPR_GRADE,
  COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON f.EMP_ID = e.EMP_ID
WHERE f.APPR_GRADE IS NOT NULL
  AND e.WORK_STATUS = '재직'
GROUP BY f.APPR_GRADE
ORDER BY emp_count DESC, f.APPR_GRADE DESC
```

---

## S32 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수를 알려줘**

**Run #1**
```sql
SELECT t.TRAINING_TYPE,
       COUNT(*) AS total_count,
       COUNT(DISTINCT t.EMP_ID) AS emp_count,
       COUNT(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 END) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY t.TRAINING_TYPE
ORDER BY total_count DESC
```

**Run #2**
```sql
SELECT NVL(t.TRAINING_TYPE, '미정') AS training_type,
       COUNT(*) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.COMPLETION_STATUS = '수료'
GROUP BY NVL(t.TRAINING_TYPE, '미정')
ORDER BY completed_count DESC, training_type ASC
```

---

## S33 [PASS-INCONSISTENT] **불일치**
**발령유형별 건수를 보여줘**

**Run #1**
```sql
SELECT
    h.ASSIGNMENT_TYPE_CODE,
    COUNT(*) AS total_count
FROM v_ai_history h
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC, h.ASSIGNMENT_TYPE_CODE
```

**Run #2**
```sql
SELECT
  h.ASSIGNMENT_TYPE_CODE,
  COUNT(*) AS total_count,
  COUNT(DISTINCT h.EMP_ID) AS emp_count
FROM v_ai_history h
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC, h.ASSIGNMENT_TYPE_CODE
```

---

## S34 [PASS-INCONSISTENT] **불일치**
**2018년 기준 직원별 잔여연차 상위 10명을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.POSITION,
  e.DEPARTMENT,
  SUM(NVL(r.REMAINING_LEAVE_DAYS, 0)) AS REMAINING_LEAVE_DAYS
FROM V_AI_EMPLOYEE e
JOIN V_AI_DTM_YY_REST r
  ON e.EMP_ID = r.EMP_ID
 AND r.REFERENCE_YEAR = '2018'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.POSITION,
  e.DEPARTMENT
ORDER BY
  SUM(NVL(r.REMAINING_LEAVE_DAYS, 0)) DESC
FETCH FIRST 10 ROWS ONLY
```

**Run #2**
```sql
SELECT emp_id,
       emp_name,
       department,
       remaining_leave_days
FROM (
    SELECT a.emp_id,
           a.emp_name,
           a.department,
           a.remaining_leave_days,
           ROW_NUMBER() OVER (ORDER BY a.remaining_leave_days DESC, a.emp_id) AS rn
    FROM (
        SELECT e.emp_id,
               MAX(e.emp_name) AS emp_name,
               MAX(e.department) AS department,
               NVL(SUM(NVL(r.remaining_leave_days, 0)), 0) AS remaining_leave_days
        FROM v_ai_employee e
        INNER JOIN v_ai_dtm_yy_rest r
                ON e.emp_id = r.emp_id
               AND r.reference_year = '2018'
        WHERE e.work_status = '재직'
        GROUP BY e.emp_id
    ) a
) x
WHERE x.rn <= 10
ORDER BY remaining_leave_days DESC, emp_id
```

---

## S35 [PASS-INCONSISTENT] **불일치**
**연도별 포상 건수 추이를 보여줘**

**Run #1**
```sql
SELECT
  r.REWARD_YEAR AS reward_year,
  COUNT(*) AS reward_count,
  COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
GROUP BY r.REWARD_YEAR
ORDER BY TO_NUMBER(r.REWARD_YEAR) DESC
```

**Run #2**
```sql
SELECT
  r.REWARD_YEAR,
  COUNT(*) AS reward_count,
  COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
  AND r.REWARD_YEAR IS NOT NULL
GROUP BY r.REWARD_YEAR
ORDER BY TO_NUMBER(r.REWARD_YEAR) DESC
```

---

## M01 [PASS-INCONSISTENT] **불일치**
**서울 거주 재직자 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND a.REGION = '서울'
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a
  ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND a.REGION = '서울'
```

---

## M02 [PASS] 일치
**지역별 재직자 분포를 알려줘**

**Run #1**
```sql
SELECT NVL(a.REGION, '미등록') AS region,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_address a
  ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(a.REGION, '미등록')
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT NVL(a.REGION, '미등록') AS region, COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_address a
  ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(a.REGION, '미등록')
ORDER BY emp_count DESC
```

---

## M03 [PASS] 일치
**이전 직장 경력이 있는 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_career c
    WHERE c.EMP_ID = e.EMP_ID
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_career c
    WHERE c.EMP_ID = e.EMP_ID
  )
```

---

## M04 [PASS] 일치
**전직장 경력이 3건 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  COUNT(*) AS career_count
FROM v_ai_employee e
JOIN v_ai_career c
  ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(*) >= 3
ORDER BY career_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  COUNT(*) AS career_count
FROM v_ai_employee e
JOIN v_ai_career c
  ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(*) >= 3
ORDER BY career_count DESC, e.EMP_ID DESC
```

---

## M05 [PASS] 일치
**석사 이상 학력의 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_scholar s
    WHERE s.EMP_ID = e.EMP_ID
      AND s.EDUCATION_LEVEL IN ('석사', '박사')
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_scholar s
    WHERE s.EMP_ID = e.EMP_ID
      AND s.EDUCATION_LEVEL IN ('석사', '박사')
  )
```

---

## M06 [PASS-INCONSISTENT] **불일치**
**컴퓨터공학 전공자 명단을 보여줘**

**Run #1**
```sql
SELECT e.EMP_ID
     , e.EMP_NAME
     , e.EMP_NAME_ENG
     , e.COMPANY_CODE
     , e.POSITION
     , e.DEPARTMENT
     , e.HIRE_DATE
     , s.SCHOOL_NAME
     , s.MAJOR_NAME
     , s.DOUBLE_MAJOR_NAME
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY s.MAJOR_NAME DESC, e.EMP_ID DESC
FETCH FIRST 20 ROWS ONLY
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       s.SCHOOL_NAME,
       s.MAJOR_NAME,
       s.DOUBLE_MAJOR_NAME
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
FETCH FIRST 20 ROWS ONLY
```

---

## M07 [PASS-INCONSISTENT] **불일치**
**배우자가 있는 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS spouse_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION = '처'
  )
```

**Run #2**
```sql
SELECT COUNT(*) AS married_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN ('처', '남편')
  )
```

---

## M08 [WARN-EMPTY] **불일치**
**자녀가 2명 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_NAME,
       e.EMP_ID,
       e.DEPARTMENT,
       COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.RELATION = '자녀'
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
 AND f.RELATION = '자녀'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC, e.EMP_ID DESC
```

---

## M09 [PASS-INCONSISTENT] **불일치**
**토익 800점 이상 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = 'TOEIC'
      AND NVL(l.SCORE, 0) >= 800
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
  )
```

---

## M10 [PASS] 일치
**시험종류별 평균 점수를 알려줘**

**Run #1**
```sql
SELECT
  l.EXAM_TYPE,
  ROUND(AVG(l.SCORE), 1) AS avg_score,
  COUNT(*) AS exam_count,
  COUNT(DISTINCT l.EMP_ID) AS emp_count
FROM v_ai_language l
JOIN v_ai_employee e
  ON l.EMP_ID = e.EMP_ID
WHERE l.SCORE > 0
  AND e.WORK_STATUS = '재직'
GROUP BY l.EXAM_TYPE
ORDER BY avg_score DESC
```

**Run #2**
```sql
SELECT
  l.EXAM_TYPE,
  ROUND(AVG(l.SCORE), 1) AS avg_score,
  COUNT(*) AS exam_count,
  COUNT(DISTINCT l.EMP_ID) AS emp_count
FROM v_ai_language l
JOIN v_ai_employee e
  ON l.EMP_ID = e.EMP_ID
WHERE l.SCORE > 0
  AND e.WORK_STATUS = '재직'
GROUP BY l.EXAM_TYPE
ORDER BY avg_score DESC
```

---

## M11 [PASS-INCONSISTENT] **불일치**
**자격증 보유 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS licensed_employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS license_active_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
  )
```

---

## M12 [WARN-EMPTY] **불일치**
**자격증 3개 이상 보유한 직원 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.EMP_ID,
  e.DEPARTMENT,
  e.POSITION,
  COUNT(*) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(*) >= 3
ORDER BY license_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  COUNT(l.EMP_ID) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT
HAVING COUNT(l.EMP_ID) >= 3
ORDER BY license_count DESC, e.EMP_ID DESC
```

---

## M13 [PASS-INCONSISTENT] **불일치**
**포상을 받은 재직자 부서별 수는?**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
GROUP BY e.DEPARTMENT
ORDER BY emp_count DESC, e.DEPARTMENT DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '(부서없음)') AS department,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
GROUP BY NVL(e.DEPARTMENT, '(부서없음)')
ORDER BY emp_count DESC, department ASC
```

---

## M14 [PASS-INCONSISTENT] **불일치**
**징계를 받은 직원 명단을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.GRADE,
  e.WORK_STATUS
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '징계'
  )
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT DISTINCT
       e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.POSITION,
       e.DEPARTMENT,
       e.DUTY,
       e.HIRE_DATE,
       e.WORK_STATUS
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
      SELECT 1
      FROM v_ai_reward r
      WHERE r.EMP_ID = e.EMP_ID
        AND r.REWARD_TYPE = '징계'
  )
ORDER BY e.EMP_ID DESC
```

---

## M15 [PASS] 일치
**2017년 교육을 수료한 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = '2017'
      AND t.COMPLETION_STATUS = '수료'
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = '2017'
      AND t.COMPLETION_STATUS = '수료'
  )
```

---

## M16 [PASS-INCONSISTENT] **불일치**
**부서별 1인당 평균 교육시간을 알려줘**

**Run #1**
```sql
SELECT
    e.DEPARTMENT,
    COUNT(DISTINCT e.EMP_ID) AS emp_count,
    ROUND(
        SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
        1
    ) AS avg_completion_hours_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
    AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_completion_hours_per_person DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_hours_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_hours_per_person DESC
```

---

## M17 [PASS-INCONSISTENT] **불일치**
**최근 평가에서 S등급을 받은 재직자 명단을 알려줘**

**Run #1**
```sql
WITH latest_eval AS (
  SELECT MAX(f2.APPR_YMD) AS MAX_APPR_YMD
  FROM v_ai_feedback f2
)
SELECT
  x.EMP_ID,
  x.EMP_NAME,
  x.COMPANY_CODE,
  x.DEPARTMENT,
  x.POSITION,
  x.DUTY,
  x.APPR_NM,
  x.PEE_TYPE_NM,
  x.APPR_YMD,
  x.APPR_SCORE,
  x.APPR_GRADE,
  x.RK
FROM (
  SELECT
    e.EMP_ID,
    e.EMP_NAME,
    e.COMPANY_CODE,
    e.DEPARTMENT,
    e.POSITION,
    e.DUTY,
    f.APPR_NM,
    f.PEE_TYPE_NM,
    f.APPR_YMD,
    f.APPR_SCORE,
    f.APPR_GRADE,
    f.RK,
    ROW_NUMBER() OVER (
      PARTITION BY e.EMP_ID
      ORDER BY NVL(f.APPR_SCORE, 0) DESC, f.APPR_ID DESC
    ) AS RN
  FROM v_ai_employee e
  JOIN v_ai_feedback f
    ON f.EMP_ID = e.EMP_ID
   AND f.COMPANY_CD = e.COMPANY_CODE
  CROSS JOIN latest_eval le
  WHERE e.WORK_STATUS = '재직'
    AND f.APPR_YMD = le.MAX_APPR_YMD
    AND f.APPR_GRADE = 'S'
) x
WHERE x.RN = 1
ORDER BY NVL(x.APPR_SCORE, 0) DESC, x.APPR_YMD DESC, x.EMP_ID DESC
```

**Run #2**
```sql
SELECT DISTINCT
       e.EMP_ID,
       e.EMP_NAME,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       e.DUTY,
       f.APPR_YMD AS RECENT_APPR_YMD
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
  AND f.APPR_YMD = (
      SELECT MAX(f2.APPR_YMD)
      FROM v_ai_feedback f2
      WHERE f2.APPR_GRADE = 'S'
  )
ORDER BY e.CAREER_YEARS DESC NULLS LAST, e.EMP_ID DESC
```

---

## M18 [PASS-INCONSISTENT] **불일치**
**부서별 평균 평가점수를 보여줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(f.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND NVL(f.APPR_SCORE, 0) > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(f.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_SCORE IS NOT NULL
  AND f.APPR_SCORE > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC
```

---

## M19 [PASS-INCONSISTENT] **불일치**
**최근 10년간 승진한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS PROMOTED_EMPLOYEE_COUNT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_history h
    WHERE h.EMP_ID = e.EMP_ID
      AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
      AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
      AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
      AND h.ASSIGNMENT_DATE <= SYSDATE
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS PROMOTED_EMPLOYEE_COUNT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_history h
    WHERE h.EMP_ID = e.EMP_ID
      AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
      AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
      AND h.ASSIGNMENT_DATE <= SYSDATE
  )
```

---

## M20 [PASS-INCONSISTENT] **불일치**
**현재 휴직 중인 직원 목록을 보여줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       h.ASSIGNMENT_TYPE_CODE,
       h.ASSIGNMENT_REASON_CODE,
       h.ASSIGNMENT_START_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.LEAVE_OF_ABSENCE_YN = 'Y'
 AND h.ASSIGNMENT_START_DATE = (
     SELECT MAX(h2.ASSIGNMENT_START_DATE)
     FROM v_ai_history h2
     WHERE h2.EMP_ID = e.EMP_ID
       AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
 )
WHERE e.WORK_STATUS = '재직'
ORDER BY h.ASSIGNMENT_START_DATE DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       h.ASSIGNMENT_TYPE_CODE,
       h.ASSIGNMENT_REASON_CODE,
       h.ASSIGNMENT_START_DATE,
       h.ASSIGNMENT_END_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.LEAVE_OF_ABSENCE_YN = 'Y'
 AND h.ASSIGNMENT_START_DATE = (
     SELECT MAX(h2.ASSIGNMENT_START_DATE)
     FROM v_ai_history h2
     WHERE h2.EMP_ID = e.EMP_ID
       AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
 )
WHERE e.WORK_STATUS = '재직'
ORDER BY h.ASSIGNMENT_START_DATE DESC, e.EMP_ID DESC
```

---

## M21 [PASS-INCONSISTENT] **불일치**
**부서별 월평균 실수령액을 보여줘**

**Run #1**
```sql
SELECT
    DEPARTMENT,
    ROUND(AVG(month_total)) AS avg_monthly_net_pay
FROM (
    SELECT
        e.DEPARTMENT,
        p.PAY_YEAR_MONTH,
        SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS month_total
    FROM v_ai_employee e
    JOIN v_ai_pay_report p
        ON e.EMP_ID = p.EMP_ID
    WHERE e.WORK_STATUS = '재직'
    GROUP BY
        e.DEPARTMENT,
        p.PAY_YEAR_MONTH
)
GROUP BY DEPARTMENT
ORDER BY avg_monthly_net_pay DESC
```

**Run #2**
```sql
SELECT DEPARTMENT,
       ROUND(AVG(month_total)) AS avg_monthly_net_pay
FROM (
    SELECT e.DEPARTMENT,
           p.PAY_YEAR_MONTH,
           SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS month_total
    FROM v_ai_employee e
    JOIN v_ai_pay_report p
      ON e.EMP_ID = p.EMP_ID
     AND p.PAYMENT_TYPE_NAME = '정기급여'
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.DEPARTMENT, p.PAY_YEAR_MONTH
)
GROUP BY DEPARTMENT
ORDER BY avg_monthly_net_pay DESC
```

---

## M22 [PASS-INCONSISTENT] **불일치**
**직급별 평균 총지급액을 알려줘**

**Run #1**
```sql
SELECT COALESCE(p.JOB_GRADE_NAME, e.GRADE) AS JOB_GRADE_NAME,
       COUNT(DISTINCT p.EMP_ID) AS EMP_COUNT,
       ROUND(AVG(p.GROSS_PAY_AMOUNT)) AS AVG_GROSS_PAY_AMOUNT
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY COALESCE(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY AVG_GROSS_PAY_AMOUNT DESC
```

**Run #2**
```sql
SELECT p.JOB_GRADE_NAME AS job_grade_name,
       COUNT(DISTINCT p.EMP_ID) AS emp_count,
       ROUND(AVG(p.GROSS_PAY_AMOUNT)) AS avg_gross_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY p.JOB_GRADE_NAME
ORDER BY avg_gross_pay_amount DESC
```

---

## M23 [PASS-INCONSISTENT] **불일치**
**부서별 평균 연차 사용률을 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(NVL(d.TOTAL_LEAVE_DAYS, 0)), 2) AS avg_total_leave_days,
  ROUND(AVG(NVL(d.USED_LEAVE_DAYS_PAST, 0)), 2) AS avg_used_leave_days_past,
  ROUND(AVG(
    CASE
      WHEN NVL(d.TOTAL_LEAVE_DAYS, 0) > 0 THEN NVL(d.USED_LEAVE_DAYS_PAST, 0) * 100.0 / d.TOTAL_LEAVE_DAYS
      ELSE 0
    END
  ), 2) AS avg_leave_usage_rate
FROM v_ai_employee e
LEFT JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
 AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_leave_usage_rate DESC
```

**Run #2**
```sql
WITH emp_leave AS (
  SELECT
    d.emp_id,
    SUM(NVL(d.total_leave_days, 0)) AS total_leave_days_sum,
    SUM(NVL(d.used_leave_days_past, 0)) AS used_leave_days_sum
  FROM v_ai_dtm_yy_rest d
  GROUP BY d.emp_id
)
SELECT
  e.department,
  COUNT(DISTINCT e.emp_id) AS emp_count,
  ROUND(
    AVG(
      CASE
        WHEN NVL(l.total_leave_days_sum, 0) > 0
        THEN l.used_leave_days_sum * 100.0 / l.total_leave_days_sum
        ELSE 0
      END
    ),
    2
  ) AS avg_usage_rate
FROM v_ai_employee e
LEFT JOIN emp_leave l
  ON e.emp_id = l.emp_id
WHERE e.work_status = '재직'
GROUP BY e.department
ORDER BY avg_usage_rate DESC
```

---

## M24 [WARN-EMPTY] 일치
**잔여연차가 10일 이상인 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       d.REFERENCE_YEAR,
       NVL(d.REMAINING_LEAVE_DAYS, 0) AS REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY NVL(d.REMAINING_LEAVE_DAYS, 0) DESC, e.EMP_ID ASC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       d.REFERENCE_YEAR,
       NVL(d.REMAINING_LEAVE_DAYS, 0) AS REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY NVL(d.REMAINING_LEAVE_DAYS, 0) DESC, e.EMP_ID ASC
```

---

## M25 [PASS-INCONSISTENT] **불일치**
**병역유형별 재직자 수를 보여줘**

**Run #1**
```sql
SELECT
  NVL(m.MILITARY_TYPE, '미상') AS military_type,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미상')
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT NVL(m.MILITARY_TYPE, '미등록') AS MILITARY_TYPE,
       COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_military m
       ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미등록')
ORDER BY EMP_COUNT DESC
```

---

## M26 [PASS-INCONSISTENT] **불일치**
**상여금 지급 총액 부서별 비교를 해줘**

**Run #1**
```sql
SELECT
  NVL(p.ORGANIZATION_NAME, '(미상)') AS department_name,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS bonus_total_amount
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME LIKE '%상여%'
GROUP BY NVL(p.ORGANIZATION_NAME, '(미상)')
ORDER BY bonus_total_amount DESC
```

**Run #2**
```sql
SELECT p.ORGANIZATION_NAME AS department_name,
       SUM(p.GROSS_PAY_AMOUNT) AS bonus_total_amount,
       COUNT(DISTINCT p.EMP_ID) AS bonus_employee_count
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '상여'
GROUP BY p.ORGANIZATION_NAME
ORDER BY bonus_total_amount DESC
```

---

## M27 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT NVL(e.department, '미지정') AS department,
       t.training_type,
       COUNT(t.emp_id) AS completed_count,
       COUNT(DISTINCT t.emp_id) AS completed_emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.emp_id = t.emp_id
 AND t.completion_status = '수료'
WHERE e.work_status = '재직'
GROUP BY NVL(e.department, '미지정'),
         t.training_type
ORDER BY completed_count DESC, completed_emp_count DESC
```

**Run #2**
```sql
SELECT
    e.DEPARTMENT,
    t.TRAINING_TYPE,
    COUNT(*) AS completed_count,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.COMPLETION_STATUS = '수료'
GROUP BY
    e.DEPARTMENT,
    t.TRAINING_TYPE
ORDER BY
    completed_count DESC,
    emp_count DESC
```

---

## M28 [PASS-INCONSISTENT] **불일치**
**평가등급이 C 또는 D인 재직자 명단과 부서를 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_feedback f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.APPR_GRADE IN ('C', 'D')
      AND NVL(f.APPR_SCORE, 0) > 0
  )
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT DISTINCT
       e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       f.APPR_GRADE
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
ORDER BY e.EMP_ID DESC
```

---

## M29 [PASS-INCONSISTENT] **불일치**
**부서별 인사이동 건수를 보여줘**

**Run #1**
```sql
SELECT NVL(e.DEPARTMENT, '(미상)') AS department,
       COUNT(*) AS move_count,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE = '이동'
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '(미상)')
ORDER BY move_count DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT AS department,
       COUNT(*) AS move_count,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE = '이동'
GROUP BY e.DEPARTMENT
ORDER BY move_count DESC
```

---

## M30 [PASS-INCONSISTENT] **불일치**
**부서별 학력 분포를 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  s.EDUCATION_LEVEL,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT,
  s.EDUCATION_LEVEL
ORDER BY
  EMP_COUNT DESC,
  e.DEPARTMENT ASC,
  s.EDUCATION_LEVEL ASC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미상') AS EDUCATION_LEVEL,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미상')
ORDER BY EMP_COUNT DESC
```

---

## H01 [PASS-INCONSISTENT] **불일치**
**서울 거주 토익 800점 이상 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       e.HIRE_DATE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = '서울'
  )
  AND EXISTS (
    SELECT 1
    FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LANGUAGE_TYPE = '영어'
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
  )
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.DEPARTMENT,
  e.POSITION,
  e.HIRE_DATE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = '서울'
  )
  AND EXISTS (
    SELECT 1
    FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LANGUAGE_TYPE = '영어'
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
  )
ORDER BY e.EMP_ID DESC
```

---

## H02 [PASS] 일치
**석사 이상 학력이면서 자격증 보유한 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_scholar s
    WHERE s.EMP_ID = e.EMP_ID
      AND s.EDUCATION_LEVEL IN ('석사', '박사')
  )
  AND EXISTS (
    SELECT 1
    FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_scholar s
    WHERE s.EMP_ID = e.EMP_ID
      AND s.EDUCATION_LEVEL IN ('석사', '박사')
  )
  AND EXISTS (
    SELECT 1
    FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
  )
```

---

## H03 [FAIL-SQL] **불일치**
**평가등급별 평균 급여를 보여줘**

**Run #1**
(SQL 없음)

**Run #2**
```sql
WITH latest_feedback AS (
  SELECT emp_id, appr_grade
  FROM (
    SELECT f.emp_id,
           f.appr_grade,
           ROW_NUMBER() OVER (
             PARTITION BY f.emp_id
             ORDER BY f.appr_ymd DESC, f.end_ymd DESC, f.appr_id DESC
           ) AS rn
    FROM v_ai_feedback f
    WHERE NVL(f.appr_score, 0) > 0
      AND f.appr_grade IS NOT NULL
  )
  WHERE rn = 1
),
latest_pay AS (
  SELECT MAX(p.pay_year_month) AS max_pay_year_month
  FROM v_ai_pay_report p
)
SELECT lf.appr_grade,
       COUNT(DISTINCT e.emp_id) AS emp_count,
       ROUND(AVG(p.gross_pay_amount)) AS avg_gross_pay
FROM latest_feedback lf
JOIN v_ai_employee e
  ON e.emp_id = lf.emp_id
JOIN v_ai_pay_report p
  ON p.emp_id = e.emp_id
 AND p.pay_year_month = (SELECT max_pay_year_month FROM latest_pay)
 AND p.payment_type_name = '정기급여'
WHERE e.work_status = '재직'
GROUP BY lf.appr_grade
ORDER BY avg_gross_pay DESC
```

---

## H04 [PASS-INCONSISTENT] **불일치**
**동일 직급 내 남녀 평균 급여 차이를 보여줘**

**Run #1**
```sql
SELECT
  e.GRADE,
  ROUND(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END)) AS male_avg_gross_pay,
  ROUND(AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END)) AS female_avg_gross_pay,
  ROUND(NVL(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END), 0) - NVL(AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END), 0)) AS avg_gross_pay_diff
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
 AND p.PAYMENT_TYPE_NAME = '정기급여'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY
  ABS(
    NVL(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END), 0) - NVL(AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END), 0)
  ) DESC
```

**Run #2**
```sql
SELECT
  COALESCE(p.JOB_GRADE_NAME, e.GRADE) AS job_grade,
  ROUND(AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END), 0) AS avg_salary_male,
  ROUND(AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END), 0) AS avg_salary_female,
  ROUND(
    AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END)
    - AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END)
  , 0) AS avg_salary_diff_male_minus_female,
  COUNT(DISTINCT CASE WHEN e.GENDER = '남' THEN e.EMP_ID END) AS male_emp_count,
  COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) AS female_emp_count
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY COALESCE(p.JOB_GRADE_NAME, e.GRADE)
HAVING COUNT(DISTINCT CASE WHEN e.GENDER = '남' THEN e.EMP_ID END) > 0
   AND COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) > 0
ORDER BY avg_salary_diff_male_minus_female DESC
```

---

## H05 [PASS-INCONSISTENT] **불일치**
**교육 미이수 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.COMPANY_CODE, e.EMP_ID
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND NOT EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.COMPLETION_STATUS = '수료'
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME, e.EMP_ID
```

**Run #2**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND NOT EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = TO_CHAR(SYSDATE, 'YYYY')
      AND t.COMPLETION_STATUS = '수료'
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME
```

---

## H06 [PASS-INCONSISTENT] **불일치**
**근속 10년 이상인데 승진 이력이 없는 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.GRADE,
  e.HIRE_DATE,
  e.CAREER_YEARS,
  e.DUTY,
  e.DUTY_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 10
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       e.GRADE,
       e.HIRE_DATE,
       e.CAREER_YEARS
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 10
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

---

## H07 [PASS-INCONSISTENT] **불일치**
**부서별 평균 교육비용과 평균 평가점수를 비교해줘**

**Run #1**
```sql
SELECT b.DEPARTMENT,
       NVL(t.avg_training_cost, 0) AS avg_training_cost,
       NVL(f.avg_feedback_score, 0) AS avg_feedback_score
FROM (
    SELECT DISTINCT e.DEPARTMENT
    FROM v_ai_employee e
    WHERE e.WORK_STATUS = '재직'
) b
LEFT JOIN (
    SELECT e.DEPARTMENT,
           AVG(t.TRAINING_COST) AS avg_training_cost
    FROM v_ai_employee e
    LEFT JOIN v_ai_training t
           ON e.EMP_ID = t.EMP_ID
          AND t.COMPLETION_STATUS = '수료'
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.DEPARTMENT
) t
    ON b.DEPARTMENT = t.DEPARTMENT
LEFT JOIN (
    SELECT e.DEPARTMENT,
           AVG(f.APPR_SCORE) AS avg_feedback_score
    FROM v_ai_employee e
    LEFT JOIN v_ai_feedback f
           ON e.EMP_ID = f.EMP_ID
          AND f.APPR_SCORE > 0
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.DEPARTMENT
) f
    ON b.DEPARTMENT = f.DEPARTMENT
ORDER BY NVL(t.avg_training_cost, 0) DESC, NVL(f.avg_feedback_score, 0) DESC
```

**Run #2**
```sql
WITH base_dept AS (
    SELECT DISTINCT e.department
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
),
training_by_emp AS (
    SELECT e.department,
           e.emp_id,
           SUM(NVL(t.training_cost, 0)) AS total_training_cost
    FROM v_ai_employee e
    LEFT JOIN v_ai_training t
        ON e.emp_id = t.emp_id
    WHERE e.work_status = '재직'
    GROUP BY e.department, e.emp_id
),
training_by_dept AS (
    SELECT tb.department,
           AVG(tb.total_training_cost) AS avg_training_cost
    FROM training_by_emp tb
    GROUP BY tb.department
),
feedback_by_emp AS (
    SELECT e.department,
           e.emp_id,
           AVG(f.appr_score) AS avg_feedback_score
    FROM v_ai_employee e
    LEFT JOIN v_ai_feedback f
        ON e.emp_id = f.emp_id
        AND f.appr_score IS NOT NULL
    WHERE e.work_status = '재직'
    GROUP BY e.department, e.emp_id
),
feedback_by_dept AS (
    SELECT fb.department,
           AVG(fb.avg_feedback_score) AS avg_feedback_score
    FROM feedback_by_emp fb
    GROUP BY fb.department
)
SELECT bd.department,
       ROUND(NVL(td.avg_training_cost, 0), 2) AS avg_training_cost,
       ROUND(NVL(fd.avg_feedback_score, 0), 2) AS avg_feedback_score
FROM base_dept bd
LEFT JOIN training_by_dept td
    ON bd.department = td.department
LEFT JOIN feedback_by_dept fd
    ON bd.department = fd.department
ORDER BY NVL(td.avg_training_cost, 0) DESC NULLS LAST
```

---

## H08 [PASS-INCONSISTENT] **불일치**
**직급별 평균 실수령액과 최대 최소 급여를 알려줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, e.GRADE) AS JOB_GRADE,
  ROUND(AVG(p.NET_PAY_AMOUNT), 2) AS AVG_NET_PAY_AMOUNT,
  ROUND(MAX(p.NET_PAY_AMOUNT), 2) AS MAX_NET_PAY_AMOUNT,
  ROUND(MIN(p.NET_PAY_AMOUNT), 2) AS MIN_NET_PAY_AMOUNT
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY NVL(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY MAX(p.NET_PAY_AMOUNT) DESC
```

**Run #2**
```sql
SELECT
    COALESCE(p.JOB_GRADE_NAME, e.GRADE) AS 직급,
    COUNT(DISTINCT p.EMP_ID) AS emp_count,
    ROUND(AVG(NVL(p.NET_PAY_AMOUNT, 0))) AS avg_net_pay_amount,
    ROUND(MIN(NVL(p.NET_PAY_AMOUNT, 0))) AS min_net_pay_amount,
    ROUND(MAX(NVL(p.NET_PAY_AMOUNT, 0))) AS max_net_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY COALESCE(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY max_net_pay_amount DESC
```

---

## H09 [PASS-INCONSISTENT] **불일치**
**부서별 퇴직률을 계산해줘**

**Run #1**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT CASE WHEN e.WORK_STATUS = '퇴직' THEN e.EMP_ID END) AS retire_count,
  COUNT(DISTINCT e.EMP_ID) AS total_count,
  ROUND(
    100 * COUNT(DISTINCT CASE WHEN e.WORK_STATUS = '퇴직' THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    2
  ) AS retire_rate_percent
FROM v_ai_employee e
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY retire_rate_percent DESC, retire_count DESC
```

**Run #2**
```sql
SELECT
  NVL(e.department, '미지정') AS department,
  COUNT(DISTINCT e.emp_id) AS total_count,
  COUNT(DISTINCT CASE WHEN e.retire_date IS NOT NULL THEN e.emp_id END) AS retired_count,
  ROUND(
    (COUNT(DISTINCT CASE WHEN e.retire_date IS NOT NULL THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0)) * 100,
    2
  ) AS retire_rate_pct
FROM v_ai_employee e
GROUP BY NVL(e.department, '미지정')
ORDER BY retire_rate_pct DESC NULLS LAST, total_count DESC
```

---

## H10 [PASS-INCONSISTENT] **불일치**
**고정비 대비 변동비 비율을 부서별로 분석해줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  fixed_total,
  variable_total,
  CASE
    WHEN fixed_total = 0 THEN 0
    ELSE ROUND(variable_total / fixed_total, 6)
  END AS variable_to_fixed_ratio
FROM (
  SELECT
    e.DEPARTMENT,
    SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS fixed_total,
    SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS variable_total
  FROM v_ai_employee e
  LEFT JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
)
ORDER BY variable_to_fixed_ratio DESC, DEPARTMENT DESC
```

**Run #2**
```sql
SELECT
  department,
  total_fixed_pay_amount,
  total_variable_pay_amount,
  CASE
    WHEN total_fixed_pay_amount = 0 THEN NULL
    ELSE ROUND(total_variable_pay_amount / total_fixed_pay_amount, 6)
  END AS variable_to_fixed_ratio
FROM (
  SELECT
    e.department,
    SUM(NVL(p.fixed_pay_amount, 0)) AS total_fixed_pay_amount,
    SUM(NVL(p.variable_pay_amount, 0)) AS total_variable_pay_amount
  FROM v_ai_employee e
  LEFT JOIN v_ai_pay_report p
    ON e.emp_id = p.emp_id
  WHERE e.work_status = '재직'
  GROUP BY e.department
)
ORDER BY variable_to_fixed_ratio DESC NULLS LAST, total_variable_pay_amount DESC
```

---

## H11 [PASS-INCONSISTENT] **불일치**
**포상을 받은 직원의 평균 평가점수는?**

**Run #1**
```sql
SELECT
  AVG(f.APPR_SCORE) AS avg_appr_score
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_SCORE > 0
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
```

**Run #2**
```sql
WITH emp_avg AS (
  SELECT
      e.emp_id,
      AVG(f.appr_score) AS emp_avg_score
  FROM v_ai_employee e
  INNER JOIN v_ai_feedback f
    ON f.emp_id = e.emp_id
   AND f.appr_score > 0
  WHERE e.work_status = '재직'
    AND EXISTS (
      SELECT 1
      FROM v_ai_reward r
      WHERE r.emp_id = e.emp_id
        AND r.reward_type = '포상'
    )
  GROUP BY e.emp_id
)
SELECT
  AVG(emp_avg_score) AS avg_appr_score
FROM emp_avg
```

---

## H12 [PASS-INCONSISTENT] **불일치**
**부서별 승진자 수와 승진률을 보여줘**

**Run #1**
```sql
WITH base AS (
  SELECT
      e.department,
      COUNT(DISTINCT e.emp_id) AS total_cnt
  FROM v_ai_employee e
  WHERE e.work_status = '재직'
  GROUP BY e.department
),
promo AS (
  SELECT
      e.department,
      COUNT(DISTINCT h.emp_id) AS promo_cnt
  FROM v_ai_employee e
  INNER JOIN v_ai_history h
    ON e.emp_id = h.emp_id
  WHERE e.work_status = '재직'
    AND h.assignment_type_code IN ('직급변경', '직책변경')
    AND h.assignment_reason_code IN ('승격', '승진')
  GROUP BY e.department
)
SELECT
    b.department,
    NVL(p.promo_cnt, 0) AS promo_cnt,
    b.total_cnt,
    CASE
      WHEN b.total_cnt = 0 THEN 0
      ELSE ROUND(NVL(p.promo_cnt, 0) / b.total_cnt * 100, 2)
    END AS promo_rate_pct
FROM base b
LEFT JOIN promo p
  ON b.department = p.department
ORDER BY promo_cnt DESC, b.department
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '(부서없음)') AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMP_COUNT,
  COUNT(DISTINCT h.EMP_ID) AS PROMOTED_EMP_COUNT,
  ROUND(
    (COUNT(DISTINCT h.EMP_ID) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100,
    2
  ) AS PROMOTION_RATE_PCT
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON h.EMP_ID = e.EMP_ID
 AND (
      h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
      OR (
           h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
           AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
         )
     )
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '(부서없음)')
ORDER BY PROMOTED_EMP_COUNT DESC, PROMOTION_RATE_PCT DESC, DEPARTMENT ASC
```

---

## H13 [PASS-INCONSISTENT] **불일치**
**부서별 1인당 교육비용을 보여줘**

**Run #1**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_training_cost_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
  AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_training_cost_per_person DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(NVL(SUM(t.TRAINING_COST), 0) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 0) AS avg_training_cost_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
  AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_training_cost_per_person DESC
```

---

## H14 [PASS-INCONSISTENT] **불일치**
**직급별 평균 연차 사용률을 보여줘**

**Run #1**
```sql
SELECT
  e.GRADE AS grade,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(
    CASE
      WHEN NVL(d.total_leave_days_sum, 0) > 0
      THEN NVL(d.used_leave_days_past_sum, 0) * 100.0 / d.total_leave_days_sum
      ELSE 0
    END
  ), 2) AS avg_leave_usage_rate
FROM v_ai_employee e
LEFT JOIN (
  SELECT
    r.EMP_ID,
    SUM(NVL(r.TOTAL_LEAVE_DAYS, 0)) AS total_leave_days_sum,
    SUM(NVL(r.USED_LEAVE_DAYS_PAST, 0)) AS used_leave_days_past_sum
  FROM v_ai_dtm_yy_rest r
  WHERE r.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  GROUP BY r.EMP_ID
) d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY avg_leave_usage_rate DESC
```

**Run #2**
```sql
SELECT
    emp_grade AS GRADE,
    COUNT(DISTINCT EMP_ID) AS EMP_COUNT,
    ROUND(AVG(NVL(emp_usage_rate, 0)), 2) AS AVG_LEAVE_USAGE_RATE
FROM (
    SELECT
        e.EMP_ID,
        e.GRADE AS emp_grade,
        CASE
            WHEN SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) > 0
            THEN SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) * 100.0 / SUM(NVL(d.TOTAL_LEAVE_DAYS, 0))
            ELSE 0
        END AS emp_usage_rate
    FROM v_ai_employee e
    LEFT JOIN v_ai_dtm_yy_rest d
        ON e.EMP_ID = d.EMP_ID
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.EMP_ID, e.GRADE
)
GROUP BY emp_grade
ORDER BY AVG_LEAVE_USAGE_RATE DESC
```

---

## H15 [PASS-INCONSISTENT] **불일치**
**부서별 평가점수 표준편차를 계산해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  STDDEV_SAMP(CASE WHEN f.APPR_SCORE > 0 THEN f.APPR_SCORE END) AS STDDEV_SCORE
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY STDDEV_SCORE DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT AS department,
  STDDEV_SAMP(f.APPR_SCORE) AS score_stddev,
  COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY score_stddev DESC NULLS LAST
```

---

## H16 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 급여 총지급액 추이를 보여줘**

**Run #1**
```sql
SELECT
  p.PAY_YEAR,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAY_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -120)
GROUP BY p.PAY_YEAR
ORDER BY TO_NUMBER(p.PAY_YEAR) DESC
```

**Run #2**
```sql
SELECT
  p.PAY_YEAR,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND TO_NUMBER(p.PAY_YEAR) BETWEEN
      TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY'))
      AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
GROUP BY p.PAY_YEAR
ORDER BY total_gross_pay_amount DESC, p.PAY_YEAR DESC
```

---

## H17 [PASS-INCONSISTENT] **불일치**
**정규직과 기간제 비율 및 부서별 분포를 보여줘**

**Run #1**
```sql
WITH dept_agg AS (
    SELECT
        e.department,
        COUNT(DISTINCT CASE WHEN e.emp_type = '정규직' THEN e.emp_id END) AS regular_cnt,
        COUNT(DISTINCT CASE WHEN e.emp_type = '기간제' THEN e.emp_id END) AS contract_cnt,
        COUNT(DISTINCT e.emp_id) AS dept_total_cnt
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
      AND e.emp_type IN ('정규직', '기간제')
    GROUP BY e.department
)
SELECT
    d.department,
    d.regular_cnt,
    d.contract_cnt,
    d.dept_total_cnt,
    ROUND(d.regular_cnt / NULLIF(d.dept_total_cnt, 0) * 100, 2) AS regular_ratio_dept_pct,
    ROUND(d.contract_cnt / NULLIF(d.dept_total_cnt, 0) * 100, 2) AS contract_ratio_dept_pct,
    ROUND(
        (SELECT COUNT(DISTINCT e2.emp_id)
         FROM v_ai_employee e2
         WHERE e2.work_status = '재직' AND e2.emp_type = '정규직')
        /
        NULLIF(
            (SELECT COUNT(DISTINCT e2.emp_id)
             FROM v_ai_employee e2
             WHERE e2.work_status = '재직' AND e2.emp_type IN ('정규직', '기간제')),
            0
        ) * 100
    , 2) AS regular_ratio_overall_pct,
    ROUND(
        (SELECT COUNT(DISTINCT e2.emp_id)
         FROM v_ai_employee e2
         WHERE e2.work_status = '재직' AND e2.emp_type = '기간제')
        /
        NULLIF(
            (SELECT COUNT(DISTINCT e2.emp_id)
             FROM v_ai_employee e2
             WHERE e2.work_status = '재직' AND e2.emp_type IN ('정규직', '기간제')),
            0
        ) * 100
    , 2) AS contract_ratio_overall_pct
FROM dept_agg d
ORDER BY
    (d.regular_cnt + d.contract_cnt) DESC,
    d.department ASC
```

**Run #2**
```sql
SELECT
    t.department,
    t.regular_count,
    t.period_count,
    t.total_count,
    CASE WHEN t.total_count = 0 THEN 0 ELSE t.regular_count / t.total_count END AS regular_ratio,
    CASE WHEN t.total_count = 0 THEN 0 ELSE t.period_count / t.total_count END AS period_ratio
FROM (
    SELECT
        NVL(e.department, '(미지정)') AS department,
        COUNT(DISTINCT CASE WHEN e.emp_type = '정규직' THEN e.emp_id END) AS regular_count,
        COUNT(DISTINCT CASE WHEN e.emp_type = '기간제' THEN e.emp_id END) AS period_count,
        COUNT(DISTINCT e.emp_id) AS total_count
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
      AND e.emp_type IN ('정규직', '기간제')
    GROUP BY NVL(e.department, '(미지정)')
) t
ORDER BY
    t.total_count DESC,
    t.department ASC
```

---

## H18 [PASS-INCONSISTENT] **불일치**
**휴직 유형별 현황을 알려줘**

**Run #1**
```sql
SELECT
  h.ASSIGNMENT_REASON_CODE AS LEAVE_TYPE_CODE,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
JOIN (
  SELECT
    h1.EMP_ID,
    h1.ASSIGNMENT_REASON_CODE,
    h1.ASSIGNMENT_TYPE_CODE,
    h1.ASSIGNMENT_START_DATE
  FROM v_ai_history h1
  WHERE h1.LEAVE_OF_ABSENCE_YN = 'Y'
    AND h1.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = h1.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
    )
) h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  h.ASSIGNMENT_REASON_CODE
ORDER BY
  EMP_COUNT DESC,
  LEAVE_TYPE_CODE ASC
```

**Run #2**
```sql
SELECT
  NVL(h.ASSIGNMENT_REASON_CODE, '(미상)') AS 휴직유형,
  COUNT(DISTINCT CASE WHEN h.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS 인원수
FROM v_ai_employee e
LEFT JOIN (
  SELECT
    h1.EMP_ID,
    h1.ASSIGNMENT_TYPE_CODE,
    h1.ASSIGNMENT_REASON_CODE
  FROM v_ai_history h1
  JOIN (
    SELECT
      EMP_ID,
      MAX(ASSIGNMENT_START_DATE) AS MAX_START_DATE
    FROM v_ai_history
    WHERE LEAVE_OF_ABSENCE_YN = 'Y'
    GROUP BY EMP_ID
  ) h2
    ON h1.EMP_ID = h2.EMP_ID
   AND h1.ASSIGNMENT_START_DATE = h2.MAX_START_DATE
  WHERE h1.LEAVE_OF_ABSENCE_YN = 'Y'
) h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(h.ASSIGNMENT_REASON_CODE, '(미상)')
HAVING COUNT(DISTINCT CASE WHEN h.EMP_ID IS NOT NULL THEN e.EMP_ID END) > 0
ORDER BY 인원수 DESC, 휴직유형 ASC
```

---

## H19 [PASS-INCONSISTENT] **불일치**
**평가등급이 C나 D인 직원의 근속연수 분포를 보여줘**

**Run #1**
```sql
SELECT
  NVL(e.CAREER_YEARS, 0) AS career_years,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT e.EMP_ID) * 100.0 /
    (
      SELECT COUNT(DISTINCT e2.EMP_ID)
      FROM v_ai_employee e2
      WHERE e2.WORK_STATUS = '재직'
        AND EXISTS (
          SELECT 1
          FROM v_ai_feedback f2
          WHERE f2.EMP_ID = e2.EMP_ID
            AND f2.APPR_GRADE IN ('C', 'D')
        )
    ),
    1
  ) AS percentage
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_feedback f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.APPR_GRADE IN ('C', 'D')
  )
GROUP BY NVL(e.CAREER_YEARS, 0)
ORDER BY NVL(e.CAREER_YEARS, 0) DESC
```

**Run #2**
```sql
SELECT
  t.career_years,
  t.emp_count,
  ROUND(t.emp_count * 100.0 / SUM(t.emp_count) OVER (), 1) AS percentage
FROM (
  SELECT
    NVL(e.CAREER_YEARS, 0) AS career_years,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
    AND EXISTS (
      SELECT 1
      FROM v_ai_feedback f
      WHERE f.EMP_ID = e.EMP_ID
        AND f.COMPANY_CD = e.COMPANY_CODE
        AND f.APPR_GRADE IN ('C', 'D')
    )
  GROUP BY NVL(e.CAREER_YEARS, 0)
) t
ORDER BY t.career_years DESC, t.emp_count DESC
```

---

## H20 [PASS-INCONSISTENT] **불일치**
**공제와 세금 비율을 직급별로 분석해줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, e.GRADE) AS JOB_GRADE,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    CASE
      WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
      ELSE (SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))) * 100
    END
  , 2) AS deduction_ratio_pct,
  ROUND(
    CASE
      WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
      ELSE (SUM(NVL(p.TAX_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))) * 100
    END
  , 2) AS tax_ratio_pct,
  ROUND(
    CASE
      WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
      ELSE (SUM(NVL(p.TOTAL_DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))) * 100
    END
  , 2) AS total_deduction_ratio_pct,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY total_gross_pay_amount DESC
```

**Run #2**
```sql
SELECT
    COALESCE(p.JOB_GRADE_NAME, e.GRADE) AS JOB_GRADE,
    COUNT(DISTINCT p.EMP_ID) AS EMP_COUNT,
    ROUND(
        (SUM(NVL(p.TOTAL_DEDUCTION_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
        2
    ) AS TOTAL_DEDUCTION_RATIO_PCT,
    ROUND(
        (SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
        2
    ) AS DEDUCTION_RATIO_PCT,
    ROUND(
        (SUM(NVL(p.TAX_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
        2
    ) AS TAX_RATIO_PCT
FROM v_ai_employee e
JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY COALESCE(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY TAX_RATIO_PCT DESC, TOTAL_DEDUCTION_RATIO_PCT DESC
```

---

## X01 [PASS-INCONSISTENT] **불일치**
**부서별 최고 급여자 이름과 급여를 알려줘**

**Run #1**
```sql
SELECT
  dept.department,
  dept.emp_name,
  dept.net_pay_amount
FROM (
  SELECT
    e.DEPARTMENT AS department,
    e.EMP_NAME AS emp_name,
    p.NET_PAY_AMOUNT AS net_pay_amount,
    RANK() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY p.NET_PAY_AMOUNT DESC NULLS LAST
    ) AS rnk
  FROM v_ai_employee e
  LEFT JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
) dept
WHERE dept.rnk = 1
ORDER BY dept.net_pay_amount DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  department,
  emp_name,
  net_pay
FROM (
  SELECT
    e.DEPARTMENT AS department,
    e.EMP_NAME AS emp_name,
    NVL(p.NET_PAY_AMOUNT, 0) AS net_pay,
    ROW_NUMBER() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY NVL(p.NET_PAY_AMOUNT, 0) DESC, p.PAY_YEAR_MONTH DESC
    ) AS rn
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
)
WHERE rn = 1
ORDER BY net_pay DESC
```

---

## X02 [PASS-INCONSISTENT] **불일치**
**최근 10년간 S등급을 2회 이상 받은 직원 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  COUNT(DISTINCT f.APPR_ID) AS s_grade_count
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
  AND f.APPR_YMD >= ADD_MONTHS(SYSDATE, -120)
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT
HAVING COUNT(DISTINCT f.APPR_ID) >= 2
ORDER BY
  s_grade_count DESC,
  e.EMP_ID ASC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.CAREER_YEARS,
  NVL(s.s_cnt, 0) AS s_grade_cnt
FROM v_ai_employee e
JOIN (
  SELECT
    f.EMP_ID,
    COUNT(DISTINCT f.APPR_ID) AS s_cnt
  FROM v_ai_feedback f
  WHERE f.APPR_GRADE = 'S'
    AND f.APPR_YMD >= ADD_MONTHS(SYSDATE, -120)
    AND f.APPR_YMD <= SYSDATE
  GROUP BY f.EMP_ID
  HAVING COUNT(DISTINCT f.APPR_ID) >= 2
) s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY s.s_cnt DESC, e.EMP_ID ASC
```

---

## X03 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 입사 퇴사 추이를 보여줘**

**Run #1**
```sql
SELECT
  year_val,
  SUM(hire_count) AS hire_count,
  SUM(retire_count) AS retire_count
FROM (
  SELECT
    TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
    COUNT(DISTINCT EMP_ID) AS hire_count,
    0 AS retire_count
  FROM v_ai_employee
  WHERE HIRE_DATE IS NOT NULL
    AND HIRE_DATE >= ADD_MONTHS(SYSDATE, -120)
  GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
  UNION ALL
  SELECT
    TO_CHAR(RETIRE_DATE, 'YYYY') AS year_val,
    0 AS hire_count,
    COUNT(DISTINCT EMP_ID) AS retire_count
  FROM v_ai_employee
  WHERE RETIRE_DATE IS NOT NULL
    AND RETIRE_DATE >= ADD_MONTHS(SYSDATE, -120)
  GROUP BY TO_CHAR(RETIRE_DATE, 'YYYY')
)
GROUP BY year_val
ORDER BY year_val DESC
```

**Run #2**
```sql
SELECT year_val
     , SUM(hire_cnt) AS hire_cnt
     , SUM(retire_cnt) AS retire_cnt
FROM (
    SELECT TO_CHAR(e.HIRE_DATE, 'YYYY') AS year_val
         , COUNT(DISTINCT e.EMP_ID) AS hire_cnt
         , 0 AS retire_cnt
    FROM v_ai_employee e
    WHERE e.HIRE_DATE IS NOT NULL
      AND TO_CHAR(e.HIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
    GROUP BY TO_CHAR(e.HIRE_DATE, 'YYYY')
    UNION ALL
    SELECT TO_CHAR(e.RETIRE_DATE, 'YYYY') AS year_val
         , 0 AS hire_cnt
         , COUNT(DISTINCT e.EMP_ID) AS retire_cnt
    FROM v_ai_employee e
    WHERE e.RETIRE_DATE IS NOT NULL
      AND TO_CHAR(e.RETIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
    GROUP BY TO_CHAR(e.RETIRE_DATE, 'YYYY')
)
GROUP BY year_val
ORDER BY TO_NUMBER(year_val) DESC
```

---

## X04 [PASS-INCONSISTENT] **불일치**
**승진 이력이 없는 근속 5년 이상 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       e.GRADE,
       e.HIRE_DATE,
       e.CAREER_YEARS
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       e.DUTY,
       e.GRADE,
       e.HIRE_DATE,
       e.CAREER_YEARS,
       e.GRADE_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

---

## X05 [PASS-INCONSISTENT] **불일치**
**부서별 교육 수료율을 계산해줘**

**Run #1**
```sql
SELECT
    NVL(e.DEPARTMENT, '미지정') AS department,
    COUNT(DISTINCT e.EMP_ID) AS emp_total,
    COUNT(DISTINCT t.EMP_ID) AS emp_trained,
    COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END) AS emp_completed,
    ROUND(
        CASE
            WHEN COUNT(DISTINCT t.EMP_ID) = 0 THEN 0
            ELSE (COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END) / COUNT(DISTINCT t.EMP_ID)) * 100
        END,
        2
    ) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON t.EMP_ID = e.EMP_ID
GROUP BY NVL(e.DEPARTMENT, '미지정')
HAVING COUNT(DISTINCT e.EMP_ID) > 0
ORDER BY emp_trained DESC, emp_completed DESC, department ASC
```

**Run #2**
```sql
SELECT
  e.department AS department,
  COUNT(DISTINCT e.emp_id) AS total_emp_count,
  COUNT(DISTINCT CASE WHEN t.completion_status = '수료' THEN e.emp_id END) AS completed_emp_count,
  ROUND(
    NVL(COUNT(DISTINCT CASE WHEN t.completion_status = '수료' THEN e.emp_id END), 0)
    / NULLIF(COUNT(DISTINCT e.emp_id), 0) * 100,
    2
  ) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.emp_id = t.emp_id
WHERE e.work_status = '재직'
GROUP BY e.department
ORDER BY completed_emp_count DESC, total_emp_count DESC
```

---

## X06 [PASS-INCONSISTENT] **불일치**
**직급별 평균 승진 소요연수를 알려줘**

**Run #1**
```sql
WITH promo AS (
  SELECT h.EMP_ID,
         MIN(h.ASSIGNMENT_DATE) AS FIRST_PROMO_DATE
  FROM v_ai_history h
  WHERE h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  GROUP BY h.EMP_ID
)
SELECT e.GRADE AS job_grade,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(p.FIRST_PROMO_DATE - e.HIRE_DATE) / 365, 2) AS avg_promotion_years
FROM v_ai_employee e
LEFT JOIN promo p
  ON p.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY avg_promotion_years DESC
```

**Run #2**
```sql
SELECT e.GRADE,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(MONTHS_BETWEEN(e.GRADE_DATE, e.HIRE_DATE) / 12), 2) AS avg_promotion_years
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.GRADE IS NOT NULL
  AND e.GRADE_DATE IS NOT NULL
GROUP BY e.GRADE
ORDER BY avg_promotion_years DESC, e.GRADE
```

---

## X07 [PASS-INCONSISTENT] **불일치**
**부서별 여성 비율을 알려줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_emp_count,
  COUNT(DISTINCT EMP_ID) AS total_emp_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio_percent
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY total_emp_count DESC
```

**Run #2**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,
  COUNT(DISTINCT EMP_ID) AS total_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0 / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio_percent
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY total_count DESC, DEPARTMENT
```

---

## X08 [PASS-INCONSISTENT] **불일치**
**과장 이상 관리직의 여성 비율은?**

**Run #1**
```sql
SELECT ROUND(
         (COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) * 100.0)
         / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)
       , 1) AS FEMALE_RATIO_PERCENT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.POSITION IN ('과장', '차장', '부장', '전무', '상무', '이사', '사장', '회장')
  AND (e.DUTY IN ('팀장', '대표이사') OR e.DUTY LIKE '%팀장%')
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT CASE WHEN e.gender = '여' THEN e.emp_id END) AS female_emp_count,
  COUNT(DISTINCT e.emp_id) AS total_emp_count,
  ROUND(
    NVL(COUNT(DISTINCT CASE WHEN e.gender = '여' THEN e.emp_id END), 0) * 100.0
    / NULLIF(COUNT(DISTINCT e.emp_id), 0),
    1
  ) AS female_ratio_pct
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND e.position IN ('과장', '차장', '부장', '이사', '전무', '상무', '대표이사', '회장')
ORDER BY total_emp_count DESC
```

---

## X09 [PASS-INCONSISTENT] **불일치**
**입사 5년차 이내 직원 중 S등급을 받은 비율은?**

**Run #1**
```sql
SELECT
  ROUND(
    COUNT(DISTINCT CASE
      WHEN EXISTS (
        SELECT 1
        FROM v_ai_feedback f
        WHERE f.EMP_ID = e.EMP_ID
          AND NVL(f.APPR_SCORE, 0) > 0
          AND f.APPR_GRADE = 'S'
      ) THEN e.EMP_ID
    END) * 100.0 / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)
  , 1) AS s_grade_ratio_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

**Run #2**
```sql
SELECT
  ROUND(
    (SUM(CASE
          WHEN EXISTS (
            SELECT 1
            FROM v_ai_feedback f
            WHERE f.EMP_ID = b.EMP_ID
              AND NVL(f.APPR_GRADE, ' ') = 'S'
          ) THEN 1
          ELSE 0
        END) * 100.0) / COUNT(*)
  , 2) AS s_grade_ratio
FROM (
  SELECT DISTINCT e.EMP_ID
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
    AND e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
) b
```

---

## X10 [PASS-INCONSISTENT] **불일치**
**부서별 평가등급 분포를 보여줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  f.APPR_GRADE,
  COUNT(DISTINCT f.EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT f.EMP_ID) * 100.0
    / SUM(COUNT(DISTINCT f.EMP_ID)) OVER (PARTITION BY e.DEPARTMENT),
    1
  ) AS percentage
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IS NOT NULL
GROUP BY
  e.DEPARTMENT,
  f.APPR_GRADE
ORDER BY
  emp_count DESC,
  e.DEPARTMENT,
  f.APPR_GRADE
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  NVL(f.APPR_GRADE, '미평가') AS APPR_GRADE,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
  ROUND(
    COUNT(DISTINCT e.EMP_ID) * 100.0
    / NULLIF(SUM(COUNT(DISTINCT e.EMP_ID)) OVER (PARTITION BY NVL(e.DEPARTMENT, '미지정')), 0),
    1
  ) AS PERCENTAGE
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(e.DEPARTMENT, '미지정'),
  NVL(f.APPR_GRADE, '미평가')
ORDER BY
  EMP_COUNT DESC,
  DEPARTMENT ASC,
  CASE NVL(f.APPR_GRADE, '미평가')
    WHEN 'S' THEN 1
    WHEN 'A' THEN 2
    WHEN 'B' THEN 3
    WHEN 'C' THEN 4
    WHEN 'D' THEN 5
    ELSE 6
  END ASC
```

---

## X11 [PASS] 일치
**최근 입사자 5명의 이름 부서 직급을 알려줘**

**Run #1**
```sql
SELECT EMP_NAME, DEPARTMENT, POSITION
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
ORDER BY HIRE_DATE DESC
FETCH FIRST 5 ROWS ONLY
```

**Run #2**
```sql
SELECT
  EMP_NAME,
  DEPARTMENT,
  POSITION
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
ORDER BY HIRE_DATE DESC
FETCH FIRST 5 ROWS ONLY
```

---

## X12 [PASS-INCONSISTENT] **불일치**
**50대 이상 재직자의 부서별 분포를 알려줘**

**Run #1**
```sql
SELECT
  NVL(DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 50
GROUP BY NVL(DEPARTMENT, '미지정')
ORDER BY employee_count DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT e.EMP_ID) AS employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) >= 50
GROUP BY
  NVL(e.DEPARTMENT, '미지정')
ORDER BY
  employee_count DESC
```

---

## X13 [PASS-INCONSISTENT] **불일치**
**부서별 자격증 보유율을 계산해줘**

**Run #1**
```sql
SELECT
  e.department,
  COUNT(DISTINCT e.emp_id) AS total_emp_count,
  COUNT(
    DISTINCT CASE
      WHEN EXISTS (
        SELECT 1
        FROM v_ai_license l
        WHERE l.emp_id = e.emp_id
      )
      THEN e.emp_id
    END
  ) AS licensed_emp_count,
  ROUND(
    COUNT(
      DISTINCT CASE
        WHEN EXISTS (
          SELECT 1
          FROM v_ai_license l
          WHERE l.emp_id = e.emp_id
        )
        THEN e.emp_id
      END
    ) / NULLIF(COUNT(DISTINCT e.emp_id), 0) * 100,
    2
  ) AS license_holding_rate_pct
FROM v_ai_employee e
WHERE e.work_status = '재직'
GROUP BY e.department
ORDER BY license_holding_rate_pct DESC, licensed_emp_count DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMPLOYEE_COUNT,
  COUNT(DISTINCT CASE WHEN l.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS LICENSED_EMPLOYEE_COUNT,
  ROUND(
    (COUNT(DISTINCT CASE WHEN l.EMP_ID IS NOT NULL THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100
  , 2) AS LICENSE_HOLDING_RATE
FROM v_ai_employee e
LEFT JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY LICENSE_HOLDING_RATE DESC, TOTAL_EMPLOYEE_COUNT DESC
```

---

## X14 [WARN-EMPTY] **불일치**
**연도별 부서별 승진자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS YEAR,
  NVL(e.DEPARTMENT, '(미지정)') AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS PROMOTION_CNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  NVL(e.DEPARTMENT, '(미지정)')
ORDER BY
  PROMOTION_CNT DESC,
  YEAR DESC,
  DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
  TO_CHAR(h.assignment_date, 'YYYY') AS year,
  e.department AS department,
  COUNT(DISTINCT h.emp_id) AS promotion_cnt
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.emp_id = h.emp_id
WHERE e.work_status = '재직'
  AND h.assignment_type_code LIKE '%승진%'
GROUP BY
  TO_CHAR(h.assignment_date, 'YYYY'),
  e.department
ORDER BY
  TO_NUMBER(TO_CHAR(h.assignment_date, 'YYYY')) DESC,
  promotion_cnt DESC
```

---

## X15 [WARN-EMPTY] **불일치**
**장애인 가족이 있는 재직자의 부서별 분포를 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.DISABILITY_STATUS = '장애있음'
  )
GROUP BY e.DEPARTMENT
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS DISABLED_FAMILY_EMP_COUNT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.DISABILITY_STATUS = '장애있음'
  )
GROUP BY e.DEPARTMENT
ORDER BY DISABLED_FAMILY_EMP_COUNT DESC
```

---

