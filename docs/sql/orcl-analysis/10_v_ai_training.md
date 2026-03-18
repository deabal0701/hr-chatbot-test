# V_AI_TRAINING 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_TRAINING`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_EDU`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조

```
FROM PHM_EDU PED
LEFT JOIN FRM_CODE x6 (6개 JOIN — 각 코드값 → 한글명 변환)
+ COMPLETION_STATUS CASE (Y→수료, N→미수료)
```

**소스**: `PHM_EDU` + FRM_CODE 6개 LEFT JOIN. PHM_EMP 참조 없음. 구조 양호.

> **섹션 5.1에 개선안 DDL** 작성.

---

## 2. PHM_EDU 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_EDU_ID       NUMBER         PK    교육ID
EMP_ID           NUMBER         FK    사원ID
EDU_YY           VARCHAR2(4)    NN    교육년도 → 뷰: TRAINING_YEAR
EDU_TYPE_CD      VARCHAR2(10)   NN    교육유형 → 뷰: TRAINING_TYPE (FC6)
EDU_KIND_CD      VARCHAR2(10)   NN    교육분야 → 뷰: COURSE_FIELD (FC3)
EDU_PLA_CD       VARCHAR2(10)   NN    교육장소 → 뷰: TRAINING_LOCATION (FC5)
EDU_CD           VARCHAR2(10)         교육과정코드 → 뷰: COURSE_TYPE (FC1)
EDU_NM           VARCHAR2(200)  NN    교육과정명 → 뷰: COURSE_NAME
STA_YMD          DATE           NN    교육시작일 → 뷰: START_DATE
END_YMD          DATE           NN    교육종료일 → 뷰: END_DATE
EDU_ORG_CD       VARCHAR2(10)         교육기관코드 → 뷰: INSTITUTION_TYPE (FC4)
EDU_ORG_NM       VARCHAR2(200)        교육기관명 → 뷰: INSTITUTION_NAME
RESULT_YN        CHAR(1)        NN    이수여부 (Y/N) → 뷰: COMPLETION_STATUS
RESULT_PNT       NUMBER(8,3)          이수포인트 → 뷰: COMPLETION_POINTS
RESULT_TIMES     NUMBER(8,3)          이수시간 → 뷰: COMPLETION_HOURS
APPL_AMT         NUMBER(10)           교육비
RETURN_AMT       NUMBER(10)           환급비 → 뷰: REFUND_AMOUNT
REAL_AMT         NUMBER(10)           실교육비 → 뷰: TRAINING_COST
EDU_GRD_CD       VARCHAR2(10)         교육등급코드 → 뷰: COURSE_GRADE (FC2)
PRE_REPORT_YN    CHAR(1)              사전신고여부
...
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_EDU_ID` | 교육 ID |
| **UK** | `(EMP_ID, STA_YMD, EDU_NM, EDU_ORG_NM)` | 사원+시작일+과정명+기관 = 유일 |

### 2.3 핵심 발견

1. **STA_YMD/END_YMD**: DATE NOT NULL — 교육 시작/종료일. 이력 필터 불필요 (모든 교육 이력이 유의미).
2. **구조 양호** — PHM_EMP 참조 없음, FRM_CODE 6개 JOIN 모두 정상.
3. **카탈로그 누락 심각** — 17개 뷰 컬럼 중 8개만 카탈로그에 등재. COURSE_TYPE, COURSE_GRADE, COURSE_FIELD, TRAINING_LOCATION, TRAINING_TYPE, INSTITUTION_TYPE, COMPLETION_POINTS, COMPLETION_HOURS, REFUND_AMOUNT 미등재.
4. **APPL_AMT(교육비)**: 뷰 미포함. REAL_AMT(실교육비)만 TRAINING_COST로 노출 — 의미 차이 확인 필요.
5. 샘플: `RESULT_YN='Y'`, `RESULT_PNT=0`, `RESULT_TIMES=24`, `REAL_AMT=69371` — 이수시간/비용 데이터 잘 채워져 있음.

---

## 3. 이슈 분석

### 3.1 카탈로그 누락 심각

| DDL 컬럼 | 카탈로그 등재 | NL2SQL 활용도 |
|----------|:----------:|:----------:|
| TRAINING_YEAR | O | 높음 — 연도별 집계 |
| COURSE_TYPE | **X** | 중간 — 교육과정 유형 |
| COURSE_GRADE | **X** | 낮음 — 교육등급 |
| COURSE_FIELD | **X** | 중간 — 교육분야 |
| COURSE_NAME | O | 높음 — 과정명 검색 |
| INSTITUTION_TYPE | **X** | 낮음 |
| INSTITUTION_NAME | O | 중간 |
| TRAINING_LOCATION | **X** | 낮음 |
| TRAINING_TYPE | **X** | 중간 — 교육유형 |
| START_DATE | O | 중간 |
| END_DATE | O | 중간 |
| TRAINING_COST | O | 중간 — 비용 집계 |
| COMPLETION_POINTS | **X** | 낮음 |
| COMPLETION_HOURS | **X** | 중간 — 이수시간 집계 |
| COMPLETION_STATUS | O | 높음 — 수료 필터 |
| REFUND_AMOUNT | **X** | 낮음 |

**추가 대상**: COURSE_FIELD, TRAINING_TYPE, COMPLETION_HOURS (NL2SQL 활용도 중간 이상)

### 3.2 LEFT JOIN 필수 + 1:N

교육 미등록 직원은 행 없음. 한 직원이 여러 교육 이수 가능 → 1:N → `COUNT(DISTINCT EMP_ID)` 필수.

### 3.3 DDL 변경 없음

뷰 DDL 자체에는 문제 없음. COMMENT와 카탈로그 보강만 필요.

---

## 4. 개선 사항

### 4.1 뷰 개선 — DDL 변경 없음

현재 뷰 구조 양호. COMMENT만 보강.

### 4.2 table_catalog.py 반영 코드

```python
"v_ai_training": {
    "description": "교육/연수 이수 내역 (1:N, 교육 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 교육 미등록 직원은 행 없음)",
        "TRAINING_YEAR (교육년도, YYYY)",
        "COURSE_NAME ★교육과정명 (LIKE '%과정명%'으로 검색)",
        "COURSE_FIELD (교육분야)",
        "TRAINING_TYPE (교육유형: 집합교육, 사이버교육 등)",
        "INSTITUTION_NAME (교육기관명)",
        "START_DATE (교육시작일)",
        "END_DATE (교육종료일)",
        "TRAINING_COST (실교육비, 원)",
        "COMPLETION_HOURS (이수시간)",
        "COMPLETION_STATUS ★수료여부 (수료, 미수료)",
    ],
    "keywords": ["교육", "훈련", "연수", "수료", "과정", "이수", "교육비", "교육시간", "연수원"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 교육 이수 건수만큼 행, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 4.3 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 교육 이수 현황** (JOIN 필요 — 재직자 필터)
```
title: 교육 이수 현황 조회
doc_type: query_example
usage_type: rag_action

content:
교육 이수 현황
수료 직원 수
교육 받은 직원
연수 현황
- V_AI_EMPLOYEE LEFT JOIN V_AI_TRAINING
- COMPLETION_STATUS 필터

context_data:
## SQL
```sql
SELECT b.TRAINING_YEAR,
       COUNT(*) AS training_count,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       SUM(b.COMPLETION_HOURS) AS total_hours
FROM v_ai_employee a
LEFT JOIN v_ai_training b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.COMPLETION_STATUS = '수료'
  AND b.TRAINING_YEAR IS NOT NULL
GROUP BY b.TRAINING_YEAR
ORDER BY b.TRAINING_YEAR DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 교육 미등록 직원 존재
- COMPLETION_STATUS = '수료': 수료한 교육만
- COUNT(*): 교육 건수, COUNT(DISTINCT EMP_ID): 교육 이수 직원 수
- SUM(COMPLETION_HOURS): 총 이수시간
```

**추가 예제 2: 특정 교육과정 이수자** (JOIN 필요)
```
title: 특정 교육과정 이수자 조회
doc_type: query_example
usage_type: rag_action

content:
:과정명 이수자
특정 교육 수료자
교육 과정 이수 직원
리더십 교육 받은 사람
- V_AI_EMPLOYEE LEFT JOIN V_AI_TRAINING
- COURSE_NAME LIKE 검색

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.COURSE_NAME, b.START_DATE, b.COMPLETION_STATUS
FROM v_ai_employee a
LEFT JOIN v_ai_training b ON a.EMP_ID = b.EMP_ID
WHERE b.COURSE_NAME LIKE '%' || ':과정명' || '%'
  AND a.WORK_STATUS = '재직'
ORDER BY b.START_DATE DESC
```

## 핵심 패턴
- LIKE '%과정명%': 과정명 부분 매칭
- 수료자만: AND b.COMPLETION_STATUS = '수료' 추가
- 1:N: 동일 과정 재수강 시 복수 행 가능
```

**추가 예제 3: 교육비 통계** (JOIN 필요 — 재직자 필터)
```
title: 교육비 통계 조회
doc_type: query_example
usage_type: rag_action

content:
교육비 총액
부서별 교육비
직원당 교육비
교육 비용 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_TRAINING
- TRAINING_COST 집계

context_data:
## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       COUNT(*) AS training_count,
       SUM(b.TRAINING_COST) AS total_cost,
       ROUND(SUM(b.TRAINING_COST) / NULLIF(COUNT(DISTINCT a.EMP_ID), 0)) AS cost_per_emp
FROM v_ai_employee a
LEFT JOIN v_ai_training b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.TRAINING_COST IS NOT NULL
GROUP BY a.DEPARTMENT
ORDER BY total_cost DESC
```

## 핵심 패턴
- SUM(TRAINING_COST): 교육비 총액
- cost_per_emp: 직원당 교육비 (NULLIF로 0 나누기 방지)
- 연도별: WHERE b.TRAINING_YEAR = ':연도' 추가
```

---

## 5. 수정 SQL 전문

### 5.1 V_AI_TRAINING 뷰 생성 스크립트 (DDL 변경 없음, COMMENT 보강)

```sql
-- H552_RND.V_AI_TRAINING source (개선안 — DDL 변경 없음, COMMENT 보강)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_TRAINING" (
    "EMP_ID", "TRAINING_YEAR", "COURSE_TYPE", "COURSE_GRADE",
    "COURSE_FIELD", "COURSE_NAME", "INSTITUTION_TYPE", "INSTITUTION_NAME",
    "TRAINING_LOCATION", "TRAINING_TYPE", "START_DATE", "END_DATE",
    "TRAINING_COST", "COMPLETION_POINTS", "COMPLETION_HOURS",
    "COMPLETION_STATUS", "REFUND_AMOUNT"
) AS
SELECT
    PED.EMP_ID                  AS EMP_ID,
    PED.EDU_YY                  AS TRAINING_YEAR,
    FC1.CD_NM                   AS COURSE_TYPE,
    FC2.CD_NM                   AS COURSE_GRADE,
    FC3.CD_NM                   AS COURSE_FIELD,
    PED.EDU_NM                  AS COURSE_NAME,
    FC4.CD_NM                   AS INSTITUTION_TYPE,
    PED.EDU_ORG_NM              AS INSTITUTION_NAME,
    FC5.CD_NM                   AS TRAINING_LOCATION,
    FC6.CD_NM                   AS TRAINING_TYPE,
    PED.STA_YMD                 AS START_DATE,
    PED.END_YMD                 AS END_DATE,
    PED.REAL_AMT                AS TRAINING_COST,
    PED.RESULT_PNT              AS COMPLETION_POINTS,
    PED.RESULT_TIMES            AS COMPLETION_HOURS,
    CASE PED.RESULT_YN
        WHEN 'Y' THEN '수료'
        WHEN 'N' THEN '미수료'
        ELSE PED.RESULT_YN
    END                         AS COMPLETION_STATUS,
    PED.RETURN_AMT              AS REFUND_AMOUNT
