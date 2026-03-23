# SQL 비교 로그 (실시간)

> 시작: 2026-03-23 11:03:27
> 반복횟수: 2회

## S01 [PASS-INCONSISTENT] **불일치**
**현재 재직 중인 전체 직원 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(*) AS active_employee_count
FROM v_ai_employee
WHERE work_status = '재직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS active_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```

---

## S02 [PASS] 일치
**퇴직한 직원은 총 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
```

**Run #2**
```sql
SELECT COUNT(*) AS retire_count
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
  AND GENDER IN ('남', '여')
GROUP BY GENDER
ORDER BY COUNT(DISTINCT EMP_ID) DESC, GENDER
```

---

## S04 [PASS] 일치
**2017년에 입사한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(hire_date, 'YYYY') = '2017'
```

**Run #2**
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2017'
```

---

## S05 [PASS] 일치
**부서별 직원 수를 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
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
    COUNT(DISTINCT e.EMP_ID) AS retiree_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY retiree_count DESC, e.GRADE DESC
```

**Run #2**
```sql
SELECT
    e.GRADE,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY emp_count DESC, e.GRADE
```

---

## S07 [PASS] 일치
**정규직 직원은 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS regular_employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '정규직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS regular_employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '정규직'
```

---

## S08 [PASS-INCONSISTENT] **불일치**
**계약직 직원 명단을 보여줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  e.HIRE_DATE,
  e.CAREER_MONTHS,
  e.CAREER_YEARS,
  e.GENDER,
  e.GRADE,
  e.EMP_TYPE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '기간제'
ORDER BY e.CAREER_MONTHS DESC, e.EMP_ID DESC
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
  e.HIRE_DATE,
  e.GENDER,
  e.GRADE,
  e.CAREER_YEARS,
  e.CAREER_MONTHS
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '기간제'
ORDER BY e.CAREER_MONTHS DESC, e.EMP_ID DESC
```

---

## S09 [PASS-INCONSISTENT] **불일치**
**2020년에 입사한 직원 이름과 부서를 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME AS EMP_NAME,
  e.DEPARTMENT AS DEPARTMENT
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = '2020'
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  EMP_NAME,
  DEPARTMENT
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2020'
ORDER BY CAREER_YEARS DESC, HIRE_DATE DESC
```

---

## S10 [PASS-INCONSISTENT] **불일치**
**경영지원부 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND DEPARTMENT = '경영지원부'
```

**Run #2**
```sql
SELECT COUNT(*) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND DEPARTMENT = '경영지원부'
```

---

## S11 [PASS-INCONSISTENT] **불일치**
**근속연수가 10년 이상인 직원 수는?**

**Run #1**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND NVL(CAREER_YEARS, 0) >= 10
ORDER BY employee_count DESC
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND CAREER_YEARS >= 10
ORDER BY employee_count DESC
```

---

## S12 [PASS-INCONSISTENT] **불일치**
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
    COUNT(DISTINCT e.EMP_ID) AS employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, e.BIRTH_DATE) / 12) BETWEEN 40 AND 49
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
    DUTY DESC
```

**Run #2**
```sql
SELECT
    NVL(DUTY, '미지정') AS DUTY,
    COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY NVL(DUTY, '미지정')
ORDER BY emp_count DESC, DUTY ASC
```

---

## S14 [PASS] 일치
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
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, 'YYYY') = '2018'
```

---

## S15 [PASS] 일치
**경력사원으로 입사한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.HIRE_TYPE LIKE '%경력%'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.HIRE_TYPE LIKE '%경력%'
```

---

## S16 [PASS-INCONSISTENT] **불일치**
**군필자 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS military_fulfilled_count
FROM v_ai_employee e
JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND m.SERVICE_STATUS = '군필'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS 군필자_수
FROM v_ai_employee e
JOIN v_ai_military m ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND m.SERVICE_STATUS = '군필'
```

---

## S17 [PASS-INCONSISTENT] **불일치**
**2017년 포상을 받은 직원 수는?**

**Run #1**
```sql
SELECT
  COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_YEAR = '2017'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
  AND r.REWARD_YEAR = '2017'
ORDER BY emp_count DESC
```

---

## S18 [PASS-INCONSISTENT] **불일치**
**2018년 기준 잔여연차가 0인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS CNT_EMPLOYEE
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = '2018'
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) = 0
```

**Run #2**
```sql
SELECT COUNT(DISTINCT d.EMP_ID) AS CNT_EMPLOYEE
FROM v_ai_dtm_yy_rest d
JOIN v_ai_employee e
  ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = '2018'
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) = 0
  AND e.WORK_STATUS = '재직'
```

---

## S19 [PASS-INCONSISTENT] **불일치**
**2017년 교육을 수료한 건수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS completed_education_count
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

## S20 [PASS-INCONSISTENT] **불일치**
**S등급을 받은 건수는 총 몇 건이야?**

**Run #1**
```sql
SELECT COUNT(*) AS s_grade_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE f.APPR_GRADE = 'S'
  AND e.WORK_STATUS = '재직'
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
  DEPARTMENT,
  AVG(NVL(CAREER_YEARS, 0)) AS AVG_CAREER_YEARS
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY AVG(NVL(CAREER_YEARS, 0)) DESC
```

**Run #2**
```sql
SELECT
  DEPARTMENT,
  AVG(CAREER_YEARS) AS AVG_CAREER_YEARS
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY AVG(CAREER_YEARS) DESC, DEPARTMENT DESC
```

---

## S22 [PASS] 일치
**연도별 입사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
       COUNT(DISTINCT EMP_ID) AS hire_count
FROM v_ai_employee
WHERE HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
ORDER BY year_val DESC
```

**Run #2**
```sql
SELECT TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
       COUNT(DISTINCT EMP_ID) AS hire_count
FROM v_ai_employee
WHERE HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
ORDER BY year_val DESC
```

---

## S23 [PASS-INCONSISTENT] **불일치**
**연도별 퇴사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(RETIRE_DATE, 'YYYY') AS retire_year,
  COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(RETIRE_DATE, 'YYYY')
ORDER BY TO_NUMBER(TO_CHAR(RETIRE_DATE, 'YYYY')) DESC
```

**Run #2**
```sql
SELECT
  TO_CHAR(retire_date, 'YYYY') AS retire_year,
  COUNT(DISTINCT emp_id) AS retire_count
FROM v_ai_employee
WHERE retire_date IS NOT NULL
GROUP BY TO_CHAR(retire_date, 'YYYY')
ORDER BY retire_year DESC
```

---

## S24 [PASS-INCONSISTENT] **불일치**
**직급별 남녀 비율을 보여줘**

**Run #1**
```sql
SELECT
  x.GRADE,
  x.GENDER,
  x.emp_count,
  ROUND(x.emp_count * 100.0 / NVL(SUM(x.emp_count) OVER (PARTITION BY x.GRADE), 0), 1) AS percentage
FROM (
  SELECT
    e.GRADE,
    e.GENDER,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.GRADE, e.GENDER
) x
ORDER BY x.emp_count DESC, x.GRADE, x.GENDER
```

