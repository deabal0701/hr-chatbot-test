-- ============================================================
-- 사용자 및 권한 관리 테이블 DDL
-- 파일: docs/sql/tb_user_permission.sql
-- 작성일: 2026-02-06
-- ============================================================

-- ==========================================
-- 1. 테넌트 테이블
-- ==========================================
CREATE TABLE tb_tenant (
    tenant_id       BIGSERIAL PRIMARY KEY,
    tenant_code     VARCHAR(50) UNIQUE NOT NULL,   -- 테넌트 코드 (NL2SQL 조건용)
    tenant_name     VARCHAR(200) NOT NULL,
    is_active       BOOLEAN DEFAULT true,
    metadata        JSONB,                          -- 추가 정보 (업종, 계약정보 등)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_tenant IS '테넌트(고객사) 정보';
COMMENT ON COLUMN tb_tenant.tenant_code IS '테넌트 코드 (NL2SQL WHERE 조건에 사용)';
COMMENT ON COLUMN tb_tenant.metadata IS '추가 정보 (업종, 계약정보, 연락처 등)';

CREATE INDEX idx_tenant_active ON tb_tenant(is_active);
CREATE INDEX idx_tenant_code ON tb_tenant(tenant_code);


-- ==========================================
-- 2. 사용자 테이블
-- ==========================================
CREATE TABLE tb_user (
    user_id         BIGSERIAL PRIMARY KEY,
    username        VARCHAR(100) UNIQUE NOT NULL,   -- 로그인 ID
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,          -- bcrypt 해시
    display_name    VARCHAR(100),
    tenant_id       BIGINT REFERENCES tb_tenant(tenant_id) ON DELETE SET NULL,
    is_active       BOOLEAN DEFAULT true,
    is_superuser    BOOLEAN DEFAULT false,          -- 시스템 관리자 플래그
    last_login_at   TIMESTAMPTZ,
    login_fail_count INT DEFAULT 0,                 -- 로그인 실패 횟수
    locked_until    TIMESTAMPTZ,                    -- 계정 잠금 해제 시간
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_user IS '사용자 정보';
COMMENT ON COLUMN tb_user.username IS '로그인 ID';
COMMENT ON COLUMN tb_user.password_hash IS '비밀번호 해시 (bcrypt)';
COMMENT ON COLUMN tb_user.is_superuser IS '시스템 관리자 플래그 (true면 모든 권한)';
COMMENT ON COLUMN tb_user.login_fail_count IS '연속 로그인 실패 횟수 (잠금 정책용)';
COMMENT ON COLUMN tb_user.locked_until IS '계정 잠금 해제 시간 (NULL이면 잠금 아님)';

CREATE INDEX idx_user_tenant ON tb_user(tenant_id);
CREATE INDEX idx_user_active ON tb_user(is_active);
CREATE INDEX idx_user_username ON tb_user(username);
CREATE INDEX idx_user_email ON tb_user(email);


-- ==========================================
-- 3. 역할(Role) 테이블
-- ==========================================
CREATE TABLE tb_role (
    role_id         BIGSERIAL PRIMARY KEY,
    role_code       VARCHAR(50) UNIQUE NOT NULL,    -- SYSTEM_ADMIN, TENANT_ADMIN, USER
    role_name       VARCHAR(100) NOT NULL,
    description     TEXT,
    scope_type      VARCHAR(20) NOT NULL,           -- GLOBAL, TENANT, USER (권한 범위)
    is_system       BOOLEAN DEFAULT false,          -- 시스템 기본 역할 (삭제 불가)
    sort_order      INT DEFAULT 0,                  -- 정렬 순서
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_role IS '역할 정의';
COMMENT ON COLUMN tb_role.role_code IS '역할 코드 (시스템 내부 식별자)';
COMMENT ON COLUMN tb_role.scope_type IS '권한 범위: GLOBAL(전체), TENANT(테넌트), USER(사용자)';
COMMENT ON COLUMN tb_role.is_system IS '시스템 기본 역할 (삭제 불가)';

CREATE INDEX idx_role_code ON tb_role(role_code);
CREATE INDEX idx_role_scope ON tb_role(scope_type);


-- ==========================================
-- 4. 권한(Permission) 테이블
-- ==========================================
CREATE TABLE tb_permission (
    permission_id   BIGSERIAL PRIMARY KEY,
    permission_code VARCHAR(100) UNIQUE NOT NULL,   -- nl2sql:execute, rag:search, admin:settings
    permission_name VARCHAR(200) NOT NULL,
    category        VARCHAR(50) NOT NULL,           -- nl2sql, rag, admin, document
    description     TEXT,
    is_system       BOOLEAN DEFAULT false,          -- 시스템 기본 권한 (삭제 불가)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_permission IS '권한 정의';
COMMENT ON COLUMN tb_permission.permission_code IS '권한 코드 (category:action 형식)';
COMMENT ON COLUMN tb_permission.category IS '권한 카테고리 (nl2sql, rag, admin, document 등)';

CREATE INDEX idx_permission_code ON tb_permission(permission_code);
CREATE INDEX idx_permission_category ON tb_permission(category);


-- ==========================================
-- 5. 역할-권한 매핑 테이블
-- ==========================================
CREATE TABLE tb_role_permission (
    role_id         BIGINT NOT NULL REFERENCES tb_role(role_id) ON DELETE CASCADE,
    permission_id   BIGINT NOT NULL REFERENCES tb_permission(permission_id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE tb_role_permission IS '역할-권한 매핑';

CREATE INDEX idx_role_permission_role ON tb_role_permission(role_id);
CREATE INDEX idx_role_permission_perm ON tb_role_permission(permission_id);


-- ==========================================
-- 6. 사용자-역할 매핑 테이블
-- ==========================================
CREATE TABLE tb_user_role (
    user_id         BIGINT NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,
    role_id         BIGINT NOT NULL REFERENCES tb_role(role_id) ON DELETE CASCADE,
    tenant_id       BIGINT REFERENCES tb_tenant(tenant_id) ON DELETE CASCADE,  -- NULL이면 전역 역할
    granted_at      TIMESTAMPTZ DEFAULT NOW(),
    granted_by      BIGINT REFERENCES tb_user(user_id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, role_id, COALESCE(tenant_id, 0))
);

COMMENT ON TABLE tb_user_role IS '사용자-역할 매핑';
COMMENT ON COLUMN tb_user_role.tenant_id IS '테넌트 ID (NULL이면 전역 역할)';
COMMENT ON COLUMN tb_user_role.granted_by IS '역할 부여자 ID';

CREATE INDEX idx_user_role_user ON tb_user_role(user_id);
CREATE INDEX idx_user_role_role ON tb_user_role(role_id);
CREATE INDEX idx_user_role_tenant ON tb_user_role(tenant_id);


-- ==========================================
-- 7. 데이터 접근 필터 테이블 (Row-Level Security 조건)
-- ==========================================
CREATE TABLE tb_data_filter (
    filter_id       BIGSERIAL PRIMARY KEY,
    role_id         BIGINT NOT NULL REFERENCES tb_role(role_id) ON DELETE CASCADE,
    target_table    VARCHAR(100) NOT NULL,          -- 적용 대상 테이블
    filter_column   VARCHAR(100) NOT NULL,          -- 필터 컬럼 (tenant_id, user_id 등)
    filter_type     VARCHAR(20) NOT NULL,           -- TENANT, USER, CUSTOM
    filter_sql      TEXT,                           -- 커스텀 SQL 조건 (선택)
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (role_id, target_table, filter_column)
);

COMMENT ON TABLE tb_data_filter IS '역할별 데이터 접근 필터 (NL2SQL WHERE 조건 자동 주입)';
COMMENT ON COLUMN tb_data_filter.target_table IS '필터 적용 대상 테이블명';
COMMENT ON COLUMN tb_data_filter.filter_column IS '필터 조건 컬럼 (tenant_id, emp_id 등)';
COMMENT ON COLUMN tb_data_filter.filter_type IS '필터 유형: TENANT(테넌트ID), USER(사용자ID), CUSTOM(커스텀SQL)';
COMMENT ON COLUMN tb_data_filter.filter_sql IS '커스텀 SQL 조건식 (filter_type=CUSTOM일 때 사용)';

CREATE INDEX idx_data_filter_role ON tb_data_filter(role_id);
CREATE INDEX idx_data_filter_table ON tb_data_filter(target_table);


-- ==========================================
-- 8. 사용자 세션/토큰 테이블
-- ==========================================
CREATE TABLE tb_user_session (
    session_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         BIGINT NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,
    refresh_token   VARCHAR(500),
    ip_address      VARCHAR(50),
    user_agent      TEXT,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_user_session IS '사용자 로그인 세션';
COMMENT ON COLUMN tb_user_session.refresh_token IS 'JWT Refresh Token';
COMMENT ON COLUMN tb_user_session.expires_at IS '세션 만료 시간';

CREATE INDEX idx_session_user ON tb_user_session(user_id);
CREATE INDEX idx_session_expires ON tb_user_session(expires_at);
CREATE INDEX idx_session_refresh ON tb_user_session(refresh_token);


-- ==========================================
-- 9. 비밀번호 변경 이력 테이블 (선택)
-- ==========================================
CREATE TABLE tb_password_history (
    history_id      BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,
    password_hash   VARCHAR(255) NOT NULL,
    changed_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_password_history IS '비밀번호 변경 이력 (재사용 방지)';

CREATE INDEX idx_password_history_user ON tb_password_history(user_id);


-- ==========================================
-- 10. 감사 로그 테이블
-- ==========================================
CREATE TABLE tb_audit_log (
    log_id          BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES tb_user(user_id) ON DELETE SET NULL,
    action_type     VARCHAR(50) NOT NULL,           -- LOGIN, LOGOUT, CREATE, UPDATE, DELETE
    target_type     VARCHAR(50),                    -- USER, ROLE, PERMISSION, TENANT
    target_id       BIGINT,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      VARCHAR(50),
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_audit_log IS '감사 로그 (보안 이벤트 기록)';
COMMENT ON COLUMN tb_audit_log.action_type IS '액션 유형: LOGIN, LOGOUT, CREATE, UPDATE, DELETE';
COMMENT ON COLUMN tb_audit_log.target_type IS '대상 유형: USER, ROLE, PERMISSION, TENANT';

CREATE INDEX idx_audit_log_user ON tb_audit_log(user_id);
CREATE INDEX idx_audit_log_action ON tb_audit_log(action_type);
CREATE INDEX idx_audit_log_target ON tb_audit_log(target_type, target_id);
CREATE INDEX idx_audit_log_created ON tb_audit_log(created_at DESC);


-- ============================================================
-- 기본 데이터 INSERT
-- ============================================================

-- 1. 기본 역할
INSERT INTO tb_role (role_code, role_name, scope_type, is_system, sort_order, description) VALUES
('SYSTEM_ADMIN', '시스템 관리자', 'GLOBAL', true, 1, '전체 시스템 관리 권한 (모든 테넌트, 모든 데이터)'),
('TENANT_ADMIN', '테넌트 총괄 관리자', 'TENANT', true, 2, '해당 테넌트 내 전체 데이터 접근'),
('USER', '일반 사용자', 'USER', true, 3, '본인 데이터만 접근');

-- 2. 기본 권한
INSERT INTO tb_permission (permission_code, permission_name, category, is_system, description) VALUES
-- NL2SQL 권한
('nl2sql:execute', 'NL2SQL 실행', 'nl2sql', true, 'NL2SQL 쿼리 실행 권한'),
('nl2sql:view_all', 'NL2SQL 전체 데이터 조회', 'nl2sql', true, 'NL2SQL에서 모든 데이터 조회 (필터 없음)'),
-- RAG 권한
('rag:search', 'RAG 문서 검색', 'rag', true, '문서 검색 권한'),
-- 문서 권한
('document:read', '문서 조회', 'document', true, '문서 조회 권한'),
('document:write', '문서 등록/수정', 'document', true, '문서 등록 및 수정 권한'),
('document:delete', '문서 삭제', 'document', true, '문서 삭제 권한'),
-- 관리자 권한
('admin:settings', '시스템 설정 관리', 'admin', true, '시스템 설정 조회/수정 권한'),
('admin:users', '사용자 관리', 'admin', true, '사용자/역할/권한 관리 권한'),
('admin:tenants', '테넌트 관리', 'admin', true, '테넌트(고객사) 관리 권한');

-- 3. 시스템 관리자: 전체 권한
INSERT INTO tb_role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM tb_role r
CROSS JOIN tb_permission p
WHERE r.role_code = 'SYSTEM_ADMIN';

-- 4. 고객사 관리자: NL2SQL, RAG, 문서 권한 (admin 제외)
INSERT INTO tb_role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM tb_role r
CROSS JOIN tb_permission p
WHERE r.role_code = 'TENANT_ADMIN'
AND p.permission_code IN ('nl2sql:execute', 'rag:search', 'document:read', 'document:write');

-- 5. 일반 사용자: NL2SQL, RAG, 문서 조회 권한
INSERT INTO tb_role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM tb_role r
CROSS JOIN tb_permission p
WHERE r.role_code = 'USER'
AND p.permission_code IN ('nl2sql:execute', 'rag:search', 'document:read');

-- 6. 기본 테넌트 (테스트용)
INSERT INTO tb_tenant (tenant_code, tenant_name, metadata) VALUES
('SYSTEM', '시스템', '{"type": "internal", "description": "시스템 내부 테넌트"}'),
('DEMO', '데모 테넌트', '{"type": "demo", "description": "데모/테스트용 테넌트"}');

-- 7. 기본 관리자 계정 (비밀번호: admin123! → bcrypt 해시)
-- 실제 운영 시 반드시 비밀번호 변경 필요
INSERT INTO tb_user (username, email, password_hash, display_name, is_superuser, is_active) VALUES
('admin', 'admin@system.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G6E9SiEO6oM9Oy', '시스템 관리자', true, true);
-- 위 해시는 'admin123!' 의 bcrypt 해시 예시입니다. 실제 구현 시 생성 필요

-- 8. 관리자에게 SYSTEM_ADMIN 역할 부여
INSERT INTO tb_user_role (user_id, role_id, tenant_id)
SELECT u.user_id, r.role_id, NULL
FROM tb_user u
CROSS JOIN tb_role r
WHERE u.username = 'admin' AND r.role_code = 'SYSTEM_ADMIN';

-- 9. 데이터 필터 설정 (예시: employee 테이블)
-- 테넌트 관리자: tenant_id 필터
INSERT INTO tb_data_filter (role_id, target_table, filter_column, filter_type)
SELECT r.role_id, 'employee', 'tenant_id', 'TENANT'
FROM tb_role r WHERE r.role_code = 'TENANT_ADMIN';

-- 일반 사용자: emp_id (사용자 본인) 필터
INSERT INTO tb_data_filter (role_id, target_table, filter_column, filter_type)
SELECT r.role_id, 'employee', 'emp_id', 'USER'
FROM tb_role r WHERE r.role_code = 'USER';


-- ============================================================
-- 유틸리티 함수 (선택)
-- ============================================================

-- 사용자의 모든 권한 조회 함수
CREATE OR REPLACE FUNCTION fn_get_user_permissions(p_user_id BIGINT)
RETURNS TABLE(permission_code VARCHAR, permission_name VARCHAR, category VARCHAR)
LANGUAGE SQL
AS $$
    SELECT DISTINCT p.permission_code, p.permission_name, p.category
    FROM tb_user u
    JOIN tb_user_role ur ON u.user_id = ur.user_id
    JOIN tb_role_permission rp ON ur.role_id = rp.role_id
    JOIN tb_permission p ON rp.permission_id = p.permission_id
    WHERE u.user_id = p_user_id
      AND u.is_active = true
    ORDER BY p.category, p.permission_code;
$$;

COMMENT ON FUNCTION fn_get_user_permissions IS '사용자의 모든 권한 목록 조회';


-- 사용자의 데이터 필터 조회 함수
CREATE OR REPLACE FUNCTION fn_get_user_data_filters(p_user_id BIGINT)
RETURNS TABLE(target_table VARCHAR, filter_column VARCHAR, filter_type VARCHAR, filter_sql TEXT)
LANGUAGE SQL
AS $$
    SELECT DISTINCT df.target_table, df.filter_column, df.filter_type, df.filter_sql
    FROM tb_user u
    JOIN tb_user_role ur ON u.user_id = ur.user_id
    JOIN tb_data_filter df ON ur.role_id = df.role_id
    WHERE u.user_id = p_user_id
      AND u.is_active = true
      AND df.is_active = true;
$$;

COMMENT ON FUNCTION fn_get_user_data_filters IS '사용자의 데이터 접근 필터 목록 조회';


-- 만료된 세션 정리 함수
CREATE OR REPLACE FUNCTION fn_cleanup_expired_sessions()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM tb_user_session WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

COMMENT ON FUNCTION fn_cleanup_expired_sessions IS '만료된 세션 정리 (정기 실행 권장)';


-- ============================================================
-- 참고: 초기화 시 실행 순서
-- ============================================================
-- 1. 테이블 생성 (위 DDL)
-- 2. 기본 역할/권한 INSERT
-- 3. 관리자 계정 생성 (비밀번호 해시는 애플리케이션에서 생성)
-- 4. 데이터 필터 설정 (실제 비즈니스 테이블에 맞게 조정)
