# V_AI_FAMILY 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_FAMILY`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_FAMILY`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조

현재 배포된 뷰의 핵심 구조:

```
FROM PHM_FAMILY PF
LEFT JOIN FRM_CODE FC_REL  (가족관계 코드 → 한글명)
LEFT JOIN FRM_CODE FC_GEN  (성별 코드 → 한글명)
LEFT JOIN FRM_CODE FC_HAN  (장애등급 코드 → 한글명)
```

**소스**: `PHM_FAMILY` + FRM_CODE 3개 LEFT JOIN. PHM_EMP 참조 없음.
**구조**: 양호. PHM_EMP 중복 문제 해당 없음.

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql` 참조. **섹션 6.1에 개선안 DDL** 작성.

---

## 2. PHM_FAMILY 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_FAMILY_ID    NUMBER(22)     PK    사원가족ID
EMP_ID           NUMBER(22)     FK    사원ID
PERSON_ID        NUMBER(22)     NN    개인ID
FAM_CTZ_NO       VARCHAR2(100)  NN    가족주민번호 (PII — 뷰 미노출, 정상)
FAM_LAST_NM      VARCHAR2(40)   NN    가족성명(성)
FAM_FIRST_NM     VARCHAR2(40)         가족성명(이름) → 뷰: FAMILY_NAME
FAM_REL_CD       VARCHAR2(50)   NN    가족관계코드 [PHM_FAM_REL_CD] → 뷰: RELATION
SCH_GRD_CD       VARCHAR2(10)         학력코드 [PHM_SCH_GRD_CD]
SCH_NM           VARCHAR2(40)         학교명 → 뷰: FAMILY_SCHOOL
BIRTH_YMD        VARCHAR2(8)          생년월일 (★VARCHAR2, DATE 아님) → 뷰: FAMILY_BIRTH_DATE
GENDER_CD        VARCHAR2(10)         성별코드 [PHM_GENDER_CD] → 뷰: FAMILY_GENDER
SPOUSE_YN        CHAR(1)              배우자유무
SUPPORT_YN       CHAR(1)              부양자여부
HANICAP_YN       CHAR(1)              장애자여부 → 뷰: DISABILITY_STATUS
HANDICAP_GRD_CD  VARCHAR2(10)         장애등급코드 [PHM_HANDICAP_GRD_CD] → 뷰: DISABILITY_GRADE
TOGETHER_YN      VARCHAR2(1)          동거여부
COMPANY_NM       VARCHAR2(40)         직장명 → 뷰: FAMILY_COMPANY
POSITION_NM      VARCHAR2(60)         직위명 → 뷰: FAMILY_POSITION
STA_YMD          DATE           NN    ★시작일자
END_YMD          DATE           NN    ★종료일자
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_FAMILY_ID` | 가족 ID |
| **UK** | `(EMP_ID, FAM_CTZ_NO, STA_YMD)` | 사원 + 가족주민번호 + 시작일 = 유일 |
| **INDEX** | `(EMP_ID, STA_YMD, END_YMD, FAM_CTZ_NO)` | 유효기간 검색 최적화 |

### 2.3 핵심 발견 — STA_YMD/END_YMD 이력 구조 (V_AI_ADDRESS와 동일 패턴)

**UK**: `(EMP_ID, FAM_CTZ_NO, STA_YMD)` → 동일 가족에 대해 **시기별 이력** 관리 가능

**샘플 데이터**: `STA_YMD=2018-06-12, END_YMD=2999-12-31` → V_AI_ADDRESS와 동일한 "현재 유효" 패턴

**문제**: 현재 뷰에 `STA_YMD`/`END_YMD` 필터가 없으므로, 과거 가족관계(이혼 전 배우자, 사망한 가족 등)도 포함될 수 있음 → **자녀 수, 부양가족 수 집계 시 과다 집계 위험**

**수정 방향**: V_AI_ADDRESS와 동일하게 WHERE 필터 추가
```sql
WHERE PF.STA_YMD <= SYSDATE
  AND PF.END_YMD >= SYSDATE
```

