-- ============================================================================
-- NL2SQL 최적화 Oracle View 생성 스크립트 (정규화 버전)
-- 생성일: 2024
-- 목적: 자연어 질의를 SQL로 변환할 때 LLM이 쉽게 이해할 수 있도록 최적화
-- 주요 개선사항:
--   1. 한글 컬럼명 사용 (LLM의 자연어-SQL 매핑 용이)
--   2. Y/N 코드를 의미있는 텍스트로 변환
--   3. 정규화: 각 뷰는 해당 도메인 정보만 포함 (JOIN으로 연결)
--   4. 뷰 이름 규칙: V_AI_[도메인명]
--   5. h522_rnd계정에서 view생성하고 muser 사용자에게 select 권한 부여(muser에서는 시노님 생성한 view조회 가능)
-- ============================================================================


-- ============================================================================
-- 1. V_AI_사원 (Employee Master View)
-- 사원의 기본 인사정보를 담은 핵심 뷰 (마스터 테이블)
-- 다른 뷰와 JOIN 시 사원번호로 연결
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_사원 AS
SELECT
    PE.EMP_ID                   AS 사원번호,
    PN.KOR_NAME                 AS 사원명,
    PN.ENG_NAME                 AS 영문명,
    FC.CD_NM                    AS 직위,
    PE.BIRTH_YMD                AS 생년월일,
    PE.CAREER_NUM               AS 경력개월수,
    TRUNC(PE.CAREER_NUM / 12)   AS 경력연수,
    FC3.CD_NM                   AS 직책,
    PE.DUTY_YMD                 AS 직책임명일,
    FC4.CD_NM                   AS 사원유형,
    FC5.CD_NM                   AS 성별,
    PE.GROUP_YMD                AS 그룹입사일,
    FC6.CD_NM                   AS 입사구분,
    PE.HIRE_YMD                 AS 입사일,
    CASE PE.IN_OFFI_YN
        WHEN 'Y' THEN '재직'
        WHEN 'N' THEN '퇴직'
        ELSE PE.IN_OFFI_YN
    END                         AS 재직상태,
    FC8.CD_NM                   AS 직급,
    PE.POS_GRD_YMD              AS 직급승진일,
    FC9.CD_NM                   AS 퇴직사유,
    PE.RETIRE_YMD               AS 퇴직일,
    FC10.CD_NM                  AS 호봉,
    PE.YEARNUM_YMD              AS 호봉적용일
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

COMMENT ON TABLE V_AI_사원 IS '사원 기본 인사정보 마스터 - 입퇴사, 직위/직책/직급, 재직상태 등';
COMMENT ON COLUMN V_AI_사원.사원번호 IS '사원 고유 식별 번호 (PK, 다른 뷰와 JOIN 키)';
COMMENT ON COLUMN V_AI_사원.사원명 IS '사원 한글 이름';
COMMENT ON COLUMN V_AI_사원.영문명 IS '사원 영문 이름';
COMMENT ON COLUMN V_AI_사원.직위 IS '직위 (사원, 대리, 과장, 차장, 부장 등)';
COMMENT ON COLUMN V_AI_사원.생년월일 IS '생년월일';
COMMENT ON COLUMN V_AI_사원.경력개월수 IS '총 경력 개월 수';
COMMENT ON COLUMN V_AI_사원.경력연수 IS '총 경력 연수';
COMMENT ON COLUMN V_AI_사원.직책 IS '직책 (팀장, 파트장 등)';
COMMENT ON COLUMN V_AI_사원.직책임명일 IS '직책 임명일';
COMMENT ON COLUMN V_AI_사원.사원유형 IS '사원 유형 (정규직, 계약직 등)';
COMMENT ON COLUMN V_AI_사원.성별 IS '성별 (남, 여)';
COMMENT ON COLUMN V_AI_사원.그룹입사일 IS '그룹 입사일';
COMMENT ON COLUMN V_AI_사원.입사구분 IS '입사 구분 (신입, 경력 등)';
COMMENT ON COLUMN V_AI_사원.입사일 IS '현 회사 입사일';
COMMENT ON COLUMN V_AI_사원.재직상태 IS '재직 상태 (재직, 퇴직)';
COMMENT ON COLUMN V_AI_사원.직급 IS '직급 (1급, 2급 등)';
COMMENT ON COLUMN V_AI_사원.직급승진일 IS '직급 승진일';
COMMENT ON COLUMN V_AI_사원.퇴직사유 IS '퇴직 사유';
COMMENT ON COLUMN V_AI_사원.퇴직일 IS '퇴직일';
COMMENT ON COLUMN V_AI_사원.호봉 IS '급여 호봉';
COMMENT ON COLUMN V_AI_사원.호봉적용일 IS '호봉 적용일';


