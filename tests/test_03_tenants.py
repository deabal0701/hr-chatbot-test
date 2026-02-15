"""테넌트 관리 API 테스트

위치: tests/test_03_tenants.py
테넌트 CRUD + 시스템 테넌트 보호 검증
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/admin/v1/tenants"


class TestTenantCRUD:
    """테넌트 생성 → 조회 → 수정 → 삭제 전체 흐름"""

    created_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 테넌트 삭제"""
        yield
        if TestTenantCRUD.created_id:
            client.delete(f"{PREFIX}/{TestTenantCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """테넌트 생성"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "tenant_code": "TEST_PYTEST",
            "tenant_name": "PyTest 테넌트",
            "is_active": True,
        }), status_code=201)
        assert data["tenant_code"] == "TEST_PYTEST"
        TestTenantCRUD.created_id = data["tenant_id"]

    def test_list(self, client, admin_headers):
        """테넌트 목록 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        assert "items" in data
        assert data["total"] >= 1

    def test_get(self, client, admin_headers):
        """테넌트 상세 조회"""
        data = assert_success(client.get(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["tenant_id"] == self.created_id
        assert data["tenant_code"] == "TEST_PYTEST"

    def test_update(self, client, admin_headers):
        """테넌트 수정"""
        data = assert_success(client.put(f"{PREFIX}/{self.created_id}", headers=admin_headers, json={
            "tenant_name": "PyTest 수정됨",
        }))
        assert data["tenant_name"] == "PyTest 수정됨"

    def test_delete(self, client, admin_headers):
        """테넌트 삭제"""
        assert_success(client.delete(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        TestTenantCRUD.created_id = None  # teardown에서 이중 삭제 방지

    def test_duplicate_code(self, client, admin_headers):
        """중복 코드 생성 시 에러"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "tenant_code": "TEST_DUP",
            "tenant_name": "중복 테스트",
        }), status_code=201)
        dup_id = data["tenant_id"]
        try:
            resp = client.post(PREFIX, headers=admin_headers, json={
                "tenant_code": "TEST_DUP",
                "tenant_name": "중복 테스트2",
            })
            assert resp.status_code in (400, 409)
        finally:
            client.delete(f"{PREFIX}/{dup_id}", headers=admin_headers)


class TestTenantProtection:
    """시스템 테넌트 보호"""

    def test_system_tenant_no_delete(self, client, admin_headers):
        """시스템 테넌트(is_system=true) 삭제 불가"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        system_tenants = [t for t in data["items"] if t.get("is_system")]
        if not system_tenants:
            pytest.skip("시스템 테넌트 없음")
        resp = client.delete(f"{PREFIX}/{system_tenants[0]['tenant_id']}", headers=admin_headers)
        assert resp.status_code in (400, 403)
