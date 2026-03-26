# SQL 비교 로그 (실시간)

> 시작: 2026-03-23 15:14:49
> 반복횟수: 2회

## S01 [FAIL-EXEC] 일치
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
ORDER BY GENDER DESC
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
ORDER BY emp_count DESC, GENDER
```

---

## S04 [PASS-INCONSISTENT] **불일치**
**2017년에 입사한 직원 수는?**

**Run #1**
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(hire_date, 'YYYY') = '2017'
```

**Run #2**
```sql
SELECT COUNT(*) AS hired_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2017'
```

---

## S05 [PASS] 일치
**부서별 직원 수를 알려줘**

**Run #1**
```sql
SELECT
  e.department,
  COUNT(DISTINCT e.emp_id) AS emp_count
FROM v_ai_employee e
WHERE e.work_status = '재직'
GROUP BY e.department
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
    COUNT(DISTINCT e.EMP_ID) AS active_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY
    TO_NUMBER(REGEXP_REPLACE(NVL(e.GRADE, '0'), '[^0-9]', '')) DESC
```

**Run #2**
```sql
SELECT
    NVL(GRADE, '미지정') AS grade,
    COUNT(DISTINCT EMP_ID) AS active_employee_count
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

---

## S07 [PASS-INCONSISTENT] **불일치**
**정규직 직원은 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS 정규직_인원수
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '정규직'
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS 정규직_직원_수
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
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT,
  e.HIRE_DATE,
  e.CAREER_YEARS,
  e.CAREER_MONTHS,
  e.GENDER,
  e.GRADE,
  e.WORK_STATUS
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE = '기간제'
ORDER BY NVL(e.CAREER_YEARS, 0) DESC, e.EMP_ID DESC
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
  AND e.EMP_TYPE = '기간제'
ORDER BY e.EMP_ID DESC
```

---

## S09 [PASS-INCONSISTENT] **불일치**
**2020년에 입사한 직원 이름과 부서를 알려줘**

**Run #1**
```sql
SELECT
  emp_name,
  department
FROM v_ai_employee
WHERE TO_CHAR(hire_date, 'YYYY') = '2020'
ORDER BY
  hire_date DESC,
  emp_id DESC
```

**Run #2**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = '2020'
ORDER BY e.DEPARTMENT DESC, e.EMP_NAME DESC
```

---

## S10 [PASS] 일치
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
SELECT COUNT(DISTINCT EMP_ID) AS active_count
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
  AND CAREER_YEARS >= 10
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
  COUNT(*) AS employee_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND BIRTH_DATE IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS employee_count_40s
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
    e.DUTY,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DUTY
ORDER BY emp_count DESC, e.DUTY ASC
```

**Run #2**
```sql
SELECT
  DUTY,
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DUTY
ORDER BY
  CASE DUTY
    WHEN '대표이사' THEN 1
    WHEN '회장' THEN 2
    WHEN '부회장' THEN 3
    WHEN '사장' THEN 4
    WHEN '팀장' THEN 5
    WHEN '팀원' THEN 6
    WHEN '임원' THEN 7
    ELSE 99
  END,
  NVL(DUTY, ' ') DESC,
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
SELECT COUNT(*) AS emp_count
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

## S16 [PASS] 일치
**군필자 수는 몇 명이야?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS 군필자_수
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
SELECT COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_reward
WHERE REWARD_TYPE = '포상'
  AND REWARD_YEAR = '2017'
ORDER BY emp_count DESC
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_reward
WHERE REWARD_YEAR = '2017'
```

---

## S18 [PASS-INCONSISTENT] **불일치**
**2018년 기준 잔여연차가 0인 직원 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS 직원수
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = '2018'
  AND d.REMAINING_LEAVE_DAYS = 0
```

**Run #2**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS CNT_EMPLOYEE
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = '2018'
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) = 0
```

---

## S19 [PASS-INCONSISTENT] **불일치**
**2017년 교육을 수료한 건수는?**

**Run #1**
```sql
SELECT COUNT(*) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.TRAINING_YEAR = '2017'
  AND t.COMPLETION_STATUS = '수료'
```

**Run #2**
```sql
SELECT COUNT(*) AS completed_count
FROM v_ai_training t
INNER JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.TRAINING_YEAR = '2017'
  AND t.COMPLETION_STATUS = '수료'
```

---

## S20 [PASS] 일치
**S등급을 받은 건수는 총 몇 건이야?**

**Run #1**
```sql
SELECT COUNT(*) AS s_grade_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
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
  NVL(DEPARTMENT, '미지정') AS DEPARTMENT,
  AVG(NVL(CAREER_YEARS, 0)) AS AVG_CAREER_YEARS
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY NVL(DEPARTMENT, '미지정')
ORDER BY AVG(NVL(CAREER_YEARS, 0)) DESC
```

**Run #2**
```sql
SELECT
  e.department,
  AVG(NVL(e.career_years, 0)) AS avg_career_years
FROM v_ai_employee e
WHERE e.work_status = '재직'
GROUP BY e.department
ORDER BY e.department, avg_career_years DESC
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
ORDER BY year_val DESC
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
  TO_CHAR(retire_date, 'YYYY') AS year_val,
  COUNT(DISTINCT emp_id) AS retire_count
FROM v_ai_employee
WHERE retire_date IS NOT NULL
GROUP BY TO_CHAR(retire_date, 'YYYY')
ORDER BY year_val DESC
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
  ROUND(emp_count * 100.0 / SUM(emp_count) OVER (PARTITION BY grade), 1) AS gender_ratio_pct
FROM (
  SELECT
    NVL(GRADE, '(미지정)') AS grade,
    NVL(GENDER, '(미지정)') AS gender,
    COUNT(DISTINCT EMP_ID) AS emp_count
  FROM v_ai_employee
  WHERE WORK_STATUS = '재직'
  GROUP BY
    NVL(GRADE, '(미지정)'),
    NVL(GENDER, '(미지정)')
) a
ORDER BY emp_count DESC, grade, gender
```

**Run #2**
```sql
SELECT
  e.GRADE,
  e.GENDER,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(
    COUNT(DISTINCT e.EMP_ID) * 100.0
    / NULLIF(SUM(COUNT(DISTINCT e.EMP_ID)) OVER (PARTITION BY e.GRADE), 0),
    1
  ) AS percentage
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE, e.GENDER
ORDER BY emp_count DESC, e.GRADE, e.GENDER
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
ORDER BY
  CASE age_group
    WHEN '20대' THEN 1
    WHEN '30대' THEN 2
    WHEN '40대' THEN 3
    WHEN '50대' THEN 4
    WHEN '60대 이상' THEN 5
    ELSE 6
  END
```

**Run #2**
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
ORDER BY
    employee_count DESC,
    CASE age_group
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
  COUNT(DISTINCT emp_id) AS employee_count
FROM (
  SELECT
    EMP_ID AS emp_id,
    CASE
      WHEN CAREER_YEARS < 1 THEN '1년 미만'
      WHEN CAREER_YEARS >= 1 AND CAREER_YEARS < 3 THEN '1~3년'
      WHEN CAREER_YEARS >= 3 AND CAREER_YEARS < 5 THEN '3~5년'
      WHEN CAREER_YEARS >= 5 AND CAREER_YEARS < 10 THEN '5~10년'
      WHEN CAREER_YEARS >= 10 THEN '10년 이상'
    END AS tenure_group
  FROM v_ai_employee
  WHERE WORK_STATUS = '재직'
) x
GROUP BY
  tenure_group
ORDER BY
  CASE tenure_group
    WHEN '1년 미만' THEN 1
    WHEN '1~3년' THEN 2
    WHEN '3~5년' THEN 3
    WHEN '5~10년' THEN 4
    WHEN '10년 이상' THEN 5
  END
