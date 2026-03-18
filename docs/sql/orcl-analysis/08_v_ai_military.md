# V_AI_MILITARY 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_MILITARY`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_ARMY`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조

```
FROM PHM_ARMY PA
LEFT JOIN FRM_CODE x7 (7개 JOIN — 각 코드값 → 한글명 변환)
```

**소스**: `PHM_ARMY` + FRM_CODE 7개 LEFT JOIN. PHM_EMP 참조 없음.

> **섹션 5.1에 개선안 DDL** 작성.

---

## 2. PHM_ARMY 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_ARMY_ID          NUMBER         PK    사원병역ID
EMP_ID               NUMBER         FK    사원ID
PERSON_ID            NUMBER         NN    개인ID
ARMY_SERV_CD         VARCHAR2(50)         복무형태코드 → 뷰: SERVICE_TYPE
ARMY_NO_REASON_CD    VARCHAR2(50)         군필구분코드 → 뷰: SERVICE_STATUS
ARMY_TYPE_CD         VARCHAR2(50)         군별코드 → 뷰: MILITARY_TYPE
ARMY_BRANCH_CD       VARCHAR2(50)         병과코드 → 뷰: MILITARY_BRANCH
ARMY_CLASS_CD        VARCHAR2(50)         계급코드 → 뷰: MILITARY_RANK
ARMY_NO              VARCHAR2(20)         군번 (PII) → 뷰: MILITARY_NO
ARMY_DISCHARGE_CD    VARCHAR2(50)         제대구분코드 → 뷰: DISCHARGE_TYPE
IN_YMD               DATE                 입대일자 → 뷰: 미포함
OUT_YMD              DATE                 전역일자 → 뷰: DISCHARGE_DATE
PLUS_MM              NUMBER(5)            군인정개월수
ARMY_MTALENT_CD      VARCHAR2(50)         주특기코드 → 뷰: SPECIALTY
ARMY_NO_CD           VARCHAR2(300)        미필사유
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_ARMY_ID` | 병역 ID |
| **UK** | `(EMP_ID)` | ★ **1인 1건** 확정 (EMP_ID가 UK) |

### 2.3 핵심 발견

1. **UK가 `(EMP_ID)`** → **1:1 관계 확정**. 카탈로그의 `relation: "1:1"`이 정확.
2. **IN_YMD(입대일자)** 뷰 미포함 — 추가 검토 ("입대일" 질의 가능)
3. **DISCHARGE_YEAR**: `SUBSTR(OUT_YMD, 1, 4)` — OUT_YMD는 DATE 타입이므로 06(LANGUAGE)과 동일한 **암묵적 변환 문제**. `TO_CHAR` 사용 필요.
4. **MILITARY_NO(군번)**: PII — 카탈로그 미등재 적절
5. **FC6 CD_KIND 오타 가능성**: `'PHMARMY_SERV_CD'` — `'PHM_ARMY_SERV_CD'`가 아닌지 확인 필요 (언더스코어 누락). 데이터에서 SERVICE_TYPE이 NULL이면 이것이 원인.
6. **STA_YMD/END_YMD 없음** — 이력 필터 불필요. 1인 1건.

---

## 3. 이슈 분석

### 3.1 DISCHARGE_YEAR SUBSTR 문제 (06과 동일)

```sql
-- 현재: DATE에 SUBSTR (암묵적 변환)
SUBSTR(PA.OUT_YMD, 1, 4) AS DISCHARGE_YEAR

-- 개선: TO_CHAR 명시적 변환
TO_CHAR(PA.OUT_YMD, 'YYYY') AS DISCHARGE_YEAR
```

### 3.2 FC6 CD_KIND 오타 가능성

```sql
-- 현재
FC6.CD_KIND = 'PHMARMY_SERV_CD'   -- ★ PHM_ 뒤에 언더스코어 없음

-- 다른 JOIN들은 모두
FC7.CD_KIND = 'PHM_ARMY_TYPE_CD'   -- PHM_ 패턴
```

**검증 쿼리**:
```sql
-- SERVICE_TYPE NULL 비율 확인
SELECT COUNT(*) AS total,
       SUM(CASE WHEN SERVICE_TYPE IS NULL THEN 1 ELSE 0 END) AS null_count
FROM V_AI_MILITARY;

