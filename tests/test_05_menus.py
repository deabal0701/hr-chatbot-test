"""메뉴 관리 API 테스트

위치: tests/test_05_menus.py
메뉴 CRUD + 트리 조회 + 순서 변경
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success

PREFIX = "/api/admin/v1/menus"


class TestMenuCRUD:
    created_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 메뉴 삭제"""
        yield
        if TestMenuCRUD.created_id:
            client.delete(f"{PREFIX}/{TestMenuCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """메뉴 생성"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "menu_code": "TEST_MENU_PT",
            "menu_name": "PyTest 메뉴",
            "menu_type": "PAGE",
            "menu_path": "/test/pytest",
            "sort_order": 999,
        }), status_code=201)
        assert data["menu_code"] == "TEST_MENU_PT"
        TestMenuCRUD.created_id = data["menu_id"]

    def test_get_tree(self, client, admin_headers):
        """메뉴 트리 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        assert "items" in data
        assert len(data["items"]) > 0

    def test_get(self, client, admin_headers):
        """메뉴 상세 조회"""
        data = assert_success(client.get(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["menu_id"] == self.created_id

    def test_update(self, client, admin_headers):
        """메뉴 수정"""
        data = assert_success(client.put(f"{PREFIX}/{self.created_id}", headers=admin_headers, json={
            "menu_name": "PyTest 수정됨",
            "icon": "Setting",
        }))
        assert data["menu_name"] == "PyTest 수정됨"

    def test_delete(self, client, admin_headers):
        """메뉴 삭제"""
        assert_success(client.delete(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        TestMenuCRUD.created_id = None  # teardown에서 이중 삭제 방지


class TestMenuReorder:
    def test_reorder(self, client, admin_headers):
        """메뉴 순서 변경"""
        tree = assert_success(client.get(PREFIX, headers=admin_headers))
        items = tree["items"]
        if len(items) < 2:
            return
        reorder_items = [
            {"menu_id": items[0]["menu_id"], "sort_order": 100},
            {"menu_id": items[1]["menu_id"], "sort_order": 200},
        ]
        data = assert_success(client.put(f"{PREFIX}/reorder", headers=admin_headers, json={
            "items": reorder_items,
        }))
        assert "message" in data
        assert "updated_count" in data
