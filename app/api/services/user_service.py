"""사용자 관리 서비스 (v2.0 - 메뉴 기반)

위치: app/api/services/user_service.py
사용자 CRUD + scope 기반 접근 제한 + 메뉴 권한 관리
"""
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.password import hash_password
from app.models.auth import UserContext
from app.models.menu import UserMenuPermission
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class UserService:
    """사용자 관리 비즈니스 로직 (v2.0)"""

    def _check_scope_access(self, target_tenant_id: Optional[int], current_user: UserContext) -> None:
        """scope_type에 따른 접근 범위 검증"""
        if current_user.is_global:
            return
        if current_user.scope_type == "TENANT":
            if target_tenant_id != current_user.tenant_id:
                raise APIException(ErrorCode.FORBIDDEN, "다른 테넌트의 데이터에 접근할 수 없습니다")
            return
        raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")

    def list_users(self, current_user: UserContext, request_id: str = "", limit: int = 20, offset: int = 0, tenant_id_filter: Optional[int] = None, is_active_filter: Optional[bool] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
        """사용자 목록 조회 (scope 제한 적용)"""
        conditions = []
        params: list = []

        # scope 제한
        if current_user.scope_type == "TENANT":
            conditions.append("u.tenant_id = %s")
            params.append(current_user.tenant_id)
        elif not current_user.is_global:
            conditions.append("u.user_id = %s")
            params.append(current_user.user_id)

        # 필터
        if tenant_id_filter is not None and current_user.is_global:
            conditions.append("u.tenant_id = %s")
            params.append(tenant_id_filter)
        if is_active_filter is not None:
            conditions.append("u.is_active = %s")
            params.append(is_active_filter)
        if keyword and keyword.strip():
            conditions.append("(u.display_name ILIKE %s OR u.login_id ILIKE %s)")
            like_val = f"%{keyword.strip()}%"
            params.extend([like_val, like_val])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with db_manager.get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as cnt FROM tb_user u {where}", params)
            total = cur.fetchone()["cnt"]

            cur.execute(
                f"SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                f"t.tenant_name, u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at, "
                f"r.role_id, r.role_code, r.role_name, r.scope_type, r.landing_page, "
                f"(SELECT COUNT(*) FROM tb_user_menu um WHERE um.user_id = u.user_id) as menu_count "
                f"FROM tb_user u "
                f"LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
                f"LEFT JOIN tb_role r ON u.role_id = r.role_id "
                f"{where} ORDER BY u.created_at DESC LIMIT %s OFFSET %s",
                params + [limit, offset],
            )
            rows = cur.fetchall()

        items = []
        for row in rows:
            user = dict(row)
            # 역할을 단일 객체로 포맷
            user["role"] = {
                "role_id": user.pop("role_id"),
                "role_code": user.pop("role_code"),
                "role_name": user.pop("role_name"),
                "scope_type": user.pop("scope_type"),
                "landing_page": user.pop("landing_page"),
            } if user.get("role_id") else None
            items.append(user)

        log_step(logger, request_id, "USER", "1", "LIST", "사용자 목록 조회", total=total, scope=current_user.scope_type)
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_user(self, user_id: int, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                "t.tenant_name, u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at, "
                "r.role_id, r.role_code, r.role_name, r.scope_type, r.landing_page, "
                "(SELECT COUNT(*) FROM tb_user_menu um WHERE um.user_id = u.user_id) as menu_count "
                "FROM tb_user u "
                "LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
                "LEFT JOIN tb_role r ON u.role_id = r.role_id "
                "WHERE u.user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(row)

        # 본인이 아니면 scope 검증
        if current_user.user_id != user_id:
            self._check_scope_access(user["tenant_id"], current_user)

        # 역할을 단일 객체로 포맷
        user["role"] = {
            "role_id": user.pop("role_id"),
            "role_code": user.pop("role_code"),
            "role_name": user.pop("role_name"),
            "scope_type": user.pop("scope_type"),
            "landing_page": user.pop("landing_page"),
        } if user.get("role_id") else None

        log_step(logger, request_id, "USER", "2", "GET", "사용자 상세 조회", user_id=user_id)
        return user

    def create_user(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 생성 (v2.0: role_id 단일 + 메뉴 권한)"""
        # TENANT scope → 자기 테넌트로 강제
        tenant_id = data.get("tenant_id")
        if current_user.scope_type == "TENANT":
            tenant_id = current_user.tenant_id

        password_hashed = hash_password(data["password"])
        role_id = data.get("role_id")

        # role_id 유효성 검사
        if role_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT role_id FROM tb_role WHERE role_id = %s", (role_id,))
                if not cur.fetchone():
                    raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 역할 ID: {role_id}")

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, role_id, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id",
                    (data["login_id"], data["email"], password_hashed, data.get("display_name"), tenant_id, role_id, data.get("is_active", True)),
                )
                new_user_id = cur.fetchone()["user_id"]

                # 메뉴 권한 할당
                menus = data.get("menus", [])
                for menu in menus:
                    menu_data = menu if isinstance(menu, dict) else menu.model_dump() if hasattr(menu, "model_dump") else dict(menu)
                    cur.execute(
                        "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (new_user_id, menu_data["menu_id"], menu_data.get("can_create", False), menu_data.get("can_read", True), menu_data.get("can_update", False), menu_data.get("can_delete", False), menu_data.get("can_export", False), current_user.user_id),
                    )
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 로그인 ID 또는 이메일입니다")
            raise

        log_step(logger, request_id, "USER", "3", "CREATE", "사용자 생성", user_id=new_user_id, login_id=data["login_id"], menus=len(menus))
        return self.get_user(new_user_id, current_user, request_id)

    def update_user(self, user_id: int, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, tenant_id, is_superuser FROM tb_user WHERE user_id = %s", (user_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        self._check_scope_access(existing["tenant_id"], current_user)

        # superuser 보호: 다른 관리자가 superuser 수정 불가
        if existing["is_superuser"] and current_user.user_id != user_id:
            raise APIException(ErrorCode.FORBIDDEN, "슈퍼유저는 본인만 수정할 수 있습니다")

        # role_id 유효성 검사
        if "role_id" in data and data["role_id"] is not None:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT role_id FROM tb_role WHERE role_id = %s", (data["role_id"],))
                if not cur.fetchone():
                    raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 역할 ID: {data['role_id']}")

        # 동적 UPDATE
        fields = []
        params: list = []
        for key in ("email", "display_name", "tenant_id", "role_id", "is_active"):
            if key in data and data[key] is not None:
                fields.append(f"{key} = %s")
                params.append(data[key])

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(user_id)

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(f"UPDATE tb_user SET {', '.join(fields)} WHERE user_id = %s", params)
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 이메일입니다")
            raise

        log_step(logger, request_id, "USER", "4", "UPDATE", "사용자 수정", user_id=user_id)
        return self.get_user(user_id, current_user, request_id)

    def delete_user(self, user_id: int, current_user: UserContext, request_id: str = "") -> bool:
        """사용자 삭제"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, tenant_id, is_superuser FROM tb_user WHERE user_id = %s", (user_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        self._check_scope_access(existing["tenant_id"], current_user)

        if existing["is_superuser"]:
            raise APIException(ErrorCode.BAD_REQUEST, "슈퍼유저는 삭제할 수 없습니다")
        if current_user.user_id == user_id:
            raise APIException(ErrorCode.BAD_REQUEST, "자기 자신은 삭제할 수 없습니다")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user WHERE user_id = %s", (user_id,))

        log_step(logger, request_id, "USER", "5", "DELETE", "사용자 삭제", user_id=user_id)
        return True

    def assign_menus(self, user_id: int, menus: List[UserMenuPermission], current_user: UserContext, request_id: str = "") -> List[Dict[str, Any]]:
        """사용자 메뉴 권한 할당 (replace 방식)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
            user = cur.fetchone()

        if not user:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        self._check_scope_access(user["tenant_id"], current_user)

        # menu_id 유효성 검사
        menu_ids = [m.menu_id for m in menus]
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id FROM tb_menu WHERE menu_id = ANY(%s) AND is_active = true", (menu_ids,))
            valid_ids = {row["menu_id"] for row in cur.fetchall()}

        invalid_ids = set(menu_ids) - valid_ids
        if invalid_ids:
            raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않거나 비활성 메뉴 ID: {sorted(invalid_ids)}")

        # replace 방식: 삭제 후 재할당
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_menu WHERE user_id = %s", (user_id,))
            for menu in menus:
                cur.execute(
                    "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, menu.menu_id, menu.can_create, menu.can_read, menu.can_update, menu.can_delete, menu.can_export, current_user.user_id),
                )

        log_step(logger, request_id, "USER", "6", "ASSIGN_MENUS", "메뉴 권한 할당", user_id=user_id, menus=len(menus))
        return self._get_user_menus(user_id)

    def get_user_menus(self, user_id: int, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 메뉴 권한 조회"""
        if current_user.user_id != user_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
            if not row:
                raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")
            self._check_scope_access(row["tenant_id"], current_user)

        menus = self._get_user_menus(user_id)
        log_step(logger, request_id, "USER", "7", "GET_MENUS", "메뉴 권한 조회", user_id=user_id, menus=len(menus))
        return {"user_id": user_id, "menus": menus}

    def _get_user_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 메뉴 권한 목록 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT m.menu_id, m.menu_code, m.menu_name, m.menu_type, m.menu_path, m.icon, m.depth, m.sort_order, "
                "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export, um.granted_at "
                "FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "WHERE um.user_id = %s AND m.is_active = true "
                "ORDER BY m.depth, m.sort_order",
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]


# 싱글톤 인스턴스
user_service = UserService()
