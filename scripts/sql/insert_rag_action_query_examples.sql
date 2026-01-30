-- ============================================================================
-- RAG Action 쿼리 예제 데이터 INSERT (Phase 4)
--
-- 용도: Agent의 context_search_tool에서 검색되는 Few-shot 예제
--
-- 구조:
--   content     : 임베딩 대상 (대표 질문 + 유사 질문 + 조건/목적)
--   context_data: 임베딩 제외 (SQL + 핵심 패턴)
--   usage_type  : 'rag_action'
--   doc_type    : 'query_example'
--
-- 실행: psql -f insert_rag_action_query_examples.sql
-- 임베딩: python scripts/embed_documents.py
-- ============================================================================

-- 기존 rag_action 쿼리 예제 삭제 (선택사항)
-- DELETE FROM tb_docs WHERE usage_type = 'rag_action' AND doc_type = 'query_example';

-- ============================================================================
-- 1. 기본 집계 쿼리 (v_ai_employee 단독)
-- ============================================================================

-- 1-1. 연도별 입사자 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '연도별 입사자 수 조회',
    'query_example',
    '2024년 입사자 수를 알려줘
올해 입사한 직원 몇 명
작년 신규 입사자 수
특정 연도 입사 인원
- 입사일(HIRE_DATE) 기준 연도별 집계
- 입사자 집계 시 재직 조건 불필요
- TO_CHAR로 연도 추출',
    '## SQL
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''
```

## 핵심 패턴
- 연도 추출: TO_CHAR(HIRE_DATE, ''YYYY'')
- 입사자 집계 시 WORK_STATUS 조건 불필요 (입사 시점 기준)
- HIRE_DATE 컬럼 사용 (NOT NULL)',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "hire", "tags": ["입사", "입사자", "연도별", "몇명", "신입", "채용"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-2. 연도별 퇴사자 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '연도별 퇴사자 수 조회',
    'query_example',
    '2024년 퇴사자 수를 알려줘
올해 퇴직한 직원 몇 명
작년 퇴사 인원
특정 연도 퇴직자
- 퇴직일(RETIRE_DATE) 기준 연도별 집계
- 퇴사자 집계 시 재직 조건 불필요
- RETIRE_DATE IS NOT NULL 필수',
    '## SQL
```sql
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, ''YYYY'') = ''2024''
```

## 핵심 패턴
- 연도 추출: TO_CHAR(RETIRE_DATE, ''YYYY'')
- RETIRE_DATE IS NOT NULL 조건 필수
- 퇴사자 집계 시 WORK_STATUS 조건 불필요',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "retire", "tags": ["퇴사", "퇴직", "퇴사자", "연도별", "이직"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-3. 현재 재직자 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '현재 재직자 수 조회',
    'query_example',
    '현재 재직 중인 직원 수
전체 재직자 몇 명
현재 근무 중인 사원 수
회사 전체 인원
- 현재 재직 상태인 직원만 집계
- WORK_STATUS = 재직 조건 필수
- 특별한 언급 없으면 재직자만 대상',
    '## SQL
```sql
SELECT COUNT(*) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
```

## 핵심 패턴
- 재직자 기본 조건: WORK_STATUS = ''재직''
- 특별한 언급이 없으면 재직자만 대상
- "퇴직자", "전체 직원" 등 명시적 언급 시에만 조건 변경',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "active", "tags": ["재직", "재직자", "현재", "전체", "인원"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-4. 부서별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '부서별 직원 수 조회',
    'query_example',
    '부서별 직원 수를 알려줘
팀별 인원 현황
각 부서에 몇 명이 있어
조직별 재직자 수
부서 인원 분포
- 재직자만 대상
- DEPARTMENT 컬럼 기준 그룹화
- 인원 순 내림차순 정렬',
    '## SQL
```sql
SELECT DEPARTMENT, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY DEPARTMENT
ORDER BY emp_count DESC
```

## 핵심 패턴
- 재직자 조건: WORK_STATUS = ''재직''
- GROUP BY DEPARTMENT로 부서별 그룹화
- ORDER BY로 인원 순 정렬',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "department", "tags": ["부서별", "팀별", "조직별", "GROUP BY", "부서"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-5. 직위별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '직위별 직원 수 조회',
    'query_example',
    '직위별 사원 수를 알려줘
직급별 직원 수 현황
사원 대리 과장 차장 부장 인원
직위 분포
- 재직자만 대상
- POSITION 컬럼 기준 그룹화
- 직위 순서대로 정렬 (사원→대리→과장→차장→부장)',
    '## SQL
```sql
SELECT POSITION, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY POSITION
ORDER BY
    CASE POSITION
        WHEN ''사원'' THEN 1
        WHEN ''대리'' THEN 2
        WHEN ''과장'' THEN 3
        WHEN ''차장'' THEN 4
        WHEN ''부장'' THEN 5
        WHEN ''이사'' THEN 6
        WHEN ''전무이사'' THEN 7
        WHEN ''사장'' THEN 8
        WHEN ''회장'' THEN 9
        ELSE 10
    END
