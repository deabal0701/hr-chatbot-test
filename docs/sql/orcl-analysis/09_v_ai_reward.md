# V_AI_REWARD 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_REWARD`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PPM_MNT`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조

```
FROM PPM_MNT PM
LEFT JOIN FRM_CODE FC2  (상벌종류: PPM_KIND_CD)
LEFT JOIN FRM_CODE FC3  (상벌구분: PPM_TYPE_CD)
```

**소스**: `PPM_MNT` + FRM_CODE 2개 LEFT JOIN. PHM_EMP 참조 없음. 구조 양호.

> **섹션 5.1에 개선안 DDL** 작성.

---

## 2. PPM_MNT 원본 테이블 분석

### 2.1 테이블 구조

```
PPM_MNT_ID       NUMBER         PK    포상내역관리ID
COMPANY_CD       VARCHAR2(10)   NN    인사영역코드
EMP_ID           NUMBER         FK    사원ID
TYPE_CD          VARCHAR2(10)   NN    상벌구분 → 뷰: REWARD_TYPE
KIND_CD          VARCHAR2(10)   NN    상벌종류코드 → 뷰: REWARD_KIND
INOFF_CD         VARCHAR2(10)         사내구분
PPM_NO           VARCHAR2(50)         상벌번호 → 뷰: REWARD_NO
PPM_YMD          DATE                 상벌일자 → 뷰: REWARD_DATE
PPM_MON          NUMBER(10)           포상금액 → 뷰: REWARD_AMOUNT
PPM_DESC         VARCHAR2(500)        상벌사유 → 뷰: REWARD_REASON
END_YMD          DATE                 종료일
PPM_ORG_NM       VARCHAR2(300)        포상기관 (사용안함) → 뷰: AWARDING_ORG
PRIZE_DESC       VARCHAR2(300)        포상내용 (사용안함) → 뷰: REWARD_CONTENT
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PPM_MNT_ID` | 상벌 ID |
| **UK** | `(EMP_ID, TYPE_CD, KIND_CD, PPM_DESC)` | 사원+구분+종류+사유 = 유일 |
| **INDEX** | `(EMP_ID, TYPE_CD, PPM_YMD)` | |

### 2.3 핵심 발견

1. **STA_YMD/END_YMD 이력 구조 아님** — `END_YMD`는 "종료일"이지만 상벌은 이벤트성 데이터. V_AI_ADDRESS 같은 유효기간 필터 불필요.
2. **REWARD_YEAR**: `SUBSTR(PPM_YMD, 1, 4)` — PPM_YMD는 DATE 타입이므로 **TO_CHAR 필요** (06, 08과 동일 문제).
3. **PPM_ORG_NM, PRIZE_DESC**: 원본에 "사용안함" COMMENT이지만 뷰에서 AWARDING_ORG, REWARD_CONTENT로 노출 중 → 데이터가 대부분 NULL일 가능성.
4. **COMPANY_CD 필터 없음** — PPM_MNT에 COMPANY_CD 존재. PHM_EMP와 동일한 복수 인사영역 이슈 가능. 단, PPM_MNT의 UK에 COMPANY_CD가 없으므로 중복 가능성은 낮음.
5. 샘플: `TYPE_CD='PPM'` → FRM_CODE에서 '포상'으로 변환되는 것으로 추정. '징계' 코드도 존재할 것.
6. **모든 이력이 유의미** — V_AI_CAREER와 동일, WHERE 필터 불필요.

---

## 3. 이슈 분석

### 3.1 REWARD_YEAR SUBSTR 문제 (06, 08과 동일)

```sql
-- 현재: DATE에 SUBSTR
SUBSTR(PM.PPM_YMD, 1, 4) AS REWARD_YEAR

-- 개선: TO_CHAR
TO_CHAR(PM.PPM_YMD, 'YYYY') AS REWARD_YEAR
```

### 3.2 LEFT JOIN 필수 + 1:N

상벌 미등록 직원은 행 없음. 한 직원이 여러 상벌 보유 가능 → 1:N → `COUNT(DISTINCT EMP_ID)` 필수.

### 3.3 카탈로그 누락 컬럼

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| REWARD_YEAR | **X** | 연도별 집계에 유용 → **추가** |
| REWARD_CONTENT | **X** | 원본 "사용안함" → 미등재 적절 |
| AWARDING_ORG | **X** | 원본 "사용안함" → 미등재 적절 |
| REWARD_NO | **X** | 상벌번호 — 활용도 낮음 |