**Run #2**
```sql
WITH agg AS (
  SELECT
      e.GRADE,
      e.GENDER,
      COUNT(DISTINCT e.EMP_ID) AS emp_count
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.GRADE, e.GENDER
)
SELECT
    a.GRADE,
    a.GENDER,
    a.emp_count,
    ROUND(
      a.emp_count * 100.0 / NULLIF(SUM(a.emp_count) OVER (PARTITION BY a.GRADE), 0),
      1
    ) AS gender_ratio_pct
FROM agg a
ORDER BY
  SUM(a.emp_count) OVER (PARTITION BY a.GRADE) DESC,
  a.emp_count DESC,
  a.GRADE,
  a.GENDER
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
ORDER BY CASE age_group
    WHEN '20대' THEN 1
    WHEN '30대' THEN 2
    WHEN '40대' THEN 3
    WHEN '50대' THEN 4
    WHEN '60대 이상' THEN 5
    ELSE 6
END
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
            WHEN NVL(CAREER_YEARS, 0) >= 1 AND NVL(CAREER_YEARS, 0) < 3 THEN '1~3년'
            WHEN NVL(CAREER_YEARS, 0) >= 3 AND NVL(CAREER_YEARS, 0) < 5 THEN '3~5년'
            WHEN NVL(CAREER_YEARS, 0) >= 5 AND NVL(CAREER_YEARS, 0) < 10 THEN '5~10년'
            WHEN NVL(CAREER_YEARS, 0) >= 10 THEN '10년 이상'
        END AS tenure_group,
        COUNT(DISTINCT EMP_ID) AS employee_count
    FROM v_ai_employee
    WHERE WORK_STATUS = '재직'
    GROUP BY
        CASE
            WHEN NVL(CAREER_YEARS, 0) < 1 THEN '1년 미만'
            WHEN NVL(CAREER_YEARS, 0) >= 1 AND NVL(CAREER_YEARS, 0) < 3 THEN '1~3년'
            WHEN NVL(CAREER_YEARS, 0) >= 3 AND NVL(CAREER_YEARS, 0) < 5 THEN '3~5년'
            WHEN NVL(CAREER_YEARS, 0) >= 5 AND NVL(CAREER_YEARS, 0) < 10 THEN '5~10년'
            WHEN NVL(CAREER_YEARS, 0) >= 10 THEN '10년 이상'
        END
)
ORDER BY CASE tenure_group
    WHEN '1년 미만' THEN 1
    WHEN '1~3년' THEN 2
    WHEN '3~5년' THEN 3
    WHEN '5~10년' THEN 4
    WHEN '10년 이상' THEN 5
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
      WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN '1~3년'
      WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN '3~5년'
      WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN '5~10년'
      ELSE '10년 이상'
    END AS tenure_group,
    CASE
      WHEN e.CAREER_YEARS < 1 THEN 1
      WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN 2
      WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN 3
      WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN 4
      ELSE 5
    END AS sort_key,
    COUNT(DISTINCT e.EMP_ID) AS employee_count
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
  GROUP BY
    CASE
      WHEN e.CAREER_YEARS < 1 THEN '1년 미만'
      WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN '1~3년'
      WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN '3~5년'
      WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN '5~10년'
      ELSE '10년 이상'
    END,
    CASE
      WHEN e.CAREER_YEARS < 1 THEN 1
      WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN 2
      WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN 3
      WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN 4
      ELSE 5
    END
)
ORDER BY sort_key DESC, employee_count DESC
```

---

## S27 [PASS] 일치
**10명 이상인 부서만 보여줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
HAVING COUNT(DISTINCT EMP_ID) >= 10
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT DEPARTMENT, COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
HAVING COUNT(DISTINCT EMP_ID) >= 10
ORDER BY emp_count DESC
```

---

## S28 [PASS-INCONSISTENT] **불일치**
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
SELECT
  HIRE_TYPE,
  COUNT(*) AS emp_count
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
  hire_date,
  hire_type
FROM (
  SELECT
    e.department,
    e.emp_id,
    e.emp_name,
    e.hire_date,
    e.hire_type,
    ROW_NUMBER() OVER (
      PARTITION BY e.department
      ORDER BY e.hire_date DESC, e.emp_id DESC
    ) AS rn
  FROM v_ai_employee e
  WHERE e.work_status = '재직'
) x
WHERE x.rn = 1
ORDER BY x.hire_date DESC, x.department DESC
```

**Run #2**
```sql
SELECT
  dept.department,
  dept.emp_id,
  dept.emp_name,
  dept.position,
  dept.hire_date,
  dept.hire_type
FROM (
  SELECT
    e.DEPARTMENT AS department,
    e.EMP_ID AS emp_id,
    e.EMP_NAME AS emp_name,
    e.POSITION AS position,
    e.HIRE_DATE AS hire_date,
    e.HIRE_TYPE AS hire_type,
    ROW_NUMBER() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY e.HIRE_DATE DESC, e.EMP_ID DESC
    ) AS rn
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
) dept
WHERE dept.rn = 1
ORDER BY dept.hire_date DESC, dept.emp_id DESC
```

---

## S30 [PASS-INCONSISTENT] **불일치**
**지급유형별 총 지급액을 보여줘**

**Run #1**
```sql
SELECT
  PAYMENT_TYPE_NAME,
  SUM(NVL(GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_pay_report
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_gross_pay_amount DESC
```

**Run #2**
```sql
SELECT
  p.PAYMENT_TYPE_NAME,
  SUM(p.GROSS_PAY_AMOUNT) AS TOTAL_GROSS_PAY_AMOUNT,
  SUM(p.FIXED_PAY_AMOUNT) AS TOTAL_FIXED_PAY_AMOUNT,
  SUM(p.VARIABLE_PAY_AMOUNT) AS TOTAL_VARIABLE_PAY_AMOUNT,
  SUM(p.NET_PAY_AMOUNT) AS TOTAL_NET_PAY_AMOUNT
FROM v_ai_pay_report p
GROUP BY
  p.PAYMENT_TYPE_NAME
ORDER BY
  TOTAL_GROSS_PAY_AMOUNT DESC
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
WHERE f.APPR_GRADE IS NOT NULL
  AND e.WORK_STATUS = '재직'
GROUP BY f.APPR_GRADE
ORDER BY emp_count DESC, f.APPR_GRADE
```

**Run #2**
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
ORDER BY emp_count DESC, f.APPR_GRADE
```

---

## S32 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수를 알려줘**

**Run #1**
```sql
SELECT
  NVL(t.TRAINING_TYPE, '미지정') AS training_type,
  COUNT(*) AS completed_count
FROM v_ai_training t
INNER JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.COMPLETION_STATUS = '수료'
GROUP BY
  NVL(t.TRAINING_TYPE, '미지정')
ORDER BY
  completed_count DESC
```

**Run #2**
```sql
SELECT
  t.training_type AS training_type,
  COUNT(*) AS completed_count
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.emp_id = t.emp_id
 AND t.completion_status = '수료'
WHERE e.work_status = '재직'
  AND t.training_type IS NOT NULL
GROUP BY t.training_type
ORDER BY COUNT(*) DESC, t.training_type ASC
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
INNER JOIN v_ai_employee e
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC
```

**Run #2**
```sql
SELECT
  h.ASSIGNMENT_TYPE_CODE,
  COUNT(*) AS total_count,
  COUNT(DISTINCT h.EMP_ID) AS emp_count
FROM v_ai_history h
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC, emp_count DESC
```

---

## S34 [PASS-INCONSISTENT] **불일치**
**2018년 기준 직원별 잔여연차 상위 10명을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  SUM(NVL(r.REMAINING_LEAVE_DAYS, 0)) AS REMAINING_LEAVE_DAYS
FROM V_AI_EMPLOYEE e
JOIN V_AI_DTM_YY_REST r
  ON e.EMP_ID = r.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND r.REFERENCE_YEAR = '2018'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT
ORDER BY
  SUM(NVL(r.REMAINING_LEAVE_DAYS, 0)) DESC
```

**Run #2**
```sql
SELECT
  emp_id,
  emp_name,
  remaining_leave_days_total
FROM (
  SELECT
    e.emp_id,
    e.emp_name,
    SUM(NVL(r.remaining_leave_days, 0)) AS remaining_leave_days_total,
    ROW_NUMBER() OVER (
      ORDER BY SUM(NVL(r.remaining_leave_days, 0)) DESC, e.emp_id
    ) AS rn
  FROM v_ai_dtm_yy_rest r
  JOIN v_ai_employee e
    ON e.emp_id = r.emp_id
  WHERE e.work_status = '재직'
    AND r.reference_year = '2018'
  GROUP BY e.emp_id, e.emp_name
)
WHERE rn <= 10
ORDER BY remaining_leave_days_total DESC, emp_id
```

---

## S35 [PASS-INCONSISTENT] **불일치**
**연도별 포상 건수 추이를 보여줘**

**Run #1**
```sql
SELECT
  r.REWARD_YEAR,
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
  COUNT(*) AS reward_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
GROUP BY r.REWARD_YEAR
ORDER BY r.REWARD_YEAR DESC
```

---

## M01 [PASS] 일치
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
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND a.REGION = '서울'
ORDER BY emp_count DESC
```

---

## M02 [PASS] 일치
**지역별 재직자 분포를 알려줘**

**Run #1**
```sql
SELECT NVL(a.REGION, '미등록') AS region, COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(a.REGION, '미등록')
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT NVL(a.REGION, '미등록') AS region, COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(a.REGION, '미등록')
ORDER BY emp_count DESC
```

---

## M03 [PASS-INCONSISTENT] **불일치**
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
ORDER BY emp_count DESC
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

## M04 [PASS-INCONSISTENT] **불일치**
**전직장 경력이 3건 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  COUNT(*) AS prev_career_count
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
ORDER BY prev_career_count DESC
FETCH FIRST 20 ROWS ONLY
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  COUNT(*) AS CAREER_COUNT
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
ORDER BY CAREER_COUNT DESC, e.EMP_ID ASC
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
SELECT e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.POSITION,
       e.DEPARTMENT,
       s.MAJOR_NAME,
       s.SCHOOL_NAME,
       s.GRADUATION_STATUS,
       s.GRADUATION_DATE
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%컴퓨터공학%'
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.DEPARTMENT,
  s.SCHOOL_NAME,
  s.MAJOR_NAME,
  s.DOUBLE_MAJOR_NAME,
  s.GRADUATION_STATUS,
  s.GRADUATION_DATE
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY e.EMP_ID DESC
```

