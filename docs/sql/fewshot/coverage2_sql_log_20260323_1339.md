# SQL 비교 로그 (실시간)

> 시작: 2026-03-23 13:39:03
> 반복횟수: 2회

## S01 [PASS-INCONSISTENT] **불일치**
**현재 재직 중인 전체 직원 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(*) AS active_count
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

## S02 [PASS] 일치
**퇴직한 직원은 총 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retire_count
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
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND GENDER IN ('남', '여')
GROUP BY GENDER
ORDER BY COUNT(DISTINCT EMP_ID) DESC
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
ORDER BY CASE GENDER WHEN '남' THEN 1 WHEN '여' THEN 2 ELSE 3 END DESC, GENDER DESC
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
    NVL(GRADE, '미지정') AS grade,
    COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY NVL(GRADE, '미지정')
ORDER BY
    CASE NVL(GRADE, '미지정')
        WHEN '1급' THEN 1
        WHEN '2급' THEN 2
        WHEN '3급' THEN 3
        WHEN '4급' THEN 4
        WHEN '5급' THEN 5
        WHEN '6급' THEN 6
        WHEN '7급' THEN 7
        WHEN '8급' THEN 8
        WHEN '9급' THEN 9
        ELSE 10
    END
```

**Run #2**
```sql
SELECT
    e.GRADE,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY emp_count DESC, e.GRADE DESC
```

---

## S07 [PASS-INCONSISTENT] **불일치**
**정규직 직원은 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(*) AS regular_employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND EMP_TYPE = '정규직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT emp_id) AS 정규직_인원
FROM v_ai_employee
WHERE work_status = '재직'
  AND emp_type = '정규직'
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
  e.DUTY,
  e.HIRE_DATE,
  e.GENDER,
  e.GRADE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND (
    e.EMP_TYPE = '기간제'
    OR e.EMP_TYPE = '계약직'
    OR e.EMP_TYPE LIKE '%기간%'
  )
ORDER BY e.EMP_ID DESC
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
  e.GRADE,
  e.HIRE_DATE,
  e.CAREER_MONTHS,
  e.GENDER
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '기간제'
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
ORDER BY e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  EMP_NAME AS EMP_NAME,
  DEPARTMENT AS DEPARTMENT
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2020'
ORDER BY EMP_NAME DESC, DEPARTMENT DESC
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
SELECT COUNT(DISTINCT e.EMP_ID) AS active_department_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.DEPARTMENT = '경영지원부'
```

---

## S11 [PASS] 일치
**근속연수가 10년 이상인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND CAREER_YEARS >= 10
ORDER BY employee_count DESC
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS employee_count
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
    COUNT(DISTINCT EMP_ID) AS emp_count
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
    COUNT(DISTINCT EMP_ID) DESC,
    DUTY DESC
```

---

## S14 [PASS] 일치
**2018년에 퇴직한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS retire_count
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
SELECT COUNT(*) AS 군필자수
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
WHERE r.REWARD_TYPE = '포상'
  AND r.REWARD_YEAR = '2017'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_reward
WHERE REWARD_TYPE = '포상'
  AND REWARD_YEAR = '2017'
ORDER BY emp_count DESC
```

---

## S18 [PASS-INCONSISTENT] **불일치**
**2018년 기준 잔여연차가 0인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = '2018'
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) = 0
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT d.EMP_ID) AS EMP_CNT
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = '2018'
  AND d.REMAINING_LEAVE_DAYS = 0
```

---

## S19 [PASS-INCONSISTENT] **불일치**
**2017년 교육을 수료한 건수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.COMPLETION_STATUS = '수료'
      AND t.TRAINING_YEAR = '2017'
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS edu_completed_count
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
SELECT COUNT(f.APPR_ID) AS s_grade_count
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
  ON f.EMP_ID = e.EMP_ID
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
  AVG(CAREER_YEARS) AS AVG_CAREER_YEARS
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND DEPARTMENT IS NOT NULL
GROUP BY DEPARTMENT
ORDER BY AVG(CAREER_YEARS) DESC, DEPARTMENT DESC
```

**Run #2**
```sql
SELECT
    DEPARTMENT,
    AVG(NVL(CAREER_YEARS, 0)) AS AVG_CAREER_YEARS
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY AVG(NVL(CAREER_YEARS, 0)) DESC
```

---

## S22 [PASS-INCONSISTENT] **불일치**
**연도별 입사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
  COUNT(DISTINCT EMP_ID) AS hire_count
FROM v_ai_employee
WHERE HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')
ORDER BY year_val DESC
```

**Run #2**
```sql
SELECT
  TO_CHAR(e.HIRE_DATE, 'YYYY') AS year_val,
  COUNT(DISTINCT e.EMP_ID) AS hire_count
FROM v_ai_employee e
WHERE e.HIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(e.HIRE_DATE, 'YYYY')
ORDER BY TO_NUMBER(year_val) DESC
```

---

## S23 [PASS-INCONSISTENT] **불일치**
**연도별 퇴사자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(retire_date, 'YYYY') AS retire_year,
  COUNT(DISTINCT emp_id) AS retire_count
FROM v_ai_employee
WHERE retire_date IS NOT NULL
GROUP BY TO_CHAR(retire_date, 'YYYY')
ORDER BY retire_year DESC
```

**Run #2**
```sql
SELECT
  TO_CHAR(e.RETIRE_DATE, 'YYYY') AS retire_year,
  COUNT(DISTINCT e.EMP_ID) AS retire_count
FROM v_ai_employee e
WHERE e.RETIRE_DATE IS NOT NULL
GROUP BY TO_CHAR(e.RETIRE_DATE, 'YYYY')
ORDER BY retire_year DESC
```

---

## S24 [PASS-INCONSISTENT] **불일치**
**직급별 남녀 비율을 보여줘**

**Run #1**
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
ORDER BY GRADE, emp_count DESC, GENDER
```

**Run #2**
```sql
SELECT
  GRADE,
  GENDER,
  COUNT(DISTINCT EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT EMP_ID) * 100.0
    / NULLIF(SUM(COUNT(DISTINCT EMP_ID)) OVER (PARTITION BY GRADE), 0),
    1
  ) AS percentage
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY
  GRADE,
  GENDER
ORDER BY
  emp_count DESC,
  GRADE,
  GENDER
```

---

## S25 [PASS-INCONSISTENT] **불일치**
**연령대별 직원 분포를 알려줘**

**Run #1**
```sql
SELECT age_group, employee_count
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
ORDER BY employee_count DESC, age_group DESC
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
END, employee_count DESC
```

---

## S26 [PASS-INCONSISTENT] **불일치**
**근속연수 구간별 인원 분포를 보여줘**

**Run #1**
```sql
SELECT tenure_group,
       employee_count
FROM (
    SELECT
        CASE
            WHEN e.CAREER_YEARS < 1 THEN '1년 미만'
            WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN '1~3년'
            WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN '3~5년'
            WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN '5~10년'
            WHEN e.CAREER_YEARS >= 10 THEN '10년 이상'
        END AS tenure_group,
        COUNT(DISTINCT e.EMP_ID) AS employee_count,
        CASE
            WHEN e.CAREER_YEARS < 1 THEN 1
            WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN 2
            WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN 3
            WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN 4
            WHEN e.CAREER_YEARS >= 10 THEN 5
        END AS sort_key
    FROM v_ai_employee e
    WHERE e.WORK_STATUS = '재직'
    GROUP BY
        CASE
            WHEN e.CAREER_YEARS < 1 THEN '1년 미만'
            WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN '1~3년'
            WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN '3~5년'
            WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN '5~10년'
            WHEN e.CAREER_YEARS >= 10 THEN '10년 이상'
        END,
        CASE
            WHEN e.CAREER_YEARS < 1 THEN 1
            WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN 2
            WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN 3
            WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN 4
            WHEN e.CAREER_YEARS >= 10 THEN 5
        END
)
ORDER BY sort_key
```

**Run #2**
```sql
SELECT
  tenure_group,
  employee_count
