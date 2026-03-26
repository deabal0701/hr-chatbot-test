-- =============================================================
-- Few-shot 수정/추가 SQL
-- 생성일: 2026-03-23
-- 사유: coverage2 테스트 결과 분석 후 실제 데이터값 반영
--
-- 문제 요약:
--   1. #29 승진자 목록: LIKE '%승진%' → 실제값 '직급변경' (0건 반환)
--   2. #31 발령유형별 통계: 패턴 설명에 '전보' → 실제값 '이동'
--   3. #43 승진이력 없는 장기근속자: LIKE '%승진%' → '직급변경'
--   4. #15 배우자 보유: RELATION IN ('배우자','처','남편') → 실제값 '처'
--   5. #19 자격증: LICENSE_TYPE '국가자격' → 실제값 '사내자격','사외자격'
--   6. COUNT(*) vs COUNT(DISTINCT EMP_ID) 일관성 부족
--   7. 교육유형 few-shot 부재 (TRAINING_TYPE: 선택,필수)
--   8. 평가명 few-shot 부재 (APPR_NM: 역량평가,업적평가 등)
-- =============================================================


-- ─────────────────────────────────────────
-- 기존 few-shot 수정 (DELETE + RE-INSERT)
-- ─────────────────────────────────────────

-- ■ #29 승진자 목록 조회 — 직급변경 + 직책변경 모두 포함
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '승진자 목록 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '승진자 목록 조회', 'query_example', 'ko',
'올해 승진한 직원
승진자 목록
승진한 사람 몇 명
승진 현황
직급변경 직책변경 직원
- v_ai_employee JOIN v_ai_history
- 승진 = ASSIGNMENT_TYPE_CODE IN (직급변경, 직책변경)
- 직급변경(REASON=승격) 679건 + 직책변경(REASON=승진) 104건',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.GRADE,
       h.ASSIGNMENT_DATE, h.ASSIGNMENT_TYPE_CODE, h.ASSIGNMENT_REASON_CODE
FROM v_ai_employee e
JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND h.ASSIGNMENT_TYPE_CODE IN (''직급변경'', ''직책변경'')
  AND h.ASSIGNMENT_REASON_CODE IN (''승격'', ''승진'')
  AND TO_CHAR(h.ASSIGNMENT_DATE, ''YYYY'') = '':년도''
ORDER BY h.ASSIGNMENT_DATE DESC

패턴:
- 승진 = ASSIGNMENT_TYPE_CODE IN (''직급변경'', ''직책변경'') (DB 실제값)
- 직급변경 + REASON=''승격'' (직급 승급, 679건)
- 직책변경 + REASON=''승진'' (직책 승진, 104건)
- LIKE ''%승진%'' 사용 금지 (ASSIGNMENT_TYPE_CODE에 해당 값 없음)
- 승진 수: COUNT(DISTINCT h.EMP_ID)');


-- ■ #31 발령유형별 통계 조회 — 패턴 설명 실제값 반영
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '발령유형별 통계 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '발령유형별 통계 조회', 'query_example', 'ko',
'발령유형별 현황
인사이동 통계
발령 종류별 건수
이동 승진 휴직 건수
부서 이동 건수
전보 현황
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
- ASSIGNMENT_TYPE_CODE 실제값: 채용, 이동, 퇴직, 직책변경, 직급변경, 조직개편, 전출, 귀임, 파견, 겸직, 휴직, 복직, 직위변경
- 자연어 매핑: 승진→직급변경+직책변경(REASON IN 승격,승진), 전보/부서이동→이동, 전직→전출
- COUNT(*): 발령 총 건수
- COUNT(DISTINCT EMP_ID): 대상 직원 수 (1인 다건 발령 가능)');


-- ■ #43 승진이력 없는 장기 근속자 — 직급변경+직책변경 모두 포함
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '승진이력 없는 장기 근속자 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '승진이력 없는 장기 근속자 조회', 'query_example', 'ko',
'5년 이상 근무했는데 승진 안 한 직원
승진 이력 없는 장기 근속자
승진 누락 직원
오래 근무했는데 승진 못한 사람
직급변경 직책변경 이력 없는 재직자
- LEFT JOIN + IS NULL 패턴
- v_ai_history의 ASSIGNMENT_TYPE_CODE IN (직급변경, 직책변경)',
'SQL:
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.GRADE,
       e.HIRE_DATE, e.CAREER_YEARS
