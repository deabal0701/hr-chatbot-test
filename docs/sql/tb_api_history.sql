-- ============================================================
-- tb_api_history: API 요청 이력 및 실행 추적 테이블
-- 멀티테넌트 및 사용자별 이력 조회 지원
-- ============================================================

-- 시퀀스 생성
CREATE SEQUENCE IF NOT EXISTS api_history_id_seq;

-- 테이블 생성
CREATE TABLE IF NOT EXISTS tb_api_history (
    id BIGINT DEFAULT nextval('api_history_id_seq') PRIMARY KEY,

    -- ===== 멀티테넌트 및 사용자 식별 =====
    tenant_id VARCHAR(50) NULL,           -- 고객사/테넌트 ID (NULL = 기본 테넌트)
    user_id VARCHAR(100) NULL,            -- 사용자 ID (NULL = 익명)
    user_name VARCHAR(100) NULL,          -- 사용자 표시명 (선택)

    -- ===== 요청 식별 =====
    request_id VARCHAR(20) NOT NULL,      -- 8자 UUID (LoggingMiddleware 생성)
    session_id VARCHAR(100) NULL,         -- 멀티턴 세션 ID

    -- ===== 요청 분류 =====
    request_type VARCHAR(20) NOT NULL,    -- 'agent', 'nl2sql', 'rag'
    endpoint VARCHAR(100) NOT NULL,       -- API 엔드포인트

    -- ===== 요청/응답 데이터 =====
    question TEXT NOT NULL,               -- 원본 질문
    answer TEXT NULL,                     -- 최종 답변
    response_code INT NOT NULL DEFAULT 200,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT NULL,

    -- ===== 실행 추적 (타입별 JSONB) =====
    trace_data JSONB NULL,
    -- Agent: {steps, tools_used, iteration_count, intent_analysis}
    -- NL2SQL: {sql, sql_result, current_turn, validation_errors}
    -- RAG: {sources, similarity_scores, chunks_count}

    -- ===== 성능 메트릭 =====
    response_time_ms INT NOT NULL DEFAULT 0,
    llm_calls_count INT NULL,             -- LLM API 호출 횟수
    tokens_used INT NULL,                 -- 사용된 토큰 수 (추후 집계용)

    -- ===== 클라이언트 정보 =====
    client_ip VARCHAR(45) NULL,           -- IPv4/IPv6 지원
    user_agent TEXT NULL,

    -- ===== 타임스탬프 =====
    requested_at TIMESTAMPTZ NOT NULL,            -- 요청 시작 시간
    completed_at TIMESTAMPTZ NULL,                -- 응답 완료 시간
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL, -- DB 저장 시간 (자동)

    -- 제약조건
    CONSTRAINT chk_request_type CHECK (request_type IN ('agent', 'nl2sql', 'rag'))
);

-- ===== 핵심 인덱스 =====
CREATE INDEX IF NOT EXISTS idx_api_history_request_id ON tb_api_history(request_id);
CREATE INDEX IF NOT EXISTS idx_api_history_session_id ON tb_api_history(session_id);
CREATE INDEX IF NOT EXISTS idx_api_history_created_at ON tb_api_history(created_at DESC);

-- ===== 멀티테넌트 인덱스 (고객사별 조회) =====
CREATE INDEX IF NOT EXISTS idx_api_history_tenant ON tb_api_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_history_tenant_date ON tb_api_history(tenant_id, created_at DESC);

-- ===== 사용자별 인덱스 (내 이력 조회) =====
CREATE INDEX IF NOT EXISTS idx_api_history_user ON tb_api_history(user_id);
CREATE INDEX IF NOT EXISTS idx_api_history_user_date ON tb_api_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_history_tenant_user ON tb_api_history(tenant_id, user_id);

-- ===== 필터링 인덱스 =====
CREATE INDEX IF NOT EXISTS idx_api_history_type ON tb_api_history(request_type);
CREATE INDEX IF NOT EXISTS idx_api_history_success ON tb_api_history(success);
CREATE INDEX IF NOT EXISTS idx_api_history_type_date ON tb_api_history(request_type, created_at DESC);

-- ===== JSONB 인덱스 (trace_data 검색용) =====
CREATE INDEX IF NOT EXISTS idx_api_history_trace ON tb_api_history USING GIN (trace_data);

-- ===== 테이블 및 컬럼 코멘트 =====
COMMENT ON TABLE tb_api_history IS 'API 요청 이력 및 실행 추적 (멀티테넌트/사용자별 지원)';
COMMENT ON COLUMN tb_api_history.tenant_id IS '고객사/테넌트 식별자 (NULL = 기본 테넌트)';
COMMENT ON COLUMN tb_api_history.user_id IS '사용자 식별자 (NULL = 익명, 향후 인증 연동)';
COMMENT ON COLUMN tb_api_history.user_name IS '사용자 표시명 (UI 노출용)';
COMMENT ON COLUMN tb_api_history.request_id IS '요청 고유 ID (LoggingMiddleware 생성, 8자 UUID)';
COMMENT ON COLUMN tb_api_history.session_id IS '멀티턴 대화 세션 ID';
COMMENT ON COLUMN tb_api_history.request_type IS '요청 타입: agent, nl2sql, rag';
COMMENT ON COLUMN tb_api_history.trace_data IS '실행 추적 데이터 (타입별 JSONB)';
COMMENT ON COLUMN tb_api_history.response_time_ms IS '총 응답 시간 (밀리초)';
COMMENT ON COLUMN tb_api_history.llm_calls_count IS 'LLM API 호출 횟수';
COMMENT ON COLUMN tb_api_history.tokens_used IS '사용된 토큰 수';


-- ============================================================
-- 예시: trace_data 구조
-- ============================================================
--
-- Agent:
-- {
--   "steps": [
--     {"step": 1, "thought": "...", "action": "query_database_tool", "observation": "..."},
--     {"step": 2, "thought": "...", "action": "search_documents_tool", "observation": "..."}
--   ],
--   "tools_used": ["query_database_tool", "search_documents_tool"],
--   "iteration_count": 2,
--   "intent_analysis": {"type": "hybrid", "confidence": 0.85}
-- }
--
-- NL2SQL:
-- {
--   "sql": "SELECT COUNT(*) FROM employee WHERE ...",
--   "sql_result": {"columns": ["count"], "rows": [{"count": 27}], "row_count": 1},
--   "current_turn": 1,
--   "validation_passed": true
-- }
--
-- RAG:
-- {
--   "sources": [{"id": 42, "title": "재택근무 정책", "similarity": 0.89}],
--   "sources_count": 3,
--   "top_similarity": 0.89
-- }
