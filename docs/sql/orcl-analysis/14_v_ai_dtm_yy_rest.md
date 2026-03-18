# V_AI_DTM_YY_REST 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_DTM_YY_REST`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음 — dead JOIN + 잔여연차 부재)

```sql
CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "V_AI_DTM_YY_REST" (
    "LEAVE_ACCRUAL_ID", "EMP_ID", "REFERENCE_YEAR",
    "LEAVE_TYPE_CODE", "ACCRUAL_DATE", "LEAVE_GRANT_RULE_CODE",
    "ACCRUED_LEAVE_DAYS", "ADDITIONAL_LEAVE_DAYS",
    "COMPENSATED_LEAVE_DAYS", "COMPENSATION_MONTH",
    "COMPENSATED_LEAVE_DAYS_2", "COMPENSATION_MONTH_2",
    "RETIREMENT_LEAVE_DAYS", "RETIREMENT_COMPENSATION_MONTH",
    "USED_LEAVE_DAYS_PAST", "CARRIED_OVER_LEAVE_DAYS",
    "REMARKS", "UPDATED_BY", "UPDATED_AT",
    "TIMEZONE_CODE", "TIMEZONE_DATETIME"
) AS
SELECT
    DY.DTM_YY_REST_ID           AS leave_accrual_id,
    DY.EMP_ID                   AS emp_id,
    DY.APP_YY                   AS reference_year,
    DY.YY_KIND_CD               AS leave_type_code,        -- ★ 코드값 그대로 (FC1.CD_NM 아님)
    DY.WORK_YMD                 AS accrual_date,
    DY.YY_NUM_KIND_CD           AS leave_grant_rule_code,   -- ★ 코드값 그대로 (FC2.CD_NM 아님)
    NVL(DY.YY_NUM, 0)           AS accrued_leave_days,
    NVL(DY.ADD_NUM, 0)          AS additional_leave_days,
    NVL(DY.PAY_YY_NUM, 0)       AS compensated_leave_days,
    DY.PAY_MM                   AS compensation_month,
    NVL(DY.PAY_YY_NUM2, 0)      AS compensated_leave_days_2,
    DY.PAY_MM2                  AS compensation_month_2,
    NVL(DY.RETIRE_PAY_YY_NUM, 0) AS retirement_leave_days,
    DY.RETIRE_PAY_MM            AS retirement_compensation_month,
    DY.USED_NUM                 AS used_leave_days_past,
    DY.NEXT_YY_NUM              AS carried_over_leave_days,
    DY.NOTE                     AS remarks,
    DY.MOD_USER_ID              AS updated_by,
    DY.MOD_DATE                 AS updated_at,
    DY.TZ_CD                    AS timezone_code,
    DY.TZ_DATE                  AS timezone_datetime
FROM DTM_YY_REST DY
LEFT JOIN FRM_CODE FC1 ON FC1.CD = DY.YY_KIND_CD     AND FC1.CD_KIND = 'DTM_YY_KIND_CD'      -- ★ dead JOIN
LEFT JOIN FRM_CODE FC2 ON FC2.CD = DY.YY_NUM_KIND_CD  AND FC2.CD_KIND = 'DTM_YY_NUM_KIND_CD'; -- ★ dead JOIN
```

**소스**: `DTM_YY_REST` + FRM_CODE 2개 LEFT JOIN. PHM_EMP 참조 없음.
**문제**: FC1, FC2를 JOIN하지만 **SELECT에서 사용하지 않음** (dead JOIN).

---

## 2. 이슈 분석

### 2.1 Dead JOIN — FC1, FC2 미사용 (확정)

**문제**: FC1(DTM_YY_KIND_CD), FC2(DTM_YY_NUM_KIND_CD)를 LEFT JOIN하지만, SELECT에서 `FC1.CD_NM`, `FC2.CD_NM`이 아닌 **원본 코드값**(`DY.YY_KIND_CD`, `DY.YY_NUM_KIND_CD`)을 직접 사용.

