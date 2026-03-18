# V_AI_SCHOLAR 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_SCHOLAR`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_SCHOLAR`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음)

현재 배포된 뷰의 핵심 구조:

```
FROM PHM_SCHOLAR PS
JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID    ← INNER JOIN + COMPANY_CD 필터 없음
```

**문제 2가지**:
1. **PHM_EMP COMPANY_CD 중복** (01에서 식별): INNER JOIN에 `PE.COMPANY_CD = '01'` 필터 없음 → 4명 중복
2. **POSITION 컬럼 중복**: PHM_EMP.POS_CD를 통해 직위를 가져오나, 이미 V_AI_EMPLOYEE에 POSITION 존재 → 불필요한 JOIN

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql` 참조. **섹션 7.1에 개선안 DDL** 작성.

---

## 2. 이슈 분석

### 2.1 PHM_EMP JOIN 중복 — 01 문서 연쇄 영향 (확정)

**현재**:
```sql
FROM PHM_SCHOLAR PS
JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID   -- COMPANY_CD 필터 없음
LEFT JOIN FRM_CODE FC ON FC.CD = PE.POS_CD AND FC.CD_KIND = 'PHM_POS_CD'
```

**문제**: PHM_EMP에 COMPANY_CD='01'(주소속) + '02'(겸직) 복수 등록된 4명이 있으므로, 이 직원들의 학력이 2배로 증가.

**수정**:
```sql
JOIN PHM_EMP PE ON PE.EMP_ID = PS.EMP_ID AND PE.COMPANY_CD = '01'
```

### 2.2 POSITION 컬럼 — 제거 확정

**현재**: `FC.CD_NM AS POSITION` — PHM_EMP.POS_CD → FRM_CODE(PHM_POS_CD) → 직위명

**문제**:
- 이 POSITION은 PHM_EMP의 **현재 직위**이지 학력 취득 당시의 직위가 아님
- 학력은 과거에 취득한 것이므로 현재 직위와 무관
- V_AI_EMPLOYEE.POSITION과 완전히 동일한 값 → NL2SQL이 잘못 사용할 위험만 증가
- POSITION을 위해서만 PHM_EMP JOIN을 유지하는 것은 비합리적

**결론**: **POSITION 제거 + PHM_EMP JOIN 제거** 확정. 직위가 필요하면 항상 V_AI_EMPLOYEE와 LEFT JOIN하여 가져옴. PHM_EMP JOIN 제거 시 COMPANY_CD 중복 문제도 자동 해결.

### 2.3 PHM_SCHOLAR 원본 테이블 — 뷰 미활용 핵심 컬럼 발견

원본 테이블(`orcl-business_org_db.sql`)에서 뷰에 미포함된 핵심 컬럼:

| 원본 컬럼 | 타입 | COMMENT | NL2SQL 활용도 | 현재 뷰 |
|----------|------|---------|:----------:|:------:|
| **SCH_GRD_CD** | VARCHAR2(50) | 학력코드 [PHM_SCH_GRD_CD] | **★높음** — "대졸 직원 수" 질의 가능 | 미포함 |
| **LAST_YN** | VARCHAR2(1) NN | 최종여부 | **★높음** — 최종학력만 필터 가능 | 미포함 |
| **GRAD_CD** | VARCHAR2(50) | 졸업구분코드 [PHM_GRAD_CD] (졸업/재학/중퇴) | 중간 | 미포함 |
| ENTRANCE_CD | VARCHAR2(10) | 입학구분코드 [PHM_ENTRNCE_CD] | 낮음 | 미포함 |
| DAY_KIND_CD | VARCHAR2(10) | 주야간구분 (1:주간,2:야간) | 낮음 | 미포함 |

**핵심 발견**:
1. **`SCH_GRD_CD`(학력코드)**: 샘플값 '45', '40', '42' → FRM_CODE(PHM_SCH_GRD_CD) 경유 시 "대학원", "전문대", "대학교" 등으로 변환 가능. 뷰에 **EDUCATION_LEVEL** 컬럼으로 추가하면 "대졸 직원 수", "석사 이상 직원" 질의 지원 가능.
2. **`LAST_YN`(최종여부)**: NOT NULL, 'Y'/'N'. 최종학력만 필터 가능 → 뷰 WHERE에 `LAST_YN = 'Y'` 필터 추가 검토.
3. **`GRAD_CD`(졸업구분)**: FRM_CODE(PHM_GRAD_CD) 경유 시 "졸업", "재학", "중퇴" 등 변환. NL2SQL에서 활용 가능.

**추가 발견**:
- `STA_YMD`/`END_YMD`: COMMENT에 "사용안함" 표기. 실제로 뷰에서 `STA_YM`/`END_YM`(VARCHAR2, 입학/졸업 **년월**)을 사용 중.
- `MAJOR_NM`: COMMENT에 "사용안함" 표기이나, 뷰에서 직접 사용 중 (`PS.MAJOR_NM AS MAJOR_NAME`). 정규 경로는 `MAJOR_CD` → FRM_CODE(PHM_MAJOR_CD)이나 현재 뷰는 코드 변환 없이 원본명 직접 사용.

**검증 쿼리**:
```sql
-- SCH_GRD_CD 값 도메인 확인
SELECT FC.CD, FC.CD_NM, COUNT(*) AS cnt
FROM PHM_SCHOLAR PS
LEFT JOIN FRM_CODE FC ON FC.CD = PS.SCH_GRD_CD AND FC.CD_KIND = 'PHM_SCH_GRD_CD'
GROUP BY FC.CD, FC.CD_NM
ORDER BY cnt DESC;

