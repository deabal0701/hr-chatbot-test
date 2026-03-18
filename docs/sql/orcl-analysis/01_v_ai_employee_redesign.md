# V_AI_EMPLOYEE 뷰 재설계

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_EMPLOYEE`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 뷰 중복 데이터 문제 (2,437건 → 2,345건)

### 1.1 현황

| 쿼리 | 결과 | 의미 |
|------|------|------|
| `SELECT COUNT(DISTINCT EMP_NO) FROM PHM_EMP` | **2,345** | 실제 직원 수 |
| `SELECT COUNT(*) FROM PHM_EMP` | 2,349 | PHM_EMP 전체 행 수 |
| `SELECT COUNT(*) FROM V_AI_EMPLOYEE` | **2,437** | 뷰 행 수 (중복 포함) |

**중복 원인 2가지** (진단 완료):

| 원인 | 증가 | 진단 방법 |
|------|------|----------|
| **① PHM_EMP COMPANY_CD 복수 소속** | +4건 (2,345→2,349) | `SELECT COUNT(*) FROM PHM_EMP WHERE COMPANY_CD='01'` = 2,345 |
| **② FC11(DEPARTMENT) FRM_CODE 곱집합** | +88건 (2,345→2,433) | 아래 진단 참조 |

**진단 결과**: JOIN을 하나씩 추가하며 COUNT 확인 → **FC11(CPE_GROUP_CD)에서만 증가 발생**.

```sql
-- FC11(DEPARTMENT)만 JOIN해도 2,433 (나머지 JOIN은 모두 2,345 유지)
SELECT COUNT(*) FROM PHM_EMP PE
LEFT JOIN FRM_CODE FC11 ON FC11.CD = PE.ORG_ID AND FC11.CD_KIND = 'CPE_GROUP_CD'
WHERE PE.COMPANY_CD = '01';   -- 결과: 2,433 (+88건)
```

**원인**: `PE.ORG_ID`에 대해 FRM_CODE의 `CPE_GROUP_CD`에 동일 코드(CD)의 **유효기간(STA_YMD/END_YMD) 이력이 복수** 존재 (조직 개편/명칭 변경 등). JOIN 조건이 `CD + CD_KIND`만이라 이력 전체가 매칭되어 row 증가.

**해결**: FRM_CODE 테이블 쪽에서 CPE_GROUP_CD 중복 이력 데이터 정리 완료 → 뷰 JOIN 조건 변경 불필요

### 1.2 원인 분석

#### 중복 사번: '9012', '9013', '4601', '20160415'

| EMP_NO | EMP_ID | PERSON_ID | COMPANY_CD | HIRE_CD | MOD_DATE | MOD_USER_ID |
|--------|--------|-----------|------------|---------|----------|-------------|
| 20160415 | 62311 | 62311 | **01** | 1020 | 2016-04-15 | 241 |
| 20160415 | 67520 | 62311 | **02** | NULL | 2020-02-20 | 214639 |
| 4601 | 4601 | 4601 | **01** | 1030 | 2013-11-26 | 0 |
| 4601 | 67518 | 4601 | **02** | NULL | 2020-02-20 | 214639 |
| 9012 | 9012 | 9012 | **01** | 1010 | 2015-04-24 | 210111 |
| 9012 | 67519 | 9012 | **02** | NULL | 2020-02-20 | 214639 |
| 9013 | 9013 | 9013 | **01** | 3010 | 2020-02-28 | 214639 |
| 9013 | 67517 | 9013 | **02** | NULL | 2020-02-20 | 214639 |

#### 결론

**중복 원인: `COMPANY_CD`(인사영역코드)가 다른 복수 소속 등록**

- 이력성 중복(MOD_DATE 기반 스냅샷)이 **아님**
- 인사영역 '01'(주 소속)과 '02'(겸직/파견/분할법인 등)에 동일 직원이 이중 등록된 구조
- 2020-02-20에 사용자 214639가 인사영역 '02'로 4명을 일괄 등록한 것으로 추정
- '02' 영역 데이터는 HIRE_CD가 전부 NULL이고, 각종 _YMD가 전부 2020-02-20으로 동일 → 원본이 아닌 부가 등록

#### MOD_DATE 기반 중복 제거가 부적절한 이유

- 사번 9012: '02'의 MOD_DATE(2020-02-20)가 '01'(2015-04-24)보다 최신 → MOD_DATE DESC 시 HIRE_CD=NULL인 '02'가 선택됨
- 비즈니스 키는 MOD_DATE가 아닌 **COMPANY_CD**

### 1.3 수정 방향

```sql
WHERE PE.COMPANY_CD = '01'   -- 주 인사영역만 필터
```

### 1.4 영향 범위

PHM_EMP를 직접 참조하는 뷰만 수정 필요:

| 뷰 이름 | PHM_EMP 참조 방식 | 수정 필요 |
|---------|------------------|----------|
| **V_AI_EMPLOYEE** | `FROM PHM_EMP PE` | **필요** — WHERE 조건 추가 |
| **V_AI_SCHOLAR** | `JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID` | **필요** — JOIN 조건 추가 |
| V_AI_FEEDBACK | `VI_FRM_PHM_EMP` (HR 시스템 내부 뷰) | 확인 필요 |
| 그 외 모든 뷰 | PHM_EMP 직접 참조 없음 | 불필요 |

### 1.5 기대 효과

- V_AI_EMPLOYEE: 2,437 → **2,345건** (COMPANY_CD 필터 -4건 + FRM_CODE CPE_GROUP_CD 중복 정리 -88건)
- NL2SQL 집계 정확도 보장
- JOIN 시 중복 EMP_ID로 인한 곱집합 위험 제거
- HIRE_CD 등 핵심 필드에서 NULL 행(02 영역) 제거

---

## 2. CAREER_MONTHS / CAREER_YEARS NULL 문제

### 2.1 현황

```sql
-- 현재 뷰 정의 (orcl-business_view_db.sql:134-135)
PE.CAREER_NUM               AS CAREER_MONTHS,
TRUNC(PE.CAREER_NUM / 12)   AS CAREER_YEARS,
```

```sql
-- 실제 데이터 확인
SELECT COUNT(*) FROM V_AI_EMPLOYEE WHERE CAREER_MONTHS IS NOT NULL;
-- 결과: 0