```

## 핵심 패턴
- 재직자 조건: WORK_STATUS = ''재직''
- GROUP BY POSITION
- CASE WHEN으로 직위 순서 정렬
- 주의: GRADE(직급)와 POSITION(직위)은 다름',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "position", "tags": ["직위별", "직급별", "사원", "대리", "과장", "차장", "부장", "POSITION"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-6. 성별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '성별 직원 수 조회',
    'query_example',
    '성별 직원 수를 알려줘
남녀 비율
남자 여자 직원 몇 명
성별 인원 현황
- 재직자만 대상
- GENDER 컬럼 기준 그룹화
- 비율 계산 포함 가능',
    '## SQL
```sql
SELECT
    GENDER,
    COUNT(*) AS emp_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY GENDER
ORDER BY GENDER
```

## 핵심 패턴
- GENDER 컬럼: 남, 여
- 비율 계산: 윈도우 함수 SUM() OVER()
- ROUND로 소수점 처리',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "gender", "tags": ["성별", "남녀", "남자", "여자", "비율"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-7. 고용형태별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '고용형태별 직원 수 조회',
    'query_example',
    '고용형태별 직원 수
정규직 계약직 인턴 몇 명
고용 유형별 인원
비정규직 현황
- 재직자만 대상
- EMP_TYPE 컬럼 기준 그룹화
- 정규직, 계약직, 인턴 등',
    '## SQL
```sql
SELECT EMP_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY EMP_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- EMP_TYPE 컬럼: 정규직, 계약직, 인턴 등
- 비정규직 조건: EMP_TYPE != ''정규직''',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "emp_type", "tags": ["고용형태", "정규직", "계약직", "인턴", "비정규직"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 1-8. 채용유형별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '채용유형별 직원 수 조회',
    'query_example',
    '채용유형별 직원 수
신입 경력 입사자 현황
신입사원 몇 명
경력직 인원
- 재직자만 대상
- HIRE_TYPE 컬럼 기준 그룹화
- 신입, 경력, 입사(신입), 입사(경력) 등',
    '## SQL
```sql
SELECT HIRE_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY HIRE_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- HIRE_TYPE 컬럼: 신입, 경력, 입사(신입), 입사(경력) 등
- 신입: HIRE_TYPE LIKE ''%신입%''
- 경력: HIRE_TYPE LIKE ''%경력%''',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "hire_type", "tags": ["채용유형", "신입", "경력", "경력직", "신입사원"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 2. 기간별 추이 쿼리
-- ============================================================================

-- 2-1. 연도별 입사/퇴사 추이
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '연도별 입사 퇴사 추이 조회',
    'query_example',
    '연도별 입사자 퇴사자 추이
2010년부터 2020년까지 입사 퇴사 현황
연도별 채용 이직 트렌드
기간별 인력 변동
- 입사와 퇴사 동시 집계
- UNION ALL로 데이터 통합
- 재직 조건 제외 (시점 기준)',
    '## SQL
```sql
SELECT
    year,
    SUM(hire_count) AS hire_count,
    SUM(retire_count) AS retire_count
FROM (
    SELECT TO_CHAR(HIRE_DATE, ''YYYY'') AS year, 1 AS hire_count, 0 AS retire_count
    FROM v_ai_employee
    WHERE TO_CHAR(HIRE_DATE, ''YYYY'') BETWEEN ''2010'' AND ''2020''
    UNION ALL
    SELECT TO_CHAR(RETIRE_DATE, ''YYYY'') AS year, 0 AS hire_count, 1 AS retire_count
    FROM v_ai_employee
    WHERE RETIRE_DATE IS NOT NULL
      AND TO_CHAR(RETIRE_DATE, ''YYYY'') BETWEEN ''2010'' AND ''2020''
)
GROUP BY year
ORDER BY year
```

## 핵심 패턴
- UNION ALL로 입사/퇴사 데이터 통합
- TO_CHAR(날짜, ''YYYY'') BETWEEN으로 기간 조건
- 추이 분석 시 WORK_STATUS 조건 제외',
    '{"intent": "trend", "tables": ["v_ai_employee"], "category": "trend", "tags": ["연도별", "추이", "트렌드", "입사", "퇴사", "기간별", "UNION ALL"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 3. 1:N 관계 조인 쿼리 (EXISTS 패턴)
-- ============================================================================

-- 3-1. 지역별 거주자 수 (v_ai_address)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '지역별 거주 직원 수 조회',
    'query_example',
    '서울에 사는 직원 몇 명
경기도 거주자 수
부산 지역 직원 현황
특정 시도 거주 재직자
지역별 인원
- 1:N 관계(v_ai_address) 조인 시 EXISTS 사용
- REGION 컬럼으로 지역 필터
- 중복 방지를 위해 JOIN 대신 EXISTS',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = ''서울''
  )
