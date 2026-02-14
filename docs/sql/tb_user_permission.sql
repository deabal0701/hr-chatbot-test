-- ============================================================
-- 사용자 및 메뉴 기반 권한 관리 테이블 DDL (v2.0)
-- 파일: docs/sql/tb_user_permission.sql
-- 작성일: 2026-02-06
-- 수정일: 2026-02-14
-- 변경: permission 코드 기반 → 메뉴 기반 권한 관리 체계 전면 전환
--
-- 테이블 구성 (6개):
--   tb_tenant       : 테넌트(고객사)
--   tb_role         : 역할 (scope_type + landing_page)
--   tb_user         : 사용자 (role_id FK 직접 보유, 1:N)
--   tb_menu         : 메뉴 트리 (parent_menu_id 자기참조)
--   tb_user_menu    : 사용자별 메뉴 CRUD 권한 (★ 유일한 권한 체크 테이블)
--   tb_user_session : JWT 세션
--
-- 제거된 테이블 (v1.0 대비):
--   tb_permission, tb_role_permission, tb_user_role, tb_data_filter
-- ============================================================


-- ==========================================
-- 0. 기존 테이블 삭제 (재생성 시)
-- ==========================================
DROP TABLE IF EXISTS tb_user_session CASCADE;
DROP TABLE IF EXISTS tb_user_menu CASCADE;
DROP TABLE IF EXISTS tb_menu CASCADE;
DROP TABLE IF EXISTS tb_user CASCADE;
DROP TABLE IF EXISTS tb_role CASCADE;
DROP TABLE IF EXISTS tb_tenant CASCADE;
-- v1.0 잔존 테이블 정리
DROP TABLE IF EXISTS tb_data_filter CASCADE;
DROP TABLE IF EXISTS tb_user_role CASCADE;
DROP TABLE IF EXISTS tb_role_permission CASCADE;
DROP TABLE IF EXISTS tb_permission CASCADE;


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


-- ==========================================
-- 2. 역할(Role) 테이블
-- ==========================================
CREATE TABLE tb_role (
    role_id         BIGSERIAL PRIMARY KEY,
    role_code       VARCHAR(50) UNIQUE NOT NULL,    -- SYSTEM_ADMIN, TENANT_ADMIN, USER
    role_name       VARCHAR(100) NOT NULL,
    description     TEXT,
    scope_type      VARCHAR(20) NOT NULL,           -- GLOBAL, TENANT, USER (데이터 범위)
    landing_page    VARCHAR(200) NOT NULL DEFAULT '/chat',  -- 로그인 후 랜딩 페이지
    is_system       BOOLEAN DEFAULT false,          -- 시스템 기본 역할 (삭제 불가)
    sort_order      INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_role_scope CHECK (scope_type IN ('GLOBAL', 'TENANT', 'USER'))
);

COMMENT ON TABLE tb_role IS '역할 정의';
COMMENT ON COLUMN tb_role.role_code IS '역할 코드 (시스템 내부 식별자)';
COMMENT ON COLUMN tb_role.scope_type IS '데이터 범위: GLOBAL(전체), TENANT(테넌트), USER(사용자) - 서비스 레이어에서 NL2SQL WHERE 조건 유도';
COMMENT ON COLUMN tb_role.landing_page IS '로그인 후 랜딩 페이지 URL';
COMMENT ON COLUMN tb_role.is_system IS '시스템 기본 역할 (삭제 불가)';

CREATE INDEX idx_role_scope ON tb_role(scope_type);