SELECT COUNT(*) FROM PHM_EMP WHERE CAREER_NUM IS NOT NULL;
-- 결과: 0
```

**PHM_EMP.CAREER_NUM이 전 직원 대상 NULL** → 뷰의 CAREER_MONTHS, CAREER_YEARS도 전부 NULL.

### 2.2 NL2SQL에 미치는 영향

| 상황 | 발생 시나리오 | 결과 |
|------|-------------|------|
| LLM이 CAREER_YEARS 사용 | "5년 이상 근속자는?" → `WHERE CAREER_YEARS >= 5` | **0건 반환** (전부 NULL) |
| LLM이 CAREER_MONTHS 사용 | "평균 근속 개월수?" → `AVG(CAREER_MONTHS)` | **NULL 반환** |
| 스키마에서 컬럼 노출 | schema_description에 `CAREER_MONTHS: NUMBER` 표시 | LLM이 사용 가능한 컬럼으로 **오인** |

현재 `table_catalog.py`에는 CAREER_MONTHS/CAREER_YEARS가 미등재되어 있으나, `schema_description`(Oracle 스키마 직접 조회)에는 노출되므로 LLM이 선택할 위험이 있다.

### 2.3 해결 방안 비교

| 방안 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **A) 뷰에서 HIRE_DATE 기반 계산** | `MONTHS_BETWEEN(종료일, HIRE_DATE)` | 뷰 사용자도 근속연수 바로 조회 가능 | 뷰 수정 필요, SYSDATE 의존(비결정적) |
| **B) 컬럼 제거 + NL2SQL 유도** | 뷰에서 CAREER_* 삭제, NL2SQL가 직접 계산 | 뷰 단순화, NULL 컬럼 제거 | 스키마 변경 큼, 직접 SQL 사용자 불편 |
| **C) 병행 (권장)** | 뷰에서 계산 + NL2SQL 가이드 | 양쪽 모두 정확한 값 | 뷰+NL2SQL 양쪽 수정 |

### 2.4 권장안: 방안 C (뷰 계산 + NL2SQL 가이드)

#### 이유

1. **뷰에 값이 있어야** 직접 SQL 사용자도 `SELECT CAREER_YEARS FROM V_AI_EMPLOYEE`로 바로 조회 가능
2. **NL2SQL에도 가이드**가 있어야 LLM이 HIRE_DATE 대신 CAREER_YEARS를 적절히 사용
3. 뷰에서 이미 계산해 주면 NL2SQL이 생성하는 SQL이 단순해짐 (`WHERE CAREER_YEARS >= 5` vs 복잡한 MONTHS_BETWEEN 식)

#### 뷰 계산 로직

```sql
-- HIRE_YMD: DATE NOT NULL, RETIRE_YMD: DATE (nullable)
-- 재직자: RETIRE_YMD가 NULL → SYSDATE까지, 퇴직자: RETIRE_YMD까지
TRUNC(MONTHS_BETWEEN(NVL(PE.RETIRE_YMD, SYSDATE), PE.HIRE_YMD))      AS CAREER_MONTHS,
TRUNC(MONTHS_BETWEEN(NVL(PE.RETIRE_YMD, SYSDATE), PE.HIRE_YMD) / 12) AS CAREER_YEARS,
```

**설계 포인트**:
- `HIRE_YMD`, `RETIRE_YMD` 모두 DATE 타입 → TO_DATE/NULLIF 불필요
- `HIRE_YMD`는 NOT NULL → NULL 방어 불필요
- `NVL(RETIRE_YMD, SYSDATE)`: 재직자는 현재일, 퇴직자는 퇴직일까지 계산
- `TRUNC()`: 월/연 모두 내림 (ROUND 사용 시 15일 미만 근무가 0개월로 처리되는 문제 방지)

---

## 3. NL2SQL 연동 개선

### 3.1 table_catalog.py 수정

`v_ai_employee` 카탈로그의 `columns`에 CAREER 관련 정보 추가:

```python
# 현재
"HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,'YYYY')=':YYYY')",