-- FRM_CODE에 PHMARMY_SERV_CD가 실제 존재하는지
SELECT DISTINCT CD_KIND FROM FRM_CODE WHERE CD_KIND LIKE '%ARMY_SERV%';
```

### 3.3 IN_YMD(입대일자) 뷰 미포함

"입대일" 질의가 가능하도록 추가 검토. 단, NL2SQL에서 "입대일" 질의 빈도는 낮으므로 선택적.

### 3.4 LEFT JOIN 필수

병역 미등록 직원(여성, 면제 등)은 V_AI_MILITARY에 행 없음. **V_AI_EMPLOYEE 기준 LEFT JOIN 필수**.
단, UK가 `(EMP_ID)`이므로 1:1 — `COUNT(DISTINCT EMP_ID)` 불필요.

---

## 4. 개선 사항

### 4.1 뷰 개선 (확정)

1. DISCHARGE_YEAR: `SUBSTR` → `TO_CHAR(OUT_YMD, 'YYYY')`
2. IN_YMD → ENLIST_DATE 추가 (입대일자)
3. FC6 CD_KIND 오타 검증 후 수정

### 4.2 table_catalog.py 반영 코드

```python
"v_ai_military": {
    "description": "병역 정보 (1:1, 병역 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 병역 미등록 직원은 행 없음)",
        "MILITARY_TYPE (군 종류: 육군, 해군, 공군, 해병대 등)",
        "MILITARY_RANK (최종 계급: 병장, 상병 등)",
        "SERVICE_TYPE (복무형태: 현역, 보충역 등)",
        "SERVICE_STATUS (군필 여부: 군필, 미필, 면제 등)",
        "DISCHARGE_TYPE (전역사유)",
        "ENLIST_DATE (입대일자)",
        "DISCHARGE_DATE (전역일자)",
        "DISCHARGE_YEAR (전역 연도, YYYY)",
    ],
    "keywords": ["병역", "군대", "군필", "전역", "군복무", "입대", "면제", "미필", "육군", "해군", "공군"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:1 (1인 1건, 병역 미등록 직원은 행 없음)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.3 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 군필 여부별 직원 수** (JOIN 필요)
```
title: 군필 여부별 직원 수 조회
doc_type: query_example
usage_type: rag_action

content:
군필 직원 수
미필 직원 수
면제 직원 몇 명
군필 여부 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_MILITARY
- SERVICE_STATUS GROUP BY

context_data:
## SQL
```sql
SELECT NVL(b.SERVICE_STATUS, '병역미등록') AS service_status,
       COUNT(*) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_military b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
GROUP BY NVL(b.SERVICE_STATUS, '병역미등록')
ORDER BY emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 여성/면제 등 병역 미등록 직원 존재
- NVL: 병역 미등록 직원은 NULL → '병역미등록'으로 표시
- 1:1 관계: COUNT(DISTINCT) 불필요
```

**추가 예제 2: 특정 군종 출신 직원** (JOIN 필요)
```
title: 특정 군종 출신 직원 조회
doc_type: query_example
usage_type: rag_action

content:
해병대 출신 직원
공군 출신 직원
육군 출신 직원
:군종 출신 사원
- V_AI_EMPLOYEE LEFT JOIN V_AI_MILITARY
- MILITARY_TYPE 필터

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.MILITARY_TYPE, b.MILITARY_RANK, b.DISCHARGE_DATE
FROM v_ai_employee a
LEFT JOIN v_ai_military b ON a.EMP_ID = b.EMP_ID
WHERE b.MILITARY_TYPE = ':군종'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LEFT JOIN: 병역 미등록 직원은 WHERE에서 자연 제외
- MILITARY_TYPE 값: 육군, 해군, 공군, 해병대 등
- 1:1 관계: DISTINCT 불필요
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_MILITARY 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_MILITARY source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_MILITARY" (
    "EMP_ID", "MILITARY_TYPE", "MILITARY_BRANCH", "MILITARY_RANK",
    "SERVICE_TYPE", "SERVICE_STATUS", "DISCHARGE_TYPE",
    "ENLIST_DATE", "DISCHARGE_DATE", "DISCHARGE_YEAR",
    "SPECIALTY", "MILITARY_NO"
) AS
SELECT
    PA.EMP_ID                   AS EMP_ID,
    FC7.CD_NM                   AS MILITARY_TYPE,
    FC1.CD_NM                   AS MILITARY_BRANCH,
    FC2.CD_NM                   AS MILITARY_RANK,
    FC6.CD_NM                   AS SERVICE_TYPE,
    FC5.CD_NM                   AS SERVICE_STATUS,
    FC3.CD_NM                   AS DISCHARGE_TYPE,
    -- [추가] 입대일자
    PA.IN_YMD                   AS ENLIST_DATE,
    PA.OUT_YMD                  AS DISCHARGE_DATE,
    -- [변경] SUBSTR → TO_CHAR (OUT_YMD는 DATE 타입)
    TO_CHAR(PA.OUT_YMD, 'YYYY') AS DISCHARGE_YEAR,
    FC4.CD_NM                   AS SPECIALTY,
    PA.ARMY_NO                  AS MILITARY_NO
