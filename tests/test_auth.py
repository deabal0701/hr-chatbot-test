"""Phase 3 인증 API + 미들웨어 검증 테스트"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_all():
    errors = []

    # ===================================
    # 0. Import 확인
    # ===================================
    try:
        from app.core.errors import ErrorCode
        assert hasattr(ErrorCode, "ACCOUNT_LOCKED"), "ACCOUNT_LOCKED 에러코드 없음"
        print("[OK] error_codes - ACCOUNT_LOCKED exists")
    except Exception as e:
        errors.append(f"[FAIL] error_codes: {e}")

    try:
        from app.api.services.auth_service import auth_service, AuthService
        assert isinstance(auth_service, AuthService)
        print("[OK] auth_service - singleton imported")
    except Exception as e:
        errors.append(f"[FAIL] auth_service import: {e}")

    try:
        from app.api.routes.auth import router
        assert router.prefix == "/api/v1/auth"
        route_paths = [r.path for r in router.routes]
        # APIRouter 경로는 prefix 포함 형태일 수 있음
        expected = ["/login", "/logout", "/refresh", "/me", "/me/password"]
        for ep in expected:
            full_path = f"/api/v1/auth{ep}"
            assert ep in route_paths or full_path in route_paths, f"{ep} not in {route_paths}"
        print(f"[OK] auth routes - 5 endpoints: {route_paths}")
    except Exception as e:
        errors.append(f"[FAIL] auth routes: {e}")

    try:
        from app.middleware.auth import AuthMiddleware
        assert hasattr(AuthMiddleware, "EXCLUDE_PATHS")
        assert "/api/v1/auth/login" in AuthMiddleware.EXCLUDE_PATHS
        assert "/api/v1/auth/refresh" in AuthMiddleware.EXCLUDE_PATHS
        print(f"[OK] AuthMiddleware - EXCLUDE_PATHS: {len(AuthMiddleware.EXCLUDE_PATHS)} paths")
    except Exception as e:
        errors.append(f"[FAIL] AuthMiddleware: {e}")

    try:
        from app.middleware import AuthMiddleware as AM
        assert AM is not None
        print("[OK] middleware __init__ - AuthMiddleware exported")
    except Exception as e:
        errors.append(f"[FAIL] middleware __init__: {e}")

    # ===================================
    # 1. DB 연결 + authenticate 테스트
    # ===================================
    try:
        from app.core.database.connection import db_manager
        from app.api.services.auth_service import auth_service
        from app.core.errors import APIException

        db_manager.initialize()
        print("[OK] db_manager initialized")

        # 1-1. admin 계정 존재 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, login_id, password_hash, is_superuser FROM tb_user WHERE login_id = 'admin'")
            admin_row = cur.fetchone()

        if not admin_row:
            print("[SKIP] DB에 admin 계정이 없습니다. DB 연동 테스트를 건너뜁니다.")
            print("  → docs/sql/tb_user_permission.sql의 INSERT 문을 먼저 실행해주세요.")
        else:
            admin = dict(admin_row)
            print(f"[OK] admin 계정 확인: user_id={admin['user_id']}, is_superuser={admin['is_superuser']}")

            # 1-2. authenticate - 올바른 비밀번호
            try:
                user = auth_service.authenticate("admin", "admin123!", "test-req")
                assert user["user_id"] == admin["user_id"]
                assert user["login_id"] == "admin"
                print(f"[OK] authenticate - correct password: user_id={user['user_id']}")
            except APIException as e:
                # 비밀번호 해시가 다를 수 있음
                print(f"[WARN] authenticate - admin123! 비밀번호로 로그인 실패: {e.message}")
                print("  → tb_user.password_hash가 'admin123!'의 bcrypt 해시인지 확인해주세요.")
                errors.append(f"[FAIL] authenticate - correct password: {e.message}")

            # 1-3. authenticate - 틀린 비밀번호
            try:
                auth_service.authenticate("admin", "wrong_password!", "test-req")
                errors.append("[FAIL] authenticate - wrong password should raise")
            except APIException as e:
                assert "올바르지 않습니다" in e.message or "UNAUTHORIZED" in str(e.error_code)
                print("[OK] authenticate - wrong password: APIException raised")

            # 1-4. authenticate - 존재하지 않는 ID
            try:
                auth_service.authenticate("nonexistent_user_xyz", "any_password", "test-req")
                errors.append("[FAIL] authenticate - nonexistent user should raise")
            except APIException as e:
                print("[OK] authenticate - nonexistent user: APIException raised")

            # ===================================
            # 2. get_user_with_permissions 테스트
            # ===================================
            try:
                user_info = auth_service.get_user_with_permissions(admin["user_id"], "test-req")
                assert user_info["login_id"] == "admin"
                assert isinstance(user_info["roles"], list)
                assert isinstance(user_info["permissions"], list)
                assert "scope_type" in user_info
                print(f"[OK] get_user_with_permissions: roles={user_info['roles']}, perms={len(user_info['permissions'])}, scope={user_info['scope_type']}")
            except Exception as e:
                errors.append(f"[FAIL] get_user_with_permissions: {e}")

            # ===================================
            # 3. create_session + refresh + logout 테스트
            # ===================================
            try:
                from app.models.auth import TokenResponse

                # 3-1. 세션 생성
                token_resp = auth_service.create_session(admin["user_id"], "127.0.0.1", "test-agent", "test-req")
                assert isinstance(token_resp, TokenResponse)
                assert token_resp.access_token
                assert token_resp.refresh_token
                assert token_resp.token_type == "Bearer"
                assert token_resp.expires_in == 1800  # 30분 * 60초
                assert token_resp.user.login_id == "admin"
                print(f"[OK] create_session: access_token={token_resp.access_token[:30]}...")

                # 3-2. Refresh Token으로 Access Token 갱신
                import time
                time.sleep(1)  # JWT iat가 달라지도록 1초 대기
                new_resp = auth_service.refresh_access_token(token_resp.refresh_token, "test-req")
                assert isinstance(new_resp, TokenResponse)
                assert new_resp.access_token  # 유효한 Access Token
                assert new_resp.refresh_token == token_resp.refresh_token  # Refresh Token은 유지
                print(f"[OK] refresh_access_token: new access_token={new_resp.access_token[:30]}...")

                # 3-3. 로그아웃 (세션 삭제)
                deleted = auth_service.logout(admin["user_id"], "test-req")
                assert deleted is True
                print("[OK] logout: session deleted")

                # 3-4. 삭제 후 Refresh 시도 → 실패
                try:
                    auth_service.refresh_access_token(token_resp.refresh_token, "test-req")
                    errors.append("[FAIL] refresh after logout should raise")
                except APIException as e:
                    print(f"[OK] refresh after logout: APIException raised ({e.message})")

            except Exception as e:
                errors.append(f"[FAIL] session flow: {e}")

            # ===================================
            # 4. change_password 테스트
            # ===================================
            try:
                # 현재 비밀번호로 변경 시도 (같은 비밀번호로 되돌림)
                # admin123! → TestPass1! → admin123!
                auth_service.change_password(admin["user_id"], "admin123!", "TestPass1!", "test-req")
                print("[OK] change_password: admin123! → TestPass1!")

                # 변경된 비밀번호로 로그인 확인
                user = auth_service.authenticate("admin", "TestPass1!", "test-req")
                assert user["user_id"] == admin["user_id"]
                print("[OK] authenticate with new password: success")

                # 원래 비밀번호로 되돌림 (admin123!는 대문자 없어서 validator 통과 안되지만 서비스 직접 호출은 가능)
                auth_service.change_password(admin["user_id"], "TestPass1!", "admin123!", "test-req")
                print("[OK] change_password: TestPass1! → admin123! (원복)")

                # 틀린 현재 비밀번호로 변경 시도 → 실패
                try:
                    auth_service.change_password(admin["user_id"], "wrong_current", "NewPass1!", "test-req")
                    errors.append("[FAIL] change_password with wrong current should raise")
                except APIException:
                    print("[OK] change_password - wrong current password: APIException raised")

            except APIException as e:
                print(f"[WARN] change_password 테스트 실패: {e.message}")
                errors.append(f"[FAIL] change_password: {e.message}")

        db_manager.close()

    except Exception as e:
        errors.append(f"[FAIL] DB integration: {e}")

    # ===================================
    # Summary
    # ===================================
    print(f"\n{'='*50}")
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED - Phase 3 Auth OK")
        sys.exit(0)


if __name__ == "__main__":
    test_all()
