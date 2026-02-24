"""메뉴 관리 서비스

위치: app/api/services/menu_service.py
메뉴 트리 CRUD + 부모 변경 + 순서 변경 비즈니스 로직
"""
from typing import Any, Dict, List

from app.core.database.connection import db_manager
from app.core.errors.handlers import APIException
from app.core.errors.error_codes import ErrorCode
from app.core.errors.response import raise_on_unique_violation
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
            raise_on_unique_violation(e, "이미 존재하는 메뉴 코드입니다")

        log_step(logger, request_id, "MENU", "3", "CREATE", "메뉴 생성", menu_id=new_id, menu_code=data["menu_code"])
        return self.get_menu(new_id, request_id)

    def update_menu(self, menu_id: int, data: dict, current_user: UserContext, request_id: str = "") -> dict:
        """메뉴 수정 (parent_menu_id 변경 시 depth 자동 재계산)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id, parent_menu_id, depth FROM tb_menu WHERE menu_id = %s", (menu_id,))
            existing = cur.fetchone()
        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "메뉴를 찾을 수 없습니다")

        fields = []
        params: list = []

        # parent_menu_id 변경 처리 (depth 자동 재계산)
        if "parent_menu_id" in data:
            new_parent_id = data["parent_menu_id"]
            new_depth = 0
            if new_parent_id is not None:
                if new_parent_id == menu_id:
                    raise APIException(ErrorCode.BAD_REQUEST, "자기 자신을 상위 메뉴로 설정할 수 없습니다")
                self._check_circular_reference(menu_id, new_parent_id)
                with db_manager.get_cursor() as cur:
                    cur.execute("SELECT depth FROM tb_menu WHERE menu_id = %s", (new_parent_id,))
                    parent = cur.fetchone()
                if not parent:
                    raise APIException(ErrorCode.BAD_REQUEST, "상위 메뉴가 존재하지 않습니다")
                new_depth = parent["depth"] + 1
            fields.append("parent_menu_id = %s")
            params.append(new_parent_id)
            fields.append("depth = %s")
            params.append(new_depth)

        # 기존 필드 업데이트
        for key in ("menu_name", "menu_type", "menu_path", "api_pattern", "icon", "sort_order", "is_active", "description"):
            if key in data:
                fields.append(f"{key} = %s")
                params.append(data[key])

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(menu_id)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_menu SET {', '.join(fields)} WHERE menu_id = %s", params)

        # 하위 메뉴 depth 재계산 (parent 변경 시)
        if "parent_menu_id" in data:
            self._recalculate_children_depth(menu_id)

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
            cur.execute("DELETE FROM tb_user_menu WHERE menu_id = %s", (menu_id,))
            cur.execute("DELETE FROM tb_menu WHERE menu_id = %s", (menu_id,))

        log_step(logger, request_id, "MENU", "5", "DELETE", "메뉴 삭제", menu_id=menu_id, menu_code=existing["menu_code"])
        return True

    def reorder_menus(self, items: list, request_id: str = "") -> dict:
        """메뉴 순서 일괄 변경 (드래그앤드롭용)"""
        with db_manager.get_cursor(commit=True) as cur:
            for item in items:
                cur.execute(
                    "UPDATE tb_menu SET sort_order = %s, updated_at = NOW() WHERE menu_id = %s",
                    (item.sort_order, item.menu_id),
                )
        log_step(logger, request_id, "MENU", "6", "REORDER", "메뉴 순서 변경", count=len(items))
        return {"message": "메뉴 순서가 변경되었습니다", "updated_count": len(items)}

    # ===== 내부 헬퍼 =====

    def _check_circular_reference(self, menu_id: int, new_parent_id: int) -> None:
        """순환 참조 검사: new_parent_id가 menu_id의 하위 메뉴인지 확인"""
        with db_manager.get_cursor() as cur:
            current_id = new_parent_id
            visited = set()
            while current_id is not None:
                if current_id in visited:
                    break
                visited.add(current_id)
                if current_id == menu_id:
                    raise APIException(ErrorCode.BAD_REQUEST, "순환 참조가 발생합니다 (하위 메뉴를 상위로 설정할 수 없습니다)")
                cur.execute("SELECT parent_menu_id FROM tb_menu WHERE menu_id = %s", (current_id,))
                row = cur.fetchone()
                current_id = row["parent_menu_id"] if row else None

    def _recalculate_children_depth(self, parent_menu_id: int) -> None:
        """하위 메뉴의 depth를 재귀적으로 재계산 (단일 커서로 처리)"""
        with db_manager.get_cursor(commit=True) as cur:
            self._recalc_depth_recursive(cur, parent_menu_id)

    def _recalc_depth_recursive(self, cur, parent_menu_id: int) -> None:
        """단일 커서 내에서 재귀적으로 depth 재계산"""
        cur.execute("SELECT menu_id, depth FROM tb_menu WHERE menu_id = %s", (parent_menu_id,))
        parent = cur.fetchone()
        if not parent:
            return
        parent_depth = parent["depth"]
        cur.execute("SELECT menu_id FROM tb_menu WHERE parent_menu_id = %s", (parent_menu_id,))
        children = cur.fetchall()
        for child in children:
            cur.execute("UPDATE tb_menu SET depth = %s, updated_at = NOW() WHERE menu_id = %s", (parent_depth + 1, child["menu_id"]))
            self._recalc_depth_recursive(cur, child["menu_id"])


menu_service = MenuService()