---

## M07 [PASS-INCONSISTENT] **불일치**
**배우자가 있는 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN ('배우자', '남편', '처')
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN ('배우자', '처', '남편')
  )
```

---

## M08 [WARN-EMPTY] **불일치**
**자녀가 2명 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
 AND f.RELATION = '자녀'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.EMP_NAME_ENG, e.COMPANY_CODE, e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
 AND f.RELATION = '자녀'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC
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
      AND l.LANGUAGE_TYPE = '영어'
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
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
SELECT COUNT(DISTINCT e.EMP_ID) AS license_holder_active_employee_count
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
SELECT COUNT(DISTINCT e.EMP_ID) AS holding_license_employee_count
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
SELECT e.EMP_ID,
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
GROUP BY e.EMP_ID, e.EMP_NAME, e.EMP_NAME_ENG, e.COMPANY_CODE, e.POSITION, e.DEPARTMENT
HAVING COUNT(l.EMP_ID) >= 3
ORDER BY license_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       COUNT(*) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.EMP_NAME_ENG, e.COMPANY_CODE, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY license_count DESC, e.EMP_ID DESC
```

---

## M13 [PASS-INCONSISTENT] **불일치**
**포상을 받은 재직자 부서별 수는?**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS reward_emp_count
FROM v_ai_employee e
INNER JOIN v_ai_reward r
  ON r.EMP_ID = e.EMP_ID
 AND r.REWARD_TYPE = '포상'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY reward_emp_count DESC, e.DEPARTMENT ASC
```

**Run #2**
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
ORDER BY emp_count DESC
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
  e.DUTY,
  e.DUTY_DATE,
  e.EMP_TYPE,
  e.GENDER,
  e.GRADE,
  e.GRADE_DATE,
  e.HIRE_DATE,
  e.RETIRE_DATE,
  r.REWARD_KIND,
  r.REWARD_REASON,
  r.REWARD_DATE,
  r.REWARD_AMOUNT,
  r.REWARD_NO
FROM v_ai_employee e
INNER JOIN v_ai_reward r
  ON r.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND r.REWARD_TYPE = '징계'
ORDER BY r.REWARD_AMOUNT DESC, r.REWARD_DATE DESC, e.EMP_ID DESC
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
  e.DUTY_DATE,
  e.GENDER,
  e.GRADE,
  e.GRADE_DATE,
  e.HIRE_DATE,
  e.RETIRE_DATE,
  e.RETIRE_REASON,
  r.REWARD_DATE,
  r.REWARD_KIND,
  r.REWARD_REASON,
  r.REWARD_CONTENT,
  r.REWARD_AMOUNT,
  r.REWARD_NO
FROM v_ai_employee e
INNER JOIN v_ai_reward r
  ON r.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND r.REWARD_TYPE = '징계'
ORDER BY
  r.REWARD_AMOUNT DESC NULLS LAST,
  r.REWARD_DATE DESC NULLS LAST,
  e.EMP_ID DESC NULLS LAST
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
WITH ranked_feedback AS (
  SELECT
    f.*,
    ROW_NUMBER() OVER (
      PARTITION BY f.EMP_ID
      ORDER BY f.APPR_YMD DESC, f.END_YMD DESC, f.APPR_ID DESC
    ) AS rn
  FROM v_ai_feedback f
)
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  r.APPR_NM,
  r.APPR_YMD AS RECENT_APPR_YMD,
  r.APPR_GRADE,
  NVL(r.APPR_SCORE, 0) AS APPR_SCORE
FROM ranked_feedback r
JOIN v_ai_employee e
  ON e.EMP_ID = r.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND r.rn = 1
  AND r.APPR_GRADE = 'S'
ORDER BY NVL(e.CAREER_YEARS, 0) DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.emp_id,
  e.emp_name,
  e.department,
  e.duty,
  f.appr_ymd AS latest_appr_ymd,
  f.appr_nm AS latest_appr_nm,
  f.appr_score AS latest_appr_score
FROM v_ai_employee e
JOIN (
  SELECT
    fb.emp_id,
    fb.appr_ymd,
    fb.appr_nm,
    fb.appr_score,
    fb.appr_grade,
    ROW_NUMBER() OVER (
      PARTITION BY fb.emp_id
      ORDER BY fb.appr_ymd DESC, fb.appr_id DESC
    ) AS rn
  FROM v_ai_feedback fb
) f
  ON e.emp_id = f.emp_id
  AND f.rn = 1
WHERE e.work_status = '재직'
  AND f.appr_grade = 'S'
ORDER BY NVL(e.career_years, 0) DESC, e.emp_id DESC
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
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC NULLS LAST
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
  AND NVL(f.APPR_SCORE, 0) > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC
```

---

## M19 [PASS-INCONSISTENT] **불일치**
**최근 10년간 승진한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS promoted_employee_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS promoted_emp_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
```

---

## M20 [PASS-INCONSISTENT] **불일치**
**현재 휴직 중인 직원 목록을 보여줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.DUTY,
  h.ASSIGNMENT_TYPE_CODE,
  h.ASSIGNMENT_REASON_CODE,
  h.ASSIGNMENT_START_DATE,
  h.ASSIGNMENT_END_DATE,
  h.EXPECTED_RETURN_FROM_LEAVE_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.LEAVE_OF_ABSENCE_YN = 'Y'
  AND h.ASSIGNMENT_START_DATE = (
    SELECT MAX(h2.ASSIGNMENT_START_DATE)
    FROM v_ai_history h2
    WHERE h2.EMP_ID = h.EMP_ID
      AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
  )
  AND h.ASSIGNMENT_START_DATE <= SYSDATE
  AND h.ASSIGNMENT_END_DATE >= SYSDATE
ORDER BY h.ASSIGNMENT_START_DATE DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.DUTY,
  e.DUTY_DATE,
  h.ASSIGNMENT_TYPE_CODE,
  h.ASSIGNMENT_REASON_CODE,
  h.ASSIGNMENT_START_DATE,
  h.ASSIGNMENT_END_DATE,
  h.ASSIGNMENT_TITLE_NAME
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.LEAVE_OF_ABSENCE_YN = 'Y'
 AND h.ASSIGNMENT_END_DATE >= SYSDATE
 AND h.ASSIGNMENT_START_DATE = (
   SELECT MAX(h2.ASSIGNMENT_START_DATE)
   FROM v_ai_history h2
   WHERE h2.EMP_ID = e.EMP_ID
     AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
     AND h2.ASSIGNMENT_END_DATE >= SYSDATE
 )
WHERE e.WORK_STATUS = '재직'
ORDER BY h.ASSIGNMENT_START_DATE DESC, e.EMP_ID DESC
```

---

## M21 [PASS-INCONSISTENT] **불일치**
**부서별 월평균 실수령액을 보여줘**

**Run #1**
```sql
WITH dept_month AS (
  SELECT
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH,
    SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS monthly_net_pay_amount
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
   AND p.PAYMENT_TYPE_NAME = '정기급여'
  WHERE e.WORK_STATUS = '재직'
  GROUP BY
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH
)
SELECT
  dm.DEPARTMENT,
  COUNT(DISTINCT dm.PAY_YEAR_MONTH) AS month_count,
  ROUND(AVG(dm.monthly_net_pay_amount)) AS avg_monthly_net_pay_amount
FROM dept_month dm
GROUP BY
  dm.DEPARTMENT
ORDER BY
  avg_monthly_net_pay_amount DESC
```

**Run #2**
```sql
SELECT
  dm.DEPARTMENT,
  COUNT(DISTINCT dm.PAY_YEAR_MONTH) AS MONTH_COUNT,
  COUNT(DISTINCT dm.EMP_ID) AS EMP_COUNT,
  ROUND(AVG(dm.MONTH_NET_PAY_AMOUNT)) AS AVG_MONTH_NET_PAY_AMOUNT
FROM (
  SELECT
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH,
    e.EMP_ID,
    SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS MONTH_NET_PAY_AMOUNT
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
   AND p.PAYMENT_TYPE_NAME = '정기급여'
  WHERE e.WORK_STATUS = '재직'
  GROUP BY
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH,
    e.EMP_ID
) dm
GROUP BY
  dm.DEPARTMENT
ORDER BY
  AVG_MONTH_NET_PAY_AMOUNT DESC
```

