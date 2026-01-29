-- ============================================================================
-- Cortex SQL 컨텍스트 데이터 INSERT (Oracle 뷰 기반)
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
-- 기반: docs/NL2SQL 시스템 프롬프트.md (Oracle 뷰 정의)
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

-- v_ai_employee 뷰 스키마 (핵심 테이블)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_employee 뷰',
    'schema',
    '## v_ai_employee 뷰 (직원 정보 - 핵심)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 직원 고유 ID (다른 뷰와 조인 키)
- EMP_NAME: VARCHAR2 - 직원 이름 (한글)
- EMP_NAME_ENG: VARCHAR2 - 직원 영문 이름
- POSITION: VARCHAR2 - 직위 (사원, 대리, 과장, 차장, 부장, 이사, 전무이사, 사장, 회장)
- BIRTH_DATE: DATE - 생년월일
- DEPARTMENT: VARCHAR2 - 부서명
- CAREER_MONTHS: NUMBER - 총 경력 개월수
- CAREER_YEARS: NUMBER - 총 경력 연수
- DUTY: VARCHAR2 - 현재 직무/담당업무
- DUTY_DATE: DATE - 직무 배치일
- EMP_TYPE: VARCHAR2 - 고용형태 (정규직, 계약직, 인턴 등)
- GENDER: VARCHAR2 - 성별 (남, 여)
- GROUP_JOIN_DATE: DATE - 그룹 입사일
- HIRE_TYPE: VARCHAR2 - 채용유형 (신입, 경력, 입사(신입), 입사(경력))
- HIRE_DATE: DATE (NOT NULL) - 입사일 ★ 입사자 집계 시 사용
- WORK_STATUS: VARCHAR2 - 재직상태 (재직, 퇴직) ★ 재직자 조회 필수
- GRADE: VARCHAR2 - 직급/등급 (직위 아님)
- GRADE_DATE: DATE - 직급/등급 변경일
- RETIRE_REASON: VARCHAR2 - 퇴직 사유
- RETIRE_DATE: DATE - 퇴직일 ★ 퇴사자 집계 시 사용
- SALARY_STEP: VARCHAR2 - 호봉/급여 단계
- SALARY_STEP_DATE: DATE - 호봉 변경일

### 주요 관계
- 모든 뷰는 EMP_ID를 통해 이 뷰와 조인 가능
- 1:N 관계 뷰: v_ai_address, v_ai_career, v_ai_education, v_ai_family, v_ai_language, v_ai_license, v_ai_reward, v_ai_training, v_ai_feedback
- 1:1 관계 뷰: v_ai_military

