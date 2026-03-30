"""
win-AI NL2SQL 테스트 스크립트 - Google Colab용
기존 Colab 환경(모델+tokenizer+test_chat 로딩 완료)에서
아래 셀들을 순서대로 붙여넣어 실행합니다.

== Colab 셀 구성 ==
  셀 1: (이미 완료) pip install, 모델 로드, test_chat 정의
  셀 2: 이 파일의 [셀 2] 부분 붙여넣기 → 시스템 프롬프트 + 유틸 함수 정의
  셀 3: 개별 질문 테스트 (하나씩 붙여넣기)
  셀 4: (선택) 전체 일괄 테스트
"""

# ==============================================================
# [셀 2] 시스템 프롬프트 + 유틸 함수 정의
# ==============================================================

import time

# ── 시스템 프롬프트 (로그에서 추출한 실제 프롬프트) ──
SYSTEM_PROMPT = """당신은 Oracle 전문가입니다. 자연어 질문을 Oracle SQL로 변환하세요.

# 스키마
# 데이터베이스 스키마 (ORACLE)

## 테이블: v_ai_employee
컬럼:
  - EMP_ID: NUMBER (NOT NULL)
  - EMP_NAME: VARCHAR2 (NULL 가능)
  - EMP_NAME_ENG: VARCHAR2 (NULL 가능)
  - COMPANY_CODE: VARCHAR2 (NOT NULL)
  - POSITION: VARCHAR2 (NULL 가능)
  - BIRTH_DATE: DATE (NULL 가능)
  - DEPARTMENT: VARCHAR2 (NULL 가능)
  - CAREER_MONTHS: NUMBER (NULL 가능)
  - CAREER_YEARS: NUMBER (NULL 가능)
  - DUTY: VARCHAR2 (NULL 가능)
  - DUTY_DATE: DATE (NULL 가능)
  - EMP_TYPE: VARCHAR2 (NULL 가능)
  - GENDER: VARCHAR2 (NULL 가능)
  - GROUP_JOIN_DATE: DATE (NULL 가능)
  - HIRE_TYPE: VARCHAR2 (NULL 가능)
  - HIRE_DATE: DATE (NOT NULL)
  - WORK_STATUS: VARCHAR2 (NULL 가능)
  - GRADE: VARCHAR2 (NULL 가능)
  - GRADE_DATE: DATE (NULL 가능)
  - RETIRE_REASON: VARCHAR2 (NULL 가능)
  - RETIRE_DATE: DATE (NULL 가능)
  - SALARY_STEP: VARCHAR2 (NULL 가능)
  - SALARY_STEP_DATE: DATE (NULL 가능)
샘플 데이터 (예시):
  1. {'emp_id': 1507, 'emp_name': '문복정', 'company_code': '01', 'position': '대리', 'birth_date': '1972-02-17', 'department': 'LA지점', 'emp_type': '정규직', 'gender': '남', 'hire_type': '입사(신입)', 'hire_date': '2009-05-15', 'work_status': '퇴직', 'grade': '5급', 'retire_date': '2011-05-06'}
  2. {'emp_id': 2282, 'emp_name': '편자경', 'company_code': '01', 'position': '대리', 'birth_date': '1972-02-18', 'department': '2차그룹', 'duty': '팀원', 'emp_type': '정규직', 'gender': '여', 'hire_type': '입사(신입)', 'hire_date': '2007-09-21', 'work_status': '재직', 'grade': '5급'}

## 테이블: v_ai_pay_report (급여통계 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMPLOYEE_ID: NUMBER (NOT NULL) -- 사원ID PK (FK → V_AI_EMPLOYEE)
  - EMPLOYEE_NAME: VARCHAR2 (NULL 가능) -- 성명
  - PAY_YEAR: VARCHAR2 (NULL 가능) -- 급여년도 (예: '2024')
  - PAY_YEAR_MONTH: VARCHAR2 (NULL 가능) -- 급여년월 PK (예: '202403', YYYYMM 형식)
  - PAY_DATE: VARCHAR2 (NULL 가능) -- 급여일 (YYYYMMDD 형식)
  - PAY_DATE_ID: NUMBER (NULL 가능) -- 급여일자ID
  - PAYMENT_TYPE_NAME: VARCHAR2 (NULL 가능) -- 급여지급구분 PK (정기급여, 연차수당, 격려금, 상여)
  - SALARY_TYPE_NAME: VARCHAR2 (NULL 가능) -- 급여유형
  - PAY_GRADE_NAME: VARCHAR2 (NULL 가능) -- 급여직급
  - JOB_GRADE_NAME: VARCHAR2 (NULL 가능) -- 직급
  - EMPLOYMENT_TYPE: VARCHAR2 (NULL 가능) -- 급여직군
  - ACCOUNT_TYPE_NAME: VARCHAR2 (NULL 가능) -- 코스트센터
  - JOB_TYPE_NAME: VARCHAR2 (NULL 가능) -- 계정유형
  - ORGANIZATION_ID: VARCHAR2 (NULL 가능) -- 소속코드
  - ORGANIZATION_NAME: VARCHAR2 (NULL 가능) -- 소속명
  - FIXED_PAY_AMOUNT: NUMBER (NULL 가능) -- 고정비
  - VARIABLE_PAY_AMOUNT: NUMBER (NULL 가능) -- 변동비
  - GROSS_PAY_AMOUNT: NUMBER (NULL 가능) -- 지급합계
  - DEDUCTION_AMOUNT: NUMBER (NULL 가능) -- 공제합계
  - TAX_AMOUNT: NUMBER (NULL 가능) -- 세금합계
  - TOTAL_DEDUCTION_AMOUNT: NUMBER (NULL 가능) -- 총공제액
  - NET_PAY_AMOUNT: NUMBER (NULL 가능) -- 실지급액
  - REMARKS: VARCHAR2 (NULL 가능) -- 비고
샘플 데이터 (예시):
  1. {'employee_id': 2282, 'employee_name': '편자경', 'pay_year': '2024', 'pay_year_month': '202403', 'payment_type_name': '정기급여', 'organization_name': '2차그룹', 'fixed_pay_amount': 3200000, 'variable_pay_amount': 500000, 'gross_pay_amount': 3700000, 'deduction_amount': 148000, 'tax_amount': 222000, 'total_deduction_amount': 370000, 'net_pay_amount': 3330000}
  2. {'employee_id': 1234, 'pay_year': '2024', 'pay_year_month': '202412', 'payment_type_name': '상여', 'gross_pay_amount': 5000000, 'net_pay_amount': 4300000}

## 테이블: v_ai_dtm_yy_rest (년월차관리 - EMPLOYEE_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - LEAVE_ACCRUAL_ID: NUMBER (NOT NULL) -- 발생연차관리ID
  - EMPLOYEE_ID: NUMBER (NULL 가능) -- 사원ID (FK → V_AI_EMPLOYEE)
  - REFERENCE_YEAR: VARCHAR2 (NULL 가능) -- 기준년도 (예: '2024')
  - LEAVE_TYPE_CODE: VARCHAR2 (NULL 가능) -- 연차구분코드
  - ACCRUAL_DATE: DATE (NULL 가능) -- 발생일자
  - LEAVE_GRANT_RULE_CODE: VARCHAR2 (NULL 가능) -- 연차부여기준코드
  - ACCRUED_LEAVE_DAYS: NUMBER (NULL 가능) -- 발생연차일수
  - ADDITIONAL_LEAVE_DAYS: NUMBER (NULL 가능) -- 추가연차일수
  - COMPENSATED_LEAVE_DAYS: NUMBER (NULL 가능) -- 보상연차
  - COMPENSATION_MONTH: VARCHAR2 (NULL 가능) -- 보상적용월
  - COMPENSATED_LEAVE_DAYS_2: NUMBER (NULL 가능) -- 보상연차2
  - COMPENSATION_MONTH_2: VARCHAR2 (NULL 가능) -- 보상적용월2
  - RETIREMENT_LEAVE_DAYS: NUMBER (NULL 가능) -- 퇴직연차
  - RETIREMENT_COMPENSATION_MONTH: VARCHAR2 (NULL 가능) -- 퇴직보상적용월
  - USED_LEAVE_DAYS_PAST: NUMBER (NULL 가능) -- 사용연차(과거)
  - CARRIED_OVER_LEAVE_DAYS: NUMBER (NULL 가능) -- 이월연차(차년추가연차)
  - REMARKS: VARCHAR2 (NULL 가능) -- 비고
  - UPDATED_AT: DATE (NULL 가능) -- 변경일시

## 테이블: v_ai_address (사원 주소 - EMP_ID로 v_ai_employee와 JOIN)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - ADDRESS: VARCHAR2 (NULL 가능) -- 기본 주소
  - ADDRESS_DETAIL: VARCHAR2 (NULL 가능) -- 상세 주소
  - ZIP_CODE: VARCHAR2 (NULL 가능) -- 우편번호
  - REGION: VARCHAR2 (NULL 가능) -- 거주 시/도 (서울, 경기, 부산 등)
  - MOD_DATE: DATE (NULL 가능) -- 수정일시

## 테이블: v_ai_career (이전 직장 경력 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - PREV_COMPANY: VARCHAR2 (NULL 가능) -- 이전에 근무한 회사명
  - LOCATION: VARCHAR2 (NULL 가능) -- 전직장 소재지
  - PREV_POSITION: VARCHAR2 (NULL 가능) -- 전직장 직위
  - WORK_MONTHS: NUMBER (NULL 가능) -- 해당 직장 근무 개월 수
  - WORK_YEARS: NUMBER (NULL 가능) -- 해당 직장 근무 연수
  - RECOGNITION_RATE: NUMBER (NULL 가능) -- 경력 인정 비율 (%)
  - LEAVE_REASON: VARCHAR2 (NULL 가능) -- 퇴직 사유

## 테이블: v_ai_scholar (학력사항 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - POSITION: VARCHAR2 (NULL 가능) -- 직위
  - MAJOR_NAME: VARCHAR2 (NULL 가능) -- 전공학과 명
  - DOUBLE_MAJOR_NAME: VARCHAR2 (NULL 가능) -- 복수 전공 명
  - SCHOOL_NAME: VARCHAR2 (NULL 가능) -- 학교 명
  - ADMISSION_DATE: VARCHAR2 (NULL 가능) -- 입학일자 (YYYYMM)
  - GRADUATION_DATE: VARCHAR2 (NULL 가능) -- 졸업일자 (YYYYMM)
  - SUB_MAJOR_NM: VARCHAR2 (NULL 가능) -- 부전공 명
  - SCHOOL_LOCATION_NAME: VARCHAR2 (NULL 가능) -- 학교 위치(소재지)

## 테이블: v_ai_family (가족 구성원 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - RELATION: VARCHAR2 (NULL 가능) -- 가족 관계 (배우자, 자녀, 부모 등)
  - FAMILY_NAME: VARCHAR2 (NULL 가능) -- 가족 구성원 이름
  - FAMILY_GENDER: VARCHAR2 (NULL 가능) -- 가족 성별
  - FAMILY_BIRTH_DATE: DATE (NULL 가능) -- 가족 생년월일
  - FAMILY_COMPANY: VARCHAR2 (NULL 가능) -- 가족 근무회사
  - FAMILY_POSITION: VARCHAR2 (NULL 가능) -- 가족 근무회사 직위
  - FAMILY_SCHOOL: VARCHAR2 (NULL 가능) -- 가족 출신학교
  - DISABILITY_STATUS: VARCHAR2 (NULL 가능) -- 장애 여부 (장애있음, 장애없음)
  - DISABILITY_GRADE: VARCHAR2 (NULL 가능) -- 장애 등급

## 테이블: v_ai_language (어학 성적 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - LANGUAGE_TYPE: VARCHAR2 (NULL 가능) -- 어학 종류 (영어, 일본어, 중국어 등)
  - EXAM_TYPE: VARCHAR2 (NULL 가능) -- 시험 종류 (TOEIC, TOEFL, JLPT 등)
  - EXAM_INSTITUTION: VARCHAR2 (NULL 가능) -- 시험 기관
  - SCORE: NUMBER (NULL 가능) -- 어학 시험 점수
  - LANGUAGE_GRADE: VARCHAR2 (NULL 가능) -- 어학 등급
  - EXAM_DATE: VARCHAR2 (NULL 가능) -- 시험일 (YYYYMMDD)
  - EXAM_YEAR: VARCHAR2 (NULL 가능) -- 시험 응시 연도 (YYYY)
  - EVALUATION_YEAR: VARCHAR2 (NULL 가능) -- 평가 기준년도
  - EVALUATION_SEQ: NUMBER (NULL 가능) -- 평가 순번

## 테이블: v_ai_license (자격증/면허 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - LICENSE_TYPE: VARCHAR2 (NULL 가능) -- 자격 구분 (국가자격, 민간자격 등)
  - LICENSE_NAME: VARCHAR2 (NULL 가능) -- 자격증 이름
  - LICENSE_NO: VARCHAR2 (NULL 가능) -- 자격증 번호
  - ISSUING_ORG: VARCHAR2 (NULL 가능) -- 발급기관
  - ISSUE_DATE: VARCHAR2 (NULL 가능) -- 자격증 취득일 (YYYYMMDD)
  - EXPIRY_DATE: VARCHAR2 (NULL 가능) -- 자격증 만료일 (YYYYMMDD)
  - VALIDITY_STATUS: VARCHAR2 (NULL 가능) -- 유효 상태 (유효, 만료, 영구)
  - ALLOWANCE_TYPE: VARCHAR2 (NULL 가능) -- 수당 유형

## 테이블: v_ai_reward (상벌 내역 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - REWARD_TYPE: VARCHAR2 (NULL 가능) -- 상벌 구분 (포상, 징계)
  - REWARD_KIND: VARCHAR2 (NULL 가능) -- 상벌 종류
  - REWARD_REASON: VARCHAR2 (NULL 가능) -- 사유
  - REWARD_CONTENT: VARCHAR2 (NULL 가능) -- 내용
  - REWARD_DATE: VARCHAR2 (NULL 가능) -- 일자 (YYYYMMDD)
  - REWARD_YEAR: VARCHAR2 (NULL 가능) -- 상벌 발생 연도 (YYYY)
  - AWARDING_ORG: VARCHAR2 (NULL 가능) -- 기관
  - REWARD_AMOUNT: NUMBER (NULL 가능) -- 포상금 금액

## 테이블: v_ai_training (교육/연수 이수 내역 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - TRAINING_YEAR: VARCHAR2 (NULL 가능) -- 교육 실시 연도 (YYYY)
  - COURSE_TYPE: VARCHAR2 (NULL 가능) -- 교육 종류
  - COURSE_GRADE: VARCHAR2 (NULL 가능) -- 등급
  - COURSE_FIELD: VARCHAR2 (NULL 가능) -- 교육 분야
  - COURSE_NAME: VARCHAR2 (NULL 가능) -- 교육 과정 이름
  - INSTITUTION_TYPE: VARCHAR2 (NULL 가능) -- 교육기관 유형
  - INSTITUTION_NAME: VARCHAR2 (NULL 가능) -- 교육기관 이름
  - TRAINING_LOCATION: VARCHAR2 (NULL 가능) -- 교육장소
  - TRAINING_TYPE: VARCHAR2 (NULL 가능) -- 교육 유형
  - START_DATE: VARCHAR2 (NULL 가능) -- 교육시작일자 (YYYYMMDD)
  - END_DATE: VARCHAR2 (NULL 가능) -- 교육종료일자 (YYYYMMDD)
  - TRAINING_COST: NUMBER (NULL 가능) -- 교육비용
  - COMPLETION_POINTS: NUMBER (NULL 가능) -- 총이수포인트
  - COMPLETION_HOURS: NUMBER (NULL 가능) -- 총 이수 시간
  - COMPLETION_STATUS: VARCHAR2 (NULL 가능) -- 수료 여부 (수료, 미수료)
  - REFUND_AMOUNT: NUMBER (NULL 가능) -- 환급금액

## 테이블: v_ai_feedback (인사평가 - EMP_ID로 v_ai_employee와 JOIN, 1:N)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - APPR_ID: VARCHAR2 (NULL 가능) -- 평가번호
  - APPR_NM: VARCHAR2 (NULL 가능) -- 평가 명
  - PEE_TYPE_CD: VARCHAR2 (NULL 가능) -- 평가 종류 코드
  - PEE_TYPE_NM: VARCHAR2 (NULL 가능) -- 평가 이름
  - EMP_ORG_NM: VARCHAR2 (NULL 가능) -- 소속 부서 명
  - RATEE_LEVEL_NM: VARCHAR2 (NULL 가능) -- 직책 명
  - APPR_SCORE: NUMBER (NULL 가능) -- 평가 점수
  - APPR_GRADE: VARCHAR2 (NULL 가능) -- 평가등급
  - RK: VARCHAR2 (NULL 가능) -- 순위
  - PEE_OPINION: VARCHAR2 (NULL 가능) -- 평가자 의견
  - END_YMD: VARCHAR2 (NULL 가능) -- 평가종료일자 (YYYYMMDD)
  - APPR_YMD: VARCHAR2 (NULL 가능) -- 평가 일자 (YYYYMMDD)

## 테이블: v_ai_military (병역 정보 - EMP_ID로 v_ai_employee와 JOIN)
컬럼:
  - EMP_ID: NUMBER (NOT NULL) -- 사원ID (FK → V_AI_EMPLOYEE)
  - MILITARY_TYPE: VARCHAR2 (NULL 가능) -- 군 종류 (육군, 해군, 공군, 해병대 등)
  - MILITARY_BRANCH: VARCHAR2 (NULL 가능) -- 병과 주특기
  - MILITARY_RANK: VARCHAR2 (NULL 가능) -- 최종 계급 (병장, 상병 등)
  - SERVICE_TYPE: VARCHAR2 (NULL 가능) -- 복무 유형
  - SERVICE_STATUS: VARCHAR2 (NULL 가능) -- 군필 여부 (군필, 미필, 면제 등)
  - DISCHARGE_TYPE: VARCHAR2 (NULL 가능) -- 전역사유
  - DISCHARGE_DATE: VARCHAR2 (NULL 가능) -- 전역일자 (YYYYMMDD)
  - DISCHARGE_YEAR: VARCHAR2 (NULL 가능) -- 전역한 연도 (YYYY)
  - SPECIALTY: VARCHAR2 (NULL 가능) -- 특기
  - MILITARY_NO: VARCHAR2 (NULL 가능) -- 군번


# 필수 규칙(중요)
- SELECT만 생성 (INSERT/UPDATE/DELETE/DROP 금지)
- *** 단일 쿼리만 생성 ***   (세미콜론 금지)
- *** SQL만 출력 *** (설명, 마크다운 코드블록 금지)
- 행 수 제한 절 사용 금지 (시스템이 자동 추가)
- 큰 수치를 기준으로 ORDER BY 하세요.

# 날짜
- 올해는 2026년, 오늘 = 2026년 03월 12일임(LLM기준 날짜 추측 절대 금지)
- 기간 미명시 → 전체 기간 조회
- "올해", "작년", "최근 N년" 등 명시 시에만 연도 조건 추가

# 재직 조건 (우선순위)
1. 입사자/퇴직자 집계 → 재직 조건 없음 (HIRE_DATE, RETIRE_DATE 기준)
2. 그 외 직원 조회 → WHERE WORK_STATUS = '재직'
3. "퇴직자", "전체 직원" 명시 시 조건 변경

# 1:N 관계 조인 (중복 방지)
- 1:N 뷰: V_AI_ADDRESS, V_AI_CAREER, V_AI_SCHOLAR, V_AI_FAMILY, V_AI_LANGUAGE, V_AI_LICENSE, V_AI_REWARD, V_AI_TRAINING, V_AI_FEEDBACK, V_AI_PAY_REPORT
- COUNT + 1:N 조건 → EXISTS 사용
- 목록 조회 + 1:N 조건 → EXISTS 또는 IN 사용
- 상세 데이터 필요 시만 JOIN

# 서브쿼리
- 이름으로 ID 조회 → IN 사용 (= 금지, 동명이인 ORA-01427)

# 인원수 집계 (중요)
- 인원수/사람 수를 셀 때는 반드시 COUNT(DISTINCT EMP_ID)를 사용하세요
- V_AI_EMPLOYEE 뷰에 1인당 여러 행이 존재할 수 있음 (FRM_CODE JOIN)
- COUNT(*)는 행 수이므로 실제 인원수와 다를 수 있음

# 급여 (V_AI_PAY_REPORT)
- PAY_YEAR_MONTH = 'YYYYMM' (예: 2016년 3월 → '201603')
- 일반 급여: PAYMENT_TYPE_NAME = '정기급여'

# 평가
- 인사평가/직원평가 → V_AI_FEEDBACK 조회

# 년월차
- 총 년월차 일수 = accrued_leave_days+additional_leave_days+compensated_leave_days+compensated_leave_days2+retirement_leave_days

---
## 유사 쿼리 예제 (Few-shot)

### 예제 1: 현재 재직자 수 조회
질문: 현재 재직 중인 직원 수
## SQL
```sql
SELECT COUNT(*) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```
## 핵심 패턴
- 재직자 기본 조건: WORK_STATUS = '재직'
- 특별한 언급이 없으면 재직자만 대상

### 예제 2: 연도별 입사자 수 조회
질문: 2024년 입사자 수를 알려줘
## SQL
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = '2024'
```
## 핵심 패턴
- 연도 추출: TO_CHAR(HIRE_DATE, 'YYYY')
- 입사자 집계 시 WORK_STATUS 조건 불필요

### 예제 3: 부서별 직원 수
질문: 부서별 직원 수를 알려줘
## SQL
```sql
SELECT DEPARTMENT, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY emp_count DESC
```
## 핵심 패턴
- GROUP BY DEPARTMENT로 부서별 그룹화"""


