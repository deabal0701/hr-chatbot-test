# V_AI_LICENSE 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_LICENSE`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_LICENSE`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조

현재 배포된 뷰의 핵심 구조:

```
FROM PHM_LICENSE PL
LEFT JOIN FRM_CODE FC1  (자격면허코드: PHM_LICENSE_CD → LICENSE_NAME)
LEFT JOIN FRM_CODE FC2  (자격구분코드: PHM_LICENSE_TYPE_CD → LICENSE_TYPE)
+ VALIDITY_STATUS CASE (END_YMD 기반 유효/만료/영구 판단)
```

**소스**: `PHM_LICENSE` + FRM_CODE 2개 LEFT JOIN. PHM_EMP 참조 없음.

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql` 참조. **섹션 5.1에 개선안 DDL** 작성.

---

## 2. PHM_LICENSE 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_LICENSE_ID   NUMBER(22)     PK    사원자격ID
EMP_ID           NUMBER(22)     FK    사원ID
PERSON_ID        NUMBER(22)     NN    개인ID
LICENSE_TYPE_CD  VARCHAR2(10)         자격구분코드 [PHM_LICENSE_TYPE_CD] → 뷰: LICENSE_TYPE
LICENSE_CD       VARCHAR2(50)   NN    자격면허코드 [PHM_LICENSE_CD] → 뷰: LICENSE_NAME
LICENSE_NM       VARCHAR2(300)        자격면허명 (사용안함)
GRADE_CD         VARCHAR2(50)         자격등급코드 (사용안함)
GRADE_NM         VARCHAR2(50)         자격등급명 (사용안함)
STA_YMD          DATE           NN    ★취득일자 → 뷰: ISSUE_DATE
END_YMD          DATE                 ★유효일자 (NULL 가능) → 뷰: EXPIRY_DATE + VALIDITY_STATUS
LICENSE_NO       VARCHAR2(100)        자격면허번호 (PII) → 뷰: LICENSE_NO
REG_YN           CHAR(1)              등록여부
ORG_NM           VARCHAR2(100)        주관처 → 뷰: ISSUING_ORG
BONUS_TYPE       VARCHAR2(10)         수당지급구분 → 뷰: ALLOWANCE_TYPE
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_LICENSE_ID` | 자격 ID |
| **UK** | `(EMP_ID, LICENSE_CD, STA_YMD)` | 사원+자격코드+취득일 = 유일 |
| **INDEX** | `(EMP_ID, STA_YMD, END_YMD, LICENSE_CD)` | |

### 2.3 핵심 발견

1. **STA_YMD는 취득일** (DATE NOT NULL), **END_YMD는 유효일** (DATE, NULL 가능) — V_AI_ADDRESS처럼 이력 필터가 아닌 **자격증 유효기간**
2. 샘플: `END_YMD=2999-12-31` → "영구 유효" 패턴 (V_AI_ADDRESS와 동일)
3. **VALIDITY_STATUS**: 뷰에서 `END_YMD` 기반 CASE로 유효/만료/영구 판단 — 그런데 `END_YMD`는 DATE 타입인데 뷰에서 **REGEXP_LIKE, TO_CHAR 비교** 사용 → **타입 오류 가능성**
4. **LICENSE_NO**: PII (자격증 번호) — 뷰에서 노출 중
5. 자격증은 **이력 전체가 유의미** (보유 자격증 목록) → WHERE 필터 불필요 (V_AI_CAREER와 동일 패턴)

### 2.4 VALIDITY_STATUS 타입 문제 — 확정된 버그

```sql
-- 현재 뷰 (orcl-business_view_db.sql:468-472)
CASE
    WHEN PL.END_YMD IS NOT NULL AND REGEXP_LIKE(PL.END_YMD, '^\d{8}$') ...  -- ★ DATE에 REGEXP_LIKE
    WHEN PL.END_YMD < TO_CHAR(SYSDATE, 'YYYYMMDD') ...                       -- ★ DATE < VARCHAR2
```

`PHM_LICENSE.END_YMD`는 **DATE 타입**인데:
- `REGEXP_LIKE(PL.END_YMD, '^\d{8}$')`: DATE에 정규식 매칭 → Oracle 암묵적 TO_CHAR 변환 (NLS_DATE_FORMAT 의존)
- `PL.END_YMD < TO_CHAR(SYSDATE, 'YYYYMMDD')`: DATE < VARCHAR2 비교 → 암묵적 변환

**수정**: DATE 타입에 맞는 비교로 변경:
```sql
CASE
    WHEN PL.END_YMD IS NULL THEN '영구'
    WHEN PL.END_YMD < SYSDATE THEN '만료'
    WHEN PL.END_YMD >= SYSDATE THEN '유효'
    ELSE '확인필요'
END AS VALIDITY_STATUS
```