### 2.4 BIRTH_YMD — VARCHAR2(8) 타입

원본에서 `BIRTH_YMD`는 **VARCHAR2(8)** (예: '19950101')이며 DATE 타입이 아님. 뷰 COMMENT에 타입을 정확히 명시해야 함.

---

## 3. 이슈 분석

### 3.1 STA_YMD/END_YMD 필터 부재 — 확정된 문제

V_AI_ADDRESS(02)와 동일한 구조적 문제:
- PHM_FAMILY에 `STA_YMD`/`END_YMD` (DATE NOT NULL) 존재
- 현재 뷰에 WHERE 필터 없음 → 과거 가족관계도 포함

**NL2SQL 영향**:

| 질의 | 기대 | 실제 (현재) |
|------|------|------------|
| "자녀 2명 이상 직원" | 현재 자녀 수 | **과거 가족 포함 → 과다 집계 가능** |
| "배우자 있는 직원" | 현재 배우자 | **이혼 전 배우자도 포함 가능** |

### 3.2 구조적 이슈 — PHM_EMP 참조 없음 (양호)

- PHM_EMP 참조 없음 → COMPANY_CD 중복 영향 없음
- FRM_CODE JOIN 3개 모두 LEFT JOIN → 코드 미매칭 시 NULL (안전)
- DISABILITY_STATUS CASE 변환 정상 (Y→장애있음, N→장애없음)

### 2.2 LEFT JOIN 필수

가족 미등록 직원은 V_AI_FAMILY에 행이 없으므로, **반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 필수**.

또한 1:N 관계 (한 직원에 배우자, 자녀, 부모 등 여러 가족 등록 가능) → 직원 수 집계 시 `COUNT(DISTINCT EMP_ID)` 필수.

### 2.3 카탈로그 누락 컬럼

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| EMP_ID | O (FK) | |
| RELATION | O | 값 도메인 미기재 → 보강 필요 |
| FAMILY_NAME | O | PII 주의 |
| FAMILY_GENDER | O | |
| FAMILY_BIRTH_DATE | **X** | 가족 생년월일 — PII, 미등재 적절 |
| FAMILY_COMPANY | **X** | 가족 근무회사 — 활용도 낮음 |
| FAMILY_POSITION | **X** | 가족 직위 — 활용도 낮음 |
| FAMILY_SCHOOL | **X** | 가족 출신학교 — 활용도 낮음 |
| DISABILITY_STATUS | O | 값: 장애있음/장애없음 |
| DISABILITY_GRADE | **X** | 장애등급 — 추가 검토 |

### 2.4 RELATION 값 도메인

카탈로그에 `(가족관계: 배우자,자녀,부모)`로 간략히 기재되어 있으나, FRM_CODE `PHM_FAM_REL_CD`의 실제 값 도메인을 확인하여 보강 필요.

**확인 필요 쿼리**:
```sql
SELECT DISTINCT FC_REL.CD_NM AS relation_name
FROM PHM_FAMILY PF
LEFT JOIN FRM_CODE FC_REL ON PF.FAM_REL_CD = FC_REL.CD AND FC_REL.CD_KIND = 'PHM_FAM_REL_CD'
WHERE FC_REL.CD_NM IS NOT NULL
ORDER BY relation_name;
```

### 2.5 저채움률 컬럼

`FAMILY_COMPANY`, `FAMILY_POSITION`, `FAMILY_SCHOOL`은 채움률이 매우 낮을 가능성이 높음 (가족의 직장/학교 정보를 HR 시스템에 입력하는 경우가 드묾). 카탈로그 미등재가 적절.

### 2.6 FAMILY_NAME — PII

가족 이름은 개인정보이므로 NL2SQL에서 직접 SELECT 지양. 카탈로그에는 등재하되, COMMENT에 PII 주의를 명시.

---

## 3. 개선 사항

### 3.1 뷰 개선 — WHERE 필터 추가 (확정)

V_AI_ADDRESS(02)와 동일하게 현재 유효한 가족관계만 필터:

```sql
WHERE PF.STA_YMD <= SYSDATE
  AND PF.END_YMD >= SYSDATE
```

### 3.2 카탈로그 개선 (확정)

```python
# 현재
"v_ai_family": {
    "description": "가족 관계 정보",
    "columns": [
        "EMP_ID (FK)",
        "RELATION (가족관계: 배우자,자녀,부모)",
        "FAMILY_NAME (가족 이름)",
        "FAMILY_GENDER (가족 성별)",
        "DISABILITY_STATUS (장애여부)",
    ],
    "keywords": ["가족", "배우자", "자녀", "부모", "부양"],
    ...
}

# 변경
"v_ai_family": {
    "description": "사원 가족 구성원 정보 (1:N, 가족 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 가족 미등록 직원은 행 없음)",
        "RELATION ★가족관계 (배우자,자녀,부,모,형제,자매 등 [PHM_FAM_REL_CD])",
        "FAMILY_NAME (가족 이름, PII)",
        "FAMILY_GENDER (가족 성별: 남,여)",
        "DISABILITY_STATUS (장애여부: 장애있음,장애없음)",
        "DISABILITY_GRADE (장애등급)",
    ],
    "keywords": ["가족", "배우자", "자녀", "부모", "부양", "가족수", "자녀수", "장애", "부양가족"],
    ...
}
```

### 3.3 table_catalog.py 반영 코드

```python
"v_ai_family": {
    "description": "사원 가족 구성원 정보 (1:N, 가족 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 가족 미등록 직원은 행 없음)",
        "RELATION ★가족관계 (배우자,자녀,부,모,형제,자매 등 [PHM_FAM_REL_CD])",
        "FAMILY_NAME (가족 이름, PII — NL2SQL에서 직접 조회 지양)",
        "FAMILY_GENDER (가족 성별: 남,여)",
        "DISABILITY_STATUS (장애여부: 장애있음,장애없음)",
        "DISABILITY_GRADE (장애등급)",
    ],
    "keywords": ["가족", "배우자", "자녀", "부모", "부양", "가족수", "자녀수", "장애", "부양가족"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 가족 수만큼 행 존재, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 3.4 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 자녀 수 기준 직원 조회** (JOIN 필요 — 재직자 필터)
```
title: 자녀 수 기준 직원 조회
doc_type: query_example
usage_type: rag_action

content:
자녀 2명 이상 직원
자녀수별 직원 분포
다자녀 직원 목록
자녀가 있는 직원
- V_AI_EMPLOYEE LEFT JOIN V_AI_FAMILY
- RELATION = '자녀' 필터 후 COUNT

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, COUNT(b.EMP_ID) AS child_count
FROM v_ai_employee a
LEFT JOIN v_ai_family b ON a.EMP_ID = b.EMP_ID AND b.RELATION = '자녀'
WHERE a.WORK_STATUS = '재직'
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT
HAVING COUNT(b.EMP_ID) >= :자녀수
ORDER BY child_count DESC
```

## 핵심 패턴
- LEFT JOIN + ON 절에 RELATION 조건: '자녀'만 JOIN (WHERE 대신 ON 사용 → 자녀 없는 직원도 포함)
- COUNT(b.EMP_ID): NULL 제외 → 자녀 수만 집계
- :자녀수=0 이면 HAVING 제거 → 전체 직원 자녀 수 조회
```

**추가 예제 2: 가족 구성 현황** (JOIN 필요 — 재직자 필터)
```
title: 가족관계별 등록 현황 조회
doc_type: query_example
usage_type: rag_action

content:
가족관계별 현황
배우자 있는 직원 수
부양가족 통계
가족 구성 분포
- V_AI_EMPLOYEE LEFT JOIN V_AI_FAMILY
- RELATION GROUP BY

context_data:
## SQL
```sql
SELECT b.RELATION, COUNT(DISTINCT a.EMP_ID) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_family b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.RELATION IS NOT NULL
GROUP BY b.RELATION
ORDER BY emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 가족 미등록 직원 존재
- COUNT(DISTINCT EMP_ID): 1인 다건 가족 → 직원 수 기준 집계
- 배우자 유무: WHERE b.RELATION = '배우자' → COUNT(DISTINCT a.EMP_ID)
```

**추가 예제 3: 장애 가족이 있는 직원** (JOIN 필요)
```
title: 장애 가족 보유 직원 조회
doc_type: query_example
usage_type: rag_action

