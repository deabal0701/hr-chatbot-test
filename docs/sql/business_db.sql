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




-- =========================
-- employee (사원 정보)
-- =========================

COMMENT ON TABLE public.employee IS '사원 기본 정보 테이블';

COMMENT ON COLUMN public.employee.emp_id IS '사원 ID (PK)';
COMMENT ON COLUMN public.employee.emp_no IS '사원 번호 (유니크)';
COMMENT ON COLUMN public.employee."name" IS '사원명';
COMMENT ON COLUMN public.employee.name_en IS '사원 영문명';
COMMENT ON COLUMN public.employee.gender IS '성별';
COMMENT ON COLUMN public.employee.birth_date IS '생년월일';
COMMENT ON COLUMN public.employee.hire_date IS '입사일';
COMMENT ON COLUMN public.employee."position" IS '직급 / 직위';
COMMENT ON COLUMN public.employee.job_family IS '직무 그룹';
COMMENT ON COLUMN public.employee.department_id IS '소속 부서 ID';
COMMENT ON COLUMN public.employee.work_location IS '근무지';
COMMENT ON COLUMN public.employee.employment_type IS '고용 형태 (정규직/계약직 등)';
COMMENT ON COLUMN public.employee.status IS '재직 상태 (active, resigned 등)';
COMMENT ON COLUMN public.employee.resignation_date IS '퇴사일';
COMMENT ON COLUMN public.employee.email IS '이메일 주소';
COMMENT ON COLUMN public.employee.phone IS '연락처';
COMMENT ON COLUMN public.employee.created_at IS '생성 일시';
COMMENT ON COLUMN public.employee.updated_at IS '수정 일시';


-- =========================
-- department (부서 정보)
-- =========================

COMMENT ON TABLE public.department IS '부서 정보 테이블';

COMMENT ON COLUMN public.department.dept_id IS '부서 ID (PK)';
COMMENT ON COLUMN public.department.dept_name IS '부서명';
COMMENT ON COLUMN public.department.dept_code IS '부서 코드 (유니크)';
COMMENT ON COLUMN public.department.parent_dept_id IS '상위 부서 ID';
COMMENT ON COLUMN public.department.region IS '부서 지역';
COMMENT ON COLUMN public.department.created_at IS '생성 일시';
COMMENT ON COLUMN public.department.updated_at IS '수정 일시';


-- =========================
-- job_history (인사 이동 이력)
-- =========================

COMMENT ON TABLE public.job_history IS '사원 인사 이동 및 직무 이력 테이블';

COMMENT ON COLUMN public.job_history.id IS '이력 ID (PK)';
COMMENT ON COLUMN public.job_history.emp_id IS '사원 ID';
COMMENT ON COLUMN public.job_history.from_date IS '시작 일자';
COMMENT ON COLUMN public.job_history.to_date IS '종료 일자';
COMMENT ON COLUMN public.job_history.department_id IS '부서 ID';
COMMENT ON COLUMN public.job_history."position" IS '직급 / 직위';
COMMENT ON COLUMN public.job_history.job_family IS '직무 그룹';
COMMENT ON COLUMN public.job_history.work_location IS '근무지';
COMMENT ON COLUMN public.job_history.change_reason IS '변경 사유';
COMMENT ON COLUMN public.job_history.created_at IS '생성 일시';


-- =========================
-- performance_review (성과 평가)
-- =========================

COMMENT ON TABLE public.performance_review IS '사원 성과 평가 테이블';

COMMENT ON COLUMN public.performance_review.id IS '성과 평가 ID (PK)';
COMMENT ON COLUMN public.performance_review.emp_id IS '평가 대상 사원 ID';
COMMENT ON COLUMN public.performance_review.review_period IS '평가 기간 (예: 2024-H1)';
COMMENT ON COLUMN public.performance_review.reviewer_id IS '평가자 사원 ID';
COMMENT ON COLUMN public.performance_review.rating IS '평가 등급';
COMMENT ON COLUMN public.performance_review."comments" IS '평가 의견';
COMMENT ON COLUMN public.performance_review.created_at IS '생성 일시';


-- =========================
-- salary (급여 정보)
-- =========================

COMMENT ON TABLE public.salary IS '사원 급여 정보 테이블';

COMMENT ON COLUMN public.salary.id IS '급여 ID (PK)';
COMMENT ON COLUMN public.salary.emp_id IS '사원 ID';
COMMENT ON COLUMN public.salary.effective_date IS '급여 적용 일자';
COMMENT ON COLUMN public.salary.base_salary IS '기본 급여';
COMMENT ON COLUMN public.salary.currency IS '통화 코드 (기본: KRW)';
COMMENT ON COLUMN public.salary.created_at IS '생성 일시';


-- =========================================
-- Test Data Insertion Order:
-- 1. department (기준 테이블)
-- 2. employee (department_id 참조)
-- 3. job_history, salary, performance_review (emp_id 참조)
-- =========================================