```

**Run #2**
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
        CASE
            WHEN e.CAREER_YEARS < 1 THEN 1
            WHEN e.CAREER_YEARS >= 1 AND e.CAREER_YEARS < 3 THEN 2
            WHEN e.CAREER_YEARS >= 3 AND e.CAREER_YEARS < 5 THEN 3
            WHEN e.CAREER_YEARS >= 5 AND e.CAREER_YEARS < 10 THEN 4
            WHEN e.CAREER_YEARS >= 10 THEN 5
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
ORDER BY sort_key DESC
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
  COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_employee
GROUP BY HIRE_TYPE
ORDER BY emp_count DESC, HIRE_TYPE ASC
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
  hire_date
FROM (
  SELECT
    e.department,
    e.emp_id,
    e.emp_name,
    e.hire_date,
    ROW_NUMBER() OVER (
      PARTITION BY e.department
      ORDER BY e.hire_date DESC
    ) AS rn
  FROM v_ai_employee e
  WHERE e.work_status = '재직'
)
WHERE rn = 1
ORDER BY hire_date DESC NULLS LAST
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
) x
WHERE x.rn = 1
ORDER BY x.hire_date DESC, x.department ASC, x.emp_id DESC
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
  r.PAYMENT_TYPE_NAME,
  SUM(NVL(r.GROSS_PAY_AMOUNT, 0)) AS TOTAL_GROSS_PAY_AMOUNT
FROM v_ai_pay_report r
GROUP BY
  r.PAYMENT_TYPE_NAME
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
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IS NOT NULL
GROUP BY f.APPR_GRADE
ORDER BY emp_count DESC, f.APPR_GRADE
```

**Run #2**
```sql
SELECT
  f.APPR_GRADE AS appr_grade,
  COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IS NOT NULL
GROUP BY f.APPR_GRADE
ORDER BY emp_count DESC, appr_grade DESC
```

---

## S32 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수를 알려줘**

**Run #1**
```sql
SELECT
  t.TRAINING_TYPE,
  COUNT(*) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
 AND e.WORK_STATUS = '재직'
 AND t.COMPLETION_STATUS = '수료'
GROUP BY
  t.TRAINING_TYPE
ORDER BY
  completed_count DESC
```

**Run #2**
```sql
SELECT
    t.TRAINING_TYPE,
    COUNT(*) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
    ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND t.COMPLETION_STATUS = '수료'
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
JOIN v_ai_employee e
  ON e.EMP_ID = h.EMP_ID
 AND e.WORK_STATUS = '재직'
GROUP BY
  h.ASSIGNMENT_TYPE_CODE
ORDER BY
  total_count DESC,
  h.ASSIGNMENT_TYPE_CODE DESC
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
  remaining_leave_days
FROM (
  SELECT
    e.emp_id,
    e.emp_name,
    e.department,
    NVL(r.remaining_leave_days, 0) AS remaining_leave_days,
    ROW_NUMBER() OVER (
      ORDER BY NVL(r.remaining_leave_days, 0) DESC, r.leave_accrual_id
    ) AS rn
  FROM v_ai_dtm_yy_rest r
  INNER JOIN v_ai_employee e
    ON r.emp_id = e.emp_id
  WHERE r.reference_year = '2018'
    AND e.work_status = '재직'
)
WHERE rn <= 10
ORDER BY remaining_leave_days DESC, emp_id ASC
```

**Run #2**
```sql
SELECT emp_id,
       emp_name,
       position,
       remaining_days
FROM (
    SELECT emp_id,
           emp_name,
           position,
           remaining_days,
           ROW_NUMBER() OVER (ORDER BY remaining_days DESC, emp_id) AS rn
    FROM (
        SELECT e.emp_id,
               e.emp_name,
               e.position,
               SUM(NVL(r.remaining_leave_days, 0)) AS remaining_days
        FROM v_ai_employee e
        LEFT JOIN v_ai_dtm_yy_rest r
            ON e.emp_id = r.emp_id
           AND r.reference_year = '2018'
        WHERE e.work_status = '재직'
        GROUP BY e.emp_id, e.emp_name, e.position
    )
)
WHERE rn <= 10
ORDER BY remaining_days DESC, emp_id
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
GROUP BY r.REWARD_YEAR
ORDER BY r.REWARD_YEAR DESC
```

**Run #2**
```sql
SELECT
  r.REWARD_YEAR,
  COUNT(*) AS reward_count,
  COUNT(DISTINCT r.EMP_ID) AS emp_count
FROM v_ai_reward r
WHERE r.REWARD_TYPE = '포상'
GROUP BY r.REWARD_YEAR
ORDER BY TO_NUMBER(r.REWARD_YEAR) DESC NULLS LAST
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
```

**Run #2**
```sql
SELECT COUNT(*) AS emp_count
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
  e.EMP_NAME_ENG,
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
  e.EMP_NAME_ENG,
  e.DEPARTMENT,
  e.POSITION
HAVING COUNT(*) >= 3
ORDER BY career_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       COUNT(DISTINCT c.CAREER_START_DATE) AS career_count
FROM v_ai_employee e
JOIN v_ai_career c
  ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
HAVING COUNT(DISTINCT c.CAREER_START_DATE) >= 3
ORDER BY career_count DESC
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
       e.POSITION,
       e.DEPARTMENT,
       s.SCHOOL_NAME,
       s.MAJOR_NAME,
       s.DOUBLE_MAJOR_NAME
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY e.CAREER_YEARS DESC, e.HIRE_DATE DESC, e.EMP_ID DESC
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
  s.MAJOR_NAME,
  s.SCHOOL_NAME,
  s.EDUCATION_LEVEL,
  s.GRADUATION_STATUS,
  s.ADMISSION_DATE,
  s.GRADUATION_DATE
FROM v_ai_employee e
JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND s.MAJOR_NAME LIKE '%' || '컴퓨터공학' || '%'
ORDER BY e.EMP_ID DESC
FETCH FIRST 20 ROWS ONLY
```

---

## M07 [PASS-INCONSISTENT] **불일치**
**배우자가 있는 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS married_emp_count
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
  e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.RELATION = '자녀'
GROUP BY
  e.EMP_ID, e.EMP_NAME, e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC, e.EMP_ID DESC
```

---

## M09 [PASS-INCONSISTENT] **불일치**
**토익 800점 이상 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS toeic_800_or_more_count
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
SELECT COUNT(DISTINCT e.EMP_ID) AS toeic_800_or_more_employee_count
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

## M11 [PASS] 일치
**자격증 보유 재직자 수는?**

**Run #1**
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS license_emp_count
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
SELECT COUNT(DISTINCT e.EMP_ID) AS license_emp_count
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
       e.DEPARTMENT,
       e.POSITION,
       COUNT(*) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY license_count DESC
```

**Run #2**
```sql
SELECT e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       COUNT(*) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY license_count DESC
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
ORDER BY emp_count DESC, e.DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미등록') AS department,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
GROUP BY NVL(e.DEPARTMENT, '미등록')
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
  e.DEPARTMENT,
  e.POSITION,
  e.DUTY
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
  e.COMPANY_CODE,
  e.POSITION,
  e.DEPARTMENT
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

## M15 [PASS-INCONSISTENT] **불일치**
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
SELECT COUNT(DISTINCT e.EMP_ID) AS trained_completed_emp_count
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
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_hours_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_hours_per_person DESC, emp_count DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_hours_per_person
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
 AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_hours_per_person DESC NULLS LAST
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
  e.POSITION,
  f.APPR_NM AS RECENT_APPR_NM,
  f.APPR_TYPE_CD AS RECENT_PEE_TYPE_CD,
  f.APPR_GRADE AS RECENT_APPR_GRADE,
  f.APPR_SCORE AS RECENT_APPR_SCORE,
  f.APPR_YMD AS RECENT_APPR_YMD
FROM v_ai_employee e
JOIN (
  SELECT
    fb.EMP_ID,
    fb.APPR_NM,
    fb.PEE_TYPE_CD AS APPR_TYPE_CD,
    fb.APPR_GRADE,
    fb.APPR_SCORE,
    fb.APPR_YMD,
    ROW_NUMBER() OVER (
      PARTITION BY fb.EMP_ID
      ORDER BY fb.APPR_YMD DESC, fb.END_YMD DESC, fb.APPR_ID DESC
    ) AS RN
  FROM v_ai_feedback fb
  WHERE fb.APPR_GRADE = 'S'
) f
  ON e.EMP_ID = f.EMP_ID
 AND f.RN = 1
WHERE e.WORK_STATUS = '재직'
ORDER BY NVL(f.APPR_SCORE, 0) DESC, e.EMP_ID DESC
```