-- LAST_YN 분포 확인
SELECT LAST_YN, COUNT(*) AS cnt
FROM PHM_SCHOLAR
GROUP BY LAST_YN;

-- GRAD_CD 값 도메인 확인
SELECT FC.CD, FC.CD_NM, COUNT(*) AS cnt
FROM PHM_SCHOLAR PS
LEFT JOIN FRM_CODE FC ON FC.CD = PS.GRAD_CD AND FC.CD_KIND = 'PHM_GRAD_CD'
GROUP BY FC.CD, FC.CD_NM
ORDER BY cnt DESC;
```

### 2.4 카탈로그 컬럼명 불일치 (현재 table_catalog.py vs 뷰 DDL)

| 카탈로그 표기 | 실제 DDL 컬럼명 | 문제 |
|-------------|---------------|------|
| `MAJOR` | MAJOR_NAME | **불일치** |
| `DOUBLE_MAJOR` | DOUBLE_MAJOR_NAME | **불일치** |
| `GRADUATION_YEAR` | GRADUATION_DATE | **불일치** (연도 vs 일자) |
| `SCHOOL_NAME` | SCHOOL_NAME | O |

### 2.5 누락 컬럼 (현재 뷰에 있지만 카탈로그 미등재)

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| ADMISSION_DATE | X | 입학일자 — 활용도 낮음 |
| SUB_MAJOR_CD | X | 부전공 코드 — NL2SQL 불필요 |
| SUB_MAJOR_NM | X | 부전공명 — 추가 검토 |
| SCHOOL_LOCATION_CODE | X | 학교 소재지 코드 — NL2SQL 불필요 |
| SCHOOL_LOCATION_NAME | X | 학교 소재지명 — 추가 검토 |

### 2.6 학력 수준(EDUCATION_LEVEL) — SCH_GRD_CD로 추가 가능 (확정)

PHM_SCHOLAR에 `SCH_GRD_CD`(학력코드, [PHM_SCH_GRD_CD])가 존재하므로, FRM_CODE JOIN을 추가하면 "고졸/전문대졸/대졸/석사/박사" 등 **학력 수준** 컬럼을 뷰에 추가 가능.

```sql
-- 뷰에 EDUCATION_LEVEL 추가
LEFT JOIN FRM_CODE FC_GRD ON FC_GRD.CD = PS.SCH_GRD_CD AND FC_GRD.CD_KIND = 'PHM_SCH_GRD_CD'
...
FC_GRD.CD_NM AS EDUCATION_LEVEL,
```

### 2.7 LEFT JOIN 필수

학력 미등록 직원은 V_AI_SCHOLAR에 행이 없으므로, **반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 필수**.

---

## 3. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 카탈로그 표기 | 비고 |
|----------|:----------:|------------|------|
| EMP_ID | O (FK) | - | |
| POSITION | O | - | **제거 권장** (V_AI_EMPLOYEE와 중복) |
| MAJOR_NAME | O | ~~MAJOR~~ → **MAJOR_NAME** | 이름 불일치 수정 |
| DOUBLE_MAJOR_NAME | O | ~~DOUBLE_MAJOR~~ → **DOUBLE_MAJOR_NAME** | 이름 불일치 수정 |
| SCHOOL_NAME | O | SCHOOL_NAME | |
| ADMISSION_DATE | X | - | 입학일자, 추가 검토 |
| GRADUATION_DATE | O | ~~GRADUATION_YEAR~~ → **GRADUATION_DATE** | 이름 불일치 수정 |
| SUB_MAJOR_NM | X | - | 부전공명, 추가 검토 |
| SCHOOL_LOCATION_NAME | X | - | 학교 소재지, 추가 검토 |

---

## 4. 개선 사항

### 4.1 뷰 개선 — POSITION 제거 + PHM_EMP JOIN 제거 (확정)

- POSITION: 학력과 무관한 현재 직위 → 제거
- PHM_EMP JOIN: POSITION을 위해서만 존재 → 제거
- COMPANY_CD 중복: PHM_EMP JOIN 제거로 자동 해결
- EDUCATION_LEVEL, GRADUATION_STATUS: FRM_CODE JOIN 추가

### 4.2 카탈로그 개선 (확정)

```python
# 현재
"v_ai_scholar": {
    "description": "학력 정보",
    "columns": [
        "EMP_ID (FK)",
        "SCHOOL_NAME (학교명)",
        "MAJOR (전공)",
        "DOUBLE_MAJOR (복수전공)",
        "GRADUATION_YEAR (졸업연도)",
    ],
    "keywords": ["학력", "학교", "대학", "전공", "졸업", ...],
    ...
}