FROM (
  SELECT
    CASE
      WHEN CAREER_YEARS < 1 THEN '1년 미만'
      WHEN CAREER_YEARS < 3 THEN '1~3년'
      WHEN CAREER_YEARS < 5 THEN '3~5년'
      WHEN CAREER_YEARS < 10 THEN '5~10년'
      ELSE '10년 이상'
    END AS tenure_group,
    CASE
      WHEN CAREER_YEARS < 1 THEN 1
      WHEN CAREER_YEARS < 3 THEN 2
      WHEN CAREER_YEARS < 5 THEN 3
      WHEN CAREER_YEARS < 10 THEN 4
      ELSE 5
    END AS group_rank,
    COUNT(DISTINCT EMP_ID) AS employee_count
  FROM v_ai_employee
  WHERE WORK_STATUS = '재직'
  GROUP BY
    CASE
      WHEN CAREER_YEARS < 1 THEN '1년 미만'
      WHEN CAREER_YEARS < 3 THEN '1~3년'
      WHEN CAREER_YEARS < 5 THEN '3~5년'
      WHEN CAREER_YEARS < 10 THEN '5~10년'
      ELSE '10년 이상'
    END,
    CASE
      WHEN CAREER_YEARS < 1 THEN 1
      WHEN CAREER_YEARS < 3 THEN 2
      WHEN CAREER_YEARS < 5 THEN 3
      WHEN CAREER_YEARS < 10 THEN 4
      ELSE 5
    END
)
ORDER BY group_rank DESC
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
SELECT
  DEPARTMENT,
  COUNT(DISTINCT EMP_ID) AS emp_count
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
ORDER BY emp_count DESC, HIRE_TYPE DESC
```

**Run #2**
```sql
SELECT
  e.HIRE_TYPE,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
GROUP BY e.HIRE_TYPE
ORDER BY emp_count DESC
```

---

## S29 [PASS-INCONSISTENT] **불일치**
**부서별 최근 입사자 입사일을 알려줘**

**Run #1**
```sql
WITH ranked AS (
  SELECT
    EMP_ID,
    EMP_NAME,
    DEPARTMENT,
    POSITION,
    HIRE_DATE,
    ROW_NUMBER() OVER (
      PARTITION BY DEPARTMENT
      ORDER BY HIRE_DATE DESC, EMP_ID DESC
    ) AS RN
  FROM v_ai_employee
  WHERE HIRE_DATE IS NOT NULL
)
SELECT
  DEPARTMENT,
  EMP_ID,
  EMP_NAME,
  POSITION,
  HIRE_DATE
FROM ranked
WHERE RN = 1
ORDER BY HIRE_DATE DESC, DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
  DEPARTMENT,
  EMP_ID,
  EMP_NAME,
  POSITION,
  HIRE_DATE
FROM (
  SELECT
    e.DEPARTMENT,
    e.EMP_ID,
    e.EMP_NAME,
    e.POSITION,
    e.HIRE_DATE,
    ROW_NUMBER() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY e.HIRE_DATE DESC, e.EMP_ID DESC
    ) AS RN
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
    AND e.DEPARTMENT IS NOT NULL
) t
WHERE t.RN = 1
ORDER BY t.HIRE_DATE DESC, t.EMP_ID DESC
```

---

## S30 [PASS-INCONSISTENT] **불일치**
**지급유형별 총 지급액을 보여줘**

**Run #1**
```sql
SELECT
  p.PAYMENT_TYPE_NAME,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount,
  SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS total_fixed_pay_amount,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS total_variable_pay_amount,
  SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS total_net_pay_amount
FROM v_ai_pay_report p
GROUP BY p.PAYMENT_TYPE_NAME
ORDER BY total_gross_pay_amount DESC
```

**Run #2**
```sql
SELECT
  PAYMENT_TYPE_NAME,
  SUM(NVL(GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_pay_report
GROUP BY PAYMENT_TYPE_NAME
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
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IS NOT NULL
GROUP BY f.APPR_GRADE
ORDER BY emp_count DESC, f.APPR_GRADE ASC
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
ORDER BY emp_count DESC, f.APPR_GRADE ASC
```

---

## S32 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수를 알려줘**

**Run #1**
```sql
SELECT
    t.training_type,
    SUM(CASE WHEN t.completion_status = '수료' THEN 1 ELSE 0 END) AS completed_count
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON e.emp_id = t.emp_id
WHERE e.work_status = '재직'
GROUP BY t.training_type
ORDER BY completed_count DESC
```

**Run #2**
```sql
SELECT t.TRAINING_TYPE,
       SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY t.TRAINING_TYPE
ORDER BY completed_count DESC
```

---

## S33 [PASS-INCONSISTENT] **불일치**
**발령유형별 건수를 보여줘**

**Run #1**
```sql
SELECT
  h.ASSIGNMENT_TYPE_CODE,
  COUNT(*) AS total_count,
  COUNT(DISTINCT h.EMP_ID) AS emp_count
FROM v_ai_history h
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC, emp_count DESC
```

**Run #2**
```sql
SELECT
  h.ASSIGNMENT_TYPE_CODE,
  COUNT(*) AS total_count,
  COUNT(DISTINCT h.EMP_ID) AS emp_count
FROM v_ai_history h
INNER JOIN v_ai_employee e
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY h.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC, emp_count DESC
```

---

## S34 [PASS-INCONSISTENT] **불일치**
**2018년 기준 직원별 잔여연차 상위 10명을 알려줘**

**Run #1**
```sql
SELECT
  emp_id,
  emp_name,
  department,
  total_remaining_leave_days
FROM (
  SELECT
    e.emp_id,
    e.emp_name,
    e.department,
    SUM(NVL(r.remaining_leave_days, 0)) AS total_remaining_leave_days
  FROM v_ai_employee e
  LEFT JOIN v_ai_dtm_yy_rest r
    ON e.emp_id = r.emp_id
    AND r.reference_year = '2018'
  WHERE e.work_status = '재직'
  GROUP BY
    e.emp_id,
    e.emp_name,
    e.department
)
ORDER BY
  total_remaining_leave_days DESC,
  emp_id DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.POSITION,
  SUM(NVL(r.REMAINING_LEAVE_DAYS, 0)) AS REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest r
  ON e.EMP_ID = r.EMP_ID
  AND r.REFERENCE_YEAR = '2018'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.POSITION
ORDER BY
  REMAINING_LEAVE_DAYS DESC
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
ORDER BY r.REWARD_YEAR DESC
```

**Run #2**
```sql
SELECT
  r.REWARD_YEAR,
  COUNT(*) AS reward_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
GROUP BY r.REWARD_YEAR
ORDER BY TO_NUMBER(r.REWARD_YEAR) DESC NULLS LAST
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
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND a.REGION = '서울'
```

---

## M02 [PASS-INCONSISTENT] **불일치**
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
SELECT NVL(a.REGION, '미등록') AS region,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_address a
       ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(a.REGION, '미등록')
ORDER BY emp_count DESC, region ASC
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
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS prev_career_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_career c
    WHERE c.EMP_ID = e.EMP_ID
  )
ORDER BY prev_career_emp_count DESC
```

---

## M04 [PASS-INCONSISTENT] **불일치**
**전직장 경력이 3건 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID, e.EMP_NAME, e.EMP_NAME_ENG, e.DEPARTMENT, e.POSITION, COUNT(*) AS prev_career_count
FROM v_ai_employee e
JOIN v_ai_career c ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.EMP_NAME_ENG, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY prev_career_count DESC, e.EMP_ID DESC
```

**Run #2**
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
ORDER BY
  prev_career_count DESC,
  e.EMP_ID ASC
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
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       e.POSITION,
       s.MAJOR_NAME,
       s.DOUBLE_MAJOR_NAME,
       s.SCHOOL_NAME
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.COMPANY_CODE,
       e.POSITION,
       e.DEPARTMENT,
       s.SCHOOL_NAME,
       s.MAJOR_NAME,
       s.DOUBLE_MAJOR_NAME,
       s.EDUCATION_LEVEL,
       s.GRADUATION_STATUS,
       s.GRADUATION_DATE
FROM v_ai_employee e
JOIN v_ai_scholar s ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND (s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
       OR s.DOUBLE_MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%')
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
FETCH FIRST 20 ROWS ONLY
```

---

## M07 [PASS] 일치
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

---

## M08 [WARN-EMPTY] **불일치**
**자녀가 2명 이상인 직원 목록을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  COUNT(*) AS CHILD_COUNT
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
ORDER BY CHILD_COUNT DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  COUNT(DISTINCT f.EMP_ID) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
 AND f.RELATION = '자녀'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT
HAVING COUNT(DISTINCT f.EMP_ID) >= 2
ORDER BY child_count DESC, e.EMP_NAME ASC
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
      AND l.SCORE >= 800
  )
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS employed_toi_people_count
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
SELECT COUNT(DISTINCT e.EMP_ID) AS license_employee_count
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
SELECT COUNT(DISTINCT e.EMP_ID) AS license_retired_active_count
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
  e.EMP_ID,
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
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
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
  e.DEPARTMENT,
  e.POSITION,
  COUNT(DISTINCT l.EMP_ID) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(DISTINCT l.EMP_ID) >= 3
ORDER BY license_count DESC, e.EMP_ID DESC
```

---

## M13 [PASS-INCONSISTENT] **불일치**
**포상을 받은 재직자 부서별 수는?**

**Run #1**
```sql
SELECT
  e.department,
  COUNT(DISTINCT e.emp_id) AS emp_count
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.emp_id = e.emp_id
      AND r.reward_type = '포상'
  )