FROM PHM_ARMY PA
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PA.ARMY_BRANCH_CD AND FC1.CD_KIND = 'PHM_ARMY_BRANCH_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PA.ARMY_CLASS_CD AND FC2.CD_KIND = 'PHM_ARMY_CLASS_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PA.ARMY_DISCHARGE_CD AND FC3.CD_KIND = 'PHM_ARMY_DISCHARGE_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PA.ARMY_MTALENT_CD AND FC4.CD_KIND = 'PHM_ARMY_MTALENT_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PA.ARMY_NO_REASON_CD AND FC5.CD_KIND = 'PHM_ARMY_NO_REASON_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PA.ARMY_SERV_CD AND FC6.CD_KIND = 'PHMARMY_SERV_CD'
LEFT JOIN FRM_CODE FC7 ON FC7.CD = PA.ARMY_TYPE_CD AND FC7.CD_KIND = 'PHM_ARMY_TYPE_CD';
-- ★ FC6 CD_KIND 'PHMARMY_SERV_CD' 오타 여부 검증 필요 → SERVICE_TYPE이 모두 NULL이면 'PHM_ARMY_SERV_CD'로 수정

GRANT SELECT ON "H552_RND"."V_AI_MILITARY" TO "MUSER";

-- 테이블 COMMENT (LLM SQL 생성용)
COMMENT ON TABLE H552_RND.V_AI_MILITARY IS '사원 병역 정보 (1:1, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN). 병역 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT (LLM SQL 생성용 — 원본 코드 참조 불포함)
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.MILITARY_TYPE IS '군 종류 (육군, 해군, 공군, 해병대 등)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.MILITARY_BRANCH IS '병과';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.MILITARY_RANK IS '최종 계급 (병장, 상병, 하사 등)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.SERVICE_TYPE IS '복무형태 (현역, 보충역, 전환복무 등)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.SERVICE_STATUS IS '군필 여부 (군필, 미필, 면제 등)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.DISCHARGE_TYPE IS '전역사유';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.ENLIST_DATE IS '입대일자';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.DISCHARGE_DATE IS '전역일자';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.DISCHARGE_YEAR IS '전역 연도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.SPECIALTY IS '주특기';
COMMENT ON COLUMN H552_RND.V_AI_MILITARY.MILITARY_NO IS '군번 (PII — NL2SQL에서 직접 조회 지양)';
```

### 5.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **ENLIST_DATE** | 미포함 | IN_YMD → ENLIST_DATE 추가 | **컬럼 추가** |
| **DISCHARGE_YEAR** | `SUBSTR(OUT_YMD, 1, 4)` | `TO_CHAR(OUT_YMD, 'YYYY')` | DATE 명시적 변환 |
| FC6 CD_KIND | `'PHMARMY_SERV_CD'` | 오타 여부 검증 후 수정 | 검증 필요 |
| COMMENT | 기본 | LEFT JOIN 필수, PII 주의, 값 도메인 | |

---

## 6. 검증 계획

```sql
-- 1) 뷰 건수 vs 원본 건수
SELECT 'PHM_ARMY' AS src, COUNT(*) FROM PHM_ARMY
UNION ALL
SELECT 'V_AI_MILITARY', COUNT(*) FROM V_AI_MILITARY;

-- 2) 1:1 확인 (UK가 EMP_ID)
SELECT EMP_ID, COUNT(*) FROM V_AI_MILITARY
GROUP BY EMP_ID HAVING COUNT(*) > 1;
-- 기대: 0건

-- 3) FC6 CD_KIND 오타 확인
SELECT DISTINCT CD_KIND FROM FRM_CODE WHERE CD_KIND LIKE '%ARMY_SERV%';

-- 4) SERVICE_TYPE NULL 비율 (FC6 오타 영향)
SELECT COUNT(*) AS total,
       SUM(CASE WHEN SERVICE_TYPE IS NULL THEN 1 ELSE 0 END) AS null_count
FROM V_AI_MILITARY;

-- 5) 병역 미등록 직원 수
SELECT COUNT(*) AS no_military_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_MILITARY b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **DISCHARGE_YEAR SUBSTR** | DATE에 SUBSTR | TO_CHAR 명시적 변환 | **확정** |
| **ENLIST_DATE 추가** | 뷰 미포함 | IN_YMD → ENLIST_DATE 추가 | **확정** |
| **FC6 CD_KIND 오타** | `'PHMARMY_SERV_CD'` | 검증 후 수정 | **검증 필요** |
| LEFT JOIN 필수 | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| MILITARY_NO PII | 뷰에서 노출 | 카탈로그 미등재 + COMMENT PII 주의 | **확정** |
| fewshot 예제 | 없음 | 2건 추가 (군필여부, 군종출신) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PHM_ARMY DDL 분석, UK(EMP_ID) 1:1 확정, SUBSTR/FC6오타/ENLIST_DATE 이슈, fewshot 2건 |
