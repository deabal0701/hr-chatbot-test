# V_AI_CAREER 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_CAREER`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_CAREER`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음)

현재 배포된 뷰 (`orcl-business_view_db.sql`)의 핵심 구조:

```
FROM PHM_CAREER PC    ← WHERE 없음, 전체 행 노출
```

**소스**: `PHM_CAREER` 단일 테이블, FRM_CODE JOIN 없음.

**문제**: PHM_CAREER의 UK는 `(EMP_ID, STA_YMD)` → 동일 직원이 전직장이 여러 곳이면 복수 행. 또한 STA_YMD/END_YMD(근무 시작/종료일)가 뷰에 미노출되어 시기 기반 질의 불가.

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql` 참조. 이 문서의 **섹션 7.1에 개선안 DDL**(실행 가능)을 작성함.

---

## 2. PHM_CAREER 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_CAREER_ID    NUMBER         PK    사원경력ID
EMP_ID           NUMBER         FK    사원ID
PERSON_ID        NUMBER         NN    개인ID
STA_YMD          DATE           NN    근무시작일자
END_YMD          DATE           NN    근무종료일
ORG_CORP_CD      VARCHAR2(50)         근무회사코드 [PHM_ORG_CORP_CD] (사용안함)
ORG_CORP_NM      VARCHAR2(150)        근무기관명        → 뷰: PREV_COMPANY
DEPT_NM          VARCHAR2(150)        근무처명          → 뷰: 미포함
POSITION_NM      VARCHAR2(100)        최종직위명        → 뷰: PREV_POSITION
WORK_NM          VARCHAR2(150)        담당업무 (사용안함)
JOB_CD           VARCHAR2(50)         직무코드 (사용안함)
JOB_NM           VARCHAR2(150)        직무명 (사용안함)
RETIRE_CAUSE     VARCHAR2(500)        퇴직사유          → 뷰: LEAVE_REASON
SAMIL_INC_YN     CHAR(1)              삼일경력포함여부 (추가)
RCAREER_NUM      NUMBER               실제경력월수 (추가) → 뷰: WORK_MONTHS
RECO_RATE        NUMBER               인정률 (추가)      → 뷰: RECOGNITION_RATE
CAREER_NUM       NUMBER               인정경력개월수     → 뷰: 미포함
NOTE             VARCHAR2(200)        비고
MOD_USER_ID      NUMBER         NN    변경자
MOD_DATE         DATE           NN    변경일시
TZ_CD            VARCHAR2(10)   NN    타임존코드
TZ_DATE          DATE           NN    타임존일시
ORG_ENG_NM       VARCHAR2(150)        영문회사명
PLACE_NM         VARCHAR2(750)        소재지            → 뷰: LOCATION
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_CAREER_ID` | 경력 ID |
| **UK** | `(EMP_ID, STA_YMD)` | 사원 + 근무시작일 = 유일 (1인 N건 가능) |

### 2.3 샘플 데이터 분석

```
(50151, 1733, 1733, 2011-10-01, 2014-06-01, NULL, '신아텍', NULL, '사원', ..., RCAREER_NUM=33, RECO_RATE=NULL, CAREER_NUM=32, NOTE='2년9개월')
(50154, 1738, 1738, 1992-10-01, 1995-07-31, NULL, '대성정밀', NULL, 'operator', ..., RCAREER_NUM=34, CAREER_NUM=34, NOTE='2년10개월')
(50155, 1738, 1738, 1997-05-01, 2000-10-25, NULL, '(주)기아특수강', NULL, 'operator', ..., RCAREER_NUM=42, CAREER_NUM=41, NOTE='3년6개월')
```

**핵심 발견**:
- `STA_YMD`, `END_YMD`: **DATE NOT NULL** — 모든 행에 근무 시작/종료일 존재
- `RCAREER_NUM`: 샘플에서 **값이 채워져 있음** (33, 51, 27, 34, 42...)
- `CAREER_NUM`(인정경력개월수) vs `RCAREER_NUM`(실제경력월수): 다른 값 (인정률 적용 차이)
- `EMP_ID=1738`이 2건 → **1인 다건 확인** (전직장 여러 곳)
- `NOTE`에 '2년9개월' 등 사람이 읽을 수 있는 기간 텍스트 포함

---

## 3. 이슈 분석

### 3.1 STA_YMD/END_YMD 뷰 미포함 — 확정된 문제

