-- =============================================================
-- NL2SQL Few-shot 전체 재생성 SQL
-- 생성일: 2026-03-18
-- 대상: hermesdb.tb_docs
-- 설계문서: docs/sql/fewshot/fewshot_design.md
-- 총 47건 (14개 뷰 커버 + 복합 패턴 10건)
-- =============================================================

-- ① 기존 few-shot 전건 삭제
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action';


-- =============================================================
-- 01. V_AI_EMPLOYEE — 직원 기본정보 (8건)
-- =============================================================

-- #1 현재 재직자 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '현재 재직자 수 조회', 'query_example', 'ko',
'현재 재직 중인 직원 수
전체 재직자 몇 명
현재 근무 중인 사원 수
회사 전체 인원
우리 회사 직원 몇 명이야
- WORK_STATUS = 재직 조건 필수
- 특별한 언급 없으면 재직자만 대상',
'SQL:
SELECT COUNT(*) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''

패턴:
- 재직자 기본조건: WORK_STATUS = ''재직''
- 특별한 언급 없으면 재직자만 대상
- "퇴직자 포함", "퇴직 인원" 명시 시에만 조건 변경 ("전체 직원", "전체 인원" 표현은 재직자만)');

-- #2 부서별 직원 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 직원 수 조회', 'query_example', 'ko',
'부서별 직원 수를 알려줘
팀별 인원 현황
각 부서에 몇 명이 있어
조직별 재직자 수
부서 인원 분포
- DEPARTMENT 기준 GROUP BY
- 인원 순 내림차순 정렬',
'SQL:
SELECT DEPARTMENT, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY DEPARTMENT
ORDER BY emp_count DESC

패턴:
- GROUP BY DEPARTMENT로 부서별 그룹화
- ORDER BY emp_count DESC로 인원 많은 순 정렬
- 재직자 조건 필수');

-- #3 직위별 직원 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직위별 직원 수 조회', 'query_example', 'ko',
'직위별 사원 수를 알려줘
직급별 직원 수 현황
사원 대리 과장 차장 부장 인원
직위 분포
- POSITION 기준 GROUP BY
- 직위 순서대로 정렬 (사원→부장→회장)',
'SQL:
SELECT POSITION, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY POSITION
ORDER BY
    CASE POSITION
        WHEN ''사원'' THEN 1 WHEN ''대리'' THEN 2
        WHEN ''과장'' THEN 3 WHEN ''차장'' THEN 4
        WHEN ''부장'' THEN 5 WHEN ''이사'' THEN 6
        WHEN ''전무이사'' THEN 7 WHEN ''사장'' THEN 8
        WHEN ''회장'' THEN 9 ELSE 10
    END

패턴:
- CASE WHEN으로 직위 순서 정렬
- 주의: GRADE(직급 1급~9급)와 POSITION(직위 사원~회장)은 다름');

-- #4 성별 직원 비율 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '성별 직원 비율 조회', 'query_example', 'ko',
'성별 직원 수를 알려줘
남녀 비율
남자 여자 직원 몇 명
성별 인원 현황
- GENDER 기준 GROUP BY
- 비율 계산 포함',
'SQL:
SELECT GENDER, COUNT(*) AS emp_count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
GROUP BY GENDER
ORDER BY GENDER

패턴:
- GENDER: 남, 여
- 비율 계산: SUM(COUNT(*)) OVER() 윈도우 함수
- ROUND로 소수점 1자리');

-- #5 연도별 입사자 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '연도별 입사자 수 조회', 'query_example', 'ko',
'2024년 입사자 수를 알려줘
올해 입사한 직원 몇 명
작년 신규 입사자 수
특정 연도 입사 인원
- HIRE_DATE 기준 연도별 집계
- 입사 인원수 집계(COUNT) 시 재직 조건 불필요',
'SQL:
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, ''YYYY'') = '':년도''

패턴:
- 연도 추출: TO_CHAR(HIRE_DATE, ''YYYY'')
- 입사 인원수 집계(COUNT) 시 WORK_STATUS 조건 불필요 (입사 시점 분석)
- HIRE_DATE는 NOT NULL');

-- #6 연도별 퇴사자 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '연도별 퇴사자 수 조회', 'query_example', 'ko',
'올해 퇴사자 수를 알려줘
퇴직한 직원 몇 명
작년 퇴사 인원
퇴직자 현황
- RETIRE_DATE 기준 연도별 집계
- RETIRE_DATE IS NOT NULL 필수',
'SQL:
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, ''YYYY'') = '':년도''

패턴:
- RETIRE_DATE IS NOT NULL 조건 필수
- 퇴직 인원수 집계(COUNT) 시 WORK_STATUS 조건 불필요 (퇴직 시점 분석)
- 재직자의 RETIRE_DATE는 NULL');

-- #7 연령대별 직원 분포 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '연령대별 직원 분포 조회', 'query_example', 'ko',
'연령대별 직원 수를 알려줘
나이대별 사원이 몇 명
20대 30대 40대 각각 몇 명이야
직원들의 연령대 분포
세대별 직원 수 분포
- BIRTH_DATE 기준 MONTHS_BETWEEN 계산
- CASE WHEN 구간별 그룹화',
'SQL:
SELECT age_group, employee_count
FROM (
    SELECT
        CASE
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN ''20대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN ''30대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN ''40대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN ''50대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN ''60대 이상''
            ELSE ''기타''
        END AS age_group,
        COUNT(*) AS employee_count
    FROM v_ai_employee
    WHERE WORK_STATUS = ''재직'' AND BIRTH_DATE IS NOT NULL
    GROUP BY
        CASE
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN ''20대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN ''30대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN ''40대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN ''50대''
            WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN ''60대 이상''
            ELSE ''기타''
        END
)
ORDER BY CASE age_group
    WHEN ''20대'' THEN 1 WHEN ''30대'' THEN 2 WHEN ''40대'' THEN 3
    WHEN ''50대'' THEN 4 WHEN ''60대 이상'' THEN 5 ELSE 6
END