```

## 핵심 패턴
- 1:N 관계 뷰 조건 시 EXISTS 서브쿼리 사용 (중복 방지)
- JOIN 대신 EXISTS 사용
- REGION 값: 서울, 경기, 경북, 경남, 전북, 전남, 충북, 충남, 강원, 제주 등',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_address"], "category": "region", "tags": ["지역", "거주", "서울", "경기", "부산", "EXISTS", "주소", "REGION"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-2. 자격증 보유자 수 (v_ai_license)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '자격증 보유자 수 조회',
    'query_example',
    '정보처리기사 자격증 보유자 수
특정 자격증 보유 직원 몇 명
자격증 있는 사원
국가자격 보유자
- 1:N 관계(v_ai_license) 조인 시 EXISTS 사용
- LICENSE_NAME으로 자격증명 검색
- LIKE로 부분 일치 검색',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LICENSE_NAME LIKE ''%정보처리기사%''
  )
```

## 핵심 패턴
- LIKE ''%키워드%''로 자격증명 검색
- 1:N 관계 뷰에서 중복 방지를 위한 EXISTS
- LICENSE_TYPE: 국가자격, 민간자격, 사내자격',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_license"], "category": "license", "tags": ["자격증", "정보처리기사", "보유자", "EXISTS", "LIKE", "국가자격"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-3. 어학 점수 조건 (v_ai_language)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '어학 점수 조건 직원 수 조회',
    'query_example',
    'TOEIC 800점 이상인 직원 수
영어 점수 높은 사원
토익 점수 조건
어학 성적 우수자
- 1:N 관계(v_ai_language) 조인 시 EXISTS 사용
- EXAM_TYPE으로 시험 종류 필터
- SCORE로 점수 조건',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = ''TOEIC''
      AND l.SCORE >= 800
  )
```

## 핵심 패턴
- EXAM_TYPE: TOEIC, TOEFL, JLPT, BCT 등
- SCORE 컬럼으로 점수 조건
- LANGUAGE_TYPE: 영어, 일본어, 중국어 등',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_language"], "category": "language", "tags": ["어학", "TOEIC", "토익", "점수", "영어", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-4. 학력 조건 (v_ai_education)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '학력 조건 직원 수 조회',
    'query_example',
    '서울대 출신 직원 몇 명
특정 학교 졸업자
컴퓨터공학 전공자 수
특정 전공 직원
- 1:N 관계(v_ai_education) 조인 시 EXISTS 사용
- SCHOOL_NAME으로 학교 검색
- MAJOR로 전공 검색',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_education ed
    WHERE ed.EMP_ID = e.EMP_ID
      AND ed.SCHOOL_NAME LIKE ''%서울대%''
  )
```