**문제**: PHM_CAREER에 `STA_YMD`(근무시작일, DATE NOT NULL), `END_YMD`(근무종료일, DATE NOT NULL)가 존재하나 현재 뷰에 미포함. 시기 기반 질의 불가.

**NL2SQL 영향**:

| 질의 | 현재 | 개선 후 |
|------|------|--------|
| "2020년 이후 이직한 직원" | **불가** | `WHERE CAREER_END_DATE >= '2020-01-01'` |
| "전직장 근무기간 3년 이상" | WORK_MONTHS로 가능 (NULL 위험) | WORK_MONTHS + CAREER_START/END_DATE 양쪽 가능 |

**조치**: 뷰에 `CAREER_START_DATE`, `CAREER_END_DATE` 추가 (확정).

### 3.2 RCAREER_NUM vs CAREER_NUM — 두 개의 경력 개월수

| 컬럼 | 의미 | 뷰 포함 | 샘플값 |
|------|------|:------:|--------|
| `RCAREER_NUM` | **실제** 경력 월수 | O (WORK_MONTHS) | 33, 51, 42 |
| `CAREER_NUM` | **인정** 경력 개월수 (인정률 적용) | X | 32, 50, 41 |

**판단**: NL2SQL에서 "전직장 근무기간"은 **실제 기간**(RCAREER_NUM)이 적합. 현행 유지. CAREER_NUM은 HR 내부용이므로 뷰 미포함 유지.

### 3.3 RCAREER_NUM NULL 가능성 — 톤 완화

샘플 데이터에서 RCAREER_NUM이 채워져 있으나, 전체 데이터에서의 NULL 비율은 확인 필요. PHM_EMP.CAREER_NUM이 전부 NULL이었던 전례가 있으므로 주의.

### 3.4 LEFT JOIN 필수 — 02(V_AI_ADDRESS)와 동일 패턴

경력 미등록 직원은 V_AI_CAREER에 행이 없으므로, **반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 필수**.

```sql
-- ✅ 올바른 패턴
SELECT a.EMP_NAME, b.PREV_COMPANY
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_CAREER b ON a.EMP_ID = b.EMP_ID;

-- ❌ 잘못된 패턴
SELECT * FROM V_AI_CAREER;  -- 경력 미등록 직원 누락
```

### 3.5 DEPT_NM(근무처명) — 뷰 미포함

원본에 `DEPT_NM`(근무처명)이 존재하나 뷰에 미포함. NL2SQL에서 "전직장 부서"를 질의하는 빈도가 낮으므로 추가하지 않음. 필요 시 추후 검토.

### 3.6 RETIRE_CAUSE — 자유 텍스트 추정

COMMENT에 '퇴직사유', VARCHAR2(500). 샘플에서 NULL만 보이나, 자유 텍스트일 가능성 높음 (코드값이면 보통 VARCHAR2(50) 이하). 데이터 확인 후 확정.

---

## 4. 카탈로그 vs 뷰 DDL 비교

### 4.1 현재 뷰 컬럼

| DDL 컬럼 | 원본 컬럼 | 카탈로그 등재 | 비고 |
|----------|----------|:----------:|------|
| EMP_ID | EMP_ID | O (FK) | |
| PREV_COMPANY | ORG_CORP_NM | O | |
| LOCATION | PLACE_NM | **X** | 활용도 낮음, 미등재 적절 |
| PREV_POSITION | POSITION_NM | O | |
| WORK_MONTHS | RCAREER_NUM | O | NULL 가능 주의 |
| WORK_YEARS | RCAREER_NUM/12 | O | NULL 가능 주의 |
| RECOGNITION_RATE | RECO_RATE | **X** | HR 내부 개념, 미등재 적절 |
| LEAVE_REASON | RETIRE_CAUSE | **X** → 추가 | 카탈로그에 추가 |

### 4.2 개선안에서 추가하는 컬럼

| 추가 컬럼 | 원본 컬럼 | 타입 | 비고 |
|----------|----------|------|------|
| CAREER_START_DATE | STA_YMD | DATE NOT NULL | **신규** — 전직장 근무 시작일 |
| CAREER_END_DATE | END_YMD | DATE NOT NULL | **신규** — 전직장 근무 종료일 |

---

## 5. 개선 사항

### 5.1 뷰 개선 — STA_YMD/END_YMD 추가 (확정)

