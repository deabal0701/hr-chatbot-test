# NL2SQL Few-shot 설계 문서

> 최종 갱신: 2026-03-18
> 대상 DB: Oracle (H552_RND 스키마, MUSER 시노님)
> 저장 위치: hermesdb.tb_docs (usage_type='rag_action', doc_type='query_example')

---

## 1. 설계 원칙

### 1.1 context_data 포맷

LLM 프롬프트에 직접 주입되므로, 중첩 마크다운을 제거하고 플레인 텍스트로 통일한다.

```
-- 기존 (AS-IS): 중첩 코드블록 → 파싱 오류 가능
## SQL
```sql
SELECT ...
```
## 핵심 패턴
- 포인트

-- 변경 (TO-BE): 플레인 텍스트
SQL:
SELECT ...

패턴:
- 포인트
```

### 1.2 content 작성 규칙

- 자연어 질의 변형 4~6개 포함 (벡터 검색 히트율 향상)
- 구어체 표현 포함 (예: "몇 명이야?", "알려줘", "보여줘")
- 마지막에 핵심 테이블/컬럼 힌트 추가 (임베딩 정확도 향상)

### 1.3 SQL 작성 규칙

- Oracle 문법 전용 (SYSDATE, NVL, TO_CHAR, FETCH FIRST N ROWS ONLY)
- 플레이스홀더: ':년도', ':이름', ':부서' 등 콜론 접두사
- 재직자 기본조건: `WORK_STATUS = '재직'` (명시적 퇴직자 요청 제외)
- 1:N 뷰 집계: `COUNT(DISTINCT EMP_ID)` 필수
- 1:N 뷰 필터: EXISTS 서브쿼리 사용 (중복 방지)
- 1:1 뷰 (address, military): JOIN 사용 가능
- JOIN 키: 모든 뷰 `EMP_ID` 통일 (v_ai_pay_report 포함)

---

## 2. 뷰별 예제 목록

### 2.1 V_AI_EMPLOYEE — 직원 기본정보 (8건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 1 | 현재 재직자 수 조회 | 현재 재직 중인 직원 수 | COUNT + WHERE WORK_STATUS='재직' |
| 2 | 부서별 직원 수 조회 | 부서별 인원 현황 | GROUP BY DEPARTMENT + ORDER BY |
| 3 | 직위별 직원 수 조회 | 직급별 사원 수 | GROUP BY + CASE WHEN 순서 정렬 |
| 4 | 성별 직원 비율 조회 | 남녀 비율 | GROUP BY + SUM() OVER() 비율 계산 |
| 5 | 연도별 입사자 수 조회 | 2024년 입사자 수 | TO_CHAR(HIRE_DATE,'YYYY') + COUNT |
| 6 | 연도별 퇴사자 수 조회 | 올해 퇴직한 직원 | RETIRE_DATE IS NOT NULL + TO_CHAR |
| 7 | 연령대별 직원 분포 조회 | 연령대별 인원 현황 | CASE WHEN + MONTHS_BETWEEN 구간 |
| 8 | 근속연수 구간별 직원 분포 | 근속 구간별 인원 | CASE WHEN CAREER_YEARS 구간 + GROUP BY |

### 2.2 V_AI_ADDRESS — 현재 거주지 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 9 | 특정 지역 거주 직원 수 | 서울 사는 직원 몇 명 | JOIN + WHERE REGION = ':지역' |
| 10 | 지역별 직원 분포 조회 | 지역별 인원 분포 | JOIN + GROUP BY REGION |

### 2.3 V_AI_CAREER — 이전 직장 경력 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 11 | 이전 경력 보유 직원 수 | 경력직 출신 직원 수 | EXISTS 서브쿼리 |
| 12 | 전직장 다수 경력자 목록 | 전직장 3곳 이상인 직원 | JOIN + GROUP BY + HAVING COUNT >= 3 + FETCH |

### 2.4 V_AI_SCHOLAR — 학력 정보 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 13 | 학력별 직원 수 조회 | 대졸 이상 직원 수 | EXISTS + EDUCATION_LEVEL IN |
| 14 | 특정 전공자 목록 조회 | 컴퓨터공학 전공자 | JOIN + MAJOR_NAME LIKE |