-- ============================================================================
-- 2. V_AI_사원주소 (Employee Address View)
-- 사원별 주소 정보 (1:1 관계, 사원당 1개 주소)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_사원주소 AS
SELECT
    PA.EMP_ID                   AS 사원번호,
    PA.ADDR                     AS 주소,
    PA.DETAIL_ADDR              AS 상세주소,
    PA.ZIP_NO                   AS 우편번호,
    -- 주소에서 시/도 추출 (NL2SQL 편의)
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
    END                         AS 거주지역,
    PA.MOD_DATE                 AS 수정일시
FROM PHM_ADDR PA;

COMMENT ON TABLE V_AI_사원주소 IS '사원 주소 정보 (사원번호로 V_AI_사원과 JOIN)';
COMMENT ON COLUMN V_AI_사원주소.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_사원주소.주소 IS '기본 주소';
COMMENT ON COLUMN V_AI_사원주소.상세주소 IS '상세 주소';
COMMENT ON COLUMN V_AI_사원주소.우편번호 IS '우편번호';
COMMENT ON COLUMN V_AI_사원주소.거주지역 IS '거주 시/도 (서울, 경기 등)';


-- ============================================================================
-- 3. V_AI_병역 (Military Service View)
-- 사원별 병역 정보 (1:1 관계)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_병역 AS
SELECT
    PA.EMP_ID                   AS 사원번호,
    FC7.CD_NM                   AS 군별,
    FC1.CD_NM                   AS 병과,
    FC2.CD_NM                   AS 계급,
    FC6.CD_NM                   AS 복무형태,
    FC5.CD_NM                   AS 군필구분,
    FC3.CD_NM                   AS 전역구분,
    PA.OUT_YMD                  AS 전역일,
    CASE
        WHEN PA.OUT_YMD IS NOT NULL THEN
            SUBSTR(PA.OUT_YMD, 1, 4)
        ELSE NULL
    END                         AS 전역년도,
    FC4.CD_NM                   AS 주특기,
    PA.ARMY_NO                  AS 군번
FROM PHM_ARMY PA
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PA.ARMY_BRANCH_CD AND FC1.CD_KIND = 'PHM_ARMY_BRANCH_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PA.ARMY_CLASS_CD AND FC2.CD_KIND = 'PHM_ARMY_CLASS_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PA.ARMY_DISCHARGE_CD AND FC3.CD_KIND = 'PHM_ARMY_DISCHARGE_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PA.ARMY_MTALENT_CD AND FC4.CD_KIND = 'PHM_ARMY_MTALENT_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PA.ARMY_NO_REASON_CD AND FC5.CD_KIND = 'PHM_ARMY_NO_REASON_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PA.ARMY_SERV_CD AND FC6.CD_KIND = 'PHMARMY_SERV_CD'
LEFT JOIN FRM_CODE FC7 ON FC7.CD = PA.ARMY_TYPE_CD AND FC7.CD_KIND = 'PHM_ARMY_TYPE_CD';

COMMENT ON TABLE V_AI_병역 IS '사원 병역 정보 (사원번호로 V_AI_사원과 JOIN)';
COMMENT ON COLUMN V_AI_병역.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_병역.군별 IS '군 종류 (육군, 해군, 공군, 해병대 등)';
COMMENT ON COLUMN V_AI_병역.계급 IS '최종 계급 (병장, 상병 등)';
COMMENT ON COLUMN V_AI_병역.군필구분 IS '군필 여부 (군필, 미필, 면제 등)';
COMMENT ON COLUMN V_AI_병역.전역년도 IS '전역한 연도 (YYYY)';


-- ============================================================================
-- 4. V_AI_경력 (Career History View)
-- 사원별 이전 직장 경력 (1:N 관계, 사원당 여러 경력)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_경력 AS
SELECT
    PC.EMP_ID                   AS 사원번호,
    PC.ORG_CORP_NM              AS 이전직장명,
    PC.PLACE_NM                 AS 소재지,
    PC.POSITION_NM              AS 이전직위,
    PC.RCAREER_NUM              AS 근무개월,
    TRUNC(PC.RCAREER_NUM / 12)  AS 근무연수,
    PC.RECO_RATE                AS 경력인정률,
    PC.RETIRE_CAUSE             AS 퇴사사유
