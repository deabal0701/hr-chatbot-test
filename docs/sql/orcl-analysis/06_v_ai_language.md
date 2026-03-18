# V_AI_LANGUAGE 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_LANGUAGE`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_LANG_EST`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음)

현재 배포된 뷰의 핵심 구조:

```
FROM PHM_LANG_EST PL
LEFT JOIN FRM_CODE FC1  (어학종류: PHM_LANG_CD)
LEFT JOIN FRM_CODE FC2  (시험종류: PHM_EST_CD)
LEFT JOIN FRM_CODE FC3  (★dead JOIN: REM_LANG_LEVEL_CD — SELECT에서 미사용)
LEFT JOIN FRM_CODE FC4  (평가기관: PHM_EST_ORG_CD)
```

**문제**: FC3 JOIN이 SELECT에서 사용되지 않는 dead JOIN.

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql` 참조. **섹션 5.1에 개선안 DDL** 작성.

---

## 2. PHM_LANG_EST 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_LANG_EST_ID  NUMBER         PK    사원어학평가ID
EMP_ID           NUMBER         FK    사원ID
PERSON_ID        NUMBER         NN    개인ID
LANG_CD          VARCHAR2(50)   NN    어학코드 [PHM_LANG_CD] → 뷰: LANGUAGE_TYPE
STD_YY           VARCHAR2(4)    NN    년도 → 뷰: EVALUATION_YEAR
STD_SEQ          NUMBER(1)      NN    차수 → 뷰: EVALUATION_SEQ
EST_YMD          DATE                 평가일자 (사용안함) → 뷰: EXAM_DATE
VALID_YMD        DATE                 유효일자 (사용안함)
EST_CD           VARCHAR2(50)   NN    어학구분코드 [PHM_EST_CD] → 뷰: EXAM_TYPE
EST_ORG_CD       VARCHAR2(10)         평가기관코드 [PHM_EST_ORG_CD] → 뷰: EXAM_INSTITUTION
EST_ORG_NM       VARCHAR2(100)        평가기관명
READ_PNT         NUMBER(4)            독해점수 (사용안함)
LISTEN_PNT       NUMBER(4)            청취점수 (사용안함)
EST_PNT          NUMBER(6,2)   NN    어학점수 → 뷰: SCORE
EST_GRD_CD       VARCHAR2(50)         어학등급코드 [PHM_EST_GRD_CD] → 뷰: EVAL_METHOD (★코드 직접 노출)
INTERNAL_PNT     NUMBER(4)            Present Level
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_LANG_EST_ID` | 어학평가 ID |
| **UK** | `(EMP_ID, LANG_CD, STD_YY, STD_SEQ)` | 사원+어학종류+년도+차수 = 유일 |
| **INDEX** | `(EMP_ID, EST_YMD, LANG_CD)` | |

### 2.3 핵심 발견

1. **STA_YMD/END_YMD 없음** — V_AI_ADDRESS/FAMILY와 달리 이력 필터 불필요. 어학 시험은 **모든 이력이 유의미** (TOEIC 2020년 750점, 2023년 850점 등).
2. **dead JOIN**: FC3(`REM_LANG_LEVEL_CD`)은 SELECT에서 미사용 → 제거
3. **EVAL_METHOD 코드 직접 노출**: `PL.EST_GRD_CD`를 그대로 노출. FRM_CODE(`PHM_EST_GRD_CD`) JOIN으로 한글명 변환 필요.
4. **EST_YMD COMMENT "사용안함"** — 그러나 뷰에서 EXAM_DATE, EXAM_YEAR로 사용 중. SUBSTR로 연도 추출하는데 DATE 타입이므로 SUBSTR 불가 → **뷰에 오류 가능성** (EST_YMD가 DATE인데 SUBSTR 적용).
5. 샘플: `EST_YMD=NULL` (대부분 NULL), `EST_PNT=215, 750, 340, 550` → 점수는 잘 채워져 있음.

