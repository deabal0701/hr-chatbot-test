"""코드 관리 API 테스트

위치: tests/test_07_codes.py
코드 CRUD + 그룹 조회 + 순서 변경 + 공개 조회
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success

ADMIN_PREFIX = "/api/admin/v1/codes"
PUBLIC_PREFIX = "/api/v1/codes"


class TestCodeCRUD:
    created_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 코드 삭제"""
        yield
        if TestCodeCRUD.created_id:
            client.delete(f"{ADMIN_PREFIX}/{TestCodeCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """코드 생성"""
        data = assert_success(client.post(ADMIN_PREFIX, headers=admin_headers, json={
            "code_group": "PYTEST_GROUP",
            "code_value": "PT_VAL_01",
            "code_name": "PyTest 코드 1",
            "sort_order": 1,
        }), status_code=201)
        assert data["code_value"] == "PT_VAL_01"
        TestCodeCRUD.created_id = data["code_id"]

    def test_get_groups(self, client, admin_headers):
        """코드 그룹 목록"""
        resp = client.get(f"{ADMIN_PREFIX}/groups", headers=admin_headers)
        assert resp.status_code == 200

    def test_get_by_group(self, client, admin_headers):
        """그룹별 코드 조회"""
        data = assert_success(client.get(f"{ADMIN_PREFIX}/PYTEST_GROUP", headers=admin_headers))
        assert data["code_group"] == "PYTEST_GROUP"
        assert len(data["items"]) >= 1

    def test_get_by_id(self, client, admin_headers):
        """코드 상세"""
        data = assert_success(client.get(f"{ADMIN_PREFIX}/item/{self.created_id}", headers=admin_headers))
        assert data["code_id"] == self.created_id

    def test_update(self, client, admin_headers):
        """코드 수정"""
        data = assert_success(client.put(f"{ADMIN_PREFIX}/{self.created_id}", headers=admin_headers, json={
            "code_name": "PyTest 수정됨",
        }))
        assert data["code_name"] == "PyTest 수정됨"

    def test_delete(self, client, admin_headers):
        """코드 삭제"""
        assert_success(client.delete(f"{ADMIN_PREFIX}/{self.created_id}", headers=admin_headers))
        TestCodeCRUD.created_id = None  # teardown에서 이중 삭제 방지


class TestCodeReorder:
    def test_reorder(self, client, admin_headers):
        """코드 순서 변경"""
        c1_id = None
        c2_id = None
        try:
            c1 = assert_success(client.post(ADMIN_PREFIX, headers=admin_headers, json={
                "code_group": "PYTEST_ORD", "code_value": "ORD_A", "code_name": "A",
            }), status_code=201)
            c1_id = c1["code_id"]
            c2 = assert_success(client.post(ADMIN_PREFIX, headers=admin_headers, json={
                "code_group": "PYTEST_ORD", "code_value": "ORD_B", "code_name": "B",
            }), status_code=201)
            c2_id = c2["code_id"]
            # 순서 변경
            data = assert_success(client.post(f"{ADMIN_PREFIX}/PYTEST_ORD/reorder", headers=admin_headers, json={
                "code_ids": [c2_id, c1_id],
            }))
            assert "message" in data
        finally:
            if c1_id:
                client.delete(f"{ADMIN_PREFIX}/{c1_id}", headers=admin_headers)
            if c2_id:
                client.delete(f"{ADMIN_PREFIX}/{c2_id}", headers=admin_headers)


class TestCodePublic:
    def test_public_lookup(self, client, admin_headers):
        """공개 코드 조회 (인증만 필요, 메뉴 권한 불필요)"""
        code_id = None
        try:
            c = assert_success(client.post(ADMIN_PREFIX, headers=admin_headers, json={
                "code_group": "PYTEST_PUB", "code_value": "PUB_01", "code_name": "공개 코드",
            }), status_code=201)
            code_id = c["code_id"]
            # 공개 API로 조회
            data = assert_success(client.get(f"{PUBLIC_PREFIX}/PYTEST_PUB", headers=admin_headers))
            assert data["code_group"] == "PYTEST_PUB"
        finally:
            if code_id:
                client.delete(f"{ADMIN_PREFIX}/{code_id}", headers=admin_headers)