```sql
-- SELECT에서 FC1/FC2가 아닌 원본 코드값 직접 사용
DY.YY_KIND_CD       AS leave_type_code,       -- FC1.CD_NM이 아님!
DY.YY_NUM_KIND_CD   AS leave_grant_rule_code,  -- FC2.CD_NM이 아님!
```

**영향**:
1. 불필요한 JOIN으로 쿼리 성능 저하
2. `LEAVE_TYPE_CODE`, `LEAVE_GRANT_RULE_CODE`가 코드값('10', '20' 등)으로 반환 → 사람이 읽을 수 없음
3. NL2SQL이 해당 컬럼을 사용하면 "연차구분이 '10'인..." 같은 무의미한 결과

**수정 방향**: FC1/FC2의 `CD_NM`을 SELECT에 추가하여 코드명 변환 + 기존 코드값 컬럼 유지

### 2.2 잔여연차 계산 컬럼 부재 (확정)

**현재 컬럼**:
- `ACCRUED_LEAVE_DAYS`: 발생연차 — `NVL(YY_NUM, 0)`
- `ADDITIONAL_LEAVE_DAYS`: 추가연차 — `NVL(ADD_NUM, 0)`
- `USED_LEAVE_DAYS_PAST`: 사용연차(과거) — `USED_NUM` (★NVL 미적용)
- `CARRIED_OVER_LEAVE_DAYS`: 이월연차 — `NEXT_YY_NUM` (★NVL 미적용)
- `COMPENSATED_LEAVE_DAYS`: 보상연차 — `NVL(PAY_YY_NUM, 0)`
- `COMPENSATED_LEAVE_DAYS_2`: 보상연차2 — `NVL(PAY_YY_NUM2, 0)`
- `RETIREMENT_LEAVE_DAYS`: 퇴직연차 — `NVL(RETIRE_PAY_YY_NUM, 0)`
- ❌ **REMAINING_LEAVE_DAYS (잔여연차)**: 없음!

**NL2SQL 영향**:

| 질의 | 현재 | 기대 |
|------|------|------|
| "올해 남은 연차 몇 일?" | ❌ 직접 계산 불가 | `REMAINING_LEAVE_DAYS` 컬럼 |
| "잔여연차 5일 미만 직원" | ❌ 직접 계산 불가 | `WHERE REMAINING_LEAVE_DAYS < 5` |
| "연차 사용률" | ❌ 복잡한 계산 필요 | `USED / (ACCRUED + ADDITIONAL) * 100` |

**수정 방향**: 뷰에 `REMAINING_LEAVE_DAYS` 계산 컬럼 추가.

### 2.3 USED_LEAVE_DAYS_PAST / CARRIED_OVER_LEAVE_DAYS — NVL 미적용

```sql
DY.USED_NUM      AS used_leave_days_past,       -- NVL 없음! NULL 가능
DY.NEXT_YY_NUM   AS carried_over_leave_days,     -- NVL 없음! NULL 가능
```

다른 일수 컬럼(`ACCRUED_LEAVE_DAYS` 등)은 `NVL(..., 0)`이 적용되어 있지만, 이 2개 컬럼은 누락. 잔여연차 계산 시 NULL 방어 필요.

### 2.4 EMP_ID 통일 (완료)

V_AI_DTM_YY_REST도 `EMP_ID` (EMP_ID 아님). V_AI_PAY_REPORT, V_AI_HISTORY와 동일 패턴.

### 2.5 NL2SQL 활용도 분석