**Run #2**
```sql
WITH latest_feedback AS (
  SELECT
      f.EMP_ID,
      f.APPR_NM,
      f.PEE_TYPE_NM,
      f.APPR_SCORE,
      f.APPR_GRADE,
      f.APPR_YMD,
      f.END_YMD,
      ROW_NUMBER() OVER (
        PARTITION BY f.EMP_ID
        ORDER BY f.END_YMD DESC, f.APPR_YMD DESC, f.APPR_ID DESC
      ) AS rn
  FROM v_ai_feedback f
  WHERE f.APPR_GRADE = 'S'
)
SELECT
    e.EMP_ID,
    e.EMP_NAME,
    e.EMP_NAME_ENG,
    e.COMPANY_CODE,
    e.DEPARTMENT,
    e.POSITION,
    lf.APPR_NM,
    lf.PEE_TYPE_NM,
    lf.APPR_SCORE,
    lf.APPR_GRADE,
    lf.APPR_YMD,
    lf.END_YMD
FROM latest_feedback lf
JOIN v_ai_employee e
  ON e.EMP_ID = lf.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND lf.rn = 1
ORDER BY lf.APPR_SCORE DESC NULLS LAST, lf.END_YMD DESC, lf.APPR_YMD DESC, e.EMP_ID DESC
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
  AND f.APPR_SCORE > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC
```

**Run #2**
```sql
SELECT e.DEPARTMENT,
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
SELECT COUNT(DISTINCT e.EMP_ID) AS PROMOTED_EMP_COUNT
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
      AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
      AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
      AND h.ASSIGNMENT_DATE >= ADD_MONTHS(SYSDATE, -120)
      AND h.ASSIGNMENT_DATE <= SYSDATE
  )
```

---

## M20 [PASS-INCONSISTENT] **불일치**
**현재 휴직 중인 직원 목록을 보여줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.EMP_NAME_ENG,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  e.DUTY,
  e.HIRE_DATE,
  h.ASSIGNMENT_TYPE_CODE,
  h.ASSIGNMENT_REASON_CODE,
  h.ASSIGNMENT_START_DATE,
  h.ASSIGNMENT_END_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.LEAVE_OF_ABSENCE_YN = 'Y'
  AND h.ASSIGNMENT_START_DATE = (
    SELECT MAX(h2.ASSIGNMENT_START_DATE)
    FROM v_ai_history h2
    WHERE h2.EMP_ID = e.EMP_ID
      AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
  )
ORDER BY h.ASSIGNMENT_START_DATE DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       h.ASSIGNMENT_TYPE_CODE,
       h.ASSIGNMENT_REASON_CODE,
       h.ASSIGNMENT_START_DATE
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.LEAVE_OF_ABSENCE_YN = 'Y'
  AND h.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = e.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
  )
ORDER BY h.ASSIGNMENT_START_DATE DESC
```

---

## M21 [PASS-INCONSISTENT] **불일치**
**부서별 월평균 실수령액을 보여줘**

**Run #1**
```sql
WITH dept AS (
    SELECT DISTINCT e.DEPARTMENT
    FROM v_ai_employee e
    WHERE e.WORK_STATUS = '재직'
),
monthly AS (
    SELECT e.DEPARTMENT,
           p.PAY_YEAR_MONTH,
           SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS monthly_net_pay
    FROM v_ai_employee e
    JOIN v_ai_pay_report p
        ON p.EMP_ID = e.EMP_ID
        AND p.PAYMENT_TYPE_NAME = '정기급여'
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.DEPARTMENT, p.PAY_YEAR_MONTH
)
SELECT d.DEPARTMENT,
       ROUND(AVG(m.monthly_net_pay)) AS avg_monthly_net_pay
FROM dept d
LEFT JOIN monthly m
    ON m.DEPARTMENT = d.DEPARTMENT
GROUP BY d.DEPARTMENT
ORDER BY avg_monthly_net_pay DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  p.PAY_YEAR_MONTH,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(NVL(p.NET_PAY_AMOUNT, 0))) AS avg_net_pay_amount
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
  AND p.PAYMENT_TYPE_NAME = '정기급여'
WHERE e.WORK_STATUS = '재직'
GROUP BY
  e.DEPARTMENT,
  p.PAY_YEAR_MONTH
ORDER BY
  avg_net_pay_amount DESC
```

---

## M22 [PASS-INCONSISTENT] **불일치**
**직급별 평균 총지급액을 알려줘**

**Run #1**
```sql
SELECT
  JOB_GRADE_NAME AS JOB_GRADE,
  COUNT(DISTINCT EMP_ID) AS EMP_COUNT,
  ROUND(AVG(NVL(GROSS_PAY_AMOUNT, 0))) AS AVG_TOTAL_PAID_AMOUNT
FROM v_ai_pay_report
GROUP BY JOB_GRADE_NAME
ORDER BY AVG(NVL(GROSS_PAY_AMOUNT, 0)) DESC NULLS LAST
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미지정') AS JOB_GRADE_NAME,
  ROUND(AVG(NVL(p.GROSS_PAY_AMOUNT, 0))) AS AVG_GROSS_PAY_AMOUNT,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, '미지정')
ORDER BY AVG(NVL(p.GROSS_PAY_AMOUNT, 0)) DESC, JOB_GRADE_NAME DESC
```

---

## M23 [PASS-INCONSISTENT] **불일치**
**부서별 평균 연차 사용률을 알려줘**

**Run #1**
```sql
SELECT
    e.DEPARTMENT,
    COUNT(DISTINCT e.EMP_ID) AS emp_count,
    ROUND(AVG(
        CASE
            WHEN NVL(d.TOTAL_LEAVE_DAYS, 0) > 0
            THEN NVL(d.USED_LEAVE_DAYS_PAST, 0) * 100.0 / NVL(d.TOTAL_LEAVE_DAYS, 0)
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
SELECT
    e.DEPARTMENT,
    COUNT(DISTINCT e.EMP_ID) AS emp_count,
    ROUND(
        AVG(NVL(u.usage_rate, 0)),
        2
    ) AS avg_usage_rate
FROM v_ai_employee e
LEFT JOIN (
    SELECT
        d.EMP_ID,
        CASE
            WHEN SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) > 0
            THEN SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) * 100.0 / SUM(NVL(d.TOTAL_LEAVE_DAYS, 0))
            ELSE 0
        END AS usage_rate
    FROM v_ai_dtm_yy_rest d
    GROUP BY d.EMP_ID
) u
    ON e.EMP_ID = u.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_usage_rate DESC
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
       d.REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d
  ON e.EMP_ID = d.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND d.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND NVL(d.REMAINING_LEAVE_DAYS, 0) >= 10
ORDER BY NVL(d.REMAINING_LEAVE_DAYS, 0) DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION,
       d.REFERENCE_YEAR,
       NVL(d.TOTAL_LEAVE_DAYS, 0) AS TOTAL_LEAVE_DAYS,
       NVL(d.USED_LEAVE_DAYS_PAST, 0) AS USED_LEAVE_DAYS_PAST,
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
GROUP BY
    NVL(m.MILITARY_TYPE, '미상')
ORDER BY
    emp_count DESC
```

**Run #2**
```sql
SELECT
    NVL(m.MILITARY_TYPE, '미등록') AS military_type,
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
SELECT
    p.ORGANIZATION_NAME AS DEPARTMENT_NAME,
    SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS BONUS_TOTAL_AMT,
    COUNT(DISTINCT p.EMP_ID) AS EMP_COUNT
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
    ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME LIKE '%상여%'
GROUP BY p.ORGANIZATION_NAME
ORDER BY BONUS_TOTAL_AMT DESC
```

**Run #2**
```sql
SELECT
  p.ORGANIZATION_ID,
  NVL(p.ORGANIZATION_NAME, '미등록') AS ORGANIZATION_NAME,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS TOTAL_BONUS_GROSS_AMOUNT,
  SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS TOTAL_BONUS_NET_AMOUNT
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
 AND e.WORK_STATUS = '재직'
