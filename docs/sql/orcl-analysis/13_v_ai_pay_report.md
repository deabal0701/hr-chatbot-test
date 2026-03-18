# V_AI_PAY_REPORT 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_PAY_REPORT`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음 — FC5 CD_KIND 매핑 오류 + 컬럼명 불일치)

현재 배포된 뷰의 핵심 구조:

```
FROM PAY_REPORT PR
LEFT JOIN FRM_CODE FC1 (PAY_TYPE_CD — 급여지급구분)
LEFT JOIN FRM_CODE FC2 (PAY_SALARY_TYPE_CD — 급여유형)
LEFT JOIN FRM_CODE FC3 (PAY_POS_GRD_CD — 급여직급)
LEFT JOIN FRM_CODE FC4 (PRM_POS_GRD_CD — 직급)      ← PRM 오타?
LEFT JOIN FRM_CODE FC5 (PHM_ARMY_MTALENT_CD — ★★ 군 특기 코드!! 오류)
LEFT JOIN FRM_CODE FC6 (PHM_POS_CD — 직위)
```

**PK 구조** (COMMENT에서 확인): `(EMP_ID, PAY_YEAR_MONTH, PAYMENT_TYPE_NAME)`

**급여 계산 구조** (COMMENT에서 확인):
```
지급합계(GROSS) = 고정비(FIXED) + 변동비(VARIABLE)
총공제액(TOTAL_DEDUCTION) = 공제합계(DEDUCTION) + 세금합계(TAX)
실지급액(NET) = 지급합계(GROSS) - 총공제액(TOTAL_DEDUCTION)
```

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql:534-597` 참조.

---

## 2. 이슈 분석

### 2.1 FC5 CD_KIND 매핑 오류 — 확정

```sql
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PR.ACC_CD AND FC5.CD_KIND = 'PHM_ARMY_MTALENT_CD'
```

**문제**: `PR.ACC_CD`(계정코드/코스트센터)를 `PHM_ARMY_MTALENT_CD`(군 특기 코드)로 조회.

- `PHM_ARMY_MTALENT_CD`는 병역 정보(V_AI_MILITARY)에서 사용하는 군 특기 코드
- `ACC_CD`는 급여 계정 코드로, 군 특기와는 **완전히 무관**
- COMMENT에도 `ACCOUNT_TYPE_NAME IS '코스트센터'`로 명시 → 군 특기 코드가 아닌 계정/코스트센터 코드여야 함

**영향**: `ACCOUNT_TYPE_NAME` 컬럼이:
- 우연히 매칭되면 군 특기 명칭이 반환됨 (잘못된 데이터)
- 매칭 실패하면 NULL (데이터 손실)

**확인 필요 쿼리**:
```sql
-- 1) 현재 ACCOUNT_TYPE_NAME 실제 값 확인 (오류 영향 진단)
SELECT FC5.CD_NM AS account_type_name, COUNT(*)
FROM PAY_REPORT PR
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PR.ACC_CD AND FC5.CD_KIND = 'PHM_ARMY_MTALENT_CD'
GROUP BY FC5.CD_NM
ORDER BY COUNT(*) DESC
FETCH FIRST 10 ROWS ONLY;

-- 2) ACC_CD가 실제 어떤 코드체계에 속하는지 탐색
SELECT DISTINCT FC.CD_KIND
FROM FRM_CODE FC
WHERE FC.CD IN (SELECT DISTINCT ACC_CD FROM PAY_REPORT WHERE ACC_CD IS NOT NULL)
ORDER BY FC.CD_KIND;