| 컬럼 | NL2SQL 활용도 | 카탈로그 등재 | 비고 |
|------|:----------:|:----------:|------|
| EMP_ID | FK | O | ★EMP_ID 아님 주의 |
| REFERENCE_YEAR | ★높음 | O | 기준년도 |
| LEAVE_TYPE_CODE | 낮음 | **X** | 코드값 그대로 → 미등재 |
| LEAVE_TYPE_NAME (신규) | 중간 | O | 연차구분명 (FC1.CD_NM) |
| ACCRUED_LEAVE_DAYS | ★높음 | O | 발생연차 |
| ADDITIONAL_LEAVE_DAYS | 중간 | O | 추가연차 |
| USED_LEAVE_DAYS_PAST | ★높음 | O | 사용연차 |
| REMAINING_LEAVE_DAYS (신규) | ★높음 | O | 잔여연차 (계산 컬럼) |
| CARRIED_OVER_LEAVE_DAYS | 중간 | O | 이월연차 |
| COMPENSATED_LEAVE_DAYS | 중간 | O | 보상연차 |
| ACCRUAL_DATE | 낮음 | **X** | 발생일자 — 활용도 낮음 |
| LEAVE_GRANT_RULE_CODE | 낮음 | **X** | 코드값 그대로 |
| COMPENSATION_MONTH* | 낮음 | **X** | 보상적용월 — 활용도 낮음 |
| COMPENSATED_LEAVE_DAYS_2 | 낮음 | **X** | 보상연차2 — 활용도 낮음 |
| RETIREMENT_* | 낮음 | **X** | 퇴직연차 — 활용도 낮음 |
| LEAVE_ACCRUAL_ID | 낮음 | **X** | 내부 PK |
| UPDATED_BY/AT | 낮음 | **X** | 내부 변경 정보 |
| TIMEZONE_* | 낮음 | **X** | 내부 타임존 |
| REMARKS | 낮음 | **X** | 비고 |

---

## 3. 개선 사항

### 3.1 뷰 개선 — dead JOIN 활용 + 잔여연차 추가 (확정)

```sql
CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_DTM_YY_REST" (
    "LEAVE_ACCRUAL_ID", "EMP_ID", "REFERENCE_YEAR",
    "LEAVE_TYPE_CODE", "LEAVE_TYPE_NAME",
    "ACCRUAL_DATE", "LEAVE_GRANT_RULE_CODE", "LEAVE_GRANT_RULE_NAME",
    "ACCRUED_LEAVE_DAYS", "ADDITIONAL_LEAVE_DAYS",
    "COMPENSATED_LEAVE_DAYS", "COMPENSATION_MONTH",
    "COMPENSATED_LEAVE_DAYS_2", "COMPENSATION_MONTH_2",
    "RETIREMENT_LEAVE_DAYS", "RETIREMENT_COMPENSATION_MONTH",
    "USED_LEAVE_DAYS_PAST", "CARRIED_OVER_LEAVE_DAYS",
    "TOTAL_LEAVE_DAYS", "REMAINING_LEAVE_DAYS",
    "REMARKS", "UPDATED_BY", "UPDATED_AT",
    "TIMEZONE_CODE", "TIMEZONE_DATETIME"
) AS
SELECT
    DY.DTM_YY_REST_ID              AS leave_accrual_id,
    DY.EMP_ID                      AS emp_id,
    DY.APP_YY                      AS reference_year,
    DY.YY_KIND_CD                  AS leave_type_code,
    -- [추가] 연차구분명 (dead JOIN 활용)
    FC1.CD_NM                      AS leave_type_name,
    DY.WORK_YMD                    AS accrual_date,
    DY.YY_NUM_KIND_CD              AS leave_grant_rule_code,
    -- [추가] 연차부여기준명 (dead JOIN 활용)
    FC2.CD_NM                      AS leave_grant_rule_name,
    NVL(DY.YY_NUM, 0)              AS accrued_leave_days,
    NVL(DY.ADD_NUM, 0)             AS additional_leave_days,
    NVL(DY.PAY_YY_NUM, 0)          AS compensated_leave_days,
    DY.PAY_MM                      AS compensation_month,
    NVL(DY.PAY_YY_NUM2, 0)         AS compensated_leave_days_2,
    DY.PAY_MM2                     AS compensation_month_2,
    NVL(DY.RETIRE_PAY_YY_NUM, 0)   AS retirement_leave_days,
    DY.RETIRE_PAY_MM               AS retirement_compensation_month,
    -- [수정] NVL 추가 (기존에 누락)
    NVL(DY.USED_NUM, 0)            AS used_leave_days_past,
    NVL(DY.NEXT_YY_NUM, 0)         AS carried_over_leave_days,
    -- [추가] 총 년월차 일수 = 발생 + 추가 + 보상 + 보상2 + 퇴직연차
    NVL(DY.YY_NUM, 0) + NVL(DY.ADD_NUM, 0)
      + NVL(DY.PAY_YY_NUM, 0) + NVL(DY.PAY_YY_NUM2, 0)
      + NVL(DY.RETIRE_PAY_YY_NUM, 0)
                                   AS total_leave_days,
    -- [추가] 잔여연차 = 총 년월차 - 사용
    NVL(DY.YY_NUM, 0) + NVL(DY.ADD_NUM, 0)
      + NVL(DY.PAY_YY_NUM, 0) + NVL(DY.PAY_YY_NUM2, 0)
      + NVL(DY.RETIRE_PAY_YY_NUM, 0)
      - NVL(DY.USED_NUM, 0)
                                   AS remaining_leave_days,
    DY.NOTE                        AS remarks,
    DY.MOD_USER_ID                 AS updated_by,
    DY.MOD_DATE                    AS updated_at,
    DY.TZ_CD                       AS timezone_code,
    DY.TZ_DATE                     AS timezone_datetime
FROM DTM_YY_REST DY
-- [변경] dead JOIN → 활용 (FC1.CD_NM, FC2.CD_NM SELECT에 추가)
LEFT JOIN FRM_CODE FC1 ON FC1.CD = DY.YY_KIND_CD     AND FC1.CD_KIND = 'DTM_YY_KIND_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = DY.YY_NUM_KIND_CD  AND FC2.CD_KIND = 'DTM_YY_NUM_KIND_CD';

GRANT SELECT ON "H552_RND"."V_AI_DTM_YY_REST" TO "MUSER";
```

