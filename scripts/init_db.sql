-- public.app_settings definition

-- Drop table

-- DROP TABLE public.app_settings;

CREATE TABLE public.app_settings (
	id bigserial NOT NULL,
	category varchar(50) NOT NULL,
	"key" varchar(100) NOT NULL,
	value text NOT NULL,
	value_type varchar(20) DEFAULT 'string'::character varying NULL,
	description text NULL,
	is_secret bool DEFAULT false NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT app_settings_category_key_key UNIQUE (category, key),
	CONSTRAINT app_settings_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_app_settings_category ON public.app_settings USING btree (category);


-- public.code_master definition

-- Drop table

-- DROP TABLE public.code_master;

CREATE TABLE public.code_master (
	code_id bigserial NOT NULL,
	code_group varchar(50) NOT NULL,
	code_value varchar(100) NOT NULL,
	code_name varchar(200) NOT NULL,
	description text NULL,
	metadata jsonb NULL,
	sort_order int4 DEFAULT 0 NULL,
	is_active bool DEFAULT true NULL,
	is_system bool DEFAULT false NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT code_master_code_group_code_value_key UNIQUE (code_group, code_value),
	CONSTRAINT code_master_pkey PRIMARY KEY (code_id)
);
CREATE INDEX idx_code_master_active ON public.code_master USING btree (is_active);
CREATE INDEX idx_code_master_group ON public.code_master USING btree (code_group);
CREATE INDEX idx_code_master_group_active ON public.code_master USING btree (code_group, is_active);


-- public.query_log definition

-- Drop table

-- DROP TABLE public.query_log;

CREATE TABLE public.query_log (
	id bigserial NOT NULL,
	user_id text NULL,
	query_text text NOT NULL,
	query_type text NULL,
	intent text NULL,
	filters jsonb NULL,
	response_time_ms int4 NULL,
	success bool DEFAULT true NULL,
	error_message text NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT query_log_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_query_log_created ON public.query_log USING btree (created_at DESC);
CREATE INDEX idx_query_log_type ON public.query_log USING btree (query_type);
CREATE INDEX idx_query_log_user ON public.query_log USING btree (user_id);


-- public.vect_test definition

-- Drop table

-- DROP TABLE public.vect_test;

CREATE TABLE public.vect_test (
	id serial4 NOT NULL,
	emb public.vector NULL,
	CONSTRAINT vect_test_pkey PRIMARY KEY (id)
);


-- public.department definition

-- Drop table

-- DROP TABLE public.department;

CREATE TABLE public.department (
	dept_id bigserial NOT NULL,
	dept_name text NOT NULL,
	dept_code text NULL,
	parent_dept_id int8 NULL,
	region text NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT department_dept_code_key UNIQUE (dept_code),
	CONSTRAINT department_pkey PRIMARY KEY (dept_id),
	CONSTRAINT department_parent_dept_id_fkey FOREIGN KEY (parent_dept_id) REFERENCES public.department(dept_id)
);
CREATE INDEX idx_department_parent ON public.department USING btree (parent_dept_id);
CREATE INDEX idx_department_region ON public.department USING btree (region);


-- public.employee definition

-- Drop table

-- DROP TABLE public.employee;

CREATE TABLE public.employee (
	emp_id bigserial NOT NULL,
	emp_no text NOT NULL,
	"name" text NOT NULL,
	name_en text NULL,
	gender text NULL,
	birth_date date NULL,
	hire_date date NOT NULL,
	"position" text NULL,
	job_family text NULL,
	department_id int8 NULL,
	work_location text NULL,
	employment_type text NULL,
	status text DEFAULT 'active'::text NULL,
	resignation_date date NULL,
	email text NULL,
	phone text NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT employee_emp_no_key UNIQUE (emp_no),
	CONSTRAINT employee_pkey PRIMARY KEY (emp_id),
	CONSTRAINT employee_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(dept_id)
);
CREATE INDEX idx_employee_department ON public.employee USING btree (department_id);
CREATE INDEX idx_employee_emp_no ON public.employee USING btree (emp_no);
CREATE INDEX idx_employee_hire_date ON public.employee USING btree (hire_date);
CREATE INDEX idx_employee_job_family ON public.employee USING btree (job_family);
CREATE INDEX idx_employee_status ON public.employee USING btree (status);
CREATE INDEX idx_employee_work_location ON public.employee USING btree (work_location);


-- public.hr_docs definition

-- Drop table

-- DROP TABLE public.hr_docs;

CREATE TABLE public.hr_docs (
	id bigserial NOT NULL,
	title text NOT NULL,
	doc_type text NOT NULL,
	"language" text DEFAULT 'ko'::text NULL,
	"content" text NOT NULL,
	metadata jsonb NULL,
	embedding public.vector NULL,
	embedding_model text DEFAULT 'text-embedding-3-small'::text NULL,
	indexed bool DEFAULT false NULL,
	embedded_at timestamptz NULL,
	chunk_index int4 DEFAULT 0 NULL,
	total_chunks int4 DEFAULT 1 NULL,
	parent_doc_id int8 NULL,
	source_type text DEFAULT 'ui_input'::text NULL,
	source_file text NULL,
	content_hash text NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT hr_docs_pkey PRIMARY KEY (id),
	CONSTRAINT hr_docs_parent_doc_id_fkey FOREIGN KEY (parent_doc_id) REFERENCES public.hr_docs(id) ON DELETE CASCADE
);
CREATE INDEX idx_hr_docs_content_hash ON public.hr_docs USING btree (content_hash);
CREATE INDEX idx_hr_docs_created_at ON public.hr_docs USING btree (created_at DESC);
CREATE INDEX idx_hr_docs_doc_type ON public.hr_docs USING btree (doc_type);
CREATE INDEX idx_hr_docs_embedding ON public.hr_docs USING ivfflat (embedding) WITH (lists='100');
CREATE INDEX idx_hr_docs_indexed ON public.hr_docs USING btree (indexed);
CREATE INDEX idx_hr_docs_language ON public.hr_docs USING btree (language);
CREATE INDEX idx_hr_docs_metadata ON public.hr_docs USING gin (metadata);
CREATE INDEX idx_hr_docs_parent_doc ON public.hr_docs USING btree (parent_doc_id);
CREATE INDEX idx_hr_docs_source_type ON public.hr_docs USING btree (source_type);


-- public.job_history definition

-- Drop table

-- DROP TABLE public.job_history;

CREATE TABLE public.job_history (
	id bigserial NOT NULL,
	emp_id int8 NOT NULL,
	from_date date NOT NULL,
	to_date date NULL,
	department_id int8 NULL,
	"position" text NULL,
	job_family text NULL,
	work_location text NULL,
	change_reason text NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT job_history_pkey PRIMARY KEY (id),
	CONSTRAINT job_history_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(dept_id),
	CONSTRAINT job_history_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES public.employee(emp_id) ON DELETE CASCADE
);
CREATE INDEX idx_job_history_dates ON public.job_history USING btree (from_date, to_date);
CREATE INDEX idx_job_history_emp ON public.job_history USING btree (emp_id);


-- public.performance_review definition

-- Drop table

-- DROP TABLE public.performance_review;

CREATE TABLE public.performance_review (
	id bigserial NOT NULL,
	emp_id int8 NOT NULL,
	review_period text NOT NULL,
	reviewer_id int8 NULL,
	rating text NULL,
	"comments" text NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT performance_review_pkey PRIMARY KEY (id),
	CONSTRAINT performance_review_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES public.employee(emp_id) ON DELETE CASCADE,
	CONSTRAINT performance_review_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.employee(emp_id)
);
CREATE INDEX idx_performance_emp ON public.performance_review USING btree (emp_id);
CREATE INDEX idx_performance_period ON public.performance_review USING btree (review_period);


-- public.rag_search_log definition

-- Drop table

-- DROP TABLE public.rag_search_log;

CREATE TABLE public.rag_search_log (
	id bigserial NOT NULL,
	query_log_id int8 NULL,
	top_k int4 NULL,
	retrieved_docs jsonb NULL,
	llm_model text NULL,
	llm_tokens int4 NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT rag_search_log_pkey PRIMARY KEY (id),
	CONSTRAINT rag_search_log_query_log_id_fkey FOREIGN KEY (query_log_id) REFERENCES public.query_log(id) ON DELETE CASCADE
);
CREATE INDEX idx_rag_log_query ON public.rag_search_log USING btree (query_log_id);


-- public.salary definition

-- Drop table

-- DROP TABLE public.salary;

CREATE TABLE public.salary (
	id bigserial NOT NULL,
	emp_id int8 NOT NULL,
	effective_date date NOT NULL,
	base_salary numeric(12, 2) NULL,
	currency text DEFAULT 'KRW'::text NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT salary_pkey PRIMARY KEY (id),
	CONSTRAINT salary_emp_id_fkey FOREIGN KEY (emp_id) REFERENCES public.employee(emp_id) ON DELETE CASCADE
);
CREATE INDEX idx_salary_date ON public.salary USING btree (effective_date DESC);
CREATE INDEX idx_salary_emp ON public.salary USING btree (emp_id);


-- public.sql_execution_log definition

-- Drop table

-- DROP TABLE public.sql_execution_log;

CREATE TABLE public.sql_execution_log (
	id bigserial NOT NULL,
	query_log_id int8 NULL,
	generated_sql text NOT NULL,
	executed_sql text NULL,
	row_count int4 NULL,
	execution_time_ms int4 NULL,
	success bool DEFAULT true NULL,
	error_message text NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT sql_execution_log_pkey PRIMARY KEY (id),
	CONSTRAINT sql_execution_log_query_log_id_fkey FOREIGN KEY (query_log_id) REFERENCES public.query_log(id) ON DELETE CASCADE
);
CREATE INDEX idx_sql_log_created ON public.sql_execution_log USING btree (created_at DESC);
CREATE INDEX idx_sql_log_query ON public.sql_execution_log USING btree (query_log_id);


-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users (
	id bigserial NOT NULL,
	username text NOT NULL,
	email text NOT NULL,
	hashed_password text NOT NULL,
	full_name text NULL,
	"role" text DEFAULT 'user'::text NULL,
	department_id int8 NULL,
	is_active bool DEFAULT true NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT users_email_key UNIQUE (email),
	CONSTRAINT users_pkey PRIMARY KEY (id),
	CONSTRAINT users_username_key UNIQUE (username),
	CONSTRAINT users_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.department(dept_id)
);
CREATE INDEX idx_users_email ON public.users USING btree (email);
CREATE INDEX idx_users_username ON public.users USING btree (username);


INSERT INTO public.app_settings (category,"key",value,value_type,description,is_secret,created_at,updated_at) VALUES
	 ('nl2sql','timeout_seconds','30','int','SQL 실행 타임아웃 (초)',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:28:33.4552+09'),
	 ('nl2sql','max_rows','1000','int','최대 반환 행 수',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:28:33.4552+09'),
	 ('nl2sql','read_only_mode','true','bool','읽기 전용 모드',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:28:33.4552+09'),
	 ('chunking','default_chunk_size','1000','int','기본 청크 크기 (문자)',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:28:33.4552+09'),
	 ('chunking','default_overlap','100','int','기본 오버랩 크기 (문자)',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:28:33.4552+09'),
	 ('openai','api_key','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','string','OpenAI API Key',true,'2025-11-29 21:28:33.4552+09','2025-11-29 21:34:18.252249+09'),
	 ('openai','organization_id','','string','OpenAI Organization ID (선택)',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:34:18.293148+09'),
	 ('embedding','model','text-embedding-3-small','string','임베딩 모델명',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:35:10.392819+09'),
	 ('embedding','dimension','1536','int','벡터 차원 수',false,'2025-11-29 21:28:33.4552+09','2025-11-29 21:35:10.435874+09'),
	 ('rag','top_k','5','int','검색 문서 수',false,'2025-11-29 21:28:33.4552+09','2025-11-29 23:26:26.109965+09');
INSERT INTO public.app_settings (category,"key",value,value_type,description,is_secret,created_at,updated_at) VALUES
	 ('rag','similarity_threshold','0.3','float','유사도 임계값 (0.0-1.0)',false,'2025-11-29 21:28:33.4552+09','2025-11-29 23:26:26.16976+09'),
	 ('rag','max_context_length','4000','int','최대 컨텍스트 길이',false,'2025-11-29 21:28:33.4552+09','2025-11-29 23:26:26.203655+09'),
	 ('llm','model','gpt-4.1-nano','string','LLM 모델명',false,'2025-11-29 21:28:33.4552+09','2025-12-30 10:12:40.291284+09'),
	 ('llm','temperature','0.6','float','생성 온도 (0.0-2.0)',false,'2025-11-29 21:28:33.4552+09','2025-12-30 10:12:40.312987+09'),
	 ('llm','max_tokens','2000','int','최대 토큰 수',false,'2025-11-29 21:28:33.4552+09','2025-12-30 10:12:40.332046+09'),
	 ('agent','max_iterations','10','int','최대 반복 횟수 (1-20)',false,'2026-01-04 22:33:09.921925+09','2026-01-04 22:33:09.921925+09'),
	 ('agent','timeout_seconds','60','int','전체 타임아웃 (초, 10-300)',false,'2026-01-04 22:33:09.967964+09','2026-01-04 22:33:09.967964+09'),
	 ('agent','enable_memory','true','bool','대화 메모리 활성화',false,'2026-01-04 22:33:10.010695+09','2026-01-04 22:33:10.010695+09'),
	 ('agent','enabled_tools','query_database,search_documents,calculate','string','사용 가능한 도구 (쉼표 구분)',false,'2026-01-04 22:33:10.050835+09','2026-01-04 22:33:10.050835+09'),
	 ('embedding','provider','openai','string','임베딩 제공자 (현재 openai만 지원)',false,'2026-01-07 10:37:38.861841+09','2026-01-07 10:37:38.861841+09');
INSERT INTO public.app_settings (category,"key",value,value_type,description,is_secret,created_at,updated_at) VALUES
	 ('anthropic','api_key','','string','Anthropic API Key (Phase 2)',true,'2026-01-07 11:20:44.64738+09','2026-01-07 11:20:44.64738+09'),
	 ('llm','provider','openai','string','LLM 제공자 (openai, anthropic)',false,'2026-01-07 10:37:38.861841+09','2026-01-07 10:37:38.861841+09'),
	 ('agent','llm_provider','openai','string','Agent용 LLM 제공자 (openai, anthropic)',false,'2026-01-07 10:37:38.861841+09','2026-01-07 10:37:38.861841+09');


INSERT INTO public.code_master (code_group,code_value,code_name,description,metadata,sort_order,is_active,is_system,created_at,updated_at) VALUES
	 ('LLM_PROVIDER','openai','OpenAI','OpenAI LLM 제공자','{"pricing_link": "https://platform.openai.com/docs/pricing", "default_model": "gpt-4o"}',1,true,true,'2026-01-07 14:36:19.101636+09','2026-01-07 14:36:19.101636+09'),
	 ('LLM_PROVIDER','anthropic','Anthropic (Claude)','Anthropic Claude LLM 제공자','{"pricing_link": "https://www.anthropic.com/pricing#anthropic-api", "default_model": "claude-3-5-sonnet-20241022"}',2,true,true,'2026-01-07 14:36:19.101636+09','2026-01-07 14:36:19.101636+09'),
	 ('LLM_MODEL_OPENAI','gpt-4o','GPT-4o','OpenAI GPT-4o 모델 (최신, 권장)',NULL,1,true,true,'2026-01-07 14:36:34.901102+09','2026-01-07 14:36:34.901102+09'),
	 ('LLM_MODEL_OPENAI','gpt-4-turbo-preview','GPT-4 Turbo Preview','OpenAI GPT-4 Turbo Preview 모델',NULL,2,true,true,'2026-01-07 14:36:34.901102+09','2026-01-07 14:36:34.901102+09'),
	 ('LLM_MODEL_OPENAI','gpt-4','GPT-4','OpenAI GPT-4 모델',NULL,3,true,true,'2026-01-07 14:36:34.901102+09','2026-01-07 14:36:34.901102+09'),
	 ('LLM_MODEL_OPENAI','gpt-3.5-turbo','GPT-3.5 Turbo','OpenAI GPT-3.5 Turbo 모델',NULL,4,true,true,'2026-01-07 14:36:34.901102+09','2026-01-07 14:36:34.901102+09'),
	 ('LLM_MODEL_ANTHROPIC','claude-3-5-sonnet-20241022','Claude 3.5 Sonnet','Anthropic Claude 3.5 Sonnet 모델 (최신, 권장)',NULL,1,true,true,'2026-01-07 14:36:41.760248+09','2026-01-07 14:36:41.760248+09'),
	 ('LLM_MODEL_ANTHROPIC','claude-3-opus-20240229','Claude 3 Opus','Anthropic Claude 3 Opus 모델 (고성능)',NULL,2,true,true,'2026-01-07 14:36:41.760248+09','2026-01-07 14:36:41.760248+09'),
	 ('LLM_MODEL_ANTHROPIC','claude-3-sonnet-20240229','Claude 3 Sonnet','Anthropic Claude 3 Sonnet 모델',NULL,3,true,true,'2026-01-07 14:36:41.760248+09','2026-01-07 14:36:41.760248+09'),
	 ('EMBEDDING_MODEL','text-embedding-3-small','Text Embedding 3 Small (권장)','OpenAI Text Embedding 3 Small 모델','{"provider": "openai", "dimension": 1536}',1,true,true,'2026-01-07 14:36:50.956807+09','2026-01-07 14:36:50.956807+09');
INSERT INTO public.code_master (code_group,code_value,code_name,description,metadata,sort_order,is_active,is_system,created_at,updated_at) VALUES
	 ('EMBEDDING_MODEL','text-embedding-3-large','Text Embedding 3 Large','OpenAI Text Embedding 3 Large 모델 (고성능, 고비용)','{"provider": "openai", "dimension": 3072}',2,true,true,'2026-01-07 14:36:50.956807+09','2026-01-07 14:36:50.956807+09'),
	 ('EMBEDDING_MODEL','text-embedding-ada-002','Text Embedding Ada-002 (레거시)','OpenAI Text Embedding Ada-002 모델 (이전 버전)','{"provider": "openai", "dimension": 1536}',3,true,true,'2026-01-07 14:36:50.956807+09','2026-01-07 14:36:50.956807+09');
