# V_AI_HISTORY 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_HISTORY`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (EMPLOYEE_ID → EMP_ID로 변경 완료)

```sql
CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "V_AI_HISTORY" (
    "ASSIGNMENT_HISTORY_ID", "EMP_ID", "PERSON_ID",
    "ASSIGNMENT_APPROVAL_ID", "ASSIGNMENT_START_DATE", "ASSIGNMENT_END_DATE",
    "ASSIGNMENT_DATE", "ASSIGNMENT_SEQUENCE", "ASSIGNMENT_TYPE_CODE",
    "ASSIGNMENT_REASON_CODE", "HR_AREA", "ASSIGNMENT_DEPARTMENT_ID",
    "PAYROLL_DEPARTMENT_ID", "ATTENDANCE_DEPARTMENT_ID",
    "ASSIGNMENT_GRADE_CODE", "ASSIGNMENT_JOB_CODE", "ASSIGNMENT_TITLE_NAME",
    "IS_ORG_LEADER_YN", "LEAVE_OF_ABSENCE_YN",
    "EXPECTED_RETURN_FROM_LEAVE_DATE", "EXPECTED_CHILDBIRTH_DATE",
    "HR_REFLECTED_YN", "PRINT_YN"
) AS
SELECT
    CH.CAM_HISTORY_ID  AS assignment_history_id,
    CH.EMP_ID          AS emp_id,
    CH.PERSON_ID       AS person_id,
    CH.CAM_DOC_ID      AS assignment_approval_id,
    CH.STA_YMD         AS assignment_start_date,
    CH.END_YMD         AS assignment_end_date,
    CH.CAM_YMD         AS assignment_date,
    CH.SEQ             AS assignment_sequence,
    FC1.CD_NM          AS assignment_type_code,
    FC2.CD_NM          AS assignment_reason_code,
    FC3.CD_NM          AS hr_area,
    CH.ORG_ID          AS assignment_department_id,
    CH.PAY_ORG_ID      AS payroll_department_id,
    CH.DTM_ORG_ID      AS attendance_department_id,
    FC4.CD_NM          AS assignment_grade_code,
    FC5.CD_NM          AS assignment_job_code,
    FC6.CD_NM          AS assignment_title_name,
    CH.LEADER_YN       AS is_org_leader_yn,
    CH.REN_YN          AS leave_of_absence_yn,
    CH.REN_YMD         AS expected_return_from_leave_date,
    CH.BABY_YMD        AS expected_childbirth_date,
    CH.MAS_YN          AS hr_reflected_yn,
    CH.PRINT_YN        AS print_yn
FROM CAM_HISTORY CH
LEFT JOIN FRM_CODE FC1 ON FC1.CD = CH.TYPE_CD   AND FC1.CD_KIND = 'CAM_TYPE_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = CH.CAU_CD    AND FC2.CD_KIND = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = CH.COMPANY_CD AND FC3.CD_KIND = 'CAM_COMPANY_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = CH.POS_GRD_CD AND FC4.CD_KIND = 'PHM_POS_GRD_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = CH.JOB_CD    AND FC5.CD_KIND = 'PHM_JOB_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = CH.DUTY_CD   AND FC6.CD_KIND = 'PHM_DUTY_CD';
```

**소스**: `CAM_HISTORY` + FRM_CODE 6개 LEFT JOIN. PHM_EMP 참조 없음.
**구조**: COMPANY_CD 중복 문제 해당 없음 (PHM_EMP 미참조).
**변경**: 조인키를 `EMPLOYEE_ID` → `EMP_ID`로 통일 (다른 V_AI_* 뷰와 일관성).

---

## 2. 이슈 분석

### 2.1 table_catalog 미등재 — NL2SQL 사각지대 (확정)

**현재 `table_catalog.py`에 `v_ai_history` 항목이 없음**. schema_retrieval_node가 이 테이블을 선택할 수 없으므로, 발령/인사이동 관련 모든 질의가 실패.

**NL2SQL 영향**:

| 질의 | 현재 결과 |
|------|----------|
| "지난해 승진자 목록" | ❌ 테이블 선택 불가 |
| "부서이동 이력" | ❌ 테이블 선택 불가 |
| "휴직 중인 직원" | ❌ 테이블 선택 불가 |
| "발령 이력 조회" | ❌ 테이블 선택 불가 |

### 2.2 COMMENT 오류 — 컬럼 COMMENT 뒤바뀜 (확정)

현재 `orcl-business_view_db.sql:412-413`:

```sql
-- 현재 (오류 — 뒤바뀜)
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_TITLE_NAME IS '조직장유무';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.IS_ORG_LEADER_YN IS '발령직책';
```

DDL에서 확인:
- `ASSIGNMENT_TITLE_NAME` = `FC6.CD_NM` (PHM_DUTY_CD → 직책명) → COMMENT는 '발령직책명'이 맞음
- `IS_ORG_LEADER_YN` = `CH.LEADER_YN` (조직장 여부 Y/N) → COMMENT는 '조직장 여부'가 맞음

### 2.3 EMPLOYEE_ID → EMP_ID 변경 (완료)

기존 뷰는 조인키가 `EMPLOYEE_ID`로 되어 있어 다른 V_AI_* 뷰의 `EMP_ID`와 불일치했음.
→ **`EMP_ID`로 통일 완료**. JOIN 시 별도 컬럼명 매칭 불필요.

```sql
-- 변경 전
JOIN v_ai_history b ON a.EMP_ID = b.EMPLOYEE_ID  -- 컬럼명 불일치

-- 변경 후
JOIN v_ai_history b ON a.EMP_ID = b.EMP_ID       -- 일관성 확보
```

### 2.4 ASSIGNMENT_DEPARTMENT_ID — 부서명 없음

`CH.ORG_ID`(숫자)만 노출되고, 부서명이 없음. NL2SQL에서 "영업팀으로 발령된 직원" 같은 질의에 부서명 매칭이 불가.

**개선 검토**: ORM_ORG JOIN 추가 시 부서명 제공 가능.
```sql
-- 검토: ORM_ORG JOIN 추가
LEFT JOIN ORM_ORG OO ON OO.ORG_ID = CH.ORG_ID
-- → OO.ORG_NM AS ASSIGNMENT_DEPARTMENT_NAME 추가 가능
```

→ 단, ORM_ORG에도 STA_YMD/END_YMD 이력이 있어 곱집합 위험. DB 검증 필요.

### 2.5 NL2SQL 활용도 분석

| 컬럼 | NL2SQL 활용도 | 카탈로그 등재 | 비고 |
|------|:----------:|:----------:|------|
| EMP_ID | FK | O | 다른 뷰와 동일 조인키 |
| ASSIGNMENT_TYPE_CODE | ★높음 | O | 발령유형 (승진,전보,휴직 등) |
| ASSIGNMENT_REASON_CODE | 중간 | O | 발령사유 |
| ASSIGNMENT_DATE | ★높음 | O | 발령일자 |
| ASSIGNMENT_START_DATE | 중간 | O | 발령 시작일 |
| ASSIGNMENT_END_DATE | 중간 | O | 발령 종료일 |
| ASSIGNMENT_GRADE_CODE | 중간 | O | 발령 직급 |
| ASSIGNMENT_TITLE_NAME | 중간 | O | 발령 직책명 |
| LEAVE_OF_ABSENCE_YN | ★높음 | O | 휴직 여부 |
| ASSIGNMENT_DEPARTMENT_ID | 낮음 | **X** | 코드값 (부서명 아님) |
| HR_AREA | 낮음 | **X** | 인사영역 코드명 |
| ASSIGNMENT_HISTORY_ID | 낮음 | **X** | 내부 PK |
| PERSON_ID | 낮음 | **X** | 내부 ID |
| ASSIGNMENT_APPROVAL_ID | 낮음 | **X** | 내부 ID |
| ASSIGNMENT_SEQUENCE | 낮음 | **X** | 발령 순서 |
| PAYROLL_DEPARTMENT_ID | 낮음 | **X** | 급여부서 ID |
| ATTENDANCE_DEPARTMENT_ID | 낮음 | **X** | 근태부서 ID |
| IS_ORG_LEADER_YN | 낮음 | **X** | 조직장 여부 |
| EXPECTED_RETURN_FROM_LEAVE_DATE | 낮음 | **X** | 복직예정일 |
| EXPECTED_CHILDBIRTH_DATE | 낮음 | **X** | 출산예정일 (PII) |
| HR_REFLECTED_YN | 낮음 | **X** | 인사반영 여부 |
| PRINT_YN | 낮음 | **X** | 출력여부 |

