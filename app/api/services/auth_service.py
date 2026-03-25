"""인증 서비스 (v2.0 - 메뉴 기반)

위치: app/api/services/auth_service.py
로그인, 세션 관리, 토큰 갱신, 비밀번호 변경 비즈니스 로직
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.database.connection import db_manager
from app.core.errors.handlers import APIException
from app.core.errors.error_codes import ErrorCode
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security.password import hash_password, verify_password
from app.core.security.sso import verify_sso_token
from app.models.auth import MenuPermission, SSOTokenPayload, TokenResponse, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


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

        # JWT 토큰 데이터 구성 (v4.0: scope_level 기반 데이터 범위)
        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "dept_id": user_info.get("dept_id"),
            "role_code": user_info["role_code"],
            "scope_level": user_info.get("scope_level", 3),
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
                role_code=user_info["role_code"],
                role_name=user_info.get("role_name", ""),
                landing_page=user_info["landing_page"],
                menus=user_info["menus"],
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

        # 4. 최신 권한으로 Access Token + Refresh Token 재생성 (로테이션)
        user_id = session["user_id"]
        user_info = self.get_user_with_permissions(user_id, request_id)

        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "dept_id": user_info.get("dept_id"),
            "role_code": user_info["role_code"],
            "scope_level": user_info.get("scope_level", 3),
            "is_superuser": user_info["is_superuser"],
        }
        new_access_token = create_access_token(token_data)

        # Refresh Token 로테이션: 새 토큰 발급 + DB 교체 (기존 토큰 즉시 무효화)
        new_refresh_token = create_refresh_token({"sub": str(user_id), "session_id": session_id})
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("UPDATE tb_user_session SET refresh_token = %s WHERE session_id = %s", (new_refresh_token, session_id))

        log_step(logger, request_id, "AUTH", "3", "REFRESH", "토큰 갱신 완료 (로테이션)", user_id=user_id, session_id=session_id[:8])

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=user_id,
                login_id=user_info["login_id"],
                display_name=user_info["display_name"],
                tenant_id=user_info["tenant_id"],
                role_code=user_info["role_code"],
                role_name=user_info.get("role_name", ""),
                landing_page=user_info["landing_page"],
                menus=user_info["menus"],
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
        """사용자 정보 + 역할 + 메뉴 권한 일괄 조회 (v2.0)"""
        # 1. 사용자 + 역할 정보 (tb_user.role_id → tb_role 직접 JOIN)
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                "u.dept_id, u.is_superuser, u.is_active, "
                "r.role_code, r.role_name, "
                "COALESCE(u.landing_page, r.landing_page) AS landing_page, r.scope_level "
                "FROM tb_user u "
                "JOIN tb_role r ON r.role_id = u.role_id "
                "WHERE u.user_id = %s",
                (user_id,),
            )
            user_row = cur.fetchone()

        if not user_row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(user_row)
        if not user["is_active"]:
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 2. 메뉴 권한 조회 (할당된 메뉴 + DIRECTORY 조상 자동 포함)
        # 재귀 CTE로 할당 메뉴의 부모 DIRECTORY 체인을 자동 포함하여
        # 사이드바에서 트리 구조를 정확히 빌드할 수 있도록 함
        with db_manager.get_cursor() as cur:
            cur.execute(
                "WITH RECURSIVE "
                "assigned AS ("
                "  SELECT m.menu_id FROM tb_user_menu um "
                "  JOIN tb_menu m ON m.menu_id = um.menu_id "
                "  WHERE um.user_id = %s AND m.is_active = true"
                "), "
                "parent_chain AS ("
                "  SELECT DISTINCT m.parent_menu_id AS menu_id "
                "  FROM assigned a JOIN tb_menu m ON m.menu_id = a.menu_id "
                "  WHERE m.parent_menu_id IS NOT NULL"
                "  UNION "
                "  SELECT m.parent_menu_id "
                "  FROM parent_chain pc JOIN tb_menu m ON m.menu_id = pc.menu_id "
                "  WHERE m.parent_menu_id IS NOT NULL"
                "), "
                "all_ids AS ("
                "  SELECT menu_id FROM assigned "
                "  UNION "
                "  SELECT menu_id FROM parent_chain WHERE menu_id IS NOT NULL"
                ") "
                "SELECT m.menu_code, m.menu_name, m.menu_path, m.menu_type, m.icon, "
                "m.depth, m.sort_order, pm.menu_code AS parent_menu_code, "
                "COALESCE(um.can_create, false) AS can_create, "
                "COALESCE(um.can_read, false) AS can_read, "
                "COALESCE(um.can_update, false) AS can_update, "
                "COALESCE(um.can_delete, false) AS can_delete, "
                "COALESCE(um.can_export, false) AS can_export "
                "FROM all_ids ai "
                "JOIN tb_menu m ON m.menu_id = ai.menu_id "
                "LEFT JOIN tb_user_menu um ON um.menu_id = m.menu_id AND um.user_id = %s "
                "LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id "
                "WHERE m.is_active = true "
                "ORDER BY m.depth, m.sort_order",
                (user_id, user_id),
            )
            menu_rows = cur.fetchall()

        menus: List[MenuPermission] = []
        for row in menu_rows:
            menus.append(MenuPermission(
                menu_code=row["menu_code"],
                menu_name=row["menu_name"],
                menu_path=row["menu_path"],
                menu_type=row["menu_type"],
                icon=row["icon"],
                parent_menu_code=row["parent_menu_code"],
                depth=row["depth"],
                sort_order=row["sort_order"],
                can_create=row["can_create"],
                can_read=row["can_read"],
                can_update=row["can_update"],
                can_delete=row["can_delete"],
                can_export=row["can_export"],
            ))

        user["menus"] = menus

        log_step(logger, request_id, "AUTH", "2", "PERMISSION", "권한 조회 완료", user_id=user_id, role=user["role_code"], menus=len(menus))
        return user

    def sso_authenticate(self, sso_token: str, request_id: str = "") -> Dict[str, Any]:
        """SSO 토큰 검증 + 사용자 조회/자동 생성 + 정보 동기화"""
        log_step(logger, request_id, "SSO", "1", "VERIFY", "SSO 토큰 검증 시작")

        if not settings.sso_enabled:
            raise APIException(ErrorCode.SSO_DISABLED, "SSO 로그인이 비활성화되어 있습니다")

        # 1. SSO 토큰 검증 (RS256)
        payload: SSOTokenPayload = verify_sso_token(sso_token)
        log_step(logger, request_id, "SSO", "2", "PAYLOAD", "토큰 검증 완료", sub=payload.sub, iss=payload.iss)

        # 2. 사용자 조회: sso_provider + sso_external_id 우선, login_id fallback
        user = self._find_sso_user(payload, request_id)

        if user:
            # 3A. 기존 사용자 → 정보 동기화 (display_name, email)
            self._sync_sso_user_info(user, payload, request_id)
        else:
            # 3B. 사용자 미존재 → 자동 생성 또는 에러
            if not settings.sso_auto_create_user:
                raise APIException(ErrorCode.SSO_USER_NOT_FOUND, f"SSO 사용자를 찾을 수 없습니다 (sub={payload.sub})")
            user = self._create_sso_user(payload, request_id)

        # 4. 비활성 계정 체크
        if not user["is_active"]:
            log_step(logger, request_id, "SSO", "3", "LOGIN", "비활성 계정", login_id=user["login_id"])
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 5. SSO 메타데이터 업데이트 (sso_provider, sso_external_id, last_login_at)
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tb_user SET sso_provider = %s, sso_external_id = %s, "
                "last_login_at = NOW(), login_fail_count = 0, locked_until = NULL "
                "WHERE user_id = %s",
                (payload.iss, payload.sub, user["user_id"]),
            )

        log_step(logger, request_id, "SSO", "3", "LOGIN", "SSO 로그인 성공", login_id=user["login_id"], user_id=user["user_id"])
        return user

    def _find_sso_user(self, payload: SSOTokenPayload, request_id: str) -> Optional[Dict[str, Any]]:
        """SSO 사용자 조회: 1순위 sso_provider+sso_external_id, 2순위 login_id=sub"""
        _cols = "user_id, login_id, email, is_active, is_superuser, display_name, tenant_id"
        with db_manager.get_cursor() as cur:
            # 1순위: sso_provider + sso_external_id
            cur.execute(f"SELECT {_cols} FROM tb_user WHERE sso_provider = %s AND sso_external_id = %s", (payload.iss, payload.sub))
            row = cur.fetchone()
            if row:
                log_step(logger, request_id, "SSO", "2", "LOOKUP", "sso_external_id로 사용자 발견", user_id=row["user_id"])
                return dict(row)

            # 2순위: login_id = sub
            cur.execute(f"SELECT {_cols} FROM tb_user WHERE login_id = %s", (payload.sub,))
            row = cur.fetchone()
            if row:
                log_step(logger, request_id, "SSO", "2", "LOOKUP", "login_id로 사용자 발견", user_id=row["user_id"])
                return dict(row)

        log_step(logger, request_id, "SSO", "2", "LOOKUP", "사용자 없음", sub=payload.sub)
        return None

    def _create_sso_user(self, payload: SSOTokenPayload, request_id: str) -> Dict[str, Any]:
        """SSO 사용자 JIT(Just-In-Time) 자동 생성"""
        # 1. 필수 필드 검증
        if not payload.email:
            raise APIException(ErrorCode.BAD_REQUEST, "SSO 자동 생성 시 email은 필수입니다")
        if not payload.tenant_code:
            raise APIException(ErrorCode.BAD_REQUEST, "SSO 자동 생성 시 tenant_code는 필수입니다")

        # 2. tenant_code → tenant_id
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT tenant_id FROM tb_tenant WHERE tenant_code = %s AND is_active = true", (payload.tenant_code,))
            tenant_row = cur.fetchone()
        if not tenant_row:
            raise APIException(ErrorCode.NOT_FOUND, f"테넌트를 찾을 수 없습니다: {payload.tenant_code}")
        tenant_id = tenant_row["tenant_id"]

        # 3. 기본 역할 조회 (sso_default_role)
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id FROM tb_role WHERE role_code = %s", (settings.sso_default_role,))
            role_row = cur.fetchone()
        if not role_row:
            raise APIException(ErrorCode.NOT_FOUND, f"기본 역할을 찾을 수 없습니다: {settings.sso_default_role}")
        role_id = role_row["role_id"]

        # 4. dept_code → dept_id (선택, 없으면 NULL)
        dept_id = None
        if payload.dept_code:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT dept_id FROM tb_department WHERE dept_code = %s AND tenant_id = %s", (payload.dept_code, tenant_id))
                dept_row = cur.fetchone()
            if dept_row:
                dept_id = dept_row["dept_id"]

        # 5. email 중복 체크
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id FROM tb_user WHERE email = %s", (payload.email,))
            if cur.fetchone():
                raise APIException(ErrorCode.DUPLICATE_ERROR, f"이미 사용 중인 이메일입니다: {payload.email}")

        # 6. 사용자 INSERT
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tb_user (login_id, email, password_hash, display_name, "
                "tenant_id, role_id, dept_id, is_active, is_superuser, "
                "sso_provider, sso_external_id, landing_page) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, true, false, %s, %s, %s) "
                "RETURNING user_id",
                (payload.sub, payload.email, "!SSO_USER!", payload.name,
                 tenant_id, role_id, dept_id,
                 payload.iss, payload.sub, "/chat"),
            )
            user_id = cur.fetchone()["user_id"]

        log_step(logger, request_id, "SSO", "2", "CREATE", "SSO 사용자 자동 생성", user_id=user_id, login_id=payload.sub, tenant_code=payload.tenant_code)

        # 6. USER 기본 메뉴 권한 할당 (AI_CHAT: can_create, can_read)
        self._assign_default_sso_menus(user_id, request_id)

        return {
            "user_id": user_id,
            "login_id": payload.sub,
            "email": payload.email,
            "display_name": payload.name,
            "tenant_id": tenant_id,
            "is_active": True,
            "is_superuser": False,
        }

    def _assign_default_sso_menus(self, user_id: int, request_id: str) -> None:
        """SSO 자동 생성 사용자에게 USER 기본 메뉴 권한 할당"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id FROM tb_menu WHERE menu_code = 'AI_CHAT' AND is_active = true")
            menu_row = cur.fetchone()

        if not menu_row:
            log_step(logger, request_id, "SSO", "2", "MENU", "AI_CHAT 메뉴 없음 — 기본 메뉴 할당 건너뜀")
            return

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export) "
                "VALUES (%s, %s, true, true, false, false, false) "
                "ON CONFLICT (user_id, menu_id) DO NOTHING",
                (user_id, menu_row["menu_id"]),
            )

        log_step(logger, request_id, "SSO", "2", "MENU", "기본 메뉴 권한 할당", user_id=user_id, menu="AI_CHAT")

    def _sync_sso_user_info(self, user: Dict[str, Any], payload: SSOTokenPayload, request_id: str) -> None:
        """기존 사용자의 SSO 페이로드 정보 동기화 (display_name, email)"""
        updates = []
        params = []

        if payload.name and payload.name != user.get("display_name"):
            updates.append("display_name = %s")
            params.append(payload.name)
        if payload.email and payload.email != user.get("email"):
            # email 중복 체크 (다른 사용자가 이미 사용 중인 email이면 동기화 건너뜀)
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT user_id FROM tb_user WHERE email = %s AND user_id != %s", (payload.email, user["user_id"]))
                if cur.fetchone():
                    log_step(logger, request_id, "SSO", "2", "SYNC", "email 중복으로 동기화 건너뜀", user_id=user["user_id"], email=payload.email)
                else:
                    updates.append("email = %s")
                    params.append(payload.email)

        if not updates:
            return

        params.append(user["user_id"])
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_user SET {', '.join(updates)}, updated_at = NOW() WHERE user_id = %s", params)

        log_step(logger, request_id, "SSO", "2", "SYNC", "사용자 정보 동기화", user_id=user["user_id"], fields=", ".join(u.split(" =")[0] for u in updates))

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