def make_user_prompt(question):
    """유저 프롬프트 생성"""
    return f"""질문: {question}

위 질문에 대한 Oracle SELECT 쿼리를 생성해주세요.
SQL만 출력하세요 (설명 없이)."""


def nl2sql(question, max_new_tokens=512):
    """질문 → SQL 생성 (기존 test_chat 활용)"""
    user_prompt = make_user_prompt(question)
    start = time.time()
    result = test_chat(user_prompt, SYSTEM_PROMPT, max_new_tokens=max_new_tokens)
    elapsed = time.time() - start

    # 마크다운 코드블록 제거
    result = result.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        result = "\n".join(lines).strip()
    # 세미콜론 제거
    result = result.rstrip(";").strip()

    print(f"질문: {question}")
    print(f"생성 SQL: {result}")
    print(f"소요시간: {elapsed:.1f}초")
    print()
    return result


print("준비 완료! nl2sql('질문') 으로 테스트하세요.")


# ==============================================================
# [셀 3] 개별 질문 테스트 - 하나씩 복사해서 셀에 붙여넣기
# ==============================================================

# --- 기본 ---
# nl2sql("회사의 직원수는?")
# nl2sql("2024년 입사자 수를 알려줘")
# nl2sql("현재 재직 중인 여성 직원은 몇 명이야?")