### 2.5 V_AI_FAMILY — 가족 정보 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 15 | 배우자 보유 직원 수 | 기혼자 몇 명 | EXISTS + RELATION IN ('배우자') |
| 16 | 자녀 다수 보유 직원 | 자녀 2명 이상 직원 | JOIN + GROUP BY + HAVING COUNT >= 2 |

### 2.6 V_AI_LANGUAGE — 어학 성적 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 17 | 어학 점수 조건 직원 수 | TOEIC 800점 이상 직원 | EXISTS + EXAM_TYPE + SCORE >= |
| 18 | 시험종류별 평균 점수 | 어학 시험별 평균 점수 | GROUP BY EXAM_TYPE + AVG(SCORE) |

### 2.7 V_AI_LICENSE — 자격증 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 19 | 자격증 보유자 수 조회 | 정보처리기사 보유자 수 | EXISTS + LICENSE_NAME LIKE |
| 20 | 자격증 다수 보유자 목록 | 자격증 3개 이상 보유 직원 | JOIN + GROUP BY + HAVING COUNT >= 3 |

### 2.8 V_AI_MILITARY — 병역 정보 (1건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 21 | 군종별 직원 수 조회 | 육군 출신 몇 명 | JOIN + GROUP BY MILITARY_TYPE |

### 2.9 V_AI_REWARD — 상벌 내역 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 22 | 포상 직원 수 조회 | 포상 받은 직원 수 | EXISTS + REWARD_TYPE = '포상' |
| 23 | 연도별 포상 건수 조회 | 올해 포상 현황 | GROUP BY REWARD_YEAR + COUNT |

### 2.10 V_AI_TRAINING — 교육/연수 (2건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 24 | 교육 수료자 수 조회 | 올해 교육 수료한 직원 | EXISTS + COMPLETION_STATUS = '수료' |
| 25 | 부서별 교육시간 합계 | 부서별 1인당 교육시간 | JOIN + GROUP BY + SUM + AVG |

### 2.11 V_AI_FEEDBACK — 인사평가 (3건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 26 | 평가등급 분포 조회 | S등급 몇 명 | GROUP BY APPR_GRADE + 비율 계산 |
| 27 | 특정 직원 평가 이력 조회 | 홍길동 평가 기록 | JOIN + EMP_NAME LIKE |
| 28 | 부서별 평균 평가점수 | 부서 평가 현황 | JOIN + GROUP BY DEPARTMENT + AVG |

### 2.12 V_AI_HISTORY — 인사발령 (3건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 29 | 승진자 목록 조회 | 올해 승진한 직원 | JOIN + ASSIGNMENT_TYPE_CODE LIKE '%승진%' |
| 30 | 휴직 직원 조회 | 현재 휴직 중인 직원 | JOIN + LEAVE_OF_ABSENCE_YN = 'Y' + 최신 발령 |
| 31 | 발령유형별 통계 조회 | 발령 종류별 건수 | GROUP BY ASSIGNMENT_TYPE_CODE |

### 2.13 V_AI_PAY_REPORT — 급여 (3건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 32 | 부서별 평균 급여 조회 | 부서별 평균 월급 | JOIN(EMP_ID) + GROUP BY DEPARTMENT + AVG |
| 33 | 특정 연월 급여 현황 | 이번 달 급여 통계 | GROUP BY PAYMENT_TYPE_NAME + SUM |
| 34 | 직원 연간 급여 합계 | 연간 실수령액 | GROUP BY EMP_ID + SUM + ORDER BY |

### 2.14 V_AI_DTM_YY_REST — 연차 (3건)

| # | title | 대표 질의 | SQL 핵심 패턴 |
|---|-------|----------|-------------|
| 35 | 잔여연차 조회 | 남은 연차 현황 | JOIN + REFERENCE_YEAR + ORDER BY ASC |
| 36 | 부서별 연차 사용률 | 연차 소진률 | JOIN + GROUP BY + CASE WHEN 비율 (0 방어) |
| 37 | 잔여연차 부족 직원 | 연차 5일 미만 직원 | JOIN + REMAINING_LEAVE_DAYS < N |

### 2.15 복합 패턴 (10건)