---

## 4. 개선 사항

### 4.1 뷰 개선 (확정)

1. REWARD_YEAR: `SUBSTR` → `TO_CHAR(PPM_YMD, 'YYYY')`

### 4.2 table_catalog.py 반영 코드

```python
"v_ai_reward": {
    "description": "상벌 내역 (1:N, 상벌 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 상벌 미등록 직원은 행 없음)",
        "REWARD_TYPE ★상벌구분 (포상, 징계)",
        "REWARD_KIND (상벌종류)",
        "REWARD_REASON (상벌사유)",
        "REWARD_DATE (상벌일자)",
        "REWARD_YEAR (상벌 연도, YYYY — 연도별 집계 시 사용)",
        "REWARD_AMOUNT (포상금액)",
    ],
    "keywords": ["상벌", "포상", "징계", "표창", "상금", "포상금", "징계이력"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 상벌 건수만큼 행, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.3 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 포상/징계 이력 조회** (JOIN 필요)
```
title: 포상 또는 징계 이력 조회
doc_type: query_example
usage_type: rag_action

content:
포상 받은 직원
징계 이력
상벌 조회
포상 내역
- V_AI_EMPLOYEE LEFT JOIN V_AI_REWARD
- REWARD_TYPE 필터 (포상/징계)

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.REWARD_TYPE, b.REWARD_KIND, b.REWARD_REASON,
       b.REWARD_DATE, b.REWARD_AMOUNT
FROM v_ai_employee a
LEFT JOIN v_ai_reward b ON a.EMP_ID = b.EMP_ID
WHERE b.REWARD_TYPE = ':포상또는징계'
  AND a.WORK_STATUS = '재직'
ORDER BY b.REWARD_DATE DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 상벌 미등록 직원 존재
- REWARD_TYPE: '포상' 또는 '징계'
- 1:N: 동일 직원 여러 상벌 → 직원 수 집계 시 COUNT(DISTINCT EMP_ID)
```

**추가 예제 2: 연도별 포상 현황** (JOIN 필요 — 재직자 필터)
```
title: 연도별 포상 현황 조회
doc_type: query_example
usage_type: rag_action

content:
연도별 포상 건수
올해 포상 받은 직원
:연도 포상 현황
포상 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_REWARD
- REWARD_YEAR 필터 또는 GROUP BY

context_data:
## SQL
```sql
SELECT b.REWARD_YEAR, COUNT(*) AS reward_count,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       SUM(b.REWARD_AMOUNT) AS total_amount
FROM v_ai_employee a
LEFT JOIN v_ai_reward b ON a.EMP_ID = b.EMP_ID
WHERE b.REWARD_TYPE = '포상'
  AND a.WORK_STATUS = '재직'
  AND b.REWARD_YEAR IS NOT NULL
GROUP BY b.REWARD_YEAR
ORDER BY b.REWARD_YEAR DESC
```

## 핵심 패턴
- REWARD_YEAR: 연도별 집계에 사용
- COUNT(*): 포상 건수, COUNT(DISTINCT EMP_ID): 포상 받은 직원 수
- SUM(REWARD_AMOUNT): 포상금 총액
- 특정 연도: WHERE b.REWARD_YEAR = ':연도'
```

**추가 예제 3: 포상 N회 이상 직원** (JOIN 필요)
```
title: 다수 포상 직원 조회
doc_type: query_example
usage_type: rag_action

content:
포상 3회 이상 직원
포상 많이 받은 사람
다수 포상자
포상 횟수별 직원
- V_AI_EMPLOYEE LEFT JOIN V_AI_REWARD
- GROUP BY + HAVING COUNT

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, COUNT(b.EMP_ID) AS reward_count,
       SUM(b.REWARD_AMOUNT) AS total_amount
