"""인증 API 엔드포인트

위치: app/api/routes/auth.py
로그인, 로그아웃, 토큰 갱신, 내 정보 조회, 비밀번호 변경, SSO
"""
import base64
import json
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.api.services.auth_service import auth_service
from app.config import settings
from app.core.errors.response import success_response
from app.core.security.dependencies import get_current_active_user
from app.models.auth import LoginRequest, RefreshRequest, PasswordChangeRequest, SSOLoginRequest, UserContext, UserInfo
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


@router.post("/sso")
async def sso_login(body: SSOLoginRequest, request: Request):
    """SSO 로그인 — 외부 시스템 JWT 토큰 검증 후 MUREUM JWT 발급"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    user = auth_service.sso_authenticate(body.sso_token, request_id)
    token_response = auth_service.create_session(user["user_id"], ip, user_agent, request_id)

    return success_response(token_response.model_dump())


@router.post("/sso-redirect")
async def sso_redirect(request: Request, token: str = Form(...)):
    """SSO 리다이렉트 — 외부 시스템 Hidden Form POST → 토큰 검증 → Base64URL 쿠키 → 302"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    user = auth_service.sso_authenticate(token, request_id)
    token_response = auth_service.create_session(user["user_id"], ip, user_agent, request_id)

    redirect_url = f"{settings.sso_frontend_url}/sso" if settings.sso_frontend_url else "/sso"
    response = RedirectResponse(url=redirect_url, status_code=302)

    # Base64URL 인코딩 (RFC 4648 §5, JWT와 동일 방식: A-Za-z0-9-_ 패딩 없음)
    auth_data = json.dumps({"at": token_response.access_token, "rt": token_response.refresh_token})
    auth_b64url = base64.urlsafe_b64encode(auth_data.encode()).decode().rstrip("=")
    response.set_cookie("sso_auth", auth_b64url, max_age=60, path="/", samesite="lax", httponly=False, secure=False)

    log_step(logger, request_id, "SSO", "4", "REDIRECT", "SSO 쿠키(Base64URL) 설정 후 리다이렉트", redirect_url=redirect_url)
    return response


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
        role_code=user_data["role_code"],
        role_name=user_data.get("role_name", ""),
        landing_page=user_data["landing_page"],
        menus=user_data["menus"],
    )
    return success_response(user_info.model_dump())


@router.put("/me/password")
async def change_password(body: PasswordChangeRequest, request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """비밀번호 변경"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    auth_service.change_password(current_user.user_id, body.current_password, body.new_password, request_id)
    return success_response({"message": "비밀번호가 변경되었습니다"})