WHERE p.PAYMENT_TYPE_NAME LIKE '%상여%'
GROUP BY
  p.ORGANIZATION_ID,
  NVL(p.ORGANIZATION_NAME, '미등록')
ORDER BY
  TOTAL_BONUS_GROSS_AMOUNT DESC
```

---

## M27 [PASS-INCONSISTENT] **불일치**
**교육 유형별 수료 건수 부서별 분포를 보여줘**

**Run #1**
```sql
SELECT NVL(t.TRAINING_TYPE, '(미정)') AS TRAINING_TYPE,
       NVL(e.DEPARTMENT, '(미배치)') AS DEPARTMENT,
       COUNT(*) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e
  ON e.EMP_ID = t.EMP_ID
 AND e.WORK_STATUS = '재직'
WHERE t.COMPLETION_STATUS = '수료'
GROUP BY NVL(t.TRAINING_TYPE, '(미정)'),
         NVL(e.DEPARTMENT, '(미배치)')
ORDER BY completed_count DESC
```

**Run #2**
```sql
SELECT
    NVL(t.TRAINING_TYPE, '미수료/미이수') AS training_type,
    NVL(e.DEPARTMENT, '미등록') AS department,
    COUNT(t.EMP_ID) AS completed_count
FROM v_ai_employee e
LEFT JOIN v_ai_training t
    ON t.EMP_ID = e.EMP_ID
   AND t.COMPLETION_STATUS = '수료'
WHERE e.WORK_STATUS = '재직'
GROUP BY
    NVL(t.TRAINING_TYPE, '미수료/미이수'),
    NVL(e.DEPARTMENT, '미등록')
HAVING COUNT(t.EMP_ID) > 0
ORDER BY completed_count DESC
```

---

## M28 [PASS-INCONSISTENT] **불일치**
**평가등급이 C 또는 D인 재직자 명단과 부서를 알려줘**

**Run #1**
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
ORDER BY e.EMP_ID DESC, f.APPR_GRADE DESC
```

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT,
  MAX(f.APPR_GRADE) AS APPR_GRADE
FROM v_ai_employee e
JOIN v_ai_feedback f
  ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.APPR_GRADE IN ('C', 'D')
GROUP BY
  e.EMP_ID,
  e.EMP_NAME,
  e.DEPARTMENT
ORDER BY e.EMP_ID DESC
```

---

## M29 [PASS-INCONSISTENT] **불일치**
**부서별 인사이동 건수를 보여줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(*) AS move_count,
  COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE = '이동'
GROUP BY e.DEPARTMENT
ORDER BY move_count DESC, emp_count DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(*) AS move_count
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
  NVL(e.DEPARTMENT, '미등록') AS DEPARTMENT,
  NVL(s.EDUCATION_LEVEL, '미등록') AS EDUCATION_LEVEL,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
LEFT JOIN v_ai_scholar s
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  NVL(e.DEPARTMENT, '미등록'),
  NVL(s.EDUCATION_LEVEL, '미등록')
ORDER BY EMP_COUNT DESC
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
SELECT e.EMP_ID,
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
  e.DEPARTMENT
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

## H03 [PASS-INCONSISTENT] **불일치**
**평가등급별 평균 급여를 보여줘**

**Run #1**
```sql
SELECT g.APPR_GRADE,
       COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
       ROUND(AVG(NVL(p.NET_PAY_AMOUNT, 0)), 2) AS AVG_NET_PAY_AMOUNT
FROM v_ai_employee e
JOIN (
    SELECT DISTINCT EMP_ID, APPR_GRADE
    FROM v_ai_feedback
    WHERE APPR_GRADE IS NOT NULL
) g
  ON e.EMP_ID = g.EMP_ID
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY g.APPR_GRADE
ORDER BY AVG_NET_PAY_AMOUNT DESC
```

**Run #2**
```sql
WITH emp_pay AS (
    SELECT
        p.EMPLOYEE_ID AS EMP_ID,
        AVG(p.NET_PAY_AMOUNT) AS AVG_NET_PAY
    FROM v_ai_pay_report p
    GROUP BY p.EMPLOYEE_ID
),
emp_grade AS (
    SELECT DISTINCT
        f.EMP_ID,
        f.APPR_GRADE
    FROM v_ai_feedback f
    WHERE f.APPR_GRADE IS NOT NULL
)
SELECT
    eg.APPR_GRADE,
    COUNT(DISTINCT eg.EMP_ID) AS EMP_COUNT,
    ROUND(AVG(ep.AVG_NET_PAY), 2) AS AVG_NET_PAY
FROM emp_grade eg
JOIN v_ai_employee e
    ON e.EMP_ID = eg.EMP_ID
   AND e.WORK_STATUS = '재직'
LEFT JOIN emp_pay ep
    ON ep.EMP_ID = eg.EMP_ID
GROUP BY eg.APPR_GRADE
ORDER BY AVG_NET_PAY DESC NULLS LAST
```

---

## H04 [PASS-INCONSISTENT] **불일치**
**동일 직급 내 남녀 평균 급여 차이를 보여줘**

**Run #1**
```sql
SELECT
  e.grade,
  AVG(CASE WHEN e.gender = '남'
           AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
           THEN TO_NUMBER(e.salary_step)
      END) AS avg_salary_male,
  AVG(CASE WHEN e.gender = '여'
           AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
           THEN TO_NUMBER(e.salary_step)
      END) AS avg_salary_female,
  ( NVL(AVG(CASE WHEN e.gender = '남'
                    AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
                    THEN TO_NUMBER(e.salary_step)
               END), 0)
  - NVL(AVG(CASE WHEN e.gender = '여'
                    AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
                    THEN TO_NUMBER(e.salary_step)
               END), 0)
  ) AS avg_salary_diff_male_minus_female
FROM v_ai_employee e
WHERE e.work_status = '재직'
GROUP BY e.grade
ORDER BY ABS(
  ( NVL(AVG(CASE WHEN e.gender = '남'
                    AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
                    THEN TO_NUMBER(e.salary_step)
               END), 0)
  - NVL(AVG(CASE WHEN e.gender = '여'
                    AND REGEXP_LIKE(e.salary_step, '^\d+(\.\d+)?$')
                    THEN TO_NUMBER(e.salary_step)
               END), 0)
  )
) DESC
```

**Run #2**
(SQL 없음)

---

## H05 [PASS-INCONSISTENT] **불일치**
**교육 미이수 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT e.EMP_ID,
       e.EMP_NAME,
       e.DEPARTMENT,
       e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND NOT EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.COMPLETION_STATUS = '수료'
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME
```

**Run #2**
```sql
SELECT e.EMP_NAME,
       e.EMP_NAME_ENG,
       e.DEPARTMENT,
       e.POSITION,
       e.COMPANY_CODE
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND NOT EXISTS (
    SELECT 1
    FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = TO_CHAR(SYSDATE, 'YYYY')
      AND t.COMPLETION_STATUS = '수료'
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME, e.EMP_ID DESC
```

---

## H06 [PASS-INCONSISTENT] **불일치**
**근속 10년 이상인데 승진 이력이 없는 재직자 목록을 알려줘**

**Run #1**
```sql
SELECT DISTINCT
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

**Run #2**
```sql
SELECT e.EMP_NAME,
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
SELECT
  d.DEPARTMENT,
  NVL(tr.avg_training_cost, 0) AS avg_training_cost,
  NVL(fb.avg_feedback_score, 0) AS avg_feedback_score
FROM (
  SELECT e.DEPARTMENT
  FROM v_ai_employee e
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.DEPARTMENT
) d
LEFT JOIN (
  SELECT
    e.DEPARTMENT,
    ROUND(AVG(t.TRAINING_COST), 2) AS avg_training_cost
  FROM v_ai_employee e
  JOIN v_ai_training t
    ON e.EMP_ID = t.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND t.TRAINING_COST IS NOT NULL
  GROUP BY e.DEPARTMENT
) tr
  ON d.DEPARTMENT = tr.DEPARTMENT