FROM v_ai_employee e
LEFT JOIN v_ai_history h
  ON e.EMP_ID = h.EMP_ID
  AND h.ASSIGNMENT_TYPE_CODE IN (''직급변경'', ''직책변경'')
  AND h.ASSIGNMENT_REASON_CODE IN (''승격'', ''승진'')
WHERE e.WORK_STATUS = ''재직''
  AND e.CAREER_YEARS >= 5
  AND h.EMP_ID IS NULL
ORDER BY e.CAREER_YEARS DESC

패턴:
- LEFT JOIN + ON 절에 조건: 직급변경/직책변경 발령만 대상
- WHERE h.EMP_ID IS NULL: 승진 이력 없음
- 승진 = ASSIGNMENT_TYPE_CODE IN (''직급변경'', ''직책변경'') + REASON IN (''승격'', ''승진'')
- LIKE ''%승진%'' 사용 금지');


-- ■ #15 배우자 보유 직원 수 — RELATION 실제값 '처' 반영
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '배우자 보유 직원 수 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '배우자 보유 직원 수 조회', 'query_example', 'ko',
'배우자가 있는 직원 수
결혼한 직원
기혼자 수
배우자 보유 현황
- v_ai_family (1:N) EXISTS 사용
- RELATION 실제값: 처, 자녀, 형제자매',
'SQL:
SELECT COUNT(*) AS married_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION = ''처''
  )

