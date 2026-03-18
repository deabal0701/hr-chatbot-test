# V_AI_FEEDBACK 뷰 분석 및 개선

> 원본 뷰: `docs/sql/orcl-business_view_db.sql` — `V_AI_FEEDBACK`
> 관련 코드: `app/core/database/table_catalog.py`, `app/graphs/nl2sql/nodes.py`

---

## 1. 현재 뷰 구조 (문제 있음 — Oracle 함수 의존 + VI_FRM_PHM_EMP 중복 가능)

현재 배포된 뷰의 핵심 구조:

```
FROM (서브쿼리)
  PEE_DEFINITION A          — 평가 정의
  PEE_APPR_AGGREGATE B      — 평가 종합
  PEE_RATEE C               — 피평가자
  PEE_APPR_RESULT D         — 평가 결과
  VI_FRM_PHM_EMP E          — ★HR 시스템 내부 뷰 (PHM_EMP 기반)
WHERE A.PEE_DEFINITION_ID = B.PEE_DEFINITION_ID
  AND B.APPR_ID = C.APPR_ID
  AND C.RATEE_ID = D.RATEE_ID
  AND C.RATEE_EMP_ID = E.EMP_ID
  AND A.COMPANY_CD = E.COMPANY_CD
```

**Oracle 함수 의존** (뷰 내부에서 사용):
- `F_FRM_CODE_NM()` — 코드명 변환 (4곳: PEE_TYPE_NM, RATEE_LEVEL_NM, APPR_GRADE, PEE_TYPE_NM)
- `F_FRM_ORM_ORG_NM()` — 조직명 변환 (2곳: EMP_ORG_NM, RATEE_ORG_NM)
- `F_PEE_GET_RATEE_GROUP_INFO()` — 평가 그룹 정보 (RATEE_GROUP_NM)
- `F_PEE_GET_APPR_GRADE_RANK()` — 등급 랭킹 (RK)
- `F_PEE_GET_APPR_OPINION()` — 평가 의견 (PEE_OPINION)
- `XF_NVL_C()` — NVL 래퍼 (6곳)

> 현재 뷰 전체 DDL은 `docs/sql/orcl-business_view_db.sql:214-321` 참조.

---

## 2. 이슈 분석

### 2.1 COMPANY_CD 중복 파급 (확인 필요)

**배경**: 01 문서에서 PHM_EMP에 COMPANY_CD='01'(주소속) + '02'(겸직) 복수 소속 4명 확인.

**위험**: `VI_FRM_PHM_EMP`는 PHM_EMP 기반 내부 뷰. 이 4명이 VI_FRM_PHM_EMP에도 존재하면:
- `A.COMPANY_CD = E.COMPANY_CD` 조건이 있으므로, PEE_DEFINITION에 '02' 영역 평가가 **없으면** 자연 필터됨
- '02' 영역 평가 데이터가 **있으면** 중복 발생

**현재 판단**: 평가(PEE_*) 데이터는 대부분 COMPANY_CD='01'에만 존재할 가능성이 높으나, DB 조회로 확인 필요.

**확인 필요 쿼리**:
```sql
-- 1) VI_FRM_PHM_EMP 중복 확인
SELECT COUNT(*), COUNT(DISTINCT EMP_ID) FROM VI_FRM_PHM_EMP;

-- 2) V_AI_FEEDBACK 중복 확인
SELECT COUNT(*), COUNT(DISTINCT EMP_ID) FROM V_AI_FEEDBACK;

-- 3) COMPANY_CD별 평가 건수 (중복 진단)
SELECT COMPANY_CD, COUNT(*) FROM V_AI_FEEDBACK GROUP BY COMPANY_CD;

-- 4) 1인 다건 평가 확인 (정상적 1:N인지 중복인지)
SELECT EMP_ID, COUNT(*) AS cnt
FROM V_AI_FEEDBACK
GROUP BY EMP_ID
HAVING COUNT(*) > 10
ORDER BY cnt DESC
FETCH FIRST 10 ROWS ONLY;
```