---

## 3. 이슈 분석

### 3.1 VALIDITY_STATUS 타입 오류 — 확정

DATE 타입에 REGEXP_LIKE, TO_CHAR 비교 사용 → 단순 DATE 비교로 수정 필요.

### 3.2 LICENSE_NO — PII 노출

자격증 번호는 개인정보이나, NL2SQL에서 직접 질의할 가능성 낮음. 카탈로그 미등재로 대응 (현행 유지).

### 3.3 LEFT JOIN 필수 + 1:N

자격증 미등록 직원은 행 없음. 한 직원이 여러 자격증 보유 가능 → 1:N.

### 3.4 자격증은 이력 전체 필요

V_AI_CAREER와 동일 — "보유 자격증 목록"이므로 WHERE 필터 불필요. 모든 자격증이 유의미.

---

## 4. 개선 사항

### 4.1 뷰 개선 (확정)

1. VALIDITY_STATUS: REGEXP_LIKE/TO_CHAR → DATE 비교로 수정
2. COMMENT 보강

### 4.2 table_catalog.py 반영 코드

```python
"v_ai_license": {
    "description": "자격증/면허 보유 현황 (1:N — 보유 자격증 수만큼 행, 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 자격증 미등록 직원은 행 없음)",
        "LICENSE_TYPE (자격구분: 국가자격,민간자격 등 [PHM_LICENSE_TYPE_CD])",
        "LICENSE_NAME ★자격증명 [PHM_LICENSE_CD]",
        "ISSUING_ORG (발급/주관기관)",
        "ISSUE_DATE (취득일, DATE NOT NULL)",
        "EXPIRY_DATE (유효만료일, DATE — NULL이면 영구)",
        "VALIDITY_STATUS ★유효상태 (유효,만료,영구)",
    ],
    "keywords": ["자격증", "자격", "면허", "취득", "보유", "국가자격", "민간자격", "유효", "만료"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 보유 자격증 수만큼 행, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.3 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 특정 자격증 보유 직원** (JOIN 필요)
```
title: 특정 자격증 보유 직원 조회
doc_type: query_example
usage_type: rag_action

content:
자격증 보유 직원
워드프로세서 자격증
:자격증명 보유자
특정 자격 보유
- V_AI_EMPLOYEE LEFT JOIN V_AI_LICENSE
- LICENSE_NAME LIKE 검색

context_data:
## SQL
```sql
SELECT DISTINCT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.LICENSE_NAME, b.ISSUE_DATE, b.VALIDITY_STATUS
FROM v_ai_employee a
LEFT JOIN v_ai_license b ON a.EMP_ID = b.EMP_ID
WHERE b.LICENSE_NAME LIKE '%' || ':자격증명' || '%'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LEFT JOIN 필수: 자격증 미등록 직원 존재
- LIKE '%자격증명%': 자격증명 부분 매칭
- VALIDITY_STATUS = '유효': 유효한 자격증만 필터 가능
```

**추가 예제 2: 자격증 보유 현황 통계** (JOIN 필요 — 재직자 필터)
```
title: 자격증 보유 현황 통계
doc_type: query_example
usage_type: rag_action

content:
자격증 보유 직원 수
자격증별 보유자 수
자격증 통계
보유 자격증 종류별 인원
- V_AI_EMPLOYEE LEFT JOIN V_AI_LICENSE
- LICENSE_NAME GROUP BY

context_data:
## SQL
```sql
SELECT b.LICENSE_NAME, COUNT(DISTINCT a.EMP_ID) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_license b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.LICENSE_NAME IS NOT NULL
GROUP BY b.LICENSE_NAME
ORDER BY emp_count DESC
FETCH FIRST 20 ROWS ONLY
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- COUNT(DISTINCT EMP_ID): 동일 자격증 갱신 이력 → 중복 방지
- 유효 자격증만: AND b.VALIDITY_STATUS = '유효' 추가
```

**추가 예제 3: 자격증 N개 이상 보유자** (JOIN 필요)
```
title: 다수 자격증 보유자 조회
doc_type: query_example
usage_type: rag_action