---

## 3. 개선 사항

### 3.1 수정 SQL 전문 (개선안 — EMPLOYEE_ID → EMP_ID + COMMENT 오류 수정)

```sql
-- H552_RND.V_AI_HISTORY source (개선안 — EMP_ID 통일 + COMMENT 오류 수정)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_HISTORY" (
    "ASSIGNMENT_HISTORY_ID", "EMP_ID", "PERSON_ID",
    "ASSIGNMENT_APPROVAL_ID", "ASSIGNMENT_START_DATE", "ASSIGNMENT_END_DATE",
    "ASSIGNMENT_DATE", "ASSIGNMENT_SEQUENCE", "ASSIGNMENT_TYPE_CODE",
    "ASSIGNMENT_REASON_CODE", "HR_AREA", "ASSIGNMENT_DEPARTMENT_ID",
    "PAYROLL_DEPARTMENT_ID", "ATTENDANCE_DEPARTMENT_ID",
    "ASSIGNMENT_GRADE_CODE", "ASSIGNMENT_JOB_CODE", "ASSIGNMENT_TITLE_NAME",
    "IS_ORG_LEADER_YN", "LEAVE_OF_ABSENCE_YN",
    "EXPECTED_RETURN_FROM_LEAVE_DATE", "EXPECTED_CHILDBIRTH_DATE",
    "HR_REFLECTED_YN", "PRINT_YN"
) AS
SELECT
    CH.CAM_HISTORY_ID  AS assignment_history_id,
    -- [변경] EMPLOYEE_ID → EMP_ID (다른 V_AI_* 뷰와 조인키 통일)
    CH.EMP_ID          AS emp_id,
    CH.PERSON_ID       AS person_id,
    CH.CAM_DOC_ID      AS assignment_approval_id,
    CH.STA_YMD         AS assignment_start_date,
    CH.END_YMD         AS assignment_end_date,
    CH.CAM_YMD         AS assignment_date,
    CH.SEQ             AS assignment_sequence,
    FC1.CD_NM          AS assignment_type_code,
    FC2.CD_NM          AS assignment_reason_code,
    FC3.CD_NM          AS hr_area,
    CH.ORG_ID          AS assignment_department_id,
    CH.PAY_ORG_ID      AS payroll_department_id,
    CH.DTM_ORG_ID      AS attendance_department_id,
    FC4.CD_NM          AS assignment_grade_code,
    FC5.CD_NM          AS assignment_job_code,
    FC6.CD_NM          AS assignment_title_name,
    CH.LEADER_YN       AS is_org_leader_yn,
    CH.REN_YN          AS leave_of_absence_yn,
    CH.REN_YMD         AS expected_return_from_leave_date,
    CH.BABY_YMD        AS expected_childbirth_date,
    CH.MAS_YN          AS hr_reflected_yn,
    CH.PRINT_YN        AS print_yn
FROM CAM_HISTORY CH
LEFT JOIN FRM_CODE FC1
  ON FC1.CD = CH.TYPE_CD
 AND FC1.CD_KIND = 'CAM_TYPE_CD'
LEFT JOIN FRM_CODE FC2
  ON FC2.CD = CH.CAU_CD
 AND FC2.CD_KIND = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC3
  ON FC3.CD = CH.COMPANY_CD
 AND FC3.CD_KIND = 'CAM_COMPANY_CD'
LEFT JOIN FRM_CODE FC4
  ON FC4.CD = CH.POS_GRD_CD
 AND FC4.CD_KIND = 'PHM_POS_GRD_CD'
LEFT JOIN FRM_CODE FC5
  ON FC5.CD = CH.JOB_CD
 AND FC5.CD_KIND = 'PHM_JOB_CD'
LEFT JOIN FRM_CODE FC6
  ON FC6.CD = CH.DUTY_CD
 AND FC6.CD_KIND = 'PHM_DUTY_CD';

GRANT SELECT ON "H552_RND"."V_AI_HISTORY" TO "MUSER";
```