-- 3) ACC_CD 원본값 확인
SELECT ACC_CD, COUNT(*) FROM PAY_REPORT
WHERE ACC_CD IS NOT NULL
GROUP BY ACC_CD ORDER BY COUNT(*) DESC
FETCH FIRST 20 ROWS ONLY;
```

**수정 방향**: DB 조회 결과에 따라:
- 올바른 CD_KIND를 찾으면 → 교체
- 매칭되는 CD_KIND가 없으면 → FC5 JOIN 제거 + ACCOUNT_TYPE_NAME 컬럼 제거 (또는 원본 코드값 유지)

### 2.2 FC4 CD_KIND 오타 가능성 — 확인 필요

```sql
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PR.POS_GRD_CD AND FC4.CD_KIND = 'PRM_POS_GRD_CD'
```

- V_AI_EMPLOYEE에서는 동일 의미의 직급 코드에 `PHM_POS_GRD_CD` 사용
- `PRM_POS_GRD_CD`는 `PHM_POS_GRD_CD`의 오타이거나, 급여 전용 직급 코드체계일 수 있음

**확인 필요 쿼리**:
```sql
-- PRM vs PHM 코드 존재 여부
SELECT 'PRM' AS kind, COUNT(*) FROM FRM_CODE WHERE CD_KIND = 'PRM_POS_GRD_CD'
UNION ALL
SELECT 'PHM', COUNT(*) FROM FRM_CODE WHERE CD_KIND = 'PHM_POS_GRD_CD';
```

### 2.3 EMPLOYEE_ID / EMPLOYEE_NAME → EMP_ID / EMP_NAME 통일 (완료)

기존 뷰는 조인키가 `EMPLOYEE_ID`, 성명이 `EMPLOYEE_NAME`으로 되어 있어 다른 V_AI_* 뷰와 불일치했음.
→ **`EMP_ID`, `EMP_NAME`으로 통일 완료**.

### 2.4 NL2SQL 활용도 분석

| 컬럼 | NL2SQL 활용도 | 카탈로그 등재 | 비고 |
|------|:----------:|:----------:|------|
| EMP_ID | FK | O | 다른 뷰와 동일 조인키 |
| EMP_NAME | 중간 | O | 급여 시점 성명 |
| PAY_YEAR | ★높음 | O | 급여 연도 |
| PAY_YEAR_MONTH | ★높음 | O | 급여 년월 |
| PAYMENT_TYPE_NAME | ★높음 | O | 지급구분 (정기급여,상여 등) |
| ORGANIZATION_NAME | 중간 | O | 소속부서명 |
| FIXED_PAY_AMOUNT | 중간 | O | 고정비 (원) |
| VARIABLE_PAY_AMOUNT | 중간 | O | 변동비 (원) |
| GROSS_PAY_AMOUNT | ★높음 | O | 지급합계 (원) = 고정비 + 변동비 |
| DEDUCTION_AMOUNT | 중간 | O | 공제합계 (원) |
| TAX_AMOUNT | 중간 | O | 세금합계 (원) |
| TOTAL_DEDUCTION_AMOUNT | 중간 | O | 총공제액 (원) = 공제 + 세금 |
| NET_PAY_AMOUNT | ★높음 | O | 실지급액 (원) = 지급합계 - 총공제액 |
| SALARY_TYPE_NAME | 낮음 | **X** | 급여유형 — 활용도 낮음 |
| PAY_GRADE_NAME | 낮음 | **X** | 급여직급 — GRADE와 중복 |
| JOB_GRADE_NAME | 낮음 | **X** | 직급 — GRADE와 중복 |
| EMPLOYMENT_TYPE | 낮음 | **X** | 급여직군 — EMP_TYPE과 중복 |
| ACCOUNT_TYPE_NAME | 낮음 | **X** | 코스트센터 — ★FC5 오류 |
| JOB_TYPE_NAME | 낮음 | **X** | 계정유형 — 활용도 낮음 |
| ORGANIZATION_ID | 낮음 | **X** | 코드값 |
| PAY_DATE | 낮음 | **X** | 급여일 |
| PAY_DATE_ID | 낮음 | **X** | 내부 ID |
| REMARKS | 낮음 | **X** | 비고 |
| TIMEZONE_* | 낮음 | **X** | 내부 타임존 |

---

## 3. 개선 사항

### 3.1 수정 SQL 전문 (개선안 — EMP_ID/EMP_NAME 통일 + FC5 CD_KIND 수정 대기)

```sql
-- H552_RND.V_AI_PAY_REPORT source (개선안 — EMP_ID/EMP_NAME 통일)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_PAY_REPORT" (
    "EMP_ID", "EMP_NAME", "PAY_YEAR", "PAY_YEAR_MONTH",
    "PAY_DATE", "PAY_DATE_ID", "PAYMENT_TYPE_NAME", "SALARY_TYPE_NAME",
    "PAY_GRADE_NAME", "JOB_GRADE_NAME", "EMPLOYMENT_TYPE",
    "ACCOUNT_TYPE_NAME", "JOB_TYPE_NAME", "ORGANIZATION_ID",
    "ORGANIZATION_NAME", "FIXED_PAY_AMOUNT", "VARIABLE_PAY_AMOUNT",
    "GROSS_PAY_AMOUNT", "DEDUCTION_AMOUNT", "TAX_AMOUNT",
    "TOTAL_DEDUCTION_AMOUNT", "NET_PAY_AMOUNT", "REMARKS",
    "TIMEZONE_CODE", "TIMEZONE_DATETIME"
) AS
SELECT
    -- [변경] EMPLOYEE_ID → EMP_ID, EMPLOYEE_NAME → EMP_NAME (다른 V_AI_* 뷰와 통일)
    PR.EMP_ID         AS emp_id,
    PR.EMP_NM         AS emp_name,
    PR.PAY_YYYY       AS pay_year,
    PR.PAY_YM         AS pay_year_month,
    PR.PAY_YMD        AS pay_date,
    PR.PAY_YMD_ID     AS pay_date_id,
    FC1.CD_NM         AS payment_type_name,
    FC2.CD_NM         AS salary_type_name,
    FC3.CD_NM         AS pay_grade_name,
    FC4.CD_NM         AS job_grade_name,
    PR.DTM_TYPE       AS employment_type,
    FC5.CD_NM         AS account_type_name,
    FC6.CD_NM         AS job_type_name,
    PR.ORG_ID         AS organization_id,
    PR.ORG_NM         AS organization_name,
    PR.G_MON          AS fixed_pay_amount,
    PR.B_MON          AS variable_pay_amount,
    PR.PSUM           AS gross_pay_amount,
    PR.DSUM           AS deduction_amount,
    PR.TSUM           AS tax_amount,
    PR.DTSUM          AS total_deduction_amount,
    PR.REAL_AMT       AS net_pay_amount,
    PR.NOTE           AS remarks,
    PR.TZ_CD          AS timezone_code,
    PR.TZ_DATE        AS timezone_datetime
