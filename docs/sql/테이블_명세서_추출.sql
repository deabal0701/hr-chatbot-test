-- ============================================================================
-- 테이블 명세서 추출 SQL (PostgreSQL)
-- 사용법: 결과를 CSV로 Export 후 Excel에 붙여넣기
-- ============================================================================

-- ============================================================================
-- 1. 전체 테이블 목록 조회
-- ============================================================================
SELECT
    t.table_name AS "테이블명",
    COALESCE(d.description, '-') AS "테이블설명",
    (SELECT COUNT(*)
     FROM information_schema.columns c
     WHERE c.table_schema = t.table_schema
       AND c.table_name = t.table_name) AS "컬럼수"
FROM information_schema.tables t
LEFT JOIN pg_catalog.pg_class pc ON pc.relname = t.table_name
LEFT JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace AND pn.nspname = t.table_schema
LEFT JOIN pg_catalog.pg_description d ON d.objoid = pc.oid AND d.objsubid = 0
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;


-- ============================================================================
-- 2. 전체 컬럼 명세 조회 (Excel 붙여넣기용)
-- ============================================================================
SELECT
    c.table_name AS "테이블명",
    c.column_name AS "컬럼명",
    c.data_type ||
        CASE
            WHEN c.character_maximum_length IS NOT NULL
                THEN '(' || c.character_maximum_length || ')'
            WHEN c.numeric_precision IS NOT NULL AND c.data_type IN ('numeric', 'decimal')
                THEN '(' || c.numeric_precision || ',' || COALESCE(c.numeric_scale, 0) || ')'
            ELSE ''
        END AS "데이터타입",
    CASE WHEN c.is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END AS "NULL허용",
    COALESCE(c.column_default, '-') AS "기본값",
    CASE
        WHEN pk.column_name IS NOT NULL THEN 'PK'
        WHEN fk.column_name IS NOT NULL THEN 'FK'
        WHEN uk.column_name IS NOT NULL THEN 'UK'
        ELSE '-'
    END AS "PK/FK",
    COALESCE(col_desc.description, '-') AS "설명"
FROM information_schema.columns c
-- Primary Key 조인
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY'
) pk ON c.table_schema = pk.table_schema
     AND c.table_name = pk.table_name
     AND c.column_name = pk.column_name
-- Foreign Key 조인
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
) fk ON c.table_schema = fk.table_schema
     AND c.table_name = fk.table_name
     AND c.column_name = fk.column_name
-- Unique Key 조인
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'UNIQUE'
) uk ON c.table_schema = uk.table_schema
     AND c.table_name = uk.table_name
     AND c.column_name = uk.column_name
-- 컬럼 코멘트 조인
LEFT JOIN (
    SELECT
        pn.nspname AS table_schema,
        pc.relname AS table_name,
        pa.attname AS column_name,
        pd.description
    FROM pg_catalog.pg_class pc
    JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace
    JOIN pg_catalog.pg_attribute pa ON pa.attrelid = pc.oid
    LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = pc.oid AND pd.objsubid = pa.attnum
    WHERE pa.attnum > 0 AND NOT pa.attisdropped
) col_desc ON c.table_schema = col_desc.table_schema
          AND c.table_name = col_desc.table_name
          AND c.column_name = col_desc.column_name
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;


-- ============================================================================
-- 3. 특정 테이블만 조회 (테이블명 지정)
-- ============================================================================
-- 아래 IN 절에 원하는 테이블명을 추가/수정하세요
SELECT
    c.table_name AS "테이블명",
    c.column_name AS "컬럼명",
    c.data_type ||
        CASE
            WHEN c.character_maximum_length IS NOT NULL
                THEN '(' || c.character_maximum_length || ')'
            WHEN c.numeric_precision IS NOT NULL AND c.data_type IN ('numeric', 'decimal')
                THEN '(' || c.numeric_precision || ',' || COALESCE(c.numeric_scale, 0) || ')'
            ELSE ''
        END AS "데이터타입",
    CASE WHEN c.is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END AS "NULL허용",
    COALESCE(c.column_default, '-') AS "기본값",
    CASE
        WHEN pk.column_name IS NOT NULL THEN 'PK'
        WHEN fk.column_name IS NOT NULL THEN 'FK'
        WHEN uk.column_name IS NOT NULL THEN 'UK'
        ELSE '-'
    END AS "PK/FK",
    COALESCE(col_desc.description, '-') AS "설명"