FROM PHM_EDU PED
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PED.EDU_CD AND FC1.CD_KIND = 'PHM_EDU_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PED.EDU_GRD_CD AND FC2.CD_KIND = 'PHM_EDU_GRD_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PED.EDU_KIND_CD AND FC3.CD_KIND = 'PHM_EDU_KIND_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PED.EDU_ORG_CD AND FC4.CD_KIND = 'PHM_EDU_ORG_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PED.EDU_PLA_CD AND FC5.CD_KIND = 'PHM_EDU_PLA_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PED.EDU_TYPE_CD AND FC6.CD_KIND = 'PHM_EDU_TYPE_CD';

GRANT SELECT ON "H552_RND"."V_AI_TRAINING" TO "MUSER";

-- 테이블 COMMENT (LLM SQL 생성용)
COMMENT ON TABLE H552_RND.V_AI_TRAINING IS '사원 교육/연수 이수 내역 (1:N, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN). 교육 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT (LLM SQL 생성용)
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.TRAINING_YEAR IS '교육 실시 연도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COURSE_TYPE IS '교육과정 유형';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COURSE_GRADE IS '교육등급';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COURSE_FIELD IS '교육분야';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COURSE_NAME IS '교육과정명';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.INSTITUTION_TYPE IS '교육기관 유형';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.INSTITUTION_NAME IS '교육기관명';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.TRAINING_LOCATION IS '교육장소';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.TRAINING_TYPE IS '교육유형 (집합교육, 사이버교육 등)';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.START_DATE IS '교육 시작일';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.END_DATE IS '교육 종료일';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.TRAINING_COST IS '실교육비 (원)';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COMPLETION_POINTS IS '이수 포인트';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COMPLETION_HOURS IS '이수 시간';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.COMPLETION_STATUS IS '수료 여부 (수료, 미수료)';
COMMENT ON COLUMN H552_RND.V_AI_TRAINING.REFUND_AMOUNT IS '환급금액 (원)';
```

### 5.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| 뷰 DDL | 동일 | **동일** (구조 변경 없음) | |
| TABLE COMMENT | `'사원 교육/연수 이수 내역 (..., 1:N)'` | LEFT JOIN 필수 + 미등록 직원 명시 | |
| COURSE_TYPE/FIELD 등 COMMENT | (없음) | 누락 컬럼 COMMENT 전부 추가 | **7개 신규** |
| TRAINING_TYPE COMMENT | (없음) | `'교육유형 (집합교육, 사이버교육 등)'` | |

---

## 6. 검증 계획

```sql
-- 1) 뷰 건수 vs 원본 건수
SELECT 'PHM_EDU' AS src, COUNT(*) FROM PHM_EDU
UNION ALL
SELECT 'V_AI_TRAINING', COUNT(*) FROM V_AI_TRAINING;