LEFT JOIN (
  SELECT
    e.DEPARTMENT,
    ROUND(AVG(f.APPR_SCORE), 2) AS avg_feedback_score
  FROM v_ai_employee e
  JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
  WHERE e.WORK_STATUS = '재직'
    AND f.APPR_SCORE > 0
  GROUP BY e.DEPARTMENT
) fb
  ON d.DEPARTMENT = fb.DEPARTMENT
ORDER BY
  NVL(tr.avg_training_cost, 0) DESC,
  NVL(fb.avg_feedback_score, 0) DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  NVL(ROUND(AVG(t.TRAINING_COST), 0), 0) AS avg_training_cost,
  NVL(ROUND(AVG(f.APPR_SCORE), 1), 0) AS avg_appr_score
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY avg_training_cost DESC, avg_appr_score DESC
```

---

## H08 [PASS-INCONSISTENT] **불일치**
**직급별 평균 실수령액과 최대 최소 급여를 알려줘**

**Run #1**
```sql
SELECT
  COALESCE(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME, '미분류') AS grade_name,
  COUNT(DISTINCT e.EMP_ID) AS emp_count,
  ROUND(AVG(NVL(p.NET_PAY_AMOUNT, 0))) AS avg_net_pay_amount,
  MAX(NVL(p.NET_PAY_AMOUNT, 0)) AS max_net_pay_amount,
  MIN(NVL(p.NET_PAY_AMOUNT, 0)) AS min_net_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND p.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY COALESCE(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME, '미분류')
ORDER BY avg_net_pay_amount DESC, max_net_pay_amount DESC
```

**Run #2**
```sql
SELECT
  NVL(p.JOB_GRADE_NAME, '미지정') AS job_grade_name,
  ROUND(AVG(p.NET_PAY_AMOUNT), 0) AS avg_net_pay_amount,
  MAX(p.NET_PAY_AMOUNT) AS max_net_pay_amount,
  MIN(p.NET_PAY_AMOUNT) AS min_net_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, '미지정')
ORDER BY avg_net_pay_amount DESC, max_net_pay_amount DESC
```

---

## H09 [PASS-INCONSISTENT] **불일치**
**부서별 퇴직률을 계산해줘**

**Run #1**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT CASE WHEN e.RETIRE_DATE IS NOT NULL THEN e.EMP_ID END) AS retire_count,
  COUNT(DISTINCT e.EMP_ID) AS total_count,
  ROUND(
    100 * COUNT(DISTINCT CASE WHEN e.RETIRE_DATE IS NOT NULL THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    2
  ) AS retire_rate_pct
FROM v_ai_employee e
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY retire_rate_pct DESC, total_count DESC, department ASC
```

**Run #2**
```sql
SELECT
  e.department AS department,
  COUNT(DISTINCT e.emp_id) AS total_employee_count,
  COUNT(DISTINCT CASE WHEN e.work_status = '퇴직' THEN e.emp_id END) AS retired_employee_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN e.work_status = '퇴직' THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0),
    4
  ) AS retirement_rate
FROM v_ai_employee e
GROUP BY e.department
ORDER BY retirement_rate DESC, retired_employee_count DESC
```

---

## H10 [PASS-INCONSISTENT] **불일치**
**고정비 대비 변동비 비율을 부서별로 분석해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT AS department_name,
  SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS fixed_pay_total,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS variable_pay_total,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) / NULLIF(SUM(NVL(p.FIXED_PAY_AMOUNT, 0)), 0) AS variable_to_fixed_ratio
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY variable_to_fixed_ratio DESC NULLS LAST, variable_pay_total DESC
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) AS FIXED_PAY_AMOUNT_SUM,
  SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) AS VARIABLE_PAY_AMOUNT_SUM,
  CASE
    WHEN SUM(NVL(p.FIXED_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE SUM(NVL(p.VARIABLE_PAY_AMOUNT, 0)) / SUM(NVL(p.FIXED_PAY_AMOUNT, 0))
  END AS VARIABLE_TO_FIXED_RATIO
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY VARIABLE_TO_FIXED_RATIO DESC, e.DEPARTMENT
```

---

## H11 [PASS-INCONSISTENT] **불일치**
**포상을 받은 직원의 평균 평가점수는?**

**Run #1**
```sql
SELECT AVG(t.emp_avg_score) AS avg_emp_appr_score
FROM (
    SELECT
        e.EMP_ID,
        AVG(f.APPR_SCORE) AS emp_avg_score
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
    GROUP BY e.EMP_ID
) t
```

**Run #2**
```sql
SELECT AVG(f.APPR_SCORE) AS avg_appr_score
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

---

## H12 [PASS-INCONSISTENT] **불일치**
**부서별 승진자 수와 승진률을 보여줘**

**Run #1**
```sql
SELECT
  t.department,
  NVL(p.promotion_cnt, 0) AS promotion_cnt,
  ROUND(
    NVL(p.promotion_cnt, 0) / NULLIF(t.total_cnt, 0) * 100,
    2
  ) AS promotion_rate_pct
FROM
  (
    SELECT
      NVL(e.department, '미지정') AS department,
      COUNT(DISTINCT e.emp_id) AS total_cnt
    FROM v_ai_employee e
    WHERE e.work_status = '재직'
    GROUP BY NVL(e.department, '미지정')
  ) t
  LEFT JOIN
  (
    SELECT
      NVL(e.department, '미지정') AS department,
      COUNT(DISTINCT h.emp_id) AS promotion_cnt
    FROM v_ai_employee e
      JOIN v_ai_history h
        ON e.emp_id = h.emp_id
    WHERE e.work_status = '재직'
      AND (
        h.assignment_type_code LIKE '%승진%'
        OR (
          h.assignment_type_code IN ('직급변경', '직책변경')
          AND h.assignment_reason_code IN ('승격', '승진')
        )
      )
    GROUP BY NVL(e.department, '미지정')
  ) p
    ON t.department = p.department
ORDER BY
  promotion_cnt DESC,
  t.total_cnt DESC
```

**Run #2**
```sql
SELECT
    e.DEPARTMENT,
    COUNT(DISTINCT e.EMP_ID) AS TOTAL_EMPLOYEE_CNT,
    NVL(COUNT(DISTINCT p.EMP_ID), 0) AS PROMOTION_EMPLOYEE_CNT,
    CASE
        WHEN COUNT(DISTINCT e.EMP_ID) = 0 THEN 0
        ELSE ROUND(NVL(COUNT(DISTINCT p.EMP_ID), 0) / COUNT(DISTINCT e.EMP_ID) * 100, 2)
    END AS PROMOTION_RATE
FROM v_ai_employee e
LEFT JOIN v_ai_history p
    ON e.EMP_ID = p.EMP_ID
   AND p.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
   AND p.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY PROMOTION_EMPLOYEE_CNT DESC, PROMOTION_RATE DESC
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
ORDER BY total_training_cost DESC
```

**Run #2**
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
ORDER BY avg_training_cost_per_person DESC, total_training_cost DESC
```

---

## H14 [PASS-INCONSISTENT] **불일치**
**직급별 평균 연차 사용률을 보여줘**

**Run #1**
```sql
SELECT t.GRADE,
       COUNT(*) AS emp_count,
       ROUND(AVG(t.EMP_USAGE_RATE), 2) AS avg_usage_rate
FROM (
    SELECT e.EMP_ID,
           e.GRADE,
           CASE
               WHEN SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) > 0
               THEN SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) * 100.0 / SUM(NVL(d.TOTAL_LEAVE_DAYS, 0))
               ELSE 0
           END AS EMP_USAGE_RATE
    FROM V_AI_EMPLOYEE e
    LEFT JOIN V_AI_DTM_YY_REST d
           ON e.EMP_ID = d.EMP_ID
    WHERE e.WORK_STATUS = '재직'
    GROUP BY e.EMP_ID, e.GRADE
) t
GROUP BY t.GRADE
ORDER BY avg_usage_rate DESC
```

**Run #2**
```sql
WITH emp_leave AS (
  SELECT
    e.EMP_ID,
    e.GRADE,
    SUM(NVL(d.TOTAL_LEAVE_DAYS, 0)) AS TOTAL_DAYS,
    SUM(NVL(d.USED_LEAVE_DAYS_PAST, 0)) AS USED_DAYS
  FROM V_AI_EMPLOYEE e
  LEFT JOIN V_AI_DTM_YY_REST d
    ON e.EMP_ID = d.EMP_ID
  WHERE e.WORK_STATUS = '재직'
  GROUP BY e.EMP_ID, e.GRADE
)
SELECT
  el.GRADE,
  COUNT(DISTINCT el.EMP_ID) AS EMP_COUNT,
  ROUND(
    AVG(
      CASE
        WHEN el.TOTAL_DAYS > 0 THEN el.USED_DAYS * 100.0 / el.TOTAL_DAYS
        ELSE 0
      END
    ),
    1
  ) AS AVG_LEAVE_USAGE_RATE