content:
장애 가족이 있는 직원
장애인 가족 보유자
가족 중 장애인
장애 부양가족
- V_AI_EMPLOYEE LEFT JOIN V_AI_FAMILY
- DISABILITY_STATUS 필터

context_data:
## SQL
```sql
SELECT DISTINCT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.RELATION, b.DISABILITY_STATUS, b.DISABILITY_GRADE
FROM v_ai_employee a
LEFT JOIN v_ai_family b ON a.EMP_ID = b.EMP_ID
WHERE b.DISABILITY_STATUS = '장애있음'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LEFT JOIN: 가족 미등록 직원은 WHERE에서 자연 제외
- DISABILITY_STATUS = '장애있음': 장애 가족만 필터
- DISTINCT: 장애 가족이 여러 명이면 직원 중복 방지
```

---

## 4. 수정 SQL 전문

### 4.1 V_AI_FAMILY 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_FAMILY source (개선안 — STA_YMD/END_YMD 유효기간 필터 추가)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_FAMILY" (
    "EMP_ID", "RELATION", "FAMILY_NAME", "FAMILY_GENDER",
    "FAMILY_BIRTH_DATE", "FAMILY_COMPANY", "FAMILY_POSITION",
    "FAMILY_SCHOOL", "DISABILITY_STATUS", "DISABILITY_GRADE"
) AS
SELECT
    PF.EMP_ID                   AS EMP_ID,
    FC_REL.CD_NM                AS RELATION,
    PF.FAM_FIRST_NM             AS FAMILY_NAME,
    FC_GEN.CD_NM                AS FAMILY_GENDER,
    PF.BIRTH_YMD                AS FAMILY_BIRTH_DATE,
    PF.COMPANY_NM               AS FAMILY_COMPANY,
    PF.POSITION_NM              AS FAMILY_POSITION,
    PF.SCH_NM                   AS FAMILY_SCHOOL,
    CASE PF.HANICAP_YN
        WHEN 'Y' THEN '장애있음'
        WHEN 'N' THEN '장애없음'
        ELSE PF.HANICAP_YN
    END                         AS DISABILITY_STATUS,
    FC_HAN.CD_NM                AS DISABILITY_GRADE
FROM PHM_FAMILY PF
LEFT JOIN FRM_CODE FC_REL ON PF.FAM_REL_CD = FC_REL.CD AND FC_REL.CD_KIND = 'PHM_FAM_REL_CD'
LEFT JOIN FRM_CODE FC_GEN ON PF.GENDER_CD = FC_GEN.CD AND FC_GEN.CD_KIND = 'PHM_GENDER_CD'
LEFT JOIN FRM_CODE FC_HAN ON PF.HANDICAP_GRD_CD = FC_HAN.CD AND FC_HAN.CD_KIND = 'PHM_HANDICAP_GRD_CD'
-- [추가] 현재 유효한 가족관계만 (과거 가족관계 제외)
WHERE PF.STA_YMD <= SYSDATE
  AND PF.END_YMD >= SYSDATE;