## 핵심 패턴
- SCHOOL_NAME: 학교명 (LIKE 검색)
- MAJOR: 전공 학과명
- GRADUATION_YEAR: 졸업 연도',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_education"], "category": "education", "tags": ["학력", "학교", "전공", "졸업", "출신", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-5. 가족 조건 (v_ai_family)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '가족 조건 직원 수 조회',
    'query_example',
    '배우자가 있는 직원 수
기혼자 몇 명
자녀가 있는 사원
부양가족 있는 직원
- 1:N 관계(v_ai_family) 조인 시 EXISTS 사용
- RELATION으로 가족 관계 필터
- 배우자: 처, 남편, 배우자',
    '## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN (''배우자'', ''처'', ''남편'')
  )
```

## 핵심 패턴
- RELATION: 배우자, 처, 남편, 자녀, 부, 모 등
- 자녀 조건: RELATION = ''자녀''
- DISABILITY_STATUS: 장애있음, 장애없음',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_family"], "category": "family", "tags": ["가족", "배우자", "기혼", "자녀", "부양가족", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-6. 교육 이수 조건 (v_ai_training)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '교육 이수 직원 수 조회',
    'query_example',
    '특정 교육 이수자 수
2024년 교육 수료자
교육 과정 완료한 직원
연수 이수 현황
- 1:N 관계(v_ai_training) 조인 시 EXISTS 사용
- COMPLETION_STATUS로 수료 여부 확인
- TRAINING_YEAR로 연도 필터',
    '## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = ''2024''
      AND t.COMPLETION_STATUS = ''수료''
  )
```

## 핵심 패턴
- TRAINING_YEAR: 교육 연도
- COMPLETION_STATUS: 수료, 미수료
- COURSE_NAME: 교육 과정명',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_training"], "category": "training", "tags": ["교육", "연수", "수료", "이수", "과정", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-7. 포상 이력 조건 (v_ai_reward)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '포상 이력 직원 수 조회',
    'query_example',
    '포상 받은 직원 수
우수사원 몇 명
상 받은 사람
징계 이력 있는 직원
- 1:N 관계(v_ai_reward) 조인 시 EXISTS 사용
- REWARD_TYPE으로 포상/징계 구분
- REWARD_KIND로 상 종류 확인',
    '## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = ''포상''
  )
```

## 핵심 패턴
- REWARD_TYPE: 포상, 징계
- REWARD_KIND: 우수상, 우수상-혁신 등
- REWARD_AMOUNT: 포상금 금액',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_reward"], "category": "reward", "tags": ["포상", "징계", "우수사원", "상", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 3-8. 경력 조건 (v_ai_career)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '이전 경력 조건 직원 수 조회',
    'query_example',
    '경력직 출신 직원 수
이전 회사 경력 있는 사원
전직장 경험자
특정 회사 출신
- 1:N 관계(v_ai_career) 조인 시 EXISTS 사용
- PREV_COMPANY로 이전 회사 검색
- WORK_YEARS로 경력 연수 확인',
    '## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_career c
    WHERE c.EMP_ID = e.EMP_ID
  )
```

## 핵심 패턴
- PREV_COMPANY: 이전 회사명
- WORK_YEARS: 해당 직장 근무 연수
- WORK_MONTHS: 해당 직장 근무 개월수',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_career"], "category": "career", "tags": ["경력", "전직장", "이전회사", "경력직", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 4. 평가 관련 쿼리 (v_ai_feedback)
-- ============================================================================

-- 4-1. 평가 등급 분포
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '평가 등급 분포 조회',
    'query_example',
    '2024년 평가 등급 분포
인사평가 등급별 인원
S A B C D 등급 분포
성과평가 결과 현황
- v_ai_feedback 테이블 사용
- APPR_GRADE로 등급 그룹화
- 연도는 END_YMD 기준',
    '## SQL