패턴:
- 나이 계산: TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12)
- CASE WHEN 구간: 서브쿼리로 감싸서 alias ORDER BY 가능
- BIRTH_DATE IS NOT NULL 필수');

-- #8 근속연수 구간별 직원 분포
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '근속연수 구간별 직원 분포', 'query_example', 'ko',
'근속연수 구간별 인원 분포
근속 5년 이상 직원 수
장기 근속자 몇 명
근속연수별 직원 현황
1년 미만 신입 몇 명이야
- CAREER_YEARS 기준 구간 분류
- CASE WHEN 구간별 GROUP BY',
'SQL:
SELECT tenure_group, employee_count
FROM (
    SELECT
        CASE
            WHEN CAREER_YEARS < 1 THEN ''1년 미만''
            WHEN CAREER_YEARS BETWEEN 1 AND 2 THEN ''1~3년''
            WHEN CAREER_YEARS BETWEEN 3 AND 4 THEN ''3~5년''
            WHEN CAREER_YEARS BETWEEN 5 AND 9 THEN ''5~10년''
            WHEN CAREER_YEARS >= 10 THEN ''10년 이상''
        END AS tenure_group,
        COUNT(*) AS employee_count
    FROM v_ai_employee
    WHERE WORK_STATUS = ''재직''
    GROUP BY
        CASE
            WHEN CAREER_YEARS < 1 THEN ''1년 미만''
            WHEN CAREER_YEARS BETWEEN 1 AND 2 THEN ''1~3년''
            WHEN CAREER_YEARS BETWEEN 3 AND 4 THEN ''3~5년''
            WHEN CAREER_YEARS BETWEEN 5 AND 9 THEN ''5~10년''
            WHEN CAREER_YEARS >= 10 THEN ''10년 이상''
        END
)
ORDER BY CASE tenure_group
    WHEN ''1년 미만'' THEN 1 WHEN ''1~3년'' THEN 2 WHEN ''3~5년'' THEN 3
    WHEN ''5~10년'' THEN 4 WHEN ''10년 이상'' THEN 5
END

패턴:
- CAREER_YEARS: 재직연수 (자동 계산 컬럼)
- CASE WHEN 구간: 서브쿼리로 감싸서 alias ORDER BY 가능
- 특정 구간만 필요시: WHERE CAREER_YEARS >= 5');


-- =============================================================
-- 02. V_AI_ADDRESS — 현재 거주지 (2건)
-- =============================================================

-- #9 특정 지역 거주 직원 수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 지역 거주 직원 수 조회', 'query_example', 'ko',
'서울에 사는 직원 몇 명
경기도 거주자 수
부산 지역 직원 현황
특정 시도 거주 재직자
- v_ai_address JOIN (1:1 관계)
- REGION으로 지역 필터',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND a.REGION = '':지역''

패턴:
- v_ai_address는 1:1 관계 (JOIN 가능)
- REGION 값: 서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주,기타');

-- #10 지역별 직원 분포 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '지역별 직원 분포 조회', 'query_example', 'ko',
'지역별 인원 분포
시도별 직원 수
거주지별 사원 현황
어디에 많이 살아
- v_ai_address JOIN
- REGION GROUP BY',
'SQL:
SELECT a.REGION, COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_address a ON e.EMP_ID = a.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY a.REGION
ORDER BY emp_count DESC

패턴:
- GROUP BY REGION으로 지역별 분포
- v_ai_address는 1:1 관계 (JOIN 가능, 중복 없음)');


-- =============================================================
-- 03. V_AI_CAREER — 이전 직장 경력 (2건)
-- =============================================================

-- #11 이전 경력 보유 직원 수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '이전 경력 보유 직원 수 조회', 'query_example', 'ko',
'경력직 출신 직원 수
이전 회사 경력 있는 사원
전직장 경험자 몇 명
경력 입사자 수
- v_ai_career (1:N 관계) EXISTS 사용
- 경력 유무만 확인할 때',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_career c WHERE c.EMP_ID = e.EMP_ID
  )

패턴:
- 1:N 관계에서 존재 여부만 확인: EXISTS 사용
- JOIN 대신 EXISTS로 중복 방지
- 특정 회사 출신: AND c.PREV_COMPANY LIKE ''%회사명%'' 추가');

-- #12 전직장 다수 경력자 목록
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '전직장 다수 경력자 목록 조회', 'query_example', 'ko',
'전직장 3곳 이상인 직원
이직 경험 많은 사원
전직장 많은 직원 목록
경력이 다양한 직원
- v_ai_career JOIN + GROUP BY
- HAVING으로 N건 이상 필터',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, COUNT(*) AS career_count
FROM v_ai_employee e
JOIN v_ai_career c ON e.EMP_ID = c.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY career_count DESC
FETCH FIRST 20 ROWS ONLY

패턴:
- HAVING COUNT(*) >= N: 그룹별 조건 필터
- GROUP BY에 EMP_ID 포함 필수 (동명이인 구분)
- FETCH FIRST N ROWS ONLY: 상위 N건 제한');


-- =============================================================
-- 04. V_AI_SCHOLAR — 학력 정보 (2건)
-- =============================================================

-- #13 학력별 직원 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '학력별 직원 수 조회', 'query_example', 'ko',
'대졸 이상 직원 수
학력별 인원 현황
석사 박사 몇 명
고졸 직원 수
- v_ai_scholar (1:N) EXISTS 사용
- EDUCATION_LEVEL로 학력 필터',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_scholar s
    WHERE s.EMP_ID = e.EMP_ID
      AND s.EDUCATION_LEVEL IN (''대졸'', ''석사'', ''박사'')
  )

패턴:
- EDUCATION_LEVEL: 고졸, 전문대졸, 대졸, 석사, 박사 등
- 1:N 관계: EXISTS로 중복 방지
- 대졸 이상: IN (''대졸'', ''석사'', ''박사'')');

