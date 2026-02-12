"""
비밀번호 해싱 및 검증 유틸리티

위치: app/core/security/password.py
bcrypt 알고리즘을 사용한 비밀번호 처리
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """비밀번호를 bcrypt로 해싱 (cost factor = 12)"""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시 비교"""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