content:
자격증 3개 이상 보유 직원
자격증 많은 사람
다수 자격증 보유자
자격증 개수별 직원
- V_AI_EMPLOYEE LEFT JOIN V_AI_LICENSE
- GROUP BY + HAVING COUNT

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, COUNT(b.EMP_ID) AS license_count
FROM v_ai_employee a
LEFT JOIN v_ai_license b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT
HAVING COUNT(b.EMP_ID) >= :개수
ORDER BY license_count DESC
```

## 핵심 패턴
- LEFT JOIN: 자격증 없는 직원은 license_count=0
- COUNT(b.EMP_ID): NULL 제외 → 자격증 수만 집계
- 유효 자격증만: ON 절에 b.VALIDITY_STATUS = '유효' 추가
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_LICENSE 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_LICENSE source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_LICENSE" (
    "EMP_ID", "LICENSE_TYPE", "LICENSE_NAME", "LICENSE_NO",
    "ISSUING_ORG", "ISSUE_DATE", "EXPIRY_DATE",
    "VALIDITY_STATUS", "ALLOWANCE_TYPE"
) AS
SELECT
    PL.EMP_ID                   AS EMP_ID,
    FC2.CD_NM                   AS LICENSE_TYPE,
    FC1.CD_NM                   AS LICENSE_NAME,
    PL.LICENSE_NO               AS LICENSE_NO,
    PL.ORG_NM                   AS ISSUING_ORG,
    PL.STA_YMD                  AS ISSUE_DATE,
    PL.END_YMD                  AS EXPIRY_DATE,
    -- [변경] VALIDITY_STATUS: REGEXP_LIKE/TO_CHAR → 단순 DATE 비교
    CASE
        WHEN PL.END_YMD IS NULL THEN '영구'
        WHEN PL.END_YMD < SYSDATE THEN '만료'
        WHEN PL.END_YMD >= SYSDATE THEN '유효'
        ELSE '확인필요'
    END                         AS VALIDITY_STATUS,
    PL.BONUS_TYPE               AS ALLOWANCE_TYPE
FROM PHM_LICENSE PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.LICENSE_CD AND FC1.CD_KIND = 'PHM_LICENSE_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.LICENSE_TYPE_CD AND FC2.CD_KIND = 'PHM_LICENSE_TYPE_CD';

GRANT SELECT ON "H552_RND"."V_AI_LICENSE" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_LICENSE IS '사원 자격증/면허 보유 현황 (EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N). 자격증 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.LICENSE_TYPE IS '자격 구분 (국가자격,민간자격 등)';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.LICENSE_NAME IS '자격증명';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.LICENSE_NO IS '자격증 번호 (PII — NL2SQL에서 직접 조회 지양)';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.ISSUING_ORG IS '발급/주관기관';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.ISSUE_DATE IS '취득일자 (DATE, NOT NULL)';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.EXPIRY_DATE IS '유효만료일 (DATE, NULL=영구)';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.VALIDITY_STATUS IS '유효 상태 (유효,만료,영구) — EXPIRY_DATE 기반 자동 산출';
COMMENT ON COLUMN H552_RND.V_AI_LICENSE.ALLOWANCE_TYPE IS '수당지급구분 (NL2SQL 미사용)';
```

### 5.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **VALIDITY_STATUS** | REGEXP_LIKE + TO_CHAR 비교 (DATE에 부적절) | 단순 DATE 비교 (`END_YMD < SYSDATE`) | **버그 수정** |
| LICENSE_NO COMMENT | `'자격증 번호'` | PII 주의 추가 | |
| TABLE COMMENT | 기본 | LEFT JOIN 필수 + 미등록 직원 명시 | |

---

## 6. 검증 계획

```sql
-- 1) 뷰 건수 vs 원본 건수 (FRM_CODE 곱집합 확인)
SELECT 'PHM_LICENSE' AS src, COUNT(*) FROM PHM_LICENSE
UNION ALL
SELECT 'V_AI_LICENSE', COUNT(*) FROM V_AI_LICENSE;

-- 2) VALIDITY_STATUS 분포 확인
SELECT VALIDITY_STATUS, COUNT(*) AS cnt
FROM V_AI_LICENSE
GROUP BY VALIDITY_STATUS
ORDER BY cnt DESC;

-- 3) 자격증 미등록 직원 수
SELECT COUNT(*) AS no_license_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_LICENSE b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 4) LICENSE_TYPE 값 도메인 확인
SELECT LICENSE_TYPE, COUNT(*) AS cnt
FROM V_AI_LICENSE
WHERE LICENSE_TYPE IS NOT NULL
GROUP BY LICENSE_TYPE
ORDER BY cnt DESC;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **VALIDITY_STATUS 타입 오류** | DATE에 REGEXP_LIKE/TO_CHAR 사용 | 단순 DATE 비교로 수정 | **확정 (버그)** |
| LEFT JOIN 필수 | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| LICENSE_NO PII | 뷰에서 노출 | 카탈로그 미등재 + COMMENT에 PII 주의 | **확정** |
| fewshot 예제 | 없음 | 3건 추가 (특정자격, 보유통계, 다수보유) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PHM_LICENSE 원본 DDL 분석, VALIDITY_STATUS 타입 버그 확정, fewshot 3건 |
