"""역할 관리 서비스

위치: app/api/services/role_service.py
역할 CRUD + 권한 할당 비즈니스 로직
"""
from typing import Any, Dict, List

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class RoleService:
    """역할 관리 비즈니스 로직"""

    def list_roles(self, request_id: str = "") -> Dict[str, Any]:
        """역할 목록 조회 (권한 포함)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id, role_code, role_name, description, scope_type, is_system, sort_order, created_at FROM tb_role ORDER BY sort_order, role_id")
            rows = cur.fetchall()

        items = []
        for row in rows:
            role = dict(row)
            role["permissions"] = self._get_role_permissions(role["role_id"])
            items.append(role)

        log_step(logger, request_id, "ROLE", "1", "LIST", "역할 목록 조회", total=len(items))
        return {"total": len(items), "items": items}

    def get_role(self, role_id: int, request_id: str = "") -> Dict[str, Any]:
        """역할 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT r.role_id, r.role_code, r.role_name, r.description, r.scope_type, r.is_system, r.sort_order, r.created_at, "
                "(SELECT COUNT(*) FROM tb_user_role ur WHERE ur.role_id = r.role_id) as user_count "
                "FROM tb_role r WHERE r.role_id = %s",
                (role_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        role = dict(row)
        role["permissions"] = self._get_role_permissions(role_id)
        log_step(logger, request_id, "ROLE", "2", "GET", "역할 상세 조회", role_id=role_id)
        return role

    def create_role(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """역할 생성"""
        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_role (role_code, role_name, description, scope_type, sort_order) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING role_id",
                    (data["role_code"], data["role_name"], data.get("description"), data["scope_type"], data.get("sort_order", 0)),
                )
                new_role_id = cur.fetchone()["role_id"]

                # 권한 할당
                permission_ids = data.get("permission_ids", [])
                for pid in permission_ids:
                    cur.execute("INSERT INTO tb_role_permission (role_id, permission_id) VALUES (%s, %s)", (new_role_id, pid))
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 역할 코드입니다")
            raise

        log_step(logger, request_id, "ROLE", "3", "CREATE", "역할 생성", role_id=new_role_id, role_code=data["role_code"])
        return self.get_role(new_role_id, request_id)

    def update_role(self, role_id: int, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """역할 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id, is_system, role_code, scope_type FROM tb_role WHERE role_id = %s", (role_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        # 시스템 역할: scope_type 변경 불가
        if existing["is_system"] and "scope_type" in data and data["scope_type"] is not None:
            if data["scope_type"] != existing["scope_type"]:
                raise APIException(ErrorCode.BAD_REQUEST, "시스템 역할의 scope_type은 변경할 수 없습니다")

        fields = []
        params: list = []
        for key in ("role_name", "description", "scope_type"):
            if key in data and data[key] is not None:
                fields.append(f"{key} = %s")
                params.append(data[key])

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(role_id)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_role SET {', '.join(fields)} WHERE role_id = %s", params)

        log_step(logger, request_id, "ROLE", "4", "UPDATE", "역할 수정", role_id=role_id)
        return self.get_role(role_id, request_id)

    def delete_role(self, role_id: int, current_user: UserContext, request_id: str = "") -> bool:
        """역할 삭제"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id, is_system, role_code FROM tb_role WHERE role_id = %s", (role_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        if existing["is_system"]:
            raise APIException(ErrorCode.BAD_REQUEST, "시스템 기본 역할은 삭제할 수 없습니다")

        # 사용 중 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user_role WHERE role_id = %s", (role_id,))
            if cur.fetchone()["cnt"] > 0:
                raise APIException(ErrorCode.BAD_REQUEST, "사용 중인 역할은 삭제할 수 없습니다. 먼저 사용자에게서 역할을 해제하세요")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_role WHERE role_id = %s", (role_id,))

        log_step(logger, request_id, "ROLE", "5", "DELETE", "역할 삭제", role_id=role_id, role_code=existing["role_code"])
        return True

    def assign_permissions(self, role_id: int, permission_ids: List[int], current_user: UserContext, request_id: str = "") -> List[Dict[str, Any]]:
        """역할에 권한 할당 (replace 방식)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id FROM tb_role WHERE role_id = %s", (role_id,))
            if not cur.fetchone():
                raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        # permission_ids 유효성
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT permission_id FROM tb_permission WHERE permission_id = ANY(%s)", (permission_ids,))
            valid_ids = {row["permission_id"] for row in cur.fetchall()}

        invalid_ids = set(permission_ids) - valid_ids
        if invalid_ids:
            raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 권한 ID: {sorted(invalid_ids)}")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_role_permission WHERE role_id = %s", (role_id,))
            for pid in permission_ids:
                cur.execute("INSERT INTO tb_role_permission (role_id, permission_id) VALUES (%s, %s)", (role_id, pid))

        log_step(logger, request_id, "ROLE", "6", "ASSIGN_PERMS", "권한 할당", role_id=role_id, perms=len(permission_ids))
        return self._get_role_permissions(role_id)

    def list_permissions(self, request_id: str = "") -> List[Dict[str, Any]]:
        """사용 가능한 전체 권한 목록"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT permission_id, permission_code, permission_name, category, description, is_system FROM tb_permission ORDER BY category, permission_id")
            return [dict(row) for row in cur.fetchall()]

    def _get_role_permissions(self, role_id: int) -> List[Dict[str, Any]]:
        """역할의 권한 목록 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT p.permission_id, p.permission_code, p.permission_name, p.category "
                "FROM tb_role_permission rp JOIN tb_permission p ON rp.permission_id = p.permission_id "
                "WHERE rp.role_id = %s ORDER BY p.category, p.permission_id",
                (role_id,),
            )
            return [dict(row) for row in cur.fetchall()]


# 싱글톤 인스턴스
role_service = RoleService()