GROUP BY e.department
ORDER BY emp_count DESC, e.department
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
GROUP BY e.DEPARTMENT
ORDER BY EMP_COUNT DESC, e.DEPARTMENT ASC
```

---

## M14 [PASS] 일치
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
  e.GRADE,
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
  e.GRADE,
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
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_completion_hours_per_person
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
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS avg_hours_per_person
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
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.DUTY,
  e.GRADE,
  f.APPR_NM,
  f.APPR_YMD,
  f.END_YMD,
  NVL(f.APPR_SCORE, 0) AS APPR_SCORE
FROM v_ai_employee e
JOIN (
  SELECT *
  FROM (
    SELECT
      f0.EMP_ID,
      f0.COMPANY_CD,
      f0.LOCALE_CD,
      f0.PEE_DEFINITION_ID,
      f0.APPR_ID,
      f0.APPR_NM,
      f0.PEE_TYPE_CD,
      f0.PEE_TYPE_NM,
      f0.EMP_ORG_ID,
      f0.EMP_ORG_NM,
      f0.RATEE_ORG_ID,
      f0.RATEE_ORG_NM,
      f0.RATEE_GROUP_ID,
      f0.RATEE_GROUP_NAME,
      f0.RATEE_LEVEL_CD,
      f0.RATEE_LEVEL_NM,
      f0.APPR_SCORE,
      f0.APPR_GRADE,
      f0.RK,
      f0.PEE_OPINION,
      f0.APPR_SCORE_OPEN_YN,
      f0.APPR_GRADE_OPEN_YN,
      f0.APPR_RANK_OPEN_YN,
      f0.APPR_OPINION_OPEN_YN,
      f0.END_YMD,
      f0.APPR_YMD,
      ROW_NUMBER() OVER (
        PARTITION BY f0.EMP_ID
        ORDER BY
          f0.APPR_YMD DESC,
          f0.END_YMD DESC,
          f0.APPR_ID DESC
      ) AS rn
    FROM v_ai_feedback f0
    WHERE f0.APPR_GRADE = 'S'
      AND f0.APPR_YMD IS NOT NULL
  )
  WHERE rn = 1
) f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY
  NVL(f.APPR_SCORE, 0) DESC,
  e.EMP_ID DESC
```

**Run #2**
```sql
WITH latest AS (
  SELECT
      f.*,
      ROW_NUMBER() OVER (
        PARTITION BY f.EMP_ID
        ORDER BY f.APPR_YMD DESC, f.END_YMD DESC, f.APPR_ID DESC
      ) AS rn
  FROM v_ai_feedback f
  WHERE f.APPR_GRADE IS NOT NULL
)
SELECT
    e.EMP_ID,
    e.EMP_NAME,
    e.EMP_NAME_ENG,
    e.COMPANY_CODE,
    e.POSITION,
    e.DEPARTMENT,
    e.DUTY,
    l.APPR_NM,
    l.PEE_TYPE_NM,
    l.APPR_YMD,
    l.APPR_GRADE,
    l.APPR_SCORE
FROM latest l
JOIN v_ai_employee e
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND l.rn = 1
  AND l.APPR_GRADE = 'S'
ORDER BY NVL(l.APPR_SCORE, 0) DESC, l.APPR_YMD DESC, e.EMP_ID DESC
```

---

## M18 [PASS] 일치
**부서별 평균 평가점수를 보여줘**

**Run #1**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(f.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_SCORE > 0
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
  AND f.APPR_SCORE > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC
```

---

## M19 [PASS-INCONSISTENT] **불일치**
**최근 10년간 승진한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS PROMOTED_EMP_COUNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
  AND h.ASSIGNMENT_DATE <= SYSDATE
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS PROMOTED_EMPLOYEE_COUNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
  AND h.ASSIGNMENT_DATE <= SYSDATE
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
  h.ASSIGNMENT_TYPE_CODE,
  h.ASSIGNMENT_REASON_CODE,
  h.ASSIGNMENT_START_DATE,
  h.ASSIGNMENT_END_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.LEAVE_OF_ABSENCE_YN = 'Y'
  AND h.ASSIGNMENT_START_DATE <= SYSDATE
  AND h.ASSIGNMENT_END_DATE >= SYSDATE
  AND h.ASSIGNMENT_START_DATE = (
    SELECT MAX(h2.ASSIGNMENT_START_DATE)
    FROM v_ai_history h2
    WHERE h2.EMP_ID = e.EMP_ID
      AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
      AND h2.ASSIGNMENT_START_DATE <= SYSDATE
      AND h2.ASSIGNMENT_END_DATE >= SYSDATE
  )
ORDER BY h.ASSIGNMENT_START_DATE DESC
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
  h.ASSIGNMENT_HISTORY_ID,
  h.ASSIGNMENT_TYPE_CODE,
  h.ASSIGNMENT_REASON_CODE,
  h.ASSIGNMENT_START_DATE,
  h.ASSIGNMENT_END_DATE,
  h.EXPECTED_RETURN_FROM_LEAVE_DATE,
  h.LEAVE_OF_ABSENCE_YN,
  h.HR_REFLECTED_YN,
  h.PRINT_YN
FROM v_ai_employee e
JOIN (
  SELECT
    hh.*
  FROM v_ai_history hh
  WHERE hh.LEAVE_OF_ABSENCE_YN = 'Y'
    AND hh.ASSIGNMENT_END_DATE >= SYSDATE
    AND hh.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = hh.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
        AND h2.ASSIGNMENT_END_DATE >= SYSDATE
    )
) h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY h.ASSIGNMENT_START_DATE DESC, e.EMP_ID DESC
```

---

## M21 [PASS-INCONSISTENT] **불일치**
**부서별 월평균 실수령액을 보여줘**

**Run #1**
```sql
SELECT
  t.DEPARTMENT,
  NVL(ROUND(AVG(t.MONTHLY_NET_PAY_AMOUNT)), 0) AS AVG_MONTHLY_NET_PAY_AMOUNT,
  COUNT(DISTINCT t.PAY_YEAR_MONTH) AS PAY_MONTH_COUNT
FROM (
  SELECT
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH,
    SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS MONTHLY_NET_PAY_AMOUNT
  FROM v_ai_employee e
  LEFT JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY
    e.DEPARTMENT,
    p.PAY_YEAR_MONTH
) t
GROUP BY
  t.DEPARTMENT
ORDER BY
  AVG_MONTHLY_NET_PAY_AMOUNT DESC,
  t.DEPARTMENT DESC
```

**Run #2**
```sql
SELECT
  x.department,
  ROUND(AVG(x.monthly_net_pay_amount)) AS avg_monthly_net_pay_amount
FROM (
  SELECT
    e.department AS department,
    p.pay_year_month AS pay_year_month,
    SUM(NVL(p.net_pay_amount, 0)) AS monthly_net_pay_amount
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.emp_id = p.emp_id
   AND p.payment_type_name = '정기급여'
  WHERE e.work_status = '재직'
  GROUP BY
    e.department,
    p.pay_year_month
) x
GROUP BY x.department
ORDER BY avg_monthly_net_pay_amount DESC
```

---

## M22 [PASS-INCONSISTENT] **불일치**
**직급별 평균 총지급액을 알려줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미등록') AS JOB_GRADE_NAME,
  ROUND(AVG(p.GROSS_PAY_AMOUNT), 0) AS AVG_GROSS_PAY_AMOUNT,
  SUM(p.GROSS_PAY_AMOUNT) AS TOTAL_GROSS_PAY_AMOUNT,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON p.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(p.JOB_GRADE_NAME, '미등록')
ORDER BY
  AVG(p.GROSS_PAY_AMOUNT) DESC,
  SUM(p.GROSS_PAY_AMOUNT) DESC