# 변경
"HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,'YYYY')=':YYYY', 근속연수 원천)",
"CAREER_MONTHS (재직 개월수, HIRE_DATE 기반 자동계산, 퇴직자는 퇴직일까지)",
"CAREER_YEARS ★재직 연수 (근속연수 질의 시 사용: CAREER_YEARS >= N)",
```

### 3.2 fewshot 예제 (tb_docs)

hermesdb 확인 결과, 근속연수 관련 예제(id=960)가 이미 존재한다. 기존 DB 포맷이 문서 제안보다 우수하므로 **기존 포맷을 따라** 미존재 예제만 추가한다.

**기존 DB 포맷 특징** (기존 39건의 fewshot 예제 참조):
- `content`: 질문 변형을 여러 줄로 나열 (벡터 매칭률 향상)
- `context_data`: `## SQL` + 코드블록 + `## 핵심 패턴` 설명
- 파라미터: `:연수`, `:연도` 등 플레이스홀더 사용

| 예제 | DB 상태 | 조치 |
|------|---------|------|
| 근속연수 기준 집계 | **id=960 존재** | 추가 불필요 |
| 평균 근속연수 | 없음 | 아래 포맷으로 추가 |
| 근속연수 구간별 분포 | 없음 | 아래 포맷으로 추가 |

**추가 예제 1: 평균 근속연수** (기존 DB 포맷 준수)
```
title: 평균 근속연수 조회
doc_type: query_example
usage_type: rag_action

content:
평균 근속연수
재직자 평균 근무기간
직원 평균 재직기간
근속년수 평균
- CAREER_YEARS의 AVG 사용
- 재직자만 대상

context_data:
## SQL
```sql
SELECT ROUND(AVG(CAREER_YEARS), 1) AS avg_career_years
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```

## 핵심 패턴
- AVG(CAREER_YEARS): 평균 근속 연수
- ROUND(..., 1): 소수 첫째자리
- 부서별: GROUP BY DEPARTMENT 추가
```

