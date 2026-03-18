# V_AI_ADDRESS 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_ADDRESS`
> 원본 테이블: `docs/sql/orcl-business_org_db.sql` — `PHM_ADDR`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음 — 필터 없이 전체 행 노출)

```sql
-- H552_RND.V_AI_ADDRESS source (현재 — 문제 있는 버전)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_ADDRESS" (
    "EMP_ID", "ADDRESS", "ADDRESS_DETAIL", "ZIP_CODE", "REGION", "MOD_DATE"
) AS
SELECT
    PA.EMP_ID                   AS EMP_ID,
    PA.ADDR                     AS ADDRESS,
    PA.DETAIL_ADDR              AS ADDRESS_DETAIL,
    PA.ZIP_NO                   AS ZIP_CODE,
    CASE
        WHEN PA.ADDR LIKE '서울%' THEN '서울'
        WHEN PA.ADDR LIKE '부산%' THEN '부산'
        WHEN PA.ADDR LIKE '대구%' THEN '대구'
        WHEN PA.ADDR LIKE '인천%' THEN '인천'
        WHEN PA.ADDR LIKE '광주%' THEN '광주'
        WHEN PA.ADDR LIKE '대전%' THEN '대전'
        WHEN PA.ADDR LIKE '울산%' THEN '울산'
        WHEN PA.ADDR LIKE '세종%' THEN '세종'
        WHEN PA.ADDR LIKE '경기%' THEN '경기'
        WHEN PA.ADDR LIKE '강원%' THEN '강원'
        WHEN PA.ADDR LIKE '충북%' OR PA.ADDR LIKE '충청북%' THEN '충북'
        WHEN PA.ADDR LIKE '충남%' OR PA.ADDR LIKE '충청남%' THEN '충남'
        WHEN PA.ADDR LIKE '전북%' OR PA.ADDR LIKE '전라북%' THEN '전북'
        WHEN PA.ADDR LIKE '전남%' OR PA.ADDR LIKE '전라남%' THEN '전남'
        WHEN PA.ADDR LIKE '경북%' OR PA.ADDR LIKE '경상북%' THEN '경북'
        WHEN PA.ADDR LIKE '경남%' OR PA.ADDR LIKE '경상남%' THEN '경남'
        WHEN PA.ADDR LIKE '제주%' THEN '제주'
        ELSE '기타'
    END                         AS REGION,
    PA.MOD_DATE                 AS MOD_DATE
FROM PHM_ADDR PA;
-- ★ 문제: WHERE 없음 → ADDR_TYPE_CD(주소유형) + STA_YMD/END_YMD(이력) 전체 노출
-- ★ 결과: 1인 N건 → V_AI_EMPLOYEE와 JOIN 시 곱집합 발생

GRANT SELECT ON "H552_RND"."V_AI_ADDRESS" TO "MUSER";

COMMENT ON TABLE H552_RND.V_AI_ADDRESS IS '사원 주소 정보 (EMP_ID로 V_AI_EMPLOYEE와 JOIN)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ADDRESS IS '기본 주소';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ADDRESS_DETAIL IS '상세 주소';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ZIP_CODE IS '우편번호';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.REGION IS '거주 시/도 (서울, 경기 등)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.MOD_DATE IS '수정일시';
```

**소스**: `PHM_ADDR` 단일 테이블, FRM_CODE JOIN 없음.
**문제**: PHM_ADDR의 UK는 `(EMP_ID, ADDR_TYPE_CD, STA_YMD)` → 주소유형별 + 유효기간별 복수 행이 필터 없이 전부 노출됨.

---

## 2. PHM_ADDR 원본 테이블 분석

### 2.1 테이블 구조

```
PHM_ADDR_ID      NUMBER         PK    주소ID
EMP_ID           NUMBER         FK    사원ID
PERSON_ID        NUMBER               개인ID
ADDR_TYPE_CD     VARCHAR2(50)   NN    주소종류코드 [PHM_ADDR_TYPE_CD]
STA_YMD          DATE           NN    시작일자
END_YMD          DATE           NN    종료일자
NATION_CD        VARCHAR2(50)         국가코드 [PHM_NATION_CD]
AREA_CD          VARCHAR2(50)         국가지역코드 [PHM_AREA_CD]
ZIP_NO           VARCHAR2(50)         우편번호
ADDR             VARCHAR2(200)        주소
DETAIL_ADDR      VARCHAR2(200)        상세주소
LAT              VARCHAR2(30)         위도 (사용안함)
LNG              VARCHAR2(30)         경도 (사용안함)
NOTE             VARCHAR2(200)        비고
MOD_USER_ID      NUMBER         NN    변경자
MOD_DATE         DATE           NN    변경일시
TZ_CD            VARCHAR2(10)   NN    타임존코드
TZ_DATE          DATE           NN    타임존일시
SIGUNGU_CD       VARCHAR2(5)          시군구코드
```