-- 2) 교육 미등록 직원 수
SELECT COUNT(*) AS no_training_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_TRAINING b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 3) COMPLETION_STATUS 분포
SELECT COMPLETION_STATUS, COUNT(*) AS cnt
FROM V_AI_TRAINING
GROUP BY COMPLETION_STATUS;

-- 4) TRAINING_TYPE 값 도메인 확인
SELECT TRAINING_TYPE, COUNT(*) AS cnt
FROM V_AI_TRAINING
WHERE TRAINING_TYPE IS NOT NULL
GROUP BY TRAINING_TYPE
ORDER BY cnt DESC;

-- 5) COURSE_FIELD 값 도메인 확인
SELECT COURSE_FIELD, COUNT(*) AS cnt
FROM V_AI_TRAINING
WHERE COURSE_FIELD IS NOT NULL
GROUP BY COURSE_FIELD
ORDER BY cnt DESC;
```

---

## 7. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| 뷰 DDL | 구조 양호 | **변경 없음** | - |
| **카탈로그 누락** | 17개 중 8개만 등재 | COURSE_FIELD, TRAINING_TYPE, COMPLETION_HOURS 추가 | **확정** |
| LEFT JOIN 필수 | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| COMMENT 누락 | 7개 컬럼 COMMENT 없음 | 전 컬럼 COMMENT 추가 | **확정** |
| fewshot 예제 | 없음 | 3건 추가 (이수현황, 특정과정, 교육비) | **확정** |

---

## 8. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: PHM_EDU DDL 분석, DDL 변경 없음, 카탈로그/COMMENT 대폭 보강, fewshot 3건 |