**추가 예제 2: 근속연수 구간별 분포** (기존 DB 포맷 준수)
```
title: 근속연수 구간별 직원 분포 조회
doc_type: query_example
usage_type: rag_action

content:
근속연수별 직원 분포
재직기간 구간별 인원
장기근속 단기근속 비율
근속 기간 분석
- CASE WHEN으로 구간 분류
- CAREER_YEARS 사용

context_data:
## SQL
```sql
SELECT
    CASE
        WHEN CAREER_YEARS < 1 THEN '1년 미만'
        WHEN CAREER_YEARS < 3 THEN '1~3년'
        WHEN CAREER_YEARS < 5 THEN '3~5년'
        WHEN CAREER_YEARS < 10 THEN '5~10년'
        ELSE '10년 이상'
    END AS career_range,
    COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY
    CASE
        WHEN CAREER_YEARS < 1 THEN '1년 미만'
        WHEN CAREER_YEARS < 3 THEN '1~3년'
        WHEN CAREER_YEARS < 5 THEN '3~5년'
        WHEN CAREER_YEARS < 10 THEN '5~10년'
        ELSE '10년 이상'
    END
ORDER BY MIN(CAREER_YEARS)
```

## 핵심 패턴
- CASE WHEN 구간: 비즈니스 요구에 따라 조정 가능
- ORDER BY MIN(CAREER_YEARS): 구간 순서 보장
- 비율 추가 시: ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1)
```

### 3.3 prompt_build 보강 (검토 사항)

현재 `table_catalog`의 비즈니스 메타데이터가 `schema_retrieval_node`(테이블 선택)에서만 사용되고, `prompt_build_node`(SQL 생성)에는 전달되지 않는 구조적 한계가 있다.

**현재 흐름**:
```
schema_retrieval → table_catalog (비즈니스 컨텍스트 사용) → 테이블 선택
prompt_build     → schema_description (DB 스키마만 사용) → SQL 생성 ← catalog 정보 없음
```

**개선 검토**: prompt_build에 catalog의 컬럼 가이드를 주입하면 LLM이 더 정확한 SQL을 생성할 수 있다. 단, 프롬프트 길이 증가 → 토큰 비용/지연 트레이드오프 고려 필요. → `20_table_catalog_update.md`에서 상세 검토.

---

## 4. 수정 SQL 전문

### 4.1 V_AI_EMPLOYEE 뷰 수정