### 2.2 인덱스/제약 조건

| 제약 | 컬럼 | 의미 |
|------|------|------|
| **PK** | `PHM_ADDR_ID` | 주소 ID |
| **UK** | `(EMP_ID, ADDR_TYPE_CD, STA_YMD)` | 사원 + 주소유형 + 시작일 = 유일 |
| **INDEX** | `(EMP_ID, STA_YMD, END_YMD, ADDR_TYPE_CD)` | 유효기간 검색 최적화 |

### 2.3 중복 원인 — 확정

**UK 구조가 핵심**: `(EMP_ID, ADDR_TYPE_CD, STA_YMD)`

동일 EMP_ID에 대해 **2가지 축으로 복수 행 발생**:

| 축 | 설명 | 예시 |
|----|------|------|
| **ADDR_TYPE_CD** | 주소 종류별 별도 행 | 현주소('01'), 본적, 비상연락처 등 |
| **STA_YMD/END_YMD** | 동일 유형 내 이력 관리 | 2020~2023 서울 → 2023~2999 경기 (이사) |

### 2.4 샘플 데이터 분석

```sql
-- 샘플: ADDR_TYPE_CD='01', STA_YMD=1900-01-01, END_YMD=2999-12-31
(508, 2485, 2485, '01', 1900-01-01, 2999-12-31, 'KR', '11', '730-140', '경북 구미시 오태동', ...)
```

- `ADDR_TYPE_CD = '01'`: 현주소 코드
- `STA_YMD = 1900-01-01`: "시작일 미지정" 패턴 (기존 데이터 마이그레이션)
- `END_YMD = 2999-12-31`: "현재 유효" 패턴

---

## 3. 이슈 분석

### 3.1 JOIN 시 중복 — 확정된 문제

```sql
-- 현재: 중복 발생
SELECT a.emp_id FROM v_ai_employee a
LEFT JOIN v_ai_address b ON a.emp_id = b.emp_id;
-- → V_AI_EMPLOYEE 건수보다 많은 행 반환
```

**원인**: PHM_ADDR에 필터 없이 전체 행을 노출하므로, 1인 N건(주소 유형별 + 이력별)이 JOIN에서 곱집합을 발생시킨다.

**NL2SQL 영향**:

| 질의 | 기대 | 실제 (현재) |
|------|------|------------|
| "서울 거주 직원 수" | 정확한 인원수 | **과다 집계** (이력 건수만큼 중복) |
| "지역별 분포" | 1인 1건 기준 | **이중 카운트** (이사 이력 포함) |
| "경기도 과장 목록" | 1인 1행 | **동일인 복수 행** |

### 3.2 시간축(Temporal) 질의 — WHERE 필터로 해결

**현재 뷰**: `STA_YMD`/`END_YMD`를 SELECT하지 않고 WHERE에서도 사용하지 않으므로, "현재 주소"와 "과거 주소"를 구분할 수 없다.

**개선안**: 뷰에 `STA_YMD`/`END_YMD`를 컬럼으로 노출할 필요는 없고, **WHERE 절에서 현재 유효 기간만 필터**하면 된다. NL2SQL에서 주소 이력 질의("이전에 서울에 살았던 직원")는 빈도가 극히 낮으므로, **현재 유효 주소 1건만 제공**하는 것이 NL2SQL에 적합하다.

```sql
-- 개선: WHERE에서 유효기간 필터 (뷰 컬럼 추가 불필요)
WHERE PA.ADDR_TYPE_CD = '01'
  AND PA.STA_YMD <= SYSDATE
  AND PA.END_YMD >= SYSDATE
```

### 3.3 REGION 매핑 — 이상 없음

`LIKE '강원%'`, `LIKE '전북%'`는 2023년 행정구역 개편('강원특별자치도', '전북특별자치도')에도 매칭됨. 주석으로 기록만 추가.

### 3.4 ADDRESS / ADDRESS_DETAIL — PII

