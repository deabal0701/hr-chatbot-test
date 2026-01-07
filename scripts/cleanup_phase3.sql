-- ============================================
-- Phase 3: Database Cleanup Script
-- ============================================
-- 목적: Phase 2 완료 후 불필요한 설정 제거
-- 실행: psql -d hr_chatbot -f scripts/cleanup_phase3.sql

-- 1. embedding.provider 제거 (임베딩은 OpenAI만 지원, provider 선택 불필요)
DELETE FROM app_settings
WHERE category = 'embedding' AND key = 'provider';

-- 2. 설정 확인 쿼리
SELECT
    category,
    key,
    CASE
        WHEN is_secret THEN '***'
        ELSE value
    END as value,
    value_type,
    description,
    is_secret
FROM app_settings
ORDER BY
    CASE category
        WHEN 'openai' THEN 1
        WHEN 'anthropic' THEN 2
        WHEN 'llm' THEN 3
        WHEN 'embedding' THEN 4
        WHEN 'rag' THEN 5
        WHEN 'nl2sql' THEN 6
        WHEN 'agent' THEN 7
        WHEN 'chunking' THEN 8
        ELSE 99
    END,
    key;

-- 3. Provider 설정 확인
SELECT
    category,
    key,
    value,
    description
FROM app_settings
WHERE key LIKE '%provider%'
ORDER BY category, key;