```sql
PC.STA_YMD   AS CAREER_START_DATE,    -- 전직장 근무 시작일
PC.END_YMD   AS CAREER_END_DATE,      -- 전직장 근무 종료일
```

### 5.2 카탈로그 개선 (확정)

```python
# 현재
"v_ai_career": {
    "description": "이전 직장 경력 정보",
    "columns": [
        "EMP_ID (FK)",
        "PREV_COMPANY (전 직장명)",
        "PREV_POSITION (전 직장 직위)",
        "WORK_MONTHS (근무 개월수)",
        "WORK_YEARS (근무 연수)",
    ],
    "keywords": ["경력", "전직장", "이전회사", "근무경력"],
    "join_key": "EMP_ID",
    "relation": "1:N",
    ...
}

# 변경
"v_ai_career": {
    "description": "이전 직장 경력 정보 (1:N, 경력 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 경력 미등록 직원은 행 없음)",
        "PREV_COMPANY ★전 직장명",
        "PREV_POSITION (전 직장 직위)",
        "CAREER_START_DATE (전직장 근무 시작일)",
        "CAREER_END_DATE (전직장 근무 종료일)",
        "WORK_MONTHS (전 직장 실제 근무 개월수, NULL 가능)",
        "WORK_YEARS (전 직장 근무 연수, NULL 가능)",
        "LEAVE_REASON (퇴직사유)",
    ],
    "keywords": ["경력", "전직장", "이전회사", "근무경력", "경력직", "이직", "전직", "퇴직사유"],
    "join_key": "EMP_ID",
    "relation": "1:N",
    "related_tables": ["v_ai_employee"],
}
```

### 5.3 table_catalog.py 반영 코드

`app/core/database/table_catalog.py`의 `_DEFAULT_CATALOG`에서 `v_ai_career` 항목을 아래로 교체:

```python
"v_ai_career": {
    "description": "이전 직장(전직장) 경력 이력 — 현재 직장은 포함하지 않음. 1:N 관계 (1인 다건). 경력 미등록 직원은 행 없음 → V_AI_EMPLOYEE 기준 LEFT JOIN 권장. 직원 이름/재직여부 필터 불필요 시 단독 조회 가능",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE.EMP_ID, 경력 미등록 직원은 행 없음)",
        "PREV_COMPANY ★전 직장 회사명 (LIKE '%회사명%'으로 검색)",
        "PREV_POSITION (전 직장 최종 직위)",
        "CAREER_START_DATE ★전직장 근무 시작일 (DATE NOT NULL, 이직 시기 질의 시 사용)",
        "CAREER_END_DATE ★전직장 근무 종료일 (DATE NOT NULL, 이직 시기 질의 시 사용)",
        "WORK_MONTHS (전 직장 실제 근무 개월수, NULL 가능 — NULL이면 CAREER_START/END_DATE로 계산)",
        "WORK_YEARS (전 직장 근무 연수 = WORK_MONTHS/12 내림, NULL 가능)",
        "LEAVE_REASON (전직장 퇴직사유, 자유 텍스트)",
    ],
    "keywords": ["경력", "전직장", "이전회사", "근무경력", "경력직", "이직", "전직", "퇴직사유", "출신회사", "경력사항"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 전직장 수만큼 행 존재, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 5.4 fewshot 예제 추가 (tb_docs)

V_AI_CAREER는 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN으로 사용해야 한다.

**추가 예제 1: 전직장 경력 조회** (기존 DB 포맷 준수)
```
title: 전직장 경력 조회
doc_type: query_example
usage_type: rag_action

content:
전직장 경력
이전 회사 이력
전 직장 근무 이력
경력사항 조회
- V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER
- 1:N 관계 (1인 다건)

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.PREV_COMPANY, b.PREV_POSITION,
       b.CAREER_START_DATE, b.CAREER_END_DATE,
       b.WORK_MONTHS
FROM v_ai_employee a
LEFT JOIN v_ai_career b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
ORDER BY a.EMP_NAME, b.CAREER_START_DATE
```

## 핵심 패턴
- LEFT JOIN 필수: 경력 미등록 직원 존재
- 1:N: 한 직원이 여러 전직장 → 결과 행 수 > 직원 수
- 직원 수 집계 시 COUNT(DISTINCT a.EMP_ID) 사용
```

