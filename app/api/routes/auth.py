"""인증 API 엔드포인트

위치: app/api/routes/auth.py
로그인, 로그아웃, 토큰 갱신, 내 정보 조회, 비밀번호 변경
"""
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.services.auth_service import auth_service
from app.core.errors import success_response
from app.core.security.dependencies import get_current_active_user
from app.models.auth import LoginRequest, RefreshRequest, PasswordChangeRequest, UserContext, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """로그인 — JWT 토큰 발급"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    user = auth_service.authenticate(body.login_id, body.password, request_id)
    token_response = auth_service.create_session(user["user_id"], ip, user_agent, request_id)

    return success_response(token_response.model_dump())


@router.post("/logout")
async def logout(request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """로그아웃 — 해당 사용자의 세션 삭제"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    auth_service.logout(current_user.user_id, request_id)
    return success_response({"message": "로그아웃되었습니다"})


@router.post("/refresh")
async def refresh(body: RefreshRequest, request: Request):
    """Access Token 갱신"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    token_response = auth_service.refresh_access_token(body.refresh_token, request_id)
    return success_response(token_response.model_dump())


@router.get("/me")
async def get_me(request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """현재 사용자 정보 조회 (DB에서 최신 권한 로드)"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    user_data = auth_service.get_user_with_permissions(current_user.user_id, request_id)
    user_info = UserInfo(
        user_id=user_data["user_id"],
        login_id=user_data["login_id"],
        display_name=user_data["display_name"],
        tenant_id=user_data["tenant_id"],
        scope_type=user_data["scope_type"],
        roles=user_data["roles"],
        role_names=user_data["role_names"],
        permissions=user_data["permissions"],
    )
    return success_response(user_info.model_dump())


@router.put("/me/password")
async def change_password(body: PasswordChangeRequest, request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """비밀번호 변경"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    auth_service.change_password(current_user.user_id, body.current_password, body.new_password, request_id)
    return success_response({"message": "비밀번호가 변경되었습니다"})