```sql
CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_EMPLOYEE" (
    "EMP_ID", "EMP_NAME", "EMP_NAME_ENG", "COMPANY_CODE",
    "POSITION", "BIRTH_DATE", "DEPARTMENT",
    "CAREER_MONTHS", "CAREER_YEARS",
    "DUTY", "DUTY_DATE", "EMP_TYPE", "GENDER",
    "GROUP_JOIN_DATE", "HIRE_TYPE", "HIRE_DATE",
    "WORK_STATUS", "GRADE", "GRADE_DATE",
    "RETIRE_REASON", "RETIRE_DATE",
    "SALARY_STEP", "SALARY_STEP_DATE"
) AS
SELECT
    PE.EMP_ID                   AS EMP_ID,
    PN.KOR_NAME                 AS EMP_NAME,
    PN.ENG_NAME                 AS EMP_NAME_ENG,
    PE.COMPANY_CD               AS COMPANY_CODE,
    FC.CD_NM                    AS POSITION,
    PE.BIRTH_YMD                AS BIRTH_DATE,
    FC11.CD_NM                  AS DEPARTMENT,
    -- [변경] CAREER_MONTHS/YEARS: NULL이던 PE.CAREER_NUM → HIRE_YMD(DATE NOT NULL) 기반 계산
    TRUNC(MONTHS_BETWEEN(NVL(PE.RETIRE_YMD, SYSDATE), PE.HIRE_YMD))      AS CAREER_MONTHS,
    TRUNC(MONTHS_BETWEEN(NVL(PE.RETIRE_YMD, SYSDATE), PE.HIRE_YMD) / 12) AS CAREER_YEARS,
    FC3.CD_NM                   AS DUTY,
    PE.DUTY_YMD                 AS DUTY_DATE,
    FC4.CD_NM                   AS EMP_TYPE,
    FC5.CD_NM                   AS GENDER,
    PE.GROUP_YMD                AS GROUP_JOIN_DATE,
    FC6.CD_NM                   AS HIRE_TYPE,
    PE.HIRE_YMD                 AS HIRE_DATE,
    CASE PE.IN_OFFI_YN
        WHEN 'Y' THEN '재직'
        WHEN 'N' THEN '퇴직'
        ELSE PE.IN_OFFI_YN
    END                         AS WORK_STATUS,
    FC8.CD_NM                   AS GRADE,
    PE.POS_GRD_YMD              AS GRADE_DATE,
    FC9.CD_NM                   AS RETIRE_REASON,
    PE.RETIRE_YMD               AS RETIRE_DATE,
    FC10.CD_NM                  AS SALARY_STEP,
    PE.YEARNUM_YMD              AS SALARY_STEP_DATE
FROM PHM_EMP PE
-- [변경] 이름: MAX 집계 유지 (PHM_NAME 스키마에 STA_YMD/END_YMD 여부 확인 필요)
LEFT JOIN (
    SELECT EMP_ID,
           MAX(CASE WHEN NAME_TYPE_CD = 'KOR' THEN LAST_NM END) AS KOR_NAME,
           MAX(CASE WHEN NAME_TYPE_CD = 'ENG' THEN LAST_NM END) AS ENG_NAME
    FROM PHM_NAME
    GROUP BY EMP_ID
) PN ON PN.EMP_ID = PE.EMP_ID
-- FRM_CODE JOIN (FRM_CODE 쪽에서 중복 제거 처리 완료 → 단순 JOIN 유지)
LEFT JOIN FRM_CODE FC   ON FC.CD   = PE.POS_CD         AND FC.CD_KIND   = 'PHM_POS_CD'
LEFT JOIN FRM_CODE FC3  ON FC3.CD  = PE.DUTY_CD        AND FC3.CD_KIND  = 'PHM_DUTY_CD'
LEFT JOIN FRM_CODE FC4  ON FC4.CD  = PE.EMP_KIND_CD    AND FC4.CD_KIND  = 'PHM_EMP_KIND_CD'
LEFT JOIN FRM_CODE FC5  ON FC5.CD  = PE.GENDER_CD      AND FC5.CD_KIND  = 'PHM_GENDER_CD'
LEFT JOIN FRM_CODE FC6  ON FC6.CD  = PE.HIRE_CD        AND FC6.CD_KIND  = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC8  ON FC8.CD  = PE.POS_GRD_CD     AND FC8.CD_KIND  = 'PHM_POS_GRD_CD'
LEFT JOIN FRM_CODE FC9  ON FC9.CD  = PE.RETIRE_TYPE_CD AND FC9.CD_KIND  = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC11 ON FC11.CD = PE.ORG_ID          AND FC11.CD_KIND = 'CPE_GROUP_CD'
LEFT JOIN FRM_CODE FC10 ON FC10.CD = PE.YEARNUM_CD     AND FC10.CD_KIND = 'PHM_HOBONG'
-- [변경] 주 인사영역만 필터 (중복 4건 제거)
WHERE PE.COMPANY_CD = '01';

GRANT SELECT ON "H552_RND"."V_AI_EMPLOYEE" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_EMPLOYEE IS '직원 기본정보 뷰 (메인 테이블, 모든 V_AI_* 뷰와 EMP_ID로 JOIN)';

-- PK / 조인 관계
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.EMP_ID IS '사원 고유 식별 번호 (PK, PHM_EMP.EMP_ID). 모든 V_AI_* 뷰의 조인키 (V_AI_PAY_REPORT만 EMPLOYEE_ID)';

-- 인적사항
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.EMP_NAME IS '사원 이름 (한글, PHM_NAME.LAST_NM)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.EMP_NAME_ENG IS '사원 이름 (영문, PHM_NAME.LAST_NM)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.COMPANY_CODE IS '인사영역코드 (01=주소속, WHERE 필터로 01만 노출)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.BIRTH_DATE IS '생년월일 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.GENDER IS '성별 (남, 여)';

-- 조직/직위/직책/직급
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.DEPARTMENT IS '소속 부서명';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.POSITION IS '직위 (회장~사원)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.DUTY IS '직책 (대표이사,팀장,팀원 등)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.DUTY_DATE IS '직책 부여일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.GRADE IS '직급 (1급~9급)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.GRADE_DATE IS '직급 승진일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.EMP_TYPE IS '고용형태 (정규직, 기간제)';

-- 입사/퇴직/재직
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.HIRE_TYPE IS '입사구분 (신입,경력,재입사 등)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.HIRE_DATE IS '입사일자 (DATE, NOT NULL). 근속연수 계산 원천';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.GROUP_JOIN_DATE IS '그룹 입사일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.WORK_STATUS IS '재직상태 (재직/퇴직, PHM_EMP.IN_OFFI_YN 변환)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.RETIRE_REASON IS '퇴직사유 (퇴직,정년,사망 등)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.RETIRE_DATE IS '퇴직일자 (DATE, 재직자는 NULL)';

-- 근속연수 (계산 컬럼)
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.CAREER_MONTHS IS '재직 개월수 (TRUNC(MONTHS_BETWEEN) 계산: 재직자=SYSDATE-HIRE_YMD, 퇴직자=RETIRE_YMD-HIRE_YMD)';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.CAREER_YEARS IS '재직 연수 (CAREER_MONTHS/12 내림). 근속연수 질의 시 사용';

-- 호봉
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.SALARY_STEP IS '호봉';
COMMENT ON COLUMN H552_RND.V_AI_EMPLOYEE.SALARY_STEP_DATE IS '호봉 승급일자 (DATE)';
```