```sql
SELECT
    APPR_GRADE,
    COUNT(*) AS cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM v_ai_feedback
WHERE TO_CHAR(END_YMD, ''YYYY'') = ''2024''
GROUP BY APPR_GRADE
ORDER BY
    CASE APPR_GRADE
        WHEN ''S'' THEN 1
        WHEN ''A'' THEN 2
        WHEN ''B'' THEN 3
        WHEN ''C'' THEN 4
        WHEN ''D'' THEN 5
    END
```

## 핵심 패턴
- v_ai_feedback 테이블: 인사평가/성과평가 정보
- APPR_GRADE: S, A, B, C, D 등급
- END_YMD: 평가 종료일 (연도 기준)
- APPR_SCORE: 평가 점수',
    '{"intent": "aggregate", "tables": ["v_ai_feedback"], "category": "feedback", "tags": ["평가", "인사평가", "등급", "S등급", "A등급", "분포", "성과평가"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 4-2. 특정 등급 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '특정 평가 등급 직원 수 조회',
    'query_example',
    'S등급 받은 직원 몇 명
A등급 이상 우수자 수
평가 우수자 현황
최우수 등급 인원
- 특정 등급 조건으로 필터
- 우수 이상: S, A 등급
- EXISTS로 중복 방지',
    '## SQL
```sql
SELECT COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND TO_CHAR(f.END_YMD, ''YYYY'') = ''2024''
  AND f.APPR_GRADE IN (''S'', ''A'')
```

## 핵심 패턴
- 우수 이상: APPR_GRADE IN (''S'', ''A'')
- 최우수: APPR_GRADE = ''S''
- COUNT(DISTINCT EMP_ID)로 중복 제거',
    '{"intent": "aggregate", "tables": ["v_ai_feedback", "v_ai_employee"], "category": "feedback", "tags": ["평가", "S등급", "A등급", "우수자", "최우수"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 5. 급여 관련 쿼리 (v_ai_pay_report)
-- ============================================================================

-- 5-1. 부서별 평균 급여
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '부서별 평균 급여 조회',
    'query_example',
    '부서별 평균 급여
팀별 연봉 현황
조직별 급여 통계
부서 평균 월급
- v_ai_pay_report 테이블 사용
- NET_PAY_AMOUNT: 실지급액
- 정기급여만 필터',
    '## SQL
```sql
SELECT
    ORGANIZATION_NAME,
    ROUND(AVG(NET_PAY_AMOUNT), 0) AS avg_pay,
    MIN(NET_PAY_AMOUNT) AS min_pay,
    MAX(NET_PAY_AMOUNT) AS max_pay,
    COUNT(DISTINCT EMPLOYEE_ID) AS emp_count
FROM v_ai_pay_report
WHERE PAY_YEAR = ''2024''
  AND PAYMENT_TYPE_NAME = ''정기급여''
GROUP BY ORGANIZATION_NAME
ORDER BY avg_pay DESC
```

## 핵심 패턴
- v_ai_pay_report 테이블: 급여 정보
- NET_PAY_AMOUNT: 실지급액
- PAYMENT_TYPE_NAME: 정기급여, 연차수당, 격려금, 상여
- 주의: EMPLOYEE_ID로 조인 (EMP_ID 아님)',
    '{"intent": "aggregate", "tables": ["v_ai_pay_report"], "category": "pay", "tags": ["급여", "평균", "연봉", "월급", "부서별", "실지급액"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 5-2. 특정 연월 급여 현황
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '특정 연월 급여 현황 조회',
    'query_example',
    '2024년 1월 급여 현황
특정 월 급여 지급 내역
연월별 급여 조회
이번 달 급여 통계
- PAY_YEAR_MONTH로 연월 필터
- 급여 유형별 조회 가능
- 지급합계, 공제합계 확인',
    '## SQL
```sql
SELECT
    PAYMENT_TYPE_NAME,
    COUNT(DISTINCT EMPLOYEE_ID) AS emp_count,
    SUM(GROSS_PAY_AMOUNT) AS total_gross,
    SUM(NET_PAY_AMOUNT) AS total_net
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = ''202401''
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_net DESC
```

