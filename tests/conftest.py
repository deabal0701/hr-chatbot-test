"""테스트 공통 Fixture

위치: tests/conftest.py
- BASE_URL: 환경변수 TEST_BASE_URL 또는 기본값 http://localhost:19090
- admin 로그인 → access_token 제공
- 테스트 데이터 정리용 cleanup 리스트
- 세션 종료 시 DB 직접 정리 (API rate limit 우회)

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


# ── DB 직접 정리 (전체 테스트 종료 후) ──

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb",
)


@pytest.fixture(autouse=True, scope="session")
def _cleanup_test_data_after_session():
    """
    전체 테스트 세션 종료 후 잔여 테스트 데이터를 DB에서 직접 삭제.

    API cleanup이 rate limit 등으로 실패해도 DB 레벨에서 확실히 정리.
    테스트 데이터는 PYTEST/pytest 접두사로 식별.
    """
    yield  # ← 모든 테스트 실행 후 아래 코드 실행

    try:
        import psycopg
        conn = psycopg.connect(DATABASE_URL)
        cur = conn.cursor()
        deleted = {}

        # 순서 중요: FK 의존성 고려 (자식 → 부모)
        cleanup_queries = [
            ("tb_user_menu", "DELETE FROM tb_user_menu WHERE user_id IN (SELECT user_id FROM tb_user WHERE login_id LIKE 'pytest%')"),
            ("tb_user_session", "DELETE FROM tb_user_session WHERE user_id IN (SELECT user_id FROM tb_user WHERE login_id LIKE 'pytest%')"),
            ("tb_user", "DELETE FROM tb_user WHERE login_id LIKE 'pytest%'"),
            ("tb_code", "DELETE FROM tb_code WHERE code_group LIKE 'PYTEST%'"),
            ("tb_menu", "DELETE FROM tb_menu WHERE menu_code LIKE 'PYTEST%' OR menu_code LIKE 'TEST_MENU%'"),
            ("tb_role", "DELETE FROM tb_role WHERE role_code LIKE 'TEST_%' AND is_system = false"),
            ("tb_tenant", "DELETE FROM tb_tenant WHERE tenant_code LIKE 'TEST_%' AND is_system = false"),
            ("tb_docs", "DELETE FROM tb_docs WHERE title LIKE 'PyTest%'"),
        ]

        for table, sql in cleanup_queries:
            cur.execute(sql)
            if cur.rowcount > 0:
                deleted[table] = cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        if deleted:
            summary = ", ".join(f"{t}={n}" for t, n in deleted.items())
            print(f"\n[CLEANUP] 잔여 테스트 데이터 DB 직접 삭제: {summary}")
    except Exception as e:
        print(f"\n[CLEANUP] DB 정리 실패 (무시): {e}")
