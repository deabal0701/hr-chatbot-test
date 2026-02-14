-- ============================================================
-- scope_type 제거 및 role_code 통합 마이그레이션
-- 파일: docs/sql/migration_role_scope.sql
-- 작성일: 2026-02-14
-- 설계서: docs/design/user_tenant.md v3.0
--
-- 변경 내용:
--   1. role_code 변경: SYSTEM_ADMIN → GLOBAL, TENANT_ADMIN → TENANT
--   2. scope_type 컬럼/제약조건/인덱스 삭제
--   role_code가 데이터 접근 범위를 직접 결정 (scope_type과 동일 역할)
-- ============================================================

BEGIN;

-- 1. role_code 변경
UPDATE tb_role SET role_code = 'GLOBAL' WHERE role_code = 'SYSTEM_ADMIN';
UPDATE tb_role SET role_code = 'TENANT' WHERE role_code = 'TENANT_ADMIN';
-- USER는 변경 없음

-- 2. scope_type 관련 제약조건/인덱스 삭제
ALTER TABLE tb_role DROP CONSTRAINT IF EXISTS chk_role_scope;
DROP INDEX IF EXISTS idx_role_scope;

-- 3. scope_type 컬럼 삭제
ALTER TABLE tb_role DROP COLUMN IF EXISTS scope_type;

-- 4. 검증
-- SELECT role_id, role_code, role_name, landing_page, is_system FROM tb_role ORDER BY sort_order;

COMMIT;