# --- 중급 ---
# nl2sql("부서별 직원 수를 알려줘")
# nl2sql("직위별 인원 현황을 보여줘")
# nl2sql("올해 퇴사한 직원 수는?")
# nl2sql("고용형태별 직원 수를 보여줘")

# --- 고급 ---
# nl2sql("최근 3년간 연도별 입사자 수 추이를 보여줘")
# nl2sql("부서별 성별 인원 현황을 보여줘")
# nl2sql("경력 10년 이상인 재직 직원은 몇 명이야?")

# --- 급여 ---
# nl2sql("2024년 3월 정기급여 지급 총액은?")
# nl2sql("부서별 월평균 실지급액을 보여줘")
# nl2sql("2024년 연간 급여 지급 현황을 월별로 보여줘")
# nl2sql("올해 상여금을 받은 직원 수는?")

# --- 연차/년월차 ---
# nl2sql("2024년 기준 직원별 총 년월차 일수를 보여줘")
# nl2sql("발생연차가 가장 많은 직원 10명을 알려줘")

# --- 기타 ---
# nl2sql("영어 TOEIC 점수가 800점 이상인 재직 직원은?")
# nl2sql("자격증을 3개 이상 보유한 직원 수는?")
# nl2sql("최근 3년간 포상을 받은 직원 목록을 보여줘")
# nl2sql("서울 거주 재직 직원 수는?")
# nl2sql("배우자가 있는 재직 직원 수는?")
# nl2sql("인사평가 점수가 90점 이상인 직원은?")
# nl2sql("2024년 교육 이수 시간이 가장 많은 직원 5명을 보여줘")