-- =========================================
-- 1. Department data (must be inserted first)
-- =========================================
INSERT INTO department (dept_name,dept_code,parent_dept_id,region,created_at,updated_at) VALUES
	 ('경영지원본부','MGMT',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('인사팀','HR',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('재무팀','FIN',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('기술본부','TECH',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('개발1팀','DEV1',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('개발2팀','DEV2',NULL,'판교','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('마케팅본부','MKT',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('영업본부','SALES',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('데이터팀','DATA',NULL,'서울','2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');


-- =========================================
-- 2. Employee data (references department_id)
-- =========================================
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00001','직원1',NULL,'남','1980-12-20','2023-09-24','과장','마케팅',5,'판교','계약직','active',NULL,'emp1@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00002','직원2',NULL,'남','1995-10-14','2022-01-14','과장','마케팅',6,'부산','계약직','active',NULL,'emp2@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00003','직원3',NULL,'여','1991-09-04','2023-12-27','과장','마케팅',7,'서울','정규직','active',NULL,'emp3@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00006','직원6',NULL,'여','1981-11-25','2023-03-29','부장','마케팅',4,'서울','계약직','active',NULL,'emp6@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00007','직원7',NULL,'여','1997-12-14','2023-04-25','과장','개발',8,'서울','계약직','active',NULL,'emp7@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00009','직원9',NULL,'여','1991-05-07','2022-06-04','대리','디자인',5,'서울','계약직','active',NULL,'emp9@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00010','직원10',NULL,'남','1996-04-21','2022-03-24','차장','마케팅',6,'판교','정규직','active',NULL,'emp10@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00011','직원11',NULL,'여','1981-08-31','2020-04-21','대리','디자인',3,'서울','정규직','active',NULL,'emp11@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00012','직원12',NULL,'여','1990-03-27','2022-05-30','사원','HR',7,'판교','계약직','active',NULL,'emp12@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00013','직원13',NULL,'여','1999-12-10','2022-08-22','대리','디자인',6,'부산','계약직','active',NULL,'emp13@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00014','직원14',NULL,'남','1988-07-05','2023-02-07','대리','기획',2,'서울','정규직','active',NULL,'emp14@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00015','직원15',NULL,'남','1997-12-06','2020-11-22','과장','영업',2,'판교','정규직','active',NULL,'emp15@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00016','직원16',NULL,'남','1984-09-13','2023-04-25','차장','디자인',9,'서울','정규직','active',NULL,'emp16@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00017','직원17',NULL,'여','1997-10-22','2021-09-27','부장','영업',4,'서울','계약직','active',NULL,'emp17@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00018','직원18',NULL,'남','1986-07-27','2020-03-18','대리','개발',5,'판교','계약직','active',NULL,'emp18@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00019','직원19',NULL,'남','1991-10-08','2021-11-09','사원','마케팅',6,'판교','정규직','active',NULL,'emp19@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00020','직원20',NULL,'여','1984-02-02','2020-02-08','차장','개발',7,'부산','계약직','active',NULL,'emp20@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00022','직원22',NULL,'남','1980-02-03','2023-11-08','과장','HR',7,'서울','계약직','active',NULL,'emp22@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00024','직원24',NULL,'남','1984-01-06','2020-07-28','대리','기획',1,'부산','계약직','active',NULL,'emp24@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00025','직원25',NULL,'남','1992-05-23','2020-11-26','부장','개발',2,'판교','계약직','active',NULL,'emp25@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00026','직원26',NULL,'남','1995-06-21','2021-04-06','차장','HR',5,'서울','계약직','active',NULL,'emp26@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00027','직원27',NULL,'여','1998-07-18','2023-12-26','대리','HR',8,'부산','정규직','active',NULL,'emp27@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00028','직원28',NULL,'여','1987-12-05','2023-09-17','부장','개발',8,'판교','정규직','active',NULL,'emp28@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00029','직원29',NULL,'여','1982-05-27','2021-01-09','과장','개발',8,'부산','계약직','active',NULL,'emp29@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00030','직원30',NULL,'여','1994-05-25','2023-07-27','과장','기획',1,'서울','계약직','active',NULL,'emp30@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00031','직원31',NULL,'여','1998-06-30','2021-01-08','차장','마케팅',7,'부산','정규직','active',NULL,'emp31@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00032','직원32',NULL,'남','1980-07-14','2022-03-10','사원','영업',4,'부산','정규직','active',NULL,'emp32@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00033','직원33',NULL,'남','1998-09-06','2020-07-30','대리','HR',4,'판교','계약직','active',NULL,'emp33@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00034','직원34',NULL,'남','1997-05-16','2021-09-08','과장','HR',7,'판교','계약직','active',NULL,'emp34@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00035','직원35',NULL,'남','1991-05-20','2021-06-26','부장','HR',6,'부산','계약직','active',NULL,'emp35@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00037','직원37',NULL,'여','1987-08-07','2022-12-18','사원','디자인',6,'판교','정규직','active',NULL,'emp37@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00038','직원38',NULL,'남','1999-07-20','2023-10-16','과장','마케팅',4,'부산','계약직','active',NULL,'emp38@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00039','직원39',NULL,'여','1997-04-21','2021-06-01','과장','마케팅',4,'판교','계약직','active',NULL,'emp39@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00040','직원40',NULL,'여','1994-09-04','2022-11-12','과장','마케팅',5,'판교','정규직','active',NULL,'emp40@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00041','직원41',NULL,'남','1986-08-21','2020-08-13','과장','디자인',9,'부산','계약직','active',NULL,'emp41@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00042','직원42',NULL,'여','1980-01-30','2021-09-18','부장','기획',3,'부산','정규직','active',NULL,'emp42@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00043','직원43',NULL,'남','1994-09-22','2023-05-07','대리','HR',8,'서울','계약직','active',NULL,'emp43@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00044','직원44',NULL,'남','1991-01-18','2022-05-15','사원','기획',4,'서울','계약직','active',NULL,'emp44@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00045','직원45',NULL,'남','1989-10-05','2021-12-28','대리','디자인',3,'서울','계약직','active',NULL,'emp45@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00046','직원46',NULL,'남','1989-09-25','2020-11-23','사원','기획',8,'부산','계약직','active',NULL,'emp46@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00005','직원5',NULL,'여','1995-07-13','2024-05-17','사원','영업',8,'부산','정규직','active',NULL,'emp5@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00008','직원8',NULL,'남','1992-02-11','2024-12-29','사원','마케팅',2,'부산','정규직','active',NULL,'emp8@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00021','직원21',NULL,'남','1990-03-13','2024-04-25','과장','개발',3,'서울','정규직','active',NULL,'emp21@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00023','직원23',NULL,'여','1981-11-17','2024-03-22','과장','영업',3,'판교','계약직','active',NULL,'emp23@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00036','직원36',NULL,'남','1986-12-20','2024-02-24','사원','영업',8,'판교','계약직','active',NULL,'emp36@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00047','직원47',NULL,'남','1981-03-05','2020-01-26','사원','마케팅',9,'서울','정규직','active',NULL,'emp47@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00048','직원48',NULL,'여','1991-08-17','2023-01-06','부장','개발',1,'서울','정규직','active',NULL,'emp48@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00049','직원49',NULL,'남','1988-10-12','2023-06-07','대리','영업',9,'서울','정규직','active',NULL,'emp49@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00050','직원50',NULL,'여','1994-06-29','2022-03-22','대리','개발',8,'서울','계약직','active',NULL,'emp50@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00051','직원51',NULL,'여','1998-01-01','2022-10-25','사원','기획',4,'판교','계약직','active',NULL,'emp51@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00052','직원52',NULL,'남','1984-01-14','2023-08-10','과장','HR',5,'부산','정규직','active',NULL,'emp52@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00053','직원53',NULL,'남','1994-07-10','2020-10-13','부장','영업',8,'판교','계약직','active',NULL,'emp53@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00054','직원54',NULL,'남','1999-03-24','2020-01-29','부장','마케팅',2,'부산','정규직','active',NULL,'emp54@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00055','직원55',NULL,'여','1988-07-10','2023-05-20','부장','영업',7,'부산','정규직','active',NULL,'emp55@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00056','직원56',NULL,'여','1996-01-28','2020-10-08','과장','HR',8,'서울','정규직','active',NULL,'emp56@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00057','직원57',NULL,'여','1989-06-01','2021-12-14','사원','기획',8,'서울','정규직','active',NULL,'emp57@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00058','직원58',NULL,'남','1988-02-29','2020-11-18','사원','디자인',6,'판교','정규직','active',NULL,'emp58@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00059','직원59',NULL,'여','1998-06-18','2023-07-18','부장','개발',2,'부산','정규직','active',NULL,'emp59@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00060','직원60',NULL,'남','1996-09-06','2023-03-31','부장','영업',2,'부산','정규직','active',NULL,'emp60@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00061','직원61',NULL,'여','1990-02-05','2023-08-05','부장','개발',2,'판교','정규직','active',NULL,'emp61@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00062','직원62',NULL,'남','1997-03-14','2023-05-05','사원','영업',1,'서울','정규직','active',NULL,'emp62@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00063','직원63',NULL,'남','1982-02-24','2021-09-26','과장','디자인',8,'서울','정규직','active',NULL,'emp63@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00064','직원64',NULL,'여','1983-06-02','2022-09-16','대리','기획',6,'부산','정규직','active',NULL,'emp64@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00066','직원66',NULL,'여','1991-06-12','2021-12-19','과장','영업',5,'판교','정규직','active',NULL,'emp66@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00068','직원68',NULL,'남','1987-12-06','2022-03-17','과장','HR',8,'판교','계약직','active',NULL,'emp68@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00069','직원69',NULL,'여','1983-07-17','2021-07-31','사원','기획',8,'부산','계약직','active',NULL,'emp69@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00070','직원70',NULL,'여','1997-12-06','2022-09-20','과장','영업',1,'판교','계약직','active',NULL,'emp70@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00071','직원71',NULL,'여','1985-03-16','2022-12-30','차장','마케팅',1,'판교','정규직','active',NULL,'emp71@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00072','직원72',NULL,'여','1983-12-21','2022-03-31','대리','HR',5,'서울','계약직','active',NULL,'emp72@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00073','직원73',NULL,'여','1981-06-11','2021-01-30','차장','기획',6,'판교','계약직','active',NULL,'emp73@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00074','직원74',NULL,'남','1983-12-06','2022-06-30','대리','마케팅',4,'서울','정규직','active',NULL,'emp74@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00075','직원75',NULL,'여','1983-06-03','2022-10-15','부장','기획',5,'판교','정규직','active',NULL,'emp75@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00076','직원76',NULL,'여','1993-05-20','2020-01-13','과장','기획',9,'서울','정규직','active',NULL,'emp76@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00077','직원77',NULL,'남','1991-05-18','2021-05-19','대리','마케팅',1,'판교','정규직','active',NULL,'emp77@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00078','직원78',NULL,'남','1990-12-13','2021-07-10','과장','디자인',5,'판교','정규직','active',NULL,'emp78@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00079','직원79',NULL,'여','1981-03-24','2021-10-26','과장','기획',8,'판교','계약직','active',NULL,'emp79@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00080','직원80',NULL,'남','1995-10-16','2021-01-23','과장','디자인',1,'판교','계약직','active',NULL,'emp80@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00081','직원81',NULL,'남','1991-03-29','2023-10-07','차장','마케팅',4,'서울','계약직','active',NULL,'emp81@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00082','직원82',NULL,'남','1982-07-20','2021-09-01','대리','HR',6,'판교','계약직','active',NULL,'emp82@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00083','직원83',NULL,'남','1984-09-26','2020-07-02','대리','기획',6,'판교','계약직','active',NULL,'emp83@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00084','직원84',NULL,'여','1991-10-30','2023-05-08','차장','디자인',7,'서울','계약직','active',NULL,'emp84@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00085','직원85',NULL,'남','1993-03-18','2022-08-17','사원','마케팅',3,'부산','정규직','active',NULL,'emp85@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00086','직원86',NULL,'여','1992-07-25','2022-07-13','대리','기획',1,'판교','정규직','active',NULL,'emp86@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00087','직원87',NULL,'여','1984-01-21','2021-09-05','차장','기획',1,'판교','정규직','active',NULL,'emp87@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00088','직원88',NULL,'여','1986-10-01','2020-07-20','사원','HR',4,'판교','정규직','active',NULL,'emp88@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00089','직원89',NULL,'남','1983-10-28','2021-08-18','차장','HR',5,'부산','계약직','active',NULL,'emp89@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00090','직원90',NULL,'남','1985-07-25','2022-09-02','부장','마케팅',2,'판교','계약직','active',NULL,'emp90@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00091','직원91',NULL,'여','1988-09-14','2020-12-22','대리','디자인',4,'판교','정규직','active',NULL,'emp91@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00092','직원92',NULL,'남','1982-05-27','2023-08-19','부장','마케팅',8,'서울','계약직','active',NULL,'emp92@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00093','직원93',NULL,'남','1988-04-02','2021-10-20','차장','마케팅',2,'판교','정규직','active',NULL,'emp93@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');
INSERT INTO employee (emp_no,"name",name_en,gender,birth_date,hire_date,"position",job_family,department_id,work_location,employment_type,status,resignation_date,email,phone,created_at,updated_at) VALUES
	 ('EMP00094','직원94',NULL,'남','1999-10-26','2021-06-13','부장','기획',3,'판교','정규직','active',NULL,'emp94@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00067','직원67',NULL,'여','1995-09-10','2025-01-02','사원','디자인',4,'부산','계약직','active',NULL,'emp67@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00095','직원95',NULL,'남','1987-11-26','2021-01-09','사원','HR',3,'서울','정규직','active',NULL,'emp95@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00096','직원96',NULL,'남','1998-08-24','2020-01-21','차장','영업',3,'부산','정규직','active',NULL,'emp96@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00097','직원97',NULL,'남','1999-04-09','2022-03-01','차장','개발',4,'판교','정규직','active',NULL,'emp97@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00098','직원98',NULL,'남','1996-11-18','2022-04-13','대리','기획',6,'판교','정규직','active',NULL,'emp98@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00099','직원99',NULL,'남','1990-09-27','2022-11-26','과장','마케팅',8,'서울','정규직','active',NULL,'emp99@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00100','직원100',NULL,'여','1997-06-24','2020-01-28','차장','영업',6,'판교','정규직','active',NULL,'emp100@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00004','직원4',NULL,'여','1991-03-22','2024-04-09','사원','기획',5,'판교','정규직','active',NULL,'emp4@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09'),
	 ('EMP00065','직원65',NULL,'여','1981-09-02','2024-04-27','대리','영업',4,'판교','계약직','active',NULL,'emp65@company.com',NULL,'2025-11-29 16:19:33.190168+09','2025-11-29 16:19:33.190168+09');


-- =========================================
-- 3. Related tables data (references emp_id)
-- =========================================

-- =========================================
-- Test Data for job_history table
-- =========================================
-- 직원들의 이력 변경 기록 (승진, 부서이동, 위치변경 등)

INSERT INTO job_history (emp_id, from_date, to_date, department_id, position, job_family, work_location, change_reason, created_at) VALUES
	-- 직원1의 이력 (사원 -> 대리 -> 과장)
	(1, '2023-09-24', '2024-03-31', 5, '사원', '마케팅', '판교', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(1, '2024-04-01', '2024-12-31', 5, '대리', '마케팅', '판교', '승진', '2025-11-29 16:19:33.190168+09'),
	(1, '2025-01-01', NULL, 5, '과장', '마케팅', '판교', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원3의 이력 (부서이동 + 승진)
	(3, '2023-12-27', '2024-06-30', 6, '사원', '마케팅', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(3, '2024-07-01', '2024-12-31', 7, '대리', '마케팅', '서울', '부서이동 및 승진', '2025-11-29 16:19:33.190168+09'),
	(3, '2025-01-01', NULL, 7, '과장', '마케팅', '서울', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원6의 이력 (차장 -> 부장)
	(6, '2023-03-29', '2024-09-30', 4, '차장', '마케팅', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(6, '2024-10-01', NULL, 4, '부장', '마케팅', '서울', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원7의 이력 (위치변경)
	(7, '2023-04-25', '2024-08-31', 8, '사원', '개발', '판교', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(7, '2024-09-01', NULL, 8, '과장', '개발', '서울', '승진 및 근무지 변경', '2025-11-29 16:19:33.190168+09');

INSERT INTO job_history (emp_id, from_date, to_date, department_id, position, job_family, work_location, change_reason, created_at) VALUES
	-- 직원11의 이력 (장기 근속자)
	(11, '2020-04-21', '2021-04-20', 3, '사원', '디자인', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(11, '2021-04-21', '2023-04-20', 3, '대리', '디자인', '서울', '1년 근속 승진', '2025-11-29 16:19:33.190168+09'),
	(11, '2023-04-21', NULL, 3, '대리', '디자인', '서울', '2년 근속', '2025-11-29 16:19:33.190168+09'),

	-- 직원15의 이력 (부서이동)
	(15, '2020-11-22', '2022-12-31', 8, '대리', '영업', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(15, '2023-01-01', '2024-06-30', 2, '대리', '영업', '판교', '부서이동 및 근무지 변경', '2025-11-29 16:19:33.190168+09'),
	(15, '2024-07-01', NULL, 2, '과장', '영업', '판교', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원20의 이력 (개발팀 차장)
	(20, '2020-02-08', '2022-01-31', 7, '대리', '개발', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(20, '2022-02-01', '2023-12-31', 7, '과장', '개발', '부산', '승진 및 지역 발령', '2025-11-29 16:19:33.190168+09'),
	(20, '2024-01-01', NULL, 7, '차장', '개발', '부산', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원25의 이력 (빠른 승진)
	(25, '2020-11-26', '2022-05-31', 2, '사원', '개발', '판교', '신규입사', '2025-11-29 16:19:33.190168+09');

INSERT INTO job_history (emp_id, from_date, to_date, department_id, position, job_family, work_location, change_reason, created_at) VALUES
	(25, '2022-06-01', '2023-11-30', 2, '대리', '개발', '판교', '우수 성과 특별 승진', '2025-11-29 16:19:33.190168+09'),
	(25, '2023-12-01', '2024-12-31', 2, '과장', '개발', '판교', '승진', '2025-11-29 16:19:33.190168+09'),
	(25, '2025-01-01', NULL, 2, '부장', '개발', '판교', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원28의 이력 (개발부장)
	(28, '2023-09-17', '2024-06-30', 8, '과장', '개발', '서울', '신규입사 (경력)', '2025-11-29 16:19:33.190168+09'),
	(28, '2024-07-01', NULL, 8, '부장', '개발', '판교', '승진 및 근무지 변경', '2025-11-29 16:19:33.190168+09'),

	-- 직원42의 이력 (기획부장)
	(42, '2021-09-18', '2023-03-31', 3, '차장', '기획', '부산', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(42, '2023-04-01', NULL, 3, '부장', '기획', '부산', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원48의 이력 (개발부장)
	(48, '2023-01-06', '2024-03-31', 1, '과장', '개발', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(48, '2024-04-01', NULL, 1, '부장', '개발', '서울', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원55의 이력 (영업부장)
	(55, '2023-05-20', '2024-09-30', 7, '차장', '영업', '부산', '신규입사', '2025-11-29 16:19:33.190168+09');

INSERT INTO job_history (emp_id, from_date, to_date, department_id, position, job_family, work_location, change_reason, created_at) VALUES
	(55, '2024-10-01', NULL, 7, '부장', '영업', '부산', '승진', '2025-11-29 16:19:33.190168+09'),

	-- 직원71의 이력 (마케팅 차장)
	(71, '2022-12-30', '2024-06-30', 1, '과장', '마케팅', '서울', '신규입사', '2025-11-29 16:19:33.190168+09'),
	(71, '2024-07-01', NULL, 1, '차장', '마케팅', '판교', '승진 및 근무지 변경', '2025-11-29 16:19:33.190168+09');


-- =========================================
-- Test Data for salary table
-- =========================================
-- 직원들의 급여 변경 이력 (신규, 승진 시 인상 등)

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	-- 직원1 급여 (과장급)
	(1, '2023-09-24', 3500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(1, '2024-04-01', 4200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(1, '2025-01-01', 5000000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원2 급여 (과장급)
	(2, '2022-01-14', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(2, '2023-01-01', 4800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(2, '2024-01-01', 5100000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원3 급여 (과장급)
	(3, '2023-12-27', 3500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(3, '2024-07-01', 4000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(3, '2025-01-01', 4800000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원6 급여 (부장급)
	(6, '2023-03-29', 6500000, 'KRW', '2025-11-29 16:19:33.190168+09');

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	(6, '2024-10-01', 8000000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원7 급여 (과장급)
	(7, '2023-04-25', 3500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(7, '2024-09-01', 4800000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원9 급여 (대리급)
	(9, '2022-06-04', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(9, '2023-06-01', 4100000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(9, '2024-06-01', 4400000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원10 급여 (차장급)
	(10, '2022-03-24', 5500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(10, '2023-03-01', 5900000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(10, '2024-03-01', 6300000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원11 급여 (대리급, 장기 근속)
	(11, '2020-04-21', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09');

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	(11, '2021-04-21', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(11, '2022-04-21', 4200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(11, '2023-04-21', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(11, '2024-04-21', 4800000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원15 급여 (과장급)
	(15, '2020-11-22', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(15, '2022-01-01', 4200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(15, '2023-01-01', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(15, '2024-07-01', 5200000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원20 급여 (차장급)
	(20, '2020-02-08', 4000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(20, '2022-02-01', 5000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(20, '2023-02-01', 5500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(20, '2024-01-01', 6500000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원25 급여 (부장급, 빠른 승진)
	(25, '2020-11-26', 3500000, 'KRW', '2025-11-29 16:19:33.190168+09');

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	(25, '2022-06-01', 4200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(25, '2023-12-01', 5500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(25, '2025-01-01', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원28 급여 (부장급)
	(28, '2023-09-17', 6000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(28, '2024-07-01', 7800000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원42 급여 (부장급)
	(42, '2021-09-18', 6500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(42, '2022-09-01', 6900000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(42, '2023-04-01', 7800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(42, '2024-04-01', 8200000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원48 급여 (부장급)
	(48, '2023-01-06', 5500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(48, '2024-04-01', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 직원55 급여 (부장급)
	(55, '2023-05-20', 6500000, 'KRW', '2025-11-29 16:19:33.190168+09');

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	(55, '2024-10-01', 8000000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 신입/사원급 급여 (최근 입사자들)
	(5, '2024-05-17', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(8, '2024-12-29', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(21, '2024-04-25', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(23, '2024-03-22', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(36, '2024-02-24', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(67, '2025-01-02', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(4, '2024-04-09', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(65, '2024-04-27', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 중간급 (대리/과장) 급여 샘플
	(12, '2022-05-30', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(13, '2022-08-22', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(14, '2023-02-07', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(16, '2023-04-25', 5800000, 'KRW', '2025-11-29 16:19:33.190168+09');

INSERT INTO salary (emp_id, effective_date, base_salary, currency, created_at) VALUES
	(17, '2021-09-27', 7000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(18, '2020-03-18', 3800000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(19, '2021-11-09', 3200000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(22, '2023-11-08', 4500000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 차장급 급여
	(26, '2021-04-06', 6000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(31, '2021-01-08', 6000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(71, '2022-12-30', 5000000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(71, '2024-07-01', 6500000, 'KRW', '2025-11-29 16:19:33.190168+09'),

	-- 부장급 급여 추가
	(35, '2021-06-26', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(53, '2020-10-13', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(54, '2020-01-29', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(59, '2023-07-18', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(60, '2023-03-31', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09'),
	(61, '2023-08-05', 7500000, 'KRW', '2025-11-29 16:19:33.190168+09');


-- =========================================
-- Test Data for performance_review table
-- =========================================
-- 직원들의 성과 평가 기록 (반기별/연간)

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	-- 직원1 평가 (2024년 상반기, 하반기)
	(1, '2024-H1', 6, 'A', '마케팅 캠페인 성공적 수행. 목표 대비 120% 달성. 팀워크 우수.', '2024-07-15 10:00:00+09'),
	(1, '2024-H2', 6, 'S', '신규 프로젝트 리드. 매출 30% 증가 기여. 승진 추천.', '2025-01-15 10:00:00+09'),

	-- 직원2 평가
	(2, '2023-H1', 6, 'B', '업무 수행 양호. 협업 능력 개선 필요.', '2023-07-15 10:00:00+09'),
	(2, '2023-H2', 6, 'A', '고객 만족도 향상. 프로세스 개선 제안 우수.', '2024-01-15 10:00:00+09'),
	(2, '2024-H1', 6, 'A', '안정적 성과 유지. 신입 멘토링 우수.', '2024-07-15 10:00:00+09'),

	-- 직원3 평가
	(3, '2024-H1', 6, 'A', '데이터 분석 역량 우수. 인사이트 도출 탁월.', '2024-07-15 10:00:00+09'),
	(3, '2024-H2', 6, 'S', '부서 이동 후 빠른 적응. ROI 150% 달성.', '2025-01-15 10:00:00+09'),

	-- 직원7 평가 (개발팀)
	(7, '2024-H1', 28, 'A', '코드 품질 우수. 버그 감소율 40%.', '2024-07-15 10:00:00+09'),
	(7, '2024-H2', 28, 'S', '신기술 도입 주도. 개발 생산성 25% 향상.', '2025-01-15 10:00:00+09'),

	-- 직원9 평가 (디자인팀)
	(9, '2023-H1', NULL, 'B', '기본 업무 충실. 창의성 개선 필요.', '2023-07-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(9, '2023-H2', NULL, 'A', 'UI/UX 개선 프로젝트 주도. 사용자 만족도 상승.', '2024-01-15 10:00:00+09'),
	(9, '2024-H1', NULL, 'A', '디자인 시스템 구축 기여. 일관성 향상.', '2024-07-15 10:00:00+09'),

	-- 직원11 평가 (장기 근속자)
	(11, '2021-H2', NULL, 'B', '성실한 근무 태도. 기술 역량 강화 필요.', '2022-01-15 10:00:00+09'),
	(11, '2022-H1', NULL, 'A', '포트폴리오 다양화. 브랜딩 프로젝트 성공.', '2022-07-15 10:00:00+09'),
	(11, '2022-H2', NULL, 'A', '안정적 성과 유지. 협업 능력 우수.', '2023-01-15 10:00:00+09'),
	(11, '2023-H1', NULL, 'A', '지속적 성장. 후배 양성 기여.', '2023-07-15 10:00:00+09'),
	(11, '2023-H2', NULL, 'B', '업무 부하 과다로 성과 다소 저하.', '2024-01-15 10:00:00+09'),
	(11, '2024-H1', NULL, 'A', '회복 및 개선. 프로젝트 일정 준수.', '2024-07-15 10:00:00+09'),

	-- 직원15 평가 (영업팀)
	(15, '2022-H2', NULL, 'A', '분기 목표 110% 달성. 신규 고객 확보.', '2023-01-15 10:00:00+09'),
	(15, '2023-H1', NULL, 'S', '대형 계약 체결. 분기 매출 1위.', '2023-07-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(15, '2023-H2', NULL, 'A', '영업 프로세스 개선. 팀 효율성 향상.', '2024-01-15 10:00:00+09'),
	(15, '2024-H1', NULL, 'S', '부서 이동 후 즉시 성과 창출. 리더십 우수.', '2024-07-15 10:00:00+09'),

	-- 직원20 평가 (개발 차장)
	(20, '2022-H1', 48, 'A', '시스템 안정성 향상. 장애 감소 50%.', '2022-07-15 10:00:00+09'),
	(20, '2022-H2', 48, 'S', '아키텍처 개선 주도. 성능 2배 향상.', '2023-01-15 10:00:00+09'),
	(20, '2023-H1', 48, 'A', '지역 발령 후 팀 안정화. 부산 지사 성과 향상.', '2023-07-15 10:00:00+09'),
	(20, '2023-H2', 48, 'S', '신입 개발자 교육 프로그램 구축. 팀 역량 강화.', '2024-01-15 10:00:00+09'),
	(20, '2024-H1', 48, 'S', '차장 승진 후 리더십 발휘. 프로젝트 완수.', '2024-07-15 10:00:00+09'),

	-- 직원25 평가 (빠른 승진 - 부장)
	(25, '2021-H2', 48, 'A', '신입이지만 뛰어난 기술력. 주요 기능 개발.', '2022-01-15 10:00:00+09'),
	(25, '2022-H1', 48, 'S', '핵심 서비스 아키텍처 설계. 특별 승진 추천.', '2022-07-15 10:00:00+09'),
	(25, '2022-H2', 48, 'S', '대리 승진 후 팀 리드 역할 수행. 프로젝트 성공.', '2023-01-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(25, '2023-H1', 48, 'S', 'AI 기반 신기능 개발. 특허 출원.', '2023-07-15 10:00:00+09'),
	(25, '2023-H2', 48, 'S', '과장 승진. 멀티 프로젝트 동시 관리 능력 탁월.', '2024-01-15 10:00:00+09'),
	(25, '2024-H1', 48, 'S', 'CTO 보좌. 기술 전략 수립 기여.', '2024-07-15 10:00:00+09'),
	(25, '2024-H2', 48, 'S', '부장 승진. 전사 기술 표준 확립. 차기 임원 후보.', '2025-01-15 10:00:00+09'),

	-- 직원28 평가 (개발부장)
	(28, '2024-H1', NULL, 'A', '경력 입사자. 빠른 조직 적응. 기술 리더십 발휘.', '2024-07-15 10:00:00+09'),
	(28, '2024-H2', NULL, 'S', '부장 승진. 개발팀 혁신 주도. 개발 문화 개선.', '2025-01-15 10:00:00+09'),

	-- 직원42 평가 (기획부장)
	(42, '2022-H1', NULL, 'A', '전략 기획 우수. 사업 계획 수립 주도.', '2022-07-15 10:00:00+09'),
	(42, '2022-H2', NULL, 'A', '신사업 발굴. 시장 분석 역량 탁월.', '2023-01-15 10:00:00+09'),
	(42, '2023-H1', NULL, 'S', '부장 승진. 전사 중장기 전략 수립.', '2023-07-15 10:00:00+09'),
	(42, '2023-H2', NULL, 'S', '신규 사업부 런칭 성공. 첫 해 목표 달성.', '2024-01-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(42, '2024-H1', NULL, 'A', '안정적 사업 운영. 수익성 개선.', '2024-07-15 10:00:00+09'),

	-- 직원48 평가 (개발부장)
	(48, '2023-H1', NULL, 'A', '경력 입사. 레거시 시스템 개선 착수.', '2023-07-15 10:00:00+09'),
	(48, '2023-H2', NULL, 'S', '기술 부채 해소. 코드 품질 향상 프로그램 도입.', '2024-01-15 10:00:00+09'),
	(48, '2024-H1', NULL, 'S', '부장 승진. 개발 생산성 30% 향상 달성.', '2024-07-15 10:00:00+09'),
	(48, '2024-H2', NULL, 'S', 'DevOps 문화 정착. CI/CD 파이프라인 구축.', '2025-01-15 10:00:00+09'),

	-- 직원55 평가 (영업부장)
	(55, '2023-H2', NULL, 'A', '지역 영업 총괄. 부산 지역 매출 성장.', '2024-01-15 10:00:00+09'),
	(55, '2024-H1', NULL, 'S', '대형 프로젝트 수주. 연간 목표 조기 달성.', '2024-07-15 10:00:00+09'),
	(55, '2024-H2', NULL, 'S', '부장 승진. 영업본부 전체 성과 향상 기여.', '2025-01-15 10:00:00+09'),

	-- 신입 직원들 평가 (2024년 입사)
	(5, '2024-H2', NULL, 'B', '신입 교육 이수. 기본 업무 습득 중.', '2025-01-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(8, '2024-H2', 6, 'B', '입사 직후. 적응 기간 중. 성실한 태도.', '2025-01-15 10:00:00+09'),
	(21, '2024-H2', 28, 'A', '개발 과장. 즉시 전력화. 코드 리뷰 역량 우수.', '2025-01-15 10:00:00+09'),
	(23, '2024-H2', NULL, 'A', '영업 과장. 기존 고객 관리 탁월.', '2025-01-15 10:00:00+09'),
	(36, '2024-H2', NULL, 'B', '영업 사원. 교육 이수 중. 잠재력 보유.', '2025-01-15 10:00:00+09'),
	(4, '2024-H2', NULL, 'B', '기획 사원. 문서 작성 능력 우수. 분석 역량 개발 중.', '2025-01-15 10:00:00+09'),

	-- 중간급 직원 평가 샘플
	(12, '2023-H1', NULL, 'B', 'HR 사원. 급여 관리 정확성 우수.', '2023-07-15 10:00:00+09'),
	(12, '2023-H2', NULL, 'A', '채용 프로세스 개선 제안. 채용 기간 단축.', '2024-01-15 10:00:00+09'),
	(12, '2024-H1', NULL, 'A', '복리후생 제도 개선 기여. 직원 만족도 상승.', '2024-07-15 10:00:00+09'),

	(13, '2023-H1', NULL, 'A', '디자인 대리. 브랜드 리뉴얼 프로젝트 참여.', '2023-07-15 10:00:00+09');

INSERT INTO performance_review (emp_id, review_period, reviewer_id, rating, comments, created_at) VALUES
	(13, '2023-H2', NULL, 'A', 'UI 컴포넌트 라이브러리 구축. 생산성 향상.', '2024-01-15 10:00:00+09'),
	(13, '2024-H1', NULL, 'S', '디자인 시스템 2.0 주도. 전사 적용 완료.', '2024-07-15 10:00:00+09'),

	(14, '2023-H2', NULL, 'A', '기획 대리. 시장 조사 및 분석 우수.', '2024-01-15 10:00:00+09'),
	(14, '2024-H1', NULL, 'A', '신규 서비스 기획. 론칭 성공.', '2024-07-15 10:00:00+09'),

	-- 저성과자 샘플 (개선 필요 케이스)
	(19, '2022-H1', 6, 'C', '업무 이해도 부족. 기한 미준수 빈번.', '2022-07-15 10:00:00+09'),
	(19, '2022-H2', 6, 'B', '개선 노력 인정. 교육 이수 후 성과 향상.', '2023-01-15 10:00:00+09'),
	(19, '2023-H1', 6, 'B', '안정적 업무 수행. 추가 성장 필요.', '2023-07-15 10:00:00+09'),
	(19, '2023-H2', 6, 'A', '마케팅 캠페인 기여. 데이터 분석 역량 향상.', '2024-01-15 10:00:00+09'),
	(19, '2024-H1', 6, 'A', '지속 성장. 팀워크 우수.', '2024-07-15 10:00:00+09');
