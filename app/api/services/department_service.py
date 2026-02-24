"""부서(조직) 관리 서비스

위치: app/api/services/department_service.py
부서 트리 CRUD + depth 재계산 + 순환참조 검사 비즈니스 로직
"""
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode, raise_on_unique_violation
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class DepartmentService:
    """부서 관리 비즈니스 로직"""

    def get_department_tree(self, tenant_id_filter: Optional[int], current_user: UserContext, request_id: str = "") -> dict:
        """부서 트리 조회 (테넌트별 필터, 계층 구조)"""
        conditions: List[str] = []
        params: list = []

        # scope 기반 테넌트 필터
        if current_user.is_global:
            if tenant_id_filter is not None:
                conditions.append("d.tenant_id = %s")
                params.append(tenant_id_filter)
        else:
            conditions.append("d.tenant_id = %s")
            params.append(current_user.tenant_id)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with db_manager.get_cursor() as cur:
            cur.execute(
                f"SELECT d.dept_id, d.parent_dept_id, d.tenant_id, d.dept_code, d.dept_name, "
                f"d.depth, d.sort_order, d.is_active, d.created_at, d.updated_at, "
                f"t.tenant_name, "
                f"(SELECT COUNT(*) FROM tb_user u WHERE u.dept_id = d.dept_id) as user_count "
                f"FROM tb_department d "
                f"LEFT JOIN tb_tenant t ON d.tenant_id = t.tenant_id "
                f"{where} ORDER BY d.depth, d.sort_order",
                params,
            )
            rows = [dict(row) for row in cur.fetchall()]

        # 트리 빌드 (menu_service.get_menu_tree 패턴)
        dept_map = {row["dept_id"]: {**row, "children": []} for row in rows}
        root_items: List[dict] = []

        for row in rows:
            parent_id = row["parent_dept_id"]
            if parent_id and parent_id in dept_map:
                dept_map[parent_id]["children"].append(dept_map[row["dept_id"]])
            else:
                root_items.append(dept_map[row["dept_id"]])

        log_step(logger, request_id, "DEPT", "1", "TREE", "부서 트리 조회", total=len(rows))
        return {"total": len(rows), "items": root_items}

    def get_department(self, dept_id: int, request_id: str = "") -> dict:
        """부서 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT d.dept_id, d.parent_dept_id, d.tenant_id, d.dept_code, d.dept_name, "
                "d.depth, d.sort_order, d.is_active, d.created_at, d.updated_at, "
                "t.tenant_name, "
                "(SELECT COUNT(*) FROM tb_user u WHERE u.dept_id = d.dept_id) as user_count "
                "FROM tb_department d "
                "LEFT JOIN tb_tenant t ON d.tenant_id = t.tenant_id "
                "WHERE d.dept_id = %s",
                (dept_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "부서를 찾을 수 없습니다")

        log_step(logger, request_id, "DEPT", "2", "GET", "부서 상세 조회", dept_id=dept_id)
        return dict(row)

    def create_department(self, data: dict, current_user: UserContext, request_id: str = "") -> dict:
        """부서 생성"""
        tenant_id = data["tenant_id"]
        parent_dept_id = data.get("parent_dept_id")
        depth = 0

        # 테넌트 존재 + scope 검증
        self._validate_tenant_access(tenant_id, current_user)

        # 상위 부서 검증
        if parent_dept_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT dept_id, tenant_id, depth FROM tb_department WHERE dept_id = %s", (parent_dept_id,))
                parent = cur.fetchone()
            if not parent:
                raise APIException(ErrorCode.BAD_REQUEST, "상위 부서가 존재하지 않습니다")
            if parent["tenant_id"] != tenant_id:
                raise APIException(ErrorCode.BAD_REQUEST, "상위 부서와 같은 테넌트여야 합니다")
            depth = parent["depth"] + 1
            if depth > 10:
                raise APIException(ErrorCode.BAD_REQUEST, "부서 트리 깊이는 최대 10까지 허용됩니다")

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_department (tenant_id, parent_dept_id, dept_code, dept_name, "
                    "depth, sort_order, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING dept_id",
                    (tenant_id, parent_dept_id, data["dept_code"], data["dept_name"],
                     depth, data.get("sort_order", 0), data.get("is_active", True)),
                )
                new_id = cur.fetchone()["dept_id"]
        except Exception as e:
            raise_on_unique_violation(e, "이미 존재하는 부서 코드입니다 (같은 테넌트 내)")

        log_step(logger, request_id, "DEPT", "3", "CREATE", "부서 생성", dept_id=new_id, dept_code=data["dept_code"])
        return self.get_department(new_id, request_id)

    def update_department(self, dept_id: int, data: dict, current_user: UserContext, request_id: str = "") -> dict:
        """부서 수정 (parent_dept_id 변경 시 depth 자동 재계산)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT dept_id, parent_dept_id, tenant_id, depth FROM tb_department WHERE dept_id = %s", (dept_id,))
            existing = cur.fetchone()
        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "부서를 찾을 수 없습니다")

        self._validate_tenant_access(existing["tenant_id"], current_user)

        fields: List[str] = []
        params: list = []

        # parent_dept_id 변경 처리 (depth 자동 재계산)
        if "parent_dept_id" in data:
            new_parent_id = data["parent_dept_id"]
            new_depth = 0
            if new_parent_id is not None:
                if new_parent_id == dept_id:
                    raise APIException(ErrorCode.BAD_REQUEST, "자기 자신을 상위 부서로 설정할 수 없습니다")
                self._check_circular_reference(dept_id, new_parent_id)
                with db_manager.get_cursor() as cur:
                    cur.execute("SELECT depth, tenant_id FROM tb_department WHERE dept_id = %s", (new_parent_id,))
                    parent = cur.fetchone()
                if not parent:
                    raise APIException(ErrorCode.BAD_REQUEST, "상위 부서가 존재하지 않습니다")
                if parent["tenant_id"] != existing["tenant_id"]:
                    raise APIException(ErrorCode.BAD_REQUEST, "상위 부서와 같은 테넌트여야 합니다")
                new_depth = parent["depth"] + 1
                if new_depth > 10:
                    raise APIException(ErrorCode.BAD_REQUEST, "부서 트리 깊이는 최대 10까지 허용됩니다")
            fields.append("parent_dept_id = %s")
            params.append(new_parent_id)
            fields.append("depth = %s")
            params.append(new_depth)

        # 일반 필드 업데이트
        for key in ("dept_name", "sort_order", "is_active"):
            if key in data:
                fields.append(f"{key} = %s")
                params.append(data[key])

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(dept_id)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_department SET {', '.join(fields)} WHERE dept_id = %s", params)

        # 하위 부서 depth 재계산 (parent 변경 시)
        if "parent_dept_id" in data:
            self._recalculate_children_depth(dept_id)

        log_step(logger, request_id, "DEPT", "4", "UPDATE", "부서 수정", dept_id=dept_id)
        return self.get_department(dept_id, request_id)

    def delete_department(self, dept_id: int, current_user: UserContext, request_id: str = "") -> bool:
        """부서 삭제 (하위 부서 또는 소속 사용자 있으면 불가)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT dept_id, dept_code, tenant_id FROM tb_department WHERE dept_id = %s", (dept_id,))
            existing = cur.fetchone()
        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "부서를 찾을 수 없습니다")

        self._validate_tenant_access(existing["tenant_id"], current_user)

        # 하위 부서 존재 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_department WHERE parent_dept_id = %s", (dept_id,))
            if cur.fetchone()["cnt"] > 0:
                raise APIException(ErrorCode.BAD_REQUEST, "하위 부서가 있어 삭제할 수 없습니다. 하위 부서를 먼저 삭제하세요")

        # 소속 사용자 존재 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE dept_id = %s", (dept_id,))
            if cur.fetchone()["cnt"] > 0:
                raise APIException(ErrorCode.BAD_REQUEST, "소속 사용자가 있어 삭제할 수 없습니다. 사용자를 먼저 이동하세요")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_department WHERE dept_id = %s", (dept_id,))

        log_step(logger, request_id, "DEPT", "5", "DELETE", "부서 삭제", dept_id=dept_id, dept_code=existing["dept_code"])
        return True

    def reorder_departments(self, items: list, request_id: str = "") -> dict:
        """부서 순서 일괄 변경 (드래그앤드롭용)"""
        with db_manager.get_cursor(commit=True) as cur:
            for item in items:
                cur.execute(
                    "UPDATE tb_department SET sort_order = %s, updated_at = NOW() WHERE dept_id = %s",
                    (item.sort_order, item.dept_id),
                )
        log_step(logger, request_id, "DEPT", "6", "REORDER", "부서 순서 변경", count=len(items))
        return {"message": "부서 순서가 변경되었습니다", "updated_count": len(items)}

    # ===== 내부 헬퍼 =====

    def _validate_tenant_access(self, tenant_id: int, current_user: UserContext) -> None:
        """테넌트 존재 여부 + 현재 사용자 scope 내 접근 검증"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT tenant_id FROM tb_tenant WHERE tenant_id = %s", (tenant_id,))
            if not cur.fetchone():
                raise APIException(ErrorCode.BAD_REQUEST, "존재하지 않는 테넌트입니다")

        if not current_user.is_global and current_user.tenant_id != tenant_id:
            raise APIException(ErrorCode.FORBIDDEN, "다른 테넌트의 부서에 접근할 수 없습니다")

    def _check_circular_reference(self, dept_id: int, new_parent_id: int) -> None:
        """순환 참조 검사: new_parent_id가 dept_id의 하위 부서인지 확인"""
        with db_manager.get_cursor() as cur:
            current_id = new_parent_id
            visited = set()
            while current_id is not None:
                if current_id in visited:
                    break
                visited.add(current_id)
                if current_id == dept_id:
                    raise APIException(ErrorCode.BAD_REQUEST, "순환 참조가 발생합니다 (하위 부서를 상위로 설정할 수 없습니다)")
                cur.execute("SELECT parent_dept_id FROM tb_department WHERE dept_id = %s", (current_id,))
                row = cur.fetchone()
                current_id = row["parent_dept_id"] if row else None

    def _recalculate_children_depth(self, parent_dept_id: int) -> None:
        """하위 부서의 depth를 재귀적으로 재계산"""
        with db_manager.get_cursor(commit=True) as cur:
            self._recalc_depth_recursive(cur, parent_dept_id)

    def _recalc_depth_recursive(self, cur, parent_dept_id: int) -> None:
        """단일 커서 내에서 재귀적으로 depth 재계산"""
        cur.execute("SELECT dept_id, depth FROM tb_department WHERE dept_id = %s", (parent_dept_id,))
        parent = cur.fetchone()
        if not parent:
            return
        parent_depth = parent["depth"]
        cur.execute("SELECT dept_id FROM tb_department WHERE parent_dept_id = %s", (parent_dept_id,))
        children = cur.fetchall()
        for child in children:
            cur.execute("UPDATE tb_department SET depth = %s, updated_at = NOW() WHERE dept_id = %s", (parent_depth + 1, child["dept_id"]))
            self._recalc_depth_recursive(cur, child["dept_id"])


department_service = DepartmentService()
