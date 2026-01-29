-- ============================================================================
-- Cortex SQL 컨텍스트 데이터 INSERT
--
-- 용도: Cortex Agent의 컨텍스트 검색(RAG)에 사용되는 데이터
-- - schema: 테이블 스키마 정보
-- - query_example: Few-shot 쿼리 예제
-- - glossary: 비즈니스 용어집
--
-- 대상 테이블: tb_docs (기존 문서 테이블 활용)
-- - usage_type='cortex': Cortex 전용 문서 (RAG 문서와 구분)
-- - doc_type으로 컨텍스트 유형 구분
-- - metadata jsonb에 추가 정보 저장
--
-- 실행 순서:
-- 1. 컬럼 추가: psql -f alter_tb_docs_usage_type.sql
-- 2. 코드 추가: psql -f insert_cortex_codes.sql
-- 3. 데이터 추가: psql -f insert_nl2sql_rag_data.sql
-- 4. 임베딩 생성: python scripts/embed_documents.py
-- ============================================================================

-- 기존 Cortex 관련 데이터 삭제 (선택사항)
-- DELETE FROM tb_docs WHERE usage_type = 'cortex';

-- ============================================================================
-- 1. 스키마 정보 (doc_type: 'schema')
-- ============================================================================

-- employee 테이블 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'employee 테이블',
    'schema',
    '## employee 테이블 (직원 정보)

### 컬럼
- emp_id: INTEGER (PK) - 직원 고유 ID
- emp_name: VARCHAR(100) NOT NULL - 직원 이름
- emp_no: VARCHAR(20) UNIQUE - 사번
- email: VARCHAR(200) - 이메일 주소
- phone: VARCHAR(20) - 전화번호
- hire_date: DATE NOT NULL - 입사일
- dept_id: INTEGER (FK → department.dept_id) - 소속 부서 ID
- position: VARCHAR(50) - 직급 (사원, 대리, 과장, 차장, 부장, 이사)
- status: VARCHAR(20) DEFAULT ''active'' - 재직상태 (active, inactive, resigned)
- work_type: VARCHAR(20) - 근무유형 (office, remote, hybrid)
- location: VARCHAR(100) - 근무지

### 주요 관계
- department 테이블과 dept_id로 연결
- salary 테이블과 emp_id로 연결
- job_history 테이블과 emp_id로 연결
- performance_review 테이블과 emp_id로 연결