GRANT SELECT ON "H552_RND"."V_AI_FAMILY" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_FAMILY IS '사원 현재 가족 구성원 (현재 유효 기간만 필터, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N). 가족 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.RELATION IS '가족 관계 (배우자,자녀,부,모,형제,자매 등)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_NAME IS '가족 구성원 이름 (PII — NL2SQL에서 직접 조회 지양)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_GENDER IS '가족 성별 (남,여)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_BIRTH_DATE IS '가족 생년월일 (PII — NL2SQL에서 직접 조회 지양)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_COMPANY IS '가족 근무회사 (채움률 낮음 — NL2SQL 미사용)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_POSITION IS '가족 근무회사 직위 (채움률 낮음 — NL2SQL 미사용)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.FAMILY_SCHOOL IS '가족 출신학교 (채움률 낮음 — NL2SQL 미사용)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.DISABILITY_STATUS IS '장애 여부 (장애있음,장애없음)';
COMMENT ON COLUMN H552_RND.V_AI_FAMILY.DISABILITY_GRADE IS '장애등급';
```

### 4.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| 뷰 DDL | 동일 | **동일** (구조 변경 없음) | |
| TABLE COMMENT | `'사원 가족 구성원 (..., 1:N)'` | LEFT JOIN 필수 + 가족 미등록 직원 미포함 명시 | |
| FAMILY_NAME COMMENT | `'가족 구성원 이름'` | PII 주의 추가 | |
| FAMILY_BIRTH_DATE COMMENT | `'가족 생년월일'` | PII 주의 추가 | |
| FAMILY_COMPANY COMMENT | `'가족 근무회사'` | 채움률 낮음 + NL2SQL 미사용 명시 | |
| DISABILITY_GRADE COMMENT | (없음) | **신규** — 장애등급 코드 출처 명시 | |

---

## 5. 검증 계획

```sql
-- 1) 전체 건수 + 1인 평균 가족 수
SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT EMP_ID) AS distinct_emp,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT EMP_ID), 1) AS avg_family_per_emp
FROM V_AI_FAMILY;

-- 2) RELATION 값 도메인 확인
SELECT RELATION, COUNT(*) AS cnt
FROM V_AI_FAMILY
WHERE RELATION IS NOT NULL
GROUP BY RELATION
ORDER BY cnt DESC;

-- 3) 가족 미등록 직원 수
SELECT COUNT(*) AS no_family_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_FAMILY b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 4) 저채움률 컬럼 확인
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN FAMILY_COMPANY IS NOT NULL THEN 1 ELSE 0 END) AS has_company,
    SUM(CASE WHEN FAMILY_POSITION IS NOT NULL THEN 1 ELSE 0 END) AS has_position,
    SUM(CASE WHEN FAMILY_SCHOOL IS NOT NULL THEN 1 ELSE 0 END) AS has_school,
    SUM(CASE WHEN DISABILITY_GRADE IS NOT NULL THEN 1 ELSE 0 END) AS has_disability_grade
FROM V_AI_FAMILY;

-- 5) JOIN 정합성 확인
SELECT COUNT(*) FROM (
    SELECT a.EMP_ID
    FROM V_AI_EMPLOYEE a
    LEFT JOIN V_AI_FAMILY b ON a.EMP_ID = b.EMP_ID
);
```

---

## 6. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **STA/END_YMD 필터 추가** | 과거 가족관계 포함 | WHERE 필터 추가 (현재 유효만) | **확정** |
| **LEFT JOIN 필수** | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| RELATION 값 도메인 | `(배우자,자녀,부모)` 간략 | DB 조회로 전체 값 확인 후 보강 | 검증 필요 |
| 카탈로그 누락 | DISABILITY_GRADE 미등재 | DISABILITY_GRADE 추가 | **확정** |
| 저채움률 컬럼 | 미확인 | FAMILY_COMPANY/POSITION/SCHOOL 채움률 확인 | 검증 필요 |
| PII 주의 | 미명시 | FAMILY_NAME, FAMILY_BIRTH_DATE에 PII 주의 | **확정** |
| COMMENT 보강 | 기본 수준 | LEFT JOIN 필수, PII, 채움률, 코드 출처 | **확정** |
| fewshot 예제 | 없음 | 3건 추가 (자녀수, 가족관계 현황, 장애가족) | **확정** |

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: 뷰 구조 분석, 카탈로그/COMMENT 보강, fewshot 3건 추가 |
| 2026-03-17 | PHM_FAMILY 원본 DDL 확인: STA_YMD/END_YMD 이력 구조 발견, WHERE 필터 추가 확정, BIRTH_YMD VARCHAR2 타입 수정 |
