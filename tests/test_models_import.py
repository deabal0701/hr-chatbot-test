"""Phase 1 모델 import 검증 테스트"""
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    errors = []

    # 1. auth.py import
    try:
        from app.models.auth import (
            LoginRequest, UserInfo, TokenResponse,
            RefreshRequest, PasswordChangeRequest, UserContext
        )
        print("[OK] auth.py - 6 classes imported")
    except Exception as e:
        errors.append(f"[FAIL] auth.py: {e}")

    # 2. user.py import
    try:
        from app.models.user import (
            UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
            RoleBase, RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
            RoleSimple, PermissionSimple, PermissionResponse,
            UserRoleAssign, RolePermissionAssign, DataFilterResponse
        )
        print("[OK] user.py - 16 classes imported")
    except Exception as e:
        errors.append(f"[FAIL] user.py: {e}")

    # 3. tenant.py import
    try:
        from app.models.tenant import (
            TenantBase, TenantCreate, TenantUpdate,
            TenantResponse, TenantListResponse
        )
        print("[OK] tenant.py - 5 classes imported")
    except Exception as e:
        errors.append(f"[FAIL] tenant.py: {e}")

    # 4. config.py import
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
        print(f"[OK] config.py - 4 new fields verified (refresh={s.jwt_refresh_token_expire_days}d, pwd_min={s.password_min_length}, max_fail={s.login_max_fail_count}, lock={s.login_lock_minutes}m)")
    except Exception as e:
        errors.append(f"[FAIL] config.py: {e}")

    # 5. Validation tests
    try:
        from app.models.auth import LoginRequest
        req = LoginRequest(login_id="testuser", password="Pass1234!")
        assert req.login_id == "testuser"
        print("[OK] LoginRequest validation passed")
    except Exception as e:
        errors.append(f"[FAIL] LoginRequest validation: {e}")

    try:
        from app.models.tenant import TenantCreate
        t = TenantCreate(tenant_code="company_a", tenant_name="A사")
        assert t.tenant_code == "COMPANY_A"  # auto uppercase
        print("[OK] TenantCreate tenant_code auto-uppercase passed")
    except Exception as e:
        errors.append(f"[FAIL] TenantCreate validation: {e}")

    try:
        from app.models.user import UserCreate
        u = UserCreate(
            login_id="user01", email="user01@test.com",
            password="Password1!", tenant_id=1
        )
        assert u.email == "user01@test.com"
        print("[OK] UserCreate email validation passed")
    except Exception as e:
        errors.append(f"[FAIL] UserCreate validation: {e}")

    try:
        from app.models.user import RoleCreate
        r = RoleCreate(
            role_code="TEST_ROLE", role_name="테스트",
            scope_type="tenant"
        )
        assert r.scope_type == "TENANT"  # auto uppercase
        print("[OK] RoleCreate scope_type auto-uppercase passed")
    except Exception as e:
        errors.append(f"[FAIL] RoleCreate validation: {e}")

    # Summary
    print(f"\n{'='*50}")
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED - Phase 1 Models OK")
        sys.exit(0)

if __name__ == "__main__":
    test_imports()
