"""역할 관리 API 테스트

위치: tests/test_04_roles.py
역할 CRUD + 기본 메뉴 조회 + 시스템 역할 보호
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/admin/v1/roles"


class TestRoleCRUD:
    created_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 역할 삭제"""
        yield
        if TestRoleCRUD.created_id:
            client.delete(f"{PREFIX}/{TestRoleCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """역할 생성"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "role_code": "TEST_ROLE",
            "role_name": "PyTest 역할",
            "landing_page": "/chat",
        }), status_code=201)
        assert data["role_code"] == "TEST_ROLE"
        TestRoleCRUD.created_id = data["role_id"]

    def test_list(self, client, admin_headers):
        """역할 목록 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        assert "items" in data
        assert data["total"] >= 3  # GLOBAL, TENANT, USER 기본 역할

    def test_get(self, client, admin_headers):
        """역할 상세 조회"""
        data = assert_success(client.get(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["role_id"] == self.created_id

    def test_update(self, client, admin_headers):
        """역할 수정"""
        data = assert_success(client.put(f"{PREFIX}/{self.created_id}", headers=admin_headers, json={
            "role_name": "PyTest 수정됨",
        }))
        assert data["role_name"] == "PyTest 수정됨"

    def test_delete(self, client, admin_headers):
        """역할 삭제"""
        assert_success(client.delete(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        TestRoleCRUD.created_id = None  # teardown에서 이중 삭제 방지


class TestDefaultMenus:
    def test_global_default_menus(self, client, admin_headers):
        """GLOBAL 역할 기본 메뉴 조회"""
        data = assert_success(client.get(f"{PREFIX}/default-menus/GLOBAL", headers=admin_headers))
        assert "items" in data
        assert data["total"] > 0
        assert len(data["items"]) == data["total"]

    def test_user_default_menus(self, client, admin_headers):
        """USER 역할 기본 메뉴 조회"""
        data = assert_success(client.get(f"{PREFIX}/default-menus/USER", headers=admin_headers))
        assert "items" in data


class TestRoleProtection:
    def test_system_role_no_delete(self, client, admin_headers):
        """시스템 역할 삭제 불가"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        system_roles = [r for r in data["items"] if r.get("is_system")]
        if not system_roles:
            pytest.skip("시스템 역할 없음")
        resp = client.delete(f"{PREFIX}/{system_roles[0]['role_id']}", headers=admin_headers)
        assert resp.status_code in (400, 403)