### 4.2 V_AI_SCHOLAR 뷰 수정 (연쇄 영향)

```sql
-- 기존
JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID

-- 변경: COMPANY_CD 필터 추가
JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID AND PE.COMPANY_CD = '01'
```

---

## 5. 검증 계획

### 5.1 데이터 정합성

```sql
-- 1) 중복 제거 확인
SELECT COUNT(*) FROM V_AI_EMPLOYEE;          -- 기대: 2,345
SELECT COUNT(DISTINCT EMP_ID) FROM V_AI_EMPLOYEE;  -- 기대: 2,345 (동일)

-- 2) CAREER 계산 확인
SELECT EMP_ID, HIRE_DATE, RETIRE_DATE, WORK_STATUS,
       CAREER_MONTHS, CAREER_YEARS
FROM V_AI_EMPLOYEE
WHERE HIRE_DATE IS NOT NULL
FETCH FIRST 10 ROWS ONLY;

-- 3) 재직자 근속연수 범위 확인
SELECT MIN(CAREER_YEARS), MAX(CAREER_YEARS), AVG(CAREER_YEARS)
FROM V_AI_EMPLOYEE
WHERE WORK_STATUS = '재직';

-- 4) 퇴직자 근속연수 고정 확인 (SYSDATE 의존 아님)
SELECT EMP_ID, HIRE_DATE, RETIRE_DATE, CAREER_YEARS
FROM V_AI_EMPLOYEE
WHERE WORK_STATUS = '퇴직' AND CAREER_YEARS IS NOT NULL
FETCH FIRST 5 ROWS ONLY;
```

### 5.2 NL2SQL 테스트 질의

| 질문 | 기대 동작 |
|------|----------|
| "전체 직원 수는?" | COUNT = 2,345 (중복 제거 반영) |
| "5년 이상 근속자는?" | CAREER_YEARS >= 5 사용, 유효한 결과 반환 |
| "평균 근속연수?" | AVG(CAREER_YEARS) 사용, NULL 아닌 실수값 |
| "부서별 평균 근속연수" | GROUP BY DEPARTMENT + AVG(CAREER_YEARS) |

---

## 6. 뷰 구조 검토 (잠재 이슈)

