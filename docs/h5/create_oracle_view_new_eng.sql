-- ============================================================================
-- NL2SQL 최적화 Oracle View 생성 스크립트 (영문 컬럼명 버전)
-- 생성일: 2024
-- 목적: 자연어 질의를 SQL로 변환할 때 LLM이 정확한 SQL을 생성하도록 최적화
-- 주요 개선사항:
--   1. 영문 컬럼명 사용 (LLM이 테이블별칭과 컬럼명을 혼동하지 않음)
--   2. Y/N 코드를 의미있는 텍스트로 변환
--   3. 정규화: 각 뷰는 해당 도메인 정보만 포함 (JOIN으로 연결)
--   4. 뷰 이름 규칙: V_AI_[영문도메인명]
--   5. h522_rnd계정에서 view생성하고 muser 사용자에게 select 권한 부여
-- ============================================================================


-- ============================================================================
-- 1. V_AI_EMPLOYEE (사원 마스터 뷰)
-- 사원의 기본 인사정보를 담은 핵심 뷰 (마스터 테이블)
-- 다른 뷰와 JOIN 시 EMP_ID로 연결
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_EMPLOYEE AS
SELECT
    PE.EMP_ID                   AS EMP_ID,
    PN.KOR_NAME                 AS EMP_NAME,
    PN.ENG_NAME                 AS EMP_NAME_ENG,
    FC.CD_NM                    AS POSITION,
    PE.BIRTH_YMD                AS BIRTH_DATE,
    PE.CAREER_NUM               AS CAREER_MONTHS,
    TRUNC(PE.CAREER_NUM / 12)   AS CAREER_YEARS,
    FC3.CD_NM                   AS DUTY,
    PE.DUTY_YMD                 AS DUTY_DATE,
    FC4.CD_NM                   AS EMP_TYPE,
    FC5.CD_NM                   AS GENDER,
    PE.GROUP_YMD                AS GROUP_JOIN_DATE,
    FC6.CD_NM                   AS HIRE_TYPE,
    PE.HIRE_YMD                 AS HIRE_DATE,
    CASE PE.IN_OFFI_YN
        WHEN 'Y' THEN '재직'
        WHEN 'N' THEN '퇴직'
        ELSE PE.IN_OFFI_YN
    END                         AS WORK_STATUS,
    FC8.CD_NM                   AS GRADE,
    PE.POS_GRD_YMD              AS GRADE_DATE,
    FC9.CD_NM                   AS RETIRE_REASON,
    PE.RETIRE_YMD               AS RETIRE_DATE,
    FC10.CD_NM                  AS SALARY_STEP,
    PE.YEARNUM_YMD              AS SALARY_STEP_DATE
FROM PHM_EMP PE
LEFT JOIN (
    SELECT EMP_ID,
           MAX(CASE WHEN NAME_TYPE_CD = 'KOR' THEN LAST_NM END) AS KOR_NAME,
           MAX(CASE WHEN NAME_TYPE_CD = 'ENG' THEN LAST_NM END) AS ENG_NAME
    FROM PHM_NAME
    GROUP BY EMP_ID
) PN ON PN.EMP_ID = PE.EMP_ID
LEFT JOIN FRM_CODE FC ON FC.CD = PE.POS_CD AND FC.CD_KIND = 'PHM_POS_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PE.DUTY_CD AND FC3.CD_KIND = 'PHM_DUTY_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PE.EMP_KIND_CD AND FC4.CD_KIND = 'PHM_EMP_KIND_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PE.GENDER_CD AND FC5.CD_KIND = 'PHM_GENDER_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PE.HIRE_CD AND FC6.CD_KIND = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC8 ON FC8.CD = PE.POS_GRD_CD AND FC8.CD_KIND = 'PHM_POS_GRD_CD'
LEFT JOIN FRM_CODE FC9 ON FC9.CD = PE.RETIRE_TYPE_CD AND FC9.CD_KIND = 'CAM_CAU_CD'
LEFT JOIN FRM_CODE FC10 ON FC10.CD = PE.YEARNUM_CD AND FC10.CD_KIND = 'PHM_HOBONG';