---

## M22 [PASS-INCONSISTENT] **불일치**
**직급별 평균 총지급액을 알려줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미정') AS JOB_GRADE_NAME,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
  AVG(NVL(p.GROSS_PAY_AMOUNT, 0)) AS AVG_GROSS_PAY_AMOUNT,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS TOTAL_GROSS_PAY_AMOUNT
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, '미정')
ORDER BY TOTAL_GROSS_PAY_AMOUNT DESC
```

**Run #2**
```sql
SELECT NVL(p.JOB_GRADE_NAME, '미지정') AS JOB_GRADE_NAME,
       AVG(NVL(p.GROSS_PAY_AMOUNT, 0)) AS AVG_GROSS_PAY_AMOUNT
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
        ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, '미지정')
ORDER BY AVG(NVL(p.GROSS_PAY_AMOUNT, 0)) DESC
```

---

## M23 [PASS-INCONSISTENT] **불일치**
**부서별 평균 연차 사용률을 알려줘**

**Run #1**
```sql
SELECT
    e.DEPARTMENT,
    COUNT(DISTINCT e.EMP_ID) AS emp_count,
    ROUND(AVG(NVL(d.TOTAL_LEAVE_DAYS, 0)), 1) AS avg_total_leave_days,
    ROUND(AVG(NVL(d.USED_LEAVE_DAYS_PAST, 0)), 1) AS avg_used_leave_days,
    ROUND(AVG(
        CASE
            WHEN NVL(d.TOTAL_LEAVE_DAYS, 0) > 0
            THEN NVL(d.USED_LEAVE_DAYS_PAST, 0) * 100.0 / d.TOTAL_LEAVE_DAYS
            ELSE 0
        END
    ), 1) AS avg_leave_usage_rate
FROM v_ai_employee e
LEFT JOIN v_ai_dtm_yy_rest d
    ON e.EMP_ID = d.EMP_ID
    AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_leave_usage_rate DESC, e.DEPARTMENT
```

**Run #2**
```sql
WITH d AS (
  SELECT
    EMP_ID,
    SUM(NVL(TOTAL_LEAVE_DAYS, 0)) AS total_days,
    SUM(NVL(USED_LEAVE_DAYS_PAST, 0)) AS used_days
  FROM v_ai_dtm_yy_rest
  GROUP BY EMP_ID
)
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    AVG(
      CASE
        WHEN NVL(d.total_days, 0) > 0
        THEN NVL(d.used_days, 0) * 100.0 / d.total_days
        ELSE 0
      END
    ),
    1
  ) AS avg_usage_rate
FROM v_ai_employee e
LEFT JOIN d ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_usage_rate DESC
```

---

## M24 [WARN-EMPTY] **불일치**
**잔여연차가 10일 이상인 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  d.REFERENCE_YEAR,
  d.TOTAL_LEAVE_DAYS,
  d.USED_LEAVE_DAYS_PAST,
  d.REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY
  NVL(d.REMAINING_LEAVE_DAYS, 0) DESC,
  d.REFERENCE_YEAR DESC,
  e.EMP_ID ASC
```

**Run #2**
```sql
SELECT e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       d.REFERENCE_YEAR,
       d.REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY NVL(d.REMAINING_LEAVE_DAYS, 0) DESC, e.EMP_ID DESC
```

---

## M25 [PASS-INCONSISTENT] **불일치**
**병역유형별 재직자 수를 보여줘**

**Run #1**
```sql
SELECT NVL(m.MILITARY_TYPE, '미상') AS MILITARY_TYPE,
       COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미상')
ORDER BY EMP_COUNT DESC, MILITARY_TYPE
```

**Run #2**
```sql
SELECT NVL(m.MILITARY_TYPE, '미상') AS military_type,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미상')
ORDER BY emp_count DESC
```

---

## M26 [PASS-INCONSISTENT] **불일치**
**상여금 지급 총액 부서별 비교를 해줘**

**Run #1**
```sql
SELECT
  pr.ORGANIZATION_NAME,
  SUM(NVL(pr.GROSS_PAY_AMOUNT, 0)) AS total_award_gross_amount,
  SUM(NVL(pr.NET_PAY_AMOUNT, 0)) AS total_award_net_amount,
  COUNT(DISTINCT pr.EMP_ID) AS emp_count
FROM v_ai_pay_report pr
INNER JOIN v_ai_employee e
  ON pr.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND pr.PAYMENT_TYPE_NAME LIKE '%상여%'
GROUP BY pr.ORGANIZATION_NAME
ORDER BY total_award_gross_amount DESC
```

**Run #2**
```sql
SELECT NVL(pr.ORGANIZATION_NAME, '미등록') AS department_name,
       SUM(NVL(pr.GROSS_PAY_AMOUNT, 0)) AS bonus_total_gross_amount
FROM v_ai_pay_report pr
JOIN v_ai_employee e
  ON e.EMP_ID = pr.EMP_ID
 AND e.WORK_STATUS = '재직'
WHERE pr.PAYMENT_TYPE_NAME LIKE '%상여%'
GROUP BY NVL(pr.ORGANIZATION_NAME, '미등록')
ORDER BY bonus_total_gross_amount DESC
```

---

## M27 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT
  NVL(e.department, '미등록') AS department,
  NVL(t.training_type, '미등록') AS training_type,
  COUNT(t.EMP_ID) AS completed_count,
  COUNT(DISTINCT e.EMP_ID) AS completed_emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(e.department, '미등록'),
  NVL(t.training_type, '미등록')
ORDER BY
  completed_count DESC,
  completed_emp_count DESC,
  department ASC,
  training_type ASC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  NVL(t.TRAINING_TYPE, '미지정') AS TRAINING_TYPE,
  COUNT(t.EMP_ID) AS COMPLETED_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
  AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(e.DEPARTMENT, '미지정'),
  NVL(t.TRAINING_TYPE, '미지정')
HAVING COUNT(t.EMP_ID) > 0
ORDER BY COMPLETED_COUNT DESC, DEPARTMENT, TRAINING_TYPE
```

---

## M28 [PASS] 일치
**평가등급이 C 또는 D인 재직자 명단과 부서를 알려줘**

**Run #1**
```sql
SELECT DISTINCT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_feedback f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.APPR_GRADE IN ('C', 'D')
  )
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT DISTINCT
       e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
      SELECT 1
      FROM v_ai_feedback f
      WHERE f.EMP_ID = e.EMP_ID
        AND f.APPR_GRADE IN ('C', 'D')
  )
ORDER BY e.EMP_ID DESC
```

---

## M29 [PASS-INCONSISTENT] **불일치**
**부서별 인사이동 건수를 보여줘**

**Run #1**
```sql
SELECT
  h.ASSIGNMENT_DEPARTMENT_ID AS department_id,
  COUNT(*) AS move_count
FROM v_ai_history h
JOIN v_ai_employee e
  ON h.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%이동%'
GROUP BY h.ASSIGNMENT_DEPARTMENT_ID
ORDER BY move_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(h.ASSIGNMENT_HISTORY_ID) AS move_count
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE LIKE '%이동%'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY move_count DESC
```

---

## M30 [PASS] 일치
**부서별 학력 분포를 알려줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미등록') AS EDUCATION_LEVEL,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미등록')
ORDER BY
  EMP_COUNT DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미등록') AS EDUCATION_LEVEL,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미등록')
ORDER BY
  EMP_COUNT DESC
```

---

## H01 [PASS-INCONSISTENT] **불일치**
**서울 거주 토익 800점 이상 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  e.GRADE,
  e.HIRE_DATE,
  e.CAREER_YEARS,
  e.DUTY
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
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.COMPANY_CODE,
  lm.MAX_SCORE AS TOEIC_MAX_SCORE
FROM v_ai_employee e
JOIN v_ai_address a
  ON a.EMP_ID = e.EMP_ID
 AND a.REGION = '서울'
JOIN (
  SELECT
    EMP_ID,
    MAX(SCORE) AS MAX_SCORE
  FROM v_ai_language
  WHERE EXAM_TYPE = 'TOEIC'
    AND SCORE >= 800
  GROUP BY EMP_ID
) lm
  ON lm.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY lm.MAX_SCORE DESC, e.EMP_ID DESC
```

---

## H02 [PASS] 일치
**석사 이상 학력이면서 자격증 보유한 재직자 수는?**

**Run #1**
```sql
SELECT
  COUNT(DISTINCT e.EMP_ID) AS emp_count
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

## H03 [PASS-INCONSISTENT] **불일치**
**평가등급별 평균 급여를 보여줘**