-- #14 특정 전공자 목록 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 전공자 목록 조회', 'query_example', 'ko',
'컴퓨터공학 전공자 수
경영학과 출신 직원
특정 전공 직원 목록
전공별 인원
- v_ai_scholar JOIN
- MAJOR_NAME LIKE 검색',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, s.SCHOOL_NAME, s.MAJOR_NAME
FROM v_ai_employee e
JOIN v_ai_scholar s ON e.EMP_ID = s.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND s.MAJOR_NAME LIKE ''%'' || '':전공'' || ''%''
ORDER BY e.EMP_NAME
FETCH FIRST 20 ROWS ONLY

패턴:
- MAJOR_NAME LIKE: 전공명 부분 매칭
- SCHOOL_NAME: 학교명
- 상세 정보 필요 시 JOIN 사용 (1:N이므로 여러 행 가능)');


-- =============================================================
-- 05. V_AI_FAMILY — 가족 정보 (2건)
-- =============================================================

-- #15 배우자 보유 직원 수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '배우자 보유 직원 수 조회', 'query_example', 'ko',
'배우자가 있는 직원 수
기혼자 몇 명
결혼한 사원 수
기혼 직원 현황
- v_ai_family (1:N) EXISTS 사용
- RELATION으로 가족 관계 필터',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN (''배우자'', ''처'', ''남편'')
  )

패턴:
- RELATION: 배우자, 처, 남편, 자녀, 부, 모 등
- 자녀 조건: RELATION = ''자녀''
- DISABILITY_STATUS: 장애있음, 장애없음');

-- #16 자녀 다수 보유 직원 목록
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '자녀 다수 보유 직원 목록 조회', 'query_example', 'ko',
'자녀 2명 이상 직원
자녀가 많은 사원 목록
다자녀 직원 수
자녀 수별 직원 현황
- v_ai_family JOIN + GROUP BY
- HAVING으로 자녀 수 필터',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, COUNT(*) AS child_count
FROM v_ai_employee e
JOIN v_ai_family f ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND f.RELATION = ''자녀''
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT
HAVING COUNT(*) >= 2
ORDER BY child_count DESC

패턴:
- HAVING COUNT(*) >= N: 자녀 N명 이상
- GROUP BY에 EMP_ID 포함 필수');


-- =============================================================
-- 06. V_AI_LANGUAGE — 어학 성적 (2건)
-- =============================================================

-- #17 어학 점수 조건 직원 수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '어학 점수 조건 직원 수 조회', 'query_example', 'ko',
'TOEIC 800점 이상인 직원 수
영어 점수 높은 사원
토익 점수 조건
어학 성적 우수자
- v_ai_language (1:N) EXISTS 사용
- EXAM_TYPE으로 시험 종류, SCORE로 점수 조건',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = ''TOEIC''
      AND l.SCORE >= 800
  )

패턴:
- EXAM_TYPE: TOEIC, TOEFL, JLPT 등 (시험 종류)
- LANGUAGE_TYPE: 영어, 일본어, 중국어 등 (어학 종류) — EXAM_TYPE과 다름
- SCORE: 시험 점수
- 주의: LANGUAGE_GRADE 컬럼은 존재하지 않음. 평가유형은 EVAL_METHOD 사용');

-- #18 시험종류별 평균 점수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '시험종류별 평균 점수 조회', 'query_example', 'ko',
'어학 시험별 평균 점수
토익 평균 점수
시험 종류별 성적 현황
어학 통계
- v_ai_language 단독
- EXAM_TYPE GROUP BY + AVG(SCORE)',
'SQL:
SELECT l.EXAM_TYPE, ROUND(AVG(l.SCORE), 1) AS avg_score,
       COUNT(*) AS exam_count, COUNT(DISTINCT l.EMP_ID) AS emp_count
FROM v_ai_language l
JOIN v_ai_employee e ON l.EMP_ID = e.EMP_ID
WHERE l.SCORE > 0
  AND e.WORK_STATUS = ''재직''
GROUP BY l.EXAM_TYPE
ORDER BY avg_score DESC

패턴:
- JOIN v_ai_employee: 재직자만 대상 (퇴직자 제외)
- AVG(SCORE): 평균 점수
- SCORE > 0: 유효 점수만
- COUNT(DISTINCT EMP_ID): 응시 직원 수 (1인 다건 가능)');


-- =============================================================
-- 07. V_AI_LICENSE — 자격증 (2건)
-- =============================================================

-- #19 자격증 보유자 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '자격증 보유자 수 조회', 'query_example', 'ko',
'정보처리기사 자격증 보유자 수
특정 자격증 보유 직원 몇 명
자격증 있는 사원
국가자격 보유자
- v_ai_license (1:N) EXISTS 사용
- LICENSE_NAME LIKE로 자격증명 검색',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LICENSE_NAME LIKE ''%'' || '':자격증명'' || ''%''
  )

패턴:
- LICENSE_NAME LIKE: 자격증명 부분 매칭
- LICENSE_TYPE: 국가자격, 민간자격
- VALIDITY_STATUS: 유효, 만료, 영구');

-- #20 자격증 다수 보유자 목록
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '자격증 다수 보유자 목록 조회', 'query_example', 'ko',
'자격증 3개 이상 보유 직원
자격증 많이 가진 사원
자격증 보유 순위
자격증 개수별 직원 목록
- v_ai_license JOIN + GROUP BY
- HAVING으로 보유 건수 필터',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, COUNT(*) AS license_count
FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
HAVING COUNT(*) >= 3
ORDER BY license_count DESC

패턴:
- HAVING COUNT(*) >= N: N건 이상 보유자
- 전체 자격증 순위: HAVING 없이 ORDER BY license_count DESC');


-- =============================================================
-- 08. V_AI_MILITARY — 병역 정보 (1건)
-- =============================================================

-- #21 군종별 직원 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '군종별 직원 수 조회', 'query_example', 'ko',
'육군 출신 직원 몇 명
군종별 인원 현황
해군 공군 육군 직원
병역 이행 현황
군필 직원 수
- v_ai_military (1:1) JOIN 가능
- MILITARY_TYPE으로 군종 필터',
'SQL:
SELECT m.MILITARY_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_military m ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND m.MILITARY_TYPE IS NOT NULL
GROUP BY m.MILITARY_TYPE
ORDER BY emp_count DESC