COMMENT ON TABLE V_AI_EMPLOYEE IS '사원 기본 인사정보 마스터 - 입퇴사, 직위/직책/직급, 재직상태 등';
COMMENT ON COLUMN V_AI_EMPLOYEE.EMP_ID IS '사원 고유 식별 번호 (PK, 다른 뷰와 JOIN 키)';
COMMENT ON COLUMN V_AI_EMPLOYEE.EMP_NAME IS '사원 한글 이름';
COMMENT ON COLUMN V_AI_EMPLOYEE.EMP_NAME_ENG IS '사원 영문 이름';
COMMENT ON COLUMN V_AI_EMPLOYEE.POSITION IS '직위 (사원, 대리, 과장, 차장, 부장 등)';
COMMENT ON COLUMN V_AI_EMPLOYEE.BIRTH_DATE IS '생년월일';
COMMENT ON COLUMN V_AI_EMPLOYEE.CAREER_MONTHS IS '총 경력 개월 수';
COMMENT ON COLUMN V_AI_EMPLOYEE.CAREER_YEARS IS '총 경력 연수';
COMMENT ON COLUMN V_AI_EMPLOYEE.DUTY IS '직책 (팀장, 파트장 등)';
COMMENT ON COLUMN V_AI_EMPLOYEE.DUTY_DATE IS '직책 임명일';
COMMENT ON COLUMN V_AI_EMPLOYEE.EMP_TYPE IS '사원 유형 (정규직, 계약직 등)';
COMMENT ON COLUMN V_AI_EMPLOYEE.GENDER IS '성별 (남, 여)';
COMMENT ON COLUMN V_AI_EMPLOYEE.GROUP_JOIN_DATE IS '그룹 입사일';
COMMENT ON COLUMN V_AI_EMPLOYEE.HIRE_TYPE IS '입사 구분 (신입, 경력 등)';
COMMENT ON COLUMN V_AI_EMPLOYEE.HIRE_DATE IS '현 회사 입사일';
COMMENT ON COLUMN V_AI_EMPLOYEE.WORK_STATUS IS '재직 상태 (재직, 퇴직)';
COMMENT ON COLUMN V_AI_EMPLOYEE.GRADE IS '직급 (1급, 2급 등)';
COMMENT ON COLUMN V_AI_EMPLOYEE.GRADE_DATE IS '직급 승진일';
COMMENT ON COLUMN V_AI_EMPLOYEE.RETIRE_REASON IS '퇴직 사유';
COMMENT ON COLUMN V_AI_EMPLOYEE.RETIRE_DATE IS '퇴직일';
COMMENT ON COLUMN V_AI_EMPLOYEE.SALARY_STEP IS '급여 호봉';
COMMENT ON COLUMN V_AI_EMPLOYEE.SALARY_STEP_DATE IS '호봉 적용일';


-- ============================================================================
-- 2. V_AI_ADDRESS (사원 주소 뷰)
-- 사원별 주소 정보 (1:1 관계, 사원당 1개 주소)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_ADDRESS AS
SELECT
    PA.EMP_ID                   AS EMP_ID,
    PA.ADDR                     AS ADDRESS,
    PA.DETAIL_ADDR              AS ADDRESS_DETAIL,
    PA.ZIP_NO                   AS ZIP_CODE,
    CASE
        WHEN PA.ADDR LIKE '서울%' THEN '서울'
        WHEN PA.ADDR LIKE '부산%' THEN '부산'
        WHEN PA.ADDR LIKE '대구%' THEN '대구'
        WHEN PA.ADDR LIKE '인천%' THEN '인천'
        WHEN PA.ADDR LIKE '광주%' THEN '광주'
        WHEN PA.ADDR LIKE '대전%' THEN '대전'
        WHEN PA.ADDR LIKE '울산%' THEN '울산'
        WHEN PA.ADDR LIKE '세종%' THEN '세종'
        WHEN PA.ADDR LIKE '경기%' THEN '경기'
        WHEN PA.ADDR LIKE '강원%' THEN '강원'
        WHEN PA.ADDR LIKE '충북%' OR PA.ADDR LIKE '충청북%' THEN '충북'
        WHEN PA.ADDR LIKE '충남%' OR PA.ADDR LIKE '충청남%' THEN '충남'
        WHEN PA.ADDR LIKE '전북%' OR PA.ADDR LIKE '전라북%' THEN '전북'
        WHEN PA.ADDR LIKE '전남%' OR PA.ADDR LIKE '전라남%' THEN '전남'
        WHEN PA.ADDR LIKE '경북%' OR PA.ADDR LIKE '경상북%' THEN '경북'
        WHEN PA.ADDR LIKE '경남%' OR PA.ADDR LIKE '경상남%' THEN '경남'
        WHEN PA.ADDR LIKE '제주%' THEN '제주'
        ELSE '기타'
    END                         AS REGION,
    PA.MOD_DATE                 AS MOD_DATE
FROM PHM_ADDR PA;