### 2.2 컬럼 명명 불일치

| DDL 컬럼명 | SELECT alias | 문제 |
|-----------|-------------|------|
| `RATEE_GROUP_NAME` | `Employee_group_name` | DDL과 alias 불일치 |
| `RATEE_ORG_NM` | `Employee_org_name_R` | 의미 불명확 (_R 접미사) |
| `RATEE_ORG_ID` | `Employee_org_identifier_R` | 의미 불명확 |
| `APPR_OPINION_OPEN_YN` | `Whether_opinion_are_disclosed_` | trailing underscore |

→ DDL 컬럼명이 실제 노출 이름이므로 SELECT alias는 무관. **DDL 컬럼명 기준으로 카탈로그 작성**.

### 2.3 NL2SQL 활용도 분석

| 컬럼 | NL2SQL 활용도 | 카탈로그 등재 | 비고 |
|------|:----------:|:----------:|------|
| EMP_ID | FK | O | 조인키 |
| APPR_NM | ★높음 | O | 평가 명칭 |
| PEE_TYPE_NM | 중간 | O | 평가 종류명 |
| EMP_ORG_NM | 중간 | O | 평가 시점 소속부서 |
| APPR_SCORE | ★높음 | O | 평가 점수 (0 초과 시만 유효) |
| APPR_GRADE | ★높음 | O | 평가 등급 (S,A,B,C,D) |
| RK | 중간 | O | 등급 내 순위 |
| PEE_OPINION | 낮음 | O | 평가자 의견 (텍스트) |
| APPR_YMD | ★높음 | O | 평가일자 |
| END_YMD | 중간 | O | 평가종료일 |
| COMPANY_CD, LOCALE_CD | 낮음 | **X** | 내부 코드 |
| PEE_DEFINITION_ID, APPR_ID | 낮음 | **X** | 내부 PK |
| RATEE_* (5개) | 낮음 | **X** | 피평가자 그룹/레벨 — 중복/내부용 |
| *_OPEN_YN (4개) | 낮음 | **X** | 공개 여부 플래그 |

### 2.4 DDL 변경 리스크

이 뷰는 Oracle 전용 함수 6종에 의존하므로, **DDL 구조를 크게 변경하면 리스크가 높음**:
- `F_FRM_CODE_NM`, `F_FRM_ORM_ORG_NM` 등은 HR 시스템 내장 함수
- 함수 시그니처를 모르므로 대체 구현 불가
- COMPANY_CD 필터만 추가하는 **최소 변경**이 적절

---

## 3. 개선 사항

### 3.1 뷰 개선 — 최소 변경 (조건부)

**DB 검증 결과에 따라 조치**:

| 검증 결과 | 조치 |
|----------|------|
| COMPANY_CD='02' 평가 데이터 **없음** | DDL 변경 불필요 (자연 필터) |
| COMPANY_CD='02' 평가 데이터 **있음** | WHERE 절에 `E.COMPANY_CD = '01'` 추가 |

```sql
-- 조건부 수정 (중복 확인 후)
WHERE A.PEE_DEFINITION_ID = B.PEE_DEFINITION_ID
  AND B.APPR_ID = C.APPR_ID
  AND C.RATEE_ID = D.RATEE_ID
  AND C.RATEE_EMP_ID = E.EMP_ID
  AND A.COMPANY_CD = E.COMPANY_CD
  AND E.COMPANY_CD = '01'    -- [추가] 주 인사영역만 (중복 확인 후)
```

### 3.2 COMMENT 보강