-- ==========================================
-- 3. 사용자 테이블
-- ==========================================
-- v2.0 변경: role_id FK 직접 보유 (1:N, tb_user_role M:N 삭제)
CREATE TABLE tb_user (
    user_id         BIGSERIAL PRIMARY KEY,
    login_id        VARCHAR(100) UNIQUE NOT NULL,   -- 로그인 ID
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,          -- bcrypt 해시
    display_name    VARCHAR(100),
    tenant_id       BIGINT REFERENCES tb_tenant(tenant_id) ON DELETE SET NULL,
    role_id         BIGINT NOT NULL REFERENCES tb_role(role_id) ON DELETE RESTRICT,
    is_active       BOOLEAN DEFAULT true,
    is_superuser    BOOLEAN DEFAULT false,          -- RBAC 비상 안전장치
    last_login_at   TIMESTAMPTZ,
    login_fail_count INT DEFAULT 0,                 -- 로그인 실패 횟수
    locked_until    TIMESTAMPTZ,                    -- 계정 잠금 해제 시간
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE tb_user IS '사용자 정보';
COMMENT ON COLUMN tb_user.login_id IS '로그인 ID';
COMMENT ON COLUMN tb_user.password_hash IS '비밀번호 해시 (bcrypt)';
COMMENT ON COLUMN tb_user.role_id IS '역할 ID (사용자는 정확히 하나의 역할에 소속)';
COMMENT ON COLUMN tb_user.is_superuser IS 'RBAC 비상 안전장치 (메뉴 설정 꼬임 시 접근 유지용, 최소 1명)';
COMMENT ON COLUMN tb_user.login_fail_count IS '연속 로그인 실패 횟수 (잠금 정책용)';
COMMENT ON COLUMN tb_user.locked_until IS '계정 잠금 해제 시간 (NULL이면 잠금 아님)';

CREATE INDEX idx_user_tenant ON tb_user(tenant_id);
CREATE INDEX idx_user_role ON tb_user(role_id);
CREATE INDEX idx_user_active ON tb_user(is_active);


-- ==========================================
-- 4. 메뉴 테이블 (트리 구조)
-- ==========================================
CREATE TABLE tb_menu (
    menu_id         BIGSERIAL PRIMARY KEY,
    parent_menu_id  BIGINT REFERENCES tb_menu(menu_id) ON DELETE SET NULL,
    menu_code       VARCHAR(50) UNIQUE NOT NULL,    -- 메뉴 코드 (시스템 내부 식별자)
    menu_name       VARCHAR(100) NOT NULL,          -- 메뉴 표시명
    menu_type       VARCHAR(20) NOT NULL,           -- DIRECTORY, PAGE, API
    menu_path       VARCHAR(200),                   -- 프론트엔드 URL 경로
    api_pattern     VARCHAR(200),                   -- 연결 API 경로 패턴
    icon            VARCHAR(50),                    -- 아이콘 클래스
    sort_order      INT DEFAULT 0,
    depth           INT DEFAULT 0,                  -- 트리 깊이 (0=루트)
    is_active       BOOLEAN DEFAULT true,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_menu_type CHECK (menu_type IN ('DIRECTORY', 'PAGE', 'API')),
    CONSTRAINT chk_menu_depth CHECK (depth >= 0 AND depth <= 5)
);

COMMENT ON TABLE tb_menu IS '메뉴 트리 구조';
COMMENT ON COLUMN tb_menu.parent_menu_id IS '상위 메뉴 ID (NULL이면 루트)';
COMMENT ON COLUMN tb_menu.menu_code IS '메뉴 코드 (권한 체크 시 사용)';
COMMENT ON COLUMN tb_menu.menu_type IS 'DIRECTORY(폴더), PAGE(화면), API(API접근제어)';
COMMENT ON COLUMN tb_menu.menu_path IS '프론트엔드 라우트 경로 (PAGE 타입)';
COMMENT ON COLUMN tb_menu.api_pattern IS 'API 경로 패턴 (API 타입)';
COMMENT ON COLUMN tb_menu.depth IS '트리 깊이 (0=루트, 최대 5)';

CREATE INDEX idx_menu_parent ON tb_menu(parent_menu_id);
CREATE INDEX idx_menu_type ON tb_menu(menu_type);
CREATE INDEX idx_menu_active ON tb_menu(is_active);
CREATE INDEX idx_menu_sort ON tb_menu(depth, sort_order);


-- ==========================================
-- 5. 사용자-메뉴 권한 테이블 (★ 유일한 권한 체크 테이블)
-- ==========================================
CREATE TABLE tb_user_menu (
    user_id         BIGINT NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,
    menu_id         BIGINT NOT NULL REFERENCES tb_menu(menu_id) ON DELETE CASCADE,
    can_create      BOOLEAN DEFAULT false,          -- 등록 권한
    can_read        BOOLEAN DEFAULT true,           -- 조회 권한
    can_update      BOOLEAN DEFAULT false,          -- 수정 권한
    can_delete      BOOLEAN DEFAULT false,          -- 삭제 권한
    can_export      BOOLEAN DEFAULT false,          -- 내보내기 권한
    granted_at      TIMESTAMPTZ DEFAULT NOW(),
    granted_by      BIGINT REFERENCES tb_user(user_id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, menu_id)
);

COMMENT ON TABLE tb_user_menu IS '사용자별 메뉴 CRUD 권한 (유일한 런타임 권한 체크 테이블)';
COMMENT ON COLUMN tb_user_menu.can_create IS '등록 권한 (POST)';
COMMENT ON COLUMN tb_user_menu.can_read IS '조회 권한 (GET)';
COMMENT ON COLUMN tb_user_menu.can_update IS '수정 권한 (PUT)';
COMMENT ON COLUMN tb_user_menu.can_delete IS '삭제 권한 (DELETE)';
COMMENT ON COLUMN tb_user_menu.can_export IS '내보내기 권한 (Excel 등)';
COMMENT ON COLUMN tb_user_menu.granted_by IS '권한 부여자 ID';

-- PK (user_id, menu_id) 복합 인덱스 자동 생성됨
CREATE INDEX idx_user_menu_menu ON tb_user_menu(menu_id);
CREATE INDEX idx_user_menu_granted ON tb_user_menu(granted_by);


-- ==========================================
-- 6. 사용자 세션/토큰 테이블
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


-- ============================================================
-- 기본 데이터 INSERT
-- ============================================================

-- ==========================================
-- 1. 기본 역할 (3개)
-- ==========================================
-- scope_type: NL2SQL 데이터 필터 범위를 서비스 레이어에서 유도
--   GLOBAL → 필터 없음 (전체 데이터)
--   TENANT → WHERE tenant_id = ?
--   USER   → WHERE tenant_id = ? AND emp_id = ?
INSERT INTO tb_role (role_code, role_name, scope_type, landing_page, is_system, sort_order, description) VALUES
('SYSTEM_ADMIN', '시스템 관리자', 'GLOBAL', '/admin/dashboard', true, 1, '전체 시스템 관리 (모든 메뉴, 모든 데이터)'),
('TENANT_ADMIN', '테넌트 관리자', 'TENANT', '/admin/dashboard', true, 2, '테넌트 내 관리 (제한된 메뉴, 테넌트 데이터)'),
('USER',         '일반 사용자',   'USER',   '/chat',             true, 3, '일반 사용자 (채팅만, 본인 데이터)');


-- ==========================================
-- 2. 기본 메뉴 (계층 구조: DIRECTORY + PAGE)
-- ==========================================
-- 명명 규칙:
--   DIRECTORY: DIR_ 접두어 (DIR_ROOT, DIR_USER, DIR_SYSTEM)
--   PAGE:      _MGMT 접미어 통일 (관리 화면), 기능 화면은 서술적 이름

-- 2-1. 루트 DIRECTORY (depth=0) — 사이드바에서 투명 (자식만 표시)
INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, icon, sort_order, depth, description) VALUES
('DIR_ROOT', '관리', 'DIRECTORY', NULL, NULL, 'settings', 1, 0, '최상위 관리 그룹 (사이드바에서 자식만 표시)');