### 6.1 FRM_CODE JOIN으로 인한 row 증가 → FRM_CODE 데이터 정리로 해결

**문제**: FRM_CODE의 UK는 `(LOCALE_CD, COMPANY_CD, CD_KIND, CD, STA_YMD)`이다. 기존 JOIN 조건은 `CD_KIND + CD`만 사용하므로, 동일 코드에 STA_YMD(유효기간)가 다른 이력이 여러 건 있으면 **1:N JOIN으로 row가 증가**한다.

**진단 결과**: FC11(CPE_GROUP_CD=DEPARTMENT)에서만 +88건 발생. 나머지 FRM_CODE JOIN은 곱집합 없음.

**해결**: FRM_CODE 테이블 쪽에서 CPE_GROUP_CD 중복 이력 데이터 정리 완료. 뷰의 JOIN 조건은 기존과 동일하게 `CD + CD_KIND`만 사용.

```sql
-- 정리 후 검증 쿼리
SELECT COUNT(*) AS view_rows FROM V_AI_EMPLOYEE;           -- 기대: 2,345
SELECT COUNT(DISTINCT EMP_ID) FROM V_AI_EMPLOYEE;          -- 기대: 2,345 (동일)
```

### 6.2 이름 조회 MAX 집계 (심각도: 낮음)

**현재 로직**:
```sql
MAX(CASE WHEN NAME_TYPE_CD = 'KOR' THEN LAST_NM END) AS KOR_NAME
```

**잠재 이슈**: 동일 EMP_ID에 KOR 이름이 여러 건이면 `MAX()`가 가나다순 마지막 값을 반환. 예: '김철수', '김철수A' → '김철수A' 선택.

**판단**: HR 시스템에서 동일 이름유형에 복수 행은 드문 케이스. 발생 시 `ROW_NUMBER()` 기반 최신 이름 선택으로 대체 가능하나, 현 구조로 충분할 가능성 높음.

```sql
-- 이름 중복 여부 확인
SELECT EMP_ID, NAME_TYPE_CD, COUNT(*)
FROM PHM_NAME
WHERE NAME_TYPE_CD IN ('KOR', 'ENG')
GROUP BY EMP_ID, NAME_TYPE_CD HAVING COUNT(*) > 1;
```

### 6.3 미래 퇴직일 처리 (심각도: 낮음)

**현재**: `NVL(PE.RETIRE_YMD, SYSDATE)` — RETIRE_YMD가 미래 날짜면 CAREER_MONTHS가 음수가 될 수 있음.

**판단**: 일반적으로 퇴직일은 과거/현재이지만, 예정 퇴직일(정년 등)이 미래로 입력되는 경우 존재 가능. 이 경우 `MONTHS_BETWEEN(미래일, HIRE_YMD)`이므로 양수가 되어 문제없음. 단, 재직자인데 RETIRE_YMD가 미래 날짜로 설정되어 있으면 SYSDATE가 아닌 해당 미래 날짜로 계산됨.

```sql
-- 미래 퇴직일 확인
SELECT EMP_ID, HIRE_YMD, RETIRE_YMD, IN_OFFI_YN
FROM PHM_EMP
WHERE RETIRE_YMD > SYSDATE AND COMPANY_CD = '01';
```

### 6.4 DEPARTMENT의 조직코드 테이블 구조 (심각도: 중간)

**현재**: `FC11.CD = PE.ORG_ID AND FC11.CD_KIND = 'CPE_GROUP_CD'`

**문제**: `PE.ORG_ID`는 NUMBER, `FC.CD`는 VARCHAR2(30). 암묵적 형변환 발생. 또한 FRM_CODE는 코드 테이블인데 조직 정보를 담고 있어, 별도의 조직 테이블(ORM_ORG)이 더 적합할 수 있음.

**참고**: ORM_ORG 테이블에 `ORG_ID`, `ORG_NM`, `ORG_FULL_NM`, `SUPER_ORG_ID`(상위 조직) 등 계층 구조 정보가 있음. FRM_CODE는 flat한 코드명만 제공.