COMMENT ON TABLE V_AI_ADDRESS IS '사원 주소 정보 (EMP_ID로 V_AI_EMPLOYEE와 JOIN)';
COMMENT ON COLUMN V_AI_ADDRESS.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_ADDRESS.ADDRESS IS '기본 주소';
COMMENT ON COLUMN V_AI_ADDRESS.ADDRESS_DETAIL IS '상세 주소';
COMMENT ON COLUMN V_AI_ADDRESS.ZIP_CODE IS '우편번호';
COMMENT ON COLUMN V_AI_ADDRESS.REGION IS '거주 시/도 (서울, 경기 등)';


-- ============================================================================
-- 3. V_AI_MILITARY (병역 정보 뷰)
-- 사원별 병역 정보 (1:1 관계)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_MILITARY AS
SELECT
    PA.EMP_ID                   AS EMP_ID,
    FC7.CD_NM                   AS MILITARY_TYPE,
    FC1.CD_NM                   AS MILITARY_BRANCH,
    FC2.CD_NM                   AS MILITARY_RANK,
    FC6.CD_NM                   AS SERVICE_TYPE,
    FC5.CD_NM                   AS SERVICE_STATUS,
    FC3.CD_NM                   AS DISCHARGE_TYPE,
    PA.OUT_YMD                  AS DISCHARGE_DATE,
    CASE
        WHEN PA.OUT_YMD IS NOT NULL THEN
            SUBSTR(PA.OUT_YMD, 1, 4)
        ELSE NULL
    END                         AS DISCHARGE_YEAR,
    FC4.CD_NM                   AS SPECIALTY,
    PA.ARMY_NO                  AS MILITARY_NO
FROM PHM_ARMY PA
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PA.ARMY_BRANCH_CD AND FC1.CD_KIND = 'PHM_ARMY_BRANCH_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PA.ARMY_CLASS_CD AND FC2.CD_KIND = 'PHM_ARMY_CLASS_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PA.ARMY_DISCHARGE_CD AND FC3.CD_KIND = 'PHM_ARMY_DISCHARGE_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PA.ARMY_MTALENT_CD AND FC4.CD_KIND = 'PHM_ARMY_MTALENT_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PA.ARMY_NO_REASON_CD AND FC5.CD_KIND = 'PHM_ARMY_NO_REASON_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PA.ARMY_SERV_CD AND FC6.CD_KIND = 'PHMARMY_SERV_CD'
LEFT JOIN FRM_CODE FC7 ON FC7.CD = PA.ARMY_TYPE_CD AND FC7.CD_KIND = 'PHM_ARMY_TYPE_CD';

COMMENT ON TABLE V_AI_MILITARY IS '사원 병역 정보 (EMP_ID로 V_AI_EMPLOYEE와 JOIN)';
COMMENT ON COLUMN V_AI_MILITARY.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_MILITARY.MILITARY_TYPE IS '군 종류 (육군, 해군, 공군, 해병대 등)';
COMMENT ON COLUMN V_AI_MILITARY.MILITARY_RANK IS '최종 계급 (병장, 상병 등)';
COMMENT ON COLUMN V_AI_MILITARY.SERVICE_STATUS IS '군필 여부 (군필, 미필, 면제 등)';
COMMENT ON COLUMN V_AI_MILITARY.DISCHARGE_YEAR IS '전역한 연도 (YYYY)';


-- ============================================================================
-- 4. V_AI_CAREER (경력 정보 뷰)
-- 사원별 이전 직장 경력 (1:N 관계, 사원당 여러 경력)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_CAREER AS
SELECT
    PC.EMP_ID                   AS EMP_ID,
    PC.ORG_CORP_NM              AS PREV_COMPANY,
    PC.PLACE_NM                 AS LOCATION,
    PC.POSITION_NM              AS PREV_POSITION,
    PC.RCAREER_NUM              AS WORK_MONTHS,
    TRUNC(PC.RCAREER_NUM / 12)  AS WORK_YEARS,
    PC.RECO_RATE                AS RECOGNITION_RATE,
    PC.RETIRE_CAUSE             AS LEAVE_REASON
FROM PHM_CAREER PC;

COMMENT ON TABLE V_AI_CAREER IS '사원 이전 직장 경력 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_CAREER.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_CAREER.PREV_COMPANY IS '이전에 근무한 회사명';
COMMENT ON COLUMN V_AI_CAREER.WORK_MONTHS IS '해당 직장 근무 개월 수';
COMMENT ON COLUMN V_AI_CAREER.WORK_YEARS IS '해당 직장 근무 연수';
COMMENT ON COLUMN V_AI_CAREER.RECOGNITION_RATE IS '경력 인정 비율 (%)';