### 3.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **조인키 컬럼명** | `EMPLOYEE_ID` | `EMP_ID` | **핵심 변경 — 다른 V_AI_* 뷰와 통일** |
| SELECT alias | `AS employee_id` | `AS emp_id` | DDL 컬럼명과 동기화 |
| 뷰 구조 | 변경 없음 | 변경 없음 | FROM/JOIN 동일 |

### 3.3 COMMENT 보강 (COMMENT 오류 수정 포함)

```sql
COMMENT ON TABLE H552_RND.V_AI_HISTORY IS '인사발령 이력 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N — 발령 건수만큼 행 존재)';

COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_HISTORY_ID IS '발령이력ID (PK)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE.EMP_ID)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.PERSON_ID IS '개인ID';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_APPROVAL_ID IS '발령품의서ID';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_START_DATE IS '발령 시작일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_END_DATE IS '발령 종료일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_DATE IS '발령일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_SEQUENCE IS '발령순서';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_TYPE_CODE IS '발령유형 (승진,전보,전직,휴직,복직,퇴직 등)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_REASON_CODE IS '발령사유';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.HR_AREA IS '인사영역';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_DEPARTMENT_ID IS '발령부서ID (숫자, 부서명 아님)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.PAYROLL_DEPARTMENT_ID IS '급여부서ID';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ATTENDANCE_DEPARTMENT_ID IS '근태부서ID';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_GRADE_CODE IS '발령 직급 (1급~9급)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_JOB_CODE IS '발령 직무';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.ASSIGNMENT_TITLE_NAME IS '발령직책명 (팀장,팀원 등)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.IS_ORG_LEADER_YN IS '조직장 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.LEAVE_OF_ABSENCE_YN IS '휴직 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.EXPECTED_RETURN_FROM_LEAVE_DATE IS '휴직 복직예정일 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.EXPECTED_CHILDBIRTH_DATE IS '출산예정일 (DATE, PII)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.HR_REFLECTED_YN IS '인사반영 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_HISTORY.PRINT_YN IS '출력 여부 (Y/N)';
```

### 3.3 table_catalog.py 반영 코드 (신규 등재)

```python
"v_ai_history": {
    "description": "인사발령 이력 (1:N — 발령 건수만큼 행 존재, EMP_ID로 V_AI_EMPLOYEE와 JOIN)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE)",
        "ASSIGNMENT_TYPE_CODE ★발령유형 (승진,전보,전직,휴직,복직,퇴직 등)",
        "ASSIGNMENT_REASON_CODE (발령사유)",
        "ASSIGNMENT_DATE ★발령일자 (DATE)",
        "ASSIGNMENT_START_DATE (발령 시작일)",
        "ASSIGNMENT_END_DATE (발령 종료일)",
        "ASSIGNMENT_GRADE_CODE (발령 직급, 1급~9급)",
        "ASSIGNMENT_TITLE_NAME (발령 직책명, 팀장/팀원 등)",
        "LEAVE_OF_ABSENCE_YN ★휴직 여부 (Y/N)",
    ],
    "keywords": ["발령", "인사이동", "승진", "전보", "전직", "휴직", "복직", "부서이동", "인사발령", "발령이력"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 발령 건수만큼, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 3.4 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 특정 연도 승진자 목록**
```
title: 특정 연도 승진자 목록 조회
doc_type: query_example
usage_type: rag_action

content:
올해 승진자
승진한 직원 목록
:연도 승진자 수
승진 현황
- V_AI_EMPLOYEE JOIN V_AI_HISTORY
- ASSIGNMENT_TYPE_CODE LIKE '%승진%'

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION, a.GRADE,
       b.ASSIGNMENT_DATE, b.ASSIGNMENT_TYPE_CODE