### 2.4 EXAM_DATE/EXAM_YEAR 타입 문제

```sql
-- 현재 뷰
PL.EST_YMD              AS EXAM_DATE,      -- DATE 타입
SUBSTR(PL.EST_YMD, 1, 4) AS EXAM_YEAR,    -- ★ DATE에 SUBSTR → Oracle 암묵적 변환
```

`EST_YMD`는 DATE 타입이므로 SUBSTR 적용 시 Oracle이 암묵적으로 TO_CHAR 변환하나, NLS_DATE_FORMAT에 의존. `TO_CHAR(PL.EST_YMD, 'YYYY')`로 명시적 변환 필요. 단, COMMENT에 "사용안함"이고 샘플 데이터가 모두 NULL이므로 실질적 영향은 낮음.

---

## 3. 이슈 분석

### 3.1 dead JOIN (FC3) — 확정된 문제

```sql
-- 현재: FC3은 SELECT에서 사용되지 않음
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PL.EST_ORG_CD AND FC3.CD_KIND = 'REM_LANG_LEVEL_CD'
```

제거해도 결과에 영향 없음. 불필요한 JOIN 비용만 발생.

### 3.2 EVAL_METHOD 코드 직접 노출

```sql
-- 현재: 코드값 직접 노출
PL.EST_GRD_CD AS LANGUAGE_GRADE   -- 예: '10' (코드값, 의미 불명)

-- 개선: FRM_CODE JOIN + 컬럼명 변경
FC_GRD.CD_NM AS EVAL_METHOD       -- 예: '점수' (평가방식 명확)
```

### 3.3 LEFT JOIN 필수 + 1:N 관계

어학 성적 미등록 직원은 V_AI_LANGUAGE에 행 없음. 또한 한 직원이 여러 어학 시험(영어+일본어, 또는 TOEIC 여러 회차) 보유 가능 → 1:N.

---

## 4. 개선 사항

### 4.1 뷰 개선 (확정)

1. dead JOIN(FC3) 제거
2. EVAL_METHOD: `EST_GRD_CD` → FRM_CODE(`PHM_EST_GRD_CD`) JOIN으로 한글명 변환
3. EXAM_YEAR: `SUBSTR` → `TO_CHAR(EST_YMD, 'YYYY')` 명시적 변환

### 4.2 table_catalog.py 반영 코드

```python
"v_ai_language": {
    "description": "어학 시험 성적 (1:N — 어학종류+년도+차수별 복수 이력, 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 어학 미등록 직원은 행 없음)",
        "LANGUAGE_TYPE ★어학종류 (영어,일본어,중국어 등 [PHM_LANG_CD])",
        "EXAM_TYPE ★시험종류 (TOEIC,TOEFL,JLPT 등 [PHM_EST_CD])",
        "EXAM_INSTITUTION (평가기관 [PHM_EST_ORG_CD])",
        "SCORE ★시험점수 (NUMBER, NOT NULL)",
        "EVAL_METHOD (평가유형: 점수/등급 — 실제 어학 실력은 SCORE 사용)",
        "EVALUATION_YEAR (평가년도, VARCHAR2(4))",
        "EVALUATION_SEQ (평가차수)",
    ],
    "keywords": ["어학", "토익", "TOEIC", "토플", "TOEFL", "JLPT", "영어", "일본어", "중국어", "점수", "어학성적", "시험"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 어학종류/년도/차수별, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.3 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 토익 점수 기준 직원 조회** (JOIN 필요)
```
title: 토익 점수 기준 직원 조회
doc_type: query_example
usage_type: rag_action

content:
토익 800점 이상 직원
TOEIC 점수 높은 사람
영어 성적 우수자
토익 점수 조회
- V_AI_EMPLOYEE LEFT JOIN V_AI_LANGUAGE
- EXAM_TYPE + SCORE 필터

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.SCORE, b.EVALUATION_YEAR
FROM v_ai_employee a
LEFT JOIN v_ai_language b ON a.EMP_ID = b.EMP_ID
WHERE b.EXAM_TYPE = 'TOEIC'
  AND b.SCORE >= :점수
  AND a.WORK_STATUS = '재직'