-- ============================================================================
-- 5. V_AI_TRAINING (교육 이수 뷰)
-- 사원별 교육 이수 내역 (1:N 관계, 사원당 여러 교육)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_TRAINING AS
SELECT
    PED.EMP_ID                  AS EMP_ID,
    PED.EDU_YY                  AS TRAINING_YEAR,
    FC1.CD_NM                   AS COURSE_TYPE,
    FC2.CD_NM                   AS COURSE_GRADE,
    FC3.CD_NM                   AS COURSE_FIELD,
    PED.EDU_NM                  AS COURSE_NAME,
    FC4.CD_NM                   AS INSTITUTION_TYPE,
    PED.EDU_ORG_NM              AS INSTITUTION_NAME,
    FC5.CD_NM                   AS TRAINING_LOCATION,
    FC6.CD_NM                   AS TRAINING_TYPE,
    PED.STA_YMD                 AS START_DATE,
    PED.END_YMD                 AS END_DATE,
    PED.REAL_AMT                AS TRAINING_COST,
    PED.RESULT_PNT              AS COMPLETION_POINTS,
    PED.RESULT_TIMES            AS COMPLETION_HOURS,
    CASE PED.RESULT_YN
        WHEN 'Y' THEN '수료'
        WHEN 'N' THEN '미수료'
        ELSE PED.RESULT_YN
    END                         AS COMPLETION_STATUS,
    PED.RETURN_AMT              AS REFUND_AMOUNT
FROM PHM_EDU PED
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PED.EDU_CD AND FC1.CD_KIND = 'PHM_EDU_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PED.EDU_GRD_CD AND FC2.CD_KIND = 'PHM_EDU_GRD_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PED.EDU_KIND_CD AND FC3.CD_KIND = 'PHM_EDU_KIND_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PED.EDU_ORG_CD AND FC4.CD_KIND = 'PHM_EDU_ORG_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PED.EDU_PLA_CD AND FC5.CD_KIND = 'PHM_EDU_PLA_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PED.EDU_TYPE_CD AND FC6.CD_KIND = 'PHM_EDU_TYPE_CD';

COMMENT ON TABLE V_AI_TRAINING IS '사원 교육/연수 이수 내역 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_TRAINING.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_TRAINING.TRAINING_YEAR IS '교육 실시 연도';
COMMENT ON COLUMN V_AI_TRAINING.COURSE_NAME IS '교육 과정 이름';
COMMENT ON COLUMN V_AI_TRAINING.COMPLETION_HOURS IS '총 이수 시간';
COMMENT ON COLUMN V_AI_TRAINING.COMPLETION_STATUS IS '수료 여부 (수료, 미수료)';


-- ============================================================================
-- 6. V_AI_FAMILY (가족 정보 뷰)
-- 사원별 가족 구성원 (1:N 관계, 사원당 여러 가족)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_FAMILY AS
SELECT
    PF.EMP_ID                   AS EMP_ID,
    FC_REL.CD_NM                AS RELATION,
    PF.FAM_FIRST_NM             AS FAMILY_NAME,
    FC_GEN.CD_NM                AS FAMILY_GENDER,
    PF.BIRTH_YMD                AS FAMILY_BIRTH_DATE,
    PF.COMPANY_NM               AS FAMILY_COMPANY,
    PF.POSITION_NM              AS FAMILY_POSITION,
    PF.SCH_NM                   AS FAMILY_SCHOOL,
    CASE PF.HANICAP_YN
        WHEN 'Y' THEN '장애있음'
        WHEN 'N' THEN '장애없음'
        ELSE PF.HANICAP_YN
    END                         AS DISABILITY_STATUS,
    FC_HAN.CD_NM                AS DISABILITY_GRADE
FROM PHM_FAMILY PF
LEFT JOIN FRM_CODE FC_REL ON PF.FAM_REL_CD = FC_REL.CD AND FC_REL.CD_KIND = 'PHM_FAM_REL_CD'
LEFT JOIN FRM_CODE FC_GEN ON PF.GENDER_CD = FC_GEN.CD AND FC_GEN.CD_KIND = 'PHM_GENDER_CD'
LEFT JOIN FRM_CODE FC_HAN ON PF.HANDICAP_GRD_CD = FC_HAN.CD AND FC_HAN.CD_KIND = 'PHM_HANDICAP_GRD_CD';

