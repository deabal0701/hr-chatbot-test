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


-- =============================================================
-- 검증: 변경/추가된 few-shot 확인
-- =============================================================
-- SELECT title, LEFT(content, 80), LEFT(context_data, 80)
-- FROM tb_docs
-- WHERE doc_type = 'query_example' AND usage_type = 'rag_action'
-- ORDER BY doc_id DESC
-- LIMIT 10;