FROM PHM_CAREER PC;

COMMENT ON TABLE V_AI_경력 IS '사원 이전 직장 경력 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_경력.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_경력.이전직장명 IS '이전에 근무한 회사명';
COMMENT ON COLUMN V_AI_경력.근무개월 IS '해당 직장 근무 개월 수';
COMMENT ON COLUMN V_AI_경력.근무연수 IS '해당 직장 근무 연수';
COMMENT ON COLUMN V_AI_경력.경력인정률 IS '경력 인정 비율 (%)';


-- ============================================================================
-- 5. V_AI_교육이수 (Education/Training View)
-- 사원별 교육 이수 내역 (1:N 관계, 사원당 여러 교육)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_교육이수 AS
SELECT
    PED.EMP_ID                  AS 사원번호,
    PED.EDU_YY                  AS 교육년도,
    FC1.CD_NM                   AS 교육과정,
    FC2.CD_NM                   AS 교육등급,
    FC3.CD_NM                   AS 교육분야,
    PED.EDU_NM                  AS 교육과정명,
    FC4.CD_NM                   AS 교육기관구분,
    PED.EDU_ORG_NM              AS 교육기관명,
    FC5.CD_NM                   AS 교육장소,
    FC6.CD_NM                   AS 교육유형,
    PED.STA_YMD                 AS 시작일,
    PED.END_YMD                 AS 종료일,
    PED.REAL_AMT                AS 교육비,
    PED.RESULT_PNT              AS 이수포인트,
    PED.RESULT_TIMES            AS 이수시간,
    CASE PED.RESULT_YN
        WHEN 'Y' THEN '수료'
        WHEN 'N' THEN '미수료'
        ELSE PED.RESULT_YN
    END                         AS 수료여부,
    PED.RETURN_AMT              AS 환급금
FROM PHM_EDU PED
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PED.EDU_CD AND FC1.CD_KIND = 'PHM_EDU_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PED.EDU_GRD_CD AND FC2.CD_KIND = 'PHM_EDU_GRD_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PED.EDU_KIND_CD AND FC3.CD_KIND = 'PHM_EDU_KIND_CD'
LEFT JOIN FRM_CODE FC4 ON FC4.CD = PED.EDU_ORG_CD AND FC4.CD_KIND = 'PHM_EDU_ORG_CD'
LEFT JOIN FRM_CODE FC5 ON FC5.CD = PED.EDU_PLA_CD AND FC5.CD_KIND = 'PHM_EDU_PLA_CD'
LEFT JOIN FRM_CODE FC6 ON FC6.CD = PED.EDU_TYPE_CD AND FC6.CD_KIND = 'PHM_EDU_TYPE_CD';

COMMENT ON TABLE V_AI_교육이수 IS '사원 교육/연수 이수 내역 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_교육이수.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_교육이수.교육년도 IS '교육 실시 연도';
COMMENT ON COLUMN V_AI_교육이수.교육과정명 IS '교육 과정 이름';
COMMENT ON COLUMN V_AI_교육이수.이수시간 IS '총 이수 시간';
COMMENT ON COLUMN V_AI_교육이수.수료여부 IS '수료 여부 (수료, 미수료)';


-- ============================================================================
-- 6. V_AI_가족 (Family Member View)
-- 사원별 가족 구성원 (1:N 관계, 사원당 여러 가족)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_가족 AS
SELECT
    PF.EMP_ID                   AS 사원번호,
    FC_REL.CD_NM                AS 가족관계,
    PF.FAM_FIRST_NM             AS 가족성명,
    FC_GEN.CD_NM                AS 가족성별,
    PF.BIRTH_YMD                AS 가족생년월일,
    PF.COMPANY_NM               AS 가족직장,
    PF.POSITION_NM              AS 가족직위,
    PF.SCH_NM                   AS 가족학교,
    CASE PF.HANICAP_YN
        WHEN 'Y' THEN '장애있음'
        WHEN 'N' THEN '장애없음'
        ELSE PF.HANICAP_YN
    END                         AS 장애여부,
    FC_HAN.CD_NM                AS 장애등급