**Run #1**
```sql
SELECT
  NVL(PAY_GRADE_NAME, '미분류') AS 평가등급,
  COUNT(DISTINCT EMP_ID) AS 인원수,
  ROUND(AVG(NET_PAY_AMOUNT), 2) AS 평균급여
FROM v_ai_pay_report
GROUP BY
  NVL(PAY_GRADE_NAME, '미분류')
ORDER BY
  평균급여 DESC
```

**Run #2**
```sql
SELECT NVL(p.PAY_GRADE_NAME, '미정') AS 평가등급,
       COUNT(DISTINCT p.EMP_ID) AS 인원수,
       ROUND(AVG(p.NET_PAY_AMOUNT), 0) AS 평균급여
FROM v_ai_pay_report p
GROUP BY NVL(p.PAY_GRADE_NAME, '미정')
ORDER BY 평균급여 DESC, 인원수 DESC
```

---

## H04 [PASS-INCONSISTENT] **불일치**
**동일 직급 내 남녀 평균 급여 차이를 보여줘**

**Run #1**
```sql
SELECT
  e.grade AS grade,
  AVG(CASE WHEN e.gender = '남' THEN p.net_pay_amount END) AS avg_net_pay_male,
  AVG(CASE WHEN e.gender = '여' THEN p.net_pay_amount END) AS avg_net_pay_female,
  (AVG(CASE WHEN e.gender = '남' THEN p.net_pay_amount END) - AVG(CASE WHEN e.gender = '여' THEN p.net_pay_amount END)) AS avg_net_pay_diff
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON p.emp_id = e.emp_id
WHERE e.work_status = '재직'
GROUP BY e.grade
HAVING
  COUNT(DISTINCT CASE WHEN e.gender = '남' THEN e.emp_id END) > 0
  AND COUNT(DISTINCT CASE WHEN e.gender = '여' THEN e.emp_id END) > 0
ORDER BY ABS(
  (AVG(CASE WHEN e.gender = '남' THEN p.net_pay_amount END) - AVG(CASE WHEN e.gender = '여' THEN p.net_pay_amount END))
) DESC
```

**Run #2**
```sql
SELECT
  e.GRADE AS 직급,
  AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END) AS 남자_평균급여,
  AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END) AS 여자_평균급여,
  NVL(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END), 0)
  - NVL(AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END), 0) AS 남녀_평균급여_차이
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON p.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY ABS(
  NVL(AVG(CASE WHEN e.GENDER = '남' THEN p.GROSS_PAY_AMOUNT END), 0)
  - NVL(AVG(CASE WHEN e.GENDER = '여' THEN p.GROSS_PAY_AMOUNT END), 0)
) DESC
```

---

## H05 [PASS] 일치
**교육 미이수 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.COMPANY_CODE,
  e.EMP_ID
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
SELECT e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       e.COMPANY_CODE,
       e.EMP_ID
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

---

## H06 [PASS-INCONSISTENT] **불일치**
**근속 10년 이상인데 승진 이력이 없는 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.CAREER_YEARS,
  e.EMP_ID
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 10
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
FETCH FIRST 20 ROWS ONLY
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  e.DUTY,
  e.CAREER_YEARS,
  e.CAREER_MONTHS,
  e.HIRE_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 10
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC
FETCH FIRST 20 ROWS ONLY
```

---

## H07 [PASS-INCONSISTENT] **불일치**
**부서별 평균 교육비용과 평균 평가점수를 비교해줘**

**Run #1**
```sql
SELECT
  d.dept AS department,
  ROUND(tr.avg_training_cost) AS avg_training_cost,
  ROUND(fb.avg_feedback_score, 1) AS avg_feedback_score
FROM (
  SELECT e.DEPARTMENT AS dept
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
) d
LEFT JOIN (
  SELECT
    e.DEPARTMENT AS dept,
    AVG(t.TRAINING_COST) AS avg_training_cost
  FROM v_ai_employee e
  LEFT JOIN v_ai_training t
    ON t.EMP_ID = e.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
) tr
  ON tr.dept = d.dept
LEFT JOIN (
  SELECT
    e.DEPARTMENT AS dept,
    AVG(f.APPR_SCORE) AS avg_feedback_score
  FROM v_ai_employee e
  LEFT JOIN v_ai_feedback f
    ON f.EMP_ID = e.EMP_ID
    AND f.APPR_SCORE > 0
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
) fb
  ON fb.dept = d.dept
ORDER BY
  tr.avg_training_cost DESC NULLS LAST,
  fb.avg_feedback_score DESC NULLS LAST
```

**Run #2**
```sql
WITH training_agg AS (
  SELECT
    e.DEPARTMENT,
    AVG(t.TRAINING_COST) AS avg_training_cost
  FROM v_ai_employee e
  LEFT JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
),
feedback_agg AS (
  SELECT
    e.DEPARTMENT,
    AVG(f.APPR_SCORE) AS avg_feedback_score
  FROM v_ai_employee e
  LEFT JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
   AND f.APPR_SCORE > 0
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
)
SELECT
  COALESCE(t.DEPARTMENT, f.DEPARTMENT) AS DEPARTMENT,
  t.avg_training_cost,
  f.avg_feedback_score
FROM training_agg t
FULL OUTER JOIN feedback_agg f
  ON t.DEPARTMENT = f.DEPARTMENT
ORDER BY GREATEST(NVL(t.avg_training_cost, 0), NVL(f.avg_feedback_score, 0)) DESC
```

---

## H08 [PASS-INCONSISTENT] **불일치**
**직급별 평균 실수령액과 최대 최소 급여를 알려줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, e.GRADE) AS 직급,
  COUNT(DISTINCT e.EMP_ID) AS 인원수,
  ROUND(AVG(p.NET_PAY_AMOUNT)) AS 평균_실수령액,
  MAX(p.NET_PAY_AMOUNT) AS 최대_실수령액,
  MIN(p.NET_PAY_AMOUNT) AS 최소_실수령액
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY 평균_실수령액 DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS 직급,
  AVG(p.NET_PAY_AMOUNT) AS 평균_실수령액,
  MIN(p.NET_PAY_AMOUNT) AS 최소_실수령액,
  MAX(p.NET_PAY_AMOUNT) AS 최대_실수령액
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
 AND e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME)
ORDER BY 최대_실수령액 DESC
```

---

## H09 [PASS-INCONSISTENT] **불일치**
**부서별 퇴직률을 계산해줘**

**Run #1**
```sql
WITH dept_total AS (
  SELECT NVL(department, '미지정') AS department,
         COUNT(DISTINCT emp_id) AS total_cnt
  FROM v_ai_employee
  GROUP BY NVL(department, '미지정')
),
dept_retire AS (
  SELECT NVL(department, '미지정') AS department,
         COUNT(DISTINCT emp_id) AS retire_cnt
  FROM v_ai_employee
  WHERE retire_date IS NOT NULL
  GROUP BY NVL(department, '미지정')
)
SELECT t.department,
       NVL(r.retire_cnt, 0) AS retire_cnt,
       t.total_cnt,
       ROUND(NVL(r.retire_cnt, 0) / NULLIF(t.total_cnt, 0) * 100, 2) AS retire_rate_pct
FROM dept_total t
LEFT JOIN dept_retire r
  ON t.department = r.department
ORDER BY retire_rate_pct DESC, t.total_cnt DESC
```

**Run #2**
```sql
SELECT
  e.department AS department,
  COUNT(DISTINCT CASE WHEN e.retire_date IS NOT NULL THEN e.emp_id END) AS retired_count,
  COUNT(DISTINCT e.emp_id) AS total_count,
  ROUND(
    (COUNT(DISTINCT CASE WHEN e.retire_date IS NOT NULL THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0)) * 100,
    2
  ) AS retire_rate_percent
FROM v_ai_employee e
GROUP BY e.department
ORDER BY retire_rate_percent DESC NULLS LAST, retired_count DESC
```

---

## H10 [PASS-INCONSISTENT] **불일치**
**고정비 대비 변동비 비율을 부서별로 분석해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS TOTAL_FIXED_PAY_AMOUNT,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS TOTAL_VARIABLE_PAY_AMOUNT,
  CASE
    WHEN SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) = 0 THEN NULL
    ELSE ROUND(SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) / SUM(NVL(p.FIXED_PAY_AMOUNT, 0)), 6)
  END AS VARIABLE_TO_FIXED_RATIO
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY VARIABLE_TO_FIXED_RATIO DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  p.ORGANIZATION_NAME AS department_name,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS total_variable_pay_amount,
  SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS total_fixed_pay_amount,
  CASE
    WHEN SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) = 0 THEN NULL
    ELSE SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) / SUM(NVL(p.FIXED_PAY_AMOUNT, 0))
  END AS variable_to_fixed_ratio
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY p.ORGANIZATION_NAME
ORDER BY
  CASE
    WHEN SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) = 0 THEN NULL
    ELSE SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) / SUM(NVL(p.FIXED_PAY_AMOUNT, 0))
  END DESC