-- 2-2. PAGE 메뉴 (depth=1, parent=DIR_ROOT)
INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, api_pattern, icon, sort_order, depth, description) VALUES
('DASHBOARD',   '대시보드',   'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), '/admin/dashboard',  '/api/admin/v1/dashboard',  'dashboard', 1, 1, '대시보드'),
('AI_CHAT',     'AI 채팅',    'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), '/chat',             NULL,                        'chat',      2, 1, '사용자 AI 채팅 화면'),
('AI_SEARCH',   '자연어 검색', 'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), '/admin/chat',       NULL,                        'search',    3, 1, '관리자 자연어 검색'),
('DOC_MGMT',    '문서 관리',  'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), '/admin/documents',  '/api/admin/v1/documents',  'document',  4, 1, '지식문서 관리'),
('SEARCH_HIST', '검색 이력',  'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), '/admin/history',    '/api/admin/v1/history',    'history',   5, 1, '검색 이력 조회');

-- 2-3. 사용자 관리 DIRECTORY (depth=1)
INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, icon, sort_order, depth, description) VALUES
('DIR_USER', '사용자 관리', 'DIRECTORY', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), NULL, 'users', 6, 1, '사용자/역할/테넌트 관리 그룹');

INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, api_pattern, icon, sort_order, depth, description) VALUES
('USER_MGMT',   '사용자 관리',  'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_USER'), '/admin/users',    '/api/admin/v1/users',    'users',  1, 2, '사용자 CRUD + 메뉴 권한 할당'),
('ROLE_MGMT',   '역할 관리',    'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_USER'), '/admin/roles',    '/api/admin/v1/roles',    'role',   2, 2, '역할 CRUD'),
('TENANT_MGMT', '테넌트 관리',  'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_USER'), '/admin/tenants',  '/api/admin/v1/tenants',  'tenant', 3, 2, '테넌트 CRUD');