**추가 예제 2: 전직장 N곳 이상 경력자** (기존 DB 포맷 준수)
```
title: 다수 전직장 경력자 조회
doc_type: query_example
usage_type: rag_action

content:
전직장 3곳 이상
이직 많은 직원
경력 많은 사람
전직장 개수
- V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER
- GROUP BY + HAVING COUNT

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, COUNT(b.EMP_ID) AS career_count
FROM v_ai_employee a
LEFT JOIN v_ai_career b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
GROUP BY a.EMP_ID, a.EMP_NAME, a.DEPARTMENT
HAVING COUNT(b.EMP_ID) >= :건수
ORDER BY career_count DESC
```

## 핵심 패턴
- LEFT JOIN: 경력 없는 직원은 career_count=0
- COUNT(b.EMP_ID): NULL 제외 → 경력 건수만 집계
- :건수 파라미터: 3곳 이상, 5곳 이상 등
```

**추가 예제 3: 특정 회사 출신 직원** (기존 DB 포맷 준수)
```
title: 특정 전직장 출신 직원 조회
doc_type: query_example
usage_type: rag_action

content:
삼성 출신 직원
전 직장이 현대인 사람
이전 회사가 :회사명인 직원
특정 회사 경력자
- V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER
- PREV_COMPANY LIKE 검색

context_data:
## SQL
```sql
SELECT DISTINCT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.PREV_COMPANY, b.PREV_POSITION
FROM v_ai_employee a
LEFT JOIN v_ai_career b ON a.EMP_ID = b.EMP_ID
WHERE b.PREV_COMPANY LIKE '%' || ':회사명' || '%'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LIKE '%:회사명%': 회사명 부분 매칭
- DISTINCT: 동일 회사에서 다건 경력 시 중복 제거
- LEFT JOIN: 경력 미등록 직원은 WHERE에서 자연 제외
```

**추가 예제 4: 재직자 전직장 평균 근무기간** (JOIN 필요 — 재직자 필터)
```
title: 전직장 평균 근무기간 조회
doc_type: query_example
usage_type: rag_action

content:
전직장 평균 근무기간
이전 직장 평균 근속
전직장 평균 몇 년 다녔는지
경력 평균 기간
- V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER
- 재직자 기준 평균

context_data:
## SQL
```sql
SELECT ROUND(AVG(b.WORK_MONTHS), 1) AS avg_work_months,
       ROUND(AVG(b.WORK_MONTHS) / 12, 1) AS avg_work_years
FROM v_ai_employee a
LEFT JOIN v_ai_career b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.WORK_MONTHS IS NOT NULL
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- NULL 방어: WHERE b.WORK_MONTHS IS NOT NULL
- 전체 대상(재직+퇴직): WHERE 절에서 WORK_STATUS 조건 제거
```

**추가 예제 5: 재직자 출신 회사 통계** (JOIN 필요 — 재직자 필터)
```
title: 전직장 회사별 빈도 조회
doc_type: query_example
usage_type: rag_action

content:
가장 많이 거친 전직장
전직장 회사 순위
출신 회사 통계
어디서 많이 오는지
- V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER
- 재직자 기준 PREV_COMPANY GROUP BY

context_data:
## SQL
```sql
SELECT b.PREV_COMPANY, COUNT(*) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_career b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.PREV_COMPANY IS NOT NULL
GROUP BY b.PREV_COMPANY
ORDER BY emp_count DESC
FETCH FIRST 20 ROWS ONLY
```