```

---

## H11 [PASS-INCONSISTENT] **불일치**
**포상을 받은 직원의 평균 평가점수는?**

**Run #1**
```sql
SELECT AVG(emp_avg_score) AS avg_appr_score
FROM (
  SELECT e.EMP_ID,
         AVG(f.APPR_SCORE) AS emp_avg_score
  FROM v_ai_employee e
  INNER JOIN v_ai_feedback f
    ON f.EMP_ID = e.EMP_ID
   AND NVL(f.APPR_SCORE, 0) > 0
  WHERE e.WORK_STATUS = '재직'
    AND EXISTS (
      SELECT 1
      FROM v_ai_reward r
      WHERE r.EMP_ID = e.EMP_ID
        AND r.REWARD_TYPE = '포상'
    )
  GROUP BY e.EMP_ID
) x
```

**Run #2**
```sql
SELECT
  AVG(f.appr_score) AS avg_appr_score
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON f.emp_id = e.emp_id
WHERE e.work_status = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.emp_id = e.emp_id
      AND r.reward_type = '포상'
  )
  AND NVL(f.appr_score, 0) > 0
```

---

## H12 [PASS-INCONSISTENT] **불일치**
**부서별 승진자 수와 승진률을 보여줘**

**Run #1**
```sql
WITH total AS (
  SELECT
    NVL(e.department, '미지정') AS department,
    COUNT(DISTINCT e.emp_id) AS total_emp_cnt
  FROM v_ai_employee e
  WHERE e.work_status = '재직'
  GROUP BY NVL(e.department, '미지정')
),
promo AS (
  SELECT
    NVL(e.department, '미지정') AS department,
    COUNT(DISTINCT h.emp_id) AS promoted_emp_cnt
  FROM v_ai_history h
  JOIN v_ai_employee e
    ON e.emp_id = h.emp_id
  WHERE e.work_status = '재직'
    AND h.assignment_type_code LIKE '%승진%'
  GROUP BY NVL(e.department, '미지정')
)
SELECT
  t.department,
  NVL(p.promoted_emp_cnt, 0) AS promoted_emp_cnt,
  t.total_emp_cnt,
  ROUND(NVL(p.promoted_emp_cnt, 0) / NULLIF(t.total_emp_cnt, 0) * 100, 2) AS promotion_rate_pct
FROM total t
LEFT JOIN promo p
  ON p.department = t.department
ORDER BY NVL(p.promoted_emp_cnt, 0) DESC, t.total_emp_cnt DESC, t.department
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMP_CNT,
  COUNT(DISTINCT h.EMP_ID) AS PROMOTED_EMP_CNT,
  ROUND(
    (COUNT(DISTINCT h.EMP_ID) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100,
    2
  ) AS PROMOTION_RATE_PCT
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY PROMOTED_EMP_CNT DESC, DEPARTMENT ASC
```

---

## H13 [PASS-INCONSISTENT] **불일치**
**부서별 1인당 교육비용을 보여줘**

**Run #1**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)), 0) AS total_training_cost,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 0) AS avg_training_cost_per_person
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
       ROUND(SUM(NVL(t.TRAINING_COST, 0)), 0) AS total_cost,
       ROUND(
         SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
         0
       ) AS avg_cost_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY total_cost DESC
```

---

## H14 [PASS-INCONSISTENT] **불일치**
**직급별 평균 연차 사용률을 보여줘**

**Run #1**
```sql
WITH emp_leave AS (
  SELECT
    d.EMP_ID,
    SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) AS TOTAL_LEAVE_DAYS,
    SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) AS USED_LEAVE_DAYS_PAST
  FROM v_ai_dtm_yy_rest d
  GROUP BY d.EMP_ID
)
SELECT
  e.GRADE,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
  ROUND(AVG(
    CASE
      WHEN NVL(l.TOTAL_LEAVE_DAYS, 0) > 0
      THEN NVL(l.USED_LEAVE_DAYS_PAST, 0) * 100.0 / l.TOTAL_LEAVE_DAYS
      ELSE 0
    END
  ), 1) AS AVG_LEAVE_USAGE_RATE
FROM v_ai_employee e
LEFT JOIN emp_leave l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY AVG_LEAVE_USAGE_RATE DESC
```

**Run #2**
```sql
SELECT
    e.GRADE,
    COUNT(DISTINCT e.EMP_ID) AS emp_count,
    ROUND(
        CASE
            WHEN SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) > 0
            THEN SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) * 100.0 / SUM(NVL(d.TOTAL_LEAVE_DAYS, 0))
            ELSE 0
        END
    , 1) AS avg_leave_usage_rate
FROM v_ai_employee e
LEFT JOIN v_ai_dtm_yy_rest d
    ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY avg_leave_usage_rate DESC, e.GRADE ASC
```

---

## H15 [PASS-INCONSISTENT] **불일치**
**부서별 평가점수 표준편차를 계산해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT AS department,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  STDDEV_POP(f.APPR_SCORE) AS score_stddev
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
  AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT
ORDER BY
  score_stddev DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT f.EMP_ID) AS emp_count,
  ROUND(STDDEV_SAMP(f.APPR_SCORE), 2) AS stddev_score
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY stddev_score DESC NULLS LAST
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
  AND p.PAY_YEAR BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
GROUP BY p.PAY_YEAR
ORDER BY TO_NUMBER(p.PAY_YEAR) DESC
```

**Run #2**
```sql
SELECT
  p.PAY_YEAR,
  SUM(p.GROSS_PAY_AMOUNT) AS total_gross_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND TO_NUMBER(p.PAY_YEAR) BETWEEN TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY')) AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
GROUP BY
  p.PAY_YEAR
ORDER BY
  SUM(p.GROSS_PAY_AMOUNT) DESC
```

---

## H17 [PASS-INCONSISTENT] **불일치**
**정규직과 기간제 비율 및 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT
    NVL(e.DEPARTMENT, '미분류') AS DEPARTMENT,
    COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '정규직' THEN e.EMP_ID END) AS REGULAR_CNT,
    COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '기간제' THEN e.EMP_ID END) AS CONTRACT_CNT,
    COUNT(DISTINCT e.EMP_ID) AS TOTAL_CNT,
    ROUND(
        (COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '정규직' THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100
    , 2) AS REGULAR_RATIO_PCT,
    ROUND(
        (COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '기간제' THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100
    , 2) AS CONTRACT_RATIO_PCT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미분류')
ORDER BY TOTAL_CNT DESC, DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
    NVL(e.DEPARTMENT, '미지정') AS department,
    COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '정규직' THEN e.EMP_ID END) AS regular_count,
    COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '기간제' THEN e.EMP_ID END) AS contract_count,
    COUNT(DISTINCT e.EMP_ID) AS total_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '정규직' THEN e.EMP_ID END)
        / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
        4
    ) AS regular_ratio,
    ROUND(
        COUNT(DISTINCT CASE WHEN e.EMP_TYPE = '기간제' THEN e.EMP_ID END)
        / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
        4
    ) AS contract_ratio
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE IN ('정규직', '기간제')
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY total_count DESC, department ASC
```

---

## H18 [PASS-INCONSISTENT] **불일치**
**휴직 유형별 현황을 알려줘**

**Run #1**
```sql
SELECT
    NVL(h.assignment_reason_code, '기타') AS 휴직유형,
    COUNT(DISTINCT e.emp_id) AS 인원수
FROM v_ai_employee e
JOIN (
    SELECT
        h1.emp_id,
        h1.assignment_reason_code
    FROM v_ai_history h1
    WHERE h1.leave_of_absence_yn = 'Y'
      AND h1.assignment_start_date = (
        SELECT MAX(h2.assignment_start_date)
        FROM v_ai_history h2
        WHERE h2.emp_id = h1.emp_id
          AND h2.leave_of_absence_yn = 'Y'
      )
) h
  ON e.emp_id = h.emp_id
WHERE e.work_status = '재직'
GROUP BY NVL(h.assignment_reason_code, '기타')
ORDER BY 인원수 DESC, 휴직유형 ASC
```

