"""메뉴 관리 서비스

위치: app/api/services/menu_service.py
메뉴 트리 CRUD 비즈니스 로직
"""
from typing import Any, Dict, List

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class MenuService:
    """메뉴 관리 비즈니스 로직"""

    def get_menu_tree(self, request_id: str = "") -> dict:
        """전체 메뉴 트리 조회 (계층 구조)"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT menu_id, parent_menu_id, menu_code, menu_name, menu_type, "
                "menu_path, api_pattern, icon, sort_order, depth, is_active, "
                "description, created_at, updated_at "
                "FROM tb_menu ORDER BY depth, sort_order"
            )
            rows = [dict(row) for row in cur.fetchall()]

        menu_map = {row["menu_id"]: {**row, "children": []} for row in rows}
        root_items: List[dict] = []

        for row in rows:
            parent_id = row["parent_menu_id"]
            if parent_id and parent_id in menu_map:
                menu_map[parent_id]["children"].append(menu_map[row["menu_id"]])
            else:
                root_items.append(menu_map[row["menu_id"]])

        log_step(logger, request_id, "MENU", "1", "TREE", "메뉴 트리 조회", total=len(rows))
        return {"total": len(rows), "items": root_items}

    def get_menu(self, menu_id: int, request_id: str = "") -> dict:
        """메뉴 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT menu_id, parent_menu_id, menu_code, menu_name, menu_type, "
                "menu_path, api_pattern, icon, sort_order, depth, is_active, "
                "description, created_at, updated_at "
                "FROM tb_menu WHERE menu_id = %s",
                (menu_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "메뉴를 찾을 수 없습니다")

        log_step(logger, request_id, "MENU", "2", "GET", "메뉴 상세 조회", menu_id=menu_id)
        return dict(row)

    def create_menu(self, data: dict, current_user: UserContext, request_id: str = "") -> dict:
        """메뉴 생성"""
        parent_menu_id = data.get("parent_menu_id")
        depth = 0

        if parent_menu_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT depth FROM tb_menu WHERE menu_id = %s", (parent_menu_id,))
                parent = cur.fetchone()
            if not parent:
                raise APIException(ErrorCode.BAD_REQUEST, "상위 메뉴가 존재하지 않습니다")
            depth = parent["depth"] + 1

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_menu (parent_menu_id, menu_code, menu_name, menu_type, "
                    "menu_path, api_pattern, icon, sort_order, depth, description) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING menu_id",
                    (parent_menu_id, data["menu_code"], data["menu_name"], data["menu_type"],
                     data.get("menu_path"), data.get("api_pattern"), data.get("icon"),
                     data.get("sort_order", 0), depth, data.get("description")),
                )
                new_id = cur.fetchone()["menu_id"]
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 메뉴 코드입니다")
            raise

        log_step(logger, request_id, "MENU", "3", "CREATE", "메뉴 생성", menu_id=new_id, menu_code=data["menu_code"])
        return self.get_menu(new_id, request_id)

    def update_menu(self, menu_id: int, data: dict, current_user: UserContext, request_id: str = "") -> dict:
        """메뉴 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id FROM tb_menu WHERE menu_id = %s", (menu_id,))
            if not cur.fetchone():
                raise APIException(ErrorCode.NOT_FOUND, "메뉴를 찾을 수 없습니다")

        fields = []
        params: list = []
        for key in ("menu_name", "menu_path", "api_pattern", "icon", "sort_order", "is_active", "description"):
            if key in data:
                fields.append(f"{key} = %s")
                params.append(data[key])

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(menu_id)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_menu SET {', '.join(fields)} WHERE menu_id = %s", params)

        log_step(logger, request_id, "MENU", "4", "UPDATE", "메뉴 수정", menu_id=menu_id)
        return self.get_menu(menu_id, request_id)

    def delete_menu(self, menu_id: int, current_user: UserContext, request_id: str = "") -> bool:
        """메뉴 삭제 (하위 메뉴 있으면 불가)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id, menu_code FROM tb_menu WHERE menu_id = %s", (menu_id,))
            existing = cur.fetchone()
        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "메뉴를 찾을 수 없습니다")

        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_menu WHERE parent_menu_id = %s", (menu_id,))
            if cur.fetchone()["cnt"] > 0:
                raise APIException(ErrorCode.BAD_REQUEST, "하위 메뉴가 있어 삭제할 수 없습니다. 하위 메뉴를 먼저 삭제하세요")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_menu WHERE menu_id = %s", (menu_id,))

        log_step(logger, request_id, "MENU", "5", "DELETE", "메뉴 삭제", menu_id=menu_id, menu_code=existing["menu_code"])
        return True


menu_service = MenuService()