```sql
-- ORM_ORG 활용 시 (계층 구조 포함 가능)
LEFT JOIN ORM_ORG OO ON OO.ORG_ID = PE.ORG_ID
-- OO.ORG_NM, OO.ORG_FULL_NM, OO.SUPER_ORG_ID 활용 가능
```

→ 상세 분석은 `03_v_ai_career.md` 또는 별도 조직 체계 문서에서 다룸.

### 6.5 NULL 코드값 처리 (심각도: 낮음)

**현재**: LEFT JOIN이므로 코드값이 NULL이면 해당 컬럼이 NULL로 반환됨. 이는 의도된 동작.

**NL2SQL 영향**: `WHERE POSITION = '과장'` 같은 쿼리에서 코드값이 NULL인 직원은 자동 제외됨. 문제없음.

**개선 여지**: 특정 컬럼(EMP_TYPE, GENDER 등)에서 NULL이 비정상인 경우 COALESCE로 기본값 설정 가능하나, 원본 데이터 오류를 숨기므로 비권장.

### 6.6 WORK_STATUS 코드 확장성 (심각도: 낮음)

**현재**: `CASE WHEN 'Y' → '재직', 'N' → '퇴직', ELSE 원본값`

**판단**: `IN_OFFI_YN`은 CHAR(1) NOT NULL이며 'Y'/'N' 외 값은 거의 없음. ELSE절이 원본값을 반환하므로 미지 값도 노출됨. 휴직 등 추가 상태가 필요하면 별도 컬럼(HIRE_TYPE에 '휴직' 포함) 또는 CAM_HISTORY로 판별.

### 6.7 코드 종류(CD_KIND) 충돌 (심각도: 낮음)

**현재**: HIRE_TYPE과 RETIRE_REASON이 동일한 `CAM_CAU_CD` 코드 종류를 사용.

```sql
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PE.HIRE_CD AND FC6.CD_KIND = 'CAM_CAU_CD'      -- 입사구분
LEFT JOIN FRM_CODE FC9 ON FC9.CD = PE.RETIRE_TYPE_CD AND FC9.CD_KIND = 'CAM_CAU_CD' -- 퇴직사유
```

**판단**: CD_KIND가 같아도 CD 값이 다르므로 문제없음. 입사/퇴직 코드는 같은 '인사발령사유' 체계에서 관리되는 것이 HR 시스템의 일반적 패턴.

### 6.8 요약

| # | 이슈 | 심각도 | 조치 |
|---|------|--------|------|
| 6.1 | FRM_CODE JOIN row 증가 | ~~해결~~ | FRM_CODE CPE_GROUP_CD 중복 이력 데이터 정리 완료 |
| 6.2 | 이름 MAX 집계 | 낮음 | 실데이터 확인, 중복 있으면 ROW_NUMBER 전환 |
| 6.3 | 미래 퇴직일 | 낮음 | 실데이터 확인, 필요시 LEAST(RETIRE_YMD, SYSDATE) |
| 6.4 | 조직 FRM_CODE vs ORM_ORG | **중간** | ORM_ORG JOIN 전환 검토 (계층 구조 활용) |
| 6.5 | NULL 코드값 | 낮음 | LEFT JOIN 의도된 동작, 현행 유지 |
| 6.6 | WORK_STATUS 확장성 | 낮음 | ELSE절로 안전, 현행 유지 |
| 6.7 | CAM_CAU_CD 충돌 | 낮음 | CD값이 다르므로 문제없음 |
| ~~6.8~~ | CAREER ROUND 오류 | ~~해결~~ | TRUNC로 이미 변경 완료 |
| ~~6.9~~ | 날짜 타입 문제 | ~~해결~~ | HIRE_YMD/RETIRE_YMD 모두 DATE 확인, TO_DATE 제거 완료 |

**우선 조치 대상**: 6.4(ORM_ORG 전환 검토)

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2025-03-17 | 초안: PHM_EMP 중복 데이터 분석 (COMPANY_CD 이중 등록) |
| 2026-03-17 | 확장: CAREER NULL 해결, TRUNC 변경, DATE 타입 확인, COMMENT 추가, 뷰 구조 검토(섹션 6) |
