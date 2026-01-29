-- ============================================================================
-- Cortex SQL 컨텍스트 코드 추가
--
-- 용도: Cortex Agent의 doc_type 확장 및 SQL 컨텍스트 유형 정의
-- 대상 테이블: tb_code
--
-- 실행 순서:
-- 1. psql -f alter_tb_docs_usage_type.sql  (컬럼 추가)
-- 2. psql -f insert_cortex_codes.sql       (코드 추가)
-- 3. psql -f insert_nl2sql_rag_data.sql    (데이터 추가)
-- ============================================================================

-- ============================================================================
-- 0. USAGE_TYPE 코드 그룹 (RAG vs Cortex 구분)
-- ============================================================================

-- 코드 그룹 정의
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES ('CODE_GROUP', 'USAGE_TYPE', '문서 용도', 'tb_docs usage_type 컬럼 값', NULL, 12, true, true, NULL)
ON CONFLICT (code_group, code_value) DO UPDATE SET
    code_name = EXCLUDED.code_name,
    description = EXCLUDED.description,
    updated_at = now();

-- USAGE_TYPE 값
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
    ('USAGE_TYPE', 'rag', 'RAG 문서', '문서 기반 답변용 (policy, guide, faq 등)', '{"tag_type": "primary"}'::jsonb, 1, true, true, 'USAGE_TYPE'),
    ('USAGE_TYPE', 'cortex', 'Cortex SQL', 'SQL 생성 컨텍스트용 (schema, query_example, glossary)', '{"tag_type": "warning"}'::jsonb, 2, true, true, 'USAGE_TYPE')
ON CONFLICT (code_group, code_value) DO UPDATE SET
    code_name = EXCLUDED.code_name,
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = now();


-- ============================================================================
-- 1. SQL_CONTEXT_TYPE 코드 그룹 (Cortex 내부용)
-- ============================================================================

-- 코드 그룹 정의
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES ('CODE_GROUP', 'SQL_CONTEXT_TYPE', 'SQL 컨텍스트 유형', 'Cortex SQL 컨텍스트 유형', NULL, 11, true, true, NULL)
ON CONFLICT (code_group, code_value) DO UPDATE SET
    code_name = EXCLUDED.code_name,
    description = EXCLUDED.description,
    updated_at = now();

-- SQL 컨텍스트 유형 값
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
    ('SQL_CONTEXT_TYPE', 'schema', '스키마', '테이블/컬럼 스키마 정보', '{"tag_type": "primary"}'::jsonb, 1, true, true, 'SQL_CONTEXT_TYPE'),
    ('SQL_CONTEXT_TYPE', 'query_example', '쿼리 예제', 'Few-shot SQL 쿼리 예제', '{"tag_type": "success"}'::jsonb, 2, true, true, 'SQL_CONTEXT_TYPE'),
    ('SQL_CONTEXT_TYPE', 'glossary', '용어집', '비즈니스 용어 및 SQL 매핑', '{"tag_type": "info"}'::jsonb, 3, true, true, 'SQL_CONTEXT_TYPE')
ON CONFLICT (code_group, code_value) DO UPDATE SET
    code_name = EXCLUDED.code_name,
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = now();


-- ============================================================================
-- 2. DOC_TYPE에 Cortex 전용 유형 추가
-- ============================================================================

-- 기존 DOC_TYPE 구조:
--   sort_order 1-9: RAG용 (policy, guide, faq, job_posting) → usage_type='rag'
--   sort_order 10+: Cortex용 (schema, query_example, glossary) → usage_type='cortex'
--
-- 구분 방식:
--   tb_docs.usage_type 컬럼으로 RAG/Cortex 구분 (metadata 플래그 불필요)

-- Cortex 전용 doc_type 추가 (기존 DOC_TYPE 그룹에)
-- tag_type을 기존 RAG 유형과 다르게 설정하여 UI에서 구분 가능
INSERT INTO tb_code (code_group, code_value, code_name, description, metadata, sort_order, is_active, is_system, parent)
VALUES
    ('DOC_TYPE', 'schema', 'DB 스키마', '데이터베이스 테이블 스키마 정보', '{"tag_type": "danger"}'::jsonb, 10, true, true, 'DOC_TYPE'),
    ('DOC_TYPE', 'query_example', '쿼리 예제', 'NL2SQL Few-shot 예제', '{"tag_type": "warning"}'::jsonb, 11, true, true, 'DOC_TYPE'),
    ('DOC_TYPE', 'glossary', '용어집', '비즈니스 용어-SQL 매핑', '{"tag_type": "secondary"}'::jsonb, 12, true, true, 'DOC_TYPE')
ON CONFLICT (code_group, code_value) DO UPDATE SET
    code_name = EXCLUDED.code_name,
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = now();


-- ============================================================================
-- 3. Cortex 관련 설정 추가 (tb_app_settings)
-- ============================================================================

INSERT INTO tb_app_settings (category, key, value, value_type, description, is_secret)
VALUES
    ('cortex', 'max_corrections', '3', 'int', 'Cortex 최대 재시도 횟수', false),
    ('cortex', 'timeout_seconds', '60', 'int', 'Cortex 전체 타임아웃 (초)', false),
    ('cortex', 'schema_top_k', '5', 'int', '스키마 검색 결과 수', false),
    ('cortex', 'example_top_k', '3', 'int', '쿼리 예제 검색 결과 수', false),
    ('cortex', 'glossary_top_k', '3', 'int', '용어집 검색 결과 수', false),
    ('cortex', 'min_similarity', '0.5', 'float', '최소 유사도 임계값', false),
    ('cortex', 'human_approval_enabled', 'true', 'bool', 'Human 승인 기능 활성화', false),
    ('cortex', 'sensitive_tables', 'salary,performance_review', 'string', '민감 테이블 목록 (쉼표 구분)', false)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = now();


-- ============================================================================
-- 4. 확인
-- ============================================================================

-- 추가된 USAGE_TYPE 코드 확인
SELECT code_group, code_value, code_name, description
FROM tb_code
WHERE code_group = 'USAGE_TYPE'
ORDER BY sort_order;

-- 추가된 DOC_TYPE 코드 확인 (Cortex용)
SELECT code_group, code_value, code_name, description
FROM tb_code
WHERE code_group = 'DOC_TYPE'
  AND code_value IN ('schema', 'query_example', 'glossary')
ORDER BY sort_order;

-- 추가된 설정 확인
SELECT category, key, value, value_type, description
FROM tb_app_settings
WHERE category = 'cortex'
ORDER BY key;