### 3.2 변경 요약

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **FC1.CD_NM** | dead JOIN (미사용) | `LEAVE_TYPE_NAME` 컬럼 추가 | 연차구분명 |
| **FC2.CD_NM** | dead JOIN (미사용) | `LEAVE_GRANT_RULE_NAME` 컬럼 추가 | 부여기준명 |
| **USED_LEAVE_DAYS_PAST** | NVL 미적용 | `NVL(DY.USED_NUM, 0)` | NULL 방어 |
| **CARRIED_OVER_LEAVE_DAYS** | NVL 미적용 | `NVL(DY.NEXT_YY_NUM, 0)` | NULL 방어 |
| **TOTAL_LEAVE_DAYS** | 없음 | **계산 컬럼 추가** | 총 년월차 = 발생+추가+보상+보상2+퇴직 |
| **REMAINING_LEAVE_DAYS** | 없음 | **계산 컬럼 추가** | 잔여연차 = 총 년월차 - 사용 |

### 3.3 년월차 계산식

```
총 년월차 일수(TOTAL) = 발생(ACCRUED) + 추가(ADDITIONAL) + 보상(COMPENSATED) + 보상2(COMPENSATED_2) + 퇴직연차(RETIREMENT)

잔여연차(REMAINING) = 총 년월차 - 사용(USED)
```

**핵심**: 보상연차, 퇴직연차는 "소진"이 아니라 **"추가 발생"**이므로 총 일수에 **더한다**.

```
┌─────────────────────────────────┐
│  총 년월차 일수 (TOTAL)           │
│    = 발생(ACCRUED)               │
│    + 추가(ADDITIONAL)            │
│    + 보상(COMPENSATED)           │
│    + 보상2(COMPENSATED_2)        │
│    + 퇴직연차(RETIREMENT)         │
├─────────────────────────────────┤
│  사용(USED)                      │
├─────────────────────────────────┤
│  잔여(REMAINING) = TOTAL - USED  │
│  이월(CARRIED_OVER) ≈ 잔여 (결과) │
└─────────────────────────────────┘
```

**CARRIED_OVER(이월=NEXT_YY_NUM)은 계산에 포함하지 않음**:
- 원본 컬럼명: `NEXT_YY_NUM` = "다음년 연차수"
- 의미: **다음 해로 넘기는 연차** (결과값)이지 입력값이 아님