## 핵심 패턴
- PAY_YEAR_MONTH: YYYYMM 형식
- GROSS_PAY_AMOUNT: 지급합계
- NET_PAY_AMOUNT: 실지급액
- DEDUCTION_AMOUNT: 공제합계',
    '{"intent": "aggregate", "tables": ["v_ai_pay_report"], "category": "pay", "tags": ["급여", "연월", "지급", "공제", "실지급액"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 6. 명단 조회 쿼리 (SELECT)
-- ============================================================================

-- 6-1. 조건에 맞는 직원 명단
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '조건별 직원 명단 조회',
    'query_example',
    '서울 거주 직원 명단
특정 조건 사원 목록
직원 리스트
명단 보여줘
- COUNT 대신 실제 데이터 조회
- 필요한 컬럼만 SELECT
- ORDER BY로 정렬',
    '## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = ''서울''
  )
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- 명단 조회: COUNT 대신 컬럼 SELECT
- 명단에도 EXISTS 또는 IN 사용 (중복 방지)
- ORDER BY로 이름순 정렬',
    '{"intent": "select", "tables": ["v_ai_employee", "v_ai_address"], "category": "list", "tags": ["명단", "목록", "리스트", "직원목록", "보여줘"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 6-2. 개인 상세 정보 조회 (JOIN 사용)
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '개인 상세 정보 조회',
    'query_example',
    '홍길동의 자격증 목록
특정 직원 학력 정보
개인 상세 데이터 조회
직원 정보 보여줘
- 상세 데이터 필요 시 JOIN 사용
- 특정 직원 조건
- 1:N 데이터 전체 조회',
    '## SQL
```sql
SELECT e.EMP_NAME, l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE e.EMP_NAME = ''홍길동''
ORDER BY l.ISSUE_DATE DESC
```

## 핵심 패턴
- 상세 데이터 필요 시에만 JOIN 사용
- 집계가 아닌 개별 데이터 조회
- ORDER BY로 최신순 정렬',
    '{"intent": "select", "tables": ["v_ai_employee", "v_ai_license"], "category": "detail", "tags": ["상세", "개인정보", "자격증", "학력", "JOIN"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 7. 병역 관련 쿼리 (v_ai_military)
-- ============================================================================

-- 7-1. 군종별 직원 수
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '군종별 직원 수 조회',
    'query_example',
    '육군 출신 직원 몇 명
군종별 인원 현황
해군 공군 육군 직원
병역 이행 현황
- v_ai_military 테이블 (1:1 관계)
- MILITARY_TYPE으로 군종 필터
- JOIN 사용 가능 (1:1 관계)',
    '## SQL
```sql
SELECT m.MILITARY_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_military m ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND m.MILITARY_TYPE IS NOT NULL
GROUP BY m.MILITARY_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- v_ai_military: 1:1 관계 (JOIN 가능)
- MILITARY_TYPE: 육군, 해군, 공군, 해병대, 의무경찰 등
- MILITARY_RANK: 병장, 상병 등 최종 계급',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_military"], "category": "military", "tags": ["병역", "군대", "육군", "해군", "공군", "군종"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 8. 복합 조건 쿼리
-- ============================================================================

-- 8-1. 여러 조건 조합
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '복합 조건 직원 수 조회',
    'query_example',
    '서울 거주하면서 TOEIC 800점 이상인 직원
여러 조건 동시 만족
복합 조건 검색
다중 조건 직원 수
- 여러 EXISTS 조건 조합
- AND로 조건 연결
- 각 조건별 EXISTS 사용',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ''서울''
  )
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = ''TOEIC''
      AND l.SCORE >= 800
  )
```

## 핵심 패턴
- 여러 1:N 조건: 각각 EXISTS 사용
- AND로 조건 연결
- 모든 조건을 만족하는 직원만 집계',
    '{"intent": "aggregate", "tables": ["v_ai_employee", "v_ai_address", "v_ai_language"], "category": "complex", "tags": ["복합조건", "다중조건", "AND", "EXISTS"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 8-2. 경력연수 조건
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '경력연수 조건 직원 수 조회',
    'query_example',
    '경력 10년 이상 직원 수
근속연수 5년 이상
장기 근속자
경력 많은 직원
- v_ai_employee의 CAREER_YEARS 사용
- 근속연수 = 현재 회사 경력
- 경력연수 = 총 경력',
    '## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
  AND CAREER_YEARS >= 10
