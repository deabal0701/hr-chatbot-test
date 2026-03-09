"""테스트 공통 Fixture

위치: tests/conftest.py
- BASE_URL: 환경변수 TEST_BASE_URL 또는 기본값 http://localhost:19090
- admin 로그인 → access_token 제공
- 테스트 데이터 정리용 cleanup 리스트

참고:
- 모든 API 호출은 HistoryMiddleware에 의해 tb_api_history에 자동 기록됨
- tb_api_history 데이터는 테스트 정확성에 영향을 주지 않으므로 별도 정리 불필요
- 필요 시 DB에서 직접 삭제: DELETE FROM tb_api_history WHERE request_path LIKE '/api/%' AND created_at >= '테스트시작시간'
"""
import os
import pytest
import httpx

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:19090")
ADMIN_ID = os.getenv("TEST_ADMIN_ID", "admin")
ADMIN_PW = os.getenv("TEST_ADMIN_PW", "Win1234!")
TIMEOUT = 30.0


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def client():
    """세션 전체에서 재사용되는 httpx 클라이언트"""
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    """admin 계정 로그인 → access_token 반환"""
    resp = client.post("/api/v1/auth/login", json={
        "login_id": ADMIN_ID,
        "password": ADMIN_PW,
    })
    assert resp.status_code == 200, f"admin 로그인 실패: {resp.text}"
    body = resp.json()
    assert body["success"] is True, f"admin 로그인 응답 실패: {body}"
    return body["data"]["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """인증 헤더"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def admin_user_info(client, admin_headers):
    """admin 사용자 정보"""
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    return resp.json()["data"]


# ── 헬퍼 함수 ──

def assert_success(resp, status_code=200):
    """응답 성공 검증 헬퍼"""
    assert resp.status_code == status_code, f"HTTP {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["success"] is True, f"응답 실패: {body.get('error')}"
    return body["data"]


def assert_error(resp, expected_code=None):
    """응답 실패 검증 헬퍼"""
    body = resp.json()
    assert body["success"] is False, f"성공이면 안 됨: {body}"
    if expected_code:
        assert body["error"]["code"] == expected_code
    return body["error"]