FROM emp_leave el
GROUP BY el.GRADE
ORDER BY AVG_LEAVE_USAGE_RATE DESC
```

---

## H15 [PASS-INCONSISTENT] **불일치**
**부서별 평가점수 표준편차를 계산해줘**

**Run #1**
```sql
SELECT
    NVL(f.EMP_ORG_NM, '(미지정)') AS department,
    COUNT(*) AS eval_count,
    COUNT(DISTINCT f.EMP_ID) AS emp_count,
    STDDEV(CASE WHEN NVL(f.APPR_SCORE, 0) > 0 THEN f.APPR_SCORE END) AS score_stddev
FROM v_ai_feedback f
JOIN v_ai_employee e
  ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND NVL(f.APPR_SCORE, 0) > 0
GROUP BY NVL(f.EMP_ORG_NM, '(미지정)')
ORDER BY score_stddev DESC, eval_count DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  STDDEV_SAMP(f.APPR_SCORE) AS SCORE_STDDEV
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_SCORE > 0
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY NVL(STDDEV_SAMP(f.APPR_SCORE), 0) DESC, DEPARTMENT
```

---

## H16 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 급여 총지급액 추이를 보여줘**

**Run #1**
```sql
SELECT
  p.PAY_YEAR AS pay_year,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_pay_report p
INNER JOIN v_ai_employee e
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND TO_NUMBER(p.PAY_YEAR) BETWEEN TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -108), 'YYYY')) AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
GROUP BY p.PAY_YEAR
ORDER BY total_gross_pay_amount DESC
```

**Run #2**
```sql
SELECT
  p.PAY_YEAR AS pay_year,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS total_gross_pay_amount
FROM v_ai_employee e
JOIN v_ai_pay_report p
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
    NVL(e.DEPARTMENT, '(미지정)') AS DEPARTMENT,
    e.EMP_TYPE,
    COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT,
    ROUND(
        (COUNT(DISTINCT e.EMP_ID) * 100) / NULLIF(SUM(COUNT(DISTINCT e.EMP_ID)) OVER (PARTITION BY NVL(e.DEPARTMENT, '(미지정)')), 0),
        2
    ) AS PCT_IN_DEPT,
    ROUND(
        (COUNT(DISTINCT e.EMP_ID) * 100) / NULLIF(SUM(COUNT(DISTINCT e.EMP_ID)) OVER (), 0),
        2
    ) AS PCT_OVERALL
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.EMP_TYPE IN ('정규직', '기간제')
GROUP BY
    NVL(e.DEPARTMENT, '(미지정)'),
    e.EMP_TYPE
ORDER BY
    EMP_COUNT DESC,
    DEPARTMENT ASC,
    e.EMP_TYPE ASC
```

**Run #2**
```sql
SELECT
    e.department,
    COUNT(DISTINCT e.emp_id) AS total_emp_count,
    COUNT(DISTINCT CASE WHEN e.emp_type = '정규직' THEN e.emp_id END) AS regular_emp_count,
    ROUND(
        (COUNT(DISTINCT CASE WHEN e.emp_type = '정규직' THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0)) * 100,
        2
    ) AS regular_emp_ratio_pct,
    COUNT(DISTINCT CASE WHEN e.emp_type = '기간제' THEN e.emp_id END) AS contract_emp_count,
    ROUND(
        (COUNT(DISTINCT CASE WHEN e.emp_type = '기간제' THEN e.emp_id END) / NULLIF(COUNT(DISTINCT e.emp_id), 0)) * 100,
        2
    ) AS contract_emp_ratio_pct
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND e.emp_type IN ('정규직', '기간제')
GROUP BY
    e.department
ORDER BY
    total_emp_count DESC,
    e.department DESC
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
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.LEAVE_OF_ABSENCE_YN = 'Y'
  AND h.ASSIGNMENT_START_DATE = (
    SELECT MAX(h2.ASSIGNMENT_START_DATE)
    FROM v_ai_history h2
    WHERE h2.EMP_ID = e.EMP_ID
      AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
  )
GROUP BY h.ASSIGNMENT_REASON_CODE
ORDER BY EMP_COUNT DESC, LEAVE_TYPE_CODE
```

**Run #2**
```sql
SELECT
  l.ASSIGNMENT_TYPE_CODE,
  l.ASSIGNMENT_REASON_CODE,
  COUNT(DISTINCT e.EMP_ID) AS EMP_COUNT
FROM v_ai_employee e
JOIN (
  SELECT h.*
  FROM v_ai_history h
  WHERE h.LEAVE_OF_ABSENCE_YN = 'Y'
    AND h.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = h.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = 'Y'
    )
) l
  ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY
  l.ASSIGNMENT_TYPE_CODE,
  l.ASSIGNMENT_REASON_CODE
ORDER BY
  COUNT(DISTINCT e.EMP_ID) DESC,
  l.ASSIGNMENT_TYPE_CODE DESC,
  l.ASSIGNMENT_REASON_CODE DESC
```

---

## H19 [PASS-INCONSISTENT] **불일치**
**평가등급이 C나 D인 직원의 근속연수 분포를 보여줘**

**Run #1**
```sql
SELECT
  NVL(e.career_years, 0) AS career_years,
  COUNT(DISTINCT e.emp_id) AS emp_count,
  ROUND(
    COUNT(DISTINCT e.emp_id) * 100.0
    / SUM(COUNT(DISTINCT e.emp_id)) OVER(),
    1
  ) AS percentage
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND EXISTS (
    SELECT 1
    FROM v_ai_feedback f
    WHERE f.emp_id = e.emp_id
      AND f.appr_grade IN ('C', 'D')
  )
GROUP BY NVL(e.career_years, 0)
ORDER BY emp_count DESC, career_years DESC
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
  NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME) AS 직급,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS 공제합계,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS 세금합계,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 지급합계,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 2)
  END AS 공제비율_PCT,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE ROUND(SUM(NVL(p.TAX_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) * 100, 2)
  END AS 세금비율_PCT
FROM v_ai_employee e
JOIN v_ai_pay_report p
  ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(p.JOB_GRADE_NAME, p.PAY_GRADE_NAME)
ORDER BY SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) DESC, 직급 DESC
```

**Run #2**
```sql
SELECT
  e.GRADE AS 직급,
  COUNT(DISTINCT e.EMP_ID) AS 인원수,
  SUM(NVL(p.DEDUCTION_AMOUNT, 0)) AS 총공제액,
  SUM(NVL(p.TAX_AMOUNT, 0)) AS 총세금액,
  SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) AS 총지급합계,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE SUM(NVL(p.DEDUCTION_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))
  END AS 공제비율,
  CASE
    WHEN SUM(NVL(p.GROSS_PAY_AMOUNT, 0)) = 0 THEN 0
    ELSE SUM(NVL(p.TAX_AMOUNT, 0)) / SUM(NVL(p.GROSS_PAY_AMOUNT, 0))
  END AS 세금비율
FROM v_ai_employee e
LEFT JOIN v_ai_pay_report p
  ON p.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.GRADE
ORDER BY 세금비율 DESC, 공제비율 DESC
```

---

## X01 [PASS-INCONSISTENT] **불일치**
**부서별 최고 급여자 이름과 급여를 알려줘**

**Run #1**
```sql
SELECT DEPARTMENT,
       EMP_NAME,
       NET_PAY_AMOUNT