패턴:
- v_ai_military: 1:1 관계 (JOIN 가능)
- MILITARY_TYPE: 육군, 해군, 공군, 해병대 등
- SERVICE_STATUS: 군필, 미필, 면제 등
- MILITARY_RANK: 병장, 상병 등 최종 계급');


-- =============================================================
-- 09. V_AI_REWARD — 상벌 내역 (2건)
-- =============================================================

-- #22 포상 직원 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '포상 직원 수 조회', 'query_example', 'ko',
'포상 받은 직원 수
상 받은 사원 몇 명
우수사원 현황
징계 이력 있는 직원
- v_ai_reward (1:N) EXISTS 사용
- REWARD_TYPE으로 포상/징계 구분',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = ''포상''
  )

패턴:
- REWARD_TYPE: 포상, 징계
- REWARD_KIND: 상벌 종류
- REWARD_AMOUNT: 포상금액
- 징계 조회 시: REWARD_TYPE = ''징계''');

-- #23 연도별 포상 건수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '연도별 포상 건수 조회', 'query_example', 'ko',
'올해 포상 현황
연도별 포상 건수
포상 추이
올해 상 받은 사람 몇 명
- v_ai_reward 단독
- REWARD_YEAR GROUP BY',
'SQL:
SELECT REWARD_YEAR, COUNT(*) AS reward_count,
       COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_reward
WHERE REWARD_TYPE = ''포상''
GROUP BY REWARD_YEAR
ORDER BY REWARD_YEAR DESC

패턴:
- REWARD_YEAR: 상벌 연도 (YYYY)
- COUNT(*): 포상 총 건수
- COUNT(DISTINCT EMP_ID): 포상 받은 직원 수 (1인 다건 가능)');


-- =============================================================
-- 10. V_AI_TRAINING — 교육/연수 (2건)
-- =============================================================

-- #24 교육 수료자 수 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '교육 수료자 수 조회', 'query_example', 'ko',
'올해 교육 수료한 직원 수
교육 이수자 몇 명
교육 과정 완료한 직원
연수 이수 현황
- v_ai_training (1:N) EXISTS 사용
- COMPLETION_STATUS = 수료, TRAINING_YEAR 필터',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = '':년도''
      AND t.COMPLETION_STATUS = ''수료''
  )

패턴:
- TRAINING_YEAR: 교육 연도
- COMPLETION_STATUS: 수료, 미수료
- COURSE_NAME: 교육 과정명');

-- #25 부서별 교육시간 합계
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 교육시간 합계 조회', 'query_example', 'ko',
'부서별 교육시간 합계
부서별 1인당 교육시간
교육 이수시간 통계
부서별 교육 현황
- v_ai_employee JOIN v_ai_training
- GROUP BY DEPARTMENT + SUM/AVG',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)), 1) AS total_hours,
       ROUND(SUM(NVL(t.COMPLETION_HOURS, 0)) / NULLIF(COUNT(DISTINCT e.EMP_ID), 0), 1) AS avg_hours_per_person
FROM v_ai_employee e
JOIN v_ai_training t ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND t.COMPLETION_STATUS = ''수료''
GROUP BY e.DEPARTMENT
ORDER BY total_hours DESC

패턴:
- COMPLETION_HOURS: 이수 시간
- NVL(값, 0): NULL 방어
- NULLIF(값, 0): 0으로 나누기 방어
- 1인당 평균: SUM / COUNT(DISTINCT EMP_ID)');


-- =============================================================
-- 11. V_AI_FEEDBACK — 인사평가 (3건)
-- =============================================================

-- #26 평가등급 분포 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '평가등급 분포 조회', 'query_example', 'ko',
'평가등급 분포
등급별 직원 수
S등급 몇 명
A등급 직원 수
평가결과 현황
인사평가 등급별 인원
- v_ai_feedback 단독
- APPR_GRADE GROUP BY + 비율',
'SQL:
SELECT f.APPR_GRADE, COUNT(DISTINCT f.EMP_ID) AS emp_count,
       ROUND(COUNT(DISTINCT f.EMP_ID) * 100.0 / SUM(COUNT(DISTINCT f.EMP_ID)) OVER(), 1) AS percentage
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE f.APPR_GRADE IS NOT NULL
  AND TO_CHAR(f.END_YMD, ''YYYY'') = '':년도''
  AND e.WORK_STATUS = ''재직''
GROUP BY f.APPR_GRADE
ORDER BY CASE f.APPR_GRADE
    WHEN ''S'' THEN 1 WHEN ''A'' THEN 2 WHEN ''B'' THEN 3
    WHEN ''C'' THEN 4 WHEN ''D'' THEN 5 ELSE 6
END

패턴:
- JOIN v_ai_employee: 재직자만 대상 (퇴직자 제외)
- APPR_GRADE: S, A, B, C, D 등급
- COUNT(DISTINCT EMP_ID): 1인 다건 평가 가능 → 직원 수 기준
- END_YMD: 평가 종료일 (연도 필터 기준)
- APPR_SCORE: 평가 점수');

-- #27 특정 직원 평가 이력 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 직원 평가 이력 조회', 'query_example', 'ko',
'홍길동 평가 기록
직원 평가 이력
인사평가 결과 확인
평가 점수 확인
특정 사원 평가 조회
- v_ai_employee JOIN v_ai_feedback
- EMP_NAME 검색 + 최신순 정렬',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       f.APPR_NM, f.APPR_GRADE, f.APPR_SCORE, f.APPR_YMD
FROM v_ai_employee e
JOIN v_ai_feedback f ON e.EMP_ID = f.EMP_ID
WHERE e.EMP_NAME LIKE ''%'' || '':이름'' || ''%''
ORDER BY f.APPR_YMD DESC

패턴:
- EMP_NAME LIKE: 이름 부분 매칭
- ORDER BY APPR_YMD DESC: 최신 평가 우선
- APPR_NM: 평가명 (연간인사평가 등)');

-- #28 부서별 평균 평가점수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 평균 평가점수 조회', 'query_example', 'ko',
'부서별 평균 평가점수
부서 평가 현황
부서별 평가 통계
어떤 부서가 평가 잘 받아
- v_ai_employee JOIN v_ai_feedback
- GROUP BY DEPARTMENT + AVG(APPR_SCORE)',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(f.APPR_SCORE), 1) AS avg_score
FROM v_ai_employee e
JOIN v_ai_feedback f ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND f.APPR_SCORE > 0
GROUP BY e.DEPARTMENT
ORDER BY avg_score DESC

패턴:
- AVG(APPR_SCORE): 평균 평가점수
- APPR_SCORE > 0: 유효 점수만
- 특정 연도: AND TO_CHAR(f.END_YMD, ''YYYY'') = '':년도'' 추가');


-- =============================================================
-- 12. V_AI_HISTORY — 인사발령 (3건)
-- =============================================================

-- #29 승진자 목록 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '승진자 목록 조회', 'query_example', 'ko',
'올해 승진한 직원
승진자 목록
승진한 사람 몇 명
승진 현황
- v_ai_employee JOIN v_ai_history
- ASSIGNMENT_TYPE_CODE LIKE 승진',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.GRADE,
       h.ASSIGNMENT_DATE, h.ASSIGNMENT_TYPE_CODE
FROM v_ai_employee e
JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND h.ASSIGNMENT_TYPE_CODE LIKE ''%승진%''
  AND TO_CHAR(h.ASSIGNMENT_DATE, ''YYYY'') = '':년도''
ORDER BY h.ASSIGNMENT_DATE DESC

패턴:
- WORK_STATUS = ''재직'': 현재 재직 중인 승진자만
- ASSIGNMENT_TYPE_CODE LIKE ''%승진%'': 승진 발령
- TO_CHAR(ASSIGNMENT_DATE, ''YYYY''): 연도 필터
- 승진 수: COUNT(DISTINCT h.EMP_ID)');

-- #30 휴직 직원 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '휴직 직원 조회', 'query_example', 'ko',
'휴직 중인 직원
현재 휴직자
휴직 현황
육아휴직 직원
- v_ai_employee JOIN v_ai_history
- LEAVE_OF_ABSENCE_YN = Y + 최신 발령',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       h.ASSIGNMENT_TYPE_CODE, h.ASSIGNMENT_REASON_CODE,
       h.ASSIGNMENT_START_DATE
FROM v_ai_employee e
JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID
WHERE h.LEAVE_OF_ABSENCE_YN = ''Y''
  AND h.ASSIGNMENT_START_DATE = (
      SELECT MAX(h2.ASSIGNMENT_START_DATE)
      FROM v_ai_history h2
      WHERE h2.EMP_ID = h.EMP_ID
        AND h2.LEAVE_OF_ABSENCE_YN = ''Y''
  )
  AND e.WORK_STATUS = ''재직''
ORDER BY h.ASSIGNMENT_START_DATE DESC

패턴:
- LEAVE_OF_ABSENCE_YN = ''Y'': 휴직 발령
- MAX(ASSIGNMENT_START_DATE): 최신 휴직 발령만
- 육아휴직: ASSIGNMENT_REASON_CODE LIKE ''%육아%'' 추가');

-- #31 발령유형별 통계 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '발령유형별 통계 조회', 'query_example', 'ko',
'발령유형별 현황
인사이동 통계
발령 종류별 건수
전보 승진 휴직 건수
- v_ai_history 단독
- ASSIGNMENT_TYPE_CODE GROUP BY',
'SQL:
SELECT ASSIGNMENT_TYPE_CODE,
       COUNT(*) AS total_count,
       COUNT(DISTINCT EMP_ID) AS emp_count
FROM v_ai_history
WHERE TO_CHAR(ASSIGNMENT_DATE, ''YYYY'') = '':년도''
GROUP BY ASSIGNMENT_TYPE_CODE
ORDER BY total_count DESC

패턴:
- ASSIGNMENT_TYPE_CODE: 승진, 전보, 전직, 휴직, 복직, 퇴직 등
- COUNT(*): 발령 총 건수
- COUNT(DISTINCT EMP_ID): 대상 직원 수 (1인 다건 발령 가능)');


-- =============================================================
-- 13. V_AI_PAY_REPORT — 급여 (3건)
-- =============================================================

-- #32 부서별 평균 급여 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 평균 급여 조회', 'query_example', 'ko',
'부서별 평균 급여
팀별 연봉 현황
조직별 급여 통계
부서 평균 월급
부서별 실수령액
- v_ai_employee JOIN v_ai_pay_report (EMP_ID)
- GROUP BY DEPARTMENT + AVG(NET_PAY_AMOUNT)',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(p.NET_PAY_AMOUNT)) AS avg_net_pay
FROM v_ai_employee e
JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND p.PAY_YEAR_MONTH = '':년월''
  AND p.PAYMENT_TYPE_NAME = ''정기급여''
GROUP BY e.DEPARTMENT
ORDER BY avg_net_pay DESC

패턴:
- JOIN 키: e.EMP_ID = p.EMP_ID
- PAYMENT_TYPE_NAME = ''정기급여'': 상여 제외
- PAY_YEAR_MONTH: YYYYMM 형식 (예: 201804)
- NET_PAY_AMOUNT: 실지급액
- 주의: PAY_DATE 컬럼은 존재하지 않음. 날짜 필터는 PAY_YEAR_MONTH 사용
- 주의: EMPLOYEE_ID 컬럼 아닌 EMP_ID로 조인');

-- #33 특정 연월 급여 현황
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 연월 급여 현황 조회', 'query_example', 'ko',
'이번 달 급여 현황
급여 통계
급여 지급 현황
월별 급여 합계
특정 월 급여 지급 내역
- v_ai_pay_report 단독
- PAY_YEAR_MONTH 필터 + GROUP BY PAYMENT_TYPE_NAME',
'SQL:
SELECT PAYMENT_TYPE_NAME,
       COUNT(*) AS emp_count,
       SUM(GROSS_PAY_AMOUNT) AS total_gross,
       SUM(NET_PAY_AMOUNT) AS total_net,
       ROUND(AVG(NET_PAY_AMOUNT)) AS avg_net
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = '':년월''
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_gross DESC

패턴:
- PAY_YEAR_MONTH: YYYYMM 형식
- GROSS_PAY_AMOUNT: 지급합계
- NET_PAY_AMOUNT: 실지급액
- PAYMENT_TYPE_NAME: 정기급여, 연차수당, 격려금, 상여
- 주의: PAY_DATE 컬럼은 존재하지 않음. 날짜 필터는 PAY_YEAR_MONTH 사용');

-- #34 직원 연간 급여 합계
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직원 연간 급여 합계 조회', 'query_example', 'ko',
'연간 급여 합계
올해 급여 총액
직원별 연봉
연간 실수령액
- v_ai_employee JOIN v_ai_pay_report
- PAY_YEAR 필터 + GROUP BY EMP_ID + SUM',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       SUM(p.GROSS_PAY_AMOUNT) AS annual_gross,
       SUM(p.NET_PAY_AMOUNT) AS annual_net
FROM v_ai_employee e
JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
WHERE p.PAY_YEAR = '':년도''
  AND e.WORK_STATUS = ''재직''
GROUP BY e.EMP_ID, e.EMP_NAME, e.DEPARTMENT, e.POSITION
ORDER BY annual_gross DESC
FETCH FIRST 20 ROWS ONLY

패턴:
- PAY_YEAR: 연간 집계 (YYYY 형식)
- SUM(GROSS_PAY_AMOUNT): 연간 총 지급액
- SUM(NET_PAY_AMOUNT): 연간 실수령액
- GROUP BY에 EMP_ID 포함 필수
- 주의: PAY_DATE 컬럼은 존재하지 않음. 연도 필터는 PAY_YEAR 사용');


-- =============================================================
-- 14. V_AI_DTM_YY_REST — 연차 (3건)
-- =============================================================

-- #35 잔여연차 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '잔여연차 조회', 'query_example', 'ko',
'올해 남은 연차
잔여연차 현황
남은 휴가 일수
연차 잔여일
- v_ai_employee JOIN v_ai_dtm_yy_rest
- REFERENCE_YEAR = 올해',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       d.TOTAL_LEAVE_DAYS, d.USED_LEAVE_DAYS_PAST, d.REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND e.WORK_STATUS = ''재직''
ORDER BY d.REMAINING_LEAVE_DAYS ASC

패턴:
- REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY''): 올해 연차
- TOTAL_LEAVE_DAYS: 총 년월차일수
- USED_LEAVE_DAYS_PAST: 사용연차일수
- REMAINING_LEAVE_DAYS: 잔여연차일수
- ORDER BY ASC: 잔여연차 적은 직원 우선');

-- #36 부서별 연차 사용률
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 연차 사용률 조회', 'query_example', 'ko',
'연차 사용률
부서별 연차 사용 현황
연차 소진률
휴가 사용 통계
- v_ai_employee JOIN v_ai_dtm_yy_rest
- USED / TOTAL * 100 비율 계산',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(d.TOTAL_LEAVE_DAYS), 1) AS avg_total,
       ROUND(AVG(d.USED_LEAVE_DAYS_PAST), 1) AS avg_used,
       ROUND(AVG(
           CASE WHEN d.TOTAL_LEAVE_DAYS > 0
                THEN d.USED_LEAVE_DAYS_PAST * 100.0 / d.TOTAL_LEAVE_DAYS
                ELSE 0
           END
       ), 1) AS avg_usage_rate
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND e.WORK_STATUS = ''재직''
GROUP BY e.DEPARTMENT
ORDER BY avg_usage_rate DESC

패턴:
- 사용률 = USED / TOTAL * 100
- CASE WHEN: TOTAL_LEAVE_DAYS > 0 (0 나누기 방어)
- 부서별: GROUP BY DEPARTMENT');

-- #37 잔여연차 부족 직원
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '잔여연차 부족 직원 조회', 'query_example', 'ko',
'잔여연차 5일 미만 직원
남은 연차 적은 직원
연차 소진 임박 직원
연차 부족자
- v_ai_employee JOIN v_ai_dtm_yy_rest
- REMAINING_LEAVE_DAYS < N 조건',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       d.TOTAL_LEAVE_DAYS, d.USED_LEAVE_DAYS_PAST, d.REMAINING_LEAVE_DAYS
FROM v_ai_employee e
JOIN v_ai_dtm_yy_rest d ON e.EMP_ID = d.EMP_ID
WHERE d.REFERENCE_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
  AND d.REMAINING_LEAVE_DAYS < 5
  AND e.WORK_STATUS = ''재직''
ORDER BY d.REMAINING_LEAVE_DAYS ASC

패턴:
- REMAINING_LEAVE_DAYS < N: N일 미만 (5 → 5일 미만)
- 연차 소진 직원: REMAINING_LEAVE_DAYS = 0
- 부서별 수: GROUP BY DEPARTMENT + COUNT(*)');


-- =============================================================
-- 15. 복합 패턴 (7건)
-- =============================================================

-- #38 복합 조건 직원 수
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '복합 조건 직원 수 조회', 'query_example', 'ko',
'서울 거주하면서 TOEIC 800점 이상인 직원
여러 조건 동시 만족
복합 조건 검색
다중 조건 직원 수
- 여러 EXISTS 조건 조합
- AND로 조건 연결',
'SQL:
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID AND a.REGION = ''서울''
  )
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = ''TOEIC'' AND l.SCORE >= 800
  )

패턴:
- 여러 테이블 조건: 각각 EXISTS 사용
- AND로 조건 연결 (모든 조건 동시 충족)
- OR 조건 시: OR로 연결 (하나라도 충족)');

-- #39 입사자 자격증 보유 개수 (1:N 요약)
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '입사자 자격증 보유 개수 조회', 'query_example', 'ko',
'입사자 현황과 자격증 보유 사항을 알려줘
입사자별 자격증 개수
직원 목록과 보유 자격증 수
자격증 보유 현황
- 1:N 관계에서 1행/인 유지
- 서브쿼리로 COUNT',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.HIRE_DATE,
       (SELECT COUNT(*) FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID) AS license_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, ''YYYY'') = '':년도''
  AND e.WORK_STATUS = ''재직''
ORDER BY e.EMP_NAME

패턴:
- 서브쿼리 COUNT: 1:N 관계에서 1행/인 유지
- 자격증 없는 사람도 license_count = 0으로 표시
- JOIN 사용 시 자격증 여러개면 행이 늘어나는 문제 방지');

-- #40 개인 상세 정보 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '개인 상세 정보 조회', 'query_example', 'ko',
'홍길동의 자격증 목록
특정 직원 학력 정보
개인 상세 데이터 조회
직원 정보 보여줘
- 상세 데이터 필요 시 JOIN 사용
- 특정 직원 조건',
'SQL:
SELECT e.EMP_NAME, l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE e.EMP_NAME LIKE ''%'' || '':이름'' || ''%''
ORDER BY l.ISSUE_DATE DESC

패턴:
- 상세 데이터 필요 시에만 JOIN 사용 (1:N → 여러 행 정상)
- 집계가 아닌 개별 데이터 조회
- ORDER BY로 최신순 정렬');

-- #41 연도별 입사 퇴사 추이
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '연도별 입사 퇴사 추이 조회', 'query_example', 'ko',
'연도별 입사자 퇴사자 추이
채용 이직 트렌드
기간별 인력 변동
입사 퇴사 비교
- UNION ALL로 입사/퇴사 데이터 통합
- 재직 조건 제외 (시점 기준)',
'SQL:
SELECT year_val,
       SUM(hire_count) AS hire_count,
       SUM(retire_count) AS retire_count
FROM (
    SELECT TO_CHAR(HIRE_DATE, ''YYYY'') AS year_val, 1 AS hire_count, 0 AS retire_count
    FROM v_ai_employee
    WHERE HIRE_DATE IS NOT NULL
    UNION ALL
    SELECT TO_CHAR(RETIRE_DATE, ''YYYY'') AS year_val, 0 AS hire_count, 1 AS retire_count
    FROM v_ai_employee
    WHERE RETIRE_DATE IS NOT NULL
)
GROUP BY year_val
ORDER BY year_val DESC

패턴:
- UNION ALL: 입사/퇴사 데이터 통합
- 추이 분석 시 WORK_STATUS 조건 제외
- 기간 한정: WHERE year_val BETWEEN '':시작'' AND '':종료'' 추가');

-- #42 부서별 최고 급여자 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 최고 급여자 조회', 'query_example', 'ko',
'부서별 급여 1위
부서별 최고 연봉자
부서에서 급여 가장 많이 받는 사람
급여 상위 직원
- ROW_NUMBER() OVER(PARTITION BY) 분석함수
- 서브쿼리로 순위 필터',
'SQL:
SELECT DEPARTMENT, EMP_NAME, POSITION, net_pay
FROM (
    SELECT e.DEPARTMENT, e.EMP_NAME, e.POSITION,
           p.NET_PAY_AMOUNT AS net_pay,
           ROW_NUMBER() OVER(PARTITION BY e.DEPARTMENT ORDER BY p.NET_PAY_AMOUNT DESC) AS rn
    FROM v_ai_employee e
    JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
    WHERE e.WORK_STATUS = ''재직''
      AND p.PAYMENT_TYPE_NAME = ''정기급여''
      AND p.PAY_YEAR_MONTH = '':년월''
)
WHERE rn = 1
ORDER BY net_pay DESC

패턴:
- ROW_NUMBER() OVER(PARTITION BY 부서 ORDER BY 급여 DESC): 부서별 순위
- WHERE rn = 1: 각 부서 1위만
- rn <= 3: 각 부서 TOP 3');

-- #43 승진이력 없는 장기 근속자
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '승진이력 없는 장기 근속자 조회', 'query_example', 'ko',
'5년 이상 근무했는데 승진 안 한 직원
승진 이력 없는 장기 근속자
승진 누락 직원
오래 근무했는데 승진 못한 사람
- LEFT JOIN + IS NULL 패턴
- 이력 없는 대상 추출',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.CAREER_YEARS
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE LIKE ''%승진%''
WHERE e.WORK_STATUS = ''재직''
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC
FETCH FIRST 20 ROWS ONLY

패턴:
- LEFT JOIN + IS NULL: 매칭되는 이력이 없는 대상 추출
- ON 절에 조건 추가: 승진 발령만 대상
- WHERE h.EMP_ID IS NULL: 승진 이력 없음');

-- #44 교육 미이수 재직자 목록
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '교육 미이수 재직자 목록 조회', 'query_example', 'ko',
'올해 교육 안 받은 직원
교육 미이수 재직자
교육 수료 안 한 사원
교육 미참여 직원 목록
- NOT EXISTS 패턴
- 이수 기록 없는 직원 추출',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND NOT EXISTS (
    SELECT 1 FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = TO_CHAR(SYSDATE, ''YYYY'')
      AND t.COMPLETION_STATUS = ''수료''
  )
ORDER BY e.DEPARTMENT, e.EMP_NAME

패턴:
- NOT EXISTS: 조건에 맞는 레코드가 없는 대상 추출
- "~하지 않은", "~가 없는", "~를 안 한" 질의에 사용
- 연도별: TRAINING_YEAR = '':년도''');


