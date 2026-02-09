-- ============================================================================
-- NL2SQL 테이블 카탈로그 설정 (tb_app_settings)
--
-- 업체별 스키마에 맞게 JSON 내용을 수정하여 사용
-- category: nl2sql, key: table_catalog, value_type: json
-- ============================================================================

INSERT INTO tb_app_settings (category, key, value, value_type, description, is_secret)
VALUES (
    'nl2sql',
    'table_catalog',
    '{
    "v_ai_employee": {
        "description": "직원 기본정보 (메인 테이블)",
        "columns": [
            "EMP_ID (PK, 조인키)",
            "EMP_NAME (이름)",
            "DEPARTMENT (부서)",
            "POSITION (직위: 사원,대리,과장,차장,부장)",
            "HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,''YYYY'')='':YYYY'')",
            "RETIRE_DATE ★퇴직일 (퇴사자 집계)",
            "WORK_STATUS ★재직상태 (재직/퇴직)",
            "GRADE (직급/등급)",
            "EMP_TYPE (고용형태: 정규직,계약직)",
            "GENDER (성별)",
            "HIRE_TYPE (채용유형: 신입,경력)"
        ],
        "keywords": ["직원", "사원", "입사", "퇴사", "부서", "직급", "재직", "퇴직"],
        "is_primary": true,
        "join_key": "EMP_ID",
        "relation": "1 (메인)"
    },
    "v_ai_address": {
        "description": "직원 주소/거주지 정보",
        "columns": [
            "EMP_ID (FK)",
            "ADDRESS (기본주소)",
            "REGION ★거주 시/도 (서울,경기,부산 등)",
            "ZIP_CODE (우편번호)"
        ],
        "keywords": ["주소", "거주지", "서울", "경기", "지역", "시도"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_career": {
        "description": "이전 직장 경력 정보",
        "columns": [
            "EMP_ID (FK)",
            "PREV_COMPANY (전 직장명)",
            "PREV_POSITION (전 직장 직위)",
            "WORK_MONTHS (근무 개월수)",
            "WORK_YEARS (근무 연수)"
        ],
        "keywords": ["경력", "전직장", "이전회사", "근무경력"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_education": {
        "description": "학력 정보",
        "columns": [
            "EMP_ID (FK)",
            "SCHOOL_NAME (학교명)",
            "MAJOR (전공)",
            "DOUBLE_MAJOR (복수전공)",
            "GRADUATION_YEAR (졸업연도)"
        ],
        "keywords": ["학력", "학교", "대학", "전공", "졸업"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_family": {
        "description": "가족 관계 정보",
        "columns": [
            "EMP_ID (FK)",
            "RELATION (가족관계: 배우자,자녀,부모)",
            "FAMILY_NAME (가족 이름)",
            "FAMILY_GENDER (가족 성별)",
            "DISABILITY_STATUS (장애여부)"
        ],
        "keywords": ["가족", "배우자", "자녀", "부모", "부양"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_language": {
        "description": "어학 성적 정보 (TOEIC, TOEFL, JLPT 등)",
        "columns": [
            "EMP_ID (FK)",
            "LANGUAGE_TYPE (어학종류: 영어,일본어,중국어)",
            "EXAM_TYPE ★시험종류 (TOEIC,TOEFL,JLPT)",
            "SCORE ★시험점수",
            "LANGUAGE_GRADE (등급)",
            "EXAM_DATE (응시일)"
        ],
        "keywords": ["어학", "토익", "TOEIC", "토플", "JLPT", "영어", "점수"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_license": {
        "description": "자격증 정보",
        "columns": [
            "EMP_ID (FK)",
            "LICENSE_TYPE (자격구분: 국가자격,민간자격)",
            "LICENSE_NAME ★자격증명",
            "ISSUING_ORG (발급기관)",
            "ISSUE_DATE (취득일)",
            "VALIDITY_STATUS (유효상태: 유효,만료,영구)"
        ],
        "keywords": ["자격증", "자격", "면허", "취득", "보유"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_military": {
        "description": "병역 정보",
        "columns": [
            "EMP_ID (FK)",
            "MILITARY_TYPE (군종류: 육군,해군,공군)",
            "MILITARY_RANK (최종계급)",
            "SERVICE_STATUS (군필여부: 군필,미필,면제)",
            "DISCHARGE_DATE (전역일)"
        ],
        "keywords": ["병역", "군대", "군필", "전역", "군복무"],
        "join_key": "EMP_ID",
        "relation": "1:1",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_reward": {
        "description": "상벌 정보",
        "columns": [
            "EMP_ID (FK)",
            "REWARD_TYPE ★상벌구분 (포상,징계)",
            "REWARD_KIND (상벌종류)",
            "REWARD_REASON (사유)",
            "REWARD_DATE (일자)",
            "REWARD_AMOUNT (포상금액)"
        ],
        "keywords": ["상벌", "포상", "징계", "표창", "상금"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_training": {
        "description": "교육/훈련 이력",
        "columns": [
            "EMP_ID (FK)",
            "TRAINING_YEAR (교육연도)",
            "COURSE_NAME ★과정명",
            "INSTITUTION_NAME (교육기관)",
            "START_DATE (시작일)",
            "END_DATE (종료일)",
            "TRAINING_COST (교육비용)",
            "COMPLETION_STATUS (수료여부: 수료,미수료)"
        ],
        "keywords": ["교육", "훈련", "연수", "수료", "과정"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_feedback": {
        "description": "인사평가/직원평가 정보",
        "columns": [
            "EMP_ID (FK)",
            "APPR_NM ★평가명",
            "PEE_TYPE_NM (평가종류)",
            "EMP_ORG_NM (소속부서)",
            "APPR_SCORE ★평가점수",
            "APPR_GRADE ★평가등급 (S,A,B,C,D)",
            "PEE_OPINION (평가의견)",
            "APPR_YMD (평가일자)"
        ],
        "keywords": ["평가", "인사평가", "고과", "등급", "점수"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_pay_report": {
        "description": "급여 정보",
        "columns": [
            "EMPLOYEE_ID (FK, ★주의: EMP_ID 아님)",
            "EMPLOYEE_NAME (성명)",
            "PAY_YEAR (급여연도)",
            "PAY_YEAR_MONTH (급여년월)",
            "PAYMENT_TYPE_NAME (지급구분: 정기급여,상여)",
            "ORGANIZATION_NAME (소속)",
            "FIXED_PAY_AMOUNT (고정비)",
            "VARIABLE_PAY_AMOUNT (변동비)",
            "GROSS_PAY_AMOUNT ★지급합계",
            "DEDUCTION_AMOUNT (공제합계)",
            "NET_PAY_AMOUNT ★실지급액"
        ],
        "keywords": ["급여", "월급", "연봉", "지급", "실수령", "공제"],
        "join_key": "EMPLOYEE_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    },
    "v_ai_dtm_yy_rest": {
        "description": "년월차관리 (연차 발생/사용 정보)",
        "columns": [
            "LEAVE_ACCRUAL_ID (PK, 발생연차관리ID)",
            "EMPLOYEE_ID (FK, 사원ID)",
            "REFERENCE_YEAR ★기준년도",
            "LEAVE_TYPE_CODE (연차구분코드)",
            "ACCRUAL_DATE (발생일자)",
            "LEAVE_GRANT_RULE_CODE (연차부여기준코드)",
            "ACCRUED_LEAVE_DAYS ★발생연차일수",
            "ADDITIONAL_LEAVE_DAYS ★추가연차일수",
            "COMPENSATED_LEAVE_DAYS (보상연차)",
            "COMPENSATION_MONTH (보상적용월)",
            "COMPENSATED_LEAVE_DAYS_2 (보상연차2)",
            "COMPENSATION_MONTH_2 (보상적용월2)",
            "RETIREMENT_LEAVE_DAYS (퇴직연차)",
            "RETIREMENT_COMPENSATION_MONTH (퇴직보상적용월)",
            "USED_LEAVE_DAYS_PAST ★사용연차(과거)",
            "CARRIED_OVER_LEAVE_DAYS (이월연차/차년추가연차)",
            "REMARKS (비고)"
        ],
        "keywords": ["연차", "휴가", "발생연차", "사용연차", "추가연차", "이월", "보상연차", "퇴직연차", "년월차"],
        "join_key": "EMPLOYEE_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"]
    }
}',
    'json',
    'NL2SQL 테이블 카탈로그 (업체별 스키마 정의, JSON)',
    false
)
ON CONFLICT (category, key) DO UPDATE
SET value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = NOW();