FROM v_ai_employee a
JOIN v_ai_history b ON a.EMP_ID = b.EMP_ID
WHERE b.ASSIGNMENT_TYPE_CODE LIKE '%승진%'
  AND TO_CHAR(b.ASSIGNMENT_DATE, 'YYYY') = ':연도'
ORDER BY b.ASSIGNMENT_DATE DESC
```

## 핵심 패턴
- JOIN 키: a.EMP_ID = b.EMP_ID
- ASSIGNMENT_TYPE_CODE LIKE '%승진%': 승진 발령만 필터
- TO_CHAR(ASSIGNMENT_DATE, 'YYYY'): 연도 필터
- 승진 수: COUNT(DISTINCT b.EMP_ID)
```

**추가 예제 2: 휴직 중인 직원 조회**
```
title: 휴직 직원 조회
doc_type: query_example
usage_type: rag_action

content:
휴직 중인 직원
현재 휴직자
휴직 현황
육아휴직 직원
- V_AI_EMPLOYEE JOIN V_AI_HISTORY
- LEAVE_OF_ABSENCE_YN = 'Y'

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.ASSIGNMENT_TYPE_CODE, b.ASSIGNMENT_REASON_CODE,
       b.ASSIGNMENT_START_DATE, b.EXPECTED_RETURN_FROM_LEAVE_DATE
FROM v_ai_employee a
JOIN v_ai_history b ON a.EMP_ID = b.EMP_ID
WHERE b.LEAVE_OF_ABSENCE_YN = 'Y'
  AND b.ASSIGNMENT_START_DATE = (
      SELECT MAX(b2.ASSIGNMENT_START_DATE)
      FROM v_ai_history b2
      WHERE b2.EMP_ID = b.EMP_ID
        AND b2.LEAVE_OF_ABSENCE_YN = 'Y'
  )
  AND a.WORK_STATUS = '재직'
ORDER BY b.ASSIGNMENT_START_DATE DESC
```

## 핵심 패턴
- LEAVE_OF_ABSENCE_YN = 'Y': 휴직 발령만
- 최신 휴직 발령: MAX(ASSIGNMENT_START_DATE) 서브쿼리
- 재직자만: WORK_STATUS = '재직' (퇴직자 제외)
- 육아휴직: ASSIGNMENT_REASON_CODE LIKE '%육아%' 추가
```

**추가 예제 3: 발령유형별 통계**
```
title: 발령유형별 통계 조회
doc_type: query_example
usage_type: rag_action

content:
발령유형별 현황
인사이동 통계
발령 종류별 건수
전보 승진 휴직 건수
- V_AI_HISTORY
- ASSIGNMENT_TYPE_CODE GROUP BY

context_data:
## SQL
```sql
SELECT b.ASSIGNMENT_TYPE_CODE,
       COUNT(*) AS total_count,
       COUNT(DISTINCT b.EMP_ID) AS emp_count
FROM v_ai_history b
WHERE TO_CHAR(b.ASSIGNMENT_DATE, 'YYYY') = ':연도'
GROUP BY b.ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC
```

