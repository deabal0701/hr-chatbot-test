"""사용자 관리 서비스

위치: app/api/services/user_service.py
사용자 CRUD + scope 기반 접근 제한 비즈니스 로직
"""
import json
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.password import hash_password
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class UserService:
    """사용자 관리 비즈니스 로직"""

    def _check_scope_access(self, target_tenant_id: Optional[int], current_user: UserContext) -> None:
        """scope_type에 따른 접근 범위 검증"""
        if current_user.is_global:
            return
        if current_user.scope_type == "TENANT":
            if target_tenant_id != current_user.tenant_id:
                raise APIException(ErrorCode.FORBIDDEN, "다른 테넌트의 데이터에 접근할 수 없습니다")
            return
        raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")

    def list_users(self, current_user: UserContext, request_id: str = "", limit: int = 20, offset: int = 0, tenant_id_filter: Optional[int] = None, is_active_filter: Optional[bool] = None) -> Dict[str, Any]:
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

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with db_manager.get_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) as cnt FROM tb_user u {where}", params)
            total = cur.fetchone()["cnt"]

            cur.execute(
                f"SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                f"t.tenant_name, u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at "
                f"FROM tb_user u LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
                f"{where} ORDER BY u.created_at DESC LIMIT %s OFFSET %s",
                params + [limit, offset],
            )
            rows = cur.fetchall()

        items = []
        for row in rows:
            user = dict(row)
            user["roles"] = self._get_user_roles(user["user_id"])
            items.append(user)

        log_step(logger, request_id, "USER", "1", "LIST", "사용자 목록 조회", total=total, scope=current_user.scope_type)
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_user(self, user_id: int, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                "t.tenant_name, u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at "
                "FROM tb_user u LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id WHERE u.user_id = %s",
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(row)

        # 본인이 아니면 scope 검증
        if current_user.user_id != user_id:
            self._check_scope_access(user["tenant_id"], current_user)

        user["roles"] = self._get_user_roles(user_id)
        log_step(logger, request_id, "USER", "2", "GET", "사용자 상세 조회", user_id=user_id)
        return user

    def create_user(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 생성"""
        # TENANT scope → 자기 테넌트로 강제
        tenant_id = data.get("tenant_id")
        if current_user.scope_type == "TENANT":
            tenant_id = current_user.tenant_id

        password_hashed = hash_password(data["password"])

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id",
                    (data["login_id"], data["email"], password_hashed, data.get("display_name"), tenant_id, data.get("is_active", True)),
                )
                new_user_id = cur.fetchone()["user_id"]

                # 역할 할당
                role_ids = data.get("role_ids", [])
                for role_id in role_ids:
                    cur.execute(
                        "INSERT INTO tb_user_role (user_id, role_id, tenant_id, granted_by) VALUES (%s, %s, %s, %s)",
                        (new_user_id, role_id, tenant_id, current_user.user_id),
                    )
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 로그인 ID 또는 이메일입니다")
            raise

        log_step(logger, request_id, "USER", "3", "CREATE", "사용자 생성", user_id=new_user_id, login_id=data["login_id"])
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

        # 동적 UPDATE
        fields = []
        params: list = []
        for key in ("email", "display_name", "tenant_id", "is_active"):
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

    def assign_roles(self, user_id: int, role_ids: List[int], current_user: UserContext, request_id: str = "") -> List[Dict[str, Any]]:
        """역할 할당 (GLOBAL만 가능, replace 방식)"""
        if not current_user.is_global:
            raise APIException(ErrorCode.FORBIDDEN, "역할 할당은 GLOBAL 권한이 필요합니다")

        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
            user = cur.fetchone()

        if not user:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        # role_ids 유효성 검사
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id FROM tb_role WHERE role_id = ANY(%s)", (role_ids,))
            valid_ids = {row["role_id"] for row in cur.fetchall()}

        invalid_ids = set(role_ids) - valid_ids
        if invalid_ids:
            raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 역할 ID: {sorted(invalid_ids)}")

        # replace 방식: 삭제 후 재할당
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_role WHERE user_id = %s", (user_id,))
            for role_id in role_ids:
                cur.execute(
                    "INSERT INTO tb_user_role (user_id, role_id, tenant_id, granted_by) VALUES (%s, %s, %s, %s)",
                    (user_id, role_id, user["tenant_id"], current_user.user_id),
                )

        log_step(logger, request_id, "USER", "6", "ASSIGN_ROLES", "역할 할당", user_id=user_id, roles=len(role_ids))
        return self._get_user_roles(user_id)

    def get_user_permissions(self, user_id: int, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 권한 조회"""
        from app.api.services.auth_service import auth_service
        # 본인이 아니면 scope 검증
        if current_user.user_id != user_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
                row = cur.fetchone()
            if not row:
                raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")
            self._check_scope_access(row["tenant_id"], current_user)

        return auth_service.get_user_with_permissions(user_id, request_id)

    def _get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 역할 목록 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT r.role_id, r.role_code, r.role_name, r.scope_type "
                "FROM tb_user_role ur JOIN tb_role r ON ur.role_id = r.role_id "
                "WHERE ur.user_id = %s ORDER BY r.sort_order",
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]


# 싱글톤 인스턴스
user_service = UserService()