**Run #2**
```sql
WITH latest_leave AS (
  SELECT h.*
  FROM v_ai_history h
  WHERE h.LEAVE_OF_ABSENCE_YN = 'Y'
    AND h.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = h.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
    )
)
SELECT
  ll.ASSIGNMENT_TYPE_CODE AS LEAVE_TYPE_CODE,
  ll.ASSIGNMENT_REASON_CODE AS LEAVE_REASON_CODE,
  COUNT(DISTINCT ll.EMP_ID) AS PERSON_COUNT
FROM v_ai_employee e
LEFT JOIN latest_leave ll
  ON e.EMP_ID = ll.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  ll.ASSIGNMENT_TYPE_CODE,
  ll.ASSIGNMENT_REASON_CODE
HAVING COUNT(DISTINCT ll.EMP_ID) > 0
ORDER BY PERSON_COUNT DESC, ll.ASSIGNMENT_TYPE_CODE, ll.ASSIGNMENT_REASON_CODE
```

---

## H19 [PASS-INCONSISTENT] **불일치**
**평가등급이 C나 D인 직원의 근속연수 분포를 보여줘**

**Run #1**
```sql
SELECT
  NVL(e.CAREER_YEARS, 0) AS career_years,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
GROUP BY NVL(e.CAREER_YEARS, 0)
ORDER BY NVL(e.CAREER_YEARS, 0) DESC
```

**Run #2**
```sql
SELECT
  NVL(e.CAREER_YEARS, 0) AS career_years,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
GROUP BY NVL(e.CAREER_YEARS, 0)
ORDER BY NVL(e.CAREER_YEARS, 0) DESC
```

---

## H20 [PASS-INCONSISTENT] **불일치**
**공제와 세금 비율을 직급별로 분석해줘**

**Run #1**
```sql
SELECT
  e.GRADE,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS DEDUCTION_AMOUNT_SUM,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS TAX_AMOUNT_SUM,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS GROSS_PAY_AMOUNT_SUM,
  ROUND(
    (SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
    2
  ) AS DEDUCTION_RATIO_PCT,
  ROUND(
    (SUM(NVL(p.TAX_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
    2
  ) AS TAX_RATIO_PCT,
  ROUND(
    ((SUM(NVL(p.DEDUCTION_AMOUNT, 0)) + SUM(NVL(p.TAX_AMOUNT, 0))) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0)) * 100,
    2
  ) AS DEDUCTION_TAX_RATIO_PCT
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY e.GRADE
ORDER BY TAX_AMOUNT_SUM DESC
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, e.GRADE) AS 직급,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 지급합계,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS 공제합계,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS 세금합계,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 4)
  END AS 공제비율,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.TAX_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 4)
  END AS 세금비율,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.TOTAL_DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 4)
  END AS 총공제비율
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, e.GRADE)
ORDER BY
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE SUM(NVL(p.TOTAL_DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))
  END DESC,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) DESC
```

---

## X01 [PASS-INCONSISTENT] **불일치**
**부서별 최고 급여자 이름과 급여를 알려줘**

**Run #1**
```sql
SELECT department, emp_name, net_pay
FROM (
    SELECT
        e.department AS department,
        e.emp_name AS emp_name,
        p.net_pay_amount AS net_pay,
        ROW_NUMBER() OVER (
            PARTITION BY e.department
            ORDER BY p.net_pay_amount DESC, e.emp_id DESC
        ) AS rn
    FROM v_ai_employee e
    JOIN v_ai_pay_report p
        ON e.emp_id = p.emp_id
    WHERE e.work_status = '재직'
      AND p.payment_type_name = '정기급여'
      AND p.net_pay_amount IS NOT NULL
)
WHERE rn = 1
ORDER BY net_pay DESC, department ASC, emp_name ASC
```

**Run #2**
```sql
SELECT
  department,
  emp_name,
  position,
  net_pay_amount
FROM (
  SELECT
    e.DEPARTMENT AS department,
    e.EMP_NAME AS emp_name,
    e.POSITION AS position,
    p.NET_PAY_AMOUNT AS net_pay_amount,
    ROW_NUMBER() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY p.NET_PAY_AMOUNT DESC, p.PAY_YEAR_MONTH DESC, p.PAY_DATE DESC
    ) AS rn
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND p.NET_PAY_AMOUNT IS NOT NULL
) x
WHERE rn = 1
ORDER BY net_pay_amount DESC, department ASC
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
  AND f.APPR_GRADE = 'S'
WHERE e.WORK_STATUS = '재직'
  AND f.END_YMD >= ADD_MONTHS(SYSDATE, -120)
  AND f.END_YMD <= SYSDATE
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT
HAVING COUNT(DISTINCT f.APPR_ID) >= 2
ORDER BY
  s_grade_count DESC,
  e.EMP_ID
```

**Run #2**
```sql
SELECT
    e.EMP_ID,
    e.EMP_NAME,
    e.COMPANY_CODE,
    e.DEPARTMENT,
    e.CAREER_YEARS,
    COUNT(DISTINCT f.APPR_ID) AS s_grade_cnt
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
  AND f.END_YMD >= ADD_MONTHS(SYSDATE, -120)
  AND f.END_YMD <= SYSDATE
GROUP BY
    e.EMP_ID,
    e.EMP_NAME,
    e.COMPANY_CODE,
    e.DEPARTMENT,
    e.CAREER_YEARS
HAVING COUNT(DISTINCT f.APPR_ID) >= 2
ORDER BY
    s_grade_cnt DESC,
    e.EMP_ID DESC
```

---

## X03 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 입사 퇴사 추이를 보여줘**

**Run #1**
```sql
SELECT
    year_val,
    SUM(hire_cnt) AS hire_count,
    SUM(retire_cnt) AS retire_count
FROM (
    SELECT
        TO_CHAR(e.HIRE_DATE, 'YYYY') AS year_val,
        COUNT(DISTINCT e.EMP_ID) AS hire_cnt,
        0 AS retire_cnt
    FROM v_ai_employee e
    WHERE e.HIRE_DATE IS NOT NULL
      AND TO_CHAR(e.HIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
    GROUP BY TO_CHAR(e.HIRE_DATE, 'YYYY')
    UNION ALL
    SELECT
        TO_CHAR(e.RETIRE_DATE, 'YYYY') AS year_val,
        0 AS hire_cnt,
        COUNT(DISTINCT e.EMP_ID) AS retire_cnt
    FROM v_ai_employee e
    WHERE e.RETIRE_DATE IS NOT NULL
      AND TO_CHAR(e.RETIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
    GROUP BY TO_CHAR(e.RETIRE_DATE, 'YYYY')
)
GROUP BY year_val
ORDER BY year_val DESC
```

**Run #2**
```sql
SELECT
  year_val,
  SUM(hire_cnt) AS hire_cnt,
  SUM(retire_cnt) AS retire_cnt
FROM (
  SELECT
    TO_CHAR(e.HIRE_DATE, 'YYYY') AS year_val,
    COUNT(DISTINCT e.EMP_ID) AS hire_cnt,
    0 AS retire_cnt
  FROM v_ai_employee e
  WHERE e.HIRE_DATE IS NOT NULL
    AND e.HIRE_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -120)
    AND e.HIRE_DATE <= SYSDATE
  GROUP BY TO_CHAR(e.HIRE_DATE, 'YYYY')
  UNION ALL
  SELECT
    TO_CHAR(e.RETIRE_DATE, 'YYYY') AS year_val,
    0 AS hire_cnt,
    COUNT(DISTINCT e.EMP_ID) AS retire_cnt
  FROM v_ai_employee e
  WHERE e.RETIRE_DATE IS NOT NULL
    AND e.RETIRE_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -120)
    AND e.RETIRE_DATE <= SYSDATE
  GROUP BY TO_CHAR(e.RETIRE_DATE, 'YYYY')
) x
GROUP BY year_val
ORDER BY year_val DESC
```

---

## X04 [PASS-INCONSISTENT] **불일치**
**승진 이력이 없는 근속 5년 이상 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.CAREER_YEARS,
  e.DUTY,
  e.DUTY_DATE,
  e.HIRE_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC
FETCH FIRST 20 ROWS ONLY
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.CAREER_YEARS
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
    e.DEPARTMENT,
    COUNT(t.COMPLETION_STATUS) AS total_training_count,
    SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) AS completed_training_count,
    ROUND(
        (SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) / NULLIF(COUNT(t.COMPLETION_STATUS), 0)) * 100,
        2
    ) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY completion_rate_pct DESC, total_training_count DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       COUNT(t.COURSE_NAME) AS total_training_count,
       SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) AS completed_training_count,
       NVL(ROUND(
         100 * SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) / NULLIF(COUNT(t.COURSE_NAME), 0),
         1
       ), 0) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY completed_training_count DESC, completion_rate_pct DESC