FROM PAY_REPORT PR
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PR.PAY_TYPE_CD     AND FC1.CD_KIND = 'PAY_TYPE_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PR.SALARY_TYPE_CD   AND FC2.CD_KIND = 'PAY_SALARY_TYPE_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PR.PAY_POS_GRD_CD   AND FC3.CD_KIND = 'PAY_POS_GRD_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PR.POS_GRD_CD       AND FC4.CD_KIND = 'PRM_POS_GRD_CD'
-- ★★ FC5: CD_KIND 매핑 오류 — DB 검증 후 올바른 CD_KIND로 교체 필요
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PR.ACC_CD           AND FC5.CD_KIND = 'PHM_ARMY_MTALENT_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PR.POS_CD           AND FC6.CD_KIND = 'PHM_POS_CD';

GRANT SELECT ON "H552_RND"."V_AI_PAY_REPORT" TO "MUSER";
```

### 3.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **조인키 컬럼명** | `EMPLOYEE_ID` | `EMP_ID` | **핵심 변경 — 다른 뷰와 통일** |
| **성명 컬럼명** | `EMPLOYEE_NAME` | `EMP_NAME` | V_AI_EMPLOYEE.EMP_NAME과 통일 |
| **FC5 CD_KIND** | `PHM_ARMY_MTALENT_CD` (오류) | DB 검증 후 교체 | **검증 대기** |
| SELECT alias | `AS employee_id/name` | `AS emp_id/name` | DDL 컬럼명과 동기화 |

### 3.3 급여 계산 구조 (COMMENT에서 확인)

```
┌─────────────────────────────────────────────────────┐
│  GROSS_PAY_AMOUNT (지급합계)                          │
│    = FIXED_PAY_AMOUNT (고정비)                        │
│    + VARIABLE_PAY_AMOUNT (변동비)                     │
├─────────────────────────────────────────────────────┤
│  TOTAL_DEDUCTION_AMOUNT (총공제액)                     │
│    = DEDUCTION_AMOUNT (공제합계)                       │
│    + TAX_AMOUNT (세금합계)                            │
├─────────────────────────────────────────────────────┤
│  NET_PAY_AMOUNT (실지급액)                            │
│    = GROSS_PAY_AMOUNT - TOTAL_DEDUCTION_AMOUNT       │
│    = (고정비 + 변동비) - (공제 + 세금)                   │
└─────────────────────────────────────────────────────┘
```

**PK**: `(EMP_ID, PAY_YEAR_MONTH, PAYMENT_TYPE_NAME)` — 동일 직원의 같은 월에 지급구분(정기급여, 상여 등)별로 별도 행 존재.

### 3.4 COMMENT 보강

```sql
COMMENT ON TABLE H552_RND.V_AI_PAY_REPORT IS '급여 지급 내역 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N — 급여월+지급구분별 행 존재). PK: (EMP_ID, PAY_YEAR_MONTH, PAYMENT_TYPE_NAME). 금액 단위: 원';

COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.EMP_ID IS '사원 고유 식별 번호 PK (FK → V_AI_EMPLOYEE.EMP_ID)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.EMP_NAME IS '급여 시점 성명 (PAY_REPORT 자체 컬럼)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAY_YEAR IS '급여 연도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAY_YEAR_MONTH IS '급여 년월 PK (YYYYMM)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAY_DATE IS '급여일 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAY_DATE_ID IS '급여일자ID';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAYMENT_TYPE_NAME IS '급여 지급구분 PK (정기급여,연차수당,격려금,상여 등)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.SALARY_TYPE_NAME IS '급여유형';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.PAY_GRADE_NAME IS '급여직급';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.JOB_GRADE_NAME IS '직급';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.EMPLOYMENT_TYPE IS '급여직군';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.ACCOUNT_TYPE_NAME IS '코스트센터 (★FC5 CD_KIND 매핑 확인 필요)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.JOB_TYPE_NAME IS '직위';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.ORGANIZATION_ID IS '소속부서 ID';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.ORGANIZATION_NAME IS '소속부서명';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.FIXED_PAY_AMOUNT IS '고정비 (원)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.VARIABLE_PAY_AMOUNT IS '변동비 (원)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.GROSS_PAY_AMOUNT IS '지급합계 (원, = 고정비 + 변동비)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.DEDUCTION_AMOUNT IS '공제합계 (원)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.TAX_AMOUNT IS '세금합계 (원)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.TOTAL_DEDUCTION_AMOUNT IS '총공제액 (원, = 공제 + 세금)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.NET_PAY_AMOUNT IS '실지급액 (원, = 지급합계 - 총공제액)';
COMMENT ON COLUMN H552_RND.V_AI_PAY_REPORT.REMARKS IS '비고';
```

### 3.5 table_catalog.py 반영 코드

```python
"v_ai_pay_report": {
    "description": "급여 지급 내역 (1:N — 급여월+지급구분별 행 존재, EMP_ID로 V_AI_EMPLOYEE와 JOIN). 금액 단위: 원",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE)",
        "EMP_NAME (급여 시점 성명)",
        "PAY_YEAR ★급여연도 (YYYY)",
        "PAY_YEAR_MONTH ★급여년월 PK (YYYYMM)",
        "PAYMENT_TYPE_NAME ★지급구분 PK (정기급여,연차수당,격려금,상여 등)",
        "ORGANIZATION_NAME (소속부서명)",
        "FIXED_PAY_AMOUNT (고정비, 원)",
        "VARIABLE_PAY_AMOUNT (변동비, 원)",
        "GROSS_PAY_AMOUNT ★지급합계 (원, = 고정비 + 변동비)",
        "DEDUCTION_AMOUNT (공제합계, 원)",
        "TAX_AMOUNT (세금합계, 원)",
        "TOTAL_DEDUCTION_AMOUNT (총공제액, 원, = 공제 + 세금)",
        "NET_PAY_AMOUNT ★실지급액 (원, = 지급합계 - 총공제액)",
    ],
    "keywords": ["급여", "월급", "연봉", "지급", "실수령", "공제", "세금", "상여", "보너스", "급여명세", "고정비", "변동비"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 급여월+지급구분별, 연간 급여: SUM + WHERE PAY_YEAR = ':YYYY')",
    "related_tables": ["v_ai_employee"],
},
```

### 3.6 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 특정 년월 급여 통계**
```
title: 특정 년월 급여 통계 조회
doc_type: query_example
usage_type: rag_action

content:
이번 달 급여 현황
:년월 급여 통계
급여 지급 현황
월별 급여 합계
- V_AI_PAY_REPORT
- PAY_YEAR_MONTH 필터 + SUM

context_data:
## SQL
```sql
SELECT PAYMENT_TYPE_NAME,
       COUNT(*) AS emp_count,
       SUM(GROSS_PAY_AMOUNT) AS total_gross,
       SUM(NET_PAY_AMOUNT) AS total_net,
       ROUND(AVG(NET_PAY_AMOUNT)) AS avg_net
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = ':년월'
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_gross DESC
```

## 핵심 패턴
- PAY_YEAR_MONTH = ':년월': YYYYMM 형식 (예: '202601')
- PAYMENT_TYPE_NAME: 정기급여, 연차수당, 격려금, 상여 등
- SUM/AVG: 금액 집계 (단위: 원)
- 정기급여만: WHERE PAYMENT_TYPE_NAME = '정기급여'
```

**추가 예제 2: 부서별 평균 급여**
```
title: 부서별 평균 급여 조회
doc_type: query_example
usage_type: rag_action