FROM PHM_FAMILY PF
LEFT JOIN FRM_CODE FC_REL ON PF.FAM_REL_CD = FC_REL.CD AND FC_REL.CD_KIND = 'PHM_FAM_REL_CD'
LEFT JOIN FRM_CODE FC_GEN ON PF.GENDER_CD = FC_GEN.CD AND FC_GEN.CD_KIND = 'PHM_GENDER_CD'
LEFT JOIN FRM_CODE FC_HAN ON PF.HANDICAP_GRD_CD = FC_HAN.CD AND FC_HAN.CD_KIND = 'PHM_HANDICAP_GRD_CD';

COMMENT ON TABLE V_AI_가족 IS '사원 가족 구성원 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_가족.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_가족.가족관계 IS '가족 관계 (배우자, 자녀, 부모 등)';
COMMENT ON COLUMN V_AI_가족.가족성명 IS '가족 구성원 이름';
COMMENT ON COLUMN V_AI_가족.장애여부 IS '장애 여부 (장애있음, 장애없음)';


-- ============================================================================
-- 7. V_AI_어학성적 (Language Assessment View)
-- 사원별 어학 시험 성적 (1:N 관계, 사원당 여러 어학성적)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_어학성적 AS
SELECT
    PL.EMP_ID                   AS 사원번호,
    FC1.CD_NM                   AS 어학종류,
    FC3.CD_NM                   AS 시험종류,
    PL.EST_ORG_NM               AS 시험기관명,
    PL.EST_PNT                  AS 점수,
    FC2.CD_NM                   AS 어학등급,
    PL.EST_YMD                  AS 취득일,
    CASE
        WHEN PL.EST_YMD IS NOT NULL THEN
            SUBSTR(PL.EST_YMD, 1, 4)
        ELSE NULL
    END                         AS 취득년도,
    PL.STD_YY                   AS 평가년도,
    PL.STD_SEQ                  AS 평가차수
FROM PHM_LANG_EST PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.EST_CD AND FC1.CD_KIND = 'PHM_EST_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.EST_GRD_CD AND FC2.CD_KIND = 'PHM_EST_GRD_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PL.EST_ORG_CD AND FC3.CD_KIND = 'PHM_EST_ORG_CD';

COMMENT ON TABLE V_AI_어학성적 IS '사원 어학 시험 성적 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_어학성적.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_어학성적.어학종류 IS '어학 종류 (영어, 일본어, 중국어 등)';
COMMENT ON COLUMN V_AI_어학성적.시험종류 IS '시험 종류 (TOEIC, TOEFL, JLPT 등)';
COMMENT ON COLUMN V_AI_어학성적.점수 IS '어학 시험 점수';
COMMENT ON COLUMN V_AI_어학성적.어학등급 IS '어학 등급';
COMMENT ON COLUMN V_AI_어학성적.취득년도 IS '시험 응시 연도 (YYYY)';


-- ============================================================================
-- 8. V_AI_자격증 (License/Certification View)
-- 사원별 자격증 보유 현황 (1:N 관계, 사원당 여러 자격증)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_자격증 AS
SELECT
    PL.EMP_ID                   AS 사원번호,
    FC2.CD_NM                   AS 자격구분,
    FC1.CD_NM                   AS 자격증명,
    PL.LICENSE_NO               AS 자격증번호,
    PL.ORG_NM                   AS 발급기관,
    PL.STA_YMD                  AS 취득일,
    PL.END_YMD                  AS 유효기간,
    CASE
        WHEN PL.END_YMD IS NOT NULL AND REGEXP_LIKE(PL.END_YMD, '^\d{8}$') AND PL.END_YMD < TO_CHAR(SYSDATE, 'YYYYMMDD') THEN '만료'
        WHEN PL.END_YMD IS NOT NULL AND REGEXP_LIKE(PL.END_YMD, '^\d{8}$') AND PL.END_YMD >= TO_CHAR(SYSDATE, 'YYYYMMDD') THEN '유효'
        WHEN PL.END_YMD IS NULL OR NOT REGEXP_LIKE(NVL(PL.END_YMD, ''), '^\d{8}$') THEN '영구'
        ELSE '확인필요'
    END                         AS 유효상태,
    PL.BONUS_TYPE               AS 수당지급구분
FROM PHM_LICENSE PL
LEFT JOIN FRM_CODE FC1 ON FC1.CD = PL.LICENSE_CD AND FC1.CD_KIND = 'PHM_LICENSE_CD'
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PL.LICENSE_TYPE_CD AND FC2.CD_KIND = 'PHM_LICENSE_TYPE_CD';

