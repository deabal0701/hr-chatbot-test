-- =============================================================================
-- NL2SQL Few-shot 및 재시도 설정 (방안 C)
-- =============================================================================
-- 실행: psql -U hermesuser -d hermesdb -f insert_nl2sql_fewshot_settings.sql
-- =============================================================================

-- Few-shot 관련 설정
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'fewshot_enabled', 'true', 'boolean', 'Few-shot 예제 검색 활성화', NOW(), NOW()),
    ('nl2sql', 'fewshot_top_k', '3', 'integer', 'Few-shot 예제 검색 개수 (기본값)', NOW(), NOW()),
    ('nl2sql', 'fewshot_similarity_threshold', '0.3', 'float', 'Few-shot 유사도 임계값', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 재시도 관련 설정
INSERT INTO tb_app_settings (category, key, value, value_type, description, created_at, updated_at)
VALUES
    ('nl2sql', 'retry_enabled', 'true', 'boolean', 'SQL 재시도 기능 활성화', NOW(), NOW()),
    ('nl2sql', 'max_retries', '2', 'integer', '최대 재시도 횟수', NOW(), NOW())
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- 확인
SELECT category, key, value, value_type, description
FROM tb_app_settings
WHERE category = 'nl2sql'
ORDER BY key;