**확인 필요 쿼리**:
```sql
-- 잔여연차 계산 검증 (음수 발생 여부, 합리적 범위 확인)
SELECT
    EMP_ID, REFERENCE_YEAR,
    ACCRUED_LEAVE_DAYS, ADDITIONAL_LEAVE_DAYS,
    NVL(USED_LEAVE_DAYS_PAST, 0) AS used,
    NVL(CARRIED_OVER_LEAVE_DAYS, 0) AS carried,
    COMPENSATED_LEAVE_DAYS,
    (ACCRUED_LEAVE_DAYS + ADDITIONAL_LEAVE_DAYS
     + COMPENSATED_LEAVE_DAYS + COMPENSATED_LEAVE_DAYS_2
     + RETIREMENT_LEAVE_DAYS) AS calc_total,
    (ACCRUED_LEAVE_DAYS + ADDITIONAL_LEAVE_DAYS
     + COMPENSATED_LEAVE_DAYS + COMPENSATED_LEAVE_DAYS_2
     + RETIREMENT_LEAVE_DAYS
     - NVL(USED_LEAVE_DAYS_PAST, 0)) AS calc_remaining
FROM V_AI_DTM_YY_REST
WHERE REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
ORDER BY calc_remaining ASC
FETCH FIRST 20 ROWS ONLY;
```

### 3.4 COMMENT 보강

```sql
COMMENT ON TABLE H552_RND.V_AI_DTM_YY_REST IS '연차 발생/사용/잔여 관리 (EMP_ID로 V_AI_EMPLOYEE.EMP_ID와 JOIN, 1:N — 기준년도별 행 존재). 일수 단위: 일';

COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.LEAVE_ACCRUAL_ID IS '발생연차관리ID (PK)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE.EMP_ID)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.REFERENCE_YEAR IS '기준년도 (YYYY)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.LEAVE_TYPE_CODE IS '연차구분 코드';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.LEAVE_TYPE_NAME IS '연차구분명';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.ACCRUAL_DATE IS '연차 발생일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.LEAVE_GRANT_RULE_CODE IS '연차부여기준 코드';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.LEAVE_GRANT_RULE_NAME IS '연차부여기준명';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.ACCRUED_LEAVE_DAYS IS '발생연차일수 (일)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.ADDITIONAL_LEAVE_DAYS IS '추가연차일수 (일)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.COMPENSATED_LEAVE_DAYS IS '보상연차일수 (일)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.COMPENSATION_MONTH IS '보상적용월';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.COMPENSATED_LEAVE_DAYS_2 IS '보상연차2일수 (일)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.COMPENSATION_MONTH_2 IS '보상적용월2';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.RETIREMENT_LEAVE_DAYS IS '퇴직연차일수 (일)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.RETIREMENT_COMPENSATION_MONTH IS '퇴직보상적용월';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.USED_LEAVE_DAYS_PAST IS '사용연차일수 (일, 과거 사용분)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.CARRIED_OVER_LEAVE_DAYS IS '이월연차일수 (일, 차년 추가연차)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.TOTAL_LEAVE_DAYS IS '총 년월차일수 (일, = 발생+추가+보상+보상2+퇴직연차)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.REMAINING_LEAVE_DAYS IS '잔여연차일수 (일, = 총 년월차 - 사용)';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.REMARKS IS '비고';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.UPDATED_BY IS '변경자 ID';
COMMENT ON COLUMN H552_RND.V_AI_DTM_YY_REST.UPDATED_AT IS '변경일시 (DATE)';
```

### 3.5 table_catalog.py 반영 코드

