"""인증 API 테스트

위치: tests/test_02_auth.py
로그인, 토큰 갱신, 사용자 정보, 로그아웃
"""
from conftest import assert_success, assert_error, ADMIN_ID, ADMIN_PW


class TestLogin:
    def test_login_success(self, client):
        """정상 로그인"""
        data = assert_success(
            client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
        )
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["user"]["login_id"] == ADMIN_ID
        assert isinstance(data["user"]["menus"], list)

    def test_login_wrong_password(self, client):
        """잘못된 비밀번호"""
        resp = client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": "wrong"})
        assert resp.status_code in (400, 401)
        assert_error(resp)

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자"""
        resp = client.post("/api/v1/auth/login", json={"login_id": "nouser999", "password": "any"})
        assert resp.status_code in (400, 401, 404)
        assert_error(resp)

    def test_login_empty_body(self, client):
        """빈 요청"""
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code in (400, 422)


class TestTokenRefresh:
    def test_refresh_success(self, client):
        """토큰 갱신"""
        login = assert_success(
            client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
        )
        data = assert_success(
            client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
        )
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_rotation(self, client):
        """Refresh Token 로테이션 — 새 토큰 발급 + 기존 토큰 무효화"""
        # 1. 로그인
        login = assert_success(
            client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
        )
        old_refresh = login["refresh_token"]

        # 2. refresh → 새 refresh_token 발급
        data = assert_success(
            client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        )
        new_refresh = data["refresh_token"]
        assert new_refresh != old_refresh, "로테이션: 새 refresh_token이 발급되어야 함"

        # 3. 기존 토큰으로 재시도 → 실패 (이미 무효화됨)
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code in (400, 401), "기존 refresh_token은 무효화되어야 함"

        # 4. 새 토큰으로 재시도 → 성공
        data2 = assert_success(
            client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
        )
        assert "access_token" in data2

    def test_refresh_invalid_token(self, client):
        """잘못된 refresh token"""
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert resp.status_code in (400, 401)


class TestMe:
    def test_get_me(self, client, admin_headers):
        """현재 사용자 정보"""
        data = assert_success(client.get("/api/v1/auth/me", headers=admin_headers))
        assert data["login_id"] == ADMIN_ID
        assert "role_code" in data
        assert "menus" in data

    def test_get_me_no_token(self, client):
        """토큰 없이 접근"""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestLogout:
    def test_logout(self, client):
        """로그아웃"""
        login = assert_success(
            client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
        )
        headers = {"Authorization": f"Bearer {login['access_token']}"}
        data = assert_success(client.post("/api/v1/auth/logout", headers=headers))
        assert "message" in data
