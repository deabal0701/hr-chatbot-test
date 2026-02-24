"""사용자 관리 서비스 (v2.0 - 메뉴 기반)

위치: app/api/services/user_service.py
사용자 CRUD + scope 기반 접근 제한 + 메뉴 권한 관리
"""
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode, raise_on_unique_violation
from app.core.security.password import hash_password
from app.core.security.scope_filter import apply_scope_filter, get_dept_scope_ids
from app.models.auth import UserContext
from app.models.menu import UserMenuPermission
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class UserService:
    """사용자 관리 비즈니스 로직 (v2.0)"""

    @staticmethod
    def _format_user_role(user: dict) -> None:
        """DB 행의 role_id/role_code/role_name/landing_page를 role 객체로 포맷"""
        user["role"] = {
            "role_id": user.pop("role_id"),
            "role_code": user.pop("role_code"),
            "role_name": user.pop("role_name"),
            "landing_page": user.pop("landing_page"),
        } if user.get("role_id") else None

    def _validate_role_tenant(self, role_id: Optional[int], tenant_id: Optional[int], dept_id: Optional[int] = None) -> tuple:
        """역할-테넌트-부서 조합 유효성 검증, (보정된 tenant_id, 보정된 dept_id) 반환

        규칙:
          GLOBAL  → 시스템 테넌트 자동 설정, dept_id=NULL 강제
          TENANT  → tenant_id 필수, 시스템 테넌트 불가, dept_id 허용
          USER    → tenant_id 필수, 시스템 테넌트 불가, dept_id 허용
        """
        if not role_id:
            return tenant_id, dept_id

        with db_manager.get_cursor() as cur:
            cur.execute("SELECT role_code FROM tb_role WHERE role_id = %s", (role_id,))
            role_row = cur.fetchone()
        if not role_row:
            return tenant_id, dept_id

        role_code = role_row["role_code"]

        if role_code == "GLOBAL":
            # GLOBAL → 시스템 테넌트 자동 설정, dept_id=NULL
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT tenant_id FROM tb_tenant WHERE is_system = true LIMIT 1")
                sys_tenant = cur.fetchone()
            return (sys_tenant["tenant_id"] if sys_tenant else tenant_id), None

        # TENANT / USER → 테넌트 필수, 시스템 테넌트 불가
        if not tenant_id:
            raise APIException(ErrorCode.BAD_REQUEST, f"{role_code} 역할은 테넌트를 반드시 선택해야 합니다")
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT is_system FROM tb_tenant WHERE tenant_id = %s", (tenant_id,))
            tenant_row = cur.fetchone()
        if not tenant_row:
            raise APIException(ErrorCode.BAD_REQUEST, "존재하지 않는 테넌트입니다")
        if tenant_row["is_system"]:
            raise APIException(ErrorCode.BAD_REQUEST, f"{role_code} 역할은 시스템 테넌트에 소속될 수 없습니다")

        # dept_id 검증: 부서가 지정된 경우 같은 tenant_id인지 확인
        if dept_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT tenant_id FROM tb_department WHERE dept_id = %s AND is_active = true", (dept_id,))
                dept_row = cur.fetchone()
            if not dept_row:
                raise APIException(ErrorCode.BAD_REQUEST, "존재하지 않거나 비활성 부서입니다")
            if dept_row["tenant_id"] != tenant_id:
                raise APIException(ErrorCode.BAD_REQUEST, "선택한 부서는 해당 테넌트에 소속되지 않습니다")

        return tenant_id, dept_id

    def _check_scope_access(self, target_tenant_id: Optional[int], current_user: UserContext) -> None:
        """scope_level에 따른 접근 범위 검증"""
        if current_user.is_global:
            return
        # USER scope → 사용자 관리 접근 불가 (본인 조회는 별도 처리)
        if current_user.is_user_scope:
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
        # TENANT/DEPT scope → 같은 테넌트만 접근
        if target_tenant_id != current_user.tenant_id:
            raise APIException(ErrorCode.FORBIDDEN, "다른 테넌트의 데이터에 접근할 수 없습니다")

    def list_users(self, current_user: UserContext, request_id: str = "", limit: int = 20, offset: int = 0, tenant_id_filter: Optional[int] = None, is_active_filter: Optional[bool] = None, keyword: Optional[str] = None, dept_id_filter: Optional[int] = None) -> Dict[str, Any]:
        """사용자 목록 조회 (scope 제한 적용)"""
        conditions = []
        params: list = []

        # scope 제한 (scope_level 기반)
        apply_scope_filter(current_user, conditions, params, tenant_col="u.tenant_id", dept_col="u.dept_id", user_col="u.user_id")

        # 필터
        if tenant_id_filter is not None and current_user.is_global:
            conditions.append("u.tenant_id = %s")
            params.append(tenant_id_filter)
        if dept_id_filter is not None:
            dept_ids = get_dept_scope_ids(dept_id_filter)
            placeholders = ",".join(["%s"] * len(dept_ids))
            conditions.append(f"u.dept_id IN ({placeholders})")
            params.extend(dept_ids)
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
                f"t.tenant_name, u.dept_id, d.dept_name, "
                f"u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at, "
                f"r.role_id, r.role_code, r.role_name, r.landing_page, "
                f"(SELECT COUNT(*) FROM tb_user_menu um WHERE um.user_id = u.user_id) as menu_count "
                f"FROM tb_user u "
                f"LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
                f"LEFT JOIN tb_department d ON u.dept_id = d.dept_id "
                f"LEFT JOIN tb_role r ON u.role_id = r.role_id "
                f"{where} ORDER BY u.created_at DESC LIMIT %s OFFSET %s",
                params + [limit, offset],
            )
            rows = cur.fetchall()

        items = []
        for row in rows:
            user = dict(row)
            self._format_user_role(user)
            items.append(user)

        log_step(logger, request_id, "USER", "1", "LIST", "사용자 목록 조회", total=total, role=current_user.role_code)
        return {"total": total, "items": items, "limit": limit, "offset": offset}

    def get_user(self, user_id: int, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                "t.tenant_name, u.dept_id, d.dept_name, "
                "u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at, "
                "r.role_id, r.role_code, r.role_name, r.landing_page, "
                "(SELECT COUNT(*) FROM tb_user_menu um WHERE um.user_id = u.user_id) as menu_count "
                "FROM tb_user u "
                "LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
                "LEFT JOIN tb_department d ON u.dept_id = d.dept_id "
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

        self._format_user_role(user)

        log_step(logger, request_id, "USER", "2", "GET", "사용자 상세 조회", user_id=user_id)
        return user

    def create_user(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 생성 (v2.0: role_id 단일 + 메뉴 권한)"""
        # non-GLOBAL → 자기 테넌트로 강제
        tenant_id = data.get("tenant_id")
        if not current_user.is_global:
            tenant_id = current_user.tenant_id

        password_hashed = hash_password(data["password"])
        role_id = data.get("role_id")
        dept_id = data.get("dept_id")

        # 역할-테넌트-부서 조합 검증
        tenant_id, dept_id = self._validate_role_tenant(role_id, tenant_id, dept_id)

        # role_id 유효성 + 역할 권한 상승 방지
        if role_id:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT role_id, role_code FROM tb_role WHERE role_id = %s", (role_id,))
                role_row = cur.fetchone()
                if not role_row:
                    raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 역할 ID: {role_id}")
                allowed_codes = self._get_allowed_role_codes(current_user)
                if role_row["role_code"] not in allowed_codes:
                    raise APIException(ErrorCode.FORBIDDEN, "자신보다 상위 역할은 할당할 수 없습니다")

        # 권한 상승 방지: GLOBAL이 아닌 사용자는 자신이 보유한 메뉴만 할당 가능
        menus = data.get("menus", [])
        if menus and not current_user.is_global:
            my_menu_ids = self._get_my_menu_ids(current_user.user_id)
            req_menu_ids = {(m["menu_id"] if isinstance(m, dict) else m.menu_id) for m in menus}
            unauthorized_ids = req_menu_ids - my_menu_ids
            if unauthorized_ids:
                raise APIException(ErrorCode.FORBIDDEN, "자신이 보유하지 않은 메뉴는 할당할 수 없습니다")

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, role_id, dept_id, is_active) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING user_id",
                    (data["login_id"], data["email"], password_hashed, data.get("display_name"), tenant_id, role_id, dept_id, data.get("is_active", True)),
                )
                new_user_id = cur.fetchone()["user_id"]

                # 메뉴 권한 할당
                for menu in menus:
                    menu_data = menu if isinstance(menu, dict) else menu.model_dump() if hasattr(menu, "model_dump") else dict(menu)
                    cur.execute(
                        "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (new_user_id, menu_data["menu_id"], menu_data.get("can_create", False), menu_data.get("can_read", True), menu_data.get("can_update", False), menu_data.get("can_delete", False), menu_data.get("can_export", False), current_user.user_id),
                    )
        except Exception as e:
            raise_on_unique_violation(e, "이미 존재하는 로그인 ID 또는 이메일입니다")

        log_step(logger, request_id, "USER", "3", "CREATE", "사용자 생성", user_id=new_user_id, login_id=data["login_id"], menus=len(menus))
        return self.get_user(new_user_id, current_user, request_id)

    def update_user(self, user_id: int, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """사용자 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT user_id, tenant_id, role_id, dept_id, is_superuser FROM tb_user WHERE user_id = %s", (user_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        self._check_scope_access(existing["tenant_id"], current_user)

        # superuser 보호: 다른 관리자가 superuser 수정 불가
        if existing["is_superuser"] and current_user.user_id != user_id:
            raise APIException(ErrorCode.FORBIDDEN, "슈퍼유저는 본인만 수정할 수 있습니다")

        # role_id 유효성 + 역할 권한 상승 방지
        if "role_id" in data and data["role_id"] is not None:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT role_id, role_code FROM tb_role WHERE role_id = %s", (data["role_id"],))
                role_row = cur.fetchone()
                if not role_row:
                    raise APIException(ErrorCode.BAD_REQUEST, f"존재하지 않는 역할 ID: {data['role_id']}")
                allowed_codes = self._get_allowed_role_codes(current_user)
                if role_row["role_code"] not in allowed_codes:
                    raise APIException(ErrorCode.FORBIDDEN, "자신보다 상위 역할은 할당할 수 없습니다")

        # 역할-테넌트-부서 조합 검증 (변경될 최종값 기준)
        final_role_id = data.get("role_id", existing["role_id"])
        final_tenant_id = data.get("tenant_id", existing["tenant_id"])
        final_dept_id = data.get("dept_id", existing.get("dept_id"))
        if "role_id" in data or "tenant_id" in data or "dept_id" in data:
            validated_tenant_id, validated_dept_id = self._validate_role_tenant(final_role_id, final_tenant_id, final_dept_id)
            data["tenant_id"] = validated_tenant_id
            data["dept_id"] = validated_dept_id

        # 동적 UPDATE (nullable 필드는 None→NULL 허용)
        nullable_fields = {"display_name", "dept_id"}
        fields = []
        params: list = []
        for key in ("email", "display_name", "tenant_id", "role_id", "dept_id", "is_active"):
            if key in data:
                if data[key] is None and key not in nullable_fields:
                    continue
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
            raise_on_unique_violation(e, "이미 존재하는 이메일입니다")

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

        # 권한 상승 방지: GLOBAL이 아닌 사용자는 자신이 보유한 메뉴만 할당 가능
        if not current_user.is_global:
            my_menu_ids = self._get_my_menu_ids(current_user.user_id)
            unauthorized_ids = set(menu_ids) - my_menu_ids
            if unauthorized_ids:
                raise APIException(ErrorCode.FORBIDDEN, "자신이 보유하지 않은 메뉴는 할당할 수 없습니다")

        # replace 방식: 삭제 후 재할당
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_menu WHERE user_id = %s", (user_id,))
            for menu in menus:
                cur.execute(
                    "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, menu.menu_id, menu.can_create, menu.can_read, menu.can_update, menu.can_delete, menu.can_export, current_user.user_id),
                )

        result = self._get_user_menus(user_id)
        log_step(logger, request_id, "USER", "6", "ASSIGN_MENUS", "메뉴 권한 할당", user_id=user_id, menus=len(result))
        return {"user_id": user_id, "menus": result, "total_menus": len(result)}

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


    def _get_my_menu_ids(self, user_id: int) -> set:
        """현재 사용자가 보유한 menu_id 집합 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT menu_id FROM tb_user_menu WHERE user_id = %s", (user_id,))
            return {row["menu_id"] for row in cur.fetchall()}

    def get_menu_options(self, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """메뉴 선택 옵션 (사용자 메뉴 권한 할당용, 트리 순서 평탄화)
        전체 메뉴를 반환하되, 자신이 보유하지 않은 메뉴는 assignable=false 표시
        """
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT menu_id, parent_menu_id, menu_code, menu_name, menu_type, "
                "menu_path, icon, sort_order, depth "
                "FROM tb_menu WHERE is_active = true ORDER BY depth, sort_order"
            )
            rows = [dict(row) for row in cur.fetchall()]

        # GLOBAL/superuser가 아니면 assignable 플래그 설정
        if current_user.is_global:
            for row in rows:
                row["assignable"] = True
        else:
            my_menu_ids = self._get_my_menu_ids(current_user.user_id)
            for row in rows:
                row["assignable"] = row["menu_id"] in my_menu_ids

        # 트리 순서로 평탄화 (부모 → 자식 순서 보장)
        children_map: Dict[Optional[int], list] = {}
        for row in rows:
            pid = row["parent_menu_id"]
            children_map.setdefault(pid, []).append(row)

        result: list = []
        def _flatten(parent_id: Optional[int]) -> None:
            for item in children_map.get(parent_id, []):
                result.append(item)
                _flatten(item["menu_id"])
        _flatten(None)

        # 부모가 없어 누락된 항목도 포함
        result_ids = {r["menu_id"] for r in result}
        for row in rows:
            if row["menu_id"] not in result_ids:
                result.append(row)

        log_step(logger, request_id, "USER", "OPT", "MENUS", "메뉴 옵션 조회", total=len(result), role=current_user.role_code)
        return {"total": len(result), "items": result}

    def _get_allowed_role_codes(self, current_user: UserContext) -> list:
        """현재 사용자가 할당 가능한 역할 코드 목록 반환 (DB sort_order 기준)"""
        with db_manager.get_cursor() as cur:
            if current_user.is_global:
                cur.execute("SELECT role_code FROM tb_role ORDER BY sort_order")
                return [row["role_code"] for row in cur.fetchall()]
            cur.execute("SELECT sort_order FROM tb_role WHERE role_code = %s", (current_user.role_code,))
            my_role = cur.fetchone()
            if not my_role:
                return []
            cur.execute("SELECT role_code FROM tb_role WHERE sort_order >= %s ORDER BY sort_order", (my_role["sort_order"],))
            return [row["role_code"] for row in cur.fetchall()]

    def get_role_options(self, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """역할 선택 옵션 (드롭다운용 경량 데이터, 자신보다 상위 역할 제외)"""
        allowed_codes = self._get_allowed_role_codes(current_user)
        placeholders = ", ".join(["%s"] * len(allowed_codes))
        with db_manager.get_cursor() as cur:
            cur.execute(f"SELECT role_id, role_code, role_name FROM tb_role WHERE role_code IN ({placeholders}) ORDER BY sort_order, role_id", allowed_codes)
            rows = cur.fetchall()
        items = [dict(row) for row in rows]
        log_step(logger, request_id, "USER", "OPT", "ROLES", "역할 옵션 조회", total=len(items), role=current_user.role_code)
        return {"total": len(items), "items": items}

    def get_department_options(self, tenant_id: Optional[int], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """부서 선택 옵션 (사용자 생성/수정 시 드롭다운용, tenant_id 기반 flat 리스트)"""
        conditions = ["d.is_active = true"]
        params: list = []

        # non-GLOBAL → 자기 테넌트만
        if not current_user.is_global:
            conditions.append("d.tenant_id = %s")
            params.append(current_user.tenant_id)
        elif tenant_id:
            conditions.append("d.tenant_id = %s")
            params.append(tenant_id)

        where_clause = " AND ".join(conditions)
        with db_manager.get_cursor() as cur:
            cur.execute(f"SELECT d.dept_id, d.dept_code, d.dept_name, d.parent_dept_id, d.depth FROM tb_department d WHERE {where_clause} ORDER BY d.depth, d.sort_order, d.dept_id", params)
            rows = [dict(row) for row in cur.fetchall()]

        log_step(logger, request_id, "USER", "OPT", "DEPTS", "부서 옵션 조회", total=len(rows), tenant_id=tenant_id)
        return {"total": len(rows), "items": rows}

    def get_tenant_options(self, current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """테넌트 선택 옵션 (드롭다운용 경량 데이터)"""
        conditions = ["t.is_active = true"]
        params: list = []
        if not current_user.is_global:
            conditions.append("t.tenant_id = %s")
            params.append(current_user.tenant_id)
        where_clause = " AND ".join(conditions)
        with db_manager.get_cursor() as cur:
            cur.execute(f"SELECT t.tenant_id, t.tenant_code, t.tenant_name, t.is_system FROM tb_tenant t WHERE {where_clause} ORDER BY t.tenant_id", params)
            rows = cur.fetchall()
        items = [dict(row) for row in rows]
        log_step(logger, request_id, "USER", "OPT", "TENANTS", "테넌트 옵션 조회", total=len(items))
        return {"total": len(items), "items": items}


# 싱글톤 인스턴스
user_service = UserService()