```

---

## X06 [WARN-EMPTY] **불일치**
**직급별 평균 승진 소요연수를 알려줘**

**Run #1**
```sql
WITH promo AS (
    SELECT
        h.EMP_ID,
        h.ASSIGNMENT_GRADE_CODE,
        MIN(h.ASSIGNMENT_DATE) AS PROMOTION_DATE
    FROM v_ai_history h
    WHERE h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
      AND h.ASSIGNMENT_GRADE_CODE IS NOT NULL
    GROUP BY
        h.EMP_ID,
        h.ASSIGNMENT_GRADE_CODE
)
SELECT
    p.ASSIGNMENT_GRADE_CODE AS GRADE_CODE,
    ROUND(AVG(MONTHS_BETWEEN(p.PROMOTION_DATE, e.HIRE_DATE) / 12), 2) AS AVG_PROMOTION_YEARS
FROM promo p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
    p.ASSIGNMENT_GRADE_CODE
ORDER BY
    AVG_PROMOTION_YEARS DESC
```

**Run #2**
```sql
WITH promo AS (
    SELECT
        e.emp_id,
        NVL(h.assignment_grade_code, '미상') AS grade_code,
        h.assignment_date,
        LAG(h.assignment_date) OVER (
            PARTITION BY e.emp_id
            ORDER BY h.assignment_sequence, h.assignment_date
        ) AS prev_promo_date
    FROM v_ai_employee e
    JOIN v_ai_history h
        ON e.emp_id = h.emp_id
       AND h.assignment_type_code LIKE '%승진%'
    WHERE e.work_status = '재직'
)
SELECT
    grade_code,
    AVG(MONTHS_BETWEEN(assignment_date, prev_promo_date) / 12) AS avg_promotion_years
FROM promo
WHERE prev_promo_date IS NOT NULL
GROUP BY grade_code
ORDER BY avg_promotion_years DESC
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
  ) AS female_ratio_pct
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY total_emp_count DESC, DEPARTMENT
```

**Run #2**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,
  COUNT(DISTINCT EMP_ID) AS total_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0 / COUNT(DISTINCT EMP_ID),
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
SELECT
  COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) AS female_count,
  COUNT(DISTINCT e.EMP_ID) AS total_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS female_ratio
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND CASE e.POSITION
        WHEN '과장' THEN 1
        WHEN '차장' THEN 2
        WHEN '부장' THEN 3
        WHEN '전무' THEN 4
        WHEN '상무' THEN 5
        WHEN '사장' THEN 6
        WHEN '회장' THEN 7
        ELSE 0
      END >= 1
```

**Run #2**
```sql
SELECT
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND (
    POSITION IN ('과장', '차장', '부장', '사장', '회장', '이사', '전무', '부사장')
    OR DUTY IN ('대표이사', '팀장')
  )
  AND (
    TO_NUMBER(REGEXP_SUBSTR(GRADE, '\d+')) <= 4
  )
```

---

## X09 [PASS-INCONSISTENT] **불일치**
**입사 5년차 이내 직원 중 S등급을 받은 비율은?**

**Run #1**
```sql
SELECT
  ROUND(
    COUNT(DISTINCT CASE WHEN f.EMP_ID IS NOT NULL THEN e.EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS s_grade_ratio
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_GRADE = 'S'
WHERE e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT CASE
    WHEN EXISTS (
      SELECT 1
      FROM v_ai_feedback f
      WHERE f.EMP_ID = e.EMP_ID
        AND f.APPR_GRADE = 'S'
    ) THEN e.EMP_ID
  END) AS s_grade_emp_count,
  COUNT(DISTINCT e.EMP_ID) AS total_emp_count,
  ROUND(
    COUNT(DISTINCT CASE
      WHEN EXISTS (
        SELECT 1
        FROM v_ai_feedback f
        WHERE f.EMP_ID = e.EMP_ID
          AND f.APPR_GRADE = 'S'
      ) THEN e.EMP_ID
    END) * 100.0 / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    2
  ) AS s_grade_ratio_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

---

## X10 [PASS-INCONSISTENT] **불일치**
**부서별 평가등급 분포를 보여줘**

**Run #1**
```sql
SELECT
  NVL(e.DEPARTMENT, '미등록') AS department,
  f.APPR_GRADE,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT e.EMP_ID) * 100.0
    / NULLIF(SUM(COUNT(DISTINCT e.EMP_ID)) OVER (PARTITION BY NVL(e.DEPARTMENT, '미등록')), 0),
    1
  ) AS percentage
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_GRADE IS NOT NULL
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(e.DEPARTMENT, '미등록'),
  f.APPR_GRADE
ORDER BY emp_count DESC, department, f.APPR_GRADE
```

**Run #2**
```sql
WITH base AS (
  SELECT
    NVL(f.EMP_ORG_NM, e.DEPARTMENT) AS department,
    f.APPR_GRADE AS appr_grade,
    COUNT(DISTINCT f.EMP_ID) AS emp_count
  FROM v_ai_feedback f
  JOIN v_ai_employee e
    ON f.EMP_ID = e.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND f.APPR_GRADE IS NOT NULL
  GROUP BY NVL(f.EMP_ORG_NM, e.DEPARTMENT), f.APPR_GRADE
)
SELECT
  department,
  appr_grade,
  emp_count,
  ROUND(
    emp_count * 100.0 / NULLIF(SUM(emp_count) OVER (PARTITION BY department), 0),
    1
  ) AS percentage
FROM base
ORDER BY emp_count DESC,
  CASE appr_grade
    WHEN 'S' THEN 1
    WHEN 'A' THEN 2
    WHEN 'B' THEN 3
    WHEN 'C' THEN 4
    WHEN 'D' THEN 5
    ELSE 99
  END,
  department
```

---

## X11 [PASS] 일치
**최근 입사자 5명의 이름 부서 직급을 알려줘**

**Run #1**
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
  e.department,
  COUNT(DISTINCT e.emp_id) AS employee_count
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND e.birth_date IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, e.birth_date) / 12) >= 50
GROUP BY e.department
ORDER BY employee_count DESC
```

**Run #2**
```sql
SELECT
    department,
    employee_count
FROM (
    SELECT
        e.department,
        COUNT(DISTINCT e.emp_id) AS employee_count
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
      AND e.birth_date IS NOT NULL
      AND TRUNC(MONTHS_BETWEEN(SYSDATE, e.birth_date) / 12) >= 50
    GROUP BY
        e.department
)
ORDER BY employee_count DESC, department ASC
```

---

## X13 [PASS-INCONSISTENT] **불일치**
**부서별 자격증 보유율을 계산해줘**

**Run #1**
```sql
SELECT
  NVL(e.department, '미지정') AS department,
  COUNT(DISTINCT e.emp_id) AS total_employee_count,
  COUNT(DISTINCT CASE WHEN l.emp_id IS NOT NULL THEN e.emp_id END) AS license_employee_count,
  ROUND(
    (COUNT(DISTINCT CASE WHEN l.emp_id IS NOT NULL THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0)) * 100,
    2
  ) AS license_ownership_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_license l
  ON e.emp_id = l.emp_id
WHERE e.work_status = '재직'
GROUP BY NVL(e.department, '미지정')
ORDER BY license_ownership_rate_pct DESC, department ASC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS total_emp_count,
  COUNT(DISTINCT CASE
    WHEN EXISTS (
      SELECT 1
      FROM v_ai_license l
      WHERE l.EMP_ID = e.EMP_ID
    ) THEN e.EMP_ID
  END) AS license_emp_count,
  ROUND(
    100 * COUNT(DISTINCT CASE
      WHEN EXISTS (
        SELECT 1
        FROM v_ai_license l
        WHERE l.EMP_ID = e.EMP_ID
      ) THEN e.EMP_ID
    END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    2
  ) AS license_coverage_rate_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY license_coverage_rate_pct DESC, license_emp_count DESC
```

---

## X14 [WARN-EMPTY] **불일치**
**연도별 부서별 승진자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS YEAR,
  e.DEPARTMENT AS DEPARTMENT,
  COUNT(DISTINCT h.EMP_ID) AS PROMOTION_COUNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  e.DEPARTMENT
ORDER BY
  PROMOTION_COUNT DESC,
  DEPARTMENT ASC,
  YEAR DESC
```

**Run #2**
```sql
SELECT TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS "연도",
       NVL(e.DEPARTMENT, '(미지정)') AS "부서",
       COUNT(DISTINCT e.EMP_ID) AS "승진자수"
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
GROUP BY TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
         NVL(e.DEPARTMENT, '(미지정)')
ORDER BY "연도" ASC, "승진자수" DESC
```

---

## X15 [WARN-EMPTY] 일치
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

---

