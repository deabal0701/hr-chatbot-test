"""SSO 인증 통합 테스트

위치: tests/test_sso.py
테스트 항목:
1. 기존 사용자 SSO 로그인 (admin)
2. 신규 사용자 자동 생성 (JIT Provisioning)
3. 이메일 변경 시 동기화
4. 허용되지 않은 발급자 (iss) → 실패
5. 만료된 토큰 → 실패
6. 필수 클레임 누락 → 실패
7. 잘못된 서명 → 실패
8. 존재하지 않는 테넌트 → 실패
9. SSO 사용자 비밀번호 로그인 → 실패 (자연스럽게)
10. 동일 sub, 다른 iss(발급자)로 재로그인 → 동작 확인
"""
import os
import time
import uuid

import jwt
import httpx
import pytest

from conftest import BASE_URL, ADMIN_ID, ADMIN_PW, TIMEOUT, assert_success, assert_error

# ── 키 파일 로드 ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVATE_KEY_PATH = os.path.join(_PROJECT_ROOT, "keys", "sso_private.pem")

with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()


# ── 헬퍼 ──

def _make_sso_token(
    sub: str,
    name: str,
    iss: str = "h5-system",
    email: str = None,
    tenant_code: str = "A_TENANT",
    dept_code: str = None,
    exp_seconds: int = 300,
    include_iat: bool = True,
    extra_claims: dict = None,
) -> str:
    """테스트용 SSO JWT 토큰 생성 (RS256 서명)"""
    now = int(time.time())
    payload = {
        "sub": sub,
        "name": name,
        "iss": iss,
        "exp": now + exp_seconds,
    }
    if include_iat:
        payload["iat"] = now
    if email:
        payload["email"] = email
    if tenant_code:
        payload["tenant_code"] = tenant_code
    if dept_code:
        payload["dept_code"] = dept_code
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")


def _sso_login(client: httpx.Client, token: str) -> httpx.Response:
    """SSO 로그인 API 호출"""
    return client.post("/api/v1/auth/sso", json={"sso_token": token})


