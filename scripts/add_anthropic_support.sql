-- ============================================
-- Phase 2: Anthropic Claude 3.5 Sonnet 지원 추가
-- ============================================
-- 목적: Anthropic API 키 및 provider 설정 추가
-- 실행: psql -d hr_chatbot -f scripts/add_anthropic_support.sql
--       또는 python에서 실행

-- 1. Anthropic API 키 설정 추가 (secret)
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('anthropic', 'api_key', '', 'string', 'Anthropic API Key (Phase 2)', true)
ON CONFLICT (category, key) DO NOTHING;

-- 2. LLM Provider 설정 업데이트 (기존 설정이 없으면 생성)
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('llm', 'provider', 'openai', 'string', 'LLM 제공자 (openai, anthropic)', false)
ON CONFLICT (category, key) DO UPDATE SET description = 'LLM 제공자 (openai, anthropic)';

-- 3. Agent LLM Provider 설정 업데이트
INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
VALUES ('agent', 'llm_provider', 'openai', 'string', 'Agent용 LLM 제공자 (openai, anthropic)', false)
ON CONFLICT (category, key) DO UPDATE SET description = 'Agent용 LLM 제공자 (openai, anthropic)';

-- 확인 쿼리
SELECT category, key, value, value_type, description, is_secret
FROM app_settings
WHERE category IN ('anthropic', 'llm', 'agent')
  AND (category = 'anthropic' OR key LIKE '%provider%')
ORDER BY category, key;

-- 사용 예시:
-- Anthropic Claude 3.5 Sonnet 사용 시:
-- UPDATE app_settings SET value = 'claude-3-5-sonnet-20241022' WHERE category = 'llm' AND key = 'model';
-- UPDATE app_settings SET value = 'anthropic' WHERE category = 'llm' AND key = 'provider';
-- UPDATE app_settings SET value = 'sk-ant-...' WHERE category = 'anthropic' AND key = 'api_key';