COMMENT ON TABLE V_AI_FAMILY IS '사원 가족 구성원 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_FAMILY.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_FAMILY.RELATION IS '가족 관계 (배우자, 자녀, 부모 등)';
COMMENT ON COLUMN V_AI_FAMILY.FAMILY_NAME IS '가족 구성원 이름';
COMMENT ON COLUMN V_AI_FAMILY.DISABILITY_STATUS IS '장애 여부 (장애있음, 장애없음)';


-- ============================================================================
-- 7. V_AI_LANGUAGE (어학 성적 뷰)
-- 사원별 어학 시험 성적 (1:N 관계, 사원당 여러 어학성적)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_LANGUAGE AS
SELECT
    PL.EMP_ID                   AS EMP_ID,
    FC1.CD_NM                   AS LANGUAGE_TYPE,
    FC2.CD_NM                   AS EXAM_TYPE,
    FC4.CD_NM               AS EXAM_INSTITUTION,
    PL.EST_PNT                  AS SCORE,
    PL.EST_GRD_CD                   AS LANGUAGE_GRADE,
    PL.EST_YMD                  AS EXAM_DATE,
    CASE
        WHEN PL.EST_YMD IS NOT NULL THEN
            SUBSTR(PL.EST_YMD, 1, 4)
        ELSE NULL
    END                         AS EXAM_YEAR,
    PL.STD_YY                   AS EVALUATION_YEAR,
    PL.STD_SEQ                  AS EVALUATION_SEQ
FROM PHM_LANG_EST PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.LANG_CD AND FC1.CD_KIND = 'PHM_LANG_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.EST_CD AND FC2.CD_KIND = 'PHM_EST_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PL.EST_ORG_CD AND FC3.CD_KIND = 'REM_LANG_LEVEL_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PL.EST_ORG_CD AND FC4.CD_KIND = 'PHM_EST_ORG_CD';

COMMENT ON TABLE V_AI_LANGUAGE IS '사원 어학 시험 성적 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_LANGUAGE.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_LANGUAGE.LANGUAGE_TYPE IS '어학 종류 (영어, 일본어, 중국어 등)';
COMMENT ON COLUMN V_AI_LANGUAGE.EXAM_TYPE IS '시험 종류 (TOEIC, TOEFL, JLPT 등)';
COMMENT ON COLUMN V_AI_LANGUAGE.SCORE IS '어학 시험 점수';
COMMENT ON COLUMN V_AI_LANGUAGE.LANGUAGE_GRADE IS '어학 등급';
COMMENT ON COLUMN V_AI_LANGUAGE.EXAM_YEAR IS '시험 응시 연도 (YYYY)';



-- ============================================================================
-- 8. V_AI_LICENSE (자격증 정보 뷰)
-- 사원별 자격증 보유 현황 (1:N 관계, 사원당 여러 자격증)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_LICENSE AS
SELECT
    PL.EMP_ID                   AS EMP_ID,
    FC2.CD_NM                   AS LICENSE_TYPE,
    FC1.CD_NM                   AS LICENSE_NAME,
    PL.LICENSE_NO               AS LICENSE_NO,
    PL.ORG_NM                   AS ISSUING_ORG,
    PL.STA_YMD                  AS ISSUE_DATE,
    PL.END_YMD                  AS EXPIRY_DATE,
    CASE
        WHEN PL.END_YMD IS NOT NULL AND REGEXP_LIKE(PL.END_YMD, '^\d{8}$') AND PL.END_YMD < TO_CHAR(SYSDATE, 'YYYYMMDD') THEN '만료'
        WHEN PL.END_YMD IS NOT NULL AND REGEXP_LIKE(PL.END_YMD, '^\d{8}$') AND PL.END_YMD >= TO_CHAR(SYSDATE, 'YYYYMMDD') THEN '유효'
        WHEN PL.END_YMD IS NULL OR NOT REGEXP_LIKE(NVL(PL.END_YMD, ''), '^\d{8}$') THEN '영구'
        ELSE '확인필요'
    END                         AS VALIDITY_STATUS,
    PL.BONUS_TYPE               AS ALLOWANCE_TYPE
FROM PHM_LICENSE PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.LICENSE_CD AND FC1.CD_KIND = 'PHM_LICENSE_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.LICENSE_TYPE_CD AND FC2.CD_KIND = 'PHM_LICENSE_TYPE_CD';

COMMENT ON TABLE V_AI_LICENSE IS '사원 자격증/면허 보유 현황 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_LICENSE.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_LICENSE.LICENSE_TYPE IS '자격 구분 (국가자격, 민간자격 등)';
COMMENT ON COLUMN V_AI_LICENSE.LICENSE_NAME IS '자격증 이름';
COMMENT ON COLUMN V_AI_LICENSE.ISSUE_DATE IS '자격증 취득일';
COMMENT ON COLUMN V_AI_LICENSE.VALIDITY_STATUS IS '자격증 유효 상태 (유효, 만료, 영구)';