```python
"v_ai_dtm_yy_rest": {
    "description": "연차 발생/사용/잔여 관리 (1:N — 기준년도별 행 존재, EMP_ID로 V_AI_EMPLOYEE.EMP_ID와 JOIN). 일수 단위: 일",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE.EMP_ID, ★EMP_ID 아님 주의)",
        "REFERENCE_YEAR ★기준년도 (YYYY, 올해: TO_CHAR(SYSDATE,'YYYY'))",
        "LEAVE_TYPE_NAME (연차구분명)",
        "ACCRUED_LEAVE_DAYS ★발생연차일수 (일)",
        "ADDITIONAL_LEAVE_DAYS (추가연차일수, 일)",
        "USED_LEAVE_DAYS_PAST ★사용연차일수 (일)",
        "TOTAL_LEAVE_DAYS ★총 년월차일수 (일, = 발생+추가+보상+보상2+퇴직연차)",
        "REMAINING_LEAVE_DAYS ★잔여연차일수 (일, = 총 년월차 - 사용)",
        "CARRIED_OVER_LEAVE_DAYS (이월연차일수, 일)",
        "COMPENSATED_LEAVE_DAYS (보상연차일수, 일)",
    ],
    "keywords": ["연차", "휴가", "발생연차", "사용연차", "잔여연차", "남은연차", "추가연차", "이월", "보상연차", "연차현황", "휴가일수"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 기준년도별, 올해 연차: WHERE REFERENCE_YEAR = TO_CHAR(SYSDATE,'YYYY'))",
    "related_tables": ["v_ai_employee"],
},
```

### 3.6 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 올해 잔여연차 조회**
```
title: 올해 잔여연차 조회
doc_type: query_example
usage_type: rag_action

content:
올해 남은 연차
잔여연차 현황
남은 휴가 일수
연차 잔여일
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- REFERENCE_YEAR = 올해 + REMAINING_LEAVE_DAYS

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.ACCRUED_LEAVE_DAYS, b.ADDITIONAL_LEAVE_DAYS,
       b.USED_LEAVE_DAYS_PAST, b.REMAINING_LEAVE_DAYS
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND a.WORK_STATUS = '재직'
ORDER BY b.REMAINING_LEAVE_DAYS ASC
```

## 핵심 패턴
- JOIN 키: a.EMP_ID = b.EMP_ID
- REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY'): 올해 연차
- REMAINING_LEAVE_DAYS: 잔여연차일수
- ORDER BY ASC: 잔여연차 적은 직원 우선
```

**추가 예제 2: 연차 사용률 통계**
```
title: 부서별 연차 사용률 조회
doc_type: query_example
usage_type: rag_action

content:
연차 사용률
부서별 연차 사용 현황
연차 소진률
휴가 사용 통계
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- USED / (ACCRUED + ADDITIONAL) * 100

context_data:
## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.ACCRUED_LEAVE_DAYS + b.ADDITIONAL_LEAVE_DAYS), 1) AS avg_total,
       ROUND(AVG(b.USED_LEAVE_DAYS_PAST), 1) AS avg_used,
       ROUND(AVG(
           CASE WHEN (b.ACCRUED_LEAVE_DAYS + b.ADDITIONAL_LEAVE_DAYS) > 0
                THEN b.USED_LEAVE_DAYS_PAST * 100.0 / (b.ACCRUED_LEAVE_DAYS + b.ADDITIONAL_LEAVE_DAYS)
                ELSE 0
           END
       ), 1) AS avg_usage_rate
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND a.WORK_STATUS = '재직'
GROUP BY a.DEPARTMENT
ORDER BY avg_usage_rate DESC
```

## 핵심 패턴
- 사용률 = USED / (ACCRUED + ADDITIONAL) * 100
- CASE WHEN 0 방어: 발생연차 0인 경우 division by zero 방지
- 부서별: GROUP BY DEPARTMENT
- 전체: GROUP BY 제거
```

**추가 예제 3: 잔여연차 N일 미만 직원**
```
title: 잔여연차 부족 직원 조회
doc_type: query_example
usage_type: rag_action

content:
잔여연차 5일 미만
남은 연차 적은 직원
연차 소진 임박 직원
연차 부족자
- V_AI_EMPLOYEE JOIN V_AI_DTM_YY_REST
- REMAINING_LEAVE_DAYS < :N

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.ACCRUED_LEAVE_DAYS + b.ADDITIONAL_LEAVE_DAYS AS total_leave,
       b.USED_LEAVE_DAYS_PAST,
       b.REMAINING_LEAVE_DAYS
FROM v_ai_employee a
JOIN v_ai_dtm_yy_rest b ON a.EMP_ID = b.EMP_ID
WHERE b.REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
  AND b.REMAINING_LEAVE_DAYS < :일수
  AND a.WORK_STATUS = '재직'
ORDER BY b.REMAINING_LEAVE_DAYS ASC
```