ORDER BY b.SCORE DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 어학 미등록 직원 존재
- EXAM_TYPE: 시험종류 필터 (TOEIC, TOEFL, JLPT 등)
- SCORE: 어학 실력의 핵심 지표 (EVAL_METHOD는 평가유형일 뿐, 점수/등급 여부를 나타냄)
- 1:N: 동일 시험 여러 회차 → 최고점만 필요 시 서브쿼리 MAX 사용
```

**추가 예제 2: 어학 보유 직원 수 통계** (JOIN 필요 — 재직자 필터)
```
title: 어학 보유 직원 통계
doc_type: query_example
usage_type: rag_action

content:
어학 시험 보유 직원 수
토익 응시자 수
어학 종류별 직원 분포
영어 시험 본 직원 몇 명
- V_AI_EMPLOYEE LEFT JOIN V_AI_LANGUAGE
- LANGUAGE_TYPE 또는 EXAM_TYPE GROUP BY

context_data:
## SQL
```sql
SELECT b.EXAM_TYPE, COUNT(DISTINCT a.EMP_ID) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_language b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.EXAM_TYPE IS NOT NULL
GROUP BY b.EXAM_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- COUNT(DISTINCT EMP_ID): 1인 다건(여러 회차) → 중복 방지
- 어학 종류별: GROUP BY b.LANGUAGE_TYPE
- 주의: EVAL_METHOD는 '점수'/'등급' 등 평가유형이므로 필터 조건으로 부적합, SCORE 사용
```

**추가 예제 3: 직원 최고 토익 점수** (JOIN 필요)
```
title: 직원별 최고 토익 점수 조회
doc_type: query_example
usage_type: rag_action

content:
직원별 최고 토익 점수
토익 최고점
직원 토익 베스트 스코어
TOEIC 최고 성적
- V_AI_EMPLOYEE LEFT JOIN V_AI_LANGUAGE
- MAX(SCORE) 집계

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, MAX(b.SCORE) AS best_score
FROM v_ai_employee a
LEFT JOIN v_ai_language b ON a.EMP_ID = b.EMP_ID AND b.EXAM_TYPE = 'TOEIC'
WHERE a.WORK_STATUS = '재직'
  AND b.SCORE IS NOT NULL
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT
ORDER BY best_score DESC
```

## 핵심 패턴
- LEFT JOIN + ON 절에 EXAM_TYPE 조건: 특정 시험만 JOIN
- MAX(SCORE): 여러 회차 중 최고점 (SCORE가 어학 실력의 핵심 지표)
- 평균 점수: AVG(b.SCORE)
- 주의: EVAL_METHOD는 평가유형(점수/등급)이지 실제 등급이 아님
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_LANGUAGE 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_LANGUAGE source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_LANGUAGE" (
    "EMP_ID", "LANGUAGE_TYPE", "EXAM_TYPE", "EXAM_INSTITUTION",
    "SCORE", "EVAL_METHOD", "EXAM_DATE", "EXAM_YEAR",
    "EVALUATION_YEAR", "EVALUATION_SEQ"
) AS
SELECT
    PL.EMP_ID                   AS EMP_ID,
    FC1.CD_NM                   AS LANGUAGE_TYPE,
    FC2.CD_NM                   AS EXAM_TYPE,
    FC4.CD_NM                   AS EXAM_INSTITUTION,
    PL.EST_PNT                  AS SCORE,
    -- [변경] 평가유형 (점수=점수기반, 등급=등급기반) — 실제 어학 실력은 SCORE 컬럼
    FC_GRD.CD_NM                AS EVAL_METHOD,
    PL.EST_YMD                  AS EXAM_DATE,
    -- [변경] SUBSTR → TO_CHAR 명시적 변환 (EST_YMD는 DATE 타입)
    TO_CHAR(PL.EST_YMD, 'YYYY') AS EXAM_YEAR,
    PL.STD_YY                   AS EVALUATION_YEAR,
    PL.STD_SEQ                  AS EVALUATION_SEQ
