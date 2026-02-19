"""역할 관리 서비스 (v2.0 - 메뉴 기반)

위치: app/api/services/role_service.py
역할 CRUD 비즈니스 로직 (v2.0: 역할-권한 할당 제거, tb_user.role_id 직접 참조)
"""
from typing import Any, Dict, List

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode, raise_on_unique_violation
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class RoleService:
    """역할 관리 비즈니스 로직 (v2.0)"""

    def list_roles(self, request_id: str = "") -> Dict[str, Any]:
        """역할 목록 조회 (사용자 수 포함)"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT r.role_id, r.role_code, r.role_name, r.description, "
                "r.landing_page, r.is_system, r.sort_order, r.created_at, r.updated_at, "
                "(SELECT COUNT(*) FROM tb_user u WHERE u.role_id = r.role_id) as user_count "
                "FROM tb_role r ORDER BY r.sort_order, r.role_id"
            )
            rows = cur.fetchall()

        items = [dict(row) for row in rows]
        log_step(logger, request_id, "ROLE", "1", "LIST", "역할 목록 조회", total=len(items))
        return {"total": len(items), "items": items}

    def get_role(self, role_id: int, request_id: str = "") -> Dict[str, Any]:
        """역할 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT r.role_id, r.role_code, r.role_name, r.description, "
                "r.landing_page, r.is_system, r.sort_order, r.created_at, r.updated_at, "
                "(SELECT COUNT(*) FROM tb_user u WHERE u.role_id = r.role_id) as user_count "
                "FROM tb_role r WHERE r.role_id = %s",
                (role_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        role = dict(row)
        log_step(logger, request_id, "ROLE", "2", "GET", "역할 상세 조회", role_id=role_id)
        return role

    def create_role(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """역할 생성"""
        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_role (role_code, role_name, description, landing_page, sort_order) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING role_id",
                    (data["role_code"], data["role_name"], data.get("description"), data.get("landing_page", "/chat"), data.get("sort_order", 0)),
                )
                new_role_id = cur.fetchone()["role_id"]
        except Exception as e:
            raise_on_unique_violation(e, "이미 존재하는 역할 코드입니다")

        log_step(logger, request_id, "ROLE", "3", "CREATE", "역할 생성", role_id=new_role_id, role_code=data["role_code"])
        return self.get_role(new_role_id, request_id)

    def update_role(self, role_id: int, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """역할 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_id, is_system, role_code FROM tb_role WHERE role_id = %s", (role_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

        fields = []
        params: list = []
        for key in ("role_name", "description", "landing_page"):
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

        # 사용 중인 역할 확인 (tb_user.role_id 직접 참조)
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE role_id = %s", (role_id,))
            if cur.fetchone()["cnt"] > 0:
                raise APIException(ErrorCode.BAD_REQUEST, "사용 중인 역할은 삭제할 수 없습니다. 먼저 사용자의 역할을 변경하세요")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_role WHERE role_id = %s", (role_id,))

        log_step(logger, request_id, "ROLE", "5", "DELETE", "역할 삭제", role_id=role_id, role_code=existing["role_code"])
        return True

    # 역할 코드별 기본 메뉴 템플릿 (tb_menu.menu_code 기준)
    _DEFAULT_MENUS: Dict[str, Dict[str, dict]] = {
        "GLOBAL": {
            "__all_pages__": {"can_create": True, "can_read": True, "can_update": True, "can_delete": True, "can_export": True},
        },
        "TENANT": {
            "DASHBOARD":   {"can_read": True},
            "AI_SEARCH":   {"can_create": True, "can_read": True},
            "DOC_MGMT":    {"can_create": True, "can_read": True, "can_update": True, "can_delete": True, "can_export": True},
            "SEARCH_HIST": {"can_read": True, "can_export": True},
            "USER_MGMT":   {"can_create": True, "can_read": True, "can_update": True},
            "AI_CHAT":     {"can_create": True, "can_read": True},
        },
        "USER": {
            "AI_CHAT": {"can_create": True, "can_read": True},
        },
    }

    def get_default_menus(self, role_code: str, request_id: str = "") -> List[dict]:
        """역할별 기본 메뉴 권한 목록 (사용자 생성 시 자동 체크용, 트리 순서)"""
        template = self._DEFAULT_MENUS.get(role_code, {})

        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT menu_id, menu_code, menu_name, menu_type, menu_path, "
                "icon, depth, sort_order, parent_menu_id "
                "FROM tb_menu WHERE is_active = true "
                "ORDER BY depth, sort_order"
            )
            menus = [dict(row) for row in cur.fetchall()]

        ordered = self._flatten_menu_tree(menus)

        result = []
        for menu in ordered:
            is_dir = menu["menu_type"] == "DIRECTORY"
            defaults = {} if is_dir else template.get(menu["menu_code"], template.get("__all_pages__", {}))
            result.append({
                **menu,
                "can_create": defaults.get("can_create", False),
                "can_read":   defaults.get("can_read", False),
                "can_update": defaults.get("can_update", False),
                "can_delete": defaults.get("can_delete", False),
                "can_export": defaults.get("can_export", False),
                "checked":    bool(defaults),
                "is_directory": is_dir,
            })

        log_step(logger, request_id, "ROLE", "6", "DEFAULT_MENUS", "기본 메뉴 조회", role_code=role_code, total=len(result))
        return {"items": result, "total": len(result)}

    def _flatten_menu_tree(self, menus: List[dict]) -> List[dict]:
        """메뉴를 depth-first 순서로 펼침 (최상위 DIRECTORY 제외)"""
        by_parent: Dict[Any, List[dict]] = {}
        for m in menus:
            by_parent.setdefault(m.get("parent_menu_id"), []).append(m)

        result: List[dict] = []

        def walk(parent_id):
            children = sorted(by_parent.get(parent_id, []), key=lambda x: x["sort_order"])
            for child in children:
                if child["menu_type"] == "DIRECTORY" and child["depth"] == 0:
                    walk(child["menu_id"])
                else:
                    result.append(child)
                    walk(child["menu_id"])

        walk(None)
        return result


# 싱글톤 인스턴스
role_service = RoleService()
