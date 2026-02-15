"""사용자 관리 API 테스트

위치: tests/test_06_users.py
사용자 CRUD + 옵션 조회 + 메뉴 권한 할당 + 역할-테넌트 검증
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/admin/v1/users"


class TestUserOptions:
    """드롭다운 옵션 API"""

    def test_role_options(self, client, admin_headers):
        """역할 옵션 조회"""
        data = assert_success(client.get(f"{PREFIX}/options/roles", headers=admin_headers))
        assert "items" in data
        assert len(data["items"]) >= 1
        assert "role_code" in data["items"][0]

    def test_tenant_options(self, client, admin_headers):
        """테넌트 옵션 조회 (is_system 포함)"""
        data = assert_success(client.get(f"{PREFIX}/options/tenants", headers=admin_headers))
        assert "items" in data
        # is_system 필드 존재 확인
        if data["items"]:
            assert "is_system" in data["items"][0]

    def test_menu_options(self, client, admin_headers):
        """메뉴 옵션 조회"""
        data = assert_success(client.get(f"{PREFIX}/options/menus", headers=admin_headers))
        assert "items" in data


class TestUserCRUD:
    created_id = None
    _role_id = None
    _tenant_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _setup_and_cleanup(self, client, admin_headers):
        """setup: role_id, tenant_id 조회 / teardown: 생성된 사용자 삭제"""
        roles = assert_success(client.get(f"{PREFIX}/options/roles", headers=admin_headers))
        user_role = next((r for r in roles["items"] if r["role_code"] == "USER"), None)
        TestUserCRUD._role_id = user_role["role_id"] if user_role else roles["items"][-1]["role_id"]

        tenants = assert_success(client.get(f"{PREFIX}/options/tenants", headers=admin_headers))
        non_sys = [t for t in tenants["items"] if not t.get("is_system")]
        TestUserCRUD._tenant_id = non_sys[0]["tenant_id"] if non_sys else tenants["items"][0]["tenant_id"]

        yield

        if TestUserCRUD.created_id:
            client.delete(f"{PREFIX}/{TestUserCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """사용자 생성"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "login_id": "pytest_user",
            "email": "pytest@test.com",
            "display_name": "PyTest 사용자",
            "password": "Test1234!",
            "role_id": self._role_id,
            "tenant_id": self._tenant_id,
            "is_active": True,
            "menus": [],
        }), status_code=201)
        assert data["login_id"] == "pytest_user"
        TestUserCRUD.created_id = data["user_id"]

    def test_list(self, client, admin_headers):
        """사용자 목록 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers, params={"limit": 10}))
        assert "items" in data
        assert "total" in data

    def test_list_with_keyword(self, client, admin_headers):
        """키워드 검색"""
        data = assert_success(client.get(PREFIX, headers=admin_headers, params={"keyword": "pytest"}))
        assert any(u["login_id"] == "pytest_user" for u in data["items"])

    def test_get(self, client, admin_headers):
        """사용자 상세 조회"""
        data = assert_success(client.get(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["user_id"] == self.created_id
        assert data["email"] == "pytest@test.com"

    def test_update(self, client, admin_headers):
        """사용자 수정"""
        data = assert_success(client.put(f"{PREFIX}/{self.created_id}", headers=admin_headers, json={
            "display_name": "PyTest 수정됨",
        }))
        assert data["display_name"] == "PyTest 수정됨"

    def test_duplicate_email(self, client, admin_headers):
        """중복 이메일 에러"""
        resp = client.post(PREFIX, headers=admin_headers, json={
            "login_id": "pytest_dup",
            "email": "pytest@test.com",
            "password": "Test1234!",
            "role_id": self._role_id,
            "tenant_id": self._tenant_id,
        })
        assert resp.status_code in (400, 409)

    def test_delete(self, client, admin_headers):
        """사용자 삭제"""
        assert_success(client.delete(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        TestUserCRUD.created_id = None  # teardown에서 이중 삭제 방지


class TestUserMenuAssignment:
    """사용자 메뉴 권한 할당/조회"""
    _user_id = None
    _menu_id = None
    _role_id = None
    _tenant_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _setup(self, client, admin_headers):
        """테스트 사용자 생성 → yield → 삭제"""
        roles = assert_success(client.get(f"{PREFIX}/options/roles", headers=admin_headers))
        user_role = next((r for r in roles["items"] if r["role_code"] == "USER"), roles["items"][-1])
        TestUserMenuAssignment._role_id = user_role["role_id"]

        tenants = assert_success(client.get(f"{PREFIX}/options/tenants", headers=admin_headers))
        non_sys = [t for t in tenants["items"] if not t.get("is_system")]
        TestUserMenuAssignment._tenant_id = non_sys[0]["tenant_id"] if non_sys else tenants["items"][0]["tenant_id"]

        menus = assert_success(client.get(f"{PREFIX}/options/menus", headers=admin_headers))
        if menus["items"]:
            TestUserMenuAssignment._menu_id = menus["items"][0]["menu_id"]

        user = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "login_id": "pytest_menu_usr",
            "email": "pytest_menu@test.com",
            "password": "Test1234!",
            "role_id": self._role_id,
            "tenant_id": self._tenant_id,
        }), status_code=201)
        TestUserMenuAssignment._user_id = user["user_id"]

        yield

        client.delete(f"{PREFIX}/{TestUserMenuAssignment._user_id}", headers=admin_headers)

    def test_assign_menus(self, client, admin_headers):
        """메뉴 권한 할당"""
        if not self._menu_id:
            pytest.skip("메뉴 없음")
        data = assert_success(client.put(f"{PREFIX}/{self._user_id}/menus", headers=admin_headers, json={
            "menus": [{"menu_id": self._menu_id, "can_read": True, "can_create": False}],
        }))
        assert data["total_menus"] >= 1

    def test_get_user_menus(self, client, admin_headers):
        """메뉴 권한 조회"""
        data = assert_success(client.get(f"{PREFIX}/{self._user_id}/menus", headers=admin_headers))
        assert "menus" in data


class TestRoleTenantValidation:
    """역할-테넌트 조합 검증"""

    def test_global_auto_system_tenant(self, client, admin_headers):
        """GLOBAL 역할 → 시스템 테넌트 자동 설정"""
        roles = assert_success(client.get(f"{PREFIX}/options/roles", headers=admin_headers))
        global_role = next((r for r in roles["items"] if r["role_code"] == "GLOBAL"), None)
        if not global_role:
            pytest.skip("GLOBAL 역할 없음")

        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "login_id": "pytest_global_usr",
            "email": "pytest_global@test.com",
            "password": "Test1234!",
            "role_id": global_role["role_id"],
            "tenant_id": None,
        }), status_code=201)
        try:
            assert data["tenant_id"] is not None  # 시스템 테넌트로 자동 보정됨
        finally:
            client.delete(f"{PREFIX}/{data['user_id']}", headers=admin_headers)

    def test_user_role_requires_tenant(self, client, admin_headers):
        """USER 역할 → 테넌트 필수"""
        roles = assert_success(client.get(f"{PREFIX}/options/roles", headers=admin_headers))
        user_role = next((r for r in roles["items"] if r["role_code"] == "USER"), None)
        if not user_role:
            pytest.skip("USER 역할 없음")

        resp = client.post(PREFIX, headers=admin_headers, json={
            "login_id": "pytest_no_tenant",
            "email": "pytest_notenant@test.com",
            "password": "Test1234!",
            "role_id": user_role["role_id"],
            "tenant_id": None,
        })
        assert resp.status_code == 400