-- #45 최근 입사자 TOP N 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '최근 입사자 TOP N 조회', 'query_example', 'ko',
'최근 입사한 직원 5명
가장 최근에 들어온 사람
신규 입사자 목록
최근 채용된 직원
방금 입사한 사람 누구야
- ORDER BY HIRE_DATE DESC
- FETCH FIRST N ROWS ONLY
- SELECT * 사용 금지',
'SQL:
SELECT EMP_ID, EMP_NAME, DEPARTMENT, POSITION, HIRE_DATE, HIRE_TYPE
FROM v_ai_employee
WHERE WORK_STATUS = ''재직''
ORDER BY HIRE_DATE DESC
FETCH FIRST 5 ROWS ONLY

패턴:
- ORDER BY HIRE_DATE DESC: 최근 입사 순
- FETCH FIRST N ROWS ONLY: 상위 N건 제한 (Oracle 12c+)
- 절대 SELECT * 사용 금지 — 필요한 컬럼만 명시
- N은 사용자 요청에 따라 변경 (5, 10, 20 등)');

-- #46 두 사원 종합 비교표
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '두 사원 종합 비교표 조회', 'query_example', 'ko',
'사원번호 241번과 242번 비교
두 직원 전체 정보 비교 표로 보여줘
두 사람 인사 정보 전부 비교해줘
사원 A와 사원 B 모든 데이터 나란히 비교
두 명 비교 표 만들어줘
사원들 간의 비교 표
- CROSS JOIN으로 두 사원 나란히 비교
- UNION ALL로 항목별 행 생성
- LISTAGG로 1:N 데이터 집약',
'SQL:
SELECT ''성명'' AS 구분, e1.EMP_NAME AS "사원A", e2.EMP_NAME AS "사원B"
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = :사원번호1 AND e2.EMP_ID = :사원번호2
UNION ALL
SELECT ''부서'', e1.DEPARTMENT, e2.DEPARTMENT
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = :사원번호1 AND e2.EMP_ID = :사원번호2
UNION ALL
SELECT ''직위'', e1.POSITION, e2.POSITION
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = :사원번호1 AND e2.EMP_ID = :사원번호2
UNION ALL
SELECT ''입사일'', TO_CHAR(e1.HIRE_DATE, ''YYYY-MM-DD''), TO_CHAR(e2.HIRE_DATE, ''YYYY-MM-DD'')
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = :사원번호1 AND e2.EMP_ID = :사원번호2
UNION ALL
SELECT ''근속연수'', NVL(TO_CHAR(e1.CAREER_YEARS), ''-'') || ''년'', NVL(TO_CHAR(e2.CAREER_YEARS), ''-'') || ''년''
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = :사원번호1 AND e2.EMP_ID = :사원번호2
UNION ALL
SELECT ''학력'',
  (SELECT LISTAGG(SCHOOL_NAME || ''('' || NVL(MAJOR_NAME,''-'') || '')'', '', '') WITHIN GROUP (ORDER BY GRADUATION_DATE)
   FROM v_ai_scholar WHERE EMP_ID = :사원번호1),
  (SELECT LISTAGG(SCHOOL_NAME || ''('' || NVL(MAJOR_NAME,''-'') || '')'', '', '') WITHIN GROUP (ORDER BY GRADUATION_DATE)
   FROM v_ai_scholar WHERE EMP_ID = :사원번호2)
