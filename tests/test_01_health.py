"""서버 헬스체크 테스트

위치: tests/test_01_health.py
서버 기본 연결 및 헬스 상태 확인
"""
from conftest import assert_success


class TestHealth:
    def test_root(self, client):
        """루트 엔드포인트 접근"""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health(self, client):
        """헬스체크 엔드포인트"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"

    def test_api_info(self, client):
        """API 정보 엔드포인트"""
        resp = client.get("/api/v1/info")
        assert resp.status_code == 200
