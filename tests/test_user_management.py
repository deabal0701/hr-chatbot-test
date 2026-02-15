"""사용자/역할/테넌트/메뉴 관리 테스트 (v2.0 - 메뉴 기반)

위치: tests/test_user_management.py
테스트 대상:
  - Import 검증 (모델, 서비스, 라우터)
  - Pydantic 모델 validation
  - DB 연동 CRUD: 테넌트 → 역할 → 사용자 → 메뉴 권한 할당 → 삭제
  - role_code 기반 접근 제한
  - 역할별 기본 메뉴 템플릿 (get_default_menus)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_all():
    errors = []
    total = 0
    passed = 0

    def ok(msg):
        nonlocal total, passed
        total += 1
        passed += 1
        print(f"  [PASS] {msg}")

    def fail(msg):
        nonlocal total
        total += 1
        errors.append(msg)
        print(f"  [FAIL] {msg}")

    # ===================================
    # 1. Import 확인
    # ===================================
    print("\n[1] Import 검증")

    # 1-1. 모델 import (v2.0)
    try:
        from app.models.user import (
            UserCreate, UserUpdate, UserResponse, UserListResponse,
            RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, RoleSimple,
        )
        ok("models/user.py: 9 classes imported")
    except Exception as e:
        fail(f"models/user.py import: {e}")

    try:
        from app.models.menu import (
            MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse,
            UserMenuPermission, UserMenuAssign, UserMenuResponse,
        )
        ok("models/menu.py: 7 classes imported")
    except Exception as e:
        fail(f"models/menu.py import: {e}")

    try:
        from app.models.tenant import TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
        ok("models/tenant.py: 4 classes imported")
    except Exception as e:
        fail(f"models/tenant.py import: {e}")

    # 1-2. 서비스 import
    try:
        from app.api.services.user_service import user_service, UserService
        assert isinstance(user_service, UserService)
        ok("user_service singleton imported")
    except Exception as e:
        fail(f"user_service import: {e}")

    try:
        from app.api.services.role_service import role_service, RoleService
        assert isinstance(role_service, RoleService)
        ok("role_service singleton imported")
    except Exception as e:
        fail(f"role_service import: {e}")

    try:
        from app.api.services.tenant_service import tenant_service, TenantService
        assert isinstance(tenant_service, TenantService)
        ok("tenant_service singleton imported")
    except Exception as e:
        fail(f"tenant_service import: {e}")

    try:
        from app.api.services.menu_service import menu_service
        ok("menu_service singleton imported")
    except Exception as e:
        fail(f"menu_service import: {e}")

    # 1-3. 라우터 import
    try:
        from app.api.routes.users import router as users_router
        assert users_router.prefix == "/api/admin/v1/users"
        route_paths = [r.path for r in users_router.routes]
        prefix = "/api/admin/v1/users"
        expected = [prefix, f"{prefix}/{{user_id}}", f"{prefix}/{{user_id}}/menus"]
        for ep in expected:
            assert ep in route_paths, f"{ep} not in {route_paths}"
        ok(f"users routes: {len(route_paths)} endpoints, includes /menus")
    except Exception as e:
        fail(f"users routes: {e}")

    try:
        from app.api.routes.roles import router as roles_router
        assert roles_router.prefix == "/api/admin/v1/roles"
        route_paths = [r.path for r in roles_router.routes]
        has_default_menus = any("default-menus" in p for p in route_paths)
        assert has_default_menus, f"default-menus endpoint not found in {route_paths}"
        ok(f"roles routes: {len(route_paths)} endpoints, includes /default-menus")
    except Exception as e:
        fail(f"roles routes: {e}")

    try:
        from app.api.routes.menus import router as menus_router
        assert menus_router.prefix == "/api/admin/v1/menus"
        ok(f"menus routes: prefix={menus_router.prefix}")
    except Exception as e:
        fail(f"menus routes: {e}")

    try:
        from app.api.routes.tenants import router as tenants_router
        assert tenants_router.prefix == "/api/admin/v1/tenants"
        ok(f"tenants routes: prefix={tenants_router.prefix}")
    except Exception as e:
        fail(f"tenants routes: {e}")

    # 1-4. 권한 체크 함수 확인 (v2.0: require_menu_permission)
    try:
        from app.core.security.permission import require_menu_permission, require_superuser
        checker = require_menu_permission("USER_MGMT", "read")
        assert callable(checker)
        ok("require_menu_permission: callable factory verified")
    except Exception as e:
        fail(f"require_menu_permission: {e}")

    # ===================================
    # 2. Pydantic 모델 검증
    # ===================================
    print("\n[2] Pydantic 모델 검증")

    try:
        from app.models.user import UserCreate
        user = UserCreate(login_id="testuser", email="test@example.com", password="Password1!", role_id=1)
        assert user.login_id == "testuser"
        assert user.email == "test@example.com"
        ok("UserCreate: valid data accepted (with role_id)")

        try:
            UserCreate(login_id="test", email="invalid", password="Password1!", role_id=1)
            fail("UserCreate should reject invalid email")
        except Exception:
            ok("UserCreate: invalid email rejected")
    except Exception as e:
        fail(f"UserCreate validation: {e}")

    try:
        from app.models.user import RoleCreate
        role = RoleCreate(role_code="TEST_ROLE", role_name="테스트 역할")
        assert role.role_code == "TEST_ROLE"
        assert role.landing_page == "/chat"
        ok("RoleCreate: basic validation passed (v3.0, no scope_type)")
    except Exception as e:
        fail(f"RoleCreate validation: {e}")

    try:
        from app.models.menu import MenuCreate
        menu = MenuCreate(menu_code="TEST_MENU", menu_name="테스트", menu_type="page")
        assert menu.menu_type == "PAGE"
        assert menu.menu_code == "TEST_MENU"
        ok("MenuCreate: menu_type auto-uppercase, menu_code validated")

        try:
            MenuCreate(menu_code="invalid@code", menu_name="테스트", menu_type="PAGE")
            fail("MenuCreate should reject special chars in code")
        except Exception:
            ok("MenuCreate: invalid menu_code rejected")
    except Exception as e:
        fail(f"MenuCreate validation: {e}")

    try:
        from app.models.tenant import TenantCreate
        tenant = TenantCreate(tenant_code="test_co", tenant_name="테스트 회사")
        assert tenant.tenant_code == "TEST_CO"
        ok("TenantCreate: tenant_code auto-uppercase")

        try:
            TenantCreate(tenant_code="invalid@code!", tenant_name="테스트")
            fail("TenantCreate should reject special chars in code")
        except Exception:
            ok("TenantCreate: invalid tenant_code rejected")
    except Exception as e:
        fail(f"TenantCreate validation: {e}")

    try:
        from app.models.menu import UserMenuPermission, UserMenuAssign
        perm = UserMenuPermission(menu_id=1, can_create=True, can_read=True)
        assert perm.can_create is True
        assert perm.can_delete is False  # default
        assign = UserMenuAssign(menus=[perm])
        assert len(assign.menus) == 1
        ok("UserMenuPermission + UserMenuAssign: valid data accepted")
    except Exception as e:
        fail(f"UserMenuPermission validation: {e}")

    # ===================================
    # 3. DB 연동 테스트
    # ===================================
    print("\n[3] DB 연동 테스트")

    try:
        from app.core.database.connection import db_manager
        from app.api.services.user_service import user_service
        from app.api.services.role_service import role_service
        from app.api.services.tenant_service import tenant_service
        from app.core.errors import APIException, ErrorCode
        from app.models.auth import UserContext

        db_manager.initialize()
        ok("db_manager initialized")

        # admin UserContext 생성 (v3.0: role_code가 데이터 범위 겸용)
        admin_ctx = UserContext(
            user_id=1,
            login_id="admin",
            display_name="시스템 관리자",
            tenant_id=None,
            is_superuser=True,
            role_code="GLOBAL",
        )
        ok(f"admin UserContext: role_code={admin_ctx.role_code}, is_global={admin_ctx.is_global}")

        # 3-1. 테넌트 목록 조회
        try:
            result = tenant_service.list_tenants("test-mgmt")
            assert "total" in result
            assert "items" in result
            ok(f"tenant_service.list_tenants: total={result['total']}")
        except Exception as e:
            fail(f"tenant_service.list_tenants: {e}")

        # 3-2. 역할 목록 조회 (v2.0: user_count 포함, permissions 없음)
        try:
            result = role_service.list_roles("test-mgmt")
            assert "total" in result
            assert "items" in result
            for item in result["items"]:
                assert "user_count" in item, f"역할 {item.get('role_code')}에 user_count 없음"
            ok(f"role_service.list_roles: total={result['total']}, roles={[r['role_code'] for r in result['items']]}")
        except Exception as e:
            fail(f"role_service.list_roles: {e}")

        # 3-3. 역할별 기본 메뉴 템플릿 조회
        try:
            resp = role_service.get_default_menus("GLOBAL", "test-mgmt")
            default_menus = resp["items"]
            assert isinstance(default_menus, list)
            assert len(default_menus) > 0
            # GLOBAL은 모든 PAGE/API 메뉴에 전체 권한
            checked = [m for m in default_menus if m.get("checked")]
            ok(f"role_service.get_default_menus(GLOBAL): total={len(default_menus)}, checked={len(checked)}")

            resp = role_service.get_default_menus("TENANT", "test-mgmt")
            tenant_menus = resp["items"]
            tenant_checked = [m for m in tenant_menus if m.get("checked")]
            ok(f"role_service.get_default_menus(TENANT): total={len(tenant_menus)}, checked={len(tenant_checked)}")

            resp = role_service.get_default_menus("USER", "test-mgmt")
            user_menus = resp["items"]
            user_checked = [m for m in user_menus if m.get("checked")]
            ok(f"role_service.get_default_menus(USER): total={len(user_menus)}, checked={len(user_checked)}")
        except Exception as e:
            fail(f"role_service.get_default_menus: {e}")

        # 3-4. 사용자 목록 조회 (GLOBAL scope → 전체)
        try:
            result = user_service.list_users(admin_ctx, "test-mgmt", limit=5)
            assert "total" in result
            assert "items" in result
            for item in result["items"]:
                assert "role" in item, f"사용자 {item.get('login_id')}에 role 없음"
            ok(f"user_service.list_users (GLOBAL): total={result['total']}")
        except Exception as e:
            fail(f"user_service.list_users: {e}")

        # 3-5. admin 사용자 상세 조회 (v2.0: role 단일 객체)
        try:
            user = user_service.get_user(1, admin_ctx, "test-mgmt")
            assert user["login_id"] == "admin"
            assert "role" in user
            assert user["role"]["role_code"] == "GLOBAL"
            ok(f"user_service.get_user(1): role_code={user['role']['role_code']}")
        except Exception as e:
            fail(f"user_service.get_user: {e}")

        # ===================================
        # 4. CRUD 통합 테스트
        # ===================================
        print("\n[4] CRUD 통합 테스트")

        test_tenant_id = None
        test_role_id = None
        test_user_id = None

        # 4-1. 테넌트 생성
        try:
            tenant = tenant_service.create_tenant(
                {"tenant_code": "TEST_MGMT", "tenant_name": "관리 테스트 테넌트"},
                admin_ctx, "test-mgmt",
            )
            test_tenant_id = tenant["tenant_id"]
            assert tenant["tenant_code"] == "TEST_MGMT"
            ok(f"테넌트 생성: id={test_tenant_id}, code=TEST_MGMT")
        except APIException as e:
            if e.error_code == ErrorCode.DUPLICATE_ERROR:
                with db_manager.get_cursor() as cur:
                    cur.execute("SELECT tenant_id FROM tb_tenant WHERE tenant_code = 'TEST_MGMT'")
                    row = cur.fetchone()
                    if row:
                        test_tenant_id = row["tenant_id"]
                        ok(f"테넌트 이미 존재: id={test_tenant_id}")
            else:
                fail(f"테넌트 생성: {e.message}")
        except Exception as e:
            fail(f"테넌트 생성: {e}")

        # 4-2. 역할 생성
        try:
            role = role_service.create_role(
                {"role_code": "TEST_MGMT_ROLE", "role_name": "관리 테스트 역할"},
                admin_ctx, "test-mgmt",
            )
            test_role_id = role["role_id"]
            ok(f"역할 생성: id={test_role_id}, code=TEST_MGMT_ROLE")
        except APIException as e:
            if e.error_code == ErrorCode.DUPLICATE_ERROR:
                with db_manager.get_cursor() as cur:
                    cur.execute("SELECT role_id FROM tb_role WHERE role_code = 'TEST_MGMT_ROLE'")
                    row = cur.fetchone()
                    if row:
                        test_role_id = row["role_id"]
                        ok(f"역할 이미 존재: id={test_role_id}")
            else:
                fail(f"역할 생성: {e.message}")
        except Exception as e:
            fail(f"역할 생성: {e}")

        # 4-3. 사용자 생성 (v2.0: role_id 단일 + menus)
        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM tb_user WHERE login_id = 'test_mgmt_user'")

            # 메뉴 ID 조회 (USER_CHAT, AGENT_API)
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT menu_id, menu_code FROM tb_menu WHERE menu_code IN ('USER_CHAT', 'AGENT_API')")
                menu_rows = cur.fetchall()

            menu_perms = [{"menu_id": r["menu_id"], "can_create": True, "can_read": True} for r in menu_rows]

            user_data = {
                "login_id": "test_mgmt_user",
                "email": "test_mgmt@example.com",
                "password": "TestPass1!",
                "display_name": "관리 테스트 사용자",
                "tenant_id": test_tenant_id,
                "role_id": test_role_id,
                "is_active": True,
                "menus": menu_perms,
            }
            user = user_service.create_user(user_data, admin_ctx, "test-mgmt")
            test_user_id = user["user_id"]
            assert user["login_id"] == "test_mgmt_user"
            assert user["role"]["role_code"] == "TEST_MGMT_ROLE" if test_role_id else True
            ok(f"사용자 생성: id={test_user_id}, login_id=test_mgmt_user, menus={len(menu_perms)}개")
        except Exception as e:
            fail(f"사용자 생성: {e}")

        # 4-4. 사용자 수정
        if test_user_id:
            try:
                updated = user_service.update_user(
                    test_user_id, {"display_name": "수정된 관리 테스트 사용자"}, admin_ctx, "test-mgmt",
                )
                assert updated["display_name"] == "수정된 관리 테스트 사용자"
                ok(f"사용자 수정: display_name → '수정된 관리 테스트 사용자'")
            except Exception as e:
                fail(f"사용자 수정: {e}")

        # 4-5. 사용자 메뉴 권한 조회
        if test_user_id:
            try:
                result = user_service.get_user_menus(test_user_id, admin_ctx, "test-mgmt")
                assert "menus" in result
                assert isinstance(result["menus"], list)
                ok(f"사용자 메뉴 권한 조회: menus={len(result['menus'])}개")
            except Exception as e:
                fail(f"사용자 메뉴 권한 조회: {e}")

        # 4-6. 사용자 메뉴 권한 재할당 (assign_menus)
        if test_user_id:
            try:
                from app.models.menu import UserMenuPermission

                with db_manager.get_cursor() as cur:
                    cur.execute("SELECT menu_id FROM tb_menu WHERE menu_code = 'USER_CHAT' AND is_active = true")
                    chat_row = cur.fetchone()

                if chat_row:
                    new_menus = [UserMenuPermission(menu_id=chat_row["menu_id"], can_create=True, can_read=True, can_update=True)]
                    result = user_service.assign_menus(test_user_id, new_menus, admin_ctx, "test-mgmt")
                    assert len(result) == 1
                    ok(f"메뉴 권한 재할당: 1개 메뉴 (USER_CHAT), can_update=True")
                else:
                    print("  [SKIP] USER_CHAT 메뉴가 없습니다")
            except Exception as e:
                fail(f"메뉴 권한 재할당: {e}")

        # 4-7. TENANT scope 접근 제한 테스트
        if test_tenant_id:
            try:
                tenant_ctx = UserContext(
                    user_id=9999, login_id="tenant_scope_test",
                    tenant_id=test_tenant_id, is_superuser=False,
                    role_code="TENANT",
                )
                # TENANT scope로 사용자 목록 조회 → 자기 테넌트만
                result = user_service.list_users(tenant_ctx, "test-mgmt", limit=100)
                for item in result["items"]:
                    assert item.get("tenant_id") == test_tenant_id or item.get("tenant_id") is None, \
                        f"TENANT scope인데 다른 테넌트 사용자 {item.get('login_id')} (tenant_id={item.get('tenant_id')}) 조회됨"
                ok(f"TENANT scope 제한: 조회된 {result['total']}명 모두 자기 테넌트")
            except Exception as e:
                fail(f"TENANT scope 테스트: {e}")

        # 4-8. 역할 수정
        if test_role_id:
            try:
                updated = role_service.update_role(
                    test_role_id, {"role_name": "수정된 관리 테스트 역할"}, admin_ctx, "test-mgmt",
                )
                assert updated["role_name"] == "수정된 관리 테스트 역할"
                ok(f"역할 수정: role_name → '수정된 관리 테스트 역할'")
            except Exception as e:
                fail(f"역할 수정: {e}")

        # 4-9. 시스템 역할 삭제 방어
        try:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT role_id FROM tb_role WHERE role_code = 'GLOBAL'")
                sys_role = cur.fetchone()
            if sys_role:
                role_service.delete_role(sys_role["role_id"], admin_ctx, "test-mgmt")
                fail("시스템 역할 삭제가 성공해서는 안 됨")
        except APIException:
            ok("시스템 역할 삭제 방어: APIException raised")
        except Exception as e:
            fail(f"시스템 역할 삭제 방어: {e}")

        # --- Cleanup ---
        print("\n--- Cleanup ---")
        if test_user_id:
            try:
                user_service.delete_user(test_user_id, admin_ctx, "test-mgmt")
                ok(f"테스트 사용자 삭제: id={test_user_id}")
            except Exception as e:
                print(f"  [WARN] 테스트 사용자 삭제 실패: {e}")

        if test_role_id:
            try:
                role_service.delete_role(test_role_id, admin_ctx, "test-mgmt")
                ok(f"테스트 역할 삭제: id={test_role_id}")
            except Exception as e:
                print(f"  [WARN] 테스트 역할 삭제 실패: {e}")

        if test_tenant_id:
            try:
                tenant_service.delete_tenant(test_tenant_id, admin_ctx, "test-mgmt")
                ok(f"테스트 테넌트 삭제: id={test_tenant_id}")
            except Exception as e:
                print(f"  [WARN] 테스트 테넌트 삭제 실패: {e}")

        db_manager.close()

    except Exception as e:
        fail(f"DB integration: {e}")

    # ===================================
    # Summary
    # ===================================
    print(f"\n{'='*60}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {len(errors)}")
    print(f"{'='*60}")
    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  - {e}")
        assert False, f"{len(errors)} tests failed"
    else:
        print("\nALL TESTS PASSED - User Management v2.0 OK")


if __name__ == "__main__":
    test_all()
