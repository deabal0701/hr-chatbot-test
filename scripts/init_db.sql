-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ===================================
-- 1. 문서(텍스트)용 테이블
-- ===================================
CREATE TABLE IF NOT EXISTS hr_docs (
  id              BIGSERIAL PRIMARY KEY,
  title           TEXT NOT NULL,
  doc_type        TEXT NOT NULL,           -- 'policy', 'job_posting', 'faq', 'guide'
  language        TEXT DEFAULT 'ko',       -- 'ko', 'en'
  content         TEXT NOT NULL,
  metadata        JSONB,                   -- {"year":2024,"department":"HR","region":"Seoul"}
  embedding       VECTOR(1536),            -- text-embedding-3-small 차원수
  embedding_model TEXT DEFAULT 'text-embedding-3-small',
  indexed         BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- pgvector index (IVFFlat for approximate nearest neighbor search)
CREATE INDEX IF NOT EXISTS idx_hr_docs_embedding
  ON hr_docs USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 100);

-- Additional indexes for filtering
CREATE INDEX IF NOT EXISTS idx_hr_docs_doc_type ON hr_docs(doc_type);
CREATE INDEX IF NOT EXISTS idx_hr_docs_language ON hr_docs(language);
CREATE INDEX IF NOT EXISTS idx_hr_docs_metadata ON hr_docs USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_hr_docs_created_at ON hr_docs(created_at DESC);

-- ===================================
-- 2. HR 구조화 데이터
-- ===================================

