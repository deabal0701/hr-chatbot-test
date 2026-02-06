
CREATE TABLE tb_app_settings (
	id int8 DEFAULT nextval('app_settings_id_seq'::regclass) NOT NULL,
	tenant_id varchar(50) NULL,                -- 테넌트 식별자 (NULL = 전역 설정)
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
CREATE INDEX idx_app_settings_category ON public.tb_app_settings USING btree (category);
CREATE INDEX idx_app_settings_tenant ON public.tb_app_settings USING btree (tenant_id);
CREATE INDEX idx_app_settings_tenant_category ON public.tb_app_settings USING btree (tenant_id, category);

COMMENT ON COLUMN public.tb_app_settings.tenant_id IS '테넌트 식별자 (NULL = 전역 설정)';


-- public.tb_code definition

-- Drop table

-- DROP TABLE tb_code;

CREATE TABLE tb_code (
	code_id int8 DEFAULT nextval('code_master_code_id_seq'::regclass) NOT NULL,
	tenant_id varchar(50) NULL,                -- 테넌트 식별자 (NULL = 공통 코드)
	code_group varchar(50) NOT NULL,
	code_value varchar(100) NOT NULL,
	code_name varchar(200) NOT NULL,
	description text NULL,
	metadata jsonb NULL,
	sort_order int4 DEFAULT 0 NULL,
	is_active bool DEFAULT true NULL,
	is_system bool DEFAULT false NULL,
	parent varchar(50) NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz DEFAULT now() NULL,
	CONSTRAINT code_master_code_group_code_value_key UNIQUE (code_group, code_value),
	CONSTRAINT code_master_pkey PRIMARY KEY (code_id)
);
CREATE INDEX idx_code_master_active ON public.tb_code USING btree (is_active);
CREATE INDEX idx_code_master_group ON public.tb_code USING btree (code_group);
CREATE INDEX idx_code_master_group_active ON public.tb_code USING btree (code_group, is_active);
CREATE INDEX idx_code_tenant ON public.tb_code USING btree (tenant_id);
CREATE INDEX idx_code_tenant_group ON public.tb_code USING btree (tenant_id, code_group);

COMMENT ON COLUMN public.tb_code.tenant_id IS '테넌트 식별자 (NULL = 공통 코드)';


-- public.tb_docs definition

-- Drop table

-- DROP TABLE tb_docs;

CREATE TABLE tb_docs (
	id int8 DEFAULT nextval('hr_docs_id_seq'::regclass) NOT NULL,
	tenant_id varchar(50) NULL,                -- 테넌트 식별자 (NULL = 공용 문서)
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
	original_content text NULL,
	usage_type varchar(20) DEFAULT 'rag'::character varying NULL, -- 문서 용도 구분: rag(문서 답변), cortex(SQL 생성)
	context_data text NULL, -- 임베딩 제외 컨텍스트 데이터 (SQL, 스키마 등 Agent 참조용)
	CONSTRAINT hr_docs_pkey PRIMARY KEY (id),
	CONSTRAINT hr_docs_parent_doc_id_fkey FOREIGN KEY (parent_doc_id) REFERENCES tb_docs(id) ON DELETE CASCADE
);
CREATE INDEX idx_hr_docs_content_hash ON public.tb_docs USING btree (content_hash);
CREATE INDEX idx_hr_docs_created_at ON public.tb_docs USING btree (created_at DESC);
CREATE INDEX idx_hr_docs_doc_type ON public.tb_docs USING btree (doc_type);
CREATE INDEX idx_hr_docs_embedding ON public.tb_docs USING ivfflat (embedding) WITH (lists='100');
CREATE INDEX idx_hr_docs_indexed ON public.tb_docs USING btree (indexed);
CREATE INDEX idx_hr_docs_language ON public.tb_docs USING btree (language);
CREATE INDEX idx_hr_docs_metadata ON public.tb_docs USING gin (metadata);
CREATE INDEX idx_hr_docs_parent_doc ON public.tb_docs USING btree (parent_doc_id);
CREATE INDEX idx_hr_docs_source_type ON public.tb_docs USING btree (source_type);
CREATE INDEX idx_tb_docs_usage_doc_type ON public.tb_docs USING btree (usage_type, doc_type);
CREATE INDEX idx_tb_docs_usage_type ON public.tb_docs USING btree (usage_type);
CREATE INDEX idx_docs_tenant ON public.tb_docs USING btree (tenant_id);
CREATE INDEX idx_docs_tenant_type ON public.tb_docs USING btree (tenant_id, doc_type);
CREATE INDEX idx_docs_tenant_usage ON public.tb_docs USING btree (tenant_id, usage_type);

-- Column comments

COMMENT ON COLUMN public.tb_docs.tenant_id IS '테넌트 식별자 (NULL = 공용 문서)';
COMMENT ON COLUMN public.tb_docs.usage_type IS '문서 용도 구분: rag(문서 답변), cortex(SQL 생성)';
COMMENT ON COLUMN public.tb_docs.context_data IS '임베딩 제외 컨텍스트 데이터 (SQL, 스키마 등 Agent 참조용)';


-- public.tb_prompt_history definition

-- Drop table

-- DROP TABLE tb_prompt_history;

CREATE TABLE tb_prompt_history (
	id int4 DEFAULT nextval('prompt_history_id_seq'::regclass) NOT NULL,
	tenant_id varchar(50) NULL,                -- 테넌트 식별자 (NULL = 전역 변경 이력)
	category varchar(50) NOT NULL,
	"key" varchar(100) NOT NULL,
	old_value text NULL, -- 변경 전 값 (NULL이면 최초 생성)
	new_value text NOT NULL, -- 변경 후 값
	changed_by varchar(100) NULL, -- 변경자 정보 (향후 사용자 인증 연동)
	changed_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	change_reason text NULL, -- 변경 사유 (선택)
	CONSTRAINT prompt_history_pkey PRIMARY KEY (id),
	CONSTRAINT fk_prompt_setting FOREIGN KEY (category,"key") REFERENCES tb_app_settings(category,"key") ON DELETE CASCADE
);
CREATE INDEX idx_prompt_history_category_key ON public.tb_prompt_history USING btree (category, key);
CREATE INDEX idx_prompt_history_changed_at ON public.tb_prompt_history USING btree (changed_at DESC);
CREATE INDEX idx_prompt_history_tenant ON public.tb_prompt_history USING btree (tenant_id);
CREATE INDEX idx_prompt_history_tenant_date ON public.tb_prompt_history USING btree (tenant_id, changed_at DESC);
COMMENT ON TABLE public.tb_prompt_history IS '프롬프트 변경 이력 테이블 (원복 기능 지원)';

-- Column comments

COMMENT ON COLUMN public.tb_prompt_history.tenant_id IS '테넌트 식별자 (NULL = 전역 변경 이력)';
COMMENT ON COLUMN public.tb_prompt_history.old_value IS '변경 전 값 (NULL이면 최초 생성)';
COMMENT ON COLUMN public.tb_prompt_history.new_value IS '변경 후 값';
COMMENT ON COLUMN public.tb_prompt_history.changed_by IS '변경자 정보 (향후 사용자 인증 연동)';
COMMENT ON COLUMN public.tb_prompt_history.change_reason IS '변경 사유 (선택)';