FROM (
    SELECT e.DEPARTMENT,
           e.EMP_NAME,
           p.NET_PAY_AMOUNT,
           ROW_NUMBER() OVER (
               PARTITION BY e.DEPARTMENT
               ORDER BY NVL(p.NET_PAY_AMOUNT, 0) DESC, p.PAY_DATE DESC, p.PAY_DATE_ID DESC
           ) AS rn
    FROM v_ai_employee e
    INNER JOIN v_ai_pay_report p
        ON p.EMP_ID = e.EMP_ID
    WHERE e.WORK_STATUS = '재직'
) x
WHERE rn = 1
ORDER BY NVL(NET_PAY_AMOUNT, 0) DESC
```

**Run #2**
```sql
SELECT
    department,
    emp_name,
    net_pay_amount
FROM (
    SELECT
        e.department,
        e.emp_name,
        NVL(p.net_pay_amount, 0) AS net_pay_amount,
        ROW_NUMBER() OVER (
            PARTITION BY e.department
            ORDER BY NVL(p.net_pay_amount, 0) DESC, p.pay_date DESC
        ) AS rn
    FROM v_ai_employee e
    INNER JOIN v_ai_pay_report p
        ON e.emp_id = p.emp_id
    WHERE e.work_status = '재직'
)
WHERE rn = 1
ORDER BY net_pay_amount DESC
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
  e.DEPARTMENT,
  e.POSITION,
  s.s_grade_cnt
FROM (
  SELECT
    f.EMP_ID,
    COUNT(DISTINCT f.APPR_ID) AS s_grade_cnt
  FROM v_ai_feedback f
  WHERE f.APPR_GRADE = 'S'
    AND f.APPR_YMD >= ADD_MONTHS(SYSDATE, -120)
  GROUP BY f.EMP_ID
  HAVING COUNT(DISTINCT f.APPR_ID) >= 2
) s
JOIN v_ai_employee e
  ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY s.s_grade_cnt DESC, e.EMP_ID DESC
```

**Run #2**
```sql
SELECT
    e.EMP_ID,
    e.EMP_NAME,
    e.COMPANY_CODE,
    e.DEPARTMENT,
    s.s_cnt AS s_grade_count
FROM v_ai_employee e
JOIN (
    SELECT
        f.EMP_ID,
        COUNT(DISTINCT f.APPR_ID) AS s_cnt
    FROM v_ai_feedback f
    WHERE f.APPR_GRADE = 'S'
      AND f.END_YMD >= ADD_MONTHS(SYSDATE, -120)
      AND f.END_YMD <= SYSDATE
    GROUP BY f.EMP_ID
    HAVING COUNT(DISTINCT f.APPR_ID) >= 2
) s
    ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = '재직'
ORDER BY
    s.s_cnt DESC,
    e.EMP_ID DESC
```

---

## X03 [PASS-INCONSISTENT] **불일치**
**최근 10년간 연도별 입사 퇴사 추이를 보여줘**

**Run #1**
```sql
WITH x AS (
    SELECT TO_CHAR(HIRE_DATE, 'YYYY') AS year_val,
           EMP_ID,
           'HIRE' AS gubun
    FROM v_ai_employee
    WHERE HIRE_DATE IS NOT NULL
      AND TO_NUMBER(TO_CHAR(HIRE_DATE, 'YYYY')) BETWEEN
          TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY')) AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
    UNION ALL
    SELECT TO_CHAR(RETIRE_DATE, 'YYYY') AS year_val,
           EMP_ID,
           'RETIRE' AS gubun
    FROM v_ai_employee
    WHERE RETIRE_DATE IS NOT NULL
      AND TO_NUMBER(TO_CHAR(RETIRE_DATE, 'YYYY')) BETWEEN
          TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY')) AND TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY'))
)
SELECT year_val,
       SUM(CASE WHEN gubun = 'HIRE' THEN 1 ELSE 0 END) AS hire_count,
       SUM(CASE WHEN gubun = 'RETIRE' THEN 1 ELSE 0 END) AS retire_count
FROM x
GROUP BY year_val
ORDER BY year_val DESC
```

**Run #2**
```sql
WITH params AS (
  SELECT TO_NUMBER(TO_CHAR(ADD_MONTHS(SYSDATE, -120), 'YYYY')) AS start_year,
         TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY')) AS end_year
  FROM dual
)
SELECT t.year_val,
       SUM(t.hire_count) AS hire_count,
       SUM(t.retire_count) AS retire_count
FROM (
  SELECT TO_CHAR(e.hire_date, 'YYYY') AS year_val,
         COUNT(DISTINCT e.emp_id) AS hire_count,
         0 AS retire_count
  FROM v_ai_employee e
  CROSS JOIN params p
  WHERE e.hire_date IS NOT NULL
    AND TO_NUMBER(TO_CHAR(e.hire_date, 'YYYY')) BETWEEN p.start_year AND p.end_year
  GROUP BY TO_CHAR(e.hire_date, 'YYYY')
  UNION ALL
  SELECT TO_CHAR(e.retire_date, 'YYYY') AS year_val,
         0 AS hire_count,
         COUNT(DISTINCT e.emp_id) AS retire_count
  FROM v_ai_employee e
  CROSS JOIN params p
  WHERE e.retire_date IS NOT NULL
    AND TO_NUMBER(TO_CHAR(e.retire_date, 'YYYY')) BETWEEN p.start_year AND p.end_year
  GROUP BY TO_CHAR(e.retire_date, 'YYYY')
) t
GROUP BY t.year_val
ORDER BY t.year_val DESC
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

**Run #2**
```sql
SELECT
  e.EMP_ID,
  e.EMP_NAME,
  e.COMPANY_CODE,
  e.DEPARTMENT,
  e.POSITION,
  e.GRADE,
  e.DUTY,
  e.HIRE_DATE,
  e.CAREER_YEARS
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
WHERE e.WORK_STATUS = '재직'
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC, e.HIRE_DATE ASC
```

---

## X05 [PASS-INCONSISTENT] **불일치**
**부서별 교육 수료율을 계산해줘**

**Run #1**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS total_emp_count,
  COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN e.EMP_ID END) AS completed_emp_count,
  ROUND(
    (COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN e.EMP_ID END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) * 100
  , 2) AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY completed_emp_count DESC, total_emp_count DESC
```

**Run #2**
```sql
SELECT
  NVL(e.DEPARTMENT, '미지정') AS department,
  COUNT(DISTINCT e.EMP_ID) AS total_emp_count,
  COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN e.EMP_ID END) AS completed_emp_count,
  CASE
    WHEN COUNT(DISTINCT e.EMP_ID) = 0 THEN 0
    ELSE ROUND(
      (COUNT(DISTINCT CASE WHEN t.COMPLETION_STATUS = '수료' THEN e.EMP_ID END) / COUNT(DISTINCT e.EMP_ID)) * 100,
      2
    )
  END AS completion_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_training t
  ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = '재직'
GROUP BY NVL(e.DEPARTMENT, '미지정')
ORDER BY total_emp_count DESC, completion_rate_pct DESC
```

---

## X06 [PASS-INCONSISTENT] **불일치**
**직급별 평균 승진 소요연수를 알려줘**

**Run #1**
```sql
SELECT
  e.GRADE AS grade,
  ROUND(AVG(MONTHS_BETWEEN(e.GRADE_DATE, e.HIRE_DATE) / 12), 2) AS avg_promotion_years,
  COUNT(DISTINCT e.EMP_ID) AS employee_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.GRADE_DATE IS NOT NULL
  AND e.HIRE_DATE IS NOT NULL
GROUP BY
  e.GRADE
ORDER BY
  avg_promotion_years DESC,
  grade ASC
```

**Run #2**
```sql
SELECT
  e.GRADE AS grade,
  ROUND(AVG(MONTHS_BETWEEN(e.GRADE_DATE, e.HIRE_DATE) / 12), 2) AS avg_promotion_years
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.GRADE_DATE IS NOT NULL
  AND e.HIRE_DATE IS NOT NULL
GROUP BY
  e.GRADE
ORDER BY
  avg_promotion_years DESC NULLS LAST