## 핵심 패턴
- LEFT JOIN 필수: 재직자 필터(WORK_STATUS)는 V_AI_EMPLOYEE에만 존재
- FETCH FIRST: 상위 N건
- 전체 대상(재직+퇴직): WHERE 절에서 WORK_STATUS 조건 제거
```

---

## 6. V_AI_EMPLOYEE CAREER vs V_AI_CAREER 혼동 주의

**NL2SQL에서 가장 위험한 혼동**: "경력"이라는 키워드가 두 가지 의미로 사용됨.

| 질의 | 의도 | 올바른 테이블 | 올바른 컬럼 |
|------|------|-------------|------------|
| "5년 이상 근속자" | **현 직장** 재직 연수 | V_AI_EMPLOYEE | CAREER_YEARS |
| "전직장 경력 3년 이상" | **이전 직장** 근무 연수 | V_AI_CAREER | WORK_YEARS |
| "경력직 입사자" | 채용유형 | V_AI_EMPLOYEE | HIRE_TYPE = '입사(경력)' |
| "전 직장이 삼성인 직원" | 전직장명 | V_AI_CAREER | PREV_COMPANY |

**카탈로그 차별화 전략**:
- V_AI_EMPLOYEE: keywords에 "근속", "재직연수" 강조
- V_AI_CAREER: keywords에 "전직장", "이전회사", "이직" 강조
- V_AI_EMPLOYEE.CAREER_YEARS: "★재직 연수 (현 직장 근속연수)" 표기
- V_AI_CAREER.WORK_YEARS: "전 직장 근무 연수" 표기

---

## 7. 수정 SQL 전문

### 7.1 V_AI_CAREER 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_CAREER source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_CAREER" (
    "EMP_ID", "PREV_COMPANY", "LOCATION", "PREV_POSITION",
    "CAREER_START_DATE", "CAREER_END_DATE",
    "WORK_MONTHS", "WORK_YEARS", "RECOGNITION_RATE", "LEAVE_REASON"
) AS
SELECT
    PC.EMP_ID                   AS EMP_ID,
    PC.ORG_CORP_NM              AS PREV_COMPANY,
    PC.PLACE_NM                 AS LOCATION,
    PC.POSITION_NM              AS PREV_POSITION,
    -- [추가] 전직장 근무 시작/종료일 (PHM_CAREER.STA_YMD/END_YMD, DATE NOT NULL)
    PC.STA_YMD                  AS CAREER_START_DATE,
    PC.END_YMD                  AS CAREER_END_DATE,
    -- WORK_MONTHS: PHM_CAREER.RCAREER_NUM (실제경력월수, NULL 가능)
    PC.RCAREER_NUM              AS WORK_MONTHS,
    TRUNC(PC.RCAREER_NUM / 12)  AS WORK_YEARS,
    PC.RECO_RATE                AS RECOGNITION_RATE,
    PC.RETIRE_CAUSE             AS LEAVE_REASON
FROM PHM_CAREER PC;

GRANT SELECT ON "H552_RND"."V_AI_CAREER" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_CAREER IS '사원 이전 직장 경력 (EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N). 경력 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT
COMMENT ON COLUMN H552_RND.V_AI_CAREER.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.PREV_COMPANY IS '전직장 근무기관명';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.LOCATION IS '전직장 소재지';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.PREV_POSITION IS '전직장 최종직위';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.CAREER_START_DATE IS '전직장 근무 시작일 (DATE, NOT NULL)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.CAREER_END_DATE IS '전직장 근무 종료일 (DATE, NOT NULL)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.WORK_MONTHS IS '전직장 실제 근무 개월수 (PHM_CAREER.RCAREER_NUM, NULL 가능)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.WORK_YEARS IS '전직장 근무 연수 (WORK_MONTHS/12 내림, NULL 가능)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.RECOGNITION_RATE IS '경력 인정 비율 (%, HR 내부 관리용 — NL2SQL 미사용)';
COMMENT ON COLUMN H552_RND.V_AI_CAREER.LEAVE_REASON IS '전직장 퇴직사유';
```

### 7.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **컬럼 추가** | 8개 | **10개** (+CAREER_START_DATE, +CAREER_END_DATE) | 시기 기반 질의 가능 |
| TABLE COMMENT | `'사원 이전 직장 경력 (..., 1:N)'` | LEFT JOIN 필수 + 경력 미등록 직원 미포함 명시 | |
| WORK_MONTHS COMMENT | `'해당 직장 근무 개월 수'` | `'전직장 실제 근무 개월수 (... NULL 가능)'` | 원천 + NULL 주의 |
| LEAVE_REASON COMMENT | (없음) | `'전직장 퇴직사유'` | **신규** |
| CAREER_START_DATE | (없음) | `'전직장 근무 시작일 (DATE, NOT NULL)'` | **신규** |
| CAREER_END_DATE | (없음) | `'전직장 근무 종료일 (DATE, NOT NULL)'` | **신규** |

---

## 8. 검증 계획

### 8.1 데이터 정합성