```

## 핵심 패턴
- CAREER_YEARS: 총 경력 연수
- CAREER_MONTHS: 총 경력 개월수
- 근속연수: MONTHS_BETWEEN(SYSDATE, HIRE_DATE) / 12',
    '{"intent": "aggregate", "tables": ["v_ai_employee"], "category": "career", "tags": ["경력", "연수", "근속", "장기근속", "경력연수"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 9. 용어집/패턴 (doc_type: 'glossary')
-- ============================================================================

-- 9-1. 재직자 조건
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '재직자 조건',
    'glossary',
    '재직자 재직중 현직 현재 근무중
active 직원 현재 직원
- 특별한 언급 없으면 재직자만 대상
- "퇴직자", "전체 직원" 명시 시에만 변경',
    '## SQL 조건
```sql
WHERE WORK_STATUS = ''재직''
```

## 반대 조건
- 퇴직자: WORK_STATUS = ''퇴직''
- 전체: WORK_STATUS 조건 제외',
    '{"term": "재직자", "sql_condition": "WORK_STATUS = ''재직''", "tags": ["재직", "재직자", "현직", "active"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 9-2. EXISTS 패턴
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '1:N 관계 중복 방지 패턴',
    'glossary',
    'EXISTS 서브쿼리 중복방지 1:N 조인
직원 수 집계 시 중복 카운트 방지
- 1:N 관계 뷰와 조인하여 집계 시 필수
- JOIN 대신 EXISTS 사용',
    '## 잘못된 쿼리 (중복 발생)
```sql
SELECT COUNT(*) FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE l.LICENSE_NAME LIKE ''%기사%''
```

## 올바른 쿼리 (EXISTS 사용)
```sql
SELECT COUNT(*) FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LICENSE_NAME LIKE ''%기사%''
  )
```

## 적용 대상
- 직원 수 집계 + 1:N 뷰 조건 → EXISTS
- 직원 목록 + 1:N 뷰 조건 → EXISTS 또는 IN
- 1:N 상세 데이터 필요 시 → JOIN',
    '{"term": "EXISTS 패턴", "sql_pattern": "EXISTS (SELECT 1 FROM ...)", "tags": ["EXISTS", "서브쿼리", "중복방지", "1:N", "조인"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- 9-3. Oracle 날짜 처리
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    'Oracle 날짜 처리 패턴',
    'glossary',
    '날짜 연도 추출 TO_CHAR SYSDATE
Oracle 날짜 비교 기간 조건
- Oracle에서 날짜 처리하는 표준 패턴',
    '## 연도 추출
```sql
TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''
```

## 월 추출
```sql
TO_CHAR(HIRE_DATE, ''MM'')
TO_CHAR(HIRE_DATE, ''YYYY-MM'')
```

## 기간 조건
```sql
TO_CHAR(HIRE_DATE, ''YYYY'') BETWEEN ''2010'' AND ''2020''
```

## 현재 연도
```sql
TO_CHAR(SYSDATE, ''YYYY'')
```

## NULL 처리
```sql
NVL(컬럼, 기본값)
```',
    '{"term": "Oracle 날짜", "sql_patterns": ["TO_CHAR", "TO_DATE", "SYSDATE", "NVL"], "tags": ["Oracle", "날짜", "TO_CHAR", "TO_DATE", "SYSDATE", "연도"]}'::jsonb,
    true, 'rag_action_seed', 'rag_action'
);

-- ============================================================================
-- 확인 쿼리
-- ============================================================================

-- 추가된 데이터 확인
SELECT usage_type, doc_type, COUNT(*) as count
FROM tb_docs
WHERE usage_type = 'rag_action'
GROUP BY usage_type, doc_type
ORDER BY doc_type;

-- rag_action 쿼리 예제 목록
SELECT id, title, doc_type
FROM tb_docs
WHERE usage_type = 'rag_action'
ORDER BY doc_type, title;

-- 임베딩 대기 중인 문서 확인
SELECT COUNT(*) as pending_count
FROM tb_docs
WHERE usage_type = 'rag_action'
  AND indexed = true
  AND embedding IS NULL;