FROM information_schema.columns c
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY'
) pk ON c.table_schema = pk.table_schema
     AND c.table_name = pk.table_name
     AND c.column_name = pk.column_name
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
) fk ON c.table_schema = fk.table_schema
     AND c.table_name = fk.table_name
     AND c.column_name = fk.column_name
LEFT JOIN (
    SELECT kcu.table_schema, kcu.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'UNIQUE'
) uk ON c.table_schema = uk.table_schema
     AND c.table_name = uk.table_name
     AND c.column_name = uk.column_name
LEFT JOIN (
    SELECT
        pn.nspname AS table_schema,
        pc.relname AS table_name,
        pa.attname AS column_name,
        pd.description
    FROM pg_catalog.pg_class pc
    JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace
    JOIN pg_catalog.pg_attribute pa ON pa.attrelid = pc.oid
    LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = pc.oid AND pd.objsubid = pa.attnum
    WHERE pa.attnum > 0 AND NOT pa.attisdropped
) col_desc ON c.table_schema = col_desc.table_schema
          AND c.table_name = col_desc.table_name
          AND c.column_name = col_desc.column_name
WHERE c.table_schema = 'public'
  AND c.table_name IN (
      'tb_app_settings',
      'tb_code',
      'query_log',
      'tb_docs',
      'rag_search_log',
      'sql_execution_log',
      'tb_prompt_history'
  )
ORDER BY c.table_name, c.ordinal_position;


-- ============================================================================
-- 4. 인덱스 정보 조회
-- ============================================================================
SELECT
    schemaname AS "스키마",
    tablename AS "테이블명",
    indexname AS "인덱스명",
    indexdef AS "인덱스정의"
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;


-- ============================================================================
-- 5. 외래키 관계 조회
-- ============================================================================
SELECT
    tc.table_name AS "테이블명",
    kcu.column_name AS "컬럼명",
    ccu.table_name AS "참조테이블",
    ccu.column_name AS "참조컬럼",
    tc.constraint_name AS "제약조건명"
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;


-- ============================================================================
-- 6. 제약조건 전체 조회
-- ============================================================================
SELECT
    tc.table_name AS "테이블명",
    tc.constraint_name AS "제약조건명",
    tc.constraint_type AS "제약조건유형",
    STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) AS "컬럼"
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_schema = 'public'
GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;


-- ============================================================================
-- 7. 테이블별 상세 통계 (행 수 포함)
-- ============================================================================
SELECT
    t.table_name AS "테이블명",
    COALESCE(d.description, '-') AS "테이블설명",
    (SELECT COUNT(*)
     FROM information_schema.columns c
     WHERE c.table_schema = t.table_schema
       AND c.table_name = t.table_name) AS "컬럼수",
    pg_stat.n_live_tup AS "대략적행수",
    pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name))) AS "테이블크기"
FROM information_schema.tables t
LEFT JOIN pg_catalog.pg_class pc ON pc.relname = t.table_name
LEFT JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace AND pn.nspname = t.table_schema
LEFT JOIN pg_catalog.pg_description d ON d.objoid = pc.oid AND d.objsubid = 0
LEFT JOIN pg_stat_user_tables pg_stat ON pg_stat.relname = t.table_name
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;


-- ============================================================================
-- 8. 컬럼 코멘트 추가용 SQL 생성 (코멘트가 없는 컬럼)
-- ============================================================================
SELECT
    'COMMENT ON COLUMN ' || c.table_name || '.' || c.column_name || ' IS '''';' AS "코멘트추가SQL"
FROM information_schema.columns c
LEFT JOIN (
    SELECT
        pc.relname AS table_name,
        pa.attname AS column_name,
        pd.description
    FROM pg_catalog.pg_class pc
    JOIN pg_catalog.pg_namespace pn ON pn.oid = pc.relnamespace AND pn.nspname = 'public'
    JOIN pg_catalog.pg_attribute pa ON pa.attrelid = pc.oid
    LEFT JOIN pg_catalog.pg_description pd ON pd.objoid = pc.oid AND pd.objsubid = pa.attnum
    WHERE pa.attnum > 0 AND NOT pa.attisdropped
) col_desc ON c.table_name = col_desc.table_name
          AND c.column_name = col_desc.column_name
WHERE c.table_schema = 'public'
  AND col_desc.description IS NULL
ORDER BY c.table_name, c.ordinal_position;
