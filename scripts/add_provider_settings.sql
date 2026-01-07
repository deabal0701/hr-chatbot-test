-- ============================================
-- Phase 1: LLM Provider 설정 추가 (OpenAI only)
-- ============================================
-- 목적: init_chat_model 마이그레이션을 위한 provider 설정 추가
-- 실행: psql -d hr_chatbot -f scripts/add_provider_settings.sql
--       또는 python에서 실행

-- 1. LLM Provider 설정 추가
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('llm', 'provider', 'openai', 'string', 'LLM 제공자 (현재 openai만 지원)', false)
ON CONFLICT (category, key) DO NOTHING;

-- 2. Embedding Provider 설정 추가
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('embedding', 'provider', 'openai', 'string', '임베딩 제공자 (현재 openai만 지원)', false)
ON CONFLICT (category, key) DO NOTHING;

-- 3. Agent LLM Provider 설정 추가
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('agent', 'llm_provider', 'openai', 'string', 'Agent용 LLM 제공자 (현재 openai만 지원)', false)
ON CONFLICT (category, key) DO NOTHING;

-- 확인 쿼리
SELECT category, key, value, value_type, description
FROM app_settings
WHERE key LIKE '%provider%'
ORDER BY category, key;