COMMENT ON TABLE V_AI_자격증 IS '사원 자격증/면허 보유 현황 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_자격증.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_자격증.자격구분 IS '자격 구분 (국가자격, 민간자격 등)';
COMMENT ON COLUMN V_AI_자격증.자격증명 IS '자격증 이름';
COMMENT ON COLUMN V_AI_자격증.취득일 IS '자격증 취득일';
COMMENT ON COLUMN V_AI_자격증.유효상태 IS '자격증 유효 상태 (유효, 만료, 영구)';


-- ============================================================================
-- 9. V_AI_학력 (Education Background View)
-- 사원별 학력 정보 (1:N 관계, 사원당 여러 학력)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_학력 AS
SELECT
    PS.EMP_ID                   AS 사원번호,
    FC2.CD_NM                   AS 학교명,
    PS.SCH_PLACE_NM             AS 학교소재지,
    PS.MAJOR_NM                 AS 전공,
    PS.DOU_MAJOR_NM             AS 복수전공,
    PS.SUB_MAJOR_NM             AS 부전공,
    PS.STA_YM                   AS 입학년월,
    PS.END_YM                   AS 졸업년월,
    CASE
        WHEN PS.END_YM IS NOT NULL THEN
            SUBSTR(PS.END_YM, 1, 4)
        ELSE NULL
    END                         AS 졸업년도
FROM PHM_SCHOLAR PS
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PS.SCH_CD AND FC2.CD_KIND = 'PHM_SCH_CD';

COMMENT ON TABLE V_AI_학력 IS '사원 학력 정보 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_학력.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_학력.학교명 IS '졸업 학교명';
COMMENT ON COLUMN V_AI_학력.전공 IS '전공 학과명';
COMMENT ON COLUMN V_AI_학력.졸업년도 IS '졸업 연도 (YYYY)';


-- ============================================================================
-- 10. V_AI_상벌 (Rewards & Penalties View)
-- 사원별 상벌 내역 (1:N 관계, 사원당 여러 상벌)
-- ============================================================================

CREATE OR REPLACE VIEW V_AI_상벌 AS
SELECT
    PM.EMP_ID                   AS 사원번호,
    FC3.CD_NM                   AS 상벌구분,
    FC2.CD_NM                   AS 상벌종류,
    PM.PPM_DESC                 AS 상벌사유,
    PM.PRIZE_DESC               AS 상벌내용,
    PM.PPM_YMD                  AS 상벌일,
    CASE
        WHEN PM.PPM_YMD IS NOT NULL THEN
            SUBSTR(PM.PPM_YMD, 1, 4)
        ELSE NULL
    END                         AS 상벌년도,
    PM.PPM_ORG_NM               AS 시상기관,
    PM.PPM_MON                  AS 포상금액,
    PM.PPM_NO                   AS 상벌번호
FROM PPM_MNT PM
LEFT JOIN FRM_CODE FC2 ON FC2.CD = PM.KIND_CD AND FC2.CD_KIND = 'PPM_KIND_CD'
LEFT JOIN FRM_CODE FC3 ON FC3.CD = PM.TYPE_CD AND FC3.CD_KIND = 'PPM_TYPE_CD';

COMMENT ON TABLE V_AI_상벌 IS '사원 상벌 내역 (사원번호로 V_AI_사원과 JOIN, 1:N)';
COMMENT ON COLUMN V_AI_상벌.사원번호 IS '사원 고유 식별 번호 (FK → V_AI_사원)';
COMMENT ON COLUMN V_AI_상벌.상벌구분 IS '상벌 구분 (포상, 징계)';
COMMENT ON COLUMN V_AI_상벌.상벌종류 IS '상벌 종류';
COMMENT ON COLUMN V_AI_상벌.상벌년도 IS '상벌 발생 연도 (YYYY)';
COMMENT ON COLUMN V_AI_상벌.포상금액 IS '포상금 금액';