# 변경 (4.3 table_catalog.py 반영 코드와 동일)
"v_ai_scholar": {
    "description": "학력 정보 (1:N, 학력 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 학력 미등록 직원은 행 없음)",
        "EDUCATION_LEVEL ★학력수준 (고졸,전문대졸,대졸,석사,박사 등 [PHM_SCH_GRD_CD])",
        "GRADUATION_STATUS (졸업구분: 졸업,재학,중퇴 등 [PHM_GRAD_CD])",
        "SCHOOL_NAME ★학교명",
        "MAJOR_NAME ★전공학과명 (LIKE '%경영%' 등으로 검색)",
        "DOUBLE_MAJOR_NAME (복수전공명)",
        "SUB_MAJOR_NM (부전공명)",
        "ADMISSION_DATE (입학년월, YYYYMM 형식)",
        "GRADUATION_DATE (졸업년월, YYYYMM 형식)",
        "SCHOOL_LOCATION_NAME (학교 소재지)",
    ],
    "keywords": ["학력", "학교", "대학", "전공", "졸업", "경영학", "공학", "이학", "학과", "학부", "출신학교", "석사", "박사", "대졸", "고졸", "학위", "부전공", "복수전공", "학력수준"],
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 학력 수만큼 행 존재, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
}
```

### 4.3 table_catalog.py 반영 코드

```python
"v_ai_scholar": {
    "description": "학력 정보 (1:N, 학력 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 학력 미등록 직원은 행 없음)",
        "EDUCATION_LEVEL ★학력수준 (고졸,전문대졸,대졸,석사,박사 등 [PHM_SCH_GRD_CD])",
        "GRADUATION_STATUS (졸업구분: 졸업,재학,중퇴 등 [PHM_GRAD_CD])",
        "SCHOOL_NAME ★학교명",
        "MAJOR_NAME ★전공학과명 (LIKE '%경영%' 등으로 검색)",
        "DOUBLE_MAJOR_NAME (복수전공명)",
        "SUB_MAJOR_NM (부전공명)",
        "ADMISSION_DATE (입학년월, YYYYMM 형식)",
        "GRADUATION_DATE (졸업년월, YYYYMM 형식)",
        "SCHOOL_LOCATION_NAME (학교 소재지)",
    ],
    "keywords": ["학력", "학교", "대학", "전공", "졸업", "경영학", "공학", "이학", "학과", "학부", "출신학교", "석사", "박사", "대졸", "고졸", "학위", "부전공", "복수전공", "학력수준"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 학력 수만큼 행 존재, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.4 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 특정 학교 출신 직원** (JOIN 필요)
```
title: 특정 학교 출신 직원 조회
doc_type: query_example
usage_type: rag_action

content:
서울대 출신 직원
고려대 졸업자
:학교명 출신 사원
특정 대학 출신
- V_AI_EMPLOYEE LEFT JOIN V_AI_SCHOLAR
- SCHOOL_NAME LIKE 검색

context_data:
## SQL
```sql
SELECT DISTINCT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.SCHOOL_NAME, b.MAJOR_NAME
FROM v_ai_employee a
LEFT JOIN v_ai_scholar b ON a.EMP_ID = b.EMP_ID
WHERE b.SCHOOL_NAME LIKE '%' || ':학교명' || '%'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LEFT JOIN 필수: 학력 미등록 직원 존재
- DISTINCT: 1인 다건 학력(대학+대학원) → 중복 제거
- LIKE '%학교명%': 학교명 부분 매칭
```

**추가 예제 2: 전공별 직원 분포** (JOIN 필요 — 재직자 필터)
```
title: 전공별 직원 분포 조회
doc_type: query_example
usage_type: rag_action

content:
전공별 직원 수
경영학과 출신 몇 명
공학 전공자 수
전공 분포 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_SCHOLAR
- MAJOR_NAME GROUP BY

context_data:
## SQL
```sql
SELECT b.MAJOR_NAME, COUNT(DISTINCT a.EMP_ID) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_scholar b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.MAJOR_NAME IS NOT NULL
GROUP BY b.MAJOR_NAME
ORDER BY emp_count DESC
FETCH FIRST 20 ROWS ONLY
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- COUNT(DISTINCT EMP_ID): 1인 다건 학력 시 중복 방지
- 특정 전공: WHERE b.MAJOR_NAME LIKE '%경영%'
```

**추가 예제 3: 학력수준별 직원 분포** (JOIN 필요 — EDUCATION_LEVEL 활용)
```
title: 학력수준별 직원 분포 조회
doc_type: query_example
usage_type: rag_action

content:
학력별 직원 수
대졸 직원 몇 명
석사 이상 직원
학력수준 분포
고졸 전문대졸 대졸 비율
- V_AI_EMPLOYEE LEFT JOIN V_AI_SCHOLAR
- EDUCATION_LEVEL GROUP BY

context_data:
## SQL
```sql
SELECT b.EDUCATION_LEVEL, COUNT(DISTINCT a.EMP_ID) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_scholar b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.EDUCATION_LEVEL IS NOT NULL
GROUP BY b.EDUCATION_LEVEL
ORDER BY emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- EDUCATION_LEVEL: 학력수준 (고졸,전문대졸,대졸,석사,박사 등)
- COUNT(DISTINCT EMP_ID): 1인 다건 학력(대학+대학원) → 중복 방지
- 특정 학력: WHERE b.EDUCATION_LEVEL = '대졸' 또는 LIKE '%석사%'
```

**추가 예제 4: 직원 학력 상세 조회** (JOIN 필요)
```
title: 직원 학력 상세 조회
doc_type: query_example
usage_type: rag_action

content:
직원 학력 조회
학력 사항 확인
출신 학교 전공
학력 목록
- V_AI_EMPLOYEE LEFT JOIN V_AI_SCHOLAR
- 1:N 관계 (1인 다건 학력)

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT,
       b.SCHOOL_NAME, b.MAJOR_NAME, b.DOUBLE_MAJOR_NAME,
       b.ADMISSION_DATE, b.GRADUATION_DATE
FROM v_ai_employee a
LEFT JOIN v_ai_scholar b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
ORDER BY a.EMP_NAME, b.ADMISSION_DATE
```

## 핵심 패턴
- LEFT JOIN 필수: 학력 미등록 직원은 NULL로 표시
- 1:N: 한 직원이 대학+대학원 등 여러 학력 보유 가능
- ORDER BY ADMISSION_DATE: 학력 시간순 정렬
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_SCHOLAR 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_SCHOLAR source (개선안 A — PHM_EMP JOIN 제거, 학력수준/졸업구분 추가)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_SCHOLAR" (
    "EMP_ID", "EDUCATION_LEVEL", "GRADUATION_STATUS",
    "MAJOR_NAME", "DOUBLE_MAJOR_NAME",
    "SCHOOL_NAME", "ADMISSION_DATE", "GRADUATION_DATE",
    "SUB_MAJOR_CD", "SUB_MAJOR_NM",
    "SCHOOL_LOCATION_CODE", "SCHOOL_LOCATION_NAME"
) AS
SELECT
    PS.EMP_ID                   AS EMP_ID,
    -- [추가] 학력수준: 고졸/전문대졸/대졸/석사/박사 등 [PHM_SCH_GRD_CD]
    FC_GRD.CD_NM                AS EDUCATION_LEVEL,
    -- [추가] 졸업구분: 졸업/재학/중퇴 등 [PHM_GRAD_CD]
    FC_GRAD.CD_NM               AS GRADUATION_STATUS,
    PS.MAJOR_NM                 AS MAJOR_NAME,
    PS.DOU_MAJOR_NM             AS DOUBLE_MAJOR_NAME,
    FC_SCH.CD_NM                AS SCHOOL_NAME,
    PS.STA_YM                   AS ADMISSION_DATE,
    PS.END_YM                   AS GRADUATION_DATE,
    PS.SUB_MAJOR_CD             AS SUB_MAJOR_CD,
    PS.SUB_MAJOR_NM             AS SUB_MAJOR_NM,
    PS.SCH_PLACE_CD             AS SCHOOL_LOCATION_CODE,
    PS.SCH_PLACE_NM             AS SCHOOL_LOCATION_NAME
FROM PHM_SCHOLAR PS
-- [변경] PHM_EMP JOIN 제거 (POSITION은 V_AI_EMPLOYEE에서 조회)
-- [추가] 학교명
LEFT JOIN FRM_CODE FC_SCH
  ON FC_SCH.CD = PS.SCH_CD
 AND FC_SCH.CD_KIND = 'PHM_SCH_CD'
-- [추가] 학력수준 (고졸/전문대졸/대졸/석사/박사)
LEFT JOIN FRM_CODE FC_GRD
  ON FC_GRD.CD = PS.SCH_GRD_CD
 AND FC_GRD.CD_KIND = 'PHM_SCH_GRD_CD'
-- [추가] 졸업구분 (졸업/재학/중퇴)
LEFT JOIN FRM_CODE FC_GRAD
  ON FC_GRAD.CD = PS.GRAD_CD
 AND FC_GRAD.CD_KIND = 'PHM_GRAD_CD';

GRANT SELECT ON "H552_RND"."V_AI_SCHOLAR" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_SCHOLAR IS '사원 학력 정보 (EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N). 학력 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.EDUCATION_LEVEL IS '학력수준 (고졸,전문대졸,대졸,석사,박사 등)';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.GRADUATION_STATUS IS '졸업구분 (졸업,재학,중퇴 등)';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.MAJOR_NAME IS '전공학과명';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.DOUBLE_MAJOR_NAME IS '복수전공명';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.SCHOOL_NAME IS '학교명';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.ADMISSION_DATE IS '입학년월 (VARCHAR2, YYYYMM 형식)';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.GRADUATION_DATE IS '졸업년월 (VARCHAR2, YYYYMM 형식)';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.SUB_MAJOR_CD IS '부전공 코드';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.SUB_MAJOR_NM IS '부전공명';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.SCHOOL_LOCATION_CODE IS '학교 소재지 코드';
COMMENT ON COLUMN H552_RND.V_AI_SCHOLAR.SCHOOL_LOCATION_NAME IS '학교 소재지명';
```

---

## 6. 검증 계획

```sql
-- 1) 현재 뷰 중복 확인
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp
FROM V_AI_SCHOLAR;

-- 2) 개선 후 중복 제거 확인 (방안 A 기준)
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp
FROM PHM_SCHOLAR;

-- 3) JOIN 정합성 확인
SELECT COUNT(*) FROM (
    SELECT a.EMP_ID
    FROM V_AI_EMPLOYEE a
    LEFT JOIN V_AI_SCHOLAR b ON a.EMP_ID = b.EMP_ID
);
-- 기대: V_AI_EMPLOYEE 건수 이상 (1:N)

-- 4) 학력 미등록 직원 수
SELECT COUNT(*) AS no_scholar_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_SCHOLAR b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **PHM_EMP JOIN 제거** | COMPANY_CD 필터 없어 중복 | POSITION 제거 → PHM_EMP JOIN 불필요 → 중복 자동 해결 | **확정** |
| **POSITION 제거** | 학력과 무관한 현재 직위 | 제거 확정 — 직위는 V_AI_EMPLOYEE에서 조회 | **확정** |
| **카탈로그 컬럼명 불일치** | MAJOR≠MAJOR_NAME 등 3건 | DDL 컬럼명과 동기화 | **확정** |
| **LEFT JOIN 필수** | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| **EDUCATION_LEVEL 추가** | 뷰 미포함 | SCH_GRD_CD → FRM_CODE JOIN으로 학력수준 추가 | **확정** |
| **GRADUATION_STATUS 추가** | 뷰 미포함 | GRAD_CD → FRM_CODE JOIN으로 졸업구분 추가 | **확정** |
| ADMISSION/GRADUATION_DATE 타입 | DATE로 표기 | VARCHAR2(YYYYMM) 형식으로 수정 | **확정** |
| SCH_GRD_CD 값 도메인 | 미확인 | DB 조회로 값 확인 필요 (고졸/대졸/석사/박사 등) | 검증 필요 |
| LAST_YN 최종학력 필터 | 미적용 | WHERE LAST_YN='Y' 추가 여부 검토 | 검증 필요 |
| fewshot 예제 | 없음 | 4건 추가 (학교출신, 전공분포, 학력수준분포, 학력상세) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PHM_EMP 중복 연쇄, POSITION 중복, 카탈로그 불일치, fewshot 추가 |
| 2026-03-17 | PHM_SCHOLAR 원본 DDL 확인: SCH_GRD_CD(학력수준), LAST_YN(최종여부), GRAD_CD(졸업구분) 발견, EDUCATION_LEVEL/GRADUATION_STATUS 컬럼 추가, ADMISSION/GRADUATION_DATE VARCHAR2 형식 수정 |