패턴:
- 배우자 = RELATION = ''처'' (DB 실제값)
- RELATION 실제값: 처, 자녀, 형제자매
- ''배우자'', ''남편'' 값은 DB에 없음 — ''처'' 사용 필수
- 자녀 조건: RELATION = ''자녀''');


-- ■ #19 자격증 보유자 수 — LICENSE_TYPE 실제값 반영
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '자격증 보유자 수 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '자격증 보유자 수 조회', 'query_example', 'ko',
'자격증 보유자 수
자격증 보유한 직원
자격증 있는 직원
사내자격 보유 현황
- v_ai_license (1:N) EXISTS 사용
- LICENSE_TYPE 실제값: 사내자격, 사외자격',
'SQL:
SELECT COUNT(*) AS license_emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
  AND EXISTS (
    SELECT 1 FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
  )

패턴:
- LICENSE_TYPE 실제값: 사내자격, 사외자격
- ''국가자격'', ''민간자격'' 값은 DB에 없음
- 자격 유형별 필터: LICENSE_TYPE = ''사내자격'' 또는 ''사외자격''
- LICENSE_NAME LIKE ''%키워드%'' 로 특정 자격증 검색');


-- ─────────────────────────────────────────
-- 신규 few-shot 추가
-- ─────────────────────────────────────────

-- ■ 신규 #48 교육 유형별 통계 (TRAINING_TYPE: 선택, 필수)
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '교육 유형별 통계 조회', 'query_example', 'ko',
'교육 유형별 현황
필수교육 선택교육 통계
교육 유형별 수료 건수
교육유형 분포
- v_ai_training TRAINING_TYPE GROUP BY
- 실제값: 선택, 필수',
'SQL:
SELECT t.TRAINING_TYPE,
       COUNT(*) AS total_count,
       COUNT(DISTINCT t.EMP_ID) AS emp_count,
       SUM(CASE WHEN t.COMPLETION_STATUS = ''수료'' THEN 1 ELSE 0 END) AS completed_count
FROM v_ai_training t
JOIN v_ai_employee e ON e.EMP_ID = t.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY t.TRAINING_TYPE
ORDER BY total_count DESC

패턴:
- TRAINING_TYPE 실제값: 선택, 필수
- ''집합교육'', ''사이버교육'' 값은 DB에 없음
- 교육 유형별 분류 시 TRAINING_TYPE GROUP BY
- 수료 건수: COMPLETION_STATUS = ''수료'' 조건');


-- ■ 신규 #49 부서별 인사이동 건수 (ASSIGNMENT_TYPE_CODE = '이동')
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 인사이동 건수 조회', 'query_example', 'ko',
'부서별 인사이동 건수
부서 간 전보 빈도
부서 이동 현황
전보 건수
- v_ai_employee JOIN v_ai_history
- 인사이동/전보 = ASSIGNMENT_TYPE_CODE = 이동 (DB 실제값)',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(*) AS move_count,
       COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND h.ASSIGNMENT_TYPE_CODE = ''이동''
GROUP BY e.DEPARTMENT
ORDER BY move_count DESC

패턴:
- 인사이동/전보 = ASSIGNMENT_TYPE_CODE = ''이동'' (DB 실제값)
- ''전보'' 값은 DB에 없음 — ''이동'' 사용 필수
- 자연어 매핑: 전보 → 이동, 승진 → 직급변경, 전직 → 전출');


-- ■ 신규 #50 평가명별 통계 (APPR_NM: 역량평가, 업적평가 등)
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '평가명별 통계 조회', 'query_example', 'ko',
'평가명별 현황
역량평가 업적평가 통계
인사평가 종류별 결과
평가 유형별 분포
- v_ai_feedback APPR_NM GROUP BY
- 실제값: 역량평가, 종합평가, 업적평가, 업적평가 상반기, 업적평가 하반기, 다면평가, 리더십평가',
'SQL:
SELECT f.APPR_NM,
       COUNT(*) AS eval_count,
       COUNT(DISTINCT f.EMP_ID) AS emp_count,
       ROUND(AVG(CASE WHEN f.APPR_SCORE > 0 THEN f.APPR_SCORE END), 1) AS avg_score
FROM v_ai_feedback f
JOIN v_ai_employee e ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY f.APPR_NM
ORDER BY eval_count DESC

패턴:
- APPR_NM 실제값: 역량평가, 종합평가, 업적평가, 업적평가 상반기, 업적평가 하반기, 다면평가, 리더십평가
- ''연간인사평가'', ''수시평가'' 값은 DB에 없음
- APPR_SCORE > 0 조건: 0점은 미유효 점수');


-- ■ 신규 #51 발령유형 자연어-실제값 매핑 가이드
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '인사발령 유형 매핑 가이드', 'query_example', 'ko',
'인사이동 유형
발령 종류
승진 전보 휴직
부서이동 전출 파견
직급변경 직책변경
- v_ai_history ASSIGNMENT_TYPE_CODE 자연어→실제값 매핑
- v_ai_history ASSIGNMENT_REASON_CODE 사유 참조',
'SQL:
SELECT ASSIGNMENT_TYPE_CODE, ASSIGNMENT_REASON_CODE,
       COUNT(*) AS cnt
FROM v_ai_history
GROUP BY ASSIGNMENT_TYPE_CODE, ASSIGNMENT_REASON_CODE
ORDER BY cnt DESC

패턴:
- 자연어→DB값 매핑 (★ 중요):
  승진 → ASSIGNMENT_TYPE_CODE IN (''직급변경'', ''직책변경'') AND REASON IN (''승격'', ''승진'')
        직급변경(REASON=''승격'') 679건 + 직책변경(REASON=''승진'') 104건
  전보/부서이동 → ASSIGNMENT_TYPE_CODE = ''이동''
  전직 → ASSIGNMENT_TYPE_CODE = ''전출''
  파견 → ASSIGNMENT_TYPE_CODE = ''파견''
  겸직 → ASSIGNMENT_TYPE_CODE = ''겸직''
  휴직 → ASSIGNMENT_TYPE_CODE = ''휴직'' 또는 LEAVE_OF_ABSENCE_YN = ''Y''
  복직 → ASSIGNMENT_TYPE_CODE = ''복직''
  퇴직 → ASSIGNMENT_TYPE_CODE = ''퇴직''
- LIKE ''%승진%'' 사용 금지 (해당 값 없음)
- LIKE ''%전보%'' 사용 금지 (해당 값 없음)');


-- ■ 신규 #52 가족관계 자연어-실제값 매핑
INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '가족관계 조회 가이드', 'query_example', 'ko',
'배우자 있는 직원
자녀 있는 직원
가족 현황
부양가족 수
- v_ai_family RELATION 자연어→실제값 매핑',
'SQL:
SELECT f.RELATION,
       COUNT(*) AS family_count,
       COUNT(DISTINCT f.EMP_ID) AS emp_count
FROM v_ai_family f
JOIN v_ai_employee e ON e.EMP_ID = f.EMP_ID
WHERE e.WORK_STATUS = ''재직''
GROUP BY f.RELATION
ORDER BY family_count DESC

패턴:
- 자연어→DB값 매핑:
  배우자/남편/아내 → RELATION = ''처''
  자녀/아들/딸 → RELATION = ''자녀''
  형제/자매 → RELATION = ''형제자매''
- ''배우자'', ''남편'', ''부'', ''모'' 값은 DB에 없음
- 배우자 조회: RELATION = ''처'' 사용 필수');


-- ─────────────────────────────────────────
-- 급여 관련 few-shot 수정/추가 (2026-03-24)
-- ─────────────────────────────────────────

-- ■ #1472 부서별 평균 급여 조회 → 1인당 평균 실수령액으로 명확화
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '부서별 평균 급여 조회';
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '부서별 1인당 평균 실수령액 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 1인당 평균 실수령액 조회', 'query_example', 'ko',
'부서별 1인당 평균 실수령액
부서별 평균 급여
팀별 연봉 현황
조직별 급여 통계
부서 평균 월급
부서별 실수령액
- v_ai_employee JOIN v_ai_pay_report (EMP_ID)
- GROUP BY DEPARTMENT + AVG(NET_PAY_AMOUNT)
- 1인당 평균: 직원 개인별 급여의 평균',
'SQL:
SELECT e.DEPARTMENT,
       COUNT(DISTINCT e.EMP_ID) AS emp_count,
       ROUND(AVG(p.NET_PAY_AMOUNT)) AS avg_net_pay
FROM v_ai_employee e
JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND p.PAYMENT_TYPE_NAME = ''정기급여''
GROUP BY e.DEPARTMENT
ORDER BY avg_net_pay DESC

패턴:
- JOIN 키: e.EMP_ID = p.EMP_ID
- PAYMENT_TYPE_NAME = ''정기급여'': 상여 제외
- AVG(NET_PAY_AMOUNT): 직원 1인당 평균 실수령액
- NET_PAY_AMOUNT: 실지급액
- 주의: PAY_DATE 컬럼 없음 → 날짜 필터는 PAY_YEAR_MONTH 사용
- 주의: EMPLOYEE_ID 아닌 EMP_ID로 조인');


-- ■ 신규 #53 부서별 월 총 실수령액 평균 (2단계 집계)
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '부서별 월 총 실수령액 평균 조회';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '부서별 월 총 실수령액 평균 조회', 'query_example', 'ko',
'부서별 월 총 실수령액 평균
부서별 월평균 실수령액
부서별 월 인건비 평균
부서 전체 월급 평균
- v_ai_employee JOIN v_ai_pay_report
- 2단계 집계: 부서+월별 SUM → 부서별 AVG
- 부서 전체 합계의 월평균 (1인당 아님)',
'SQL:
SELECT DEPARTMENT,
       ROUND(AVG(month_total)) AS avg_monthly_net_pay
FROM (
    SELECT e.DEPARTMENT, p.PAY_YEAR_MONTH,
           SUM(NVL(p.NET_PAY_AMOUNT, 0)) AS month_total
    FROM v_ai_employee e
    JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
    WHERE e.WORK_STATUS = ''재직''
      AND p.PAYMENT_TYPE_NAME = ''정기급여''
    GROUP BY e.DEPARTMENT, p.PAY_YEAR_MONTH
)
GROUP BY DEPARTMENT
ORDER BY avg_monthly_net_pay DESC

패턴:
- 2단계 집계: 서브쿼리에서 부서+월별 SUM → 외부에서 부서별 AVG
- 부서별 월평균 = 부서 전체 인건비의 월평균 (1인당이 아님)
- 1인당 평균은 AVG(NET_PAY_AMOUNT) 직접 사용 (별도 few-shot 참조)
- PAYMENT_TYPE_NAME = ''정기급여'': 상여금 제외
- NVL(p.NET_PAY_AMOUNT, 0): NULL 처리');


-- ─────────────────────────────────────────
-- 직급별 급여 분석 few-shot 추가 (2026-03-24)
-- ─────────────────────────────────────────

-- ■ 신규 #54 직급별 인사 분석 (e.GRADE — 현재 직급 기준)
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '직급별 인사 현황 분석';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직급별 인사 현황 분석', 'query_example', 'ko',
'직급별 재직자 수
직급별 남녀 비율
직급별 평균 근속연수
직급별 인원 현황
직급별 여성 비율
- v_ai_employee.GRADE 사용 (현재 직급 기준)
- 인사 분석(인원,근속,비율)은 e.GRADE 사용',
'SQL:
SELECT e.GRADE,
       COUNT(*) AS emp_count,
       ROUND(AVG(e.CAREER_YEARS), 1) AS avg_career_years,
       SUM(CASE WHEN e.GENDER = ''여'' THEN 1 ELSE 0 END) AS female_count,
       ROUND(SUM(CASE WHEN e.GENDER = ''여'' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS female_ratio
FROM v_ai_employee e
WHERE e.WORK_STATUS = ''재직''
GROUP BY e.GRADE
ORDER BY e.GRADE

패턴:
- ★ 직급 컬럼 선택 기준:
  인사 분석(인원,근속,비율,연차) → e.GRADE (현재 직급)
  급여 분석(지급액,공제,상여) → p.JOB_GRADE_NAME (수령 당시 직급)
- e.GRADE 실제값: 1급, 2급, 3급, 4급, 5급, 6급, 9급
- 직급 = GRADE (1급~9급), 직위 = POSITION (회장~사원) — 혼동 주의');


-- ■ 신규 #55 직급별 급여 분석 (p.JOB_GRADE_NAME — 수령 당시 직급 기준)
DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = '직급별 평균 급여 분석';

INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data)
VALUES ('default', 'rag_action', '직급별 평균 급여 분석', 'query_example', 'ko',
'직급별 평균 총지급액
직급별 평균 급여
직급별 급여 중위값
직급별 상여금 총액
직급별 공제 세금 비율
- v_ai_pay_report.JOB_GRADE_NAME 사용 (수령 당시 직급 기준)
- 급여 분석은 수령 당시 직급이 정확함
- JOB_GRADE_NAME이 NULL인 경우 e.GRADE + 최신 월 조건으로 대체',
'SQL:
-- ● JOB_GRADE_NAME에 데이터가 있는 경우 (권장)
SELECT p.JOB_GRADE_NAME,
       COUNT(DISTINCT p.EMP_ID) AS emp_count,
       ROUND(AVG(p.GROSS_PAY_AMOUNT)) AS avg_gross_pay,
       ROUND(AVG(p.NET_PAY_AMOUNT)) AS avg_net_pay
FROM v_ai_employee e
JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
WHERE e.WORK_STATUS = ''재직''
  AND p.PAYMENT_TYPE_NAME = ''정기급여''
GROUP BY p.JOB_GRADE_NAME
ORDER BY avg_gross_pay DESC

-- ● JOB_GRADE_NAME이 NULL인 경우 (현재 상태 — 대체 쿼리)
-- SELECT e.GRADE,
--        COUNT(DISTINCT e.EMP_ID) AS emp_count,
--        ROUND(AVG(p.GROSS_PAY_AMOUNT)) AS avg_gross_pay
-- FROM v_ai_employee e
-- JOIN v_ai_pay_report p ON e.EMP_ID = p.EMP_ID
-- WHERE e.WORK_STATUS = ''재직''
--   AND p.PAYMENT_TYPE_NAME = ''정기급여''
--   AND p.PAY_YEAR_MONTH = (SELECT MAX(PAY_YEAR_MONTH) FROM v_ai_pay_report)
-- GROUP BY e.GRADE
-- ORDER BY avg_gross_pay DESC

패턴:
- ★ 직급 컬럼 선택 기준:
  급여 분석 → p.JOB_GRADE_NAME (수령 당시 직급, 과거 포함 시 정확)
  인사 분석 → e.GRADE (현재 직급)
- JOB_GRADE_NAME이 전부 NULL인 경우: e.GRADE + 최신 월 조건으로 대체
- PAYMENT_TYPE_NAME = ''정기급여'': 상여금 제외
- GROSS_PAY_AMOUNT: 총지급액, NET_PAY_AMOUNT: 실수령액');


-- =============================================================
-- 검증: 변경/추가된 few-shot 확인
-- =============================================================
-- SELECT title, LEFT(content, 80), LEFT(context_data, 80)
-- FROM tb_docs
-- WHERE doc_type = 'query_example' AND usage_type = 'rag_action'
-- ORDER BY id DESC
-- LIMIT 15;