FROM v_ai_employee a
LEFT JOIN v_ai_reward b ON a.EMP_ID = b.EMP_ID AND b.REWARD_TYPE = '포상'
WHERE a.WORK_STATUS = '재직'
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT
HAVING COUNT(b.EMP_ID) >= :횟수
ORDER BY reward_count DESC
```

## 핵심 패턴
- LEFT JOIN + ON 절에 REWARD_TYPE 조건: 포상만 JOIN
- COUNT(b.EMP_ID): NULL 제외 → 포상 건수만 집계
- SUM(REWARD_AMOUNT): 포상금 총액
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_REWARD 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_REWARD source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_REWARD" (
    "EMP_ID", "REWARD_TYPE", "REWARD_KIND", "REWARD_REASON",
    "REWARD_CONTENT", "REWARD_DATE", "REWARD_YEAR",
    "AWARDING_ORG", "REWARD_AMOUNT", "REWARD_NO"
) AS
SELECT
    PM.EMP_ID                   AS EMP_ID,
    FC3.CD_NM                   AS REWARD_TYPE,
    FC2.CD_NM                   AS REWARD_KIND,
    PM.PPM_DESC                 AS REWARD_REASON,
    PM.PRIZE_DESC               AS REWARD_CONTENT,
    PM.PPM_YMD                  AS REWARD_DATE,
    -- [변경] SUBSTR → TO_CHAR (PPM_YMD는 DATE 타입)
    TO_CHAR(PM.PPM_YMD, 'YYYY') AS REWARD_YEAR,
    PM.PPM_ORG_NM               AS AWARDING_ORG,
    PM.PPM_MON                  AS REWARD_AMOUNT,
    PM.PPM_NO                   AS REWARD_NO
FROM PPM_MNT PM
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PM.KIND_CD AND FC2.CD_KIND = 'PPM_KIND_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PM.TYPE_CD AND FC3.CD_KIND = 'PPM_TYPE_CD';

GRANT SELECT ON "H552_RND"."V_AI_REWARD" TO "MUSER";

-- 테이블 COMMENT (LLM SQL 생성용)
COMMENT ON TABLE H552_RND.V_AI_REWARD IS '사원 상벌 내역 (1:N, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN). 상벌 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT (LLM SQL 생성용)
COMMENT ON COLUMN H552_RND.V_AI_REWARD.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_TYPE IS '상벌 구분 (포상, 징계)';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_KIND IS '상벌 종류 (우수사원상, 근속상 등)';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_REASON IS '상벌 사유';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_CONTENT IS '포상 내용';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_DATE IS '상벌 일자';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_YEAR IS '상벌 연도 (YYYY, 연도별 집계 시 사용)';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.AWARDING_ORG IS '포상 기관';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_AMOUNT IS '포상금액 (원)';
COMMENT ON COLUMN H552_RND.V_AI_REWARD.REWARD_NO IS '상벌번호';
```

### 5.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **REWARD_YEAR** | `SUBSTR(PPM_YMD, 1, 4)` | `TO_CHAR(PPM_YMD, 'YYYY')` | DATE 명시적 변환 |
| COMMENT | 기본 | LEFT JOIN 필수, 값 도메인, 용도 명시 | |

---

## 6. 검증 계획

```sql
-- 1) 뷰 건수 vs 원본 건수
SELECT 'PPM_MNT' AS src, COUNT(*) FROM PPM_MNT
UNION ALL
SELECT 'V_AI_REWARD', COUNT(*) FROM V_AI_REWARD;

-- 2) REWARD_TYPE 값 도메인 확인
SELECT REWARD_TYPE, COUNT(*) AS cnt
FROM V_AI_REWARD
GROUP BY REWARD_TYPE
ORDER BY cnt DESC;

-- 3) 상벌 미등록 직원 수
SELECT COUNT(*) AS no_reward_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_REWARD b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 4) REWARD_YEAR 분포
SELECT REWARD_YEAR, COUNT(*) AS cnt
FROM V_AI_REWARD
WHERE REWARD_YEAR IS NOT NULL
GROUP BY REWARD_YEAR
ORDER BY REWARD_YEAR DESC;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **REWARD_YEAR SUBSTR** | DATE에 SUBSTR | TO_CHAR 명시적 변환 | **확정** |
| LEFT JOIN 필수 | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| 카탈로그 REWARD_YEAR 누락 | 미등재 | 연도별 집계용으로 추가 | **확정** |
| fewshot 예제 | 없음 | 3건 추가 (포상징계, 연도별, 다수포상) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PPM_MNT DDL 분석, SUBSTR 수정, 카탈로그/COMMENT/fewshot 보강 |
