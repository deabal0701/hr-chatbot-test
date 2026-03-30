"""
RS256 SSO 키 쌍 생성 스크립트

위치: scripts/generate_sso_keys.py
용도: SSO 인증용 RSA 키 쌍 (private + public) 생성

사용법:
    python scripts/generate_sso_keys.py
    python scripts/generate_sso_keys.py --output-dir /custom/path
    python scripts/generate_sso_keys.py --key-size 4096
"""
import argparse
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_key_pair(output_dir: str = "keys", key_size: int = 2048) -> None:
    """RSA 키 쌍 생성 및 PEM 파일 저장"""
    os.makedirs(output_dir, exist_ok=True)

    private_key_path = os.path.join(output_dir, "sso_private.pem")
    public_key_path = os.path.join(output_dir, "sso_public.pem")

    # 기존 키 확인
    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        answer = input(f"키 파일이 이미 존재합니다 ({output_dir}/). 덮어쓰시겠습니까? (y/N): ")
        if answer.lower() != "y":
            print("취소되었습니다.")
            sys.exit(0)

    # RSA 키 쌍 생성
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    # Private Key 저장 (PEM, PKCS8)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(private_key_path, "wb") as f:
        f.write(private_pem)

    # Public Key 저장 (PEM)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(public_key_path, "wb") as f:
        f.write(public_pem)

    print(f"RSA-{key_size} 키 쌍 생성 완료:")
    print(f"  Private Key: {private_key_path}")
    print(f"  Public Key:  {public_key_path}")
    print()
    print("주의: Private Key는 메인 시스템(SSO 토큰 서명)에서 사용합니다.")
    print("      Public Key만 win-AI 서버에 배포하세요.")
    print("      keys/ 디렉토리는 .gitignore에 포함되어 있습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSO용 RS256 키 쌍 생성")
    parser.add_argument("--output-dir", default="keys", help="키 파일 출력 디렉토리 (기본: keys/)")
    parser.add_argument("--key-size", type=int, default=2048, choices=[2048, 4096], help="RSA 키 크기 (기본: 2048)")
    args = parser.parse_args()

    generate_rsa_key_pair(args.output_dir, args.key_size)