### 자주 사용되는 조건
- 재직자만 조회: WHERE status = ''active''
- 특정 연도 입사자: WHERE EXTRACT(YEAR FROM hire_date) = 2024
- 재택근무자: WHERE work_type IN (''remote'', ''hybrid'')',
    '{
        "table_name": "employee",
        "columns": ["emp_id", "emp_name", "emp_no", "email", "phone", "hire_date", "dept_id", "position", "status", "work_type", "location"],
        "primary_key": "emp_id",
        "foreign_keys": {"dept_id": "department.dept_id"},
        "row_count_estimate": 500,
        "category": "database",
        "tags": ["employee", "직원", "인사", "HR", "사원"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- department 테이블 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'department 테이블',
    'schema',
    '## department 테이블 (부서 정보)

### 컬럼
- dept_id: INTEGER (PK) - 부서 고유 ID
- dept_name: VARCHAR(100) NOT NULL - 부서명
- dept_code: VARCHAR(20) UNIQUE - 부서 코드
- parent_dept_id: INTEGER (FK → department.dept_id) - 상위 부서 ID
- manager_id: INTEGER (FK → employee.emp_id) - 부서장 직원 ID
- location: VARCHAR(100) - 부서 위치
- created_at: TIMESTAMP - 생성일

### 주요 관계
- employee 테이블과 dept_id로 연결 (1:N)
- 자기 참조로 상위/하위 부서 계층 구조

### 주요 부서 예시
- 개발팀, 영업팀, 마케팅팀, 인사팀, 재무팀, 기획팀',
    '{
        "table_name": "department",
        "columns": ["dept_id", "dept_name", "dept_code", "parent_dept_id", "manager_id", "location", "created_at"],
        "primary_key": "dept_id",
        "foreign_keys": {"parent_dept_id": "department.dept_id", "manager_id": "employee.emp_id"},
        "row_count_estimate": 20,
        "category": "database",
        "tags": ["department", "부서", "조직", "organization", "팀"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- salary 테이블 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'salary 테이블',
    'schema',
    '## salary 테이블 (급여 정보)

### 컬럼
- id: INTEGER (PK) - 급여 기록 ID
- emp_id: INTEGER (FK → employee.emp_id) - 직원 ID
- base_salary: NUMERIC(15,2) - 기본급 (원화 기준)
- bonus: NUMERIC(15,2) - 상여금
- effective_date: DATE - 적용 시작일
- end_date: DATE - 적용 종료일 (NULL이면 현재 적용 중)
- currency: VARCHAR(3) DEFAULT ''KRW'' - 통화

### 주요 관계
- employee 테이블과 emp_id로 연결

### 현재 급여 조회 패턴
**중요**: 현재 급여를 조회할 때는 반드시 end_date IS NULL 조건 사용

```sql
-- 현재 급여
SELECT * FROM salary WHERE emp_id = ? AND end_date IS NULL

-- 또는 날짜 범위로
WHERE effective_date <= CURRENT_DATE
  AND (end_date IS NULL OR end_date > CURRENT_DATE)
```',
    '{
        "table_name": "salary",
        "columns": ["id", "emp_id", "base_salary", "bonus", "effective_date", "end_date", "currency"],
        "primary_key": "id",
        "foreign_keys": {"emp_id": "employee.emp_id"},
        "row_count_estimate": 1000,
        "category": "database",
        "tags": ["salary", "급여", "연봉", "보수", "pay", "임금"],
        "sensitive": true
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- job_history 테이블 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'job_history 테이블',
    'schema',
    '## job_history 테이블 (인사 이력)

### 컬럼
- id: INTEGER (PK) - 이력 ID
- emp_id: INTEGER (FK → employee.emp_id) - 직원 ID
- dept_id: INTEGER (FK → department.dept_id) - 부서 ID
- position: VARCHAR(50) - 직급
- start_date: DATE - 시작일
- end_date: DATE - 종료일 (NULL이면 현재)
- change_type: VARCHAR(50) - 변경 유형 (hire, promotion, transfer, resignation)
- note: TEXT - 비고

### 주요 관계
- employee, department 테이블과 연결

### 변경 유형
- hire: 입사
- promotion: 승진
- transfer: 부서이동
- resignation: 퇴사',
    '{
        "table_name": "job_history",
        "columns": ["id", "emp_id", "dept_id", "position", "start_date", "end_date", "change_type", "note"],
        "primary_key": "id",
        "foreign_keys": {"emp_id": "employee.emp_id", "dept_id": "department.dept_id"},
        "row_count_estimate": 2000,
        "category": "database",
        "tags": ["job_history", "인사이력", "승진", "이동", "발령"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- performance_review 테이블 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'performance_review 테이블',
    'schema',
    '## performance_review 테이블 (성과 평가)

### 컬럼
- id: INTEGER (PK) - 평가 ID
- emp_id: INTEGER (FK → employee.emp_id) - 직원 ID
- review_year: INTEGER - 평가 연도
- review_period: VARCHAR(20) - 평가 기간 (H1, H2, annual)
- score: NUMERIC(3,1) - 점수 (1.0 ~ 5.0)
- grade: VARCHAR(10) - 등급 (S, A, B, C, D)
- reviewer_id: INTEGER (FK → employee.emp_id) - 평가자 ID
- comments: TEXT - 평가 코멘트
- created_at: TIMESTAMP - 생성일

### 주요 관계
- employee 테이블과 연결 (피평가자, 평가자)

### 등급 기준
- S: 4.5 이상 (최우수)
- A: 4.0 이상 (우수)
- B: 3.0 이상 (양호)
- C: 2.0 이상 (보통)
- D: 2.0 미만 (미흡)',
    '{
        "table_name": "performance_review",
        "columns": ["id", "emp_id", "review_year", "review_period", "score", "grade", "reviewer_id", "comments", "created_at"],
        "primary_key": "id",
        "foreign_keys": {"emp_id": "employee.emp_id", "reviewer_id": "employee.emp_id"},
        "row_count_estimate": 1500,
        "category": "database",
        "tags": ["performance_review", "성과", "평가", "인사고과", "KPI"],
        "sensitive": true
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);


-- ============================================================================
-- 2. Few-shot 쿼리 예제 (doc_type: 'query_example')
-- ============================================================================

-- 기본 COUNT 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 입사자 수는 몇 명인가요?',
    'query_example',
    '연도별 입사자 수를 집계하는 쿼리 예제

```sql
SELECT COUNT(*) as total_count
FROM employee
WHERE EXTRACT(YEAR FROM hire_date) = 2024
  AND status = ''active'';
```

**결과 예시**: 27명

**핵심 패턴**:
- 연도 추출: EXTRACT(YEAR FROM hire_date)
- 재직자만: status = ''active''',
    '{
        "intent": "AGGREGATE",
        "complexity": "simple",
        "tables": ["employee"],
        "sql_template": "SELECT COUNT(*) FROM employee WHERE EXTRACT(YEAR FROM hire_date) = ? AND status = ''active''",
        "category": "aggregate",
        "tags": ["입사", "연도별", "COUNT", "집계", "몇명"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 부서별 집계 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '부서별 직원 수를 알려줘',
    'query_example',
    '부서별 그룹화하여 직원 수 집계

```sql
SELECT
    d.dept_name,
    COUNT(e.emp_id) as employee_count
FROM department d
LEFT JOIN employee e ON d.dept_id = e.dept_id
  AND e.status = ''active''
GROUP BY d.dept_id, d.dept_name
ORDER BY employee_count DESC;
```

**결과 예시**:
- 개발팀: 45명
- 영업팀: 32명
- 마케팅팀: 18명

**핵심 패턴**:
- LEFT JOIN으로 직원이 없는 부서도 표시
- GROUP BY로 부서별 그룹화
- COUNT(e.emp_id)로 NULL 제외 카운트',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["employee", "department"],
        "sql_template": "SELECT d.dept_name, COUNT(e.emp_id) FROM department d LEFT JOIN employee e ON d.dept_id = e.dept_id GROUP BY d.dept_name",
        "category": "aggregate",
        "tags": ["부서별", "GROUP BY", "JOIN", "집계", "팀별"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 평균 급여 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '직급별 평균 급여는 얼마인가요?',
    'query_example',
    '직급별 그룹화하여 급여 통계 집계

```sql
SELECT
    e.position,
    ROUND(AVG(s.base_salary), 0) as avg_salary,
    MIN(s.base_salary) as min_salary,
    MAX(s.base_salary) as max_salary,
    COUNT(*) as employee_count
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
WHERE e.status = ''active''
  AND s.end_date IS NULL
GROUP BY e.position
ORDER BY avg_salary DESC;
```

**결과 예시**:
- 부장: 평균 8,500만원
- 차장: 평균 7,200만원
- 과장: 평균 5,800만원

**핵심 패턴**:
- 현재 급여: s.end_date IS NULL
- ROUND로 소수점 제거
- 집계 함수 AVG, MIN, MAX 동시 사용',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["employee", "salary"],
        "sql_template": "SELECT position, AVG(base_salary) FROM employee JOIN salary ON emp_id WHERE end_date IS NULL GROUP BY position",
        "category": "aggregate",
        "tags": ["급여", "평균", "직급별", "AVG", "GROUP BY", "연봉"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 조건부 조회 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '서울 근무 직원 중 재택근무자 목록',
    'query_example',
    '복수 조건 필터링 쿼리

```sql
SELECT
    e.emp_name,
    e.position,
    d.dept_name,
    e.work_type,
    e.location
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.location LIKE ''서울%''
  AND e.work_type IN (''remote'', ''hybrid'')
  AND e.status = ''active''
ORDER BY d.dept_name, e.emp_name;
```

**핵심 패턴**:
- 지역 조건: LIKE ''서울%''
- 재택근무: work_type IN (''remote'', ''hybrid'')
- 복수 조건 AND 결합',
    '{
        "intent": "SELECT",
        "complexity": "medium",
        "tables": ["employee", "department"],
        "sql_template": "SELECT emp_name, position, dept_name FROM employee JOIN department WHERE location LIKE ? AND work_type IN (?)",
        "category": "filter",
        "tags": ["근무지", "재택근무", "WHERE", "IN", "LIKE", "원격"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 기간 조건 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '최근 3개월 이내 입사한 신입사원',
    'query_example',
    '날짜 기간 조건 쿼리

```sql
SELECT
    e.emp_name,
    e.hire_date,
    e.position,
    d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= CURRENT_DATE - INTERVAL ''3 months''
  AND e.status = ''active''
ORDER BY e.hire_date DESC;
```

**핵심 패턴**:
- 기간 계산: CURRENT_DATE - INTERVAL ''3 months''
- 최신순 정렬: ORDER BY hire_date DESC',
    '{
        "intent": "SELECT",
        "complexity": "medium",
        "tables": ["employee", "department"],
        "sql_template": "SELECT emp_name, hire_date, position FROM employee WHERE hire_date >= CURRENT_DATE - INTERVAL ''?''",
        "category": "filter",
        "tags": ["기간", "최근", "INTERVAL", "날짜", "신입", "입사"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- TOP N 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '개발팀에서 급여가 가장 높은 5명은 누구인가요?',
    'query_example',
    '상위 N개 조회 쿼리

```sql
SELECT
    e.emp_name,
    e.position,
    s.base_salary,
    d.dept_name
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
JOIN department d ON e.dept_id = d.dept_id
WHERE d.dept_name = ''개발팀''
  AND e.status = ''active''
  AND s.end_date IS NULL
ORDER BY s.base_salary DESC
LIMIT 5;
```

**핵심 패턴**:
- 3개 테이블 JOIN
- 정렬 후 상위 N개: ORDER BY ... DESC LIMIT 5
- Oracle의 경우: FETCH FIRST 5 ROWS ONLY',
    '{
        "intent": "SELECT",
        "complexity": "complex",
        "tables": ["employee", "salary", "department"],
        "sql_template": "SELECT emp_name, position, base_salary FROM employee JOIN salary JOIN department WHERE dept_name = ? ORDER BY base_salary DESC LIMIT ?",
        "category": "ranking",
        "tags": ["급여", "순위", "ORDER BY", "LIMIT", "TOP", "높은"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 서브쿼리 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '평균 급여보다 높은 급여를 받는 직원 수',
    'query_example',
    '서브쿼리를 사용한 비교 쿼리

```sql
SELECT COUNT(*) as above_average_count
FROM employee e
JOIN salary s ON e.emp_id = s.emp_id
WHERE e.status = ''active''
  AND s.end_date IS NULL
  AND s.base_salary > (
      SELECT AVG(base_salary)
      FROM salary
      WHERE end_date IS NULL
  );
```

**핵심 패턴**:
- 서브쿼리로 평균 계산
- 메인 쿼리에서 비교 조건으로 사용
- 비교 연산자: >, <, >=, <=',
    '{
        "intent": "SUBQUERY",
        "complexity": "complex",
        "tables": ["employee", "salary"],
        "sql_template": "SELECT COUNT(*) FROM employee JOIN salary WHERE base_salary > (SELECT AVG(base_salary) FROM salary)",
        "category": "subquery",
        "tags": ["평균", "비교", "서브쿼리", "SUBQUERY", "보다높은"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 연도별 추이 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '연도별 입사자 수 추이',
    'query_example',
    '시계열 트렌드 쿼리

```sql
SELECT
    EXTRACT(YEAR FROM hire_date) as hire_year,
    COUNT(*) as hire_count
FROM employee
WHERE status = ''active''
  AND hire_date >= CURRENT_DATE - INTERVAL ''5 years''
GROUP BY EXTRACT(YEAR FROM hire_date)
ORDER BY hire_year;
```

**핵심 패턴**:
- EXTRACT(YEAR FROM date)로 연도 추출
- GROUP BY로 연도별 그룹화
- 최근 5년: >= CURRENT_DATE - INTERVAL ''5 years''',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["employee"],
        "sql_template": "SELECT EXTRACT(YEAR FROM hire_date), COUNT(*) FROM employee GROUP BY EXTRACT(YEAR FROM hire_date) ORDER BY 1",
        "category": "trend",
        "tags": ["연도별", "추이", "트렌드", "EXTRACT", "입사"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 성과 등급 분포 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 성과 평가 등급 분포',
    'query_example',
    '등급별 분포 및 비율 쿼리

```sql
SELECT
    grade,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM performance_review
WHERE review_year = 2024
GROUP BY grade
ORDER BY
    CASE grade
        WHEN ''S'' THEN 1
        WHEN ''A'' THEN 2
        WHEN ''B'' THEN 3
        WHEN ''C'' THEN 4
        WHEN ''D'' THEN 5
    END;
```

**핵심 패턴**:
- 윈도우 함수로 비율 계산: SUM(...) OVER()
- CASE WHEN으로 커스텀 정렬',
    '{
        "intent": "AGGREGATE",
        "complexity": "complex",
        "tables": ["performance_review"],
        "sql_template": "SELECT grade, COUNT(*), percentage FROM performance_review WHERE review_year = ? GROUP BY grade",
        "category": "distribution",
        "tags": ["성과", "평가", "등급", "분포", "비율", "percentage"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 다중 조건 필터 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '개발팀 과장 이상 직급 중 5년 이상 근속자',
    'query_example',
    '복합 조건 필터 쿼리

```sql
SELECT
    e.emp_name,
    e.position,
    e.hire_date,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) as years_of_service,
    s.base_salary
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
JOIN salary s ON e.emp_id = s.emp_id
WHERE d.dept_name = ''개발팀''
  AND e.position IN (''과장'', ''차장'', ''부장'', ''이사'')
  AND e.hire_date <= CURRENT_DATE - INTERVAL ''5 years''
  AND e.status = ''active''
  AND s.end_date IS NULL
ORDER BY years_of_service DESC;
```

**핵심 패턴**:
- AGE 함수로 근속 연수 계산
- IN 연산자로 복수 값 조건
- 다중 AND 조건 결합',
    '{
        "intent": "SELECT",
        "complexity": "complex",
        "tables": ["employee", "department", "salary"],
        "sql_template": "SELECT emp_name, position, years_of_service FROM employee JOIN department JOIN salary WHERE dept_name = ? AND position IN (?) AND hire_date <= ?",
        "category": "complex_filter",
        "tags": ["근속", "직급", "과장이상", "개발팀", "복합조건"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);


-- ============================================================================
-- 3. 비즈니스 용어집 (doc_type: 'glossary')
-- ============================================================================

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '재직자',
    'glossary',
    '**재직자 (Active Employee)**

현재 회사에 소속되어 근무 중인 직원을 의미합니다.

**SQL 조건**:
```sql
WHERE status = ''active''
```

**반대 개념**:
- 퇴직자: status = ''resigned''
- 휴직자: status = ''inactive''',
    '{
        "term": "재직자",
        "sql_condition": "status = ''active''",
        "synonyms": ["현직", "재직중", "active"],
        "column_reference": "employee.status",
        "category": "hr_terms",
        "tags": ["재직", "재직자", "active", "현직", "근무중"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '재택근무',
    'glossary',
    '**재택근무 (Remote Work)**

사무실이 아닌 자택에서 업무를 수행하는 근무 형태입니다.

**SQL 조건**:
```sql
-- 완전 재택
WHERE work_type = ''remote''

-- 재택 포함 (하이브리드)
WHERE work_type IN (''remote'', ''hybrid'')
```

**근무 유형**:
- office: 사무실 근무
- remote: 완전 재택
- hybrid: 혼합 근무 (주 2-3일 출근)',
    '{
        "term": "재택근무",
        "sql_condition": "work_type IN (''remote'', ''hybrid'')",
        "synonyms": ["원격근무", "WFH", "하이브리드", "홈오피스"],
        "column_reference": "employee.work_type",
        "category": "hr_terms",
        "tags": ["재택", "원격근무", "remote", "WFH", "하이브리드"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '현재 급여',
    'glossary',
    '**현재 급여 (Current Salary)**

현재 시점에 적용되고 있는 급여를 의미합니다.

**SQL 조건**:
```sql
-- 방법 1: end_date가 NULL인 레코드
WHERE end_date IS NULL

-- 방법 2: 날짜 범위로 조회
WHERE effective_date <= CURRENT_DATE
  AND (end_date IS NULL OR end_date > CURRENT_DATE)
```

**설명**:
salary 테이블은 급여 이력을 관리하며, end_date가 NULL인 레코드가 현재 적용 중인 급여입니다.',
    '{
        "term": "현재 급여",
        "sql_condition": "end_date IS NULL",
        "synonyms": ["현급여", "현재연봉", "current salary"],
        "column_reference": "salary.end_date",
        "category": "hr_terms",
        "tags": ["급여", "현재급여", "연봉", "current salary", "월급"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '신입사원',
    'glossary',
    '**신입사원 (New Employee)**

입사한지 1년 이내인 직원을 의미합니다.

**SQL 조건**:
```sql
-- 1년 이내
WHERE hire_date >= CURRENT_DATE - INTERVAL ''1 year''

-- 6개월 이내 (좁은 의미)
WHERE hire_date >= CURRENT_DATE - INTERVAL ''6 months''

-- 3개월 이내 (수습 기간)
WHERE hire_date >= CURRENT_DATE - INTERVAL ''3 months''
```

**참고**: 회사 정책에 따라 기준 기간이 다를 수 있습니다.',
    '{
        "term": "신입사원",
        "sql_condition": "hire_date >= CURRENT_DATE - INTERVAL ''1 year''",
        "synonyms": ["신입", "새직원", "new hire", "수습"],
        "column_reference": "employee.hire_date",
        "category": "hr_terms",
        "tags": ["신입", "신입사원", "새직원", "new hire", "수습"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '직급',
    'glossary',
    '**직급 (Position/Rank)**

조직 내에서의 계층적 위치를 나타냅니다.

**직급 체계 (낮은 순)**:
| 직급 | 영문 | 연차 기준 |
|------|------|----------|
| 사원 | Staff | 1-3년 |
| 대리 | Assistant Manager | 3-6년 |
| 과장 | Manager | 6-10년 |
| 차장 | Deputy GM | 10-15년 |
| 부장 | General Manager | 15년+ |
| 이사 | Director | 임원급 |

**SQL 예시**:
```sql
-- 과장 이상
WHERE position IN (''과장'', ''차장'', ''부장'', ''이사'')

-- 대리 이하
WHERE position IN (''사원'', ''대리'')
```',
    '{
        "term": "직급",
        "values": ["사원", "대리", "과장", "차장", "부장", "이사"],
        "column_reference": "employee.position",
        "category": "hr_terms",
        "tags": ["직급", "직위", "position", "rank", "사원", "대리", "과장", "차장", "부장", "이사"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '근속연수',
    'glossary',
    '**근속연수 (Years of Service)**

입사일부터 현재까지의 근무 기간을 연 단위로 표시합니다.

**SQL 계산**:
```sql
-- PostgreSQL
EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date)) as years

-- 또는
DATE_PART(''year'', AGE(CURRENT_DATE, hire_date)) as years

-- Oracle
TRUNC(MONTHS_BETWEEN(SYSDATE, hire_date) / 12) as years
```

**조건 예시**:
```sql
-- 5년 이상 근속자
WHERE hire_date <= CURRENT_DATE - INTERVAL ''5 years''
```',
    '{
        "term": "근속연수",
        "sql_pattern": "EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date))",
        "synonyms": ["근속", "재직기간", "tenure", "연차"],
        "column_reference": "employee.hire_date",
        "category": "hr_terms",
        "tags": ["근속", "근속연수", "재직기간", "tenure", "연차"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '성과 등급',
    'glossary',
    '**성과 등급 (Performance Grade)**

정기 인사 평가 결과를 등급으로 표시합니다.

**등급 체계**:
| 등급 | 점수 범위 | 의미 |
|------|----------|------|
| S | 4.5 이상 | 최우수 (Superb) |
| A | 4.0-4.4 | 우수 (Excellent) |
| B | 3.0-3.9 | 양호 (Good) |
| C | 2.0-2.9 | 보통 (Average) |
| D | 2.0 미만 | 미흡 (Below) |

**SQL 예시**:
```sql
-- 우수 이상 (S, A등급)
WHERE grade IN (''S'', ''A'')

-- 특정 연도 평가
WHERE review_year = 2024
```',
    '{
        "term": "성과 등급",
        "values": ["S", "A", "B", "C", "D"],
        "column_reference": "performance_review.grade",
        "category": "hr_terms",
        "tags": ["성과", "평가", "등급", "grade", "인사고과", "S등급", "A등급"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '평가 기간',
    'glossary',
    '**평가 기간 (Review Period)**

성과 평가가 적용되는 기간을 나타냅니다.

**평가 기간 유형**:
- H1: 상반기 (1월-6월)
- H2: 하반기 (7월-12월)
- annual: 연간 평가

**SQL 예시**:
```sql
-- 2024년 상반기 평가
WHERE review_year = 2024 AND review_period = ''H1''

-- 연간 평가만
WHERE review_period = ''annual''
```',
    '{
        "term": "평가 기간",
        "values": ["H1", "H2", "annual"],
        "column_reference": "performance_review.review_period",
        "category": "hr_terms",
        "tags": ["평가기간", "상반기", "하반기", "H1", "H2", "annual"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);


-- ============================================================================
-- 확인 쿼리
-- ============================================================================

-- 추가된 데이터 확인 (usage_type으로 필터)
SELECT usage_type, doc_type, COUNT(*) as count
FROM tb_docs
WHERE usage_type = 'cortex'
GROUP BY usage_type, doc_type
ORDER BY doc_type;

-- Cortex 데이터 목록
SELECT id, title, doc_type, usage_type, source_type
FROM tb_docs
WHERE usage_type = 'cortex'
ORDER BY doc_type, title;

-- 임베딩 대기 중인 Cortex 문서 확인 (indexed=true, embedding IS NULL)
SELECT id, title, doc_type
FROM tb_docs
WHERE usage_type = 'cortex'
  AND indexed = true
  AND embedding IS NULL;
