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

