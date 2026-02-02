-- =============================================================================
-- NL2SQL 방안 C 설정 (스키마 검색 + Few-shot + 재시도)
-- =============================================================================
-- 실행: psql -U hermesuser -d hermesdb -f insert_nl2sql_fewshot_settings.sql
--
-- 주의: value_type은 코드와 일치시켜야 함
--   - bool (NOT boolean)
--   - int (NOT integer)
--   - float
--   - string
-- =============================================================================

-- 스키마 검색 관련 설정 (방안 C)
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'schema_retrieval_enabled', 'true', 'bool', '스키마 선택 기능 활성화 (비활성화 시 전체 스키마 사용)', NOW(), NOW()),
    ('nl2sql', 'schema_retrieval_confidence_threshold', '0.7', 'float', '테이블 선택 신뢰도 임계값 (낮으면 전체 스키마 사용)', NOW(), NOW()),
    ('nl2sql', 'schema_retrieval_model', 'gpt-4.1-mini', 'string', '테이블 선택용 경량 LLM 모델', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Few-shot 관련 설정 (방안 C)
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'fewshot_enabled', 'true', 'bool', 'Few-shot 예제 검색 활성화', NOW(), NOW()),
    ('nl2sql', 'fewshot_top_k', '3', 'int', 'Few-shot 예제 검색 개수', NOW(), NOW()),
    ('nl2sql', 'fewshot_similarity_threshold', '0.3', 'float', 'Few-shot 유사도 임계값', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 재시도 관련 설정 (방안 C)
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'retry_enabled', 'true', 'bool', 'SQL 재시도 기능 활성화', NOW(), NOW()),
    ('nl2sql', 'max_retries', '2', 'int', '최대 재시도 횟수', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 기본 실행 설정 (value_type 통일)
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'timeout_seconds', '30', 'int', 'SQL 실행 타임아웃 (초)', NOW(), NOW()),
    ('nl2sql', 'max_rows', '1000', 'int', '최대 반환 행 수', NOW(), NOW()),
    ('nl2sql', 'read_only_mode', 'true', 'bool', '읽기 전용 모드', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 확인: nl2sql 카테고리 설정 전체 조회
SELECT category, key, value, value_type, description
FROM tb_app_settings
WHERE category = 'nl2sql'
ORDER BY key;