-- ============================================================================
-- 뷰 관계 다이어그램 (ERD)
-- ============================================================================
--
--                          ┌─────────────┐
--                          │  V_AI_사원   │ (마스터)
--                          │  사원번호   │
--                          └──────┬──────┘
--                                 │
--       ┌──────────┬──────────┬───┴───┬──────────┬──────────┬──────────┐
--       │          │          │       │          │          │          │
--       ▼          ▼          ▼       ▼          ▼          ▼          ▼
--  ┌─────────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────┐ ┌──────┐
--  │V_AI_사원 │ │V_AI_병역│ │VAI_  │ │VAI_  │ │VAI_어학│ │VAI_  │ │VAI_  │
--  │  주소   │ │        │ │ 경력 │ │교육  │ │ 성적   │ │자격증│ │ 학력 │
--  │ (1:1)  │ │ (1:1)  │ │(1:N) │ │이수  │ │ (1:N)  │ │(1:N) │ │(1:N) │
--  └─────────┘ └────────┘ └──────┘ │(1:N) │ └────────┘ └──────┘ └──────┘
--                                  └──────┘
--       ┌──────────┐
--       │V_AI_가족  │
--       │ (1:N)    │
--       └──────────┘
--       ┌──────────┐
--       │V_AI_상벌  │
--       │ (1:N)    │
--       └──────────┘
--
-- ============================================================================


-- ============================================================================
-- NL2SQL 시스템 설정 가이드
-- ============================================================================
--
-- Admin UI → Settings → NL2SQL 에서 아래 설정 권장:
--
-- 1. Allowed Tables (허용 테이블):
--    V_AI_사원, V_AI_사원주소, V_AI_병역, V_AI_경력, V_AI_교육이수,
--    V_AI_가족, V_AI_어학성적, V_AI_자격증, V_AI_학력, V_AI_상벌
--
-- 2. Schema Description (스키마 설명):
--    - V_AI_사원: 사원 마스터 (기본정보, 입퇴사, 직위/직책/직급, 재직상태)
--    - V_AI_사원주소: 사원 주소 (거주지역 포함)
--    - V_AI_병역: 병역 정보 (군별, 계급, 군필구분)
--    - V_AI_경력: 이전 직장 경력
--    - V_AI_교육이수: 교육/연수 이수 내역
--    - V_AI_가족: 가족 구성원 정보
--    - V_AI_어학성적: 어학 시험 성적 (TOEIC 등)
--    - V_AI_자격증: 자격증 보유 현황
--    - V_AI_학력: 학력 정보 (학교, 전공)
--    - V_AI_상벌: 포상/징계 내역
--
-- 3. JOIN 관계 설명 (프롬프트에 포함):
--    - 모든 뷰는 사원번호로 V_AI_사원과 JOIN 가능
--    - 1:1 관계: V_AI_사원주소, V_AI_병역
--    - 1:N 관계: V_AI_경력, V_AI_교육이수, V_AI_가족, V_AI_어학성적, V_AI_자격증, V_AI_학력, V_AI_상벌
--
-- ============================================================================


-- ============================================================================
-- NL2SQL 질문 및 SQL 매핑 예시
-- ============================================================================
--
-- [단일 테이블 질의]
--
-- Q: "2024년 입사자 수는?"
-- A: SELECT COUNT(*) AS 입사자수 FROM V_AI_사원 WHERE 입사일 LIKE '2024%'
--
-- Q: "재직중인 과장 목록"
-- A: SELECT 사원번호, 사원명, 직위 FROM V_AI_사원 WHERE 재직상태 = '재직' AND 직위 = '과장'
--
-- Q: "남자 직원 수"
-- A: SELECT COUNT(*) AS 남자직원수 FROM V_AI_사원 WHERE 성별 = '남'
--
--
-- [JOIN 질의 - 주소]
--
-- Q: "서울 사는 직원 수는?"
-- A: SELECT COUNT(DISTINCT E.사원번호) AS 직원수
--    FROM V_AI_사원 E
--    JOIN V_AI_사원주소 A ON E.사원번호 = A.사원번호
--    WHERE A.거주지역 = '서울'
--
-- Q: "경기도에 사는 재직중인 과장 목록"
-- A: SELECT E.사원명, E.직위, A.주소
--    FROM V_AI_사원 E
--    JOIN V_AI_사원주소 A ON E.사원번호 = A.사원번호
--    WHERE A.거주지역 = '경기' AND E.재직상태 = '재직' AND E.직위 = '과장'
--
--
-- [JOIN 질의 - 어학/자격증]
--
-- Q: "TOEIC 900점 이상인 직원"
-- A: SELECT DISTINCT E.사원명, L.점수
--    FROM V_AI_사원 E
--    JOIN V_AI_어학성적 L ON E.사원번호 = L.사원번호
--    WHERE L.시험종류 = 'TOEIC' AND L.점수 >= 900
--
-- Q: "정보처리기사 자격증 보유자 수"
-- A: SELECT COUNT(DISTINCT E.사원번호) AS 보유자수
--    FROM V_AI_사원 E
--    JOIN V_AI_자격증 C ON E.사원번호 = C.사원번호
--    WHERE C.자격증명 LIKE '%정보처리기사%'
--
--
-- [JOIN 질의 - 학력]
--
-- Q: "서울대 출신 직원 목록"
-- A: SELECT DISTINCT E.사원명, S.학교명, S.전공
--    FROM V_AI_사원 E
--    JOIN V_AI_학력 S ON E.사원번호 = S.사원번호
--    WHERE S.학교명 LIKE '%서울대%'
--
--
-- [복합 JOIN 질의]
--
-- Q: "서울 사는 TOEIC 800점 이상 과장"
-- A: SELECT DISTINCT E.사원명, E.직위, A.거주지역, L.점수
--    FROM V_AI_사원 E
--    JOIN V_AI_사원주소 A ON E.사원번호 = A.사원번호
--    JOIN V_AI_어학성적 L ON E.사원번호 = L.사원번호
--    WHERE A.거주지역 = '서울'
--      AND E.직위 = '과장'
--      AND L.시험종류 = 'TOEIC'
--      AND L.점수 >= 800
--
-- ============================================================================