-- ============================================================================
-- 9. V_AI_EDUCATION (학력 정보 뷰)
-- 사원별 학력 정보 (1:N 관계, 사원당 여러 학력)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_EDUCATION AS
SELECT
    PS.EMP_ID                   AS EMP_ID,
    FC2.CD_NM                   AS SCHOOL_NAME,
    PS.SCH_PLACE_NM             AS SCHOOL_LOCATION,
    PS.MAJOR_NM                 AS MAJOR,
    PS.DOU_MAJOR_NM             AS DOUBLE_MAJOR,
    PS.SUB_MAJOR_NM             AS MINOR,
    PS.STA_YM                   AS ADMISSION_DATE,
    PS.END_YM                   AS GRADUATION_DATE,
    CASE
        WHEN PS.END_YM IS NOT NULL THEN
            SUBSTR(PS.END_YM, 1, 4)
        ELSE NULL
    END                         AS GRADUATION_YEAR
FROM PHM_SCHOLAR PS
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PS.SCH_CD AND FC2.CD_KIND = 'PHM_SCH_CD';

COMMENT ON TABLE V_AI_EDUCATION IS '사원 학력 정보 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_EDUCATION.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_EDUCATION.SCHOOL_NAME IS '졸업 학교명';
COMMENT ON COLUMN V_AI_EDUCATION.MAJOR IS '전공 학과명';
COMMENT ON COLUMN V_AI_EDUCATION.GRADUATION_YEAR IS '졸업 연도 (YYYY)';


-- ============================================================================
-- 10. V_AI_REWARD (상벌 정보 뷰)
-- 사원별 상벌 내역 (1:N 관계, 사원당 여러 상벌)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_REWARD AS
SELECT
    PM.EMP_ID                   AS EMP_ID,
    FC3.CD_NM                   AS REWARD_TYPE,
    FC2.CD_NM                   AS REWARD_KIND,
    PM.PPM_DESC                 AS REWARD_REASON,
    PM.PRIZE_DESC               AS REWARD_CONTENT,
    PM.PPM_YMD                  AS REWARD_DATE,
    CASE
        WHEN PM.PPM_YMD IS NOT NULL THEN
            SUBSTR(PM.PPM_YMD, 1, 4)
        ELSE NULL
    END                         AS REWARD_YEAR,
    PM.PPM_ORG_NM               AS AWARDING_ORG,
    PM.PPM_MON                  AS REWARD_AMOUNT,
    PM.PPM_NO                   AS REWARD_NO
FROM PPM_MNT PM
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PM.KIND_CD AND FC2.CD_KIND = 'PPM_KIND_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PM.TYPE_CD AND FC3.CD_KIND = 'PPM_TYPE_CD';

COMMENT ON TABLE V_AI_REWARD IS '사원 상벌 내역 (EMP_ID로 V_AI_EMPLOYEE와 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_REWARD.EMP_ID IS '사원 고유 식별 번호 (FK → V_AI_EMPLOYEE)';
COMMENT ON COLUMN V_AI_REWARD.REWARD_TYPE IS '상벌 구분 (포상, 징계)';
COMMENT ON COLUMN V_AI_REWARD.REWARD_KIND IS '상벌 종류';
COMMENT ON COLUMN V_AI_REWARD.REWARD_YEAR IS '상벌 발생 연도 (YYYY)';
COMMENT ON COLUMN V_AI_REWARD.REWARD_AMOUNT IS '포상금 금액';


-- ============================================================================
-- 뷰 관계 다이어그램 (ERD)
-- ============================================================================
--
--                          ┌───────────────┐
--                          │ V_AI_EMPLOYEE │ (마스터)
--                          │    EMP_ID     │
--                          └───────┬───────┘
--                                  │
--       ┌──────────┬───────────┬───┴───┬───────────┬───────────┬───────────┐
--       │          │           │       │           │           │           │
--       ▼          ▼           ▼       ▼           ▼           ▼           ▼
--  ┌─────────┐ ┌─────────┐ ┌───────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
--  │V_AI_    │ │V_AI_    │ │V_AI_  │ │V_AI_    │ │V_AI_    │ │V_AI_    │ │V_AI_    │
--  │ADDRESS  │ │MILITARY │ │CAREER │ │TRAINING │ │LANGUAGE │ │LICENSE  │ │EDUCATION│
--  │ (1:1)   │ │ (1:1)   │ │(1:N)  │ │ (1:N)   │ │ (1:N)   │ │ (1:N)   │ │ (1:N)   │
--  └─────────┘ └─────────┘ └───────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
--       ┌─────────┐
--       │V_AI_    │
--       │FAMILY   │
--       │ (1:N)   │
--       └─────────┘
--       ┌─────────┐
--       │V_AI_    │
--       │REWARD   │
--       │ (1:N)   │
--       └─────────┘
--
-- ============================================================================


