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