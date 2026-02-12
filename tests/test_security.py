"""Phase 2 Core Security 모듈 검증 테스트"""
import sys
import os
import time

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all():
    errors = []

    # ===================================
    # 1. password.py 테스트
    # ===================================
    try:
        from app.core.security.password import hash_password, verify_password

        # 1-1. 해싱 결과 형식 확인
        hashed = hash_password("admin123!")
        assert hashed.startswith("$2b$"), f"bcrypt 형식이 아님: {hashed[:10]}"
        print(f"[OK] password - hash_password: {hashed[:30]}...")

        # 1-2. 올바른 비밀번호 검증
        assert verify_password("admin123!", hashed) is True
        print("[OK] password - verify_password (correct): True")

        # 1-3. 틀린 비밀번호 검증
        assert verify_password("wrong_password", hashed) is False
        print("[OK] password - verify_password (wrong): False")

        # 1-4. salt 동작 확인 (같은 입력, 다른 해시)
        hashed2 = hash_password("admin123!")
        assert hashed != hashed2, "같은 입력인데 같은 해시 (salt 미동작)"
        print("[OK] password - salt: different hashes for same input")

    except Exception as e:
        errors.append(f"[FAIL] password: {e}")

    # ===================================
    # 2. jwt.py 테스트
    # ===================================
    try:
        from app.core.security.jwt import (
            create_access_token, create_refresh_token, verify_token, TokenPayload
        )
        from app.core.errors import APIException

        # 2-1. Access Token 생성 및 검증
        token_data = {
            "sub": "1",
            "login_id": "admin",
            "display_name": "시스템 관리자",
            "tenant_id": None,
            "scope_type": "GLOBAL",
            "roles": ["SYSTEM_ADMIN"],
            "permissions": ["admin:settings", "nl2sql:execute"],
            "is_superuser": True,
        }
        access_token = create_access_token(token_data)
        assert isinstance(access_token, str) and len(access_token) > 50
        print(f"[OK] jwt - create_access_token: {access_token[:50]}...")

        # 2-2. Access Token 검증
        payload = verify_token(access_token)
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "1"
        assert payload.login_id == "admin"
        assert payload.scope_type == "GLOBAL"
        assert payload.token_type == "access"
        assert payload.is_superuser is True
        assert "admin:settings" in payload.permissions
        assert "SYSTEM_ADMIN" in payload.roles
        print(f"[OK] jwt - verify_token: sub={payload.sub}, type={payload.token_type}")

        # 2-3. Refresh Token 생성 및 검증
        refresh_data = {"sub": "1", "session_id": "test-session-uuid"}
        refresh_token = create_refresh_token(refresh_data)
        refresh_payload = verify_token(refresh_token)
        assert refresh_payload.token_type == "refresh"
        assert refresh_payload.session_id == "test-session-uuid"
        print(f"[OK] jwt - create_refresh_token: type={refresh_payload.token_type}")

        # 2-4. 변조 토큰 검증 실패
        tampered = access_token[:-5] + "XXXXX"
        try:
            verify_token(tampered)
            errors.append("[FAIL] jwt - tampered token should raise")
        except APIException:
            print("[OK] jwt - tampered token: APIException raised")

        # 2-5. 만료 토큰 검증 실패
        from datetime import timedelta
        expired_token = create_access_token(token_data, expires_delta=timedelta(seconds=-1))
        try:
            verify_token(expired_token)
            errors.append("[FAIL] jwt - expired token should raise")
        except APIException:
            print("[OK] jwt - expired token: APIException raised")

    except Exception as e:
        errors.append(f"[FAIL] jwt: {e}")

    # ===================================
    # 3. dependencies.py 테스트
    # ===================================
    try:
        from app.core.security.dependencies import (
            get_current_user, get_current_active_user, get_optional_user
        )
        assert callable(get_current_user)
        assert callable(get_current_active_user)
        assert callable(get_optional_user)
        print("[OK] dependencies - 3 functions imported")
    except Exception as e:
        errors.append(f"[FAIL] dependencies: {e}")

    # ===================================
    # 4. permission.py 테스트
    # ===================================
    try:
        from app.core.security.permission import (
            require_permission, require_any_permission, require_superuser
        )

        # 4-1. 팩토리 반환 타입 확인
        checker = require_permission("admin:users")
        assert callable(checker), "require_permission은 callable을 반환해야 함"
        print(f"[OK] permission - require_permission returns: {type(checker).__name__}")

        checker2 = require_any_permission("admin:users", "admin:settings")
        assert callable(checker2)
        print(f"[OK] permission - require_any_permission returns: {type(checker2).__name__}")

        checker3 = require_superuser()
        assert callable(checker3)
        print(f"[OK] permission - require_superuser returns: {type(checker3).__name__}")
    except Exception as e:
        errors.append(f"[FAIL] permission: {e}")

    # ===================================
    # 5. 통합 테스트: JWT → UserContext
    # ===================================
    try:
        from app.core.security.jwt import create_access_token, verify_token
        from app.models.auth import UserContext

        token = create_access_token({
            "sub": "1",
            "login_id": "admin",
            "tenant_id": None,
            "scope_type": "GLOBAL",
            "roles": ["SYSTEM_ADMIN"],
            "permissions": ["admin:settings", "nl2sql:execute", "rag:search"],
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
            roles=payload.roles,
            permissions=payload.permissions,
        )

        assert user_ctx.has_permission("admin:settings") is True
        assert user_ctx.has_permission("nonexistent") is True  # superuser bypass
        assert user_ctx.is_global is True
        assert user_ctx.has_all_permissions("admin:settings", "nl2sql:execute") is True
        assert user_ctx.has_any_permission("admin:settings", "nonexistent") is True
        print("[OK] integration - JWT → UserContext: all permission checks passed")

        # 일반 사용자 테스트 (superuser=False)
        normal_token = create_access_token({
            "sub": "2",
            "login_id": "user01",
            "tenant_id": 2,
            "scope_type": "USER",
            "roles": ["USER"],
            "permissions": ["nl2sql:execute", "rag:search", "document:read"],
            "is_superuser": False,
        })
        normal_payload = verify_token(normal_token)
        normal_user = UserContext(
            user_id=int(normal_payload.sub),
            login_id=normal_payload.login_id,
            tenant_id=normal_payload.tenant_id,
            is_superuser=normal_payload.is_superuser,
            scope_type=normal_payload.scope_type,
            roles=normal_payload.roles,
            permissions=normal_payload.permissions,
        )
        assert normal_user.has_permission("admin:settings") is False
        assert normal_user.has_permission("nl2sql:execute") is True
        assert normal_user.is_global is False
        assert normal_user.is_user_scope is True
        print("[OK] integration - normal user: permission restrictions work")

    except Exception as e:
        errors.append(f"[FAIL] integration: {e}")

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
        print("ALL TESTS PASSED - Phase 2 Core Security OK")
        sys.exit(0)


if __name__ == "__main__":
    test_all()