-- ============================================================================
-- NL2SQL 시스템 설정 가이드
-- ============================================================================
--
-- Admin UI → Settings → NL2SQL 에서 아래 설정 권장:
--
-- 1. Allowed Tables (허용 테이블):
--    V_AI_EMPLOYEE, V_AI_ADDRESS, V_AI_MILITARY, V_AI_CAREER, V_AI_TRAINING,
--    V_AI_FAMILY, V_AI_LANGUAGE, V_AI_LICENSE, V_AI_EDUCATION, V_AI_REWARD
--
-- 2. Schema Description (스키마 설명):
--    - V_AI_EMPLOYEE: 사원 마스터 (기본정보, 입퇴사, 직위/직책/직급, 재직상태)
--    - V_AI_ADDRESS: 사원 주소 (REGION=거주지역 포함)
--    - V_AI_MILITARY: 병역 정보 (군별, 계급, 군필구분)
--    - V_AI_CAREER: 이전 직장 경력
--    - V_AI_TRAINING: 교육/연수 이수 내역
--    - V_AI_FAMILY: 가족 구성원 정보
--    - V_AI_LANGUAGE: 어학 시험 성적 (TOEIC 등)
--    - V_AI_LICENSE: 자격증 보유 현황
--    - V_AI_EDUCATION: 학력 정보 (학교, 전공)
--    - V_AI_REWARD: 포상/징계 내역
--
-- 3. JOIN 관계 설명 (프롬프트에 포함):
--    - 모든 뷰는 EMP_ID로 V_AI_EMPLOYEE와 JOIN 가능
--    - 1:1 관계: V_AI_ADDRESS, V_AI_MILITARY
--    - 1:N 관계: V_AI_CAREER, V_AI_TRAINING, V_AI_FAMILY, V_AI_LANGUAGE, V_AI_LICENSE, V_AI_EDUCATION, V_AI_REWARD
--
-- ============================================================================


-- ============================================================================
-- NL2SQL 질문 및 SQL 매핑 예시
-- ============================================================================
--
-- [단일 테이블 질의]
--
-- Q: "2008년 입사자 수는?"
-- A: SELECT COUNT(*) AS CNT FROM V_AI_EMPLOYEE WHERE HIRE_DATE LIKE '2024%'
--
-- Q: "재직중인 과장 목록"
-- A: SELECT EMP_ID, EMP_NAME, POSITION FROM V_AI_EMPLOYEE WHERE WORK_STATUS = '재직' AND POSITION = '과장'
--
-- Q: "남자 직원 수"
-- A: SELECT COUNT(*) AS CNT FROM V_AI_EMPLOYEE WHERE GENDER = '남'
--
--
-- [JOIN 질의 - 주소]
--
-- Q: "서울 사는 직원 수는?"
-- A: SELECT COUNT(DISTINCT E.EMP_ID) AS CNT
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_ADDRESS A ON E.EMP_ID = A.EMP_ID
--    WHERE A.REGION = '서울'
--
-- Q: "경기도에 사는 재직중인 과장 목록"
-- A: SELECT E.EMP_NAME, E.POSITION, A.ADDRESS
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_ADDRESS A ON E.EMP_ID = A.EMP_ID
--    WHERE A.REGION = '경기' AND E.WORK_STATUS = '재직' AND E.POSITION = '과장'
--
--
-- [JOIN 질의 - 어학/자격증]
--
-- Q: "TOEIC 900점 이상인 직원"
-- A: SELECT DISTINCT E.EMP_NAME, L.SCORE
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_LANGUAGE L ON E.EMP_ID = L.EMP_ID
--    WHERE L.EXAM_TYPE = 'TOEIC' AND L.SCORE >= 900
--
-- Q: "정보처리기사 자격증 보유자 수"
-- A: SELECT COUNT(DISTINCT E.EMP_ID) AS CNT
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_LICENSE C ON E.EMP_ID = C.EMP_ID
--    WHERE C.LICENSE_NAME LIKE '%정보처리기사%'
--
--
-- [JOIN 질의 - 학력]
--
-- Q: "서울대 출신 직원 목록"
-- A: SELECT DISTINCT E.EMP_NAME, S.SCHOOL_NAME, S.MAJOR
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_EDUCATION S ON E.EMP_ID = S.EMP_ID
--    WHERE S.SCHOOL_NAME LIKE '%서울대%'
--
--
-- [복합 JOIN 질의]
--
-- Q: "서울 사는 TOEIC 800점 이상 과장"
-- A: SELECT DISTINCT E.EMP_NAME, E.POSITION, A.REGION, L.SCORE
--    FROM V_AI_EMPLOYEE E
--    JOIN V_AI_ADDRESS A ON E.EMP_ID = A.EMP_ID
--    JOIN V_AI_LANGUAGE L ON E.EMP_ID = L.EMP_ID
--    WHERE A.REGION = '서울'
--      AND E.POSITION = '과장'
--      AND L.EXAM_TYPE = 'TOEIC'
--      AND L.SCORE >= 800
--
-- ============================================================================