## 핵심 패턴
- ASSIGNMENT_TYPE_CODE: 승진, 전보, 전직, 휴직, 복직, 퇴직 등
- COUNT(*): 발령 총 건수
- COUNT(DISTINCT EMP_ID): 대상 직원 수 (1인 다건 방지)
- 연도 필터: TO_CHAR(ASSIGNMENT_DATE, 'YYYY')
```

---

## 4. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| ASSIGNMENT_HISTORY_ID | **X** | 내부 PK |
| EMP_ID | O (FK) | 다른 뷰와 동일 |
| PERSON_ID | **X** | 내부 ID |
| ASSIGNMENT_APPROVAL_ID | **X** | 내부 ID |
| ASSIGNMENT_START_DATE | O | 발령 시작일 |
| ASSIGNMENT_END_DATE | O | 발령 종료일 |
| ASSIGNMENT_DATE | O (★) | 발령일자 |
| ASSIGNMENT_SEQUENCE | **X** | 내부용 |
| ASSIGNMENT_TYPE_CODE | O (★) | 발령유형 |
| ASSIGNMENT_REASON_CODE | O | 발령사유 |
| HR_AREA | **X** | 인사영역 — NL2SQL 미사용 |
| ASSIGNMENT_DEPARTMENT_ID | **X** | 코드값 (부서명 아님) |
| PAYROLL_DEPARTMENT_ID | **X** | 내부용 |
| ATTENDANCE_DEPARTMENT_ID | **X** | 내부용 |
| ASSIGNMENT_GRADE_CODE | O | 발령 직급 |
| ASSIGNMENT_JOB_CODE | **X** | 발령 직무 — 활용도 낮음 |
| ASSIGNMENT_TITLE_NAME | O | 발령 직책명 |
| IS_ORG_LEADER_YN | **X** | 조직장 여부 — 활용도 낮음 |
| LEAVE_OF_ABSENCE_YN | O (★) | 휴직 여부 |
| EXPECTED_RETURN_FROM_LEAVE_DATE | **X** | 복직예정일 |
| EXPECTED_CHILDBIRTH_DATE | **X** | 출산예정일 (PII) |
| HR_REFLECTED_YN | **X** | 내부용 |
| PRINT_YN | **X** | 내부용 |

---

## 5. 검증 계획

```sql
-- 1) 전체 건수 + 직원 수
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp FROM V_AI_HISTORY;

-- 2) ASSIGNMENT_TYPE_CODE 값 도메인 (최우선 — 승진,전보,휴직 등 확인)
SELECT ASSIGNMENT_TYPE_CODE, COUNT(*) FROM V_AI_HISTORY
WHERE ASSIGNMENT_TYPE_CODE IS NOT NULL
GROUP BY ASSIGNMENT_TYPE_CODE ORDER BY COUNT(*) DESC;

-- 3) ASSIGNMENT_REASON_CODE 값 도메인
SELECT ASSIGNMENT_REASON_CODE, COUNT(*) FROM V_AI_HISTORY
WHERE ASSIGNMENT_REASON_CODE IS NOT NULL
GROUP BY ASSIGNMENT_REASON_CODE ORDER BY COUNT(*) DESC
FETCH FIRST 20 ROWS ONLY;

-- 4) LEAVE_OF_ABSENCE_YN 분포
SELECT LEAVE_OF_ABSENCE_YN, COUNT(*) FROM V_AI_HISTORY
GROUP BY LEAVE_OF_ABSENCE_YN;

-- 5) ASSIGNMENT_DATE 범위
SELECT MIN(ASSIGNMENT_DATE), MAX(ASSIGNMENT_DATE) FROM V_AI_HISTORY;

-- 6) 1인당 평균 발령 건수
SELECT ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT EMP_ID), 1) AS avg_per_emp
FROM V_AI_HISTORY;
```

---

## 6. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **table_catalog 미등재** | NL2SQL 사각지대 | **신규 등재** | **최우선** |
| **EMPLOYEE_ID → EMP_ID** | 다른 뷰와 불일치 | DDL 변경 완료 (EMP_ID로 통일) | **완료** |
| **COMMENT 오류** | TITLE_NAME↔LEADER_YN 뒤바뀜 | 교정 | **확정** |
| **COMMENT 보강** | 일부만 존재 | 전체 컬럼 COMMENT 보강 | **확정** |
| **부서명 컬럼 부재** | ORG_ID만 노출 | ORM_ORG JOIN 검토 | 검토 필요 |
| **fewshot 예제** | 없음 | 3건 추가 (승진자, 휴직자, 발령통계) | **확정** |
| ASSIGNMENT_TYPE_CODE 값 도메인 | 미확인 | DB 조회로 확인 | 검증 필요 |

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: table_catalog 미등재 식별, COMMENT 오류 발견, 카탈로그 신규 등재안, fewshot 3건 |
| 2026-03-17 | EMPLOYEE_ID → EMP_ID 변경: DDL, COMMENT, 카탈로그, fewshot 전체 반영. 다른 V_AI_* 뷰와 조인키 일관성 확보 |