```sql
COMMENT ON TABLE H552_RND.V_AI_FEEDBACK IS '인사평가 결과 (EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN, 1:N — 평가 횟수만큼 행 존재). 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수';

COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_NM IS '평가명 (연간인사평가, 수시평가 등)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.PEE_TYPE_NM IS '평가 종류명';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.EMP_ORG_NM IS '평가 시점 소속 부서명';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_SCORE IS '평가 점수 (숫자, 0 초과 시만 유효)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_GRADE IS '평가등급 (S,A,B,C,D 등)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.RK IS '등급 내 순위';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.PEE_OPINION IS '평가자 의견 (텍스트)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_YMD IS '평가일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.END_YMD IS '평가종료일자 (DATE)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.PEE_TYPE_CD IS '평가 종류 코드';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.EMP_ORG_ID IS '소속 부서 코드';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.RATEE_GROUP_ID IS '피평가 그룹 코드';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.RATEE_LEVEL_CD IS '직책 코드';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.RATEE_LEVEL_NM IS '직책명';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_SCORE_OPEN_YN IS '평가 점수 공개 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_GRADE_OPEN_YN IS '평가등급 공개 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_RANK_OPEN_YN IS '랭킹 공개 여부 (Y/N)';
COMMENT ON COLUMN H552_RND.V_AI_FEEDBACK.APPR_OPINION_OPEN_YN IS '평가의견 공개 여부 (Y/N)';
```

### 3.3 table_catalog.py 반영 코드

```python
"v_ai_feedback": {
    "description": "인사평가 결과 (1:N — 평가 횟수만큼 행 존재, EMP_ID로 V_AI_EMPLOYEE와 LEFT JOIN)",
    "columns": [
        "EMP_ID (FK → V_AI_EMPLOYEE)",
        "APPR_NM ★평가명 (연간인사평가, 수시평가 등)",
        "PEE_TYPE_NM (평가종류명)",
        "EMP_ORG_NM (평가 시점 소속부서명)",
        "APPR_SCORE ★평가점수 (숫자, 0 초과 시만 유효)",
        "APPR_GRADE ★평가등급 (S,A,B,C,D 등)",
        "RK (등급 내 순위)",
        "PEE_OPINION (평가자 의견, 텍스트)",
        "APPR_YMD ★평가일자 (DATE)",
        "END_YMD (평가종료일자)",
    ],
    "keywords": ["평가", "인사평가", "고과", "등급", "점수", "S등급", "A등급", "평가결과", "인사고과"],
    "is_primary": False,
    "join_key": "EMP_ID",
    "relation": "1:N (1인 다건 — 평가 횟수만큼, 직원 수 집계 시 COUNT(DISTINCT EMP_ID) 필수)",
    "related_tables": ["v_ai_employee"],
},
```

### 3.4 fewshot 예제 추가 (tb_docs)

**추가 예제 1: 평가등급 분포 조회**
```
title: 평가등급 분포 조회
doc_type: query_example
usage_type: rag_action

content:
평가등급 분포
등급별 직원 수
S등급 몇 명
A등급 직원
평가결과 현황
- V_AI_FEEDBACK
- APPR_GRADE GROUP BY

context_data:
## SQL
```sql
SELECT b.APPR_GRADE, COUNT(DISTINCT b.EMP_ID) AS emp_count
FROM v_ai_feedback b
WHERE b.APPR_GRADE IS NOT NULL
  AND b.APPR_YMD >= TO_DATE(':연도' || '0101', 'YYYYMMDD')
  AND b.APPR_YMD < TO_DATE(TO_NUMBER(':연도') + 1 || '0101', 'YYYYMMDD')
GROUP BY b.APPR_GRADE
ORDER BY emp_count DESC
```

## 핵심 패턴
- COUNT(DISTINCT EMP_ID): 1인 다건 평가 → 직원 수 기준 집계
- APPR_GRADE: S,A,B,C,D 등
- 연도 필터: APPR_YMD 기준 (DATE 타입)
```