NL2SQL에서 주소 뷰의 주된 목적은 **REGION 기반 집계**이므로, `table_catalog`에서 ADDRESS/ADDRESS_DETAIL 미등재는 적절한 PII 보호 전략.

---

## 4. 개선 사항

### 4.1 뷰 개선 — WHERE 필터 추가 (확정)

```sql
WHERE PA.ADDR_TYPE_CD = '01'        -- 현주소만 (본적/비상연락처 제외)
  AND PA.STA_YMD <= SYSDATE         -- 시작일이 현재 이전
  AND PA.END_YMD >= SYSDATE         -- 종료일이 현재 이후 (현재 유효)
```

| 조건 | 의미 | 제거 대상 |
|------|------|----------|
| `ADDR_TYPE_CD = '01'` | 현주소만 | 본적, 비상연락처 등 |
| `STA_YMD <= SYSDATE` | 시작된 주소만 | 미래 시작 주소 |
| `END_YMD >= SYSDATE` | 아직 유효한 주소만 | 과거 만료된 이사 전 주소 |

**효과**: 1인 N건 → **1인 0~1건** (현재 유효한 현주소만), V_AI_EMPLOYEE와 JOIN 시 중복 제거.

> **주의 1**: `ADDR_TYPE_CD` 값 도메인 확인 필요. 샘플 데이터에서 '01'은 확인되었으나, 다른 유형 코드도 확인 필요.
> **주의 2**: 주소 미등록 직원은 V_AI_ADDRESS에 행이 없으므로, **반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 필수**. 단독 조회(`SELECT * FROM V_AI_ADDRESS`)로는 전체 직원을 커버하지 못함.

**검증 쿼리**:
```sql
-- ADDR_TYPE_CD 값 분포
SELECT ADDR_TYPE_CD, COUNT(*) AS cnt
FROM PHM_ADDR
GROUP BY ADDR_TYPE_CD
ORDER BY cnt DESC;

-- 필터 적용 후 중복 제거 확인
SELECT COUNT(*) AS total,
       COUNT(DISTINCT EMP_ID) AS distinct_emp
FROM PHM_ADDR
WHERE ADDR_TYPE_CD = '01'
  AND STA_YMD <= SYSDATE
  AND END_YMD >= SYSDATE;
```

### 4.2 카탈로그 개선 (확정)

```python
# 현재
"v_ai_address": {
    "description": "직원 주소/거주지 정보",
    "columns": [
        "EMP_ID (FK)",
        "ADDRESS (기본주소)",
        "REGION ★거주 시/도 (서울,경기,부산 등)",
        "ZIP_CODE (우편번호)",
    ],
    "keywords": ["주소", "거주지", "서울", "경기", "지역", "시도"],
    "join_key": "EMP_ID",
    "relation": "1:N",
    ...
}

# 변경
"v_ai_address": {
    "description": "직원 현재 거주지 정보 (현주소 + 현재 유효 기간만, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 주소 미등록 직원 미포함)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE)",
        "REGION ★거주 시/도 (서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주,기타)",
        "ZIP_CODE (우편번호)",
    ],
    "keywords": ["주소", "거주지", "서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "지역", "시도", "거주"],
    "join_key": "EMP_ID",
    "relation": "1:1",   # ← 1:N에서 1:1로 변경 (현주소 필터 후)
    ...
}
```

**변경 포인트**:
1. `description`: "현재 거주지" 명시 + 1:1 JOIN 명시
2. `relation`: `"1:N"` → `"1:1"` (뷰 필터 적용 후)
3. `columns`: ADDRESS 제거 (PII), REGION에 전체 17개 시도+기타 값 도메인 명시
4. `keywords`: 주요 시도명 전부 추가 (LLM이 "부산 거주자" 질의 시 이 테이블 선택하도록)

### 4.3 table_catalog.py 반영 코드

`app/core/database/table_catalog.py`의 `_DEFAULT_CATALOG`에서 `v_ai_address` 항목을 아래로 교체:

```python
"v_ai_address": {
    "description": "직원 현재 거주지 정보 (현주소 + 현재 유효 기간만 필터, 주소 미등록 직원은 미포함 → LEFT JOIN 필수)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE, 주소 미등록 직원은 행 없음)",
        "REGION ★현재 거주 시/도 (서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주,기타)",
        "ZIP_CODE (우편번호)",
    ],
    "keywords": ["주소", "거주지", "서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "지역", "시도", "거주"],
    "join_key": "EMP_ID",
    "relation": "1:1",
    "related_tables": ["v_ai_employee"],
},
```