```sql
-- 1) 전체 건수 + 1인 평균 경력 수
SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT EMP_ID) AS distinct_emp,
       ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT EMP_ID), 1) AS avg_career_per_emp
FROM PHM_CAREER;

-- 2) RCAREER_NUM NULL 비율
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN RCAREER_NUM IS NOT NULL THEN 1 ELSE 0 END) AS has_value,
    ROUND(SUM(CASE WHEN RCAREER_NUM IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS null_pct
FROM PHM_CAREER;

-- 3) 주요 컬럼 NULL 비율 일괄
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN ORG_CORP_NM IS NULL THEN 1 ELSE 0 END) AS null_company,
    SUM(CASE WHEN PLACE_NM IS NULL THEN 1 ELSE 0 END) AS null_location,
    SUM(CASE WHEN POSITION_NM IS NULL THEN 1 ELSE 0 END) AS null_position,
    SUM(CASE WHEN RCAREER_NUM IS NULL THEN 1 ELSE 0 END) AS null_months,
    SUM(CASE WHEN RECO_RATE IS NULL THEN 1 ELSE 0 END) AS null_recorate,
    SUM(CASE WHEN RETIRE_CAUSE IS NULL THEN 1 ELSE 0 END) AS null_reason
FROM PHM_CAREER;

-- 4) RETIRE_CAUSE 값 형태 확인 (코드 vs 텍스트)
SELECT RETIRE_CAUSE, COUNT(*) AS cnt
FROM PHM_CAREER
WHERE RETIRE_CAUSE IS NOT NULL
GROUP BY RETIRE_CAUSE
ORDER BY cnt DESC
FETCH FIRST 20 ROWS ONLY;

-- 5) 경력 미등록 직원 수
SELECT COUNT(*) AS no_career_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_CAREER b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 6) JOIN 후 결과 행 수 확인
SELECT COUNT(*) FROM (
    SELECT a.EMP_ID
    FROM V_AI_EMPLOYEE a
    LEFT JOIN V_AI_CAREER b ON a.EMP_ID = b.EMP_ID
);
-- 기대: V_AI_EMPLOYEE 건수 이상 (1:N이므로)
```

### 8.2 NL2SQL 테스트 질의

| 질문 | 기대 동작 |
|------|----------|
| "경력직 입사자 수" | V_AI_EMPLOYEE + `HIRE_TYPE LIKE '%경력%'` (**V_AI_CAREER 아님**) |
| "전직장이 삼성인 직원" | V_AI_EMPLOYEE LEFT JOIN V_AI_CAREER + `PREV_COMPANY LIKE '%삼성%'` |
| "전직장 3곳 이상 경력자" | LEFT JOIN + `GROUP BY EMP_ID HAVING COUNT(b.EMP_ID) >= 3` |
| "2020년 이후 이직한 직원" | LEFT JOIN + `CAREER_END_DATE >= '2020-01-01'` |
| "평균 전직장 근무기간" | `AVG(WORK_MONTHS)` (NULL 방어) |

---

## 9. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **STA_YMD/END_YMD 미포함** | 뷰에 없음 | CAREER_START_DATE, CAREER_END_DATE 추가 | **확정** |
| **LEFT JOIN 필수** | 미명시 | 카탈로그 + COMMENT + fewshot에 명시 | **확정** |
| RCAREER_NUM NULL 비율 | 샘플에서는 채워져 있으나 전체 확인 필요 | DB 조회로 확인 | 검증 필요 |
| RETIRE_CAUSE 형태 | 자유 텍스트 추정 (VARCHAR2(500)) | DB 조회로 확인 | 검증 필요 |
| 카탈로그 키워드 | 4개 | "경력직", "이직", "전직", "퇴직사유" 추가 | **확정** |
| CAREER vs WORK 혼동 방지 | 미조치 | 카탈로그에서 V_AI_EMPLOYEE/V_AI_CAREER 의미 차별화 | **확정** |
| COMMENT 보강 | 기본 수준 | LEFT JOIN 필수, 1:N, NULL 가능, STA/END 추가 | **확정** |
| fewshot 예제 | 없음 | 5건 추가 (LEFT JOIN 3건 + 단독 조회 2건) | **확정** |

---

## 10. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: 뷰 구조 분석, RCAREER_NUM NULL 이슈, 카탈로그/COMMENT 개선안, CAREER 혼동 방지 |
| 2026-03-17 | PHM_CAREER 원본 테이블 분석: STA_YMD/END_YMD 존재 확인, 뷰 컬럼 추가 확정, LEFT JOIN 필수 명시, fewshot 3건 추가 |
