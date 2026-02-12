"""
권한 검사 의존성 팩토리

위치: app/core/security/permission.py
FastAPI Depends로 사용하는 권한 검사 함수 생성기
"""
from fastapi import Depends

from app.core.errors import APIException, ErrorCode
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext


def require_permission(*required_permissions: str):
    """권한 검사 의존성 (AND 조건 — 모든 권한 필요)"""

    async def permission_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not current_user.has_all_permissions(*required_permissions):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"필요 권한: {', '.join(required_permissions)}")
        return current_user

    return permission_checker


def require_any_permission(*required_permissions: str):
    """권한 검사 의존성 (OR 조건 — 하나라도 있으면 통과)"""

    async def permission_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not current_user.has_any_permission(*required_permissions):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"필요 권한 중 하나: {', '.join(required_permissions)}")
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
