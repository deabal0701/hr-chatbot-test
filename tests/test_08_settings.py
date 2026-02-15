"""시스템 설정 API 테스트

위치: tests/test_08_settings.py
설정 조회, 수정, 캐시 갱신
"""
import pytest
from conftest import assert_success

PREFIX = "/api/admin/v1/settings"


class TestSettingsRead:
    def test_get_all(self, client, admin_headers):
        """전체 설정 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers))
        assert "categories" in data
        assert len(data["categories"]) > 0

    def test_get_category(self, client, admin_headers):
        """카테고리별 설정 조회"""
        all_data = assert_success(client.get(PREFIX, headers=admin_headers))
        if not all_data["categories"]:
            pytest.skip("설정 없음")
        cat = all_data["categories"][0]["category"]
        data = assert_success(client.get(f"{PREFIX}/{cat}", headers=admin_headers))
        assert "settings" in data

    def test_get_single(self, client, admin_headers):
        """단일 설정 조회"""
        all_data = assert_success(client.get(PREFIX, headers=admin_headers))
        if not all_data["categories"] or not all_data["categories"][0]["settings"]:
            pytest.skip("설정 없음")
        cat = all_data["categories"][0]["category"]
        key = all_data["categories"][0]["settings"][0]["key"]
        data = assert_success(client.get(f"{PREFIX}/{cat}/{key}", headers=admin_headers))
        assert data["key"] == key


class TestSettingsUpdate:
    _cat = None
    _key = None
    _original = None

    @pytest.fixture(autouse=True, scope="class")
    def _find_setting(self, client, admin_headers):
        """수정 가능한 설정 찾기"""
        all_data = assert_success(client.get(PREFIX, headers=admin_headers))
        for cat_group in all_data["categories"]:
            for s in cat_group["settings"]:
                if not s.get("is_secret") and s["value_type"] in ("string", "integer"):
                    TestSettingsUpdate._cat = s["category"]
                    TestSettingsUpdate._key = s["key"]
                    TestSettingsUpdate._original = s["value"]
                    break
            if self._cat:
                break

    def test_update_and_restore(self, client, admin_headers):
        """설정 수정 후 원복"""
        if not self._cat:
            pytest.skip("수정 가능한 설정 없음")

        # 수정
        data = assert_success(client.put(f"{PREFIX}/{self._cat}/{self._key}", headers=admin_headers, json={
            "value": "pytest_temp_value",
        }))
        assert data.get("success") or "updated_count" in data

        # 원복
        assert_success(client.put(f"{PREFIX}/{self._cat}/{self._key}", headers=admin_headers, json={
            "value": self._original,
        }))


class TestSettingsCache:
    def test_refresh_cache(self, client, admin_headers):
        """캐시 갱신"""
        data = assert_success(client.post(f"{PREFIX}/refresh-cache", headers=admin_headers))
        assert data.get("success") or "message" in data
