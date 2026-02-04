-- NL2SQL 멀티턴 대화 설정 추가
-- 실행: psql -d hermesdb -f add_nl2sql_multiturn_settings.sql
-- 또는 Admin UI/DBeaver에서 직접 실행

-- 멀티턴 설정 INSERT (중복 시 UPDATE)
INSERT INTO tb_app_settings (category, "key", value, value_type, description, is_secret)
VALUES
    ('nl2sql', 'multiturn_enabled', 'true', 'bool', '멀티턴 대화 활성화', false),
    ('nl2sql', 'multiturn_max_turns', '5', 'int', '최대 대화 턴 수 (1-20, 기본 5)', false)
ON CONFLICT (category, "key") DO UPDATE SET
    value = EXCLUDED.value,
    value_type = EXCLUDED.value_type,
    description = EXCLUDED.description,
    updated_at = now();

-- 확인 쿼리
SELECT category, "key", value, value_type, description
FROM tb_app_settings
WHERE category = 'nl2sql' AND "key" LIKE 'multiturn%'
ORDER BY "key";