content:
부서별 평균 급여
부서별 급여 현황
부서 평균 연봉
부서별 실수령액
- V_AI_EMPLOYEE JOIN V_AI_PAY_REPORT
- DEPARTMENT GROUP BY + AVG(NET_PAY_AMOUNT)

context_data:
## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.NET_PAY_AMOUNT)) AS avg_net_pay
FROM v_ai_employee a
JOIN v_ai_pay_report b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.PAY_YEAR_MONTH = ':년월'
  AND b.PAYMENT_TYPE_NAME = '정기급여'
GROUP BY a.DEPARTMENT
ORDER BY avg_net_pay DESC
```

## 핵심 패턴
- JOIN 키: a.EMP_ID = b.EMP_ID
- PAYMENT_TYPE_NAME = '정기급여': 상여 제외, 정기급여만
- PAY_YEAR_MONTH: 특정 월 지정
- AVG(NET_PAY_AMOUNT): 실지급액 평균
```

**추가 예제 3: 직원 연간 급여 합계**
```
title: 직원 연간 급여 합계 조회
doc_type: query_example
usage_type: rag_action

content:
연간 급여 합계
올해 급여 총액
직원별 연봉
연간 실수령액
- V_AI_EMPLOYEE JOIN V_AI_PAY_REPORT
- PAY_YEAR 필터 + GROUP BY EMP_ID + SUM

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       SUM(b.GROSS_PAY_AMOUNT) AS annual_gross,
       SUM(b.NET_PAY_AMOUNT) AS annual_net
FROM v_ai_employee a
JOIN v_ai_pay_report b ON a.EMP_ID = b.EMP_ID
WHERE b.PAY_YEAR = ':연도'
  AND a.WORK_STATUS = '재직'
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT, a.POSITION
ORDER BY annual_gross DESC
```

## 핵심 패턴
- PAY_YEAR = ':연도': 연간 집계 (YYYY 형식)
- SUM(GROSS_PAY_AMOUNT): 연간 총 지급액 (정기급여 + 상여 등 모두 포함)
- SUM(NET_PAY_AMOUNT): 연간 실수령액
- 정기급여만: WHERE PAYMENT_TYPE_NAME = '정기급여' 추가
```

---

## 4. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| EMP_ID | O (FK) | 다른 뷰와 동일 |
| EMP_NAME | O | 급여 시점 성명 |
| PAY_YEAR | O (★) | 급여 연도 |
| PAY_YEAR_MONTH | O (★) | 급여 년월 PK |
| PAY_DATE | **X** | 급여일 — 활용도 낮음 |
| PAY_DATE_ID | **X** | 내부 ID |
| PAYMENT_TYPE_NAME | O (★) | 지급구분 PK |
| SALARY_TYPE_NAME | **X** | 급여유형 — 활용도 낮음 |
| PAY_GRADE_NAME | **X** | 급여직급 — 중복 |
| JOB_GRADE_NAME | **X** | 직급 — 중복 |
| EMPLOYMENT_TYPE | **X** | 급여직군 — 중복 |
| ACCOUNT_TYPE_NAME | **X** | ★FC5 오류 컬럼 |
| JOB_TYPE_NAME | **X** | 계정유형 — 활용도 낮음 |
| ORGANIZATION_ID | **X** | 코드값 |
| ORGANIZATION_NAME | O | 소속부서명 |
| FIXED_PAY_AMOUNT | O | 고정비 |
| VARIABLE_PAY_AMOUNT | O | 변동비 |
| GROSS_PAY_AMOUNT | O (★) | 지급합계 = 고정비 + 변동비 |
| DEDUCTION_AMOUNT | O | 공제합계 |
| TAX_AMOUNT | O | 세금합계 |
| TOTAL_DEDUCTION_AMOUNT | O | 총공제액 = 공제 + 세금 |
| NET_PAY_AMOUNT | O (★) | 실지급액 = 지급합계 - 총공제액 |
| REMARKS | **X** | 비고 |
| TIMEZONE_* | **X** | 내부 타임존 |

---

## 5. 검증 계획

```sql
-- 1) 전체 건수 + 직원 수
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp FROM V_AI_PAY_REPORT;