| # | title | 대표 질의 | SQL 핵심 패턴 | 사용 뷰 |
|---|-------|----------|-------------|---------|
| 38 | 복합 조건 직원 수 | 서울+TOEIC 800이상 | 다중 EXISTS 조합 | employee + address + language |
| 39 | 입사자 자격증 보유 개수 | 입사자별 자격증 수 | 서브쿼리 COUNT (1:N 요약) | employee + license |
| 40 | 개인 상세 정보 조회 | 홍길동 자격증 목록 | JOIN + 특정 직원 | employee + license |
| 41 | 연도별 입사 퇴사 추이 | 연도별 채용 이직 트렌드 | UNION ALL + GROUP BY | employee |
| 42 | 부서별 최고 급여자 조회 | 부서별 급여 1위 | ROW_NUMBER() OVER(PARTITION BY) | employee + pay_report |
| 43 | 승진이력 없는 장기 근속자 | 5년 이상인데 승진 안 한 직원 | LEFT JOIN + IS NULL | employee + history |
| 44 | 교육 미이수 재직자 목록 | 올해 교육 안 받은 직원 | NOT EXISTS | employee + training |
| 45 | 최근 입사자 TOP N 조회 | 최근 입사한 직원 5명 | ORDER BY DESC + FETCH FIRST N (SELECT * 방지) | employee |
| 46 | 두 사원 종합 비교표 | 241번과 242번 비교 | CROSS JOIN + UNION ALL + LISTAGG + 서브쿼리 | all tables |
| 47 | 특정 직원 전체 정보 조회 | 241번 직원 정보 | SELECT 주요컬럼 WHERE EMP_ID (SELECT * 방지) | employee |

---

## 3. SQL 패턴 커버리지

| SQL 패턴 | 해당 예제 # | 비고 |
|----------|-----------|------|
| COUNT + WHERE | #1, #5, #6 | 기본 집계 |
| GROUP BY + ORDER BY | #2, #10, #23, #31 | 분류 집계 |
| CASE WHEN 순서 정렬 | #3 | 직위 정렬 |
| SUM() OVER() 비율 | #4, #26 | 윈도우 함수 비율 |
| CASE WHEN 구간 분류 | #7, #8 | 연령대/근속구간 |
| TO_CHAR 날짜 추출 | #5, #6, #26, #29, #31 | 연도 필터 |
| EXISTS 서브쿼리 | #11, #13, #15, #17, #19, #22, #24 | 1:N 중복 방지 |
| JOIN (1:1/1:N) | #9, #10, #12, #14, #16, #18, #20, #21, #25, #27, #28, #29, #30, #32, #34, #35, #36, #37, #38, #39, #40 | 다양한 JOIN |
| **HAVING** | #12, #16, #20 | **신규 추가** |
| **ROW_NUMBER() OVER** | #42 | **신규 추가** |
| **LEFT JOIN + IS NULL** | #43 | **신규 추가** |
| **NOT EXISTS** | #44 | **신규 추가** |
| **FETCH FIRST N ROWS** | #12, #42, #45 | **신규 추가** |
| **CROSS JOIN + UNION ALL + LISTAGG** | #46 | **신규 추가** (두 사원 비교표) |
| UNION ALL | #41 | 입사/퇴사 동시 집계 |
| 서브쿼리 COUNT | #39 | 1:N 요약 리스트 |
| SUM/AVG 집계 | #18, #25, #28, #32, #33, #34, #36 | 통계 |
| MONTHS_BETWEEN | #7 | 나이 계산 |
| NVL / NULLS LAST | #35 | NULL 처리 |

---

## 4. 기존 대비 변경 사항

### 4.1 삭제 대상 (기존 전건)

```sql
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action';
```

### 4.2 주요 수정 사항

