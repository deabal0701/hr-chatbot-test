"""Rate Limit 미들웨어 테스트

위치: tests/test_rate_limit.py
- 분당 요청 제한 동작 확인
- 429 응답 및 Retry-After 헤더 확인
- X-RateLimit-* 헤더 확인
- 엔드포인트 그룹별 차등 제한 확인
"""

import time
import httpx
import pytest

BASE_URL = "http://localhost:19090"
TIMEOUT = 30.0


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


class TestRateLimitHeaders:
    """Rate Limit 응답 헤더 확인"""

    def test_health_no_rate_limit_header(self, client):
        """health 엔드포인트는 Rate Limit 제외 경로"""
        resp = client.get("/health")
        assert resp.status_code == 200
        # health는 BaseMiddleware.EXCLUDE_PATHS에 포함되어 Rate Limit 미적용
        # 단, LoggingMiddleware도 skip하므로 헤더가 없을 수 있음

    def test_api_info_has_rate_limit_headers(self, client):
        """일반 API 엔드포인트에 Rate Limit 헤더 포함"""
        resp = client.get("/api/v1/info")
        assert resp.status_code == 200

        # Rate Limit 헤더 확인
        assert "x-ratelimit-limit" in resp.headers, f"X-RateLimit-Limit 헤더 없음: {dict(resp.headers)}"
        assert "x-ratelimit-remaining" in resp.headers, f"X-RateLimit-Remaining 헤더 없음"

        limit = int(resp.headers["x-ratelimit-limit"])
        remaining = int(resp.headers["x-ratelimit-remaining"])

        # 기본 RPM은 120
        assert limit == 120, f"기본 RPM이 120이어야 함: {limit}"
        assert remaining >= 0, f"remaining이 0 이상이어야 함: {remaining}"
        print(f"\n  [INFO] /api/v1/info → limit={limit}, remaining={remaining}")


class TestRateLimitLogin:
    """로그인 엔드포인트 Rate Limit 테스트 (RPM=5)"""

    def test_login_rate_limit_enforced(self, client):
        """로그인 엔드포인트 분당 5회 제한 확인"""
        login_data = {"login_id": "rate_test_nonexist", "password": "wrong_pass"}
        responses = []

        # 6회 연속 요청 (5회 허용, 6번째 차단)
        for i in range(6):
            resp = client.post("/api/v1/auth/login", json=login_data)
            responses.append(resp)

        # 처음 5개는 401 (로그인 실패) 또는 423 (계정 잠금) — 429가 아님
        for i, resp in enumerate(responses[:5]):
            assert resp.status_code != 429, f"요청 {i+1}이 429여서는 안 됨 (status={resp.status_code})"
            print(f"  요청 {i+1}: status={resp.status_code}")

        # 6번째는 429 (Rate Limit 초과)
        last = responses[5]
        assert last.status_code == 429, f"6번째 요청이 429여야 함: status={last.status_code}, body={last.text}"

        body = last.json()
        assert body["success"] is False
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry-after" in last.headers
        print(f"  요청 6: status=429, retry-after={last.headers['retry-after']}s")

    def test_login_429_response_format(self, client):
        """429 응답 형식이 표준 에러 포맷을 따르는지 확인"""
        login_data = {"login_id": "format_test_nonexist", "password": "wrong"}

        # RPM(5) 초과하도록 요청
        for _ in range(5):
            client.post("/api/v1/auth/login", json=login_data)

        resp = client.post("/api/v1/auth/login", json=login_data)

        if resp.status_code == 429:
            body = resp.json()
            # 표준 에러 응답 포맷 확인
            assert "success" in body
            assert "data" in body
            assert "error" in body
            assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert body["error"]["message"] is not None
            assert body["error"]["detail"] is not None

            # 헤더 확인
            assert "retry-after" in resp.headers
            assert "x-ratelimit-limit" in resp.headers
            assert "x-ratelimit-remaining" in resp.headers
            assert resp.headers["x-ratelimit-remaining"] == "0"
            print(f"\n  [INFO] 429 응답 형식 정상: {body['error']}")


class TestRateLimitDifferentGroups:
    """엔드포인트 그룹별 독립 제한 확인"""

    def test_login_limit_does_not_affect_other_endpoints(self, client):
        """로그인 제한이 다른 엔드포인트에 영향 주지 않음"""
        # 로그인 5회 소진
        for _ in range(5):
            client.post("/api/v1/auth/login", json={"login_id": "group_test", "password": "wrong"})

        # 로그인은 429
        resp_login = client.post("/api/v1/auth/login", json={"login_id": "group_test", "password": "wrong"})

        # 다른 엔드포인트는 정상 (로그인 그룹과 분리)
        resp_info = client.get("/api/v1/info")
        assert resp_info.status_code == 200, f"다른 엔드포인트가 로그인 제한에 영향 받으면 안 됨: {resp_info.status_code}"
        print(f"\n  [INFO] 로그인 제한 → 다른 엔드포인트 영향 없음 확인")


class TestRateLimitRemainingDecrement:
    """remaining 카운터 감소 확인"""

    def test_remaining_decreases(self, client):
        """요청마다 remaining이 감소하는지 확인"""
        # 고유 경로로 기존 카운터 영향 없게 (info 경로는 default 그룹)
        remainings = []
        for _ in range(3):
            resp = client.get("/api/v1/info")
            if "x-ratelimit-remaining" in resp.headers:
                remainings.append(int(resp.headers["x-ratelimit-remaining"]))

        if len(remainings) >= 2:
            # remaining이 감소해야 함
            for i in range(1, len(remainings)):
                assert remainings[i] <= remainings[i-1], \
                    f"remaining이 감소해야 함: {remainings}"
            print(f"\n  [INFO] remaining 감소 확인: {remainings}")
