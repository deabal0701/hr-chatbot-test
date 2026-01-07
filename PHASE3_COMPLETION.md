# Phase 3 Implementation Summary

## Completed Tasks

### 1. Frontend UI Updates (SettingsView.vue)
- ✅ Added **LLM Provider** dropdown selector in LLM settings tab (OpenAI / Anthropic)
- ✅ Created **Anthropic** tab for API key configuration
- ✅ Added **Agent LLM Provider** selector in Agent settings
- ✅ Implemented dynamic model placeholders based on selected provider
  - OpenAI: `gpt-4o, gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo`
  - Anthropic: `claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-sonnet-20240229`
- ✅ Added dynamic pricing links
  - OpenAI: https://platform.openai.com/docs/pricing
  - Anthropic: https://www.anthropic.com/pricing#anthropic-api
- ✅ Implemented provider change handler to clear incompatible model names

### 2. Backend Code Cleanup (llm_config.py)
- ✅ Removed deprecated wrapper functions:
  - `get_llm_settings()`
  - `get_rag_settings()`
  - `get_nl2sql_settings()`
- ✅ Updated all usages to `LLMConfigManager.get_*()` pattern
- ✅ Cleaned up import in `sql_executor.py`
- ✅ Updated all references in `rag_graph.py` to use `LLMConfigManager`

### 3. Database Cleanup Scripts
- ✅ Created `scripts/cleanup_phase3.sql` for SQL-based cleanup
- ✅ Created `scripts/run_cleanup_phase3.py` for Python-based cleanup

## Manual Tasks Required

### Database Cleanup (To be executed manually)

Run one of the following:

**Option 1: SQL Script**
```bash
psql -d hr_chatbot -f scripts/cleanup_phase3.sql
```

**Option 2: Python Script** (requires psycopg installed)
```bash
python scripts/run_cleanup_phase3.py
```

**Option 3: Direct SQL** (psql or pgAdmin)
```sql
-- Remove unnecessary embedding.provider setting
-- (Embeddings only support OpenAI, so provider selection is not needed)
DELETE FROM app_settings
WHERE category = 'embedding' AND key = 'provider';

-- Verify cleanup
SELECT category, key, value, description
FROM app_settings
WHERE key LIKE '%provider%'
ORDER BY category, key;
```

Expected result after cleanup:
- `llm.provider` → Retained (openai | anthropic)
- `agent.llm_provider` → Retained (openai | anthropic)
- `embedding.provider` → **Removed** (only OpenAI supported)

## Testing Checklist

### Frontend Testing
- [ ] Navigate to Admin UI → Settings
- [ ] Test OpenAI tab - API key input and validation
- [ ] Test Anthropic tab - API key input
- [ ] Test LLM tab:
  - [ ] Change provider from OpenAI to Anthropic
  - [ ] Verify model placeholder updates
  - [ ] Verify pricing link updates
  - [ ] Enter model name and save
- [ ] Test Agent tab:
  - [ ] Change Agent LLM provider
  - [ ] Save settings
- [ ] Verify all settings persist after page refresh

### Backend Testing (with OpenAI)
- [ ] Test RAG search with `llm.provider=openai`
- [ ] Test NL2SQL with `llm.provider=openai`
- [ ] Test Agent execution with `agent.llm_provider=openai`

### Backend Testing (with Anthropic)
- [ ] Set Anthropic API key in Admin UI
- [ ] Set `llm.provider=anthropic` and `llm.model=claude-3-5-sonnet-20241022`
- [ ] Test RAG search - verify Claude model is used
- [ ] Test NL2SQL - verify Claude model is used
- [ ] Set `agent.llm_provider=anthropic`
- [ ] Test Agent execution - verify Claude model is used
- [ ] Test fallback: Remove Anthropic API key, verify fallback to OpenAI