### 4.4 fewshot 예제 추가 (tb_docs)

V_AI_ADDRESS는 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN으로 사용해야 한다. 이 패턴을 LLM에 학습시키기 위한 예제:

**추가 예제 1: 지역별 직원 분포** (기존 DB 포맷 준수)
```
title: 지역별 직원 분포 조회
doc_type: query_example
usage_type: rag_action

content:
지역별 직원 분포
시도별 직원 수
서울 경기 거주 직원 수
지역별 인원 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_ADDRESS
- REGION 기준 GROUP BY

context_data:
## SQL
```sql
SELECT NVL(b.REGION, '주소미등록') AS region,
       COUNT(*) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_address b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
GROUP BY NVL(b.REGION, '주소미등록')
ORDER BY emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: 주소 미등록 직원 존재 → INNER JOIN 시 누락
- NVL(REGION, '주소미등록'): NULL 방어
- 특정 지역: WHERE b.REGION = ':지역' 추가
```

**추가 예제 2: 특정 지역 거주 직원 목록** (기존 DB 포맷 준수)
```
title: 특정 지역 거주 직원 조회
doc_type: query_example
usage_type: rag_action

content:
서울 거주 직원
경기도에 사는 직원
부산 사는 사람 목록
:지역 거주자 명단
- V_AI_EMPLOYEE LEFT JOIN V_AI_ADDRESS
- REGION 필터

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION, b.REGION
FROM v_ai_employee a
LEFT JOIN v_ai_address b ON a.EMP_ID = b.EMP_ID
WHERE b.REGION = ':지역'
  AND a.WORK_STATUS = '재직'
ORDER BY a.DEPARTMENT, a.EMP_NAME
```

## 핵심 패턴
- LEFT JOIN 필수: V_AI_ADDRESS는 주소 미등록 직원 미포함
- REGION 값: 서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주
- 복수 지역: WHERE b.REGION IN (':지역1', ':지역2')
```

**추가 예제 3: 지역별 직급 분포** (기존 DB 포맷 준수)
```
title: 지역별 직급 분포 조회
doc_type: query_example
usage_type: rag_action

content:
지역별 직급 분포
서울 거주 과장 수
지역별 직위 현황
시도별 부장 과장 대리 수
- V_AI_EMPLOYEE LEFT JOIN V_AI_ADDRESS
- REGION + POSITION 교차 집계

context_data:
## SQL
```sql
SELECT b.REGION,
       a.POSITION,
       COUNT(*) AS emp_count
FROM v_ai_employee a
LEFT JOIN v_ai_address b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.REGION IS NOT NULL
GROUP BY b.REGION, a.POSITION
ORDER BY b.REGION, emp_count DESC
```

## 핵심 패턴
- LEFT JOIN 필수: V_AI_ADDRESS는 주소 미등록 직원 미포함
- b.REGION IS NOT NULL: 주소 미등록 직원 제외 (집계 정확도)
- 특정 지역만: WHERE b.REGION = ':지역' 추가
```

---

## 5. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| EMP_ID | O (FK) | |
| ADDRESS | **X** | PII — 의도적 미등재 (적절) |
| ADDRESS_DETAIL | **X** | PII — 의도적 미등재 (적절) |
| ZIP_CODE | O | |
| REGION | O (★) | 값 도메인 17개 시도+기타 명시 |
| MOD_DATE | **X** | NL2SQL 무관 — 미등재 적절 |

---

## 6. 수정 SQL 전문

### 6.1 V_AI_ADDRESS 뷰 생성 스크립트 (개선안)