# ==============================================================
# [셀 4] (선택) 전체 일괄 테스트
# ==============================================================

TEST_QUESTIONS = [
    # (ID, 난이도, 질문, 기대 키워드)
    # --- v_ai_employee ---
    ("Q01", "기본", "회사의 직원수는?",
     ["COUNT", "v_ai_employee", "WORK_STATUS", "재직"]),
    ("Q02", "기본", "2024년 입사자 수를 알려줘",
     ["COUNT", "HIRE_DATE", "2024"]),
    ("Q03", "기본", "현재 재직 중인 여성 직원은 몇 명이야?",
     ["COUNT", "WORK_STATUS", "재직", "GENDER", "여"]),
    ("Q04", "중급", "부서별 직원 수를 알려줘",
     ["DEPARTMENT", "COUNT", "GROUP BY", "WORK_STATUS", "재직"]),
    ("Q05", "중급", "직위별 인원 현황을 보여줘",
     ["POSITION", "COUNT", "GROUP BY", "WORK_STATUS"]),
    ("Q06", "중급", "올해 퇴사한 직원 수는?",
     ["COUNT", "RETIRE_DATE", "2026"]),
    ("Q07", "중급", "고용형태별 직원 수를 보여줘",
     ["EMP_TYPE", "COUNT", "GROUP BY"]),
    ("Q08", "고급", "최근 3년간 연도별 입사자 수 추이를 보여줘",
     ["TO_CHAR", "HIRE_DATE", "GROUP BY", "ORDER BY"]),
    ("Q09", "고급", "부서별 성별 인원 현황을 보여줘",
     ["DEPARTMENT", "GENDER", "COUNT", "GROUP BY"]),
    ("Q10", "고급", "경력 10년 이상인 재직 직원은 몇 명이야?",
     ["COUNT", "CAREER_YEARS", "10", "WORK_STATUS", "재직"]),
    # --- v_ai_pay_report (급여) ---
    ("Q11", "기본", "2024년 3월 정기급여 지급 총액은?",
     ["v_ai_pay_report", "PAY_YEAR_MONTH", "202403", "PAYMENT_TYPE_NAME", "정기급여", "SUM", "GROSS_PAY_AMOUNT"]),
    ("Q12", "중급", "부서별 월평균 실지급액을 보여줘",
     ["v_ai_pay_report", "ORGANIZATION_NAME", "AVG", "NET_PAY_AMOUNT", "GROUP BY"]),
    ("Q13", "중급", "2024년 연간 급여 지급 현황을 월별로 보여줘",
     ["v_ai_pay_report", "PAY_YEAR_MONTH", "2024", "SUM", "GROUP BY", "ORDER BY"]),
    ("Q14", "고급", "올해 상여금을 받은 직원 수는?",
     ["v_ai_pay_report", "PAYMENT_TYPE_NAME", "상여", "COUNT", "2026"]),
    # --- v_ai_dtm_yy_rest (년월차) ---
    ("Q15", "중급", "2024년 기준 직원별 총 년월차 일수를 보여줘",
     ["v_ai_dtm_yy_rest", "REFERENCE_YEAR", "2024", "accrued_leave_days", "additional_leave_days"]),
    # --- 기타 뷰 ---
    ("Q16", "중급", "영어 TOEIC 점수가 800점 이상인 재직 직원은?",
     ["v_ai_language", "LANGUAGE_TYPE", "영어", "SCORE", "800", "WORK_STATUS", "재직"]),
    ("Q17", "중급", "자격증을 3개 이상 보유한 직원 수는?",
     ["v_ai_license", "COUNT", "GROUP BY", "HAVING", "3"]),
    ("Q18", "중급", "서울 거주 재직 직원 수는?",
     ["v_ai_address", "REGION", "서울", "COUNT", "WORK_STATUS", "재직"]),
    ("Q19", "고급", "2024년 교육 이수 시간이 가장 많은 직원 5명을 보여줘",
     ["v_ai_training", "TRAINING_YEAR", "2024", "SUM", "COMPLETION_HOURS", "ORDER BY", "ROWNUM"]),
    ("Q20", "고급", "인사평가 점수가 90점 이상인 직원은?",
     ["v_ai_feedback", "APPR_SCORE", "90", "WORK_STATUS", "재직"]),
]


