"""모델 Import 및 Validation 테스트 (v2.0 - 메뉴 기반)

위치: tests/test_models.py
테스트 대상:
  - auth.py: LoginRequest, UserInfo, TokenResponse, UserContext 등
  - user.py: UserCreate, RoleCreate, RoleSimple 등 (v2.0: role_id 단일, menus)
  - menu.py: MenuCreate, UserMenuPermission, UserMenuAssign 등 (v2.0 신규)
  - tenant.py: TenantCreate auto-uppercase 등
  - config.py: JWT/비밀번호 관련 설정 필드
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
    # 1. auth.py import
    # ===================================
    print("\n[1] auth.py import")
    try:
        from app.models.auth import (
            LoginRequest, UserInfo, TokenResponse,
            RefreshRequest, PasswordChangeRequest, UserContext,
            MenuPermission
        )
        ok("auth.py - 7 classes imported (incl. MenuPermission)")
    except Exception as e:
        fail(f"auth.py import: {e}")

    # ===================================
    # 2. user.py import (v2.0)
    # ===================================
    print("\n[2] user.py import (v2.0)")
    try:
        from app.models.user import (
            UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
            RoleSimple, RoleCreate, RoleUpdate, RoleResponse, RoleListResponse
        )
        ok("user.py - 10 classes imported (v2.0: no UserRoleAssign, no PermissionResponse)")
    except Exception as e:
        fail(f"user.py import: {e}")

    # v2.0: 제거된 클래스 확인
    try:
        import app.models.user as user_module
        removed = ["UserRoleAssign", "RolePermissionAssign", "PermissionResponse", "PermissionSimple", "DataFilterResponse"]
        for cls_name in removed:
            assert not hasattr(user_module, cls_name), f"{cls_name}이 아직 존재함 (v2.0에서 제거되어야 함)"
        ok(f"v2.0 removed classes verified: {', '.join(removed)}")
    except Exception as e:
        fail(f"v2.0 removed classes: {e}")

    # ===================================
    # 3. menu.py import (v2.0 신규)
    # ===================================
    print("\n[3] menu.py import (v2.0)")
    try:
        from app.models.menu import (
            MenuBase, MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse,
            UserMenuPermission, UserMenuAssign, UserMenuResponse
        )
        ok("menu.py - 8 classes imported")
    except Exception as e:
        fail(f"menu.py import: {e}")

    # ===================================
    # 4. tenant.py import
    # ===================================
    print("\n[4] tenant.py import")
    try:
        from app.models.tenant import (
            TenantBase, TenantCreate, TenantUpdate,
            TenantResponse, TenantListResponse
        )
        ok("tenant.py - 5 classes imported")
    except Exception as e:
        fail(f"tenant.py import: {e}")

    # ===================================
    # 5. config.py import
    # ===================================
    print("\n[5] config.py import")
    try:
        from app.config import Settings
        s = Settings(
            database_url="postgresql://test:test@localhost/test",
            openai_api_key="sk-test"
        )
        assert hasattr(s, "jwt_refresh_token_expire_days"), "jwt_refresh_token_expire_days missing"
        assert hasattr(s, "password_min_length"), "password_min_length missing"
        assert hasattr(s, "login_max_fail_count"), "login_max_fail_count missing"
        assert hasattr(s, "login_lock_minutes"), "login_lock_minutes missing"
        ok(f"config.py - 4 auth fields verified (refresh={s.jwt_refresh_token_expire_days}d, pwd_min={s.password_min_length}, max_fail={s.login_max_fail_count}, lock={s.login_lock_minutes}m)")
    except Exception as e:
        fail(f"config.py: {e}")

    # ===================================
    # 6. Validation 테스트
    # ===================================
    print("\n[6] Pydantic Validation")

    # 6-1. LoginRequest
    try:
        from app.models.auth import LoginRequest
        req = LoginRequest(login_id="testuser", password="Pass1234!")
        assert req.login_id == "testuser"
        ok("LoginRequest: basic validation passed")
    except Exception as e:
        fail(f"LoginRequest validation: {e}")

    # 6-2. TenantCreate auto-uppercase
    try:
        from app.models.tenant import TenantCreate
        t = TenantCreate(tenant_code="company_a", tenant_name="A사")
        assert t.tenant_code == "COMPANY_A"
        ok("TenantCreate: tenant_code auto-uppercase passed")
    except Exception as e:
        fail(f"TenantCreate validation: {e}")

    # 6-3. UserCreate (v2.0: role_id 단일, menus 필드)
    try:
        from app.models.user import UserCreate
        u = UserCreate(
            login_id="user01", email="user01@test.com",
            password="Password1!", tenant_id=1, role_id=3
        )
        assert u.email == "user01@test.com"
        assert u.role_id == 3
        assert isinstance(u.menus, list)
        ok(f"UserCreate: role_id={u.role_id}, menus={len(u.menus)} (v2.0 validated)")
    except Exception as e:
        fail(f"UserCreate validation: {e}")

    # 6-4. UserCreate with menus
    try:
        from app.models.user import UserCreate
        from app.models.menu import UserMenuPermission
        u = UserCreate(
            login_id="user02", email="user02@test.com",
            password="Password1!", tenant_id=1, role_id=2,
            menus=[
                UserMenuPermission(menu_id=4, can_read=True),
                UserMenuPermission(menu_id=5, can_create=True, can_read=True, can_export=True)
            ]
        )
        assert len(u.menus) == 2
        assert u.menus[0].menu_id == 4
        assert u.menus[0].can_read is True
        assert u.menus[0].can_create is False
        assert u.menus[1].can_export is True
        ok(f"UserCreate with menus: {len(u.menus)} menus, permissions verified")
    except Exception as e:
        fail(f"UserCreate with menus: {e}")

    # 6-5. RoleCreate (v3.0: scope_type 제거)
    try:
        from app.models.user import RoleCreate
        r = RoleCreate(
            role_code="TEST_ROLE", role_name="테스트"
        )
        assert r.role_code == "TEST_ROLE"
        assert r.landing_page == "/chat"  # default
        ok("RoleCreate: basic validation passed (no scope_type)")
    except Exception as e:
        fail(f"RoleCreate validation: {e}")

    # 6-7. MenuCreate validation
    try:
        from app.models.menu import MenuCreate
        m = MenuCreate(
            menu_code="new_page", menu_name="새 페이지",
            menu_type="page", menu_path="/admin/new"
        )
        assert m.menu_code == "NEW_PAGE"
        assert m.menu_type == "PAGE"
        ok(f"MenuCreate: menu_code={m.menu_code}, menu_type={m.menu_type} (auto-uppercase)")
    except Exception as e:
        fail(f"MenuCreate validation: {e}")

    # 6-8. MenuCreate invalid menu_type
    try:
        from app.models.menu import MenuCreate
        try:
            MenuCreate(menu_code="BAD", menu_name="Bad", menu_type="WIDGET")
            fail("MenuCreate: invalid menu_type should raise ValueError")
        except ValueError:
            ok("MenuCreate: invalid menu_type raises ValueError")
    except Exception as e:
        fail(f"MenuCreate menu_type validation: {e}")

    # 6-9. UserMenuAssign validation
    try:
        from app.models.menu import UserMenuAssign, UserMenuPermission
        assign = UserMenuAssign(menus=[
            UserMenuPermission(menu_id=4, can_read=True),
            UserMenuPermission(menu_id=5, can_create=True, can_read=True)
        ])
        assert len(assign.menus) == 2
        ok(f"UserMenuAssign: {len(assign.menus)} menus")
    except Exception as e:
        fail(f"UserMenuAssign validation: {e}")

    # 6-10. UserMenuAssign empty menus → 실패
    try:
        from app.models.menu import UserMenuAssign
        try:
            UserMenuAssign(menus=[])
            fail("UserMenuAssign: empty menus should raise ValueError")
        except ValueError:
            ok("UserMenuAssign: empty menus raises ValueError")
    except Exception as e:
        fail(f"UserMenuAssign empty: {e}")

    # 6-11. UserContext (v3.0: scope_type 제거, role_code가 데이터 범위 겸용)
    try:
        from app.models.auth import UserContext
        ctx = UserContext(
            user_id=1, login_id="admin",
            is_superuser=True, role_code="GLOBAL"
        )
        assert ctx.is_global is True
        assert ctx.is_tenant_scope is False
        assert ctx.is_user_scope is False
        ok(f"UserContext: is_global={ctx.is_global}, role_code={ctx.role_code}")

        ctx2 = UserContext(
            user_id=2, login_id="tenant_admin",
            tenant_id=1, role_code="TENANT"
        )
        assert ctx2.is_global is False
        assert ctx2.is_tenant_scope is True
        ok(f"UserContext: is_tenant_scope={ctx2.is_tenant_scope}, tenant_id={ctx2.tenant_id}")
    except Exception as e:
        fail(f"UserContext validation: {e}")

    # 6-12. PasswordChangeRequest validation
    try:
        from app.models.auth import PasswordChangeRequest
        # 유효한 비밀번호
        p = PasswordChangeRequest(current_password="old", new_password="NewPass1!")
        assert p.new_password == "NewPass1!"
        ok("PasswordChangeRequest: valid password accepted")

        # 복잡도 미달 (대문자/소문자/숫자 미포함)
        try:
            PasswordChangeRequest(current_password="old", new_password="onlylower")
            fail("PasswordChangeRequest: weak password should raise ValueError")
        except ValueError:
            ok("PasswordChangeRequest: weak password raises ValueError")
    except Exception as e:
        fail(f"PasswordChangeRequest: {e}")

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
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED - Models v2.0 OK")
        sys.exit(0)


if __name__ == "__main__":
    test_all()