```sql
-- H552_RND.V_AI_ADDRESS source (개선안)

CREATE OR REPLACE FORCE NONEDITIONABLE VIEW "H552_RND"."V_AI_ADDRESS" (
    "EMP_ID", "ADDRESS", "ADDRESS_DETAIL", "ZIP_CODE", "REGION", "MOD_DATE"
) AS
SELECT
    PA.EMP_ID                   AS EMP_ID,
    PA.ADDR                     AS ADDRESS,
    PA.DETAIL_ADDR              AS ADDRESS_DETAIL,
    PA.ZIP_NO                   AS ZIP_CODE,
    -- REGION: 주소 첫 키워드 기반 시/도 분류 (17개 시도 + 기타)
    -- 2023.06 행정구역 개편: 강원특별자치도, 전북특별자치도 → LIKE '강원%', '전북%'로 매칭됨
    CASE
        WHEN PA.ADDR LIKE '서울%' THEN '서울'
        WHEN PA.ADDR LIKE '부산%' THEN '부산'
        WHEN PA.ADDR LIKE '대구%' THEN '대구'
        WHEN PA.ADDR LIKE '인천%' THEN '인천'
        WHEN PA.ADDR LIKE '광주%' THEN '광주'
        WHEN PA.ADDR LIKE '대전%' THEN '대전'
        WHEN PA.ADDR LIKE '울산%' THEN '울산'
        WHEN PA.ADDR LIKE '세종%' THEN '세종'
        WHEN PA.ADDR LIKE '경기%' THEN '경기'
        WHEN PA.ADDR LIKE '강원%' THEN '강원'
        WHEN PA.ADDR LIKE '충북%' OR PA.ADDR LIKE '충청북%' THEN '충북'
        WHEN PA.ADDR LIKE '충남%' OR PA.ADDR LIKE '충청남%' THEN '충남'
        WHEN PA.ADDR LIKE '전북%' OR PA.ADDR LIKE '전라북%' THEN '전북'
        WHEN PA.ADDR LIKE '전남%' OR PA.ADDR LIKE '전라남%' THEN '전남'
        WHEN PA.ADDR LIKE '경북%' OR PA.ADDR LIKE '경상북%' THEN '경북'
        WHEN PA.ADDR LIKE '경남%' OR PA.ADDR LIKE '경상남%' THEN '경남'
        WHEN PA.ADDR LIKE '제주%' THEN '제주'
        ELSE '기타'
    END                         AS REGION,
    PA.MOD_DATE                 AS MOD_DATE
FROM PHM_ADDR PA
-- [추가] 현주소(ADDR_TYPE_CD='01') + 현재 유효(SYSDATE 기준) 1건만
WHERE PA.ADDR_TYPE_CD = '01'
  AND PA.STA_YMD <= SYSDATE
  AND PA.END_YMD >= SYSDATE;

GRANT SELECT ON "H552_RND"."V_AI_ADDRESS" TO "MUSER";

-- 테이블 COMMENT
COMMENT ON TABLE H552_RND.V_AI_ADDRESS IS '사원 현재 거주지 정보 (현주소 + 현재 유효 기간만 필터, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN). 주소 미등록 직원 미포함 — 반드시 V_AI_EMPLOYEE 기준 LEFT JOIN 사용';

-- 컬럼 COMMENT
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ADDRESS IS '현재 거주 주소 (PII — NL2SQL에서 직접 조회 지양, 집계용 REGION 사용 권장)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ADDRESS_DETAIL IS '상세 주소 (PII — NL2SQL에서 직접 조회 지양)';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.ZIP_CODE IS '우편번호';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.REGION IS '거주 시/도 (서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주,기타). ADDR 첫 키워드 기반 자동 분류';
COMMENT ON COLUMN H552_RND.V_AI_ADDRESS.MOD_DATE IS '주소 수정일시';
```

### 6.2 현재 뷰 대비 변경점

| 항목 | 현재 | 개선안 | 비고 |
|------|------|--------|------|
| **WHERE 절** | 없음 | `ADDR_TYPE_CD='01' AND STA_YMD<=SYSDATE AND END_YMD>=SYSDATE` | **핵심 변경 — 중복 제거** |
| 관계 | 1:N (중복 포함) | **1:1** (현주소 1건만) | JOIN 안전성 확보 |
| TABLE COMMENT | `'사원 주소 정보 (...)'` | `'사원 현재 거주지 정보 (현주소 + 현재 유효 기간만 필터, ... 1:1 JOIN)'` | 필터 조건 + 관계 명시 |
| ADDRESS COMMENT | `'기본 주소'` | `'현재 거주 주소 (PII — ...)'` | "현재" 명시 + PII 주의 |
| REGION COMMENT | `'거주 시/도 (서울, 경기 등)'` | 17개 시도 전체 + 기타 열거 | 값 도메인 명시 |
| 뷰 내 주석 | 없음 | WHERE 필터 설명 + 행정구역 개편 주석 | 유지보수용 |

---

## 7. 검증 계획

### 7.1 데이터 정합성