-- 2-4. 시스템 관리 DIRECTORY (depth=1)
INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, icon, sort_order, depth, description) VALUES
('DIR_SYSTEM', '시스템 관리', 'DIRECTORY', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_ROOT'), NULL, 'settings', 7, 1, '메뉴/코드/시스템 설정 그룹');

INSERT INTO tb_menu (menu_code, menu_name, menu_type, parent_menu_id, menu_path, api_pattern, icon, sort_order, depth, description) VALUES
('MENU_MGMT',   '메뉴 관리',    'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_SYSTEM'), '/admin/menus',     '/api/admin/v1/menus',     'menu',     1, 2, '메뉴 트리 관리'),
('CODE_MGMT',   '코드 관리',    'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_SYSTEM'), '/admin/codes',     '/api/admin/v1/codes',     'code',     2, 2, '코드 관리'),
('SYS_SETTING', '시스템 설정',  'PAGE', (SELECT menu_id FROM tb_menu WHERE menu_code='DIR_SYSTEM'), '/admin/settings',  '/api/admin/v1/settings',  'settings', 3, 2, '시스템 설정 관리');


-- ==========================================
-- 3. 기본 테넌트 (테스트용)
-- ==========================================
INSERT INTO tb_tenant (tenant_code, tenant_name, metadata) VALUES
('SYSTEM', '시스템',       '{"type": "internal", "description": "시스템 내부 테넌트"}'),
('DEMO',   '데모 테넌트',  '{"type": "demo", "description": "데모/테스트용 테넌트"}');


-- ==========================================
-- 4. 기본 관리자 계정
-- ==========================================
-- 비밀번호: admin123! → bcrypt 해시 (실 운영 시 반드시 변경)
INSERT INTO tb_user (login_id, email, password_hash, display_name, role_id, is_superuser, is_active)
SELECT 'admin', 'admin@system.local',
       '$2b$12$LzCrXdBqNOyeBaSts14cXOWmt/B8DB0E5UsnuqkKk3QTkn91uSuHW',
       '시스템 관리자',
       r.role_id, true, true
FROM tb_role r WHERE r.role_code = 'SYSTEM_ADMIN';


-- ==========================================
-- 5. 관리자 메뉴 권한 (SYSTEM_ADMIN → 전체 메뉴)
-- ==========================================
-- 시스템 관리자: 모든 PAGE/API 메뉴에 전체 CRUD 권한
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id,
       true, true, true, true, true
FROM tb_user u
CROSS JOIN tb_menu m
WHERE u.login_id = 'admin'
AND m.menu_type IN ('PAGE', 'API');


-- ==========================================
-- 6. 테스트 계정: 테넌트 관리자
-- ==========================================
INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, role_id, is_active)
SELECT 'tenant_admin', 'tenant_admin@demo.local',
       '$2b$12$LzCrXdBqNOyeBaSts14cXOWmt/B8DB0E5UsnuqkKk3QTkn91uSuHW',
       '데모 테넌트 관리자',
       t.tenant_id, r.role_id, true
FROM tb_tenant t, tb_role r
WHERE t.tenant_code = 'DEMO' AND r.role_code = 'TENANT_ADMIN';

-- 테넌트 관리자 메뉴 권한: 제한된 메뉴만
-- 대시보드: R
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, false, true, false, false, false
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'DASHBOARD';

-- AI 검색: CR
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, false, false, false
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'AI_SEARCH';

-- 문서 관리: CRUDE
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, true, true, true
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'DOC_MGMT';

-- 사용자 관리: CRU (삭제 불가)
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, true, false, false
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'USER_MGMT';

-- 검색 이력: RE
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, false, true, false, false, true
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'SEARCH_HIST';