-- 부서 테이블
CREATE TABLE IF NOT EXISTS department (
  dept_id         BIGSERIAL PRIMARY KEY,
  dept_name       TEXT NOT NULL,
  dept_code       TEXT UNIQUE,
  parent_dept_id  BIGINT REFERENCES department(dept_id),
  region          TEXT,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_department_parent ON department(parent_dept_id);
CREATE INDEX IF NOT EXISTS idx_department_region ON department(region);

-- 직원 테이블
CREATE TABLE IF NOT EXISTS employee (
  emp_id          BIGSERIAL PRIMARY KEY,
  emp_no          TEXT UNIQUE NOT NULL,
  name            TEXT NOT NULL,
  name_en         TEXT,
  gender          TEXT,
  birth_date      DATE,
  hire_date       DATE NOT NULL,
  position        TEXT,                    -- 직급: 사원, 대리, 과장, 차장, 부장
  job_family      TEXT,                    -- 직무: 개발, 기획, 디자인, 마케팅
  department_id   BIGINT REFERENCES department(dept_id),
  work_location   TEXT,
  employment_type TEXT,                    -- 정규직, 계약직, 인턴
  status          TEXT DEFAULT 'active',   -- active, resigned, on_leave
  resignation_date DATE,
  email           TEXT,
  phone           TEXT,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_employee_emp_no ON employee(emp_no);
CREATE INDEX IF NOT EXISTS idx_employee_hire_date ON employee(hire_date);
CREATE INDEX IF NOT EXISTS idx_employee_department ON employee(department_id);
CREATE INDEX IF NOT EXISTS idx_employee_status ON employee(status);
CREATE INDEX IF NOT EXISTS idx_employee_job_family ON employee(job_family);
CREATE INDEX IF NOT EXISTS idx_employee_work_location ON employee(work_location);

-- 직무 이력 테이블
CREATE TABLE IF NOT EXISTS job_history (
  id              BIGSERIAL PRIMARY KEY,
  emp_id          BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
  from_date       DATE NOT NULL,
  to_date         DATE,
  department_id   BIGINT REFERENCES department(dept_id),
  position        TEXT,
  job_family      TEXT,
  work_location   TEXT,
  change_reason   TEXT,                    -- promotion, transfer, restructuring
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_history_emp ON job_history(emp_id);
CREATE INDEX IF NOT EXISTS idx_job_history_dates ON job_history(from_date, to_date);

-- 급여 테이블 (민감 정보)
CREATE TABLE IF NOT EXISTS salary (
  id              BIGSERIAL PRIMARY KEY,
  emp_id          BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
  effective_date  DATE NOT NULL,
  base_salary     NUMERIC(12, 2),
  currency        TEXT DEFAULT 'KRW',
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_salary_emp ON salary(emp_id);
CREATE INDEX IF NOT EXISTS idx_salary_date ON salary(effective_date DESC);

-- 평가 테이블
CREATE TABLE IF NOT EXISTS performance_review (
  id              BIGSERIAL PRIMARY KEY,
  emp_id          BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
  review_period   TEXT NOT NULL,           -- '2024-H1', '2024-H2'
  reviewer_id     BIGINT REFERENCES employee(emp_id),
  rating          TEXT,                    -- S, A, B, C, D
  comments        TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_performance_emp ON performance_review(emp_id);
CREATE INDEX IF NOT EXISTS idx_performance_period ON performance_review(review_period);

-- ===================================
-- 3. 로깅/감사 테이블
-- ===================================

-- 검색 쿼리 로그
CREATE TABLE IF NOT EXISTS query_log (
  id              BIGSERIAL PRIMARY KEY,
  user_id         TEXT,
  query_text      TEXT NOT NULL,
  query_type      TEXT,                    -- 'rag', 'nl2sql', 'hybrid'
  intent          TEXT,
  filters         JSONB,
  response_time_ms INTEGER,
  success         BOOLEAN DEFAULT true,
  error_message   TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_log_user ON query_log(user_id);
CREATE INDEX IF NOT EXISTS idx_query_log_created ON query_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_log_type ON query_log(query_type);

-- NL2SQL 실행 로그
CREATE TABLE IF NOT EXISTS sql_execution_log (
  id              BIGSERIAL PRIMARY KEY,
  query_log_id    BIGINT REFERENCES query_log(id) ON DELETE CASCADE,
  generated_sql   TEXT NOT NULL,
  executed_sql    TEXT,
  row_count       INTEGER,
  execution_time_ms INTEGER,
  success         BOOLEAN DEFAULT true,
  error_message   TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sql_log_query ON sql_execution_log(query_log_id);
CREATE INDEX IF NOT EXISTS idx_sql_log_created ON sql_execution_log(created_at DESC);

-- RAG 검색 로그
CREATE TABLE IF NOT EXISTS rag_search_log (
  id              BIGSERIAL PRIMARY KEY,
  query_log_id    BIGINT REFERENCES query_log(id) ON DELETE CASCADE,
  top_k           INTEGER,
  retrieved_docs  JSONB,                   -- [{"doc_id": 1, "score": 0.95, "title": "..."}, ...]
  llm_model       TEXT,
  llm_tokens      INTEGER,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_log_query ON rag_search_log(query_log_id);

-- ===================================
-- 4. 사용자/권한 테이블 (간단한 버전)
-- ===================================

CREATE TABLE IF NOT EXISTS users (
  id              BIGSERIAL PRIMARY KEY,
  username        TEXT UNIQUE NOT NULL,
  email           TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  full_name       TEXT,
  role            TEXT DEFAULT 'user',     -- admin, hr_manager, user
  department_id   BIGINT REFERENCES department(dept_id),
  is_active       BOOLEAN DEFAULT true,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ===================================
-- 5. 샘플 데이터 (테스트용)
-- ===================================

-- 부서 샘플 데이터
INSERT INTO department (dept_name, dept_code, region) VALUES
  ('경영지원본부', 'MGMT', '서울'),
  ('인사팀', 'HR', '서울'),
  ('재무팀', 'FIN', '서울'),
  ('기술본부', 'TECH', '서울'),
  ('개발1팀', 'DEV1', '서울'),
  ('개발2팀', 'DEV2', '판교'),
  ('데이터팀', 'DATA', '서울'),
  ('마케팅본부', 'MKT', '서울'),
  ('영업본부', 'SALES', '서울')
ON CONFLICT (dept_code) DO NOTHING;

-- 직원 샘플 데이터
INSERT INTO employee (emp_no, name, gender, birth_date, hire_date, position, job_family, department_id, work_location, employment_type, status, email)
SELECT
  'EMP' || LPAD(i::TEXT, 5, '0'),
  '직원' || i,
  CASE WHEN random() < 0.5 THEN '남' ELSE '여' END,
  DATE '1980-01-01' + (random() * 365 * 20)::INTEGER,
  DATE '2020-01-01' + (random() * 365 * 4)::INTEGER,
  (ARRAY['사원', '대리', '과장', '차장', '부장'])[floor(random() * 5 + 1)],
  (ARRAY['개발', '기획', '디자인', 'HR', '마케팅', '영업'])[floor(random() * 6 + 1)],
  floor(random() * 9 + 1)::BIGINT,
  (ARRAY['서울', '판교', '부산'])[floor(random() * 3 + 1)],
  (ARRAY['정규직', '계약직'])[floor(random() * 2 + 1)],
  'active',
  'emp' || i || '@company.com'
FROM generate_series(1, 100) AS i
ON CONFLICT (emp_no) DO NOTHING;

-- 문서 샘플 데이터
INSERT INTO hr_docs (title, doc_type, language, content, metadata) VALUES
  ('2024년 채용 공고 - 백엔드 개발자', 'job_posting', 'ko',
   '우리 회사는 Python/Django 기반 백엔드 개발자를 채용합니다. 경력 3년 이상, AWS 경험 우대.',
   '{"year": 2024, "department": "개발", "position": "백엔드개발자"}'::jsonb),

  ('재택근무 정책 안내', 'policy', 'ko',
   '2024년부터 주 2회 재택근무가 가능합니다. 사전에 팀장 승인을 받아야 하며, 협업 툴을 통한 업무 공유가 필수입니다.',
   '{"year": 2024, "category": "근무제도"}'::jsonb),

  ('연차 사용 가이드', 'guide', 'ko',
   '연차는 1년 근속 시 15일이 부여됩니다. 사용은 1일 전 신청을 원칙으로 하며, 팀 업무 상황을 고려해야 합니다.',
   '{"year": 2024, "category": "휴가"}'::jsonb),

  ('인사평가 FAQ', 'faq', 'ko',
   'Q: 인사평가는 언 실시되나요? A: 연 2회, 상반기와 하반기에 실시됩니다. Q: 평가 등급은? A: S, A, B, C, D 5단계입니다.',
   '{"year": 2024, "category": "평가"}'::jsonb)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE hr_docs IS '인사 관련 문서 및 벡터 검색용 테이블';
COMMENT ON TABLE employee IS '직원 정보 테이블';
COMMENT ON TABLE department IS '부서 정보 테이블';
COMMENT ON TABLE query_log IS '사용자 검색 쿼리 로그';
COMMENT ON TABLE sql_execution_log IS 'NL2SQL 실행 로그';