### 중요 조건
- 재직자 기본 조건: WHERE WORK_STATUS = ''재직''
- 입사 연도: TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''
- 퇴사 연도: TO_CHAR(RETIRE_DATE, ''YYYY'') = ''2024''',
    '{
        "table_name": "v_ai_employee",
        "columns": ["EMP_ID", "EMP_NAME", "EMP_NAME_ENG", "POSITION", "BIRTH_DATE", "DEPARTMENT", "CAREER_MONTHS", "CAREER_YEARS", "DUTY", "DUTY_DATE", "EMP_TYPE", "GENDER", "GROUP_JOIN_DATE", "HIRE_TYPE", "HIRE_DATE", "WORK_STATUS", "GRADE", "GRADE_DATE", "RETIRE_REASON", "RETIRE_DATE", "SALARY_STEP", "SALARY_STEP_DATE"],
        "primary_key": "EMP_ID",
        "db_type": "oracle",
        "view_type": "master",
        "category": "hr",
        "tags": ["employee", "직원", "인사", "HR", "사원", "재직자", "퇴직자"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_address 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_address 뷰',
    'schema',
    '## v_ai_address 뷰 (주소 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- ADDRESS: VARCHAR2 (NOT NULL) - 기본 주소
- ADDRESS_DETAIL: VARCHAR2 (NOT NULL) - 상세 주소
- ZIP_CODE: VARCHAR2 (NOT NULL) - 우편번호
- REGION: CHAR - 거주 시/도 (서울, 경기, 경북 등)
- MOD_DATE: DATE (NOT NULL) - 수정일시

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 특정 지역 거주자 수 (EXISTS 사용)
SELECT COUNT(*) FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_address a
              WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ''서울'')
```',
    '{
        "table_name": "v_ai_address",
        "columns": ["EMP_ID", "ADDRESS", "ADDRESS_DETAIL", "ZIP_CODE", "REGION", "MOD_DATE"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["address", "주소", "거주지", "지역", "시도"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_career 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_career 뷰',
    'schema',
    '## v_ai_career 뷰 (경력 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- PREV_COMPANY: VARCHAR2 - 이전 근무 회사명
- LOCATION: VARCHAR2 - 전직장 소재지
- PREV_POSITION: VARCHAR2 - 전직장 직위
- WORK_MONTHS: NUMBER - 해당 직장 근무 개월 수
- WORK_YEARS: NUMBER - 해당 직장 근무 연수
- RECOGNITION_RATE: NUMBER - 경력 인정 비율 (%)
- LEAVE_REASON: VARCHAR2 - 이직 사유

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 경력직 출신 직원 조회
SELECT e.EMP_NAME, c.PREV_COMPANY, c.WORK_YEARS
FROM v_ai_employee e
JOIN v_ai_career c ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = ''재직''
```',
    '{
        "table_name": "v_ai_career",
        "columns": ["EMP_ID", "PREV_COMPANY", "LOCATION", "PREV_POSITION", "WORK_MONTHS", "WORK_YEARS", "RECOGNITION_RATE", "LEAVE_REASON"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["career", "경력", "이전직장", "전직장", "경력사항"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_education 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_education 뷰',
    'schema',
    '## v_ai_education 뷰 (학력 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- SCHOOL_NAME: VARCHAR2 - 졸업 학교명
- SCHOOL_LOCATION: VARCHAR2 - 학교 소재지
- MAJOR: VARCHAR2 - 전공 학과명
- DOUBLE_MAJOR: VARCHAR2 - 복수전공명
- MINOR: VARCHAR2 - 부전공명
- ADMISSION_DATE: VARCHAR2 - 입학일
- GRADUATION_DATE: VARCHAR2 - 졸업일시
- GRADUATION_YEAR: VARCHAR2 - 졸업 연도 (YYYY)

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 특정 학교 출신 직원
SELECT e.EMP_NAME, ed.SCHOOL_NAME, ed.MAJOR
FROM v_ai_employee e
JOIN v_ai_education ed ON e.EMP_ID = ed.EMP_ID
WHERE ed.SCHOOL_NAME LIKE ''%서울대%''
  AND e.WORK_STATUS = ''재직''
```',
    '{
        "table_name": "v_ai_education",
        "columns": ["EMP_ID", "SCHOOL_NAME", "SCHOOL_LOCATION", "MAJOR", "DOUBLE_MAJOR", "MINOR", "ADMISSION_DATE", "GRADUATION_DATE", "GRADUATION_YEAR"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["education", "학력", "학교", "전공", "졸업"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_family 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_family 뷰',
    'schema',
    '## v_ai_family 뷰 (가족 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- RELATION: VARCHAR2 - 가족 관계 (배우자, 자녀, 부모, 처 등)
- FAMILY_NAME: VARCHAR2 - 가족 구성원 이름
- FAMILY_GENDER: VARCHAR2 - 가족 성별
- FAMILY_BIRTH_DATE: VARCHAR2 - 가족 생년월일
- FAMILY_COMPANY: VARCHAR2 - 가족 근무회사
- FAMILY_POSITION: VARCHAR2 - 가족 직위
- FAMILY_SCHOOL: VARCHAR2 - 가족 출신학교
- DISABILITY_STATUS: VARCHAR2 - 장애 여부 (장애있음, 장애없음)
- DISABILITY_GRADE: VARCHAR2 - 장애등급

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 배우자가 있는 직원 수
SELECT COUNT(DISTINCT e.EMP_ID)
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_family f
              WHERE f.EMP_ID = e.EMP_ID AND f.RELATION IN (''배우자'', ''처'', ''남편''))
```',
    '{
        "table_name": "v_ai_family",
        "columns": ["EMP_ID", "RELATION", "FAMILY_NAME", "FAMILY_GENDER", "FAMILY_BIRTH_DATE", "FAMILY_COMPANY", "FAMILY_POSITION", "FAMILY_SCHOOL", "DISABILITY_STATUS", "DISABILITY_GRADE"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["family", "가족", "배우자", "자녀", "부양가족"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_feedback 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_feedback 뷰',
    'schema',
    '## v_ai_feedback 뷰 (인사평가/성과평가 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원번호
- COMPANY_CD: VARCHAR2 (NOT NULL) - 회사코드
- LOCALE_CD: VARCHAR2 (NOT NULL) - 언어코드
- PEE_DEFINITION_ID: NUMBER (NOT NULL) - 평가정의 ID
- APPR_ID: NUMBER (NOT NULL) - 평가번호
- APPR_NM: VARCHAR2 (NOT NULL) - 평가명 (종합평가, 업적평가, 역량평가 등)
- PEE_TYPE_CD: VARCHAR2 (NOT NULL) - 평가 종류 코드
- PEE_TYPE_NM: VARCHAR2 - 평가 이름
- EMP_ORG_ID: VARCHAR2 - 소속 부서 코드
- EMP_ORG_NM: VARCHAR2 - 소속 부서명
- RATEE_LEVEL_CD: VARCHAR2 (NOT NULL) - 직책 코드
- RATEE_LEVEL_NM: VARCHAR2 - 직책명 (팀장, 팀원(과장/대리) 등)
- EMP_NM: VARCHAR2 (NOT NULL) - 이름
- APPR_SCORE: NUMBER - 평가 점수
- APPR_GRADE: VARCHAR2 - 평가등급 (S, A, B, C, D)
- RK: VARCHAR2 - 순위
- PEE_OPINION: VARCHAR2 - 평가자 의견
- END_YMD: DATE (NOT NULL) - 평가종료일자
- APPR_YMD: DATE (NOT NULL) - 평가일자

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 중요
★ 인사평가, 직원평가, 평가 관련 질의 시 이 테이블 사용

### 사용 패턴
```sql
-- 특정 연도 평가 등급 분포
SELECT APPR_GRADE, COUNT(*) as cnt
FROM v_ai_feedback
WHERE TO_CHAR(END_YMD, ''YYYY'') = ''2024''
GROUP BY APPR_GRADE
ORDER BY APPR_GRADE
```',
    '{
        "table_name": "v_ai_feedback",
        "columns": ["EMP_ID", "COMPANY_CD", "APPR_ID", "APPR_NM", "PEE_TYPE_NM", "EMP_ORG_NM", "RATEE_LEVEL_NM", "EMP_NM", "APPR_SCORE", "APPR_GRADE", "RK", "PEE_OPINION", "END_YMD", "APPR_YMD"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["feedback", "평가", "인사평가", "성과평가", "등급", "점수", "S등급", "A등급"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_language 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_language 뷰',
    'schema',
    '## v_ai_language 뷰 (어학 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- LANGUAGE_TYPE: VARCHAR2 - 어학 종류 (영어, 일본어, 중국어 등)
- EXAM_TYPE: VARCHAR2 - 시험 종류 (TOEIC, TOEFL, JLPT, BCT 등)
- EXAM_INSTITUTION: VARCHAR2 - 시험 기관
- SCORE: NUMBER (NOT NULL) - 어학 시험 점수
- LANGUAGE_GRADE: VARCHAR2 - 어학 등급
- EXAM_DATE: DATE - 시험 응시일
- EXAM_YEAR: VARCHAR2 - 시험 응시 연도 (YYYY)
- EVALUATION_YEAR: VARCHAR2 (NOT NULL) - 평가 연도
- EVALUATION_SEQ: NUMBER (NOT NULL) - 평가 순번

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- TOEIC 800점 이상인 재직자 수
SELECT COUNT(*) FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_language l
              WHERE l.EMP_ID = e.EMP_ID
                AND l.EXAM_TYPE = ''TOEIC''
                AND l.SCORE >= 800)
```',
    '{
        "table_name": "v_ai_language",
        "columns": ["EMP_ID", "LANGUAGE_TYPE", "EXAM_TYPE", "EXAM_INSTITUTION", "SCORE", "LANGUAGE_GRADE", "EXAM_DATE", "EXAM_YEAR", "EVALUATION_YEAR", "EVALUATION_SEQ"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["language", "어학", "TOEIC", "TOEFL", "JLPT", "영어", "일본어", "중국어", "점수"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_license 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_license 뷰',
    'schema',
    '## v_ai_license 뷰 (자격증 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- LICENSE_TYPE: VARCHAR2 - 자격 구분 (국가자격, 민간자격, 사내자격 등)
- LICENSE_NAME: VARCHAR2 - 자격증 이름
- LICENSE_NO: VARCHAR2 - 자격증 번호
- ISSUING_ORG: VARCHAR2 - 발급기관
- ISSUE_DATE: DATE (NOT NULL) - 자격증 취득일
- EXPIRY_DATE: DATE - 자격증 만료일
- VALIDITY_STATUS: VARCHAR2 - 유효 상태 (유효, 만료, 영구)
- ALLOWANCE_TYPE: VARCHAR2 - 수당 유형

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 정보처리기사 보유자 수
SELECT COUNT(*) FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_license l
              WHERE l.EMP_ID = e.EMP_ID
                AND l.LICENSE_NAME LIKE ''%정보처리기사%'')
```',
    '{
        "table_name": "v_ai_license",
        "columns": ["EMP_ID", "LICENSE_TYPE", "LICENSE_NAME", "LICENSE_NO", "ISSUING_ORG", "ISSUE_DATE", "EXPIRY_DATE", "VALIDITY_STATUS", "ALLOWANCE_TYPE"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["license", "자격증", "자격", "국가자격", "기사", "정보처리"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_military 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_military 뷰',
    'schema',
    '## v_ai_military 뷰 (병역 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- MILITARY_TYPE: VARCHAR2 - 군 종류 (육군, 해군, 공군, 해병대, 의무경찰 등)
- MILITARY_BRANCH: VARCHAR2 - 병과 주특기
- MILITARY_RANK: VARCHAR2 - 최종 계급 (병장, 상병, 준장 등)
- SERVICE_TYPE: VARCHAR2 - 복무 유형
- SERVICE_STATUS: VARCHAR2 - 군필 여부 (군필, 미필, 면제 등)
- DISCHARGE_TYPE: VARCHAR2 - 전역 사유
- DISCHARGE_DATE: DATE - 전역일자
- DISCHARGE_YEAR: VARCHAR2 - 전역 연도
- SPECIALTY: VARCHAR2 - 주특기 (보병, 공병 등)
- MILITARY_NO: VARCHAR2 - 군번

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:1)

### 사용 패턴
```sql
-- 육군 출신 직원
SELECT e.EMP_NAME, m.MILITARY_RANK, m.DISCHARGE_DATE
FROM v_ai_employee e
JOIN v_ai_military m ON e.EMP_ID = m.EMP_ID
WHERE m.MILITARY_TYPE = ''육군''
  AND e.WORK_STATUS = ''재직''
```',
    '{
        "table_name": "v_ai_military",
        "columns": ["EMP_ID", "MILITARY_TYPE", "MILITARY_BRANCH", "MILITARY_RANK", "SERVICE_TYPE", "SERVICE_STATUS", "DISCHARGE_TYPE", "DISCHARGE_DATE", "DISCHARGE_YEAR", "SPECIALTY", "MILITARY_NO"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:1",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["military", "병역", "군대", "육군", "해군", "공군", "전역"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_pay_report 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_pay_report 뷰',
    'schema',
    '## v_ai_pay_report 뷰 (급여 정보)

### 컬럼
- EMPLOYEE_ID: NUMBER (NOT NULL) - 사원ID (FK → v_ai_employee.EMP_ID)
- EMPLOYEE_NAME: VARCHAR2 - 성명
- PAY_YEAR: VARCHAR2 (NOT NULL) - 급여년도
- PAY_YEAR_MONTH: VARCHAR2 (NOT NULL) - 급여년월 (YYYYMM)
- PAY_DATE: DATE (NOT NULL) - 급여일
- PAY_DATE_ID: NUMBER (NOT NULL) - 급여일자ID
- PAYMENT_TYPE_NAME: VARCHAR2 - 급여지급구분 (정기급여, 연차수당, 격려금, 상여)
- SALARY_TYPE_NAME: VARCHAR2 - 급여유형 (연봉제, 월급제)
- PAY_GRADE_NAME: VARCHAR2 - 급여직급
- JOB_GRADE_NAME: VARCHAR2 - 직급
- EMPLOYMENT_TYPE: VARCHAR2 - 급여직군
- ORGANIZATION_ID: NUMBER - 소속 ID
- ORGANIZATION_NAME: VARCHAR2 - 소속명
- FIXED_PAY_AMOUNT: NUMBER - 고정비
- VARIABLE_PAY_AMOUNT: NUMBER - 변동비
- GROSS_PAY_AMOUNT: NUMBER - 지급합계
- DEDUCTION_AMOUNT: NUMBER - 공제합계
- TAX_AMOUNT: NUMBER - 세금합계
- TOTAL_DEDUCTION_AMOUNT: NUMBER - 총공제액
- NET_PAY_AMOUNT: NUMBER - 실지급액

### 관계
- v_ai_employee와 EMPLOYEE_ID로 연결 (1:N)
- 주의: 조인 시 EMPLOYEE_ID 사용 (EMP_ID 아님)

### 사용 패턴
```sql
-- 특정 연월 급여 통계
SELECT
    ORGANIZATION_NAME,
    AVG(NET_PAY_AMOUNT) as avg_pay,
    SUM(NET_PAY_AMOUNT) as total_pay
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = ''202401''
GROUP BY ORGANIZATION_NAME
```',
    '{
        "table_name": "v_ai_pay_report",
        "columns": ["EMPLOYEE_ID", "EMPLOYEE_NAME", "PAY_YEAR", "PAY_YEAR_MONTH", "PAY_DATE", "PAYMENT_TYPE_NAME", "SALARY_TYPE_NAME", "ORGANIZATION_NAME", "FIXED_PAY_AMOUNT", "VARIABLE_PAY_AMOUNT", "GROSS_PAY_AMOUNT", "DEDUCTION_AMOUNT", "NET_PAY_AMOUNT"],
        "foreign_keys": {"EMPLOYEE_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["pay", "급여", "연봉", "월급", "실지급액", "보수"],
        "sensitive": true
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_reward 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_reward 뷰',
    'schema',
    '## v_ai_reward 뷰 (포상/징계 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- REWARD_TYPE: VARCHAR2 - 상벌 구분 (포상, 징계)
- REWARD_KIND: VARCHAR2 - 상벌 종류 (우수상, 우수상-혁신 등)
- REWARD_REASON: VARCHAR2 - 사유
- REWARD_CONTENT: VARCHAR2 - 내용
- REWARD_DATE: DATE - 일자
- REWARD_YEAR: VARCHAR2 - 상벌 발생 연도
- AWARDING_ORG: VARCHAR2 - 수여 기관
- REWARD_AMOUNT: NUMBER - 포상금 금액
- REWARD_NO: VARCHAR2 - 포상번호

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 포상 이력이 있는 직원 수
SELECT COUNT(DISTINCT e.EMP_ID)
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_reward r
              WHERE r.EMP_ID = e.EMP_ID AND r.REWARD_TYPE = ''포상'')
```',
    '{
        "table_name": "v_ai_reward",
        "columns": ["EMP_ID", "REWARD_TYPE", "REWARD_KIND", "REWARD_REASON", "REWARD_CONTENT", "REWARD_DATE", "REWARD_YEAR", "AWARDING_ORG", "REWARD_AMOUNT", "REWARD_NO"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["reward", "포상", "징계", "상벌", "우수사원"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- v_ai_training 뷰 스키마
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'v_ai_training 뷰',
    'schema',
    '## v_ai_training 뷰 (교육 이력 정보)

### 컬럼
- EMP_ID: NUMBER (NOT NULL) - 사원 고유 식별 번호 (FK → v_ai_employee)
- TRAINING_YEAR: VARCHAR2 (NOT NULL) - 교육 실시 연도
- COURSE_TYPE: VARCHAR2 - 과정 유형
- COURSE_GRADE: VARCHAR2 - 등급
- COURSE_FIELD: VARCHAR2 - 분야 (공통, 직무 등)
- COURSE_NAME: VARCHAR2 (NOT NULL) - 교육 과정 이름
- INSTITUTION_TYPE: VARCHAR2 - 교육기관 유형
- INSTITUTION_NAME: VARCHAR2 - 교육기관명
- TRAINING_LOCATION: VARCHAR2 - 교육장소 (사외, 사내)
- TRAINING_TYPE: VARCHAR2 - 교육 유형 (필수, 선택)
- START_DATE: DATE (NOT NULL) - 교육시작일자
- END_DATE: DATE (NOT NULL) - 교육종료일자
- TRAINING_COST: NUMBER - 교육비용
- COMPLETION_POINTS: NUMBER - 총이수포인트
- COMPLETION_HOURS: NUMBER - 총 이수 시간
- COMPLETION_STATUS: VARCHAR2 - 수료 여부 (수료, 미수료)
- REFUND_AMOUNT: NUMBER - 환급금액

### 관계
- v_ai_employee와 EMP_ID로 연결 (1:N)

### 사용 패턴
```sql
-- 특정 연도 교육 이수 현황
SELECT e.EMP_NAME, t.COURSE_NAME, t.COMPLETION_HOURS, t.COMPLETION_STATUS
FROM v_ai_employee e
JOIN v_ai_training t ON e.EMP_ID = t.EMP_ID
WHERE t.TRAINING_YEAR = ''2024''
  AND e.WORK_STATUS = ''재직''
```',
    '{
        "table_name": "v_ai_training",
        "columns": ["EMP_ID", "TRAINING_YEAR", "COURSE_TYPE", "COURSE_GRADE", "COURSE_FIELD", "COURSE_NAME", "INSTITUTION_TYPE", "INSTITUTION_NAME", "TRAINING_LOCATION", "TRAINING_TYPE", "START_DATE", "END_DATE", "TRAINING_COST", "COMPLETION_POINTS", "COMPLETION_HOURS", "COMPLETION_STATUS", "REFUND_AMOUNT"],
        "foreign_keys": {"EMP_ID": "v_ai_employee.EMP_ID"},
        "relation": "1:N",
        "db_type": "oracle",
        "category": "hr",
        "tags": ["training", "교육", "연수", "이수", "과정", "수료"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);


-- ============================================================================
-- 2. Few-shot 쿼리 예제 (doc_type: 'query_example')
-- ============================================================================

-- 기본 COUNT 예제 (입사자 수)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 입사자 수는 몇 명인가요?',
    'query_example',
    '연도별 입사자 수를 집계하는 쿼리 예제

```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''
```

**핵심 패턴**:
- 연도 추출: TO_CHAR(HIRE_DATE, ''YYYY'')
- 입사자 집계 시 WORK_STATUS 조건 불필요 (입사 시점 기준)
- HIRE_DATE 컬럼 사용',
    '{
        "intent": "AGGREGATE",
        "complexity": "simple",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT COUNT(*) FROM v_ai_employee WHERE TO_CHAR(HIRE_DATE, ''YYYY'') = ?",
        "category": "aggregate",
        "tags": ["입사", "연도별", "COUNT", "집계", "몇명"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 퇴사자 수 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 퇴사자 수는 몇 명인가요?',
    'query_example',
    '연도별 퇴사자 수를 집계하는 쿼리 예제

```sql
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, ''YYYY'') = ''2024''
```

**핵심 패턴**:
- 퇴직일 연도: TO_CHAR(RETIRE_DATE, ''YYYY'')
- RETIRE_DATE IS NOT NULL 조건 필수
- RETIRE_DATE 컬럼 사용',
    '{
        "intent": "AGGREGATE",
        "complexity": "simple",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT COUNT(*) FROM v_ai_employee WHERE RETIRE_DATE IS NOT NULL AND TO_CHAR(RETIRE_DATE, ''YYYY'') = ?",
        "category": "aggregate",
        "tags": ["퇴사", "퇴직", "연도별", "COUNT", "집계"]
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
SELECT DEPARTMENT, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY DEPARTMENT
ORDER BY emp_count DESC
```

**핵심 패턴**:
- 재직자 기본 조건: WORK_STATUS = ''재직''
- GROUP BY로 부서별 그룹화
- ORDER BY로 직원 수 내림차순 정렬',
    '{
        "intent": "AGGREGATE",
        "complexity": "simple",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT DEPARTMENT, COUNT(*) FROM v_ai_employee WHERE WORK_STATUS = ''재직'' GROUP BY DEPARTMENT ORDER BY 2 DESC",
        "category": "aggregate",
        "tags": ["부서별", "GROUP BY", "집계", "팀별", "조직"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 연도별 입사/퇴사 추이 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2010년부터 2020년까지 입사자/퇴사자 수를 연도별로 보여줘',
    'query_example',
    '연도별 입사/퇴사자 추이를 집계하는 쿼리

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

**핵심 패턴**:
- UNION ALL로 입사/퇴사 데이터 통합
- TO_CHAR(날짜, ''YYYY'') BETWEEN으로 기간 조건
- 추이 분석 시 WORK_STATUS 조건 제외',
    '{
        "intent": "AGGREGATE",
        "complexity": "complex",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT year, SUM(hire_count), SUM(retire_count) FROM (UNION ALL) GROUP BY year ORDER BY year",
        "category": "trend",
        "tags": ["연도별", "추이", "트렌드", "입사", "퇴사", "UNION ALL"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- EXISTS 패턴 예제 (지역 조건)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '경상북도에 사는 직원 수',
    'query_example',
    '1:N 관계 뷰와 조인하여 직원 수 집계 시 EXISTS 사용

```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_address a
              WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ''경북'')
```

**핵심 패턴**:
- 1:N 관계 뷰 조건 시 EXISTS 서브쿼리 사용 (중복 방지)
- JOIN 대신 EXISTS 사용
- 재직자 기본 조건 유지',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_employee", "v_ai_address"],
        "sql_template": "SELECT COUNT(*) FROM v_ai_employee e WHERE e.WORK_STATUS = ''재직'' AND EXISTS (SELECT 1 FROM v_ai_address a WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ?)",
        "category": "filter",
        "tags": ["지역", "거주", "EXISTS", "서브쿼리", "주소"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- EXISTS 패턴 예제 (자격증 조건)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '정보처리기사 자격증 보유자 수',
    'query_example',
    '자격증 보유자 집계 시 EXISTS 사용

```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_license l
              WHERE l.EMP_ID = e.EMP_ID
                AND l.LICENSE_NAME LIKE ''%정보처리기사%'')
```

**핵심 패턴**:
- LIKE ''%키워드%''로 자격증명 검색
- 1:N 관계 뷰에서 중복 방지를 위한 EXISTS
- COUNT(DISTINCT) 대신 EXISTS 권장',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_employee", "v_ai_license"],
        "sql_template": "SELECT COUNT(*) FROM v_ai_employee e WHERE e.WORK_STATUS = ''재직'' AND EXISTS (SELECT 1 FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID AND l.LICENSE_NAME LIKE ?)",
        "category": "filter",
        "tags": ["자격증", "정보처리기사", "EXISTS", "LIKE", "보유자"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- EXISTS 패턴 예제 (어학 점수)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'TOEIC 800점 이상인 직원 수',
    'query_example',
    '어학 점수 조건 집계

```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_language l
              WHERE l.EMP_ID = e.EMP_ID
                AND l.EXAM_TYPE = ''TOEIC''
                AND l.SCORE >= 800)
```

**핵심 패턴**:
- 어학 시험 유형: EXAM_TYPE = ''TOEIC''
- 점수 조건: SCORE >= 800
- EXISTS로 중복 방지',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_employee", "v_ai_language"],
        "sql_template": "SELECT COUNT(*) FROM v_ai_employee e WHERE e.WORK_STATUS = ''재직'' AND EXISTS (SELECT 1 FROM v_ai_language l WHERE l.EMP_ID = e.EMP_ID AND l.EXAM_TYPE = ? AND l.SCORE >= ?)",
        "category": "filter",
        "tags": ["어학", "TOEIC", "점수", "EXISTS", "영어"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 명단 조회 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '서울에 사는 직원 명단',
    'query_example',
    '조건에 맞는 직원 명단 조회

```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_address a
              WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ''서울'')
ORDER BY e.EMP_NAME
```

**핵심 패턴**:
- 명단 조회 시에도 EXISTS 또는 IN 사용
- 필요한 컬럼만 SELECT
- ORDER BY로 정렬',
    '{
        "intent": "SELECT",
        "complexity": "medium",
        "tables": ["v_ai_employee", "v_ai_address"],
        "sql_template": "SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION FROM v_ai_employee e WHERE e.WORK_STATUS = ''재직'' AND EXISTS (...) ORDER BY e.EMP_NAME",
        "category": "list",
        "tags": ["명단", "목록", "리스트", "EXISTS", "직원목록"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 상세 데이터 조회 예제 (JOIN 사용)
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '홍길동의 자격증 목록을 보여줘',
    'query_example',
    '특정 직원의 1:N 상세 데이터 조회

```sql
SELECT e.EMP_NAME, l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE e.EMP_NAME = ''홍길동''
ORDER BY l.ISSUE_DATE DESC
```

**핵심 패턴**:
- 상세 데이터 필요 시에만 JOIN 사용
- 집계가 아닌 개별 데이터 조회
- ORDER BY로 최신순 정렬',
    '{
        "intent": "SELECT",
        "complexity": "simple",
        "tables": ["v_ai_employee", "v_ai_license"],
        "sql_template": "SELECT e.EMP_NAME, l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE FROM v_ai_employee e JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID WHERE e.EMP_NAME = ? ORDER BY l.ISSUE_DATE DESC",
        "category": "detail",
        "tags": ["자격증", "상세", "개별조회", "JOIN", "목록"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 직급별 통계 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '직위별 직원 수를 보여줘',
    'query_example',
    '직위별 그룹화 통계

```sql
SELECT
    POSITION,
    COUNT(*) AS emp_count
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

**핵심 패턴**:
- GROUP BY로 직위별 그룹화
- CASE WHEN으로 커스텀 정렬
- 직위(POSITION) 컬럼 사용 (GRADE와 구분)',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT POSITION, COUNT(*) FROM v_ai_employee WHERE WORK_STATUS = ''재직'' GROUP BY POSITION ORDER BY CASE ...",
        "category": "aggregate",
        "tags": ["직위", "직급", "GROUP BY", "사원", "대리", "과장"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 성별 통계 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '성별 직원 수를 알려줘',
    'query_example',
    '성별 그룹화 통계

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

**핵심 패턴**:
- 성별: GENDER 컬럼 (남, 여)
- 비율 계산: 윈도우 함수 SUM() OVER()
- ROUND로 소수점 처리',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_employee"],
        "sql_template": "SELECT GENDER, COUNT(*), percentage FROM v_ai_employee WHERE WORK_STATUS = ''재직'' GROUP BY GENDER",
        "category": "aggregate",
        "tags": ["성별", "남녀", "비율", "통계", "GROUP BY"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 평가 등급 분포 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 평가 등급 분포를 보여줘',
    'query_example',
    '평가 등급별 분포 집계

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

**핵심 패턴**:
- 평가 정보: v_ai_feedback 테이블 사용
- 평가 연도: TO_CHAR(END_YMD, ''YYYY'')
- 등급 커스텀 정렬: CASE WHEN',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_feedback"],
        "sql_template": "SELECT APPR_GRADE, COUNT(*), percentage FROM v_ai_feedback WHERE TO_CHAR(END_YMD, ''YYYY'') = ? GROUP BY APPR_GRADE ORDER BY CASE ...",
        "category": "distribution",
        "tags": ["평가", "등급", "분포", "S등급", "A등급", "인사평가"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 급여 통계 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '부서별 평균 급여를 알려줘',
    'query_example',
    '부서별 급여 통계 집계

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

**핵심 패턴**:
- 급여 정보: v_ai_pay_report 테이블
- 정기급여만: PAYMENT_TYPE_NAME = ''정기급여''
- 실지급액: NET_PAY_AMOUNT 컬럼',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_pay_report"],
        "sql_template": "SELECT ORGANIZATION_NAME, AVG(NET_PAY_AMOUNT), MIN, MAX FROM v_ai_pay_report WHERE PAY_YEAR = ? GROUP BY ORGANIZATION_NAME",
        "category": "aggregate",
        "tags": ["급여", "평균", "부서별", "AVG", "연봉", "실지급액"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

-- 교육 이력 예제
INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '2024년 교육 이수 현황을 보여줘',
    'query_example',
    '교육 이수 현황 집계

```sql
SELECT
    t.COURSE_NAME,
    COUNT(DISTINCT t.EMP_ID) AS trainee_count,
    SUM(t.COMPLETION_HOURS) AS total_hours
FROM v_ai_training t
JOIN v_ai_employee e ON t.EMP_ID = e.EMP_ID
WHERE t.TRAINING_YEAR = ''2024''
  AND t.COMPLETION_STATUS = ''수료''
  AND e.WORK_STATUS = ''재직''
GROUP BY t.COURSE_NAME
ORDER BY trainee_count DESC
```

**핵심 패턴**:
- 교육 정보: v_ai_training 테이블
- 수료자만: COMPLETION_STATUS = ''수료''
- 연도: TRAINING_YEAR 컬럼',
    '{
        "intent": "AGGREGATE",
        "complexity": "medium",
        "tables": ["v_ai_training", "v_ai_employee"],
        "sql_template": "SELECT COURSE_NAME, COUNT(DISTINCT EMP_ID), SUM(COMPLETION_HOURS) FROM v_ai_training WHERE TRAINING_YEAR = ? GROUP BY COURSE_NAME",
        "category": "aggregate",
        "tags": ["교육", "연수", "이수", "수료", "과정"]
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
WHERE WORK_STATUS = ''재직''
```

**중요 규칙**:
- 직원 수, 직원 명단 조회 시 특별한 언급이 없으면 재직자만 대상
- "퇴직자", "퇴사자", "전체 직원" 등 명시적 언급 시에만 조건 변경

**반대 개념**:
- 퇴직자: WORK_STATUS = ''퇴직''',
    '{
        "term": "재직자",
        "sql_condition": "WORK_STATUS = ''재직''",
        "synonyms": ["현직", "재직중", "active", "근무중"],
        "column_reference": "v_ai_employee.WORK_STATUS",
        "category": "hr_terms",
        "tags": ["재직", "재직자", "active", "현직", "근무중"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '퇴직자',
    'glossary',
    '**퇴직자 (Resigned Employee)**

회사를 떠난 전 직원을 의미합니다.

**SQL 조건**:
```sql
-- 현재 퇴직 상태인 직원
WHERE WORK_STATUS = ''퇴직''

-- 특정 연도 퇴사자 (퇴사 시점 기준)
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, ''YYYY'') = ''2024''
```

**관련 컬럼**:
- WORK_STATUS: 현재 재직 상태
- RETIRE_DATE: 퇴직일
- RETIRE_REASON: 퇴직 사유',
    '{
        "term": "퇴직자",
        "sql_condition": "WORK_STATUS = ''퇴직''",
        "synonyms": ["퇴사자", "전직원", "resigned"],
        "column_reference": "v_ai_employee.WORK_STATUS, v_ai_employee.RETIRE_DATE",
        "category": "hr_terms",
        "tags": ["퇴직", "퇴사", "퇴직자", "전직원"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '입사자',
    'glossary',
    '**입사자 (New Hire)**

특정 기간에 회사에 입사한 직원을 의미합니다.

**SQL 조건**:
```sql
-- 특정 연도 입사자
WHERE TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''

-- 최근 3개월 내 입사자
WHERE HIRE_DATE >= ADD_MONTHS(SYSDATE, -3)
```

**중요**: 입사자 집계 시 WORK_STATUS 조건 불필요 (입사 시점 기준)

**관련 컬럼**:
- HIRE_DATE: 입사일 (NOT NULL)
- HIRE_TYPE: 채용유형 (신입, 경력)',
    '{
        "term": "입사자",
        "sql_condition": "TO_CHAR(HIRE_DATE, ''YYYY'') = ?",
        "synonyms": ["신입", "새직원", "new hire", "입사"],
        "column_reference": "v_ai_employee.HIRE_DATE",
        "category": "hr_terms",
        "tags": ["입사", "입사자", "신입", "채용"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '직위',
    'glossary',
    '**직위 (Position)**

조직 내에서의 계층적 위치를 나타냅니다.

**직위 체계**:
| 직위 | 순서 |
|------|------|
| 사원 | 1 |
| 대리 | 2 |
| 과장 | 3 |
| 차장 | 4 |
| 부장 | 5 |
| 이사 | 6 |
| 전무이사 | 7 |
| 사장 | 8 |
| 회장 | 9 |

**SQL 예시**:
```sql
-- 과장 이상
WHERE POSITION IN (''과장'', ''차장'', ''부장'', ''이사'', ''전무이사'', ''사장'', ''회장'')

-- 대리 이하
WHERE POSITION IN (''사원'', ''대리'')
```

**주의**: GRADE 컬럼과 다름 (GRADE는 직급/등급)',
    '{
        "term": "직위",
        "values": ["사원", "대리", "과장", "차장", "부장", "이사", "전무이사", "사장", "회장"],
        "column_reference": "v_ai_employee.POSITION",
        "category": "hr_terms",
        "tags": ["직위", "position", "사원", "대리", "과장", "차장", "부장", "이사"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '부서',
    'glossary',
    '**부서 (Department)**

직원이 소속된 조직 단위를 의미합니다.

**SQL 조건**:
```sql
-- 특정 부서
WHERE DEPARTMENT = ''개발팀''

-- 부서명 검색
WHERE DEPARTMENT LIKE ''%영업%''
```

**관련 컬럼**:
- v_ai_employee.DEPARTMENT: 부서명
- v_ai_feedback.EMP_ORG_NM: 평가 시점 소속부서
- v_ai_pay_report.ORGANIZATION_NAME: 급여 소속',
    '{
        "term": "부서",
        "sql_condition": "DEPARTMENT = ?",
        "synonyms": ["팀", "조직", "department", "소속"],
        "column_reference": "v_ai_employee.DEPARTMENT",
        "category": "hr_terms",
        "tags": ["부서", "팀", "조직", "소속", "department"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '평가등급',
    'glossary',
    '**평가등급 (Appraisal Grade)**

인사평가/성과평가 결과를 등급으로 표시합니다.

**등급 체계**:
| 등급 | 의미 |
|------|------|
| S | 최우수 (Superb) |
| A | 우수 (Excellent) |
| B | 양호 (Good) |
| C | 보통 (Average) |
| D | 미흡 (Below) |

**SQL 예시**:
```sql
-- 우수 이상 (S, A등급)
WHERE APPR_GRADE IN (''S'', ''A'')

-- 특정 연도 평가
WHERE TO_CHAR(END_YMD, ''YYYY'') = ''2024''
```

**관련 컬럼**:
- APPR_GRADE: 평가등급
- APPR_SCORE: 평가점수',
    '{
        "term": "평가등급",
        "values": ["S", "A", "B", "C", "D"],
        "column_reference": "v_ai_feedback.APPR_GRADE",
        "category": "hr_terms",
        "tags": ["평가", "등급", "grade", "인사평가", "S등급", "A등급"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '고용형태',
    'glossary',
    '**고용형태 (Employment Type)**

직원의 고용 계약 형태를 의미합니다.

**고용형태**:
- 정규직: 정규 근로계약
- 계약직: 기간제 근로계약
- 인턴: 인턴십

**SQL 조건**:
```sql
-- 정규직만
WHERE EMP_TYPE = ''정규직''

-- 비정규직 (정규직 제외)
WHERE EMP_TYPE != ''정규직''
```',
    '{
        "term": "고용형태",
        "values": ["정규직", "계약직", "인턴"],
        "column_reference": "v_ai_employee.EMP_TYPE",
        "category": "hr_terms",
        "tags": ["고용형태", "정규직", "계약직", "인턴", "employment"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '채용유형',
    'glossary',
    '**채용유형 (Hire Type)**

입사 시 채용 경로를 의미합니다.

**채용유형**:
- 신입: 신규 입사 (경력 없음)
- 경력: 경력직 채용
- 입사(신입): 신입 입사
- 입사(경력): 경력 입사

**SQL 조건**:
```sql
-- 신입 입사자
WHERE HIRE_TYPE LIKE ''%신입%''

-- 경력직
WHERE HIRE_TYPE LIKE ''%경력%''
```',
    '{
        "term": "채용유형",
        "values": ["신입", "경력", "입사(신입)", "입사(경력)"],
        "column_reference": "v_ai_employee.HIRE_TYPE",
        "category": "hr_terms",
        "tags": ["채용", "신입", "경력", "hire", "입사유형"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '급여',
    'glossary',
    '**급여 (Salary/Pay)**

직원에게 지급되는 보수를 의미합니다.

**급여 관련 컬럼**:
- FIXED_PAY_AMOUNT: 고정비
- VARIABLE_PAY_AMOUNT: 변동비
- GROSS_PAY_AMOUNT: 지급합계
- DEDUCTION_AMOUNT: 공제합계
- NET_PAY_AMOUNT: 실지급액 ★

**급여지급구분 (PAYMENT_TYPE_NAME)**:
- 정기급여: 월 정기 급여
- 연차수당: 미사용 연차 수당
- 격려금: 격려금
- 상여: 상여금

**SQL 예시**:
```sql
-- 월 정기급여
WHERE PAYMENT_TYPE_NAME = ''정기급여''

-- 특정 연월
WHERE PAY_YEAR_MONTH = ''202401''
```',
    '{
        "term": "급여",
        "columns": ["FIXED_PAY_AMOUNT", "VARIABLE_PAY_AMOUNT", "GROSS_PAY_AMOUNT", "NET_PAY_AMOUNT"],
        "column_reference": "v_ai_pay_report",
        "category": "hr_terms",
        "tags": ["급여", "연봉", "월급", "보수", "pay", "salary", "실지급액"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    '1:N 관계 조인 규칙',
    'glossary',
    '**1:N 관계 조인 시 중복 방지 규칙**

v_ai_employee와 1:N 관계인 뷰를 조인하여 직원 수를 집계할 때는 중복 카운트를 방지해야 합니다.

**1:N 관계 뷰**:
- v_ai_address, v_ai_career, v_ai_education, v_ai_family
- v_ai_language, v_ai_license, v_ai_reward, v_ai_training, v_ai_feedback

**잘못된 쿼리 (중복 발생)**:
```sql
SELECT COUNT(*) FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE l.LICENSE_NAME LIKE ''%정보처리%''
```

**올바른 쿼리 (EXISTS 사용)**:
```sql
SELECT COUNT(*) FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (SELECT 1 FROM v_ai_license l
              WHERE l.EMP_ID = e.EMP_ID
                AND l.LICENSE_NAME LIKE ''%정보처리%'')
```

**적용 기준**:
- 직원 **수** 집계 + 1:N 조건 → EXISTS 사용
- 직원 **목록** 조회 + 1:N 조건 → EXISTS 또는 IN 사용
- 1:N 뷰의 **상세 데이터** 필요 시에만 JOIN 사용',
    '{
        "term": "1:N 관계 조인",
        "sql_pattern": "EXISTS (SELECT 1 FROM ... WHERE ...)",
        "category": "sql_pattern",
        "tags": ["EXISTS", "서브쿼리", "중복방지", "1:N", "조인"]
    }'::jsonb,
    true,
    'cortex_seed',
    'cortex'
);

INSERT INTO tb_docs (title, doc_type, content, metadata, indexed, source_type, usage_type) VALUES
(
    'Oracle 날짜 처리',
    'glossary',
    '**Oracle 날짜 처리 규칙**

Oracle에서 날짜를 처리하는 표준 패턴입니다.

**연도 추출**:
```sql
TO_CHAR(날짜컬럼, ''YYYY'')
-- 예: TO_CHAR(HIRE_DATE, ''YYYY'') = ''2024''
```

**월 추출**:
```sql
TO_CHAR(날짜컬럼, ''MM'')
TO_CHAR(날짜컬럼, ''YYYY-MM'')
```

**날짜 비교**:
```sql
TO_DATE(''2024-01-01'', ''YYYY-MM-DD'')
```

**기간 조건**:
```sql
TO_CHAR(날짜컬럼, ''YYYY'') BETWEEN ''2010'' AND ''2020''
```

**현재 연도**:
```sql
TO_CHAR(SYSDATE, ''YYYY'')
```

**NULL 처리**:
```sql
NVL(컬럼, 기본값)
```',
    '{
        "term": "Oracle 날짜 처리",
        "sql_patterns": ["TO_CHAR", "TO_DATE", "SYSDATE", "NVL"],
        "category": "sql_pattern",
        "tags": ["Oracle", "날짜", "TO_CHAR", "TO_DATE", "SYSDATE"]
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