```

**Run #2**
```sql
SELECT
  NVL(JOB_GRADE_NAME, '미지정') AS job_grade_name,
  COUNT(DISTINCT EMP_ID) AS emp_count,
  ROUND(AVG(GROSS_PAY_AMOUNT), 2) AS avg_total_gross_pay_amount
FROM v_ai_pay_report
GROUP BY NVL(JOB_GRADE_NAME, '미지정')
ORDER BY avg_total_gross_pay_amount DESC
```

---

## M23 [PASS-INCONSISTENT] **불일치**
**부서별 평균 연차 사용률을 알려줘**

**Run #1**
```sql
WITH emp_rates AS (
    SELECT
        e.DEPARTMENT,
        e.EMP_ID,
        CASE
            WHEN SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) > 0
            THEN SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) * 100.0 / SUM(NVL(d.TOTAL_LEAVE_DAYS, 0))
            ELSE 0
        END AS usage_rate
    FROM v_ai_employee e
    LEFT JOIN v_ai_dtm_yy_rest d
        ON e.EMP_ID = d.EMP_ID
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.DEPARTMENT, e.EMP_ID
)
SELECT
    DEPARTMENT,
    COUNT(DISTINCT EMP_ID) AS emp_count,
    ROUND(AVG(usage_rate), 2) AS avg_usage_rate
FROM emp_rates
GROUP BY DEPARTMENT
ORDER BY avg_usage_rate DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(
    CASE
      WHEN NVL(d.TOTAL_LEAVE_DAYS, 0) > 0
      THEN NVL(d.USED_LEAVE_DAYS_PAST, 0) * 100.0 / d.TOTAL_LEAVE_DAYS
      ELSE 0
    END
  ), 2) AS avg_leave_usage_rate
FROM v_ai_employee e
LEFT JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_leave_usage_rate DESC, emp_count DESC, e.DEPARTMENT
```

---

## M24 [WARN-EMPTY] **불일치**
**잔여연차가 10일 이상인 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       d.REFERENCE_YEAR,
       d.REMAINING_LEAVE_DAYS,
       d.TOTAL_LEAVE_DAYS,
       d.USED_LEAVE_DAYS_PAST
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY d.REMAINING_LEAVE_DAYS DESC, d.TOTAL_LEAVE_DAYS DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
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
ORDER BY NVL(d.REMAINING_LEAVE_DAYS, 0) DESC, e.EMP_ID DESC
```

---

## M25 [PASS] 일치
**병역유형별 재직자 수를 보여줘**

**Run #1**
```sql
SELECT NVL(m.MILITARY_TYPE, '미등록') AS military_type,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미등록')
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT NVL(m.MILITARY_TYPE, '미등록') AS military_type,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
LEFT JOIN v_ai_military m
  ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(m.MILITARY_TYPE, '미등록')
ORDER BY emp_count DESC
```

---

## M26 [PASS-INCONSISTENT] **불일치**
**상여금 지급 총액 부서별 비교를 해줘**

**Run #1**
```sql
SELECT NVL(r.ORGANIZATION_NAME, '미지정') AS DEPARTMENT_NAME,
       COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
       SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS BONUS_TOTAL_AMOUNT
FROM v_ai_pay_report r
INNER JOIN v_ai_employee e
        ON e.EMP_ID = r.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND r.PAYMENT_TYPE_NAME = '상여'
GROUP BY NVL(r.ORGANIZATION_NAME, '미지정')
ORDER BY BONUS_TOTAL_AMOUNT DESC
```

**Run #2**
```sql
SELECT
  NVL(p.ORGANIZATION_NAME, '미등록') AS department_name,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_bonus_amount
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON p.EMP_ID = e.EMP_ID
  AND p.PAYMENT_TYPE_NAME LIKE '%상여%'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(p.ORGANIZATION_NAME, '미등록')
ORDER BY total_bonus_amount DESC
```

---

## M27 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT t.TRAINING_TYPE,
       e.DEPARTMENT,
       COUNT(*) AS completed_count,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY t.TRAINING_TYPE, e.DEPARTMENT
ORDER BY completed_count DESC, emp_count DESC
```

**Run #2**
```sql
SELECT
  t.TRAINING_TYPE,
  e.DEPARTMENT,
  COUNT(*) AS completed_count,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  t.TRAINING_TYPE,
  e.DEPARTMENT
ORDER BY
  completed_count DESC,
  emp_count DESC,
  t.TRAINING_TYPE DESC,
  e.DEPARTMENT DESC
```

---

## M28 [PASS-INCONSISTENT] **불일치**
**평가등급이 C 또는 D인 재직자 명단과 부서를 알려줘**

**Run #1**
```sql
SELECT DISTINCT
       e.EMP_ID,
       e.EMP_NAME,
       e.COMPANY_CODE,
       e.DEPARTMENT,
       f.APPR_GRADE
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
ORDER BY e.CAREER_YEARS DESC NULLS LAST, e.EMP_ID DESC
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
  e.DEPARTMENT,
  COUNT(h.ASSIGNMENT_HISTORY_ID) AS move_count
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE = '이동'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY move_count DESC, e.DEPARTMENT
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       COUNT(*) AS move_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%이동%'
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
  EMP_COUNT DESC,
  e.DEPARTMENT ASC,
  EDUCATION_LEVEL ASC
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
ORDER BY
  EMP_COUNT DESC,
  e.DEPARTMENT ASC,
  EDUCATION_LEVEL ASC
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
ORDER BY e.CAREER_YEARS DESC, e.HIRE_DATE DESC
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
  e.GRADE,
  e.GENDER
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
  fg.appr_grade,
  AVG(lp.net_pay_amount) AS avg_net_pay_amount
FROM (
  SELECT DISTINCT
    f.EMP_ID,
    f.APPR_GRADE
  FROM v_ai_feedback f
  WHERE NVL(f.APPR_SCORE, 0) > 0
) fg
JOIN v_ai_employee e
  ON e.EMP_ID = fg.EMP_ID
 AND e.WORK_STATUS = '재직'
LEFT JOIN (
  SELECT
    x.EMP_ID,
    x.NET_PAY_AMOUNT AS net_pay_amount
  FROM (
    SELECT
      p.EMP_ID,
      p.NET_PAY_AMOUNT,
      ROW_NUMBER() OVER (
        PARTITION BY p.EMP_ID
        ORDER BY p.PAY_DATE DESC, p.PAY_DATE_ID DESC
      ) AS rn
    FROM v_ai_pay_report p
  ) x
  WHERE x.rn = 1
) lp
  ON lp.EMP_ID = fg.EMP_ID
GROUP BY
  fg.appr_grade
ORDER BY
  avg_net_pay_amount DESC
```

**Run #2**
```sql
SELECT
  lf.appr_grade AS appr_grade,
  COUNT(DISTINCT e.emp_id) AS emp_count,
  ROUND(AVG(NVL(lp.net_pay_amount, 0))) AS avg_net_pay_amount
FROM v_ai_employee e
JOIN (
  SELECT emp_id, appr_grade
  FROM (
    SELECT
      f.emp_id,
      f.appr_grade,
      ROW_NUMBER() OVER (
        PARTITION BY f.emp_id
        ORDER BY f.appr_ymd DESC, f.end_ymd DESC, f.appr_id DESC
      ) AS rn
    FROM v_ai_feedback f
    WHERE f.appr_grade IS NOT NULL
  )
  WHERE rn = 1
) lf
  ON e.emp_id = lf.emp_id
JOIN (
  SELECT emp_id, net_pay_amount
  FROM (
    SELECT
      p.emp_id,
      p.net_pay_amount,
      ROW_NUMBER() OVER (
        PARTITION BY p.emp_id
        ORDER BY p.pay_date DESC, p.pay_year_month DESC
      ) AS rn
    FROM v_ai_pay_report p
  )
  WHERE rn = 1
) lp
  ON e.emp_id = lp.emp_id
WHERE e.work_status = '재직'
GROUP BY lf.appr_grade
ORDER BY avg_net_pay_amount DESC
```

---

## H04 [PASS-INCONSISTENT] **불일치**
**동일 직급 내 남녀 평균 급여 차이를 보여줘**

**Run #1**
```sql
SELECT
  e.GRADE AS grade,
  ROUND(AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END), 0) AS male_avg_net_pay,
  ROUND(AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END), 0) AS female_avg_net_pay,
  ROUND(
    AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END) - AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END),
    0
  ) AS avg_net_pay_diff_male_minus_female
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
HAVING
  COUNT(DISTINCT CASE WHEN e.GENDER = '남' THEN e.EMP_ID END) > 0
  AND COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) > 0
