"""
권한 검사 의존성 팩토리 (v2.0 - 메뉴 기반)

위치: app/core/security/permission.py
FastAPI Depends로 사용하는 권한 검사 함수 생성기
"""
from fastapi import Depends

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext


def require_menu_permission(menu_code: str, action: str = "read"):
    """메뉴 + CRUD 기반 권한 검사 의존성 (v2.0)

    Args:
        menu_code: 메뉴 코드 (예: "USER_MGMT", "DASHBOARD")
        action: CRUD 액션 (create, read, update, delete, export)
    """
    valid_actions = {"create", "read", "update", "delete", "export"}
    if action not in valid_actions:
        raise ValueError(f"action은 {valid_actions} 중 하나여야 합니다")

    async def permission_checker(current_user: UserContext = Depends(get_current_active_user), ) -> UserContext:
        # superuser는 항상 통과
        if current_user.is_superuser:
            return current_user

        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT can_create, can_read, can_update, can_delete, can_export "
                "FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true",
                (current_user.user_id, menu_code),
            )
            row = cur.fetchone()

        if not row or not row[f"can_{action}"]:
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"필요 권한: {menu_code}:{action}")
        return current_user

    return permission_checker


def require_superuser():
    """시스템 관리자 전용 의존성"""

    async def superuser_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not current_user.is_superuser:
            raise APIException(ErrorCode.FORBIDDEN, "시스템 관리자 전용 기능입니다")
        return current_user

    return superuser_checker