-- AI 채팅: CR
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, false, false, false
FROM tb_user u, tb_menu m WHERE u.login_id = 'tenant_admin' AND m.menu_code = 'AI_CHAT';


-- API 접근: CR (Agent, RAG, NL2SQL)
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, false, false, false
FROM tb_user u
CROSS JOIN tb_menu m
WHERE u.login_id = 'tenant_admin'
AND m.menu_code IN ('AGENT_API', 'RAG_API', 'NL2SQL_API');


-- ==========================================
-- 7. 테스트 계정: 일반 사용자
-- ==========================================
INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, role_id, is_active)
SELECT 'user01', 'user01@demo.local',
       '$2b$12$LzCrXdBqNOyeBaSts14cXOWmt/B8DB0E5UsnuqkKk3QTkn91uSuHW',
       '테스트 사용자',
       t.tenant_id, r.role_id, true
FROM tb_tenant t, tb_role r
WHERE t.tenant_code = 'DEMO' AND r.role_code = 'USER';

-- 일반 사용자 메뉴 권한: 채팅 + API만
-- AI 채팅: CR
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, false, false, false
FROM tb_user u, tb_menu m WHERE u.login_id = 'user01' AND m.menu_code = 'AI_CHAT';

-- API 접근: CR (Agent, RAG, NL2SQL)
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT u.user_id, m.menu_id, true, true, false, false, false
FROM tb_user u
CROSS JOIN tb_menu m
WHERE u.login_id = 'user01'
AND m.menu_code IN ('AGENT_API', 'RAG_API', 'NL2SQL_API');


-- ============================================================
-- 확인 쿼리 (실행 후 검증용)
-- ============================================================

-- 테이블 생성 확인
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'tb_%' ORDER BY tablename;

-- 역할 목록
-- SELECT role_id, role_code, role_name, scope_type, landing_page FROM tb_role ORDER BY sort_order;

-- 메뉴 트리 (depth 순 정렬)
-- SELECT menu_id, REPEAT('  ', depth) || menu_name AS menu_tree, menu_code, menu_type, menu_path, depth
-- FROM tb_menu ORDER BY depth, sort_order;

-- 사용자별 메뉴 권한 확인
-- SELECT u.login_id, u.display_name, r.role_code, r.scope_type,
--        m.menu_code, m.menu_name,
--        um.can_create AS c, um.can_read AS r, um.can_update AS u, um.can_delete AS d, um.can_export AS e
-- FROM tb_user_menu um
-- JOIN tb_user u ON u.user_id = um.user_id
-- JOIN tb_menu m ON m.menu_id = um.menu_id
-- JOIN tb_role r ON r.role_id = u.role_id
-- ORDER BY u.login_id, m.depth, m.sort_order;

-- 사용자별 접근 가능 메뉴 수
-- SELECT u.login_id, r.role_code, COUNT(*) AS menu_count
-- FROM tb_user_menu um
-- JOIN tb_user u ON u.user_id = um.user_id
-- JOIN tb_role r ON r.role_id = u.role_id
-- GROUP BY u.login_id, r.role_code
-- ORDER BY u.login_id;


-- ============================================================
-- 핵심 설계 원칙
-- ============================================================
-- 1. tb_user_menu = 유일한 런타임 권한 체크 테이블
--    프론트엔드 메뉴 렌더링 + 백엔드 API 권한 체크 모두 이 테이블만 조회
--
-- 2. tb_role.scope_type = 데이터 범위 결정
--    서비스 레이어에서 scope_type을 읽어 NL2SQL WHERE 조건 코드로 유도
--    GLOBAL → 필터 없음 | TENANT → tenant_id = ? | USER → tenant_id = ? AND emp_id = ?
--
-- 3. 사용자 1명 = 역할 1개 (tb_user.role_id FK, 1:N)
--    M:N 매핑 테이블(tb_user_role) 제거로 단순화
--
-- 4. 메뉴 트리 (tb_menu.parent_menu_id 자기참조)
--    DB에서 메뉴 추가/삭제 → 프론트엔드 코드 변경 없이 자동 반영
--
-- 5. 사용자 생성 시
--    역할 선택 → UI에서 해당 역할 기본 메뉴 자동 체크 → 관리자가 개별 조정 → tb_user_menu INSERT