ORDER BY
  ABS(
    AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END) - AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END)
  ) DESC
```

**Run #2**
```sql
SELECT
    p.JOB_GRADE_NAME AS 직급,
    ROUND(AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END), 0) AS 남자_평균_실지급액,
    ROUND(AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END), 0) AS 여자_평균_실지급액,
    ROUND(
        AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END)
        - AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END),
        0
    ) AS 남녀_평균_급여_차이,
    COUNT(DISTINCT CASE WHEN e.GENDER = '남' THEN e.EMP_ID END) AS 남자_인원수,
    COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) AS 여자_인원수
FROM v_ai_pay_report p
JOIN v_ai_employee e
    ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY p.JOB_GRADE_NAME
HAVING
    COUNT(DISTINCT CASE WHEN e.GENDER = '남' THEN e.EMP_ID END) > 0
    AND COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) > 0
ORDER BY
    ABS(
        AVG(CASE WHEN e.GENDER = '남' THEN p.NET_PAY_AMOUNT END)
        - AVG(CASE WHEN e.GENDER = '여' THEN p.NET_PAY_AMOUNT END)
    ) DESC
```

---

## H05 [PASS-INCONSISTENT] **불일치**
**교육 미이수 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.COMPANY_CODE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND NOT EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = TO_CHAR(SYSDATE, 'YYYY')
      AND t.COMPLETION_STATUS = '수료'
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
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
    e.EMP_ID,
    e.EMP_NAME,
    e.DEPARTMENT,
    e.POSITION,
    e.GRADE,
    e.DUTY,
    e.HIRE_DATE,
    e.CAREER_YEARS,
    e.CAREER_MONTHS,
    e.EMP_TYPE,
    e.GENDER
FROM v_ai_employee e
LEFT JOIN v_ai_history h
    ON e.EMP_ID = h.EMP_ID
   AND (
        h.ASSIGNMENT_TYPE_CODE IN ('승진', '승격')
        OR h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
   )
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 10
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.HIRE_DATE DESC
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
WITH dept_base AS (
  SELECT DISTINCT e.DEPARTMENT
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
),
tr AS (
  SELECT
    e.DEPARTMENT,
    AVG(NVL(t.TRAINING_COST, 0)) AS avg_training_cost,
    COUNT(DISTINCT t.EMP_ID) AS training_emp_count
  FROM v_ai_employee e
  LEFT JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
),
fb AS (
  SELECT
    e.DEPARTMENT,
    AVG(NVL(f.APPR_SCORE, 0)) AS avg_feedback_score,
    COUNT(DISTINCT f.EMP_ID) AS feedback_emp_count
  FROM v_ai_employee e
  LEFT JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND f.APPR_SCORE > 0
  GROUP BY e.DEPARTMENT
)
SELECT
  d.DEPARTMENT,
  ROUND(NVL(tr.avg_training_cost, 0), 0) AS avg_training_cost,
  NVL(tr.training_emp_count, 0) AS training_emp_count,
  ROUND(NVL(fb.avg_feedback_score, 0), 2) AS avg_feedback_score,
  NVL(fb.feedback_emp_count, 0) AS feedback_emp_count
FROM dept_base d
LEFT JOIN tr
  ON d.DEPARTMENT = tr.DEPARTMENT
LEFT JOIN fb
  ON d.DEPARTMENT = fb.DEPARTMENT
ORDER BY
  NVL(fb.avg_feedback_score, 0) DESC,
  NVL(tr.avg_training_cost, 0) DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  ROUND(AVG(NVL(t.TRAINING_COST, 0)), 0) AS avg_training_cost,
  ROUND(AVG(NVL(f.APPR_SCORE, 0)), 1) AS avg_evaluation_score
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY GREATEST(NVL(ROUND(AVG(NVL(t.TRAINING_COST, 0)), 0), 0), NVL(ROUND(AVG(NVL(f.APPR_SCORE, 0)), 1), 0)) DESC, avg_training_cost DESC
```

---

## H08 [PASS-INCONSISTENT] **불일치**
**직급별 평균 실수령액과 최대 최소 급여를 알려줘**

**Run #1**
```sql
SELECT
    e.GRADE AS job_grade,
    ROUND(AVG(p.NET_PAY_AMOUNT), 0) AS avg_net_pay_amount,
    MAX(p.NET_PAY_AMOUNT) AS max_net_pay_amount,
    MIN(p.NET_PAY_AMOUNT) AS min_net_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY avg_net_pay_amount DESC
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미지정') AS JOB_GRADE_NAME,
  ROUND(AVG(p.NET_PAY_AMOUNT), 0) AS AVG_NET_PAY_AMOUNT,
  MAX(p.NET_PAY_AMOUNT) AS MAX_NET_PAY_AMOUNT,
  MIN(p.NET_PAY_AMOUNT) AS MIN_NET_PAY_AMOUNT
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY NVL(p.JOB_GRADE_NAME, '미지정')
ORDER BY MAX(p.NET_PAY_AMOUNT) DESC
```

---

## H09 [PASS-INCONSISTENT] **불일치**
**부서별 퇴직률을 계산해줘**

**Run #1**
```sql
SELECT
  a.department AS department,
  NVL(b.retire_count, 0) AS retire_count,
  a.total_count AS total_count,
  ROUND(NVL(b.retire_count, 0) / NULLIF(a.total_count, 0) * 100, 2) AS retire_rate
FROM
  (
    SELECT
      NVL(DEPARTMENT, '미지정') AS department,
      COUNT(DISTINCT EMP_ID) AS total_count
    FROM v_ai_employee
    GROUP BY NVL(DEPARTMENT, '미지정')
  ) a
  LEFT JOIN
  (
    SELECT
      NVL(DEPARTMENT, '미지정') AS department,
      COUNT(DISTINCT EMP_ID) AS retire_count
    FROM v_ai_employee
    WHERE RETIRE_DATE IS NOT NULL
    GROUP BY NVL(DEPARTMENT, '미지정')
  ) b
    ON a.department = b.department
ORDER BY
  ROUND(NVL(b.retire_count, 0) / NULLIF(a.total_count, 0) * 100, 2) DESC,
  a.total_count DESC
```

**Run #2**
```sql
WITH dept_agg AS (
  SELECT
    NVL(DEPARTMENT, '미분류') AS DEPARTMENT,
    COUNT(DISTINCT EMP_ID) AS TOTAL_CNT,
    COUNT(DISTINCT CASE WHEN RETIRE_DATE IS NOT NULL THEN EMP_ID END) AS RETIRE_CNT
  FROM v_ai_employee
  GROUP BY NVL(DEPARTMENT, '미분류')
)
SELECT
  DEPARTMENT,
  RETIRE_CNT,
  TOTAL_CNT,
  ROUND(NVL(RETIRE_CNT, 0) / NULLIF(TOTAL_CNT, 0) * 100, 2) AS RETIRE_RATE_PCT
FROM dept_agg
ORDER BY RETIRE_RATE_PCT DESC, TOTAL_CNT DESC
```

---

## H10 [FAIL-SQL] 일치
**고정비 대비 변동비 비율을 부서별로 분석해줘**

**Run #1**
(SQL 없음)

**Run #2**
(SQL 없음)

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
 AND NVL(f.APPR_SCORE, 0) > 0
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
```

**Run #2**
```sql
SELECT AVG(f.APPR_SCORE) AS avg_appr_score
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON f.EMP_ID = e.EMP_ID
 AND NVL(f.APPR_SCORE, 0) > 0
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
```

---

## H12 [PASS-INCONSISTENT] **불일치**
**부서별 승진자 수와 승진률을 보여줘**

**Run #1**
```sql
SELECT
  department,
  total_emp_cnt,
  promote_emp_cnt,
  ROUND(promote_emp_cnt / NULLIF(total_emp_cnt, 0) * 100, 2) AS promotion_rate_pct
FROM (
  SELECT
    NVL(e.department, '미지정') AS department,
    COUNT(DISTINCT e.emp_id) AS total_emp_cnt,
    COUNT(DISTINCT h.emp_id) AS promote_emp_cnt
  FROM v_ai_employee e
  LEFT JOIN v_ai_history h
    ON e.emp_id = h.emp_id
   AND h.assignment_type_code IN ('직급변경', '직책변경')
   AND h.assignment_reason_code IN ('승격', '승진')
  WHERE e.work_status = '재직'
  GROUP BY NVL(e.department, '미지정')
)
ORDER BY promote_emp_cnt DESC, total_emp_cnt DESC
```

**Run #2**
```sql
SELECT
  t.DEPARTMENT,
  NVL(p.PROMOTED_COUNT, 0) AS PROMOTED_COUNT,
  ROUND(NVL(p.PROMOTED_COUNT, 0) / NULLIF(t.TOTAL_COUNT, 0) * 100, 2) AS PROMOTION_RATE