-- 2) PAYMENT_TYPE_NAME 값 도메인 (최우선)
SELECT PAYMENT_TYPE_NAME, COUNT(*) FROM V_AI_PAY_REPORT
WHERE PAYMENT_TYPE_NAME IS NOT NULL
GROUP BY PAYMENT_TYPE_NAME ORDER BY COUNT(*) DESC;

-- 3) FC5 오류 영향 확인 — ACCOUNT_TYPE_NAME 실제 값
SELECT ACCOUNT_TYPE_NAME, COUNT(*) FROM V_AI_PAY_REPORT
GROUP BY ACCOUNT_TYPE_NAME ORDER BY COUNT(*) DESC;

-- 4) ACC_CD 올바른 CD_KIND 탐색
SELECT DISTINCT FC.CD_KIND
FROM FRM_CODE FC
WHERE FC.CD IN (SELECT DISTINCT ACC_CD FROM PAY_REPORT WHERE ACC_CD IS NOT NULL)
ORDER BY FC.CD_KIND;

-- 5) FC4 PRM vs PHM 확인
SELECT 'PRM' AS kind, COUNT(*) FROM FRM_CODE WHERE CD_KIND = 'PRM_POS_GRD_CD'
UNION ALL
SELECT 'PHM', COUNT(*) FROM FRM_CODE WHERE CD_KIND = 'PHM_POS_GRD_CD';

-- 6) PAY_YEAR 범위
SELECT MIN(PAY_YEAR), MAX(PAY_YEAR) FROM V_AI_PAY_REPORT;

-- 7) 금액 범위 확인
SELECT
    MIN(NET_PAY_AMOUNT) AS min_net, MAX(NET_PAY_AMOUNT) AS max_net,
    ROUND(AVG(NET_PAY_AMOUNT)) AS avg_net
FROM V_AI_PAY_REPORT WHERE NET_PAY_AMOUNT > 0;

-- 8) 급여 계산 검증 (GROSS = FIXED + VARIABLE, NET = GROSS - TOTAL_DEDUCTION)
SELECT EMP_ID, PAY_YEAR_MONTH,
       FIXED_PAY_AMOUNT + VARIABLE_PAY_AMOUNT AS calc_gross,
       GROSS_PAY_AMOUNT AS actual_gross,
       GROSS_PAY_AMOUNT - TOTAL_DEDUCTION_AMOUNT AS calc_net,
       NET_PAY_AMOUNT AS actual_net
FROM V_AI_PAY_REPORT
WHERE FIXED_PAY_AMOUNT + VARIABLE_PAY_AMOUNT <> GROSS_PAY_AMOUNT
   OR GROSS_PAY_AMOUNT - TOTAL_DEDUCTION_AMOUNT <> NET_PAY_AMOUNT
FETCH FIRST 10 ROWS ONLY;
```

---

## 6. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **EMPLOYEE_ID → EMP_ID** | 다른 뷰와 불일치 | DDL 변경 완료 | **완료** |
| **EMPLOYEE_NAME → EMP_NAME** | 다른 뷰와 불일치 | DDL 변경 완료 | **완료** |
| **FC5 CD_KIND 매핑 오류** | PHM_ARMY_MTALENT_CD (군 특기) | DB 조회 후 올바른 CD_KIND로 교체 또는 제거 | **최우선** |
| **FC4 PRM 오타** | PRM_POS_GRD_CD | PHM과 비교 확인 | **확인 필요** |
| **급여 계산 구조** | COMMENT에서 확인 완료 | 카탈로그 컬럼 설명에 계산식 반영 | **확정** |
| **카탈로그 보강** | 기본 수준 | 값 도메인 + 금액 단위 + 계산식 + PK 구조 명시 | **확정** |
| **COMMENT 보강** | 일부만 존재 | 금액 단위(원), 계산식, PK 명시 | **확정** |
| **fewshot 예제** | 없음 | 3건 추가 (월별통계, 부서별평균, 연간합계) | **확정** |
| PAYMENT_TYPE_NAME 값 도메인 | 미확인 | DB 조회로 확인 | 검증 필요 |

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: FC5 CD_KIND 매핑 오류 식별, FC4 PRM 오타 의심, 카탈로그/COMMENT/fewshot 개선안 |
| 2026-03-17 | EMPLOYEE_ID→EMP_ID, EMPLOYEE_NAME→EMP_NAME 변경: DDL, COMMENT, 카탈로그, fewshot 전체 반영. 급여 계산 구조 섹션 3.3 추가, 수정 SQL 전문 섹션 3.1 추가 |