FROM DUAL
UNION ALL
SELECT ''최근급여(실지급액)'',
  (SELECT TO_CHAR(NET_PAY_AMOUNT, ''FM999,999,999'') || ''원''
   FROM (SELECT NET_PAY_AMOUNT FROM v_ai_pay_report WHERE EMP_ID = :사원번호1 AND PAYMENT_TYPE_NAME = ''정기급여'' ORDER BY PAY_YEAR_MONTH DESC)
   WHERE ROWNUM = 1),
  (SELECT TO_CHAR(NET_PAY_AMOUNT, ''FM999,999,999'') || ''원''
   FROM (SELECT NET_PAY_AMOUNT FROM v_ai_pay_report WHERE EMP_ID = :사원번호2 AND PAYMENT_TYPE_NAME = ''정기급여'' ORDER BY PAY_YEAR_MONTH DESC)
   WHERE ROWNUM = 1)
FROM DUAL

패턴:
- VARCHAR2 컬럼: 직접 비교 (CROSS JOIN)
- DATE 컬럼: TO_CHAR(날짜, ''YYYY-MM-DD'')로 변환 필수
- NUMBER 컬럼: NVL(TO_CHAR(값), ''-'')로 NULL 방어
- 1:N 데이터 집약: LISTAGG(...) WITHIN GROUP (ORDER BY ...)
- 1:N 최신 1건: 서브쿼리 ORDER BY + ROWNUM = 1
- v_ai_pay_report 조인키: EMP_ID (EMPLOYEE_ID 아님)
- 비교 항목 추가 시: UNION ALL SELECT ''항목명'', ... FROM DUAL 추가');