```sql
-- 1) ADDR_TYPE_CD 값 분포 (최우선 — '01' 외 유형 확인)
SELECT ADDR_TYPE_CD, COUNT(*) AS cnt
FROM PHM_ADDR
GROUP BY ADDR_TYPE_CD
ORDER BY cnt DESC;

-- 2) 필터 적용 전후 비교
SELECT 'before' AS phase, COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp FROM PHM_ADDR
UNION ALL
SELECT 'after', COUNT(*), COUNT(DISTINCT EMP_ID)
FROM PHM_ADDR
WHERE ADDR_TYPE_CD = '01' AND STA_YMD <= SYSDATE AND END_YMD >= SYSDATE;

-- 3) 필터 후 1인 다건 여부 (0건이어야 정상)
SELECT EMP_ID, COUNT(*) AS cnt
FROM PHM_ADDR
WHERE ADDR_TYPE_CD = '01' AND STA_YMD <= SYSDATE AND END_YMD >= SYSDATE
GROUP BY EMP_ID HAVING COUNT(*) > 1;

-- 4) JOIN 중복 제거 확인
SELECT COUNT(*) FROM (
    SELECT a.EMP_ID
    FROM V_AI_EMPLOYEE a
    LEFT JOIN V_AI_ADDRESS b ON a.EMP_ID = b.EMP_ID
);
-- 기대: V_AI_EMPLOYEE 건수와 동일 (2,345)

-- 5) 주소 미등록 직원 수 확인
SELECT COUNT(*) AS no_address_emp
FROM V_AI_EMPLOYEE a
LEFT JOIN V_AI_ADDRESS b ON a.EMP_ID = b.EMP_ID
WHERE b.EMP_ID IS NULL;

-- 5) REGION 분포 확인
SELECT REGION, COUNT(*) AS cnt
FROM V_AI_ADDRESS
GROUP BY REGION
ORDER BY cnt DESC;

-- 6) '기타' 지역 상세 확인 (NULL/빈 주소 포함 여부)
SELECT ADDR
FROM V_AI_ADDRESS
WHERE REGION = '기타'
FETCH FIRST 20 ROWS ONLY;
```

### 7.2 NL2SQL 테스트 질의

| 질문 | 기대 동작 |
|------|----------|
| "서울 거주 직원 수" | `JOIN V_AI_ADDRESS` + `WHERE REGION = '서울'` + `COUNT(*)` (중복 없이 정확) |
| "지역별 직원 분포" | `GROUP BY REGION` + `COUNT(*)` (1인 1건 보장) |
| "경기도에 사는 과장" | V_AI_EMPLOYEE + V_AI_ADDRESS JOIN + `REGION = '경기'` + `POSITION = '과장'` |

---

## 8. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **JOIN 중복** | 1인 N건 → 곱집합 발생 | WHERE 필터 추가 (ADDR_TYPE_CD + STA/END_YMD) | **확정** |
| **관계 변경** | 1:N | → **0~1:1** (필터 후, 주소 미등록 시 0건) | **확정** |
| **LEFT JOIN 필수** | 미명시 | V_AI_EMPLOYEE 기준 LEFT JOIN 필수 (카탈로그+COMMENT 명시) | **확정** |
| ADDR_TYPE_CD 값 확인 | '01' 확인, 다른 값 미확인 | DB 조회로 값 도메인 확인 | **검증 필요** |
| REGION 값 도메인 | 카탈로그 미기재 | 17개 시도+기타 전체 명시 | **확정** |
| ADDRESS PII 미등재 | 의도적 미등재 | 현행 유지 (적절) | - |
| MOD_DATE 미등재 | 의도적 미등재 | 현행 유지 (적절) | - |
| COMMENT 보강 | 기본 수준 | "현재 거주지", 1:1, 값 도메인, PII 주의 | **확정** |
| keywords 보강 | 6개 | 시도명 전체 + '거주' 추가 (20개) | **확정** |

---

## 9. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: 뷰 구조 분석, 주소 중복 이슈 식별, 카탈로그/COMMENT 개선안 |
| 2026-03-17 | PHM_ADDR 원본 테이블 분석: UK(EMP_ID, ADDR_TYPE_CD, STA_YMD) 확인, WHERE 필터 확정, 1:1 관계로 변경 |
| 2026-03-17 | 섹션 1 현재 뷰를 실행 가능한 전체 DDL로 변경, 섹션 3.2 시간축 설명 보강, 섹션 4.3 table_catalog.py 반영 코드 추가 |
| 2026-03-17 | 주소 미등록 직원 이슈 반영 (LEFT JOIN 필수), 섹션 4.4 fewshot 예제 3건 추가 |