**추가 예제 2: 부서별 평균 평가점수**
```
title: 부서별 평균 평가점수 조회
doc_type: query_example
usage_type: rag_action

content:
부서별 평균 평가점수
부서 평가 현황
부서별 평가 통계
- V_AI_EMPLOYEE LEFT JOIN V_AI_FEEDBACK
- DEPARTMENT GROUP BY + AVG(APPR_SCORE)

context_data:
## SQL
```sql
SELECT a.DEPARTMENT,
       COUNT(DISTINCT a.EMP_ID) AS emp_count,
       ROUND(AVG(b.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee a
LEFT JOIN v_ai_feedback b ON a.EMP_ID = b.EMP_ID
WHERE a.WORK_STATUS = '재직'
  AND b.APPR_SCORE > 0
GROUP BY a.DEPARTMENT
ORDER BY avg_score DESC
```

## 핵심 패턴
- LEFT JOIN: 평가 미등록 직원은 자연 제외 (APPR_SCORE > 0)
- AVG(APPR_SCORE): 평균 평가점수
- 특정 연도: AND b.APPR_YMD >= TO_DATE(':연도0101','YYYYMMDD') 추가
```

**추가 예제 3: 직원 평가 이력 조회**
```
title: 직원 평가 이력 조회
doc_type: query_example
usage_type: rag_action

content:
직원 평가 이력
평가 결과 확인
인사평가 기록
평가 점수 확인
- V_AI_EMPLOYEE LEFT JOIN V_AI_FEEDBACK
- EMP_NAME 검색 + ORDER BY APPR_YMD

context_data:
## SQL
```sql
SELECT a.EMP_NAME, a.DEPARTMENT, a.POSITION,
       b.APPR_NM, b.APPR_GRADE, b.APPR_SCORE,
       b.APPR_YMD, b.PEE_OPINION
FROM v_ai_employee a
LEFT JOIN v_ai_feedback b ON a.EMP_ID = b.EMP_ID
WHERE a.EMP_NAME LIKE '%' || ':이름' || '%'
ORDER BY b.APPR_YMD DESC
```

## 핵심 패턴
- LEFT JOIN: 평가 미등록 시 NULL
- EMP_NAME LIKE: 이름 부분 매칭
- ORDER BY APPR_YMD DESC: 최신 평가 우선
```

---

## 4. 카탈로그 vs 뷰 DDL 비교

| DDL 컬럼 | 카탈로그 등재 | 비고 |
|----------|:----------:|------|
| EMP_ID | O (FK) | |
| COMPANY_CD | **X** | 내부 코드 — NL2SQL 미사용 |
| LOCALE_CD | **X** | 내부 코드 — NL2SQL 미사용 |
| PEE_DEFINITION_ID | **X** | 내부 PK — NL2SQL 미사용 |
| APPR_ID | **X** | 내부 PK — NL2SQL 미사용 |
| APPR_NM | O (★) | 평가명 |
| PEE_TYPE_CD | **X** | 코드값 — PEE_TYPE_NM 사용 |
| PEE_TYPE_NM | O | 평가 종류명 |
| EMP_ORG_ID | **X** | 코드값 — EMP_ORG_NM 사용 |
| EMP_ORG_NM | O | 소속 부서명 |
| RATEE_ORG_ID | **X** | 내부용 |
| RATEE_ORG_NM | **X** | 내부용 (EMP_ORG_NM과 중복) |
| RATEE_GROUP_ID | **X** | 내부용 |
| RATEE_GROUP_NAME | **X** | 내부용 |
| RATEE_LEVEL_CD | **X** | 코드값 |
| RATEE_LEVEL_NM | **X** | 내부용 |
| APPR_SCORE | O (★) | 평가 점수 |
| APPR_GRADE | O (★) | 평가 등급 |
| RK | O | 순위 |
| PEE_OPINION | O | 평가 의견 |
| *_OPEN_YN (4개) | **X** | 공개 여부 — NL2SQL 미사용 |
| END_YMD | O | 평가종료일 |
| APPR_YMD | O (★) | 평가일자 |

---

## 5. 검증 계획

```sql
-- 1) VI_FRM_PHM_EMP 중복 확인 (최우선)
SELECT COUNT(*), COUNT(DISTINCT EMP_ID) FROM VI_FRM_PHM_EMP;

-- 2) V_AI_FEEDBACK 전체 건수 + 직원 수
SELECT COUNT(*) AS total, COUNT(DISTINCT EMP_ID) AS distinct_emp FROM V_AI_FEEDBACK;

-- 3) COMPANY_CD별 평가 건수 (중복 진단)
SELECT COMPANY_CD, COUNT(*) FROM V_AI_FEEDBACK GROUP BY COMPANY_CD;

-- 4) APPR_GRADE 값 도메인
SELECT APPR_GRADE, COUNT(*) FROM V_AI_FEEDBACK
WHERE APPR_GRADE IS NOT NULL GROUP BY APPR_GRADE ORDER BY COUNT(*) DESC;

-- 5) APPR_SCORE 범위
SELECT MIN(APPR_SCORE) AS min_score, MAX(APPR_SCORE) AS max_score,
       ROUND(AVG(APPR_SCORE), 1) AS avg_score
FROM V_AI_FEEDBACK WHERE APPR_SCORE > 0;

-- 6) PEE_TYPE_NM 값 도메인
SELECT PEE_TYPE_NM, COUNT(*) FROM V_AI_FEEDBACK
WHERE PEE_TYPE_NM IS NOT NULL GROUP BY PEE_TYPE_NM ORDER BY COUNT(*) DESC;

-- 7) APPR_NM 값 도메인
SELECT APPR_NM, COUNT(*) FROM V_AI_FEEDBACK
WHERE APPR_NM IS NOT NULL GROUP BY APPR_NM ORDER BY COUNT(*) DESC
FETCH FIRST 20 ROWS ONLY;

-- 8) APPR_YMD 범위
SELECT MIN(APPR_YMD), MAX(APPR_YMD) FROM V_AI_FEEDBACK;
```

### NL2SQL 테스트 질의

| 질문 | 기대 동작 |
|------|----------|
| "S등급 직원 몇 명?" | `WHERE APPR_GRADE = 'S' + COUNT(DISTINCT EMP_ID)` |
| "부서별 평균 평가점수" | `JOIN V_AI_EMPLOYEE + GROUP BY DEPARTMENT + AVG(APPR_SCORE)` |
| "올해 평가 받은 직원" | `WHERE APPR_YMD 연도 필터 + COUNT(DISTINCT EMP_ID)` |

---

## 6. 요약

| 항목 | 현재 상태 | 조치 | 우선도 |
|------|----------|------|--------|
| **VI_FRM_PHM_EMP 중복** | 미확인 | DB 조회 후 COMPANY_CD 필터 추가 여부 결정 | **확인 필요** |
| **DDL 구조 변경** | Oracle 함수 의존 | **최소 변경** (리스크 높음) | - |
| **카탈로그 보강** | 핵심 컬럼만 등재 | 값 도메인 + 관계 명시 | **확정** |
| **COMMENT 보강** | 일부만 존재 | 전체 컬럼 COMMENT 보강 | **확정** |
| **fewshot 예제** | 없음 | 3건 추가 (등급분포, 부서별점수, 직원이력) | **확정** |
| APPR_GRADE 값 도메인 | 미확인 | DB 조회로 확인 | 검증 필요 |
| PEE_TYPE_NM 값 도메인 | 미확인 | DB 조회로 확인 | 검증 필요 |

---

## 7. 변경 이력

| 일자 | 내용 |
|------|------|
| 2026-03-17 | 초안: 뷰 구조 분석, Oracle 함수 의존 식별, COMPANY_CD 중복 파급 분석, 카탈로그/COMMENT/fewshot 개선안 |