FROM
  (
    SELECT
      NVL(e.DEPARTMENT, '(미상)') AS DEPARTMENT,
      COUNT(DISTINCT e.EMP_ID) AS TOTAL_COUNT
    FROM v_ai_employee e
    WHERE e.WORK_STATUS = '재직'
    GROUP BY NVL(e.DEPARTMENT, '(미상)')
  ) t
  LEFT JOIN
  (
    SELECT
      NVL(e.DEPARTMENT, '(미상)') AS DEPARTMENT,
      COUNT(DISTINCT h.EMP_ID) AS PROMOTED_COUNT
    FROM v_ai_employee e
    JOIN v_ai_history h
      ON e.EMP_ID = h.EMP_ID
    WHERE e.WORK_STATUS = '재직'
      AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
    GROUP BY NVL(e.DEPARTMENT, '(미상)')
  ) p
    ON t.DEPARTMENT = p.DEPARTMENT
ORDER BY NVL(p.PROMOTED_COUNT, 0) DESC, t.DEPARTMENT DESC
```

---

## H13 [PASS-INCONSISTENT] **불일치**
**부서별 1인당 교육비용을 보여줘**

**Run #1**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)), 1) AS total_training_cost,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_training_cost_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY total_training_cost DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.TRAINING_COST, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_training_cost_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t ON e.EMP_ID = t.EMP_ID AND t.COMPLETION_STATUS = '수료'
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
  e.GRADE,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(NVL(x.usage_rate, 0)), 2) AS avg_usage_rate
FROM v_ai_employee e
LEFT JOIN (
  SELECT
    d.EMP_ID,
    CASE
      WHEN NVL(SUM(d.TOTAL_LEAVE_DAYS), 0) > 0
      THEN NVL(SUM(d.USED_LEAVE_DAYS_PAST), 0) * 100.0 / SUM(d.TOTAL_LEAVE_DAYS)
      ELSE 0
    END AS usage_rate
  FROM v_ai_dtm_yy_rest d
  GROUP BY d.EMP_ID
) x
  ON e.EMP_ID = x.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY avg_usage_rate DESC, emp_count DESC
```

**Run #2**
```sql
WITH emp_leave AS (
    SELECT
        e.EMP_ID,
        NVL(e.GRADE, '미정') AS GRADE,
        SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) AS USED_SUM_DAYS,
        SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) AS TOTAL_SUM_DAYS
    FROM v_ai_employee e
    LEFT JOIN v_ai_dtm_yy_rest d
        ON e.EMP_ID = d.EMP_ID
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.EMP_ID, NVL(e.GRADE, '미정')
),
emp_rate AS (
    SELECT
        GRADE,
        EMP_ID,
        CASE
            WHEN TOTAL_SUM_DAYS > 0
                THEN USED_SUM_DAYS * 100.0 / TOTAL_SUM_DAYS
            ELSE 0
        END AS USAGE_RATE
    FROM emp_leave
)
SELECT
    GRADE,
    ROUND(AVG(NVL(USAGE_RATE, 0)), 2) AS AVG_USAGE_RATE
FROM emp_rate
GROUP BY GRADE
ORDER BY AVG_USAGE_RATE DESC
```

---

## H15 [PASS-INCONSISTENT] **불일치**
**부서별 평가점수 표준편차를 계산해줘**

**Run #1**
```sql
SELECT
    e.DEPARTMENT,
    STDDEV_POP(f.APPR_SCORE) AS score_stddev
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
    AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY
    e.DEPARTMENT
ORDER BY
    NVL(STDDEV_POP(f.APPR_SCORE), 0) DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  COUNT(DISTINCT f.EMP_ID) AS scored_emp_count,
  NVL(STDDEV_SAMP(f.APPR_SCORE), 0) AS score_stddev
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY NVL(STDDEV_SAMP(f.APPR_SCORE), 0) DESC, e.DEPARTMENT ASC
```

---

## H16 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 급여 총지급액 추이를 보여줘**

**Run #1**
```sql
SELECT
  p.PAY_YEAR,
  SUM(p.GROSS_PAY_AMOUNT) AS TOTAL_GROSS_PAY_AMOUNT
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAY_YEAR BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
GROUP BY p.PAY_YEAR
ORDER BY TOTAL_GROSS_PAY_AMOUNT DESC
```

**Run #2**
```sql
SELECT
  p.PAY_YEAR AS pay_year,
  SUM(p.GROSS_PAY_AMOUNT) AS total_gross_pay_amount
FROM v_ai_pay_report p
JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND TO_NUMBER(p.PAY_YEAR) BETWEEN (TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY')) - 9) AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
GROUP BY p.PAY_YEAR
ORDER BY total_gross_pay_amount DESC
```

---

## H17 [PASS-INCONSISTENT] **불일치**
**정규직과 기간제 비율 및 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT
    DEPARTMENT,
    정규직인원,
    기간제인원,
    전체인원,
    ROUND(정규직인원 / NULLIF(전체인원, 0) * 100, 2) AS 정규직비율_부서,
    ROUND(기간제인원 / NULLIF(전체인원, 0) * 100, 2) AS 기간제비율_부서,
    ROUND(SUM(정규직인원) OVER () / NULLIF(SUM(전체인원) OVER (), 0) * 100, 2) AS 정규직비율_전체,
    ROUND(SUM(기간제인원) OVER () / NULLIF(SUM(전체인원) OVER (), 0) * 100, 2) AS 기간제비율_전체
FROM (
    SELECT
        NVL(DEPARTMENT, '미지정') AS DEPARTMENT,
        COUNT(DISTINCT CASE WHEN EMP_TYPE = '정규직' THEN EMP_ID END) AS 정규직인원,
        COUNT(DISTINCT CASE WHEN EMP_TYPE = '기간제' THEN EMP_ID END) AS 기간제인원,
        COUNT(DISTINCT EMP_ID) AS 전체인원
    FROM v_ai_employee
    WHERE WORK_STATUS = '재직'
      AND EMP_TYPE IN ('정규직', '기간제')
    GROUP BY NVL(DEPARTMENT, '미지정')
) d
ORDER BY
    전체인원 DESC,
    DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
    NVL(DEPARTMENT, '(미지정)') AS department,
    COUNT(DISTINCT CASE WHEN EMP_TYPE = '정규직' THEN EMP_ID END) AS regular_jik_count,
    COUNT(DISTINCT CASE WHEN EMP_TYPE = '기간제' THEN EMP_ID END) AS contract_jik_count,
    COUNT(DISTINCT EMP_ID) AS total_emp_count,
    ROUND(
        COUNT(DISTINCT CASE WHEN EMP_TYPE = '정규직' THEN EMP_ID END)
        / NULLIF(COUNT(DISTINCT EMP_ID), 0) * 100,
        2
    ) AS regular_jik_ratio_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN EMP_TYPE = '기간제' THEN EMP_ID END)
        / NULLIF(COUNT(DISTINCT EMP_ID), 0) * 100,
        2
    ) AS contract_jik_ratio_pct
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND EMP_TYPE IN ('정규직', '기간제')
GROUP BY
    NVL(DEPARTMENT, '(미지정)')
ORDER BY total_emp_count DESC, department ASC
```

---

## H18 [PASS-INCONSISTENT] **불일치**
**휴직 유형별 현황을 알려줘**

**Run #1**
```sql
SELECT
  NVL(h.ASSIGNMENT_REASON_CODE, '기타') AS LEAVE_TYPE_CODE,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