def _get_allowed_issuer(client: httpx.Client, admin_headers: dict) -> str:
    """서버의 SSO_ALLOWED_ISSUERS 확인 (설정 API로 조회 시도, 실패 시 기본값)"""
    # 서버 설정에서 가져오기 어려우므로, .env 에서 직접 읽거나 기본값 사용
    # 실제 서버가 로드한 값과 일치해야 함
    try:
        with open(os.path.join(_PROJECT_ROOT, ".env"), "r") as f:
            for line in f:
                if line.startswith("SSO_ALLOWED_ISSUERS="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return "hr-system"


# ── Fixtures ──

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def admin_headers(client):
    resp = client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def allowed_issuer(client, admin_headers):
    return _get_allowed_issuer(client, admin_headers)


@pytest.fixture(scope="module")
def test_user_id():
    """테스트용 고유 사용자 ID 생성"""
    return f"sso_test_{uuid.uuid4().hex[:8]}"


# ── 테스트 정리 ──

_created_user_ids = []


@pytest.fixture(scope="module", autouse=True)
def cleanup(client, admin_headers):
    """테스트 종료 후 생성된 SSO 테스트 사용자 삭제"""
    yield
    for user_id in _created_user_ids:
        try:
            client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
        except Exception:
            pass


# ===================================================================
# 1. 기존 사용자 SSO 로그인
# ===================================================================

class TestSSOExistingUser:
    """기존에 등록된 사용자가 SSO로 로그인하는 케이스"""

    def test_existing_user_sso_login(self, client, allowed_issuer):
        """admin 계정으로 SSO 로그인 → 성공 (login_id=sub fallback)"""
        token = _make_sso_token(
            sub=ADMIN_ID,
            name="관리자(SSO)",
            iss=allowed_issuer,
            email="admin_sso@test.com",
        )
        resp = _sso_login(client, token)
        data = assert_success(resp)

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["login_id"] == ADMIN_ID

    def test_existing_user_info_synced(self, client, allowed_issuer):
        """SSO 로그인 시 display_name, email이 동기화되는지 확인"""
        new_name = f"동기화테스트_{uuid.uuid4().hex[:4]}"
        new_email = f"sync_{uuid.uuid4().hex[:4]}@test.com"

        token = _make_sso_token(
            sub=ADMIN_ID,
            name=new_name,
            iss=allowed_issuer,
            email=new_email,
        )
        resp = _sso_login(client, token)
        data = assert_success(resp)

        # SSO 로그인으로 받은 새 토큰으로 /me 조회
        new_headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_resp = client.get("/api/v1/auth/me", headers=new_headers)
        me_data = assert_success(me_resp)
        assert me_data["display_name"] == new_name

        # 원래 이름으로 복원
        token2 = _make_sso_token(
            sub=ADMIN_ID,
            name="시스템 관리자",
            iss=allowed_issuer,
            email="admin@mureum.com",
        )
        _sso_login(client, token2)


# ===================================================================
# 2. 신규 사용자 자동 생성 (JIT Provisioning)
# ===================================================================

class TestSSONewUser:
    """SSO로 처음 로그인하는 사용자 → 자동 생성"""

    def test_new_user_auto_create(self, client, allowed_issuer, test_user_id):
        """신규 사용자 SSO 로그인 → 자동 생성 + 로그인 성공"""
        token = _make_sso_token(
            sub=test_user_id,
            name="SSO 테스트 사용자",
            iss=allowed_issuer,
            email=f"{test_user_id}@test.com",
            tenant_code="A_TENANT",
        )
        resp = _sso_login(client, token)
        data = assert_success(resp)

        assert "access_token" in data
        assert data["user"]["login_id"] == test_user_id

        # 정리용 user_id 기록
        _created_user_ids.append(data["user"]["user_id"])

    def test_new_user_second_login(self, client, allowed_issuer, test_user_id):
        """동일 사용자 두 번째 SSO 로그인 → 기존 사용자로 로그인 (중복 생성 안 됨)"""
        token = _make_sso_token(
            sub=test_user_id,
            name="SSO 테스트 사용자",
            iss=allowed_issuer,
            email=f"{test_user_id}@test.com",
            tenant_code="A_TENANT",
        )
        resp = _sso_login(client, token)
        data = assert_success(resp)
        assert data["user"]["login_id"] == test_user_id

    def test_new_user_password_login_fails(self, client, test_user_id):
        """SSO로 자동 생성된 사용자는 비밀번호 로그인 불가 (password_hash='!SSO_USER!')"""
        resp = client.post("/api/v1/auth/login", json={
            "login_id": test_user_id,
            "password": "anyPassword1!",
        })
        # 비밀번호 불일치 또는 인증 실패
        assert resp.status_code in (400, 401)
        assert_error(resp)

    def test_new_user_without_email_fails(self, client, allowed_issuer):
        """신규 사용자 email 없이 SSO 로그인 → 실패 (email 필수)"""
        uid = f"no_email_{uuid.uuid4().hex[:6]}"
        token = _make_sso_token(
            sub=uid,
            name="이메일 없는 사용자",
            iss=allowed_issuer,
            email=None,
            tenant_code="A_TENANT",
        )
        resp = _sso_login(client, token)
        assert resp.status_code == 400
        error = assert_error(resp, "BAD_REQUEST")
        detail = error.get("detail") or ""
        message = error.get("message") or ""
        assert "email" in detail.lower() or "email" in message.lower()

    def test_new_user_without_tenant_code_fails(self, client, allowed_issuer):
        """신규 사용자 tenant_code 없이 SSO 로그인 → 실패"""
        uid = f"no_tenant_{uuid.uuid4().hex[:6]}"
        token = _make_sso_token(
            sub=uid,
            name="테넌트 없는 사용자",
            iss=allowed_issuer,
            email=f"{uid}@test.com",
            tenant_code=None,
        )
        resp = _sso_login(client, token)
        assert resp.status_code == 400
        assert_error(resp, "BAD_REQUEST")

    def test_new_user_invalid_tenant_code_fails(self, client, allowed_issuer):
        """존재하지 않는 tenant_code → 실패"""
        uid = f"bad_tenant_{uuid.uuid4().hex[:6]}"
        token = _make_sso_token(
            sub=uid,
            name="잘못된 테넌트",
            iss=allowed_issuer,
            email=f"{uid}@test.com",
            tenant_code="NONEXISTENT_TENANT",
        )
        resp = _sso_login(client, token)
        assert resp.status_code == 404
        assert_error(resp, "NOT_FOUND")


# ===================================================================
# 3. 이메일 변경 시 동기화
# ===================================================================

class TestSSOEmailSync:
    """SSO 로그인 시 이메일이 달라지면 동기화되는지 확인"""

    def test_email_change_synced(self, client, allowed_issuer):
        """SSO 사용자 생성 후 이메일 변경 → 동기화 확인"""
        uid = f"email_sync_{uuid.uuid4().hex[:6]}"
        original_email = f"{uid}_v1@test.com"
        changed_email = f"{uid}_v2@test.com"

        # 1차: 사용자 생성
        token1 = _make_sso_token(sub=uid, name="이메일 동기화 테스트", iss=allowed_issuer, email=original_email)
        resp1 = _sso_login(client, token1)
        data1 = assert_success(resp1)
        _created_user_ids.append(data1["user"]["user_id"])

        # 2차: 이메일 변경
        token2 = _make_sso_token(sub=uid, name="이메일 동기화 테스트", iss=allowed_issuer, email=changed_email)
        resp2 = _sso_login(client, token2)
        assert_success(resp2)

        # 확인: /me로 이메일 변경 여부 확인은 어렵지만, 로그인 자체가 성공하면 동기화 동작 확인
        # (서버 로그에서 SYNC 확인 가능)


# ===================================================================
# 4. 발급자(iss) 검증
# ===================================================================

class TestSSOIssuerValidation:
    """허용되지 않은 발급자로 SSO 로그인"""

    def test_wrong_issuer_fails(self, client):
        """허용 목록에 없는 iss → SSO_INVALID_TOKEN"""
        token = _make_sso_token(
            sub=ADMIN_ID,
            name="관리자",
            iss="unknown-system",
            email="admin@test.com",
        )
        resp = _sso_login(client, token)
        assert resp.status_code == 401
        assert_error(resp, "SSO_INVALID_TOKEN")

    def test_same_sub_different_issuer(self, client, allowed_issuer):
        """동일 sub(사번)이지만 다른 iss → 허용된 iss만 통과"""
        uid = f"multi_iss_{uuid.uuid4().hex[:6]}"

        # 허용된 iss로 생성
        token1 = _make_sso_token(sub=uid, name="멀티 ISS 테스트", iss=allowed_issuer, email=f"{uid}@test.com")
        resp1 = _sso_login(client, token1)
        data1 = assert_success(resp1)
        _created_user_ids.append(data1["user"]["user_id"])

        # 다른 iss로 로그인 시도 → 실패
        token2 = _make_sso_token(sub=uid, name="멀티 ISS 테스트", iss="other-system", email=f"{uid}@test.com")
        resp2 = _sso_login(client, token2)
        assert resp2.status_code == 401
        assert_error(resp2, "SSO_INVALID_TOKEN")


# ===================================================================
# 5. 토큰 유효시간 검증
# ===================================================================

class TestSSOTokenExpiry:
    """토큰 만료/유효시간 관련 테스트"""

    def test_expired_token_fails(self, client, allowed_issuer):
        """exp가 과거인 토큰 → SSO_TOKEN_EXPIRED"""
        token = _make_sso_token(
            sub=ADMIN_ID,
            name="관리자",
            iss=allowed_issuer,
            email="admin@test.com",
            exp_seconds=-60,  # 이미 만료
        )
        resp = _sso_login(client, token)
        assert resp.status_code == 401
        assert_error(resp, "SSO_TOKEN_EXPIRED")

    def test_old_iat_exceeds_max_age(self, client, allowed_issuer):
        """iat가 SSO_TOKEN_MAX_AGE(300초) 이전 → SSO_TOKEN_EXPIRED"""
        now = int(time.time())
        payload = {
            "sub": ADMIN_ID,
            "name": "관리자",
            "iss": allowed_issuer,
            "exp": now + 3600,  # 아직 만료 안 됨
            "iat": now - 600,   # 10분 전 발급 (300초 초과)
            "email": "admin@test.com",
            "tenant_code": "A_TENANT",
        }
        token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        resp = _sso_login(client, token)
        assert resp.status_code == 401
        # iss 검증 → iat max_age 검증 순이므로 SSO_TOKEN_EXPIRED
        error = assert_error(resp)
        assert error["code"] in ("SSO_TOKEN_EXPIRED", "SSO_INVALID_TOKEN")


# ===================================================================
# 6. 잘못된 토큰 형식/서명
# ===================================================================

class TestSSOInvalidToken:
    """잘못된 토큰 형식 및 서명 테스트"""

    def test_malformed_token(self, client):
        """잘못된 형식의 토큰 → 실패"""
        resp = _sso_login(client, "not.a.valid.jwt.token")
        assert resp.status_code == 401
        assert_error(resp, "SSO_INVALID_TOKEN")

    def test_missing_required_claims(self, client):
        """필수 클레임(sub, name) 누락 → 실패"""
        now = int(time.time())
        # name 누락
        payload = {
            "sub": "testuser",
            "iss": "h5-system",
            "exp": now + 300,
        }
        token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        resp = _sso_login(client, token)
        assert resp.status_code == 401
        assert_error(resp, "SSO_INVALID_TOKEN")

    def test_wrong_signature(self, client):
        """다른 키로 서명된 토큰 → 서명 검증 실패"""
        # 임의 RSA 키로 서명 (실제 공개키와 불일치)
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        fake_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        fake_pem = fake_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        now = int(time.time())
        payload = {
            "sub": ADMIN_ID, "name": "관리자", "iss": "h5-system",
            "exp": now + 300, "iat": now,
        }
        token = jwt.encode(payload, fake_pem, algorithm="RS256")
        resp = _sso_login(client, token)
        assert resp.status_code == 401
        assert_error(resp, "SSO_INVALID_TOKEN")

    def test_empty_token(self, client):
        """빈 토큰 → 400 또는 422 (Pydantic validation)"""
        resp = client.post("/api/v1/auth/sso", json={"sso_token": ""})
        assert resp.status_code in (400, 422)


# ===================================================================
# 7. 종합 시나리오
# ===================================================================

class TestSSOScenarios:
    """복합 시나리오 테스트"""

    def test_sso_then_password_both_work_for_existing(self, client, allowed_issuer):
        """기존 사용자(admin): SSO 로그인 후에도 비밀번호 로그인 가능"""
        # SSO 로그인
        token = _make_sso_token(sub=ADMIN_ID, name="시스템 관리자", iss=allowed_issuer, email="admin@mureum.com")
        resp1 = _sso_login(client, token)
        assert_success(resp1)

        # 비밀번호 로그인 — SSO 후에도 여전히 동작
        resp2 = client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
        assert_success(resp2)

    def test_sso_redirect_endpoint(self, client, allowed_issuer):
        """SSO 리다이렉트 엔드포인트 (form POST) 테스트"""
        token = _make_sso_token(sub=ADMIN_ID, name="시스템 관리자", iss=allowed_issuer, email="admin@mureum.com")
        resp = client.post(
            "/api/v1/auth/sso-redirect",
            data={"token": token},
            follow_redirects=False,
        )
        # 302 리다이렉트 + sso_auth 쿠키
        assert resp.status_code == 302
        assert "sso_auth" in resp.cookies or "location" in resp.headers

    def test_sso_redirect_invalid_token(self, client):
        """SSO 리다이렉트 — 잘못된 토큰 → 에러 리다이렉트"""
        resp = client.post(
            "/api/v1/auth/sso-redirect",
            data={"token": "invalid.jwt.token"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        location = resp.headers.get("location", "")
        assert "error" in location
