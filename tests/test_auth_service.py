"""인증 서비스 테스트 (v2.0 - 메뉴 기반)

위치: tests/test_auth_service.py
테스트 대상:
  - auth_service.authenticate (로그인 검증)
  - auth_service.get_user_with_permissions (권한 조회 - v2.0: menus)
  - auth_service.create_session / refresh / logout (세션 흐름)
  - auth_service.change_password (비밀번호 변경)
  - auth route / middleware import 확인
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
    # 1. Import 확인
    # ===================================
    print("\n[1] Import 확인")

    try:
        from app.core.errors import ErrorCode
        assert hasattr(ErrorCode, "ACCOUNT_LOCKED"), "ACCOUNT_LOCKED 에러코드 없음"
        assert hasattr(ErrorCode, "SESSION_EXPIRED"), "SESSION_EXPIRED 에러코드 없음"
        ok("ErrorCode: ACCOUNT_LOCKED, SESSION_EXPIRED exists")
    except Exception as e:
        fail(f"error_codes: {e}")

    try:
        from app.api.services.auth_service import auth_service, AuthService
        assert isinstance(auth_service, AuthService)
        ok("auth_service singleton imported")
    except Exception as e:
        fail(f"auth_service import: {e}")

    try:
        from app.api.routes.auth import router
        assert router.prefix == "/api/v1/auth"
        route_paths = [r.path for r in router.routes]
        expected = ["/login", "/logout", "/refresh", "/me", "/me/password"]
        for ep in expected:
            full_path = f"/api/v1/auth{ep}"
            assert ep in route_paths or full_path in route_paths, f"{ep} not in {route_paths}"
        ok(f"auth routes: 5 endpoints verified")
    except Exception as e:
        fail(f"auth routes: {e}")

    try:
        from app.middleware.auth import AuthMiddleware
        assert hasattr(AuthMiddleware, "EXCLUDE_PATHS")
        assert "/api/v1/auth/login" in AuthMiddleware.EXCLUDE_PATHS
        assert "/api/v1/auth/refresh" in AuthMiddleware.EXCLUDE_PATHS
        ok(f"AuthMiddleware: EXCLUDE_PATHS has {len(AuthMiddleware.EXCLUDE_PATHS)} paths")
    except Exception as e:
        fail(f"AuthMiddleware: {e}")

    try:
        from app.middleware import AuthMiddleware as AM
        assert AM is not None
        ok("middleware __init__: AuthMiddleware exported")
    except Exception as e:
        fail(f"middleware __init__: {e}")

    # ===================================
    # 2. DB 연동 + authenticate 테스트
    # ===================================
    print("\n[2] DB 연동: authenticate")
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
            print("  [SKIP] DB에 admin 계정이 없습니다. DB 연동 테스트를 건너뜁니다.")
            print("  → docs/sql/tb_user_permission.sql의 INSERT 문을 먼저 실행해주세요.")
        else:
            admin = dict(admin_row)
            ok(f"admin 계정 확인: user_id={admin['user_id']}, is_superuser={admin['is_superuser']}")

            # 2-1. authenticate - 올바른 비밀번호
            try:
                user = auth_service.authenticate("admin", "admin123!", "test-auth")
                assert user["user_id"] == admin["user_id"]
                assert user["login_id"] == "admin"
                ok(f"authenticate (correct): user_id={user['user_id']}")
            except APIException as e:
                fail(f"authenticate (correct): {e.message}")

            # 2-2. authenticate - 틀린 비밀번호
            try:
                auth_service.authenticate("admin", "wrong_password!", "test-auth")
                fail("authenticate (wrong): should raise APIException")
            except APIException:
                ok("authenticate (wrong): APIException raised")

            # 2-3. authenticate - 존재하지 않는 ID
            try:
                auth_service.authenticate("nonexistent_user_xyz", "any_password", "test-auth")
                fail("authenticate (nonexistent): should raise APIException")
            except APIException:
                ok("authenticate (nonexistent): APIException raised")

            # ===================================
            # 3. get_user_with_permissions (v2.0: menus)
            # ===================================
            print("\n[3] DB 연동: get_user_with_permissions (v2.0)")
            try:
                user_info = auth_service.get_user_with_permissions(admin["user_id"], "test-auth")
                assert user_info["login_id"] == "admin"
                assert "role_code" in user_info, "role_code 필드 없음"
                assert "scope_type" in user_info, "scope_type 필드 없음"
                assert "landing_page" in user_info, "landing_page 필드 없음"
                assert isinstance(user_info["menus"], list), "menus가 list가 아님"
                assert len(user_info["menus"]) > 0, "admin에게 메뉴 권한이 없음"
                ok(f"get_user_with_permissions: role_code={user_info['role_code']}, menus={len(user_info['menus'])}, scope={user_info['scope_type']}")
            except Exception as e:
                fail(f"get_user_with_permissions: {e}")

            # ===================================
            # 4. create_session + refresh + logout
            # ===================================
            print("\n[4] DB 연동: session flow")
            try:
                from app.models.auth import TokenResponse

                # 4-1. 세션 생성
                token_resp = auth_service.create_session(admin["user_id"], "127.0.0.1", "test-agent", "test-auth")
                assert isinstance(token_resp, TokenResponse)
                assert token_resp.access_token
                assert token_resp.refresh_token
                assert token_resp.token_type == "Bearer"
                assert token_resp.expires_in == 1800
                assert token_resp.user.login_id == "admin"
                assert token_resp.user.role_code  # v2.0: role_code 존재
                assert isinstance(token_resp.user.menus, list)
                ok(f"create_session: token={token_resp.access_token[:30]}..., menus={len(token_resp.user.menus)}")

                # 4-2. Refresh Token으로 Access Token 갱신
                time.sleep(1)
                new_resp = auth_service.refresh_access_token(token_resp.refresh_token, "test-auth")
                assert isinstance(new_resp, TokenResponse)
                assert new_resp.access_token
                assert new_resp.refresh_token == token_resp.refresh_token
                ok(f"refresh_access_token: new token={new_resp.access_token[:30]}...")

                # 4-3. 로그아웃 (세션 삭제)
                deleted = auth_service.logout(admin["user_id"], "test-auth")
                assert deleted is True
                ok("logout: session deleted")

                # 4-4. 삭제 후 Refresh 시도 → 실패
                try:
                    auth_service.refresh_access_token(token_resp.refresh_token, "test-auth")
                    fail("refresh after logout: should raise APIException")
                except APIException:
                    ok("refresh after logout: APIException raised")

            except Exception as e:
                fail(f"session flow: {e}")

            # ===================================
            # 5. change_password
            # ===================================
            print("\n[5] DB 연동: change_password")
            try:
                # admin123! → TestPass1! → admin123!
                auth_service.change_password(admin["user_id"], "admin123!", "TestPass1!", "test-auth")
                ok("change_password: admin123! → TestPass1!")

                user = auth_service.authenticate("admin", "TestPass1!", "test-auth")
                assert user["user_id"] == admin["user_id"]
                ok("authenticate with new password: success")

                auth_service.change_password(admin["user_id"], "TestPass1!", "admin123!", "test-auth")
                ok("change_password: TestPass1! → admin123! (원복)")

                try:
                    auth_service.change_password(admin["user_id"], "wrong_current", "NewPass1!", "test-auth")
                    fail("change_password (wrong current): should raise APIException")
                except APIException:
                    ok("change_password (wrong current): APIException raised")

            except APIException as e:
                fail(f"change_password: {e.message}")

            # login_fail_count 초기화 (테스트 중 증가된 것 원복)
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("UPDATE tb_user SET login_fail_count = 0, locked_until = NULL WHERE login_id = 'admin'")

        if db_available:
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
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED - Auth Service v2.0 OK")
        sys.exit(0)


if __name__ == "__main__":
    test_all()