-- #47 특정 직원 전체 정보 조회
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '특정 직원 전체 정보 조회', 'query_example', 'ko',
'241번 직원 정보 보여줘
사원번호 100번 상세 정보
특정 직원 인사 정보 조회
직원 한 명 전체 데이터
홍길동 기본 정보
- EMP_ID 또는 EMP_NAME으로 검색
- SELECT * 사용 금지, 주요 컬럼만 선택',
'SQL:
SELECT EMP_ID, EMP_NAME, DEPARTMENT, POSITION, GRADE, DUTY,
       EMP_TYPE, GENDER, HIRE_TYPE,
       TO_CHAR(HIRE_DATE, ''YYYY-MM-DD'') AS HIRE_DATE,
       WORK_STATUS, CAREER_YEARS,
       TO_CHAR(BIRTH_DATE, ''YYYY-MM-DD'') AS BIRTH_DATE
FROM v_ai_employee
WHERE EMP_ID = :사원번호

패턴:
- 절대 SELECT * 사용 금지 — 주요 컬럼만 명시적으로 SELECT
- DATE 컬럼은 TO_CHAR로 변환하여 가독성 확보
- 이름 검색: WHERE EMP_NAME LIKE ''%'' || '':이름'' || ''%''
- 사원번호 검색: WHERE EMP_ID = :사원번호');
