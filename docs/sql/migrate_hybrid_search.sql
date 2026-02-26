-- ============================================================================
-- MUREUM Hybrid Search Migration
-- 파일: docs/sql/migrate_hybrid_search.sql
-- 대상: hermesdb (PostgreSQL, Docker 컨테이너: pgvector-db)
-- 작성: 2026-02-26
--
-- ★ 실행 완료 현황 (2026-02-26 수동 실행):
--   [완료] STEP 1: pg_trgm extension 활성화
--   [완료] STEP 2: pg_trgm.word_similarity_threshold 영구 설정 (ALTER DATABASE)
--   [완료] STEP 3: GIN Trigram 인덱스 생성
--   [미실행] STEP 4: tb_app_settings 설정 추가  ← 백엔드 코드 배포 후 실행
--   [미실행] STEP 5: 동작 검증
--
-- 실행 방법 (STEP 4 이후):
--   docker cp docs/sql/migrate_hybrid_search.sql pgvector-db:/tmp/
--   docker exec -it pgvector-db psql -U hermesuser -d hermesdb -f /tmp/migrate_hybrid_search.sql
--   (STEP 1~3은 멱등하므로 재실행해도 무해)
--
-- 주의:
--   CREATE INDEX CONCURRENTLY는 트랜잭션(BEGIN...COMMIT) 밖에서 실행해야 함.
--
-- 롤백 방법:
--   docker exec -it pgvector-db psql -U hermesuser -d hermesdb
--   DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_content_trgm;
--   DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_title_trgm;
--   UPDATE tb_app_settings SET value = 'vector' WHERE category='rag' AND key='search_mode';
-- ============================================================================

\echo '========================================================'
\echo 'MUREUM Hybrid Search Migration'
\echo '컨테이너: pgvector-db / DB: hermesdb'
\echo '========================================================'

-- ============================================================================
-- STEP 1: pg_trgm extension 활성화  [완료 - 2026-02-26 수동 실행]
-- ============================================================================
-- 실행 기록:
--   docker exec -it pgvector-db psql -U postgres -d hermesdb
--   CREATE EXTENSION IF NOT EXISTS pg_trgm;
--
-- 주의: superuser(postgres) 권한 필요. hermesuser로는 실행 불가.
-- IF NOT EXISTS: 이미 설치된 경우 오류 없이 무시됨 (멱등).
-- ============================================================================

\echo ''
\echo '[STEP 1] pg_trgm extension 확인 (이미 완료)'

CREATE EXTENSION IF NOT EXISTS pg_trgm;

SELECT
    extname    AS "Extension명",
    extversion AS "버전"
FROM pg_extension
WHERE extname = 'pg_trgm';
-- 기대값: pg_trgm | 1.6

-- ============================================================================
-- STEP 2: pg_trgm 임계값 영구 설정  [완료 - 2026-02-26 수동 실행]
-- ============================================================================
-- 실행 기록:
--   ALTER DATABASE hermesdb SET pg_trgm.word_similarity_threshold = 0.1;
--
-- ALTER DATABASE vs SET 차이:
--   SET  pg_trgm.word_similarity_threshold = 0.1  → 현재 세션에만 적용 (재접속 시 초기화)
--   ALTER DATABASE hermesdb SET ...                → DB 레벨 영구 적용 (재접속 후에도 유지) ✅
--
-- 0.1로 설정하는 이유:
--   한글은 유니코드 문자가 각각 별도 trigram을 생성하여 기본값(0.3)이 너무 높음.
--   0.1: 재현율 우선 (노이즈 포함 가능), RRF에서 자연히 낮은 점수로 희석됨.
--   %>  연산자: word_similarity(query, text) >= pg_trgm.word_similarity_threshold
-- ============================================================================

\echo ''
\echo '[STEP 2] pg_trgm 임계값 영구 설정 (이미 완료)'

ALTER DATABASE hermesdb SET pg_trgm.word_similarity_threshold = 0.1;

-- 현재 세션 설정값 확인
SHOW pg_trgm.word_similarity_threshold;
-- 기대값: 0.1
-- (새 접속 세션에서 확인해야 ALTER DATABASE 효과 반영됨)

-- ============================================================================
-- STEP 3: GIN Trigram 인덱스 생성  [완료 - 2026-02-26 수동 실행]
-- ============================================================================
-- 실행 기록:
--   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_content_trgm
--       ON tb_docs USING gin (content gin_trgm_ops);
--   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_title_trgm
--       ON tb_docs USING gin (title gin_trgm_ops);
--
-- CONCURRENTLY: 서비스 무중단 (테이블 잠금 없음).
-- gin_trgm_ops: pg_trgm 전용 GIN 연산자 클래스.
--   %> 연산자(word_similarity >= threshold) 및 <% 연산자 인덱스 지원.
-- IF NOT EXISTS: 이미 존재하면 무시 (멱등).
-- ============================================================================

