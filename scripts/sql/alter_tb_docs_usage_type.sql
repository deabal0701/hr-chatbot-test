-- ============================================================================
-- tb_docs 테이블에 usage_type 컬럼 추가
--
-- 용도: RAG와 Cortex 문서 구분
--   - rag: 문서 기반 답변용 (policy, guide, faq, job_posting)
--   - cortex: SQL 생성 컨텍스트용 (schema, query_example, glossary)
--
-- 실행 방법:
-- psql -U hermesuser -d hermesdb -f alter_tb_docs_usage_type.sql
-- ============================================================================

-- 1. usage_type 컬럼 추가
ALTER TABLE tb_docs ADD COLUMN IF NOT EXISTS
    usage_type VARCHAR(20) DEFAULT 'rag';

COMMENT ON COLUMN tb_docs.usage_type IS '문서 용도 구분: rag(문서 답변), cortex(SQL 생성)';

-- 2. 인덱스 추가 (B-tree, 빠른 필터링)
CREATE INDEX IF NOT EXISTS idx_tb_docs_usage_type
    ON tb_docs(usage_type);

-- 3. 복합 인덱스 (usage_type + doc_type)
CREATE INDEX IF NOT EXISTS idx_tb_docs_usage_doc_type
    ON tb_docs(usage_type, doc_type);

-- 4. 기존 데이터는 'rag'로 유지 (DEFAULT로 이미 처리됨)
-- 명시적으로 업데이트 (NULL인 경우 대비)
UPDATE tb_docs
SET usage_type = 'rag'
WHERE usage_type IS NULL;

-- 5. 확인
SELECT usage_type, doc_type, COUNT(*) as count
FROM tb_docs
GROUP BY usage_type, doc_type
ORDER BY usage_type, doc_type;