FROM PHM_LANG_EST PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.LANG_CD AND FC1.CD_KIND = 'PHM_LANG_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.EST_CD AND FC2.CD_KIND = 'PHM_EST_CD'
-- [삭제] dead JOIN FC3 제거 (REM_LANG_LEVEL_CD — SELECT 미사용)
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PL.EST_ORG_CD AND FC4.CD_KIND = 'PHM_EST_ORG_CD'
-- [추가] 어학등급 코드 → 한글명 변환
LEFT JOIN FRM_CODE FC_GRD ON FC_GRD.CD = PL.EST_GRD_CD AND FC_GRD.CD_KIND = 'PHM_EST_GRD_CD';

GRANT SELECT ON "H552_RND"."V_AI_LANGUAGE" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_LANGUAGE IS '사원 어학 시험 성적 (EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N — 어학종류/년도/차수별 이력). 어학 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT (LLM SQL 생성용 — 원본 테이블/코드 종류 불필요)
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.LANGUAGE_TYPE IS '어학 종류 (영어, 일본어, 중국어 등)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EXAM_TYPE IS '시험 종류 (TOEIC, TOEFL, JLPT 등)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EXAM_INSTITUTION IS '평가기관';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.SCORE IS '어학 시험 점수 (어학 실력의 핵심 지표)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EVAL_METHOD IS '평가유형 (점수, 등급) — 실력 비교는 SCORE 컬럼 사용';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EXAM_DATE IS '시험 응시일';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EXAM_YEAR IS '시험 응시 연도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EVALUATION_YEAR IS '평가 기준년도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_LANGUAGE.EVALUATION_SEQ IS '평가 차수';
```

### 5.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **dead JOIN FC3** | `REM_LANG_LEVEL_CD` JOIN 존재 | **제거** | SELECT 미사용 |
| **LANGUAGE_GRADE → EVAL_METHOD** | `PL.EST_GRD_CD` 코드 직접 노출 | 컬럼명 변경 + `FC_GRD.CD_NM` 한글명(점수/등급) | **컬럼명+값 변경** |
| **EXAM_YEAR** | `SUBSTR(EST_YMD, 1, 4)` | `TO_CHAR(EST_YMD, 'YYYY')` | DATE 타입 명시적 변환 |

---

## 6. 검증 계획

```sql
-- 1) 뷰 건수 vs 원본 건수 (FRM_CODE 곱집합 확인)
SELECT 'PHM_LANG_EST' AS src, COUNT(*) FROM PHM_LANG_EST
UNION ALL
SELECT 'V_AI_LANGUAGE', COUNT(*) FROM V_AI_LANGUAGE;

-- 2) EVAL_METHOD 변환 확인
SELECT EVAL_METHOD, COUNT(*) AS cnt
FROM V_AI_LANGUAGE
WHERE EVAL_METHOD IS NOT NULL
GROUP BY EVAL_METHOD
ORDER BY cnt DESC;

-- 3) 어학 미등록 직원 수
SELECT COUNT(*) AS no_lang_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_LANGUAGE b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **dead JOIN FC3** | SELECT 미사용 JOIN 존재 | 제거 | **확정** |
| **EVAL_METHOD 코드 노출** | EST_GRD_CD 직접 노출 | FRM_CODE JOIN 한글명 변환 | **확정** |
| **EXAM_YEAR SUBSTR** | DATE에 SUBSTR (암묵적 변환) | TO_CHAR 명시적 변환 | **확정** |
| LEFT JOIN 필수 | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| fewshot 예제 | 없음 | 3건 추가 (토익점수, 어학통계, 최고점수) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PHM_LANG_EST 원본 DDL 분석, dead JOIN/코드노출/SUBSTR 이슈 확정, fewshot 3건 |
