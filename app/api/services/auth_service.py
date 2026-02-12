"""인증 서비스

위치: app/api/services/auth_service.py
로그인, 세션 관리, 토큰 갱신, 비밀번호 변경 비즈니스 로직
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.config import settings
from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security.password import hash_password, verify_password
from app.models.auth import TokenResponse, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# scope_type 우선순위 (숫자가 클수록 넓은 범위)
_SCOPE_PRIORITY = {"USER": 1, "TENANT": 2, "GLOBAL": 3}


class AuthService:
    """인증 비즈니스 로직"""

    def authenticate(self, login_id: str, password: str, request_id: str = "") -> Dict[str, Any]:
        """로그인 검증 — 비밀번호 확인 + 실패 횟수 관리 + 계정 잠금"""
        log_step(logger, request_id, "AUTH", "1", "LOGIN", "로그인 시도", login_id=login_id)

        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, login_id, password_hash, is_active, is_superuser, "
                "login_fail_count, locked_until, display_name, tenant_id "
                "FROM tb_user WHERE login_id = %s",
                (login_id,),
            )
            row = cur.fetchone()

        if not row:
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "사용자 없음", login_id=login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다")

        user = dict(row)

        # 비활성 계정
        if not user["is_active"]:
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "비활성 계정", login_id=login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 계정 잠금 확인
        if user["locked_until"]:
            now = datetime.now(timezone.utc)
            if now < user["locked_until"]:
                remaining = int((user["locked_until"] - now).total_seconds() // 60) + 1
                log_step(logger, request_id, "AUTH", "1", "LOGIN", "계정 잠금", login_id=login_id, remaining_min=remaining)
                raise APIException(ErrorCode.ACCOUNT_LOCKED, f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요")

            # 잠금 시간 경과 → 잠금 해제
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("UPDATE tb_user SET locked_until = NULL, login_fail_count = 0 WHERE user_id = %s", (user["user_id"],))

        # 비밀번호 검증
        if not verify_password(password, user["password_hash"]):
            self._handle_login_failure(user["user_id"], user["login_fail_count"], request_id, login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다")

        # 로그인 성공 → 실패 횟수 초기화 + last_login_at 갱신
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("UPDATE tb_user SET login_fail_count = 0, locked_until = NULL, last_login_at = NOW() WHERE user_id = %s", (user["user_id"],))

        log_step(logger, request_id, "AUTH", "1", "LOGIN", "로그인 성공", login_id=login_id, user_id=user["user_id"])
        return user

    def _handle_login_failure(self, user_id: int, current_fail_count: int, request_id: str, login_id: str) -> None:
        """로그인 실패 처리 — 실패 횟수 증가 + 잠금 정책"""
        new_count = current_fail_count + 1
        locked_until = None

        if new_count >= settings.login_max_fail_count:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.login_lock_minutes)
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "계정 잠금 처리", login_id=login_id, fail_count=new_count, lock_min=settings.login_lock_minutes)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("UPDATE tb_user SET login_fail_count = %s, locked_until = %s WHERE user_id = %s", (new_count, locked_until, user_id))

    def create_session(self, user_id: int, ip: str, user_agent: str, request_id: str = "") -> TokenResponse:
        """세션 생성 — 권한 조회 + tb_user_session INSERT + 토큰 발급"""
        user_info = self.get_user_with_permissions(user_id, request_id)

        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)

        # JWT 토큰 데이터 구성
        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "scope_type": user_info["scope_type"],
            "roles": user_info["roles"],
            "role_names": user_info["role_names"],
            "permissions": user_info["permissions"],
            "is_superuser": user_info["is_superuser"],
        }
        access_token = create_access_token(token_data)

        refresh_data = {"sub": str(user_id), "session_id": session_id}
        refresh_token = create_refresh_token(refresh_data)

        # DB 세션 저장
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tb_user_session (session_id, user_id, refresh_token, ip_address, user_agent, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_id, refresh_token, ip, user_agent[:500] if user_agent else None, expires_at),
            )

        log_step(logger, request_id, "AUTH", "2", "SESSION", "세션 생성", user_id=user_id, session_id=session_id[:8])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=user_id,
                login_id=user_info["login_id"],
                display_name=user_info["display_name"],
                tenant_id=user_info["tenant_id"],
                scope_type=user_info["scope_type"],
                roles=user_info["roles"],
                role_names=user_info["role_names"],
                permissions=user_info["permissions"],
            ),
        )

    def refresh_access_token(self, refresh_token: str, request_id: str = "") -> TokenResponse:
        """Access Token 갱신 — Refresh Token 검증 + 최신 권한 로드"""
        # 1. JWT 검증
        payload = verify_token(refresh_token)
        if payload.token_type != "refresh":
            raise APIException(ErrorCode.UNAUTHORIZED, "Refresh Token이 필요합니다")

        session_id = payload.session_id
        if not session_id:
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 Refresh Token입니다")

        # 2. DB에서 세션 확인
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, expires_at FROM tb_user_session WHERE session_id = %s AND refresh_token = %s",
                (session_id, refresh_token),
            )
            session = cur.fetchone()

        if not session:
            log_step(logger, request_id, "AUTH", "3", "REFRESH", "세션 없음 또는 토큰 불일치", session_id=session_id[:8] if session_id else "none")
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 세션입니다")

        # 3. 세션 만료 확인
        if datetime.now(timezone.utc) > session["expires_at"]:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM tb_user_session WHERE session_id = %s", (session_id,))
            raise APIException(ErrorCode.SESSION_EXPIRED, "세션이 만료되었습니다. 다시 로그인해주세요")

        # 4. 최신 권한으로 Access Token 재생성
        user_id = session["user_id"]
        user_info = self.get_user_with_permissions(user_id, request_id)

        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "scope_type": user_info["scope_type"],
            "roles": user_info["roles"],
            "role_names": user_info["role_names"],
            "permissions": user_info["permissions"],
            "is_superuser": user_info["is_superuser"],
        }
        new_access_token = create_access_token(token_data)

        log_step(logger, request_id, "AUTH", "3", "REFRESH", "토큰 갱신 완료", user_id=user_id, session_id=session_id[:8])

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=user_id,
                login_id=user_info["login_id"],
                display_name=user_info["display_name"],
                tenant_id=user_info["tenant_id"],
                scope_type=user_info["scope_type"],
                roles=user_info["roles"],
                role_names=user_info["role_names"],
                permissions=user_info["permissions"],
            ),
        )

    def logout(self, user_id: int, request_id: str = "") -> bool:
        """로그아웃 — 해당 사용자의 모든 세션 삭제"""
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_session WHERE user_id = %s", (user_id,))
            deleted = cur.rowcount > 0

        log_step(logger, request_id, "AUTH", "4", "LOGOUT", "로그아웃", user_id=user_id, deleted=deleted)
        return deleted

    def get_user_with_permissions(self, user_id: int, request_id: str = "") -> Dict[str, Any]:
        """사용자 정보 + 역할 + 권한 일괄 조회"""
        # 1. 사용자 기본 정보
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, login_id, email, display_name, tenant_id, is_superuser, is_active "
                "FROM tb_user WHERE user_id = %s",
                (user_id,),
            )
            user_row = cur.fetchone()

        if not user_row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(user_row)
        if not user["is_active"]:
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 2. 역할 + 권한 조회
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT DISTINCT r.role_code, r.role_name, r.scope_type, p.permission_code "
                "FROM tb_user_role ur "
                "JOIN tb_role r ON ur.role_id = r.role_id "
                "LEFT JOIN tb_role_permission rp ON r.role_id = rp.role_id "
                "LEFT JOIN tb_permission p ON rp.permission_id = p.permission_id "
                "WHERE ur.user_id = %s",
                (user_id,),
            )
            rows = cur.fetchall()

        roles = set()
        role_names = set()
        permissions = set()
        max_scope = "USER"

        for row in rows:
            if row["role_code"]:
                roles.add(row["role_code"])
            if row["role_name"]:
                role_names.add(row["role_name"])
            if row["permission_code"]:
                permissions.add(row["permission_code"])
            row_scope = row["scope_type"] or "USER"
            if _SCOPE_PRIORITY.get(row_scope, 0) > _SCOPE_PRIORITY.get(max_scope, 0):
                max_scope = row_scope

        user["roles"] = sorted(roles)
        user["role_names"] = sorted(role_names)
        user["permissions"] = sorted(permissions)
        user["scope_type"] = max_scope

        log_step(logger, request_id, "AUTH", "2", "PERMISSION", "권한 조회 완료", user_id=user_id, roles=len(roles), perms=len(permissions), scope=max_scope)
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str, request_id: str = "") -> bool:
        """비밀번호 변경"""
        # 1. 현재 비밀번호 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT password_hash FROM tb_user WHERE user_id = %s", (user_id,))
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        if not verify_password(current_password, row["password_hash"]):
            raise APIException(ErrorCode.UNAUTHORIZED, "현재 비밀번호가 올바르지 않습니다")

        # 2. 새 비밀번호 해시 + 저장
        new_hash = hash_password(new_password)
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("UPDATE tb_user SET password_hash = %s, updated_at = NOW() WHERE user_id = %s", (new_hash, user_id))

        log_step(logger, request_id, "AUTH", "5", "PASSWORD", "비밀번호 변경 완료", user_id=user_id)
        return True


# 싱글톤 인스턴스
auth_service = AuthService()