def run_all():
    """전체 테스트 일괄 실행"""
    results = []
    total_time = 0

    print("=" * 70)
    print("  win-AI NL2SQL 전체 테스트")
    print("=" * 70)

    for qid, cat, question, keywords in TEST_QUESTIONS:
        print(f"\n{'─' * 60}")
        print(f"[{qid}] ({cat}) {question}")
        print(f"{'─' * 60}")

        user_prompt = make_user_prompt(question)
        start = time.time()
        generated = test_chat(user_prompt, SYSTEM_PROMPT, max_new_tokens=512)
        elapsed = time.time() - start
        total_time += elapsed

        # 정리
        generated = generated.strip()
        if generated.startswith("```"):
            lines = generated.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            generated = "\n".join(lines).strip()
        generated = generated.rstrip(";").strip()

        # 평가
        gen_upper = generated.upper()
        matched = [kw for kw in keywords if kw.upper() in gen_upper]
        missing = [kw for kw in keywords if kw.upper() not in gen_upper]
        score = len(matched) / len(keywords) * 100
        is_select = gen_upper.strip().startswith("SELECT")
        passed = is_select and score >= 60

        status = "PASS" if passed else "FAIL"
        print(f"  SQL  : {generated}")
        print(f"  시간 : {elapsed:.1f}초 | 점수: {score:.0f}% | {status}")
        if missing:
            print(f"  누락 : {missing}")

        results.append({
            "id": qid, "cat": cat, "question": question,
            "sql": generated, "elapsed": elapsed,
            "score": score, "passed": passed,
        })

    # ── 요약 ──
    pass_count = sum(1 for r in results if r["passed"])
    avg_score = sum(r["score"] for r in results) / len(results)

    print(f"\n{'=' * 70}")
    print(f"  결과: {pass_count}/{len(results)} 통과 | 평균 점수: {avg_score:.0f}%")
    print(f"  총 소요시간: {total_time:.0f}초 | 평균: {total_time/len(results):.1f}초")
    for cat in ["기본", "중급", "고급"]:
        cr = [r for r in results if r["cat"] == cat]
        if cr:
            cp = sum(1 for r in cr if r["passed"])
            ca = sum(r["score"] for r in cr) / len(cr)
            print(f"  [{cat}] {cp}/{len(cr)} 통과, 평균 {ca:.0f}%")
    print("=" * 70)
    return results


# 전체 실행하려면 아래 주석 해제:
# run_all()