## 핵심 패턴
- REMAINING_LEAVE_DAYS < :일수: 잔여연차 부족 직원
- :일수 = 5 → 5일 미만
- :일수 = 0 → 연차 소진 직원 (음수 포함)
- 부서별 수: GROUP BY a.DEPARTMENT + COUNT(*)
```

---

## 4. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| LEAVE_ACCRUAL_ID | **X** | 내부 PK |
| EMP_ID | O (FK) | ★EMP_ID 아님 주의 |
| REFERENCE_YEAR | O (★) | 기준년도 |
| LEAVE_TYPE_CODE | **X** | 코드값 |
| LEAVE_TYPE_NAME (신규) | O | 연차구분명 |
| ACCRUAL_DATE | **X** | 발생일자 — 활용도 낮음 |
| LEAVE_GRANT_RULE_CODE | **X** | 코드값 |
| LEAVE_GRANT_RULE_NAME (신규) | **X** | 부여기준명 — 활용도 낮음 |
| ACCRUED_LEAVE_DAYS | O (★) | 발생연차 |
| ADDITIONAL_LEAVE_DAYS | O | 추가연차 |
| COMPENSATED_LEAVE_DAYS | O | 보상연차 |
| COMPENSATION_MONTH | **X** | 보상월 — 활용도 낮음 |
| COMPENSATED_LEAVE_DAYS_2 | **X** | 보상연차2 — 활용도 낮음 |
| COMPENSATION_MONTH_2 | **X** | 보상월2 — 활용도 낮음 |
| RETIREMENT_LEAVE_DAYS | **X** | 퇴직연차 — 활용도 낮음 |
| RETIREMENT_COMPENSATION_MONTH | **X** | 퇴직보상월 — 활용도 낮음 |
| USED_LEAVE_DAYS_PAST | O (★) | 사용연차 |
| CARRIED_OVER_LEAVE_DAYS | O | 이월연차 |
| REMAINING_LEAVE_DAYS (신규) | O (★) | **잔여연차 (핵심)** |
| REMARKS | **X** | 비고 |
| UPDATED_BY/AT | **X** | 내부 변경 정보 |
| TIMEZONE_* | **X** | 내부 타임존 |

---

## 5. 검증 계획

```sql
-- 1) 전체 건수 + 직원 수
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp FROM V_AI_DTM_YY_REST;

-- 2) REFERENCE_YEAR 범위
SELECT MIN(REFERENCE_YEAR), MAX(REFERENCE_YEAR) FROM V_AI_DTM_YY_REST;

-- 3) LEAVE_TYPE_CODE 값 도메인 (FC1 활용)
SELECT FC1.CD_NM AS leave_type_name, DY.YY_KIND_CD, COUNT(*)
FROM DTM_YY_REST DY
LEFT JOIN FRM_CODE FC1 ON FC1.CD = DY.YY_KIND_CD AND FC1.CD_KIND = 'DTM_YY_KIND_CD'
GROUP BY FC1.CD_NM, DY.YY_KIND_CD
ORDER BY COUNT(*) DESC;

-- 4) LEAVE_GRANT_RULE_CODE 값 도메인 (FC2 활용)
SELECT FC2.CD_NM AS grant_rule_name, DY.YY_NUM_KIND_CD, COUNT(*)
FROM DTM_YY_REST DY
LEFT JOIN FRM_CODE FC2 ON FC2.CD = DY.YY_NUM_KIND_CD AND FC2.CD_KIND = 'DTM_YY_NUM_KIND_CD'
GROUP BY FC2.CD_NM, DY.YY_NUM_KIND_CD
ORDER BY COUNT(*) DESC;