| 항목 | 기존 (AS-IS) | 변경 (TO-BE) |
|------|-------------|-------------|
| 중복 예제 | id=969,970,971 동일 3건 | 1건으로 통합 (#39) |
| v_ai_pay_report JOIN 키 | EMPLOYEE_ID | EMP_ID (스키마 일치) |
| v_ai_language 필터 | LANGUAGE_TYPE = 'TOEIC' | EXAM_TYPE = 'TOEIC' (올바른 컬럼) |
| 연령대 ORDER BY | alias 직접 참조 (Oracle 오류) | 서브쿼리로 감싸서 해결 |
| v_ai_address relation | content에 "1:N" 표기 | "1:1"로 수정 (카탈로그 일치) |
| context_data 포맷 | ## SQL + ```sql 중첩 | SQL: / 패턴: 플레인 텍스트 |

### 4.3 신규 추가 패턴

| 패턴 | 예제 # | 실무 활용 |
|------|--------|----------|
| HAVING | #12, #16, #20 | 그룹별 조건 필터 |
| ROW_NUMBER() OVER | #42 | 부서별 TOP-N |
| LEFT JOIN + IS NULL | #43 | 이력 없는 대상 추출 |
| NOT EXISTS | #44 | 미이수/미보유 대상 추출 |
| FETCH FIRST N ROWS | #12, #42, #45 | 상위 N건 제한 |
| CROSS JOIN + UNION ALL + LISTAGG | #46 | 두 사원 종합 비교표 |
| SELECT * 방지 (주요 컬럼만 SELECT) | #45, #47 | history 분석 기반 추가 |
| v_ai_history 전체 | #29, #30, #31 | 승진/휴직/발령 (기존 미커버) |
| v_ai_dtm_yy_rest 전체 | #35, #36, #37 | 연차 현황 (기존 미커버) |

---

## 5. 확장 가이드

### 5.1 새 예제 추가 방법

```sql
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES (
    'default',
    'rag_action',
    '예제 제목',
    'query_example',
    'ko',
    '질의 변형1
질의 변형2
질의 변형3
- 사용 테이블/컬럼 힌트',
    'SQL:
SELECT ...
FROM ...

패턴:
- 핵심 포인트1
- 핵심 포인트2'
);
```

### 5.2 추후 추가 후보 (복합 패턴)

| 우선순위 | 예제 | SQL 패턴 | 비고 |
|---------|------|---------|------|
| P1 | 부서별 남녀 평균 급여 차이 | CASE WHEN + GROUP BY + PIVOT형 | 성별 급여 격차 분석 |
| P1 | 평가등급별 평균 급여 | 2테이블 + GROUP BY APPR_GRADE | Pay-for-Performance |
| P2 | 부서별 정원 대비 현원 | 서브쿼리 비율 계산 | 인력 과부족 |
| P2 | 직급별 급여 중위값/상하위 25% | PERCENTILE_CONT / NTILE | 급여 밴드 분석 |
| P3 | 전년 대비 입사자 증감 | LAG / 서브쿼리 연도 비교 | 추세 분석 |
| P3 | 교육기관별 참여 인원 통계 | GROUP BY INSTITUTION_NAME | 교육 투자 분석 |

### 5.3 History 기반 LLM 오류 패턴 (주의사항으로 반영)

> API 이력(tb_api_history) 608건 분석 결과 발견된 반복 오류 패턴.
> 해당 few-shot의 `패턴:` 섹션에 주의사항으로 추가 반영 완료.

| 오류 패턴 | 발생 건수 | 반영 예제 | 대응 |
|----------|:---:|---------|------|
| `PAY_DATE` 환각 (없는 컬럼) | 7건+ | #32, #33, #34 | 패턴에 "PAY_DATE 없음" 명시 |
| `LANGUAGE_GRADE` 환각 | 1건+ | #17 | 패턴에 "LANGUAGE_GRADE 없음" 명시 |
| `SELECT *` 남발 | 10건+ | #45, #47 | 주요 컬럼만 SELECT하는 예제 추가 |
| `EMPLOYEE_ID` 사용 | 3건+ | #32~#34 | EMP_ID로 통일 (수정 완료) |

---

## 6. 임베딩 관련

- INSERT 후 `indexed = false` 상태 → 임베딩 배치 실행 필요
- 임베딩 모델: `text-embedding-3-large` (3072차원)
- 임베딩 대상: `content` 컬럼만 (context_data는 임베딩 안 함)
- 유사도 검색: 코사인 거리, threshold 기본 0.3
- DB 설정: `tb_app_settings` → `embedding.model = text-embedding-3-large`, `embedding.dimension = 3072`