\echo ''
\echo '[STEP 3] GIN Trigram 인덱스 생성 (이미 완료)'

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_content_trgm
    ON tb_docs USING gin (content gin_trgm_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_title_trgm
    ON tb_docs USING gin (title gin_trgm_ops);

-- 인덱스 크기 확인
SELECT
    indexname                                            AS "인덱스명",
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS "크기"
FROM pg_indexes
WHERE tablename = 'tb_docs'
  AND indexname LIKE '%trgm%'
ORDER BY indexname;

-- ============================================================================
-- STEP 4: tb_app_settings 설정 추가  [미실행 - 백엔드 코드 배포 후 실행]
-- ============================================================================
-- ON CONFLICT: 이미 존재하는 키는 value/description만 갱신 (멱등 실행 가능).
-- 실행 권한: hermesuser (superuser 불필요)
-- ============================================================================

\echo ''
\echo '[STEP 4] tb_app_settings 설정 추가'

INSERT INTO tb_app_settings (category, key, value, value_type, description, is_active, tenant_id)
VALUES
    -- -------------------------------------------------------------------------
    -- Query Analysis 설정
    -- -------------------------------------------------------------------------
    -- keyword_extraction:
    --   none → 원본 쿼리를 pg_trgm에 그대로 사용 (조사·어미 노이즈 발생, 테스트용)
    --   rule → 불용어 제거 + 조사 suffix 제거 ★기본값 (추가 지연 ~1ms, 권장)
    --          pg_trgm은 문자(trigram) 기반이므로 rule만으로 충분.
    --          LLM 키워드 추출은 pg_trgm 개선 효과 미미 → 미지원.
    ('rag', 'keyword_extraction',      'rule',   'string',
     '키워드 추출 방식: none | rule', true, NULL),

    -- direct_lookup_enabled:
    --   true: "HR-001", "POL-023" 같은 식별자 패턴 감지 시 벡터/키워드 검색 건너뜀
    --         → tb_docs.title ILIKE '%HR-001%' 또는 metadata->>'doc_id' 직접 조회
    ('rag', 'direct_lookup_enabled',   'true',   'boolean',
     'Doc ID 패턴 직접 조회 활성화 (예: HR-001, POL-023)', true, NULL),

    -- -------------------------------------------------------------------------
    -- Hybrid Search 설정
    -- -------------------------------------------------------------------------
    -- search_mode:
    --   vector → 기존 벡터 검색만 (하위 호환·회귀 방지용)
    --   hybrid → 벡터 + pg_trgm → RRF 융합 ★기본값
    ('rag', 'search_mode',             'hybrid', 'string',
     '검색 모드: vector | hybrid', true, NULL),

    -- hybrid_rrf_k:
    --   RRF(Reciprocal Rank Fusion) 상수 k.
    --   공식: RRF_score(d) = 1/(k+rank_vector) + 1/(k+rank_keyword)
    --   k=60: 논문·산업 표준값. 일반적으로 변경 불필요.
    ('rag', 'hybrid_rrf_k',            '60',     'integer',
     'RRF 상수 k (기본값 60, 변경 불필요)', true, NULL),

    -- hybrid_fetch_k_factor:
    --   각 검색(벡터/키워드)에서 가져올 후보 수 = top_k × factor.
    --   factor=2, top_k=10 → 각 20개 후보 → RRF 후 상위 10개 반환.
    ('rag', 'hybrid_fetch_k_factor',   '2',      'integer',
     '검색 후보 수 = top_k × factor (기본값 2)', true, NULL),

    -- trgm_word_sim_threshold:
    --   앱 레벨 임계값 (코드에서 추가 필터링 시 사용).
    --   DB 레벨은 ALTER DATABASE로 0.1 고정됨.
    --   이 값은 코드 내 명시적 필터 조건에 사용.
    ('rag', 'trgm_word_sim_threshold', '0.1',    'float',
     'pg_trgm word_similarity 최소 임계값 (DB 설정과 동일: 0.1)', true, NULL),

    -- -------------------------------------------------------------------------
    -- Reranker 설정
    -- -------------------------------------------------------------------------
    -- reranker_mode:
    --   none          → PassthroughReranker ★기본값 (기존 동작과 완전 동일)
    --   llm           → LLMReranker (저가 LLM으로 관련도 0~10 평가)
    --   cross_encoder → CrossEncoderReranker (오픈소스 로컬 모델)
    ('rag', 'reranker_mode',           'none',                    'string',
     '리랭커 모드: none | llm | cross_encoder', true, NULL),

    -- reranker_top_n:
    --   리랭킹 후 generate_answer에 전달할 최종 문서 수.
    --   top_k(10) → reranker_top_n(5): 후보 10개 중 최상위 5개를 컨텍스트로 사용.
    ('rag', 'reranker_top_n',          '5',                       'integer',
     '리랭킹 후 최종 반환 문서 수 (기본값 5)', true, NULL),

    -- reranker_llm_model:
    --   LLM 리랭커 모델. 저가 모델 권장.
    --   gpt-4.1-mini: $0.40/M input, 1만 요청 ≈ $0.007
    ('rag', 'reranker_llm_model',      'gpt-4.1-mini',            'string',
     'LLM 리랭커 모델명 (저가 모델 권장)', true, NULL),

    -- reranker_ce_model:
    --   Cross-Encoder 모델 (HuggingFace, 최초 실행 시 자동 다운로드).
    --   BAAI/bge-reranker-v2-m3: 다국어+한국어, 568MB, RAM ~1.1GB
    --   Dongjin-kr/ko-reranker:  한국어 특화, 280MB, RAM ~550MB
    ('rag', 'reranker_ce_model',       'BAAI/bge-reranker-v2-m3', 'string',
     'Cross-Encoder 모델명 (HuggingFace, 한국어 지원)', true, NULL)

ON CONFLICT (category, key)
    DO UPDATE SET
        value       = EXCLUDED.value,
        description = EXCLUDED.description;

\echo '  설정 추가/갱신 완료'

-- 설정 결과 확인
SELECT
    key         AS "키",
    value       AS "값",
    description AS "설명"
FROM tb_app_settings
WHERE category = 'rag'
  AND key IN (
    'keyword_extraction', 'direct_lookup_enabled',
    'search_mode', 'hybrid_rrf_k', 'hybrid_fetch_k_factor', 'trgm_word_sim_threshold',
    'reranker_mode', 'reranker_top_n', 'reranker_llm_model', 'reranker_ce_model'
  )
ORDER BY key;

-- ============================================================================
-- STEP 5: 동작 검증
-- ============================================================================

\echo ''
\echo '[STEP 5] pg_trgm 동작 검증'

-- word_similarity 한글 동작 확인
SELECT
    word_similarity('재택',     '재택근무 정책은 다음과 같습니다')       AS "재택→재택근무",
    word_similarity('연차휴가', '연차휴가 신청 방법 및 처리 절차')       AS "연차휴가→연차휴가신청",
    word_similarity('법인카드', '법인카드 사용 규정 및 한도 안내')        AS "법인카드→법인카드사용",
    word_similarity('ISO',      'ISO 27001 보안 인증 절차')             AS "ISO→ISO27001",
    word_similarity('재턱',     '재택근무 정책은 다음과 같습니다')        AS "재턱(오타)→재택근무";

-- 예상 결과 참고 (환경마다 다를 수 있음):
--   재택→재택근무:    0.50 ~ 0.70
--   연차휴가→...:     0.70 ~ 0.90
--   법인카드→...:     0.70 ~ 0.90
--   ISO→ISO27001:    0.50 ~ 0.70
--   재턱(오타)→...:   0.20 ~ 0.40

-- word_similarity vs similarity 비교 (긴 텍스트에서 차이)
SELECT
    similarity('재택',      '재택근무 정책은 다음과 같습니다') AS "sim_재택(낮음)",
    word_similarity('재택', '재택근무 정책은 다음과 같습니다') AS "wsim_재택(높음)";
-- 예상: sim_재택 ≈ 0.03, wsim_재택 ≈ 0.60 → word_similarity가 긴 content에 적합

-- 실데이터 키워드 검색 테스트
\echo '[STEP 5] 실데이터 키워드 검색 테스트 (재택)'

SELECT
    id,
    left(title, 50)                                          AS "제목",
    GREATEST(
        word_similarity('재택', title),
        word_similarity('재택', content)
    )                                                        AS "keyword_score"
FROM tb_docs
WHERE usage_type = 'rag_knowledge'
  AND (title %> '재택' OR content %> '재택')
ORDER BY keyword_score DESC
LIMIT 5;

-- ============================================================================
-- 완료
-- ============================================================================

\echo ''
\echo '========================================================'
\echo 'MUREUM Hybrid Search Migration 완료'
\echo ''
\echo '실행 현황:'
\echo '  [완료] STEP 1: pg_trgm extension'
\echo '  [완료] STEP 2: word_similarity_threshold = 0.1 (ALTER DATABASE)'
\echo '  [완료] STEP 3: GIN Trigram 인덱스 (content, title)'
\echo '  [완료] STEP 4: tb_app_settings 설정'
\echo '  [완료] STEP 5: 동작 검증'
\echo ''
\echo '다음 단계: 백엔드 코드 구현 및 배포'
\echo '  - app/core/vector/keyword_extractor.py'
\echo '  - app/core/vector/hybrid_search.py'
\echo '  - app/core/reranker/'
\echo '  - app/graphs/rag/nodes.py (query_analysis, rerank 노드)'
\echo ''
\echo '롤백 필요 시 (postgres 계정으로):'
\echo '  DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_content_trgm;'
\echo '  DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_title_trgm;'
\echo '  UPDATE tb_app_settings SET value=''vector'''
\echo '    WHERE category=''rag'' AND key=''search_mode'';'
\echo '  ALTER DATABASE hermesdb RESET pg_trgm.word_similarity_threshold;'
\echo '========================================================'