-- 5) USED_LEAVE_DAYS_PAST NULL 비율 (NVL 누락 영향)
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN USED_LEAVE_DAYS_PAST IS NULL THEN 1 ELSE 0 END) AS null_used,
    SUM(CASE WHEN CARRIED_OVER_LEAVE_DAYS IS NULL THEN 1 ELSE 0 END) AS null_carried
FROM V_AI_DTM_YY_REST;

-- 6) 잔여연차 계산 검증 (음수 발생 여부)
SELECT
    EMP_ID, REFERENCE_YEAR,
    ACCRUED_LEAVE_DAYS AS accrued, ADDITIONAL_LEAVE_DAYS AS addtl,
    NVL(USED_LEAVE_DAYS_PAST, 0) AS used,
    NVL(CARRIED_OVER_LEAVE_DAYS, 0) AS carried,
    COMPENSATED_LEAVE_DAYS AS comp,
    (ACCRUED_LEAVE_DAYS + ADDITIONAL_LEAVE_DAYS
     + COMPENSATED_LEAVE_DAYS + COMPENSATED_LEAVE_DAYS_2
     + RETIREMENT_LEAVE_DAYS) AS calc_total,
    (ACCRUED_LEAVE_DAYS + ADDITIONAL_LEAVE_DAYS
     + COMPENSATED_LEAVE_DAYS + COMPENSATED_LEAVE_DAYS_2
     + RETIREMENT_LEAVE_DAYS
     - NVL(USED_LEAVE_DAYS_PAST, 0)) AS calc_remaining
FROM V_AI_DTM_YY_REST
WHERE REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY')
ORDER BY calc_remaining ASC
FETCH FIRST 20 ROWS ONLY;

-- 7) 올해 연차 일수 범위 확인
SELECT
    MIN(ACCRUED_LEAVE_DAYS) AS min_accrued, MAX(ACCRUED_LEAVE_DAYS) AS max_accrued,
    ROUND(AVG(ACCRUED_LEAVE_DAYS), 1) AS avg_accrued,
    ROUND(AVG(NVL(USED_LEAVE_DAYS_PAST, 0)), 1) AS avg_used
FROM V_AI_DTM_YY_REST
WHERE REFERENCE_YEAR = TO_CHAR(SYSDATE, 'YYYY');
```

### NL2SQL 테스트 질의

| 질문 | 기대 동작 |
|------|----------|
| "올해 남은 연차" | `WHERE REFERENCE_YEAR = 올해 + SELECT REMAINING_LEAVE_DAYS` |
| "잔여연차 5일 미만 직원" | `WHERE REMAINING_LEAVE_DAYS < 5 + JOIN V_AI_EMPLOYEE` |
| "부서별 연차 사용률" | `GROUP BY DEPARTMENT + AVG(USED / (ACCRUED + ADDITIONAL) * 100)` |

---

## 6. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **dead JOIN 활용** | FC1/FC2 미사용 | CD_NM을 SELECT에 추가 (LEAVE_TYPE_NAME, LEAVE_GRANT_RULE_NAME) | **확정** |
| **잔여연차 컬럼 추가** | 없음 | REMAINING_LEAVE_DAYS 계산 컬럼 추가 | **확정** (계산식 검증 필요) |
| **NVL 누락 수정** | USED/CARRIED에 NVL 없음 | NVL(..., 0) 추가 | **확정** |
| **카탈로그 보강** | 불필요 컬럼 과다 | 핵심 컬럼만 + 잔여연차 추가 + 불필요 컬럼 정리 | **확정** |
| **COMMENT 보강** | 기본 수준 | 잔여연차 계산식, 단위(일), JOIN 관계 명시 | **확정** |
| **fewshot 예제** | 없음 | 3건 추가 (잔여연차, 사용률, 부족 직원) | **확정** |
| 잔여연차 계산식 검증 | 미확인 | DB 데이터로 음수/이상값 확인 | **검증 필요** |
| FC1/FC2 값 도메인 | 미확인 | DB 조회로 확인 | 검증 필요 |

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: dead JOIN 식별, 잔여연차 부재 식별, NVL 누락 수정, 뷰 DDL 개선안, 카탈로그/COMMENT/fewshot 개선안 |