JOIN (
  SELECT
    h1.EMP_ID,
    h1.ASSIGNMENT_REASON_CODE,
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
GROUP BY NVL(h.ASSIGNMENT_REASON_CODE, '기타')
ORDER BY EMP_COUNT DESC, LEAVE_TYPE_CODE ASC
```

**Run #2**
```sql
SELECT
  h.ASSIGNMENT_REASON_CODE AS LEAVE_TYPE_CODE,
  COUNT(DISTINCT CASE WHEN h.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.LEAVE_OF_ABSENCE_YN = 'Y'
 AND h.ASSIGNMENT_START_DATE = (
       SELECT MAX(h2.ASSIGNMENT_START_DATE)
       FROM v_ai_history h2
       WHERE h2.EMP_ID = e.EMP_ID
         AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
 )
WHERE e.WORK_STATUS = '재직'
GROUP BY h.ASSIGNMENT_REASON_CODE
HAVING COUNT(DISTINCT CASE WHEN h.EMP_ID IS NOT NULL THEN e.EMP_ID END) > 0
ORDER BY EMP_COUNT DESC
```

---

## H19 [PASS-INCONSISTENT] **불일치**
**평가등급이 C나 D인 직원의 근속연수 분포를 보여줘**

**Run #1**
```sql
SELECT NVL(e.CAREER_YEARS, 0) AS career_years,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
GROUP BY NVL(e.CAREER_YEARS, 0)
ORDER BY career_years DESC
```

**Run #2**
```sql
SELECT
  NVL(e.CAREER_YEARS, 0) AS career_years,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_feedback f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.APPR_GRADE IN ('C', 'D')
      AND f.APPR_GRADE IS NOT NULL
  )
GROUP BY NVL(e.CAREER_YEARS, 0)
ORDER BY NVL(e.CAREER_YEARS, 0) DESC
```

---

## H20 [PASS-INCONSISTENT] **불일치**
**공제와 세금 비율을 직급별로 분석해줘**

**Run #1**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미지정') AS 직급,
  COUNT(DISTINCT e.EMP_ID) AS 직원수,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS 총공제액,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS 총세금액,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 지급합계,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 2)
  END AS 공제비율,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.TAX_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 2)
  END AS 세금비율
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON p.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, '미지정')
ORDER BY SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) DESC
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS 직급,
  COUNT(DISTINCT e.EMP_ID) AS 인원수,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS 공제합계,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS 세금합계,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 지급합계,
  ROUND(
    SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0) * 100,
    2
  ) AS 공제비율_PCT,
  ROUND(
    SUM(NVL(p.TAX_AMOUNT, 0)) / NULLIF(SUM(NVL(p.GROSS_PAY_AMOUNT, 0)), 0) * 100,
    2
  ) AS 세금비율_PCT
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME)
ORDER BY 세금비율_PCT DESC, 공제비율_PCT DESC
```

---

## X01 [PASS-INCONSISTENT] **불일치**
**부서별 최고 급여자 이름과 급여를 알려줘**

**Run #1**
```sql
SELECT
  department,
  emp_name,
  position,
  net_pay_amount
FROM (
  SELECT
    e.department AS department,
    e.emp_name AS emp_name,
    e.position AS position,
    p.net_pay_amount AS net_pay_amount,
    ROW_NUMBER() OVER (
      PARTITION BY e.department
      ORDER BY p.net_pay_amount DESC
    ) AS rn
  FROM v_ai_employee e
  JOIN v_ai_pay_report p
    ON e.emp_id = p.emp_id
  WHERE e.work_status = '재직'
) x
WHERE rn = 1
ORDER BY net_pay_amount DESC
```

**Run #2**
```sql
SELECT
  DEPARTMENT,
  EMP_NAME,
  POSITION,
  NET_PAY_AMOUNT AS NET_PAY
FROM (
  SELECT
    e.DEPARTMENT,
    e.EMP_NAME,
    e.POSITION,
    p.NET_PAY_AMOUNT,
    ROW_NUMBER() OVER (
      PARTITION BY e.DEPARTMENT
      ORDER BY p.NET_PAY_AMOUNT DESC, p.PAY_DATE DESC
    ) AS RN
  FROM v_ai_employee e
  INNER JOIN v_ai_pay_report p
    ON e.EMP_ID = p.EMP_ID
  WHERE e.WORK_STATUS = '재직'
)
WHERE RN = 1
ORDER BY NET_PAY DESC
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
  e.POSITION,
  COUNT(DISTINCT f.APPR_ID) AS s_grade_count
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE = 'S'
  AND f.END_YMD >= ADD_MONTHS(SYSDATE, -120)
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(DISTINCT f.APPR_ID) >= 2
ORDER BY s_grade_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.CAREER_YEARS,
  COUNT(DISTINCT f.APPR_ID) AS s_grade_cnt
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
  e.DEPARTMENT,
  e.CAREER_YEARS
HAVING COUNT(DISTINCT f.APPR_ID) >= 2
ORDER BY s_grade_cnt DESC, e.EMP_ID DESC
```

---

## X03 [WARN-EMPTY] **불일치**
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
    AND TO_CHAR(HIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -60), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
  GROUP BY TO_CHAR(HIRE_DATE, 'YYYY')

  UNION ALL

  SELECT
    TO_CHAR(RETIRE_DATE, 'YYYY') AS year_val,
    0 AS hire_count,
    COUNT(DISTINCT EMP_ID) AS retire_count
  FROM v_ai_employee
  WHERE RETIRE_DATE IS NOT NULL
    AND TO_CHAR(RETIRE_DATE, 'YYYY') BETWEEN TO_CHAR(ADD_MONTHS(SYSDATE, -60), 'YYYY') AND TO_CHAR(SYSDATE, 'YYYY')
  GROUP BY TO_CHAR(RETIRE_DATE, 'YYYY')
)
GROUP BY year_val
ORDER BY year_val DESC
```

**Run #2**
```sql
SELECT year_val,
       COUNT(DISTINCT hire_emp_id) AS hire_count,
       COUNT(DISTINCT retire_emp_id) AS retire_count
FROM (
    SELECT TO_CHAR(e.HIRE_DATE, 'YYYY') AS year_val,
           e.EMP_ID AS hire_emp_id,
           NULL AS retire_emp_id
    FROM v_ai_employee e
    WHERE e.HIRE_DATE IS NOT NULL
      AND e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -120)

    UNION ALL

    SELECT TO_CHAR(e.RETIRE_DATE, 'YYYY') AS year_val,
           NULL AS hire_emp_id,
           e.EMP_ID AS retire_emp_id
    FROM v_ai_employee e
    WHERE e.RETIRE_DATE IS NOT NULL
      AND e.RETIRE_DATE >= ADD_MONTHS(SYSDATE, -120)
)
GROUP BY year_val
ORDER BY TO_NUMBER(year_val) DESC
```

---

## X04 [PASS-INCONSISTENT] **불일치**
**승진 이력이 없는 근속 5년 이상 재직자 명단을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION,
  e.GRADE,
  e.HIRE_DATE,
  e.CAREER_YEARS,
  e.COMPANY_CODE
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.EMP_ID DESC
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
  e.GRADE,
  e.HIRE_DATE,
  e.CAREER_YEARS,
  e.DUTY,
  e.DUTY_DATE
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
    COUNT(DISTINCT t.EMP_ID) AS trained_emp_count,
    COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END) AS completed_emp_count,
    CASE
        WHEN COUNT(DISTINCT t.EMP_ID) = 0 THEN 0
        ELSE ROUND(
            COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END)
            / COUNT(DISTINCT t.EMP_ID) * 100
        , 2)
    END AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY completion_rate_pct DESC, trained_emp_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  NVL(COUNT(DISTINCT t.EMP_ID), 0) AS total_emp_count,
  NVL(COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END), 0) AS completed_emp_count,
  ROUND(
    100 * NVL(COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN t.EMP_ID END), 0)
    / NULLIF(NVL(COUNT(DISTINCT t.EMP_ID), 0), 0),
    2
  ) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY total_emp_count DESC, completed_emp_count DESC
```

---

## X06 [WARN-EMPTY] **불일치**
**직급별 평균 승진 소요연수를 알려줘**

**Run #1**
```sql
SELECT
  NVL(p.grade_code, '미상') AS grade_code,
  AVG(p.promote_years) AS avg_promotion_years
FROM (
  SELECT
    h.assignment_grade_code AS grade_code,
    (MONTHS_BETWEEN(h.assignment_date,
      LAG(h.assignment_date) OVER (
        PARTITION BY h.emp_id
        ORDER BY h.assignment_date, h.assignment_sequence
      )
    ) / 12) AS promote_years
  FROM v_ai_employee e
  INNER JOIN v_ai_history h
    ON e.emp_id = h.emp_id
  WHERE e.work_status = '재직'
    AND h.assignment_type_code LIKE '%승진%'
) p
WHERE p.promote_years IS NOT NULL
GROUP BY
  NVL(p.grade_code, '미상')
ORDER BY
  avg_promotion_years DESC
```