-- ============================================================================
-- H522_RND 계정에서 MUSER에게 SELECT 권한 부여
-- (H522_RND 계정으로 실행)
-- ============================================================================

-- 영문 뷰 권한 부여
GRANT SELECT ON H552_RND.V_AI_EMPLOYEE TO MUSER;
GRANT SELECT ON H552_RND.V_AI_ADDRESS TO MUSER;
GRANT SELECT ON H552_RND.V_AI_MILITARY TO MUSER;
GRANT SELECT ON H552_RND.V_AI_CAREER TO MUSER;
GRANT SELECT ON H552_RND.V_AI_TRAINING TO MUSER;
GRANT SELECT ON H552_RND.V_AI_FAMILY TO MUSER;
GRANT SELECT ON H552_RND.V_AI_LANGUAGE TO MUSER;
GRANT SELECT ON H552_RND.V_AI_LICENSE TO MUSER;
GRANT SELECT ON H552_RND.V_AI_EDUCATION TO MUSER;
GRANT SELECT ON H552_RND.V_AI_REWARD TO MUSER;


-- ============================================================================
-- MUSER 계정에서 시노님(SYNONYM) 생성
-- (MUSER 계정으로 실행)
-- ============================================================================

-- 영문 뷰 시노님 생성
CREATE OR REPLACE SYNONYM V_AI_EMPLOYEE FOR H552_RND.V_AI_EMPLOYEE;
CREATE OR REPLACE SYNONYM V_AI_ADDRESS FOR H525_RND.V_AI_ADDRESS;
CREATE OR REPLACE SYNONYM V_AI_MILITARY FOR H552_RND.V_AI_MILITARY;
CREATE OR REPLACE SYNONYM V_AI_CAREER FOR H552_RND.V_AI_CAREER;
CREATE OR REPLACE SYNONYM V_AI_TRAINING FOR H552_RND.V_AI_TRAINING;
CREATE OR REPLACE SYNONYM V_AI_FAMILY FOR H552_RND.V_AI_FAMILY;
CREATE OR REPLACE SYNONYM V_AI_LANGUAGE FOR H552_RND.V_AI_LANGUAGE;
CREATE OR REPLACE SYNONYM V_AI_LICENSE FOR H552_RND.V_AI_LICENSE;
CREATE OR REPLACE SYNONYM V_AI_EDUCATION FOR H552_RND.V_AI_EDUCATION;
CREATE OR REPLACE SYNONYM V_AI_REWARD FOR H552_RND.V_AI_REWARD;



-- ============================================================================
-- 시노님 생성 확인 (MUSER 계정에서 실행)
-- ============================================================================

-- 생성된 시노님 목록 확인
-- SELECT SYNONYM_NAME, TABLE_OWNER, TABLE_NAME
-- FROM USER_SYNONYMS
-- WHERE SYNONYM_NAME LIKE 'V_AI_%';

-- 조회 테스트
-- SELECT COUNT(*) FROM V_AI_EMPLOYEE;
-- SELECT * FROM V_AI_EMPLOYEE WHERE ROWNUM <= 5;


-- ============================================================================
-- 실행 순서 요약
-- ============================================================================
--
-- [STEP 1] H522_RND 계정 접속
--   - 위의 CREATE VIEW 문 실행 (10개 뷰 생성)
--   - GRANT SELECT 문 실행 (MUSER에게 권한 부여)
--
-- [STEP 2] MUSER 계정 접속
--   - CREATE OR REPLACE SYNONYM 문 실행 (10개 시노님 생성)
--   - 조회 테스트: SELECT * FROM V_AI_EMPLOYEE;
--
-- ============================================================================
