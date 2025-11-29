-- =====================================================
-- HR Chatbot 데이터베이스 초기화 스크립트
-- 실행: python scripts/init_db.py
-- =====================================================

-- Enable pgvector extension (슈퍼유저 권한필요)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ===================================
-- 0. 기존 테이블 삭제 (의존성 역순)
-- ===================================
DROP VIEW IF EXISTS v_document_chunks CASCADE;
DROP TABLE IF EXISTS rag_search_log CASCADE;
DROP TABLE IF EXISTS sql_execution_log CASCADE;
DROP TABLE IF EXISTS query_log CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS salary CASCADE;
DROP TABLE IF EXISTS job_history CASCADE;
DROP TABLE IF EXISTS performance_review CASCADE;
DROP TABLE IF EXISTS employee CASCADE;
DROP TABLE IF EXISTS department CASCADE;
DROP TABLE IF EXISTS hr_docs CASCADE;

-- ===================================
-- 1. 문서(텍스트)용 테이블 (청킹 지원)
-- ===================================

CREATE TABLE hr_docs (
  id              BIGSERIAL PRIMARY KEY,
  title           TEXT NOT NULL,
  doc_type        TEXT NOT NULL,           -- 'policy', 'job_posting', 'faq', 'guide'
  language        TEXT DEFAULT 'ko',       -- 'ko', 'en'
  content         TEXT NOT NULL,
  metadata        JSONB,                   -- {"year":2024,"department":"HR","region":"Seoul"}

  -- 임베딩 관련
  embedding       VECTOR(1536),            -- text-embedding-3-small 차원수
  embedding_model TEXT DEFAULT 'text-embedding-3-small',
  indexed         BOOLEAN DEFAULT false,   -- 임베딩 완료 여부
  embedded_at     TIMESTAMPTZ,             -- 임베딩 생성 일시

  -- 청킹 관련
  chunk_index     INTEGER DEFAULT 0,       -- 청크 순서 (0부터 시작)
  total_chunks    INTEGER DEFAULT 1,       -- 전체 청크 수
  parent_doc_id   BIGINT REFERENCES hr_docs(id) ON DELETE CASCADE,  -- 원본 문서 ID

  -- 소스 관련
  source_type     TEXT DEFAULT 'ui_input', -- 'ui_input', 'pdf', 'web', 'api'
  source_file     TEXT,                    -- 원본 파일명
  content_hash    TEXT,                    -- 컨텐츠 MD5 해시 (중복 검사용)

  -- 타임스탬프
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- pgvector index (IVFFlat for approximate nearest neighbor search)
CREATE INDEX idx_hr_docs_embedding ON hr_docs USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- 필터링용 인덱스
CREATE INDEX idx_hr_docs_doc_type ON hr_docs(doc_type);
CREATE INDEX idx_hr_docs_language ON hr_docs(language);
CREATE INDEX idx_hr_docs_metadata ON hr_docs USING gin(metadata);
CREATE INDEX idx_hr_docs_created_at ON hr_docs(created_at DESC);
CREATE INDEX idx_hr_docs_indexed ON hr_docs(indexed);
CREATE INDEX idx_hr_docs_source_type ON hr_docs(source_type);
CREATE INDEX idx_hr_docs_parent_doc ON hr_docs(parent_doc_id);
CREATE INDEX idx_hr_docs_content_hash ON hr_docs(content_hash);

-- ===================================
-- 2. HR 구조화 데이터
-- ===================================

-- 부서 테이블
CREATE TABLE department (
  dept_id         BIGSERIAL PRIMARY KEY,
  dept_name       TEXT NOT NULL,
  dept_code       TEXT UNIQUE,
  parent_dept_id  BIGINT REFERENCES department(dept_id),
  region          TEXT,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_department_parent ON department(parent_dept_id);
CREATE INDEX idx_department_region ON department(region);

-- 직원 테이블
CREATE TABLE employee (
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

CREATE INDEX idx_employee_emp_no ON employee(emp_no);
CREATE INDEX idx_employee_hire_date ON employee(hire_date);
CREATE INDEX idx_employee_department ON employee(department_id);
CREATE INDEX idx_employee_status ON employee(status);
CREATE INDEX idx_employee_job_family ON employee(job_family);
CREATE INDEX idx_employee_work_location ON employee(work_location);

-- 직무 이력 테이블
CREATE TABLE job_history (
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

CREATE INDEX idx_job_history_emp ON job_history(emp_id);
CREATE INDEX idx_job_history_dates ON job_history(from_date, to_date);

-- 급여 테이블 (민감 정보)
CREATE TABLE salary (
  id              BIGSERIAL PRIMARY KEY,
  emp_id          BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
  effective_date  DATE NOT NULL,
  base_salary     NUMERIC(12, 2),
  currency        TEXT DEFAULT 'KRW',
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_salary_emp ON salary(emp_id);
CREATE INDEX idx_salary_date ON salary(effective_date DESC);

-- 평가 테이블
CREATE TABLE performance_review (
  id              BIGSERIAL PRIMARY KEY,
  emp_id          BIGINT NOT NULL REFERENCES employee(emp_id) ON DELETE CASCADE,
  review_period   TEXT NOT NULL,           -- '2024-H1', '2024-H2'
  reviewer_id     BIGINT REFERENCES employee(emp_id),
  rating          TEXT,                    -- S, A, B, C, D
  comments        TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_performance_emp ON performance_review(emp_id);
CREATE INDEX idx_performance_period ON performance_review(review_period);

-- ===================================
-- 3. 로깅/감사 테이블
-- ===================================

-- 검색 쿼리 로그
CREATE TABLE query_log (
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

CREATE INDEX idx_query_log_user ON query_log(user_id);
CREATE INDEX idx_query_log_created ON query_log(created_at DESC);
CREATE INDEX idx_query_log_type ON query_log(query_type);

-- NL2SQL 실행 로그
CREATE TABLE sql_execution_log (
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

CREATE INDEX idx_sql_log_query ON sql_execution_log(query_log_id);
CREATE INDEX idx_sql_log_created ON sql_execution_log(created_at DESC);

-- RAG 검색 로그
CREATE TABLE rag_search_log (
  id              BIGSERIAL PRIMARY KEY,
  query_log_id    BIGINT REFERENCES query_log(id) ON DELETE CASCADE,
  top_k           INTEGER,
  retrieved_docs  JSONB,                   -- [{"doc_id": 1, "score": 0.95, "title": "..."}, ...]
  llm_model       TEXT,
  llm_tokens      INTEGER,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_rag_log_query ON rag_search_log(query_log_id);

-- ===================================
-- 4. 사용자/권한 테이블 (간단한 버전)
-- ===================================
CREATE TABLE users (
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

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ===================================
-- 5. 뷰 생성
-- ===================================

-- 청킹된 문서 조회 뷰
CREATE OR REPLACE VIEW v_document_chunks AS
SELECT
    COALESCE(parent_doc_id, id) as document_id,
    id as chunk_id,
    title,
    doc_type,
    chunk_index,
    total_chunks,
    LENGTH(content) as content_length,
    indexed,
    source_type,
    created_at
FROM hr_docs
ORDER BY COALESCE(parent_doc_id, id), chunk_index;

-- ===================================
-- 6. 샘플 데이터 (HR 구조화 데이터만)
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

-- ===================================
-- 7. 테이블 코멘트
-- ===================================
COMMENT ON TABLE hr_docs IS '인사 관련 문서 및 벡터 검색용 테이블 (청킹 지원)';
COMMENT ON TABLE employee IS '직원 정보 테이블';
COMMENT ON TABLE department IS '부서 정보 테이블';
COMMENT ON TABLE query_log IS '사용자 검색 쿼리 로그';
COMMENT ON TABLE sql_execution_log IS 'NL2SQL 실행 로그';
COMMENT ON VIEW v_document_chunks IS '청킹된 문서 조회용 뷰';

-- ===================================
-- 8. 시스템 설정 테이블
-- ===================================

CREATE TABLE app_settings (
  id              BIGSERIAL PRIMARY KEY,
  category        VARCHAR(50) NOT NULL,       -- 'openai', 'embedding', 'llm', 'rag', 'nl2sql', 'chunking'
  key             VARCHAR(100) NOT NULL,
  value           TEXT NOT NULL,
  value_type      VARCHAR(20) DEFAULT 'string',  -- 'string', 'int', 'float', 'bool', 'json'
  description     TEXT,
  is_secret       BOOLEAN DEFAULT FALSE,      -- API Key 등 마스킹 표시
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE(category, key)
);

CREATE INDEX idx_app_settings_category ON app_settings(category);

COMMENT ON TABLE app_settings IS '시스템 설정 테이블 (런타임 설정 관리)';

-- 기본 설정값 삽입
INSERT INTO app_settings (category, key, value, value_type, description, is_secret) VALUES
  -- OpenAI 설정
  ('openai', 'api_key', '', 'string', 'OpenAI API Key', TRUE),
  ('openai', 'organization_id', '', 'string', 'OpenAI Organization ID (선택)', FALSE),

  -- 임베딩 설정
  ('embedding', 'model', 'text-embedding-3-small', 'string', '임베딩 모델명', FALSE),
  ('embedding', 'dimension', '1536', 'int', '벡터 차원 수', FALSE),

  -- LLM 설정
  ('llm', 'model', 'gpt-4-turbo-preview', 'string', 'LLM 모델명', FALSE),
  ('llm', 'temperature', '0.1', 'float', '생성 온도 (0.0-2.0)', FALSE),
  ('llm', 'max_tokens', '2000', 'int', '최대 토큰 수', FALSE),

  -- RAG 설정
  ('rag', 'top_k', '10', 'int', '검색 문서 수', FALSE),
  ('rag', 'similarity_threshold', '0.7', 'float', '유사도 임계값 (0.0-1.0)', FALSE),
  ('rag', 'max_context_length', '4000', 'int', '최대 컨텍스트 길이', FALSE),

  -- NL2SQL 설정
  ('nl2sql', 'timeout_seconds', '30', 'int', 'SQL 실행 타임아웃 (초)', FALSE),
  ('nl2sql', 'max_rows', '1000', 'int', '최대 반환 행 수', FALSE),
  ('nl2sql', 'read_only_mode', 'true', 'bool', '읽기 전용 모드', FALSE),

  -- 청킹 설정
  ('chunking', 'default_chunk_size', '1000', 'int', '기본 청크 크기 (문자)', FALSE),
  ('chunking', 'default_overlap', '100', 'int', '기본 오버랩 크기 (문자)', FALSE)
ON CONFLICT (category, key) DO NOTHING;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'HR Chatbot 데이터베이스 초기화 완료!';
    RAISE NOTICE '==========================================';
END $$;