**Run #2**
```sql
WITH promo AS (
  SELECT
      e.emp_id,
      e.hire_date,
      h.assignment_grade_code,
      h.assignment_date,
      LAG(h.assignment_date) OVER (
        PARTITION BY e.emp_id
        ORDER BY h.assignment_date, h.assignment_sequence
      ) AS prev_promo_date
  FROM v_ai_employee e
  JOIN v_ai_history h
    ON e.emp_id = h.emp_id
  WHERE e.work_status = '재직'
    AND h.assignment_type_code LIKE '%승진%'
),
promo_calc AS (
  SELECT
      NVL(assignment_grade_code, '미상') AS assignment_grade_code_group,
      (MONTHS_BETWEEN(assignment_date, NVL(prev_promo_date, hire_date)) / 12) AS promo_years
  FROM promo
)
SELECT
  assignment_grade_code_group,
  AVG(promo_years) AS avg_promotion_years
FROM promo_calc
GROUP BY assignment_grade_code_group
ORDER BY avg_promotion_years DESC
```

---

## X07 [PASS-INCONSISTENT] **불일치**
**부서별 여성 비율을 알려줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,
  COUNT(DISTINCT EMP_ID) AS total_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY female_count DESC, DEPARTMENT
```

**Run #2**
```sql
SELECT
  NVL(e.department, '(미정)') AS department,
  COUNT(DISTINCT CASE WHEN e.gender = '여' THEN e.emp_id END) AS female_count,
  COUNT(DISTINCT e.emp_id) AS total_count,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN e.gender = '여' THEN e.emp_id END) / COUNT(DISTINCT e.emp_id),
    1
  ) AS female_ratio_percent
FROM v_ai_employee e
WHERE e.work_status = '재직'
GROUP BY NVL(e.department, '(미정)')
ORDER BY total_count DESC, female_count DESC
```

---

## X08 [PASS-INCONSISTENT] **불일치**
**과장 이상 관리직의 여성 비율은?**

**Run #1**
```sql
SELECT
  ROUND(
    100 * COUNT(DISTINCT CASE WHEN e.GENDER = '여' THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS female_ratio_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.POSITION IN ('과장', '차장', '부장', '이사', '전무', '상무', '사장', '회장')
```

**Run #2**
```sql
SELECT
  ROUND(
    (COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0)
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio_pct
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND POSITION IN ('과장', '차장', '부장', '상무', '전무', '부회장', '회장')
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
          AND f.APPR_GRADE = 'S'
      ) THEN e.EMP_ID
    END) * 100.0 / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS s_grade_ratio_pct
FROM v_ai_employee e
WHERE e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT CASE WHEN f.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS s_grade_emp_count,
  COUNT(DISTINCT e.EMP_ID) AS total_emp_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN f.EMP_ID IS NOT NULL THEN e.EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    2
  ) AS s_grade_ratio_pct
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
  AND f.APPR_GRADE = 'S'
WHERE e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

---

## X10 [PASS-INCONSISTENT] **불일치**
**부서별 평가등급 분포를 보여줘**

**Run #1**
```sql
SELECT
    x.dept_name,
    x.appr_grade,
    x.emp_count,
    ROUND(
        x.emp_count * 100.0 / NULLIF(SUM(x.emp_count) OVER (PARTITION BY x.dept_name), 0),
        1
    ) AS percentage
FROM (
    SELECT
        COALESCE(f.RATEE_ORG_NM, f.EMP_ORG_NM, '미등록') AS dept_name,
        f.APPR_GRADE AS appr_grade,
        COUNT(DISTINCT f.EMP_ID) AS emp_count
    FROM v_ai_feedback f
    JOIN v_ai_employee e
        ON e.EMP_ID = f.EMP_ID
    WHERE e.WORK_STATUS = '재직'
      AND f.APPR_GRADE IS NOT NULL
    GROUP BY
        COALESCE(f.RATEE_ORG_NM, f.EMP_ORG_NM, '미등록'),
        f.APPR_GRADE
) x
ORDER BY
    x.emp_count DESC,
    x.dept_name ASC,
    CASE x.appr_grade
        WHEN 'S' THEN 1
        WHEN 'A' THEN 2
        WHEN 'B' THEN 3
        WHEN 'C' THEN 4
        WHEN 'D' THEN 5
        ELSE 6
    END ASC
```

**Run #2**
```sql
SELECT
  t.dept,
  t.appr_grade,
  t.emp_count,
  ROUND(t.emp_count * 100.0 / NULLIF(SUM(t.emp_count) OVER (PARTITION BY t.dept), 0), 1) AS percentage
FROM (
  SELECT
    NVL(f.EMP_ORG_NM, e.DEPARTMENT) AS dept,
    f.APPR_GRADE AS appr_grade,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
  FROM v_ai_employee e
  LEFT JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND f.APPR_GRADE IS NOT NULL
  GROUP BY
    NVL(f.EMP_ORG_NM, e.DEPARTMENT),
    f.APPR_GRADE
) t
ORDER BY
  t.emp_count DESC,
  CASE t.appr_grade
    WHEN 'S' THEN 1
    WHEN 'A' THEN 2
    WHEN 'B' THEN 3
    WHEN 'C' THEN 4
    WHEN 'D' THEN 5
    ELSE 6
  END DESC
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
SELECT EMP_NAME, DEPARTMENT, POSITION
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
  NVL(DEPARTMENT, '미정') AS department,
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 50
GROUP BY NVL(DEPARTMENT, '미정')
ORDER BY employee_count DESC, department ASC
```

**Run #2**
```sql
SELECT
    department,
    COUNT(DISTINCT emp_id) AS employee_count
FROM v_ai_employee
WHERE work_status = '재직'
  AND birth_date IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, birth_date) / 12) >= 50
GROUP BY department
ORDER BY employee_count DESC, department ASC
```

---

## X13 [PASS-INCONSISTENT] **불일치**
**부서별 자격증 보유율을 계산해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS total_employee_count,
  COUNT(DISTINCT CASE
    WHEN EXISTS (
      SELECT 1
      FROM v_ai_license l
      WHERE l.EMP_ID = e.EMP_ID
    )
    THEN e.EMP_ID
  END) AS license_holder_count,
  ROUND(
    (COUNT(DISTINCT CASE
      WHEN EXISTS (
        SELECT 1
        FROM v_ai_license l
        WHERE l.EMP_ID = e.EMP_ID
      )
      THEN e.EMP_ID
    END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100,
    2
  ) AS license_holding_rate_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY license_holding_rate_pct DESC, license_holder_count DESC, e.DEPARTMENT DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT e.EMP_ID) AS total_employee_cnt,
  COUNT(DISTINCT CASE WHEN l.EMP_ID IS NOT NULL THEN e.EMP_ID END) AS license_holder_cnt,
  ROUND(
    (COUNT(DISTINCT CASE WHEN l.EMP_ID IS NOT NULL THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100,
    2
  ) AS license_holder_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY license_holder_rate_pct DESC, license_holder_cnt DESC
```

---

## X14 [PASS-INCONSISTENT] **불일치**
**연도별 부서별 승진자 수 추이를 보여줘**

**Run #1**
```sql
SELECT
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS YEAR,
  e.DEPARTMENT AS DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS PROMOTION_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
 AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
 AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
WHERE e.WORK_STATUS = '재직'
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  e.DEPARTMENT
HAVING COUNT(DISTINCT e.EMP_ID) > 0
ORDER BY
  PROMOTION_COUNT DESC,
  YEAR DESC,
  DEPARTMENT
```

**Run #2**
```sql
SELECT
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS YEAR,
  h.ASSIGNMENT_DEPARTMENT_ID AS DEPARTMENT_ID,
  NVL(e.DEPARTMENT, '미상') AS DEPARTMENT_NAME,
  COUNT(DISTINCT e.EMP_ID) AS PROMOTION_COUNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  h.ASSIGNMENT_DEPARTMENT_ID,
  NVL(e.DEPARTMENT, '미상')
ORDER BY
  PROMOTION_COUNT DESC,
  YEAR DESC,
  DEPARTMENT_ID ASC
```

---

## X15 [WARN-EMPTY] **불일치**
**장애인 가족이 있는 재직자의 부서별 분포를 알려줘**

**Run #1**
```sql
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS disabled_family_emp_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
 AND f.DISABILITY_STATUS = '장애있음'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY disabled_family_emp_count DESC
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
ORDER BY emp_count DESC, e.DEPARTMENT
```

---

