"""
SSO 로그인 테스트 스크립트

위치: scripts/test_sso_login.py
용도: RS256 Private Key로 SSO JWT를 생성하고 /api/v1/auth/sso 엔드포인트 테스트

사용법:
    python scripts/test_sso_login.py
    python scripts/test_sso_login.py --sub admin --name "시스템 관리자"
    python scripts/test_sso_login.py --base-url http://localhost:19090
"""
import argparse
import json
import sys
import time

import jwt
import requests


def create_sso_token(private_key_path: str, sub: str, name: str, email: str = "",
                     tenant_code: str = "", iss: str = "hr-system", expire_seconds: int = 300) -> str:
    """RS256 Private Key로 SSO JWT 토큰 생성"""
    with open(private_key_path, "r") as f:
        private_key = f.read()

    payload = {
        "sub": sub,
        "name": name,
        "iss": iss,
        "iat": int(time.time()),
        "exp": int(time.time()) + expire_seconds,
    }
    if email:
        payload["email"] = email
    if tenant_code:
        payload["tenant_code"] = tenant_code

    return jwt.encode(payload, private_key, algorithm="RS256")


def test_sso_login(base_url: str, sso_token: str) -> dict:
    """SSO 로그인 API 호출"""
    url = f"{base_url}/api/v1/auth/sso"
    resp = requests.post(url, json={"sso_token": sso_token}, timeout=10)
    return {"status_code": resp.status_code, "body": resp.json()}


def main():
    parser = argparse.ArgumentParser(description="SSO 로그인 테스트")
    parser.add_argument("--private-key", default="keys/sso_private.pem", help="Private Key 파일 경로")
    parser.add_argument("--base-url", default="http://localhost:19090", help="API 서버 URL")
    parser.add_argument("--sub", default="admin", help="사번 (login_id)")
    parser.add_argument("--name", default="시스템 관리자", help="사용자 이름")
    parser.add_argument("--email", default="admin@company.com", help="이메일")
    parser.add_argument("--tenant-code", default="SYSTEM", help="테넌트 코드")
    parser.add_argument("--iss", default="hr-system", help="토큰 발급자")
    args = parser.parse_args()

    print("=" * 60)
    print("SSO 로그인 테스트")
    print("=" * 60)

    # 1. SSO 토큰 생성
    print(f"\n[1] SSO 토큰 생성...")
    print(f"    sub={args.sub}, name={args.name}, iss={args.iss}")
    try:
        token = create_sso_token(
            args.private_key, args.sub, args.name,
            args.email, args.tenant_code, args.iss
        )
        print(f"    토큰: {token[:60]}...")
    except FileNotFoundError:
        print(f"    [ERROR] Private Key 파일 없음: {args.private_key}")
        print(f"    → python scripts/generate_sso_keys.py 실행 필요")
        sys.exit(1)
    except Exception as e:
        print(f"    [ERROR] 토큰 생성 실패: {e}")
        sys.exit(1)

    # 2. SSO 로그인 API 호출
    print(f"\n[2] SSO 로그인 API 호출...")
    print(f"    URL: {args.base_url}/api/v1/auth/sso")
    try:
        result = test_sso_login(args.base_url, token)
    except requests.ConnectionError:
        print(f"    [ERROR] 서버 연결 실패: {args.base_url}")
        print(f"    → 서버가 실행 중인지 확인하세요")
        sys.exit(1)

    print(f"    Status: {result['status_code']}")
    print(f"    Response:")
    print(json.dumps(result["body"], indent=4, ensure_ascii=False))

    # 3. 결과 판단
    if result["status_code"] == 200 and result["body"].get("success"):
        print(f"\n[결과] SSO 로그인 성공!")
        user = result["body"]["data"]["user"]
        print(f"    user_id: {user['user_id']}")
        print(f"    login_id: {user['login_id']}")
        print(f"    display_name: {user['display_name']}")
        print(f"    role_code: {user['role_code']}")
        print(f"    landing_page: {user['landing_page']}")
        print(f"    menus: {len(user.get('menus', []))}개")
    else:
        print(f"\n[결과] SSO 로그인 실패!")
        error = result["body"].get("error", {})
        print(f"    error_code: {error.get('code', 'N/A')}")
        print(f"    message: {error.get('message', 'N/A')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
