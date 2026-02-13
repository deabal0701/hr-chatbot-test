"""보안 모듈 통합 테스트 (v2.0 - 메뉴 기반 권한)

위치: tests/test_security.py
테스트 대상:
  1. password.py     — bcrypt 해싱/검증
  2. jwt.py          — Access/Refresh Token 생성/검증 (v2.0: role_code)
  3. dependencies.py — FastAPI 인증 의존성 임포트
  4. permission.py   — require_menu_permission, require_superuser
  5. 통합: JWT → UserContext (v2.0)
  6. DB 연동: authenticate, get_user_with_permissions, session flow, change_password, menu permission
"""
import sys
import os
import time

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
    # 1. password.py 테스트
    # ===================================
    print("\n[1] password.py - bcrypt 해싱/검증")
    try:
        from app.core.security.password import hash_password, verify_password

        hashed = hash_password("admin123!")
        assert hashed.startswith("$2b$"), f"bcrypt 형식이 아님: {hashed[:10]}"
        ok(f"hash_password: {hashed[:30]}...")

        assert verify_password("admin123!", hashed) is True
        ok("verify_password (correct): True")

        assert verify_password("wrong_password", hashed) is False
        ok("verify_password (wrong): False")

        hashed2 = hash_password("admin123!")
        assert hashed != hashed2, "같은 입력인데 같은 해시 (salt 미동작)"
        ok("salt: different hashes for same input")

    except Exception as e:
        fail(f"password: {e}")

    # ===================================
    # 2. jwt.py 테스트 (v2.0 - role_code)
    # ===================================
    print("\n[2] jwt.py - Access/Refresh Token (v2.0)")
    try:
        from app.core.security.jwt import create_access_token, create_refresh_token, verify_token, TokenPayload
        from app.core.errors import APIException

        # 2-1. Access Token 생성 (v2.0: role_code, scope_type)
        token_data = {
            "sub": "1",
            "login_id": "admin",
            "display_name": "시스템 관리자",
            "tenant_id": None,
            "scope_type": "GLOBAL",
            "role_code": "SYSTEM_ADMIN",
            "is_superuser": True,
        }
        access_token = create_access_token(token_data)
        assert isinstance(access_token, str) and len(access_token) > 50
        ok(f"create_access_token: {access_token[:50]}...")

        # 2-2. Access Token 검증
        payload = verify_token(access_token)
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "1"
        assert payload.login_id == "admin"
        assert payload.scope_type == "GLOBAL"
        assert payload.role_code == "SYSTEM_ADMIN"
        assert payload.token_type == "access"
        assert payload.is_superuser is True
        ok(f"verify_token: sub={payload.sub}, role_code={payload.role_code}, type={payload.token_type}")

        # 2-3. Refresh Token 생성 및 검증
        refresh_data = {"sub": "1", "session_id": "test-session-uuid"}
        refresh_token = create_refresh_token(refresh_data)
        refresh_payload = verify_token(refresh_token)
        assert refresh_payload.token_type == "refresh"
        assert refresh_payload.session_id == "test-session-uuid"
        ok(f"create_refresh_token: type={refresh_payload.token_type}, session_id={refresh_payload.session_id[:12]}...")

        # 2-4. 변조 토큰 검증 실패
        tampered = access_token[:-5] + "XXXXX"
        try:
            verify_token(tampered)
            fail("tampered token should raise APIException")
        except APIException:
            ok("tampered token: APIException raised")

        # 2-5. 만료 토큰 검증 실패
        from datetime import timedelta
        expired_token = create_access_token(token_data, expires_delta=timedelta(seconds=-1))
        try:
            verify_token(expired_token)
            fail("expired token should raise APIException")
        except APIException:
            ok("expired token: APIException raised")

    except Exception as e:
        fail(f"jwt: {e}")

    # ===================================
    # 3. dependencies.py 테스트
    # ===================================
    print("\n[3] dependencies.py - FastAPI 인증 의존성")
    try:
        from app.core.security.dependencies import get_current_user, get_current_active_user, get_optional_user

        assert callable(get_current_user)
        assert callable(get_current_active_user)
        assert callable(get_optional_user)
        ok("3 functions imported (get_current_user, get_current_active_user, get_optional_user)")
    except Exception as e:
        fail(f"dependencies: {e}")

    # ===================================
    # 4. permission.py 테스트 (v2.0 - 메뉴 기반)
    # ===================================
    print("\n[4] permission.py - 메뉴 기반 권한 검사 (v2.0)")
    try:
        from app.core.security.permission import require_menu_permission, require_superuser

        # v1.0 함수 제거 확인
        import app.core.security.permission as perm_mod
        assert not hasattr(perm_mod, "require_permission"), "v1.0 require_permission이 아직 존재합니다"
        assert not hasattr(perm_mod, "require_any_permission"), "v1.0 require_any_permission이 아직 존재합니다"
        ok("v1.0 functions removed (require_permission, require_any_permission)")

        # require_menu_permission 팩토리 테스트
        checker = require_menu_permission("USER_MGMT", "read")
        assert callable(checker)
        ok(f"require_menu_permission('USER_MGMT', 'read') returns callable")

        checker2 = require_menu_permission("SETTINGS", "update")
        assert callable(checker2)
        ok(f"require_menu_permission('SETTINGS', 'update') returns callable")

        # 잘못된 action 검증
        try:
            require_menu_permission("USER_MGMT", "invalid_action")
            fail("invalid action should raise ValueError")
        except ValueError:
            ok("invalid action: ValueError raised")

        # require_superuser
        checker3 = require_superuser()
        assert callable(checker3)
        ok(f"require_superuser() returns callable")

    except Exception as e:
        fail(f"permission: {e}")

    # ===================================
    # 5. 통합: JWT → UserContext (v2.0)
    # ===================================
    print("\n[5] JWT → UserContext 통합 (v2.0)")
    try:
        from app.core.security.jwt import create_access_token, verify_token
        from app.models.auth import UserContext

        # 5-1. SYSTEM_ADMIN UserContext
        token = create_access_token({
            "sub": "1",
            "login_id": "admin",
            "display_name": "시스템 관리자",
            "tenant_id": None,
            "scope_type": "GLOBAL",
            "role_code": "SYSTEM_ADMIN",
            "is_superuser": True,
        })
        payload = verify_token(token)
        user_ctx = UserContext(
            user_id=int(payload.sub),
            login_id=payload.login_id,
            display_name=payload.display_name,
            tenant_id=payload.tenant_id,
            is_superuser=payload.is_superuser,
            scope_type=payload.scope_type,
            role_code=payload.role_code,
        )
        assert user_ctx.is_global is True
        assert user_ctx.is_superuser is True
        assert user_ctx.role_code == "SYSTEM_ADMIN"
        assert user_ctx.scope_type == "GLOBAL"
        ok(f"SYSTEM_ADMIN: is_global={user_ctx.is_global}, role_code={user_ctx.role_code}")

        # 5-2. TENANT_ADMIN UserContext
        tenant_token = create_access_token({
            "sub": "2",
            "login_id": "tenant_admin",
            "tenant_id": 1,
            "scope_type": "TENANT",
            "role_code": "TENANT_ADMIN",
            "is_superuser": False,
        })
        t_payload = verify_token(tenant_token)
        tenant_user = UserContext(
            user_id=int(t_payload.sub),
            login_id=t_payload.login_id,
            tenant_id=t_payload.tenant_id,
            is_superuser=t_payload.is_superuser,
            scope_type=t_payload.scope_type,
            role_code=t_payload.role_code,
        )
        assert tenant_user.is_global is False
        assert tenant_user.is_tenant_scope is True
        assert tenant_user.role_code == "TENANT_ADMIN"
        ok(f"TENANT_ADMIN: is_tenant_scope={tenant_user.is_tenant_scope}, tenant_id={tenant_user.tenant_id}")

        # 5-3. USER UserContext
        normal_token = create_access_token({
            "sub": "3",
            "login_id": "user01",
            "tenant_id": 1,
            "scope_type": "USER",
            "role_code": "USER",
            "is_superuser": False,
        })
        n_payload = verify_token(normal_token)
        normal_user = UserContext(
            user_id=int(n_payload.sub),
            login_id=n_payload.login_id,
            tenant_id=n_payload.tenant_id,
            is_superuser=n_payload.is_superuser,
            scope_type=n_payload.scope_type,
            role_code=n_payload.role_code,
        )
        assert normal_user.is_global is False
        assert normal_user.is_user_scope is True
        assert normal_user.role_code == "USER"
        ok(f"USER: is_user_scope={normal_user.is_user_scope}, role_code={normal_user.role_code}")

        # 5-4. v2.0에서 제거된 속성 확인
        assert not hasattr(user_ctx, "permissions"), "v1.0 permissions 속성이 아직 존재합니다"
        assert not hasattr(user_ctx, "roles"), "v1.0 roles 속성이 아직 존재합니다"
        assert not hasattr(user_ctx, "has_permission"), "v1.0 has_permission 메서드가 아직 존재합니다"
        ok("v1.0 attributes removed (permissions, roles, has_permission)")

    except Exception as e:
        fail(f"integration: {e}")

    # ===================================
    # 6. Pydantic 모델 검증 (auth.py)
    # ===================================
    print("\n[6] Pydantic 모델 검증")
    try:
        from app.models.auth import LoginRequest, PasswordChangeRequest, MenuPermission, UserInfo, TokenResponse

        # 6-1. LoginRequest
        req = LoginRequest(login_id="admin", password="admin123!")
        assert req.login_id == "admin"
        ok("LoginRequest: valid")

        # 6-2. PasswordChangeRequest 검증
        try:
            PasswordChangeRequest(current_password="old", new_password="short")
            fail("PasswordChangeRequest should reject short password")
        except Exception:
            ok("PasswordChangeRequest: rejects short password")

        try:
            PasswordChangeRequest(current_password="old", new_password="nouppercase1")
            fail("PasswordChangeRequest should reject no uppercase")
        except Exception:
            ok("PasswordChangeRequest: rejects no uppercase")

        valid_req = PasswordChangeRequest(current_password="old", new_password="ValidPass1!")
        assert valid_req.new_password == "ValidPass1!"
        ok("PasswordChangeRequest: valid password accepted")

        # 6-3. MenuPermission
        menu = MenuPermission(
            menu_code="DASHBOARD", menu_name="대시보드", menu_path="/admin/dashboard",
            menu_type="PAGE", icon="dashboard", parent_menu_code=None,
            can_read=True, can_create=False, can_update=False, can_delete=False, can_export=False,
        )
        assert menu.menu_code == "DASHBOARD"
        assert menu.can_read is True
        assert menu.can_create is False
        ok("MenuPermission: DASHBOARD with CRUD flags")

        # 6-4. UserInfo (v2.0: role_code, landing_page, menus)
        user_info = UserInfo(
            user_id=1, login_id="admin", display_name="시스템 관리자",
            tenant_id=None, role_code="SYSTEM_ADMIN",
            scope_type="GLOBAL", landing_page="/admin/dashboard", menus=[menu],
        )
        assert user_info.role_code == "SYSTEM_ADMIN"
        assert len(user_info.menus) == 1
        ok(f"UserInfo: role_code={user_info.role_code}, menus={len(user_info.menus)}")

    except Exception as e:
        fail(f"models: {e}")

    # ===================================
    # 7. DB 연동: authenticate + session flow
    # ===================================
    print("\n[7] DB 연동 테스트")
    db_available = False
    try:
        from app.core.database.connection import db_manager
        from app.api.services.auth_service import auth_service
        from app.core.errors import APIException

        db_manager.initialize()
        db_available = True
        ok("db_manager initialized")

        # admin 계정 존재 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, login_id, is_superuser, role_id FROM tb_user WHERE login_id = 'admin'")
            admin_row = cur.fetchone()

        if not admin_row:
            print("  [SKIP] admin 계정이 DB에 없습니다. DB 연동 테스트를 건너뜁니다.")
        else:
            admin = dict(admin_row)
            ok(f"admin 계정 확인: user_id={admin['user_id']}, is_superuser={admin['is_superuser']}")

            # 7-1. authenticate - 올바른 비밀번호
            try:
                user = auth_service.authenticate("admin", "admin123!", "test-sec")
                assert user["user_id"] == admin["user_id"]
                assert user["login_id"] == "admin"
                ok(f"authenticate (correct): user_id={user['user_id']}")
            except APIException as e:
                fail(f"authenticate (correct): {e.message}")

            # 7-2. authenticate - 틀린 비밀번호
            try:
                auth_service.authenticate("admin", "wrong_password!", "test-sec")
                fail("authenticate (wrong): should raise APIException")
            except APIException:
                ok("authenticate (wrong): APIException raised")

            # 7-3. authenticate - 존재하지 않는 ID
            try:
                auth_service.authenticate("nonexistent_user_xyz", "any", "test-sec")
                fail("authenticate (nonexistent): should raise APIException")
            except APIException:
                ok("authenticate (nonexistent): APIException raised")

            # 7-4. get_user_with_permissions (v2.0: menus)
            try:
                user_info = auth_service.get_user_with_permissions(admin["user_id"], "test-sec")
                assert user_info["login_id"] == "admin"
                assert "role_code" in user_info
                assert "scope_type" in user_info
                assert "landing_page" in user_info
                assert isinstance(user_info["menus"], list)
                ok(f"get_user_with_permissions: role_code={user_info['role_code']}, menus={len(user_info['menus'])}, scope={user_info['scope_type']}")
            except Exception as e:
                fail(f"get_user_with_permissions: {e}")

            # 7-5. session flow: create → refresh → logout
            try:
                from app.models.auth import TokenResponse

                token_resp = auth_service.create_session(admin["user_id"], "127.0.0.1", "test-agent", "test-sec")
                assert isinstance(token_resp, TokenResponse)
                assert token_resp.access_token
                assert token_resp.refresh_token
                assert token_resp.token_type == "Bearer"
                assert token_resp.user.login_id == "admin"
                assert token_resp.user.role_code  # v2.0: role_code 존재 확인
                assert isinstance(token_resp.user.menus, list)
                ok(f"create_session: token={token_resp.access_token[:30]}..., menus={len(token_resp.user.menus)}")

                time.sleep(1)
                new_resp = auth_service.refresh_access_token(token_resp.refresh_token, "test-sec")
                assert isinstance(new_resp, TokenResponse)
                assert new_resp.access_token != token_resp.access_token
                assert new_resp.refresh_token == token_resp.refresh_token
                ok(f"refresh_access_token: new token={new_resp.access_token[:30]}...")

                deleted = auth_service.logout(admin["user_id"], "test-sec")
                assert deleted is True
                ok("logout: session deleted")

                try:
                    auth_service.refresh_access_token(token_resp.refresh_token, "test-sec")
                    fail("refresh after logout: should raise APIException")
                except APIException:
                    ok("refresh after logout: APIException raised")

            except Exception as e:
                fail(f"session flow: {e}")

            # 7-6. change_password (admin123! → TestPass1! → admin123!)
            try:
                auth_service.change_password(admin["user_id"], "admin123!", "TestPass1!", "test-sec")
                ok("change_password: admin123! → TestPass1!")

                user = auth_service.authenticate("admin", "TestPass1!", "test-sec")
                assert user["user_id"] == admin["user_id"]
                ok("authenticate with new password: success")

                auth_service.change_password(admin["user_id"], "TestPass1!", "admin123!", "test-sec")
                ok("change_password: TestPass1! → admin123! (원복)")

                try:
                    auth_service.change_password(admin["user_id"], "wrong_current", "NewPass1!", "test-sec")
                    fail("change_password (wrong current): should raise APIException")
                except APIException:
                    ok("change_password (wrong current): APIException raised")

            except APIException as e:
                fail(f"change_password: {e.message}")

            # 7-7. 메뉴 권한 데이터 확인 (tb_user_menu)
            try:
                with db_manager.get_cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) AS cnt FROM tb_user_menu WHERE user_id = %s",
                        (admin["user_id"],),
                    )
                    menu_count = cur.fetchone()["cnt"]

                assert menu_count > 0, f"admin에게 할당된 메뉴 권한이 없습니다 (count={menu_count})"
                ok(f"tb_user_menu: admin has {menu_count} menu permissions")

                # 특정 메뉴 권한 상세 확인
                with db_manager.get_cursor() as cur:
                    cur.execute(
                        "SELECT m.menu_code, um.can_create, um.can_read, um.can_update, um.can_delete "
                        "FROM tb_user_menu um "
                        "JOIN tb_menu m ON m.menu_id = um.menu_id "
                        "WHERE um.user_id = %s AND m.menu_code = 'DASHBOARD'",
                        (admin["user_id"],),
                    )
                    dash = cur.fetchone()

                if dash:
                    assert dash["can_read"] is True
                    ok(f"DASHBOARD permission: can_read={dash['can_read']}, can_create={dash['can_create']}")
                else:
                    print("  [SKIP] DASHBOARD 메뉴 권한이 없습니다")

            except Exception as e:
                fail(f"menu permission check: {e}")

            # login_fail_count 초기화 (테스트 중 증가된 것 원복)
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("UPDATE tb_user SET login_fail_count = 0, locked_until = NULL WHERE login_id = 'admin'")

        if db_available:
            db_manager.close()

    except Exception as e:
        fail(f"DB integration: {e}")

    # ===================================
    # 8. 라우터 등록 확인
    # ===================================
    print("\n[8] 라우터 엔드포인트 확인")
    try:
        from app.api.routes.auth import router as auth_router
        assert auth_router.prefix == "/api/v1/auth"
        route_paths = [r.path for r in auth_router.routes]
        prefix = auth_router.prefix
        for ep in ["/login", "/logout", "/refresh", "/me", "/me/password"]:
            full = f"{prefix}{ep}"
            assert ep in route_paths or full in route_paths, f"{ep} not in {route_paths}"
        ok(f"auth router: 5 endpoints registered")
    except Exception as e:
        fail(f"auth router: {e}")

    try:
        from app.api.routes.users import router as users_router
        assert users_router.prefix == "/api/admin/v1/users"
        ok(f"users router: prefix={users_router.prefix}")
    except Exception as e:
        fail(f"users router: {e}")

    try:
        from app.api.routes.roles import router as roles_router
        assert roles_router.prefix == "/api/admin/v1/roles"
        route_paths = [r.path for r in roles_router.routes]
        prefix = roles_router.prefix
        has_default_menus = any("default-menus" in p for p in route_paths)
        assert has_default_menus, f"default-menus endpoint not found in {route_paths}"
        ok(f"roles router: prefix={prefix}, has default-menus endpoint")
    except Exception as e:
        fail(f"roles router: {e}")

    try:
        from app.api.routes.menus import router as menus_router
        assert menus_router.prefix == "/api/admin/v1/menus"
        ok(f"menus router: prefix={menus_router.prefix}")
    except Exception as e:
        fail(f"menus router: {e}")

    try:
        from app.middleware.auth import AuthMiddleware
        assert "/api/v1/auth/login" in AuthMiddleware.EXCLUDE_PATHS
        assert "/api/v1/auth/refresh" in AuthMiddleware.EXCLUDE_PATHS
        ok(f"AuthMiddleware: EXCLUDE_PATHS has {len(AuthMiddleware.EXCLUDE_PATHS)} paths")
    except Exception as e:
        fail(f"AuthMiddleware: {e}")

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
        print("\nALL TESTS PASSED - Security v2.0 (Menu-based) OK")
        sys.exit(0)


if __name__ == "__main__":
    test_all()
