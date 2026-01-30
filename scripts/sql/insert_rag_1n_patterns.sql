-- 1:N 관계 쿼리 패턴 Few-shot 예제
-- 실행: psql -d hermesdb -f insert_rag_1n_patterns.sql

-- =====================================================
-- 1. 요약 리스트 (1행/인 + 서브쿼리로 N 집계)
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '입사자 현황 + 자격증 보유 개수 (요약 리스트)',
    'query_example',
    '입사자 현황과 자격증 보유 사항을 알려줘
입사자별 자격증 개수
직원 목록과 보유 자격증 수
연도별 입사자와 자격증 현황
- 1:N 관계에서 1행/인 유지 필요
- 서브쿼리로 N테이블 COUNT
- 자격증 없는 사람도 0으로 표시',
    '## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.HIRE_DATE,
       (SELECT COUNT(*) FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID) AS license_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, ''YYYY'') = ''2017''
  AND e.WORK_STATUS = ''재직''
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 리스트**: 서브쿼리로 COUNT하여 1행/인 유지
- 자격증 없는 사람도 license_count = 0으로 표시됨
- JOIN 사용 시 자격증 여러개면 행이 늘어나는 문제 방지',
    '{"intent": "select", "pattern": "1n_summary", "tables": ["v_ai_employee", "v_ai_license"]}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 2. 상세 리스트 (N행/인 허용 - 자격증 상세)
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '입사자 자격증 상세 목록 (상세 리스트)',
    'query_example',
    '입사자들의 자격증 상세 정보
자격증 목록 전체 보여줘
어떤 자격증을 가지고 있는지 상세히
자격증 발급일, 발급기관 포함
- 자격증별로 행 표시 (1인 여러 행 가능)
- LEFT JOIN으로 자격증 없는 사람도 포함',
    '## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT,
       l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE TO_CHAR(e.HIRE_DATE, ''YYYY'') = ''2017''
  AND e.WORK_STATUS = ''재직''
ORDER BY e.EMP_NAME, l.ISSUE_DATE
```

## 핵심 패턴
- **1:N 상세 리스트**: LEFT JOIN으로 모든 자격증 표시
- 자격증 여러개면 여러 행 (정상)
- 자격증 없으면 LICENSE 컬럼이 NULL로 표시
- INNER JOIN 사용 시 자격증 없는 사람 누락됨',
    '{"intent": "select", "pattern": "1n_detail", "tables": ["v_ai_employee", "v_ai_license"]}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 3. 학력 정보 포함 리스트
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '입사자 현황 + 학력 정보 (요약)',
    'query_example',
    '입사자 현황과 학력 사항
직원 학력 정보
최종 학력 조회
출신 학교 정보
- 1:N 관계 (직원:학력)
- 최종학력만 필요시 서브쿼리',
    '## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       (SELECT MAX(ed.SCHOOL_NAME) FROM v_ai_education ed WHERE ed.EMP_ID = e.EMP_ID) AS school_name,
       (SELECT COUNT(*) FROM v_ai_education ed WHERE ed.EMP_ID = e.EMP_ID) AS education_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, ''YYYY'') = ''2017''
  AND e.WORK_STATUS = ''재직''
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 (학력)**: 서브쿼리로 최종학력 또는 학력 수 조회
- MAX(SCHOOL_NAME)은 예시, 실제로는 졸업연도 기준 최신 학력 조회 필요',
    '{"intent": "select", "pattern": "1n_summary", "tables": ["v_ai_employee", "v_ai_education"]}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 4. 어학 점수 포함 리스트
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '입사자 현황 + 어학 점수',
    'query_example',
    '입사자 현황과 어학 성적
토익 점수 조회
어학 점수 보유 현황
영어 점수 확인
- 1:N 관계 (직원:어학)
- 어학별로 여러 건 가능',
    '## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT,
       (SELECT MAX(lg.SCORE) FROM v_ai_language lg
        WHERE lg.EMP_ID = e.EMP_ID AND lg.LANGUAGE_TYPE = ''TOEIC'') AS toeic_score
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, ''YYYY'') = ''2017''
  AND e.WORK_STATUS = ''재직''
ORDER BY toeic_score DESC NULLS LAST
```

## 핵심 패턴
- **1:N 요약 (어학)**: 특정 어학(TOEIC)의 최고 점수 조회
- NULLS LAST: 점수 없는 사람 맨 뒤로',
    '{"intent": "select", "pattern": "1n_summary", "tables": ["v_ai_employee", "v_ai_language"]}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 5. 용어집: 1:N 관계 처리 가이드
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    '1:N 관계 쿼리 패턴',
    'glossary',
    '1:N 관계 조회 패턴
JOIN 사용 시 행 증가 문제
자격증, 학력, 경력 등 N테이블 조회
리스트 조회 시 중복 방지',
    '**1:N 관계 쿼리 가이드**
- 집계(COUNT): EXISTS 사용
- 요약 리스트(1행/인): 서브쿼리로 COUNT/MAX
- 상세 리스트(N행/인): LEFT JOIN
- INNER JOIN은 N이 없는 행 누락됨',
    '{"type": "sql_pattern"}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 6. 용어집: LEFT JOIN vs INNER JOIN
-- =====================================================
INSERT INTO tb_docs (title, doc_type, content, context_data, metadata, indexed, source_type, usage_type) VALUES
(
    'LEFT JOIN vs INNER JOIN',
    'glossary',
    'LEFT JOIN과 INNER JOIN 차이
조인 방식 선택
자격증 없는 사람도 포함
N테이블 데이터 없는 경우',
    '**JOIN 선택 가이드**
- LEFT JOIN: N테이블에 데이터 없어도 1테이블 행 유지 (자격증 없는 사람도 표시)
- INNER JOIN: N테이블에 매칭되는 행만 반환 (자격증 있는 사람만)
- "현황" "명단" 질문 → LEFT JOIN 권장
- "보유자" "가진 사람" → INNER JOIN 또는 EXISTS',
    '{"type": "sql_pattern"}'::jsonb,
    true,
    'rag_action_seed',
    'rag_action'
)
ON CONFLICT DO NOTHING;