```

---

## X07 [PASS-INCONSISTENT] **불일치**
**부서별 여성 비율을 알려줘**

**Run #1**
```sql
SELECT
  DEPARTMENT,
  COUNT(DISTINCT EMP_ID) AS total_emp_count,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_emp_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0 / NULLIF(COUNT(DISTINCT EMP_ID), 0),
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
  NVL(DEPARTMENT, '(미등록)') AS DEPARTMENT,
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS FEMALE_COUNT,
  COUNT(DISTINCT EMP_ID) AS TOTAL_COUNT,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS FEMALE_RATIO_PERCENT
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY NVL(DEPARTMENT, '(미등록)')
ORDER BY FEMALE_COUNT DESC, DEPARTMENT
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
  ) AS female_ratio_pct
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND e.POSITION IN (
    '과장', '차장', '부장', '상무', '전무', '부사장', '사장', '회장', '대표이사'
  )
```

**Run #2**
```sql
SELECT
  COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) AS female_count,
  COUNT(DISTINCT EMP_ID) AS total_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN GENDER = '여' THEN EMP_ID END) * 100.0
    / NULLIF(COUNT(DISTINCT EMP_ID), 0),
    1
  ) AS female_ratio_pct
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND POSITION IN ('과장', '차장', '부장', '이사', '전무', '부사장', '사장', '회장')
```

---

## X09 [PASS-INCONSISTENT] **불일치**
**입사 5년차 이내 직원 중 S등급을 받은 비율은?**

**Run #1**
```sql
SELECT
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN f.EMP_ID IS NOT NULL THEN e.EMP_ID END)
    / NULLIF(COUNT(DISTINCT e.EMP_ID), 0),
    1
  ) AS s_grade_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.EMP_ID = f.EMP_ID
 AND f.APPR_GRADE = 'S'
WHERE e.WORK_STATUS = '재직'
  AND e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
```

**Run #2**
```sql
SELECT
  ROUND(
    100 * (
      SELECT COUNT(DISTINCT e.EMP_ID)
      FROM v_ai_employee e
      WHERE e.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)
        AND EXISTS (
          SELECT 1
          FROM v_ai_feedback f
          WHERE f.EMP_ID = e.EMP_ID
            AND f.APPR_GRADE = 'S'
            AND NVL(f.APPR_SCORE, 0) > 0
        )
    ) / NULLIF(
      (SELECT COUNT(DISTINCT e2.EMP_ID)
       FROM v_ai_employee e2
       WHERE e2.HIRE_DATE >= ADD_MONTHS(SYSDATE, -60)),
      0
    ),
    2
  ) AS s_grade_ratio_pct
FROM DUAL
```

---

## X10 [PASS-INCONSISTENT] **불일치**
**부서별 평가등급 분포를 보여줘**

**Run #1**
```sql
SELECT
  dept_name,
  appr_grade,
  emp_count,
  ROUND(emp_count * 100.0 / SUM(emp_count) OVER (PARTITION BY dept_name), 1) AS percentage
FROM (
  SELECT
    NVL(f.EMP_ORG_NM, '미평가부서') AS dept_name,
    NVL(f.APPR_GRADE, '미평가') AS appr_grade,
    COUNT(DISTINCT e.EMP_ID) AS emp_count
  FROM v_ai_employee e
  LEFT JOIN v_ai_feedback f
    ON e.EMP_ID = f.EMP_ID
    AND f.APPR_GRADE IS NOT NULL
  WHERE e.WORK_STATUS = '재직'
  GROUP BY
    NVL(f.EMP_ORG_NM, '미평가부서'),
    NVL(f.APPR_GRADE, '미평가')
) x
ORDER BY emp_count DESC, dept_name, appr_grade
```

**Run #2**
```sql
SELECT
  e.department,
  f.appr_grade,
  COUNT(DISTINCT f.emp_id) AS emp_count,
  ROUND(
    COUNT(DISTINCT f.emp_id) * 100.0
    / NULLIF(SUM(COUNT(DISTINCT f.emp_id)) OVER (PARTITION BY e.department), 0),
    1
  ) AS percentage
FROM v_ai_employee e
LEFT JOIN v_ai_feedback f
  ON e.emp_id = f.emp_id
  AND f.appr_grade IS NOT NULL
WHERE e.work_status = '재직'
GROUP BY
  e.department,
  f.appr_grade
HAVING f.appr_grade IS NOT NULL
ORDER BY
  emp_count DESC,
  CASE f.appr_grade
    WHEN 'S' THEN 1
    WHEN 'A' THEN 2
    WHEN 'B' THEN 3
    WHEN 'C' THEN 4
    WHEN 'D' THEN 5
    ELSE 6
  END ASC
```

---

## X11 [PASS-INCONSISTENT] **불일치**
**최근 입사자 5명의 이름 부서 직급을 알려줘**

**Run #1**
```sql
SELECT
  e.EMP_NAME,
  e.DEPARTMENT,
  e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
ORDER BY e.HIRE_DATE DESC
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
GROUP BY
    e.department
ORDER BY
    employee_count DESC,
    e.department ASC
```

**Run #2**
```sql
SELECT
  e.department,
  COUNT(DISTINCT e.emp_id) AS employee_count
FROM v_ai_employee e
WHERE e.work_status = '재직'
  AND e.birth_date IS NOT NULL
  AND TRUNC(MONTHS_BETWEEN(SYSDATE, e.birth_date) / 12) >= 50
GROUP BY e.department
ORDER BY employee_count DESC, e.department
```

---

## X13 [PASS-INCONSISTENT] **불일치**
**부서별 자격증 보유율을 계산해줘**

**Run #1**
```sql
SELECT
    e.department AS department,
    COUNT(DISTINCT e.emp_id) AS total_employee_cnt,
    COUNT(DISTINCT CASE WHEN l.emp_id IS NOT NULL THEN e.emp_id END) AS licensed_employee_cnt,
    ROUND(
        COUNT(DISTINCT CASE WHEN l.emp_id IS NOT NULL THEN e.emp_id END)
        / COUNT(DISTINCT e.emp_id) * 100
    , 2) AS license_holding_rate_pct
FROM v_ai_employee e
LEFT JOIN v_ai_license l
    ON e.emp_id = l.emp_id
WHERE e.work_status = '재직'
GROUP BY e.department
ORDER BY license_holding_rate_pct DESC, licensed_employee_cnt DESC, e.department
```

**Run #2**
```sql
SELECT
  e.DEPARTMENT,
  COUNT(DISTINCT e.EMP_ID) AS total_employee_cnt,
  COUNT(DISTINCT CASE
    WHEN EXISTS (
      SELECT 1
      FROM v_ai_license l
      WHERE l.EMP_ID = e.EMP_ID
    )
    THEN e.EMP_ID
  END) AS licensed_employee_cnt,
  (COUNT(DISTINCT CASE
    WHEN EXISTS (
      SELECT 1
      FROM v_ai_license l
      WHERE l.EMP_ID = e.EMP_ID
    )
    THEN e.EMP_ID
  END) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0)) AS license_coverage_rate
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
GROUP BY e.DEPARTMENT
ORDER BY license_coverage_rate DESC, licensed_employee_cnt DESC, total_employee_cnt DESC
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
FROM V_AI_EMPLOYEE e
JOIN V_AI_HISTORY h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  e.DEPARTMENT
ORDER BY
  PROMOTION_COUNT DESC,
  YEAR ASC,
  DEPARTMENT ASC
```

**Run #2**
```sql
SELECT
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') AS YEAR,
  NVL(e.DEPARTMENT, '미지정') AS DEPARTMENT,
  COUNT(DISTINCT h.EMP_ID) AS PROMOTION_COUNT
FROM v_ai_employee e
JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')
  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')
GROUP BY
  TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY'),
  NVL(e.DEPARTMENT, '미지정')
ORDER BY
  YEAR DESC,
  DEPARTMENT DESC
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
ORDER BY emp_count DESC, e.DEPARTMENT DESC
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
      AND (f.DISABILITY_STATUS = '장애있음' OR f.DISABILITY_GRADE IS NOT NULL)
  )
GROUP BY e.DEPARTMENT
ORDER BY emp_count DESC
```

---