-- ============================================================================
-- H522_RND 계정에서 MUSER에게 SELECT 권한 부여
-- (H522_RND 계정으로 실행)
-- ============================================================================

-- V_AI_사원 뷰 권한 부여
GRANT SELECT ON H552_RND.V_AI_사원 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_사원주소 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_병역 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_경력 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_교육이수 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_가족 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_어학성적 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_자격증 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_학력 TO MUSER;
GRANT SELECT ON H552_RND.V_AI_상벌 TO MUSER;


-- ============================================================================
-- MUSER 계정에서 시노님(SYNONYM) 생성
-- (MUSER 계정으로 실행)
-- ============================================================================

-- 기존 시노님이 있으면 삭제 후 재생성
-- DROP SYNONYM V_AI_사원;
-- DROP SYNONYM V_AI_사원주소;
-- DROP SYNONYM V_AI_병역;
-- DROP SYNONYM V_AI_경력;
-- DROP SYNONYM V_AI_교육이수;
-- DROP SYNONYM V_AI_가족;
-- DROP SYNONYM V_AI_어학성적;
-- DROP SYNONYM V_AI_자격증;
-- DROP SYNONYM V_AI_학력;
-- DROP SYNONYM V_AI_상벌;

-- 시노님 생성 (MUSER 계정에서 실행)
CREATE OR REPLACE SYNONYM V_AI_사원 FOR H552_RND.V_AI_사원;
CREATE OR REPLACE SYNONYM V_AI_사원주소 FOR H552_RND.V_AI_사원주소;
CREATE OR REPLACE SYNONYM V_AI_병역 FOR H552_RND.V_AI_병역;
CREATE OR REPLACE SYNONYM V_AI_경력 FOR H552_RND.V_AI_경력;
CREATE OR REPLACE SYNONYM V_AI_교육이수 FOR H552_RND.V_AI_교육이수;
CREATE OR REPLACE SYNONYM V_AI_가족 FOR H552_RND.V_AI_가족;
CREATE OR REPLACE SYNONYM V_AI_어학성적 FOR H552_RND.V_AI_어학성적;
CREATE OR REPLACE SYNONYM V_AI_자격증 FOR H552_RND.V_AI_자격증;
CREATE OR REPLACE SYNONYM V_AI_학력 FOR H552_RND.V_AI_학력;
CREATE OR REPLACE SYNONYM V_AI_상벌 FOR H552_RND.V_AI_상벌;


-- ============================================================================
-- 시노님 생성 확인 (MUSER 계정에서 실행)
-- ============================================================================

-- 생성된 시노님 목록 확인
-- SELECT SYNONYM_NAME, TABLE_OWNER, TABLE_NAME
-- FROM USER_SYNONYMS
-- WHERE SYNONYM_NAME LIKE 'V_AI_%';

-- 조회 테스트
-- SELECT COUNT(*) FROM V_AI_사원;
-- SELECT * FROM V_AI_사원 WHERE ROWNUM <= 5;


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
--   - 조회 테스트: SELECT * FROM V_AI_사원;
--
-- ============================================================================