### Error Handling Testing
- [ ] Test with invalid Anthropic API key - verify error message
- [ ] Test with missing API key - verify clear error message
- [ ] Test provider switching without saving - verify state consistency

## Files Modified

### Frontend
- `frontend/src/views/admin/SettingsView.vue` - Added provider selection UI

### Backend
- `app/utils/llm_config.py` - Removed deprecated wrapper functions
- `app/graphs/rag_graph.py` - Updated to use LLMConfigManager
- `app/services/sql_executor.py` - Cleaned up unused imports

### Scripts
- `scripts/cleanup_phase3.sql` - Database cleanup (SQL)
- `scripts/run_cleanup_phase3.py` - Database cleanup (Python)

## Architecture Summary

### Provider Selection Flow
```
User selects provider in Admin UI
  ↓
Settings saved to PostgreSQL app_settings table
  ↓
Backend reads settings on each LLM creation
  ↓
LLMConfigManager.create_llm() uses init_chat_model()
  ↓
Provider-specific LLM instance created (OpenAI or Anthropic)
  ↓
Fallback to OpenAI if Anthropic fails
```

### Settings Hierarchy
```
1. Request-level config (highest priority)
2. Database app_settings table
3. Environment variables (.env)
4. Code defaults (lowest priority)
```

### Extensibility for Future Providers

To add a new provider (e.g., Google Vertex AI):

1. Update `app/config.py` validators to include new provider
2. Add API key field to `app/config.py` if needed
3. Add default model to `LLMConfigManager.DEFAULT_MODELS`
4. Add API key handling in `LLMConfigManager._get_api_key()`
5. Add provider to Admin UI dropdowns
6. Add model placeholder in `getLLMModelPlaceholder()`
7. Add pricing link in `getPricingLink()`
8. Install provider's langchain package (e.g., `langchain-google-vertexai`)
9. Create DB migration script to add settings

**No changes needed** to:
- Graph execution logic (provider-agnostic via `init_chat_model`)
- Tool binding (standard `BaseChatModel` interface)
- Embedding logic (separate from LLM provider)

## Deployment Notes

### Prerequisites
- PostgreSQL with existing `app_settings` table
- Phase 1 and Phase 2 migration scripts already executed
- Frontend build environment (Node.js, npm)

### Deployment Steps

1. **Backend Deployment**
   ```bash
   # No new package dependencies needed (already in Phase 2)
   # Just deploy updated code
   git pull
   # Restart backend service
   ```

2. **Database Migration**
   ```bash
   # Execute cleanup script
   psql -d hr_chatbot -f scripts/cleanup_phase3.sql
   ```

3. **Frontend Deployment**
   ```bash
   cd frontend
   npm run build
   # Deploy dist/ folder to web server
   ```

4. **Verification**
   - Check Admin UI loads correctly
   - Verify provider dropdowns appear
   - Test settings save/load
   - Run integration tests

### Rollback Plan

If issues occur:

1. **Frontend**: Revert to previous build
2. **Backend**: Revert code changes (backward compatible)
3. **Database**: Re-add removed setting if needed:
   ```sql
   INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
   VALUES ('embedding', 'provider', 'openai', 'string', '임베딩 제공자 (현재 openai만 지원)', false)
   ON CONFLICT (category, key) DO NOTHING;
   ```

## Success Criteria

✅ Phase 3 is complete when:
1. Admin UI shows provider selection dropdowns
2. Anthropic API key can be configured
3. Model placeholders update dynamically
4. All three search modes work with both providers
5. Fallback to OpenAI works correctly
6. No deprecated wrapper functions remain
7. Database cleanup is executed
8. All integration tests pass

## Next Steps (Optional Future Enhancements)

- Add provider selection to non-admin user preferences
- Implement model-specific parameter tuning (e.g., Claude's `max_tokens_to_sample`)
- Add cost tracking per provider
- Implement A/B testing between providers
- Add provider-specific prompt optimization
- Create provider performance comparison dashboard
