# Phase 3 구현 가이드: 인증 API + 인증 미들웨어

> **문서 버전**: 1.0
> **작성일**: 2026-02-12
> **상위 문서**: `docs/design/user_permission_system.md`
> **선행 조건**: Phase 2 완료 (Core Security 모듈)
> **목적**: Phase 3(인증 API + 인증 미들웨어)의 실제 구현 절차를 코드 레벨에서 상세 설명

---

## 목차

1. [Phase 3 개요](#1-phase-3-개요)
2. [Step 0: `error_codes.py` 수정 — ACCOUNT_LOCKED 추가](#2-step-0-error_codes)
3. [Step 1: `auth_service.py` — 인증 비즈니스 로직](#3-step-1-auth_service)
4. [Step 2: `auth.py` (routes) — 인증 API 엔드포인트](#4-step-2-auth-routes)
5. [Step 3: `auth.py` (middleware) — 인증 미들웨어](#5-step-3-auth-middleware)
6. [Step 4: `main.py` 수정 — 미들웨어/라우터 등록](#6-step-4-main)
7. [검증 체크리스트](#7-검증-체크리스트)
8. [다음 단계 (Phase 4 Preview)](#8-다음-단계)

---

## 1. Phase 3 개요

### 1.1 무엇을 하는가

Phase 3은 실제 **로그인/로그아웃/토큰갱신** 기능을 구현하여 시스템 접근의 첫 관문을 만드는 단계입니다.

```
Phase 3 산출물:
  [MOD] app/core/errors/error_codes.py      ← ACCOUNT_LOCKED 에러코드 추가
  [NEW] app/api/services/auth_service.py    ← 인증 비즈니스 로직 (6개 메서드)
  [NEW] app/api/routes/auth.py              ← 인증 API (5개 엔드포인트)
  [NEW] app/middleware/auth.py              ← 인증 미들웨어 (선택적 모드)
  [MOD] app/middleware/__init__.py          ← AuthMiddleware export 추가
  [MOD] app/main.py                        ← 미들웨어 + 라우터 등록
```

### 1.2 왜 필요한가

| 모듈 | 없으면 어떻게 되는가 |
|------|---------------------|
| `auth_service.py` | 로그인 검증, 세션 관리, 권한 조회 로직을 API 핸들러에 직접 작성해야 함 |
| `routes/auth.py` | 클라이언트가 로그인/로그아웃/토큰갱신할 수 있는 HTTP 엔드포인트가 없음 |
| `middleware/auth.py` | 모든 API 핸들러에서 직접 토큰 검증을 해야 함 → 누락 위험 |

### 1.3 핵심 설계 결정

```
┌─────────────────────────────────────────────────────────────────────┐
│  Q: 인증 미들웨어를 바로 "필수 모드"로 도입할까?                       │
│  A: 아니요. "선택적 모드(Phase 3a)"로 도입합니다.                     │
│                                                                      │
│     이유: 기존 API (search, agent, rag 등)가 토큰 없이 동작하고      │
│     있으므로, 미들웨어 도입 즉시 401을 반환하면 기존 기능이 깨집니다.  │
│                                                                      │
│     Phase 3a: 토큰 있으면 검증, 없으면 anonymous로 통과              │
│     Phase 6+: 프론트엔드 인증 완료 후 "필수 모드"로 전환              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Q: DB 조회는 언제 하는가?                                           │
│  A: 로그인 시점과 Refresh Token 갱신 시점에만 DB에서 권한을 조회합니다.│
│     Access Token 검증(매 요청)은 JWT 페이로드만으로 처리 (DB 조회 없음)│
│                                                                      │
│     권한이 변경되면?                                                  │
│     → Access Token 만료(30분) 후 Refresh 시점에 최신 권한이 로드됨   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 Phase 2에서 만든 모듈과의 관계

```
Phase 2 (이미 완성)           Phase 3 (이번에 구현)
┌──────────────────┐         ┌──────────────────────────┐
│ password.py      │────────→│ auth_service.py          │
│ (해싱/검증)      │         │ (authenticate,           │
├──────────────────┤         │  change_password)        │
│ jwt.py           │────────→│                          │
│ (토큰생성/검증)  │         │ (create_session,         │
├──────────────────┤         │  refresh_access_token)   │
│ dependencies.py  │────────→├──────────────────────────┤
│ (get_current_user)│        │ routes/auth.py           │
├──────────────────┤         │ (login, logout, refresh, │
│ permission.py    │         │  me, change_password)    │
│ (require_perm)   │         ├──────────────────────────┤
└──────────────────┘         │ middleware/auth.py        │
                             │ (토큰→UserContext 설정)   │
                             └──────────────────────────┘
```

### 1.5 요청 흐름 (로그인 → API 사용 → 토큰 갱신)

```
1. POST /api/v1/auth/login
   → auth_service.authenticate(login_id, password)
     → tb_user 조회 → 잠금 확인 → 비밀번호 검증
   → auth_service.create_session(user_id, ip, user_agent)
     → get_user_with_permissions(user_id) → 역할/권한 조회
     → tb_user_session INSERT
     → JWT Access + Refresh Token 생성
   → TokenResponse 반환

2. GET /api/v1/auth/me (Authorization: Bearer <access_token>)
   → AuthMiddleware: Bearer 토큰 추출 → verify_token → UserContext
   → request.state.current_user에 저장
   → Depends(get_current_active_user) → UserContext 반환

3. POST /api/v1/auth/refresh (Access Token 만료 후)
   → auth_service.refresh_access_token(refresh_token)
     → JWT verify (token_type=refresh)
     → tb_user_session에서 refresh_token 조회
     → get_user_with_permissions → 최신 권한 로드
     → 새 Access Token 생성
   → TokenResponse 반환

4. POST /api/v1/auth/logout
   → auth_service.logout(session_id)
     → tb_user_session DELETE
```

---

## 2. Step 0: error_codes.py 수정

### 2.1 변경 내용

`app/core/errors/error_codes.py`에 `ACCOUNT_LOCKED` 에러코드를 추가합니다.

### 2.2 수정 부분

```python
# ========== 비즈니스 오류 ========== 섹션에 추가:
ACCOUNT_LOCKED = "ACCOUNT_LOCKED"          # 계정 잠금

# ERROR_MESSAGES에 추가:
ErrorCode.ACCOUNT_LOCKED: "계정이 잠겼습니다. 잠시 후 다시 시도해주세요",

# ERROR_STATUS_CODES에 추가:
ErrorCode.ACCOUNT_LOCKED: status.HTTP_423_LOCKED,
```

### 2.3 HTTP 423 LOCKED

HTTP 423은 WebDAV에서 유래하지만, REST API에서도 "리소스가 잠김" 상태를 표현할 때 사용할 수 있습니다. 401(인증 실패)과 구분하여 클라이언트가 "계정 잠금"과 "비밀번호 오류"를 다르게 처리할 수 있게 합니다.

---

## 3. Step 1: auth_service.py

### 3.1 파일 위치

```
app/api/services/auth_service.py
```

### 3.2 전체 소스코드

```python
"""인증 서비스

위치: app/api/services/auth_service.py
로그인, 세션 관리, 토큰 갱신, 비밀번호 변경 비즈니스 로직
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security.password import hash_password, verify_password
from app.models.auth import TokenResponse, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# scope_type 우선순위 (숫자가 클수록 넓은 범위)
_SCOPE_PRIORITY = {"USER": 1, "TENANT": 2, "GLOBAL": 3}


class AuthService:
    """인증 비즈니스 로직"""

    def authenticate(self, login_id: str, password: str, request_id: str = "") -> Dict[str, Any]:
        """로그인 검증 — 비밀번호 확인 + 실패 횟수 관리 + 계정 잠금"""
        log_step(logger, request_id, "AUTH", "1", "LOGIN", "로그인 시도", login_id=login_id)

        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, login_id, password_hash, is_active, is_superuser, "
                "login_fail_count, locked_until, display_name, tenant_id "
                "FROM tb_user WHERE login_id = %s",
                (login_id,),
            )
            row = cur.fetchone()

        if not row:
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "사용자 없음", login_id=login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다")

        user = dict(row)

        # 비활성 계정
        if not user["is_active"]:
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "비활성 계정", login_id=login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 계정 잠금 확인
        if user["locked_until"]:
            now = datetime.now(timezone.utc)
            if now < user["locked_until"]:
                remaining = int((user["locked_until"] - now).total_seconds() // 60) + 1
                log_step(logger, request_id, "AUTH", "1", "LOGIN", "계정 잠금", login_id=login_id, remaining_min=remaining)
                raise APIException(ErrorCode.ACCOUNT_LOCKED, f"계정이 잠겼습니다. {remaining}분 후 다시 시도해주세요")

            # 잠금 시간 경과 → 잠금 해제
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "UPDATE tb_user SET locked_until = NULL, login_fail_count = 0 WHERE user_id = %s",
                    (user["user_id"],),
                )

        # 비밀번호 검증
        if not verify_password(password, user["password_hash"]):
            self._handle_login_failure(user["user_id"], user["login_fail_count"], request_id, login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다")

        # 로그인 성공 → 실패 횟수 초기화 + last_login_at 갱신
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tb_user SET login_fail_count = 0, locked_until = NULL, "
                "last_login_at = NOW() WHERE user_id = %s",
                (user["user_id"],),
            )

        log_step(logger, request_id, "AUTH", "1", "LOGIN", "로그인 성공", login_id=login_id, user_id=user["user_id"])
        return user

    def _handle_login_failure(self, user_id: int, current_fail_count: int, request_id: str, login_id: str) -> None:
        """로그인 실패 처리 — 실패 횟수 증가 + 잠금 정책"""
        new_count = current_fail_count + 1
        locked_until = None

        if new_count >= settings.login_max_fail_count:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.login_lock_minutes)
            log_step(logger, request_id, "AUTH", "1", "LOGIN", "계정 잠금 처리", login_id=login_id, fail_count=new_count, lock_min=settings.login_lock_minutes)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tb_user SET login_fail_count = %s, locked_until = %s WHERE user_id = %s",
                (new_count, locked_until, user_id),
            )

    def create_session(self, user_id: int, ip: str, user_agent: str, request_id: str = "") -> TokenResponse:
        """세션 생성 — 권한 조회 + tb_user_session INSERT + 토큰 발급"""
        user_info = self.get_user_with_permissions(user_id, request_id)

        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)

        # JWT 토큰 데이터 구성
        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "scope_type": user_info["scope_type"],
            "roles": user_info["roles"],
            "permissions": user_info["permissions"],
            "is_superuser": user_info["is_superuser"],
        }
        access_token = create_access_token(token_data)

        refresh_data = {"sub": str(user_id), "session_id": session_id}
        refresh_token = create_refresh_token(refresh_data)

        # DB 세션 저장
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tb_user_session (session_id, user_id, refresh_token, ip_address, user_agent, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (session_id, user_id, refresh_token, ip, user_agent[:500] if user_agent else None, expires_at),
            )

        log_step(logger, request_id, "AUTH", "2", "SESSION", "세션 생성", user_id=user_id, session_id=session_id[:8])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=user_id,
                login_id=user_info["login_id"],
                display_name=user_info["display_name"],
                tenant_id=user_info["tenant_id"],
                scope_type=user_info["scope_type"],
                roles=user_info["roles"],
                permissions=user_info["permissions"],
            ),
        )

    def refresh_access_token(self, refresh_token: str, request_id: str = "") -> TokenResponse:
        """Access Token 갱신 — Refresh Token 검증 + 최신 권한 로드"""
        # 1. JWT 검증
        payload = verify_token(refresh_token)
        if payload.token_type != "refresh":
            raise APIException(ErrorCode.UNAUTHORIZED, "Refresh Token이 필요합니다")

        session_id = payload.session_id
        if not session_id:
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 Refresh Token입니다")

        # 2. DB에서 세션 확인
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, expires_at FROM tb_user_session "
                "WHERE session_id = %s AND refresh_token = %s",
                (session_id, refresh_token),
            )
            session = cur.fetchone()

        if not session:
            log_step(logger, request_id, "AUTH", "3", "REFRESH", "세션 없음 또는 토큰 불일치", session_id=session_id[:8] if session_id else "none")
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 세션입니다")

        # 3. 세션 만료 확인
        if datetime.now(timezone.utc) > session["expires_at"]:
            # 만료된 세션 삭제
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM tb_user_session WHERE session_id = %s", (session_id,))
            raise APIException(ErrorCode.SESSION_EXPIRED, "세션이 만료되었습니다. 다시 로그인해주세요")

        # 4. 최신 권한으로 Access Token 재생성
        user_id = session["user_id"]
        user_info = self.get_user_with_permissions(user_id, request_id)

        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "scope_type": user_info["scope_type"],
            "roles": user_info["roles"],
            "permissions": user_info["permissions"],
            "is_superuser": user_info["is_superuser"],
        }
        new_access_token = create_access_token(token_data)

        log_step(logger, request_id, "AUTH", "3", "REFRESH", "토큰 갱신 완료", user_id=user_id, session_id=session_id[:8])

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=user_id,
                login_id=user_info["login_id"],
                display_name=user_info["display_name"],
                tenant_id=user_info["tenant_id"],
                scope_type=user_info["scope_type"],
                roles=user_info["roles"],
                permissions=user_info["permissions"],
            ),
        )

    def logout(self, session_id: str, request_id: str = "") -> bool:
        """로그아웃 — 세션 삭제"""
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_session WHERE session_id = %s", (session_id,))
            deleted = cur.rowcount > 0

        log_step(logger, request_id, "AUTH", "4", "LOGOUT", "로그아웃", session_id=session_id[:8], deleted=deleted)
        return deleted

    def get_user_with_permissions(self, user_id: int, request_id: str = "") -> Dict[str, Any]:
        """사용자 정보 + 역할 + 권한 일괄 조회"""
        # 1. 사용자 기본 정보
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT user_id, login_id, email, display_name, tenant_id, is_superuser, is_active "
                "FROM tb_user WHERE user_id = %s",
                (user_id,),
            )
            user_row = cur.fetchone()

        if not user_row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(user_row)
        if not user["is_active"]:
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 2. 역할 + 권한 조회
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT DISTINCT r.role_code, r.scope_type, p.permission_code "
                "FROM tb_user_role ur "
                "JOIN tb_role r ON ur.role_id = r.role_id "
                "LEFT JOIN tb_role_permission rp ON r.role_id = rp.role_id "
                "LEFT JOIN tb_permission p ON rp.permission_id = p.permission_id "
                "WHERE ur.user_id = %s",
                (user_id,),
            )
            rows = cur.fetchall()

        roles = set()
        permissions = set()
        max_scope = "USER"

        for row in rows:
            if row["role_code"]:
                roles.add(row["role_code"])
            if row["permission_code"]:
                permissions.add(row["permission_code"])
            # scope_type 우선순위: GLOBAL > TENANT > USER
            row_scope = row["scope_type"] or "USER"
            if _SCOPE_PRIORITY.get(row_scope, 0) > _SCOPE_PRIORITY.get(max_scope, 0):
                max_scope = row_scope

        user["roles"] = sorted(roles)
        user["permissions"] = sorted(permissions)
        user["scope_type"] = max_scope

        log_step(logger, request_id, "AUTH", "2", "PERMISSION", "권한 조회 완료", user_id=user_id, roles=len(roles), perms=len(permissions), scope=max_scope)
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str, request_id: str = "") -> bool:
        """비밀번호 변경"""
        # 1. 현재 비밀번호 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT password_hash FROM tb_user WHERE user_id = %s", (user_id,))
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        if not verify_password(current_password, row["password_hash"]):
            raise APIException(ErrorCode.UNAUTHORIZED, "현재 비밀번호가 올바르지 않습니다")

        # 2. 새 비밀번호 해시 + 저장
        new_hash = hash_password(new_password)
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE tb_user SET password_hash = %s, updated_at = NOW() WHERE user_id = %s",
                (new_hash, user_id),
            )

        log_step(logger, request_id, "AUTH", "5", "PASSWORD", "비밀번호 변경 완료", user_id=user_id)
        return True


# 싱글톤 인스턴스
auth_service = AuthService()
```

### 3.3 주요 문법 설명

#### 3.3.1 scope_type 결정 로직

사용자가 여러 역할을 가질 수 있으므로, 가장 넓은 범위의 scope_type을 채택합니다.

```python
_SCOPE_PRIORITY = {"USER": 1, "TENANT": 2, "GLOBAL": 3}

# 예: 사용자가 SYSTEM_ADMIN(GLOBAL) + TENANT_ADMIN(TENANT) 역할 보유
# → max_scope = GLOBAL
```

#### 3.3.2 계정 잠금 정책

```
login_max_fail_count = 5 (settings.py에 정의)
login_lock_minutes = 30

1회 실패 → login_fail_count = 1
2회 실패 → login_fail_count = 2
...
5회 실패 → login_fail_count = 5, locked_until = NOW() + 30분
→ 잠금 해제 시간 이전 로그인 시도 → ACCOUNT_LOCKED 반환
→ 잠금 해제 시간 경과 후 로그인 시도 → 잠금 해제 + 카운트 리셋
```

#### 3.3.3 Refresh Token 갱신 시 권한 재로드

```
로그인 시점 → JWT에 roles/permissions 포함 (30분 유효)
관리자가 사용자 권한 변경 →
  현재 Access Token은 이전 권한 유지 (최대 30분)
  Access Token 만료 → Refresh → get_user_with_permissions() → 최신 권한 로드
```

---

## 4. Step 2: routes/auth.py

### 4.1 파일 위치

```
app/api/routes/auth.py
```

### 4.2 전체 소스코드

```python
"""인증 API 엔드포인트

위치: app/api/routes/auth.py
로그인, 로그아웃, 토큰 갱신, 내 정보 조회, 비밀번호 변경
"""
import uuid

from fastapi import APIRouter, Depends, Request

from app.api.services.auth_service import auth_service
from app.core.errors import success_response
from app.core.security.dependencies import get_current_active_user
from app.models.auth import (
    LoginRequest, RefreshRequest, PasswordChangeRequest,
    UserContext, UserInfo,
)
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """로그인 — JWT 토큰 발급"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # 1. 인증
    user = auth_service.authenticate(body.login_id, body.password, request_id)

    # 2. 세션 생성 + 토큰 발급
    token_response = auth_service.create_session(user["user_id"], ip, user_agent, request_id)

    return success_response(token_response.model_dump())


@router.post("/logout")
async def logout(request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """로그아웃 — 세션 삭제"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    # Authorization 헤더에서 토큰 추출 → session_id 확인
    from app.core.security.jwt import verify_token
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if token:
        payload = verify_token(token)
        # Access Token에는 session_id가 없으므로, 해당 사용자의 세션을 user_id로 삭제
        # 또는 Refresh Token의 session_id를 사용
        # 여기서는 사용자의 모든 세션을 삭제 (단일 디바이스 가정)
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_session WHERE user_id = %s", (current_user.user_id,))

    log_step(logger, request_id, "AUTH", "4", "LOGOUT", "로그아웃 완료", user_id=current_user.user_id)
    return success_response({"message": "로그아웃되었습니다"})


@router.post("/refresh")
async def refresh(body: RefreshRequest, request: Request):
    """Access Token 갱신"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    token_response = auth_service.refresh_access_token(body.refresh_token, request_id)
    return success_response(token_response.model_dump())


@router.get("/me")
async def get_me(current_user: UserContext = Depends(get_current_active_user)):
    """현재 사용자 정보 조회"""
    user_info = UserInfo(
        user_id=current_user.user_id,
        login_id=current_user.login_id,
        display_name=current_user.display_name,
        tenant_id=current_user.tenant_id,
        scope_type=current_user.scope_type,
        roles=current_user.roles,
        permissions=current_user.permissions,
    )
    return success_response(user_info.model_dump())


@router.put("/me/password")
async def change_password(
    body: PasswordChangeRequest,
    request: Request,
    current_user: UserContext = Depends(get_current_active_user),
):
    """비밀번호 변경"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    auth_service.change_password(current_user.user_id, body.current_password, body.new_password, request_id)
    return success_response({"message": "비밀번호가 변경되었습니다"})
```

### 4.3 엔드포인트별 인증 요구사항

| Endpoint | 인증 | Depends 사용 |
|----------|------|-------------|
| `POST /login` | 불필요 | - |
| `POST /logout` | 필수 | `get_current_active_user` |
| `POST /refresh` | 불필요* | *Refresh Token을 body로 받음 |
| `GET /me` | 필수 | `get_current_active_user` |
| `PUT /me/password` | 필수 | `get_current_active_user` |

---

## 5. Step 3: middleware/auth.py

### 5.1 파일 위치

```
app/middleware/auth.py
```

### 5.2 전체 소스코드

```python
"""인증 미들웨어

위치: app/middleware/auth.py
HTTP 요청의 Bearer 토큰을 검증하고 request.state.current_user에 UserContext를 저장합니다.
Phase 3a: 선택적 모드 — 토큰 없어도 차단하지 않음 (기존 API 하위호환)
"""
from typing import Set

from starlette.requests import Request
from starlette.responses import Response

from app.core.security.jwt import verify_token
from app.middleware.base import BaseMiddleware
from app.models.auth import UserContext
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """인증 미들웨어 (선택적 모드)"""

    EXCLUDE_PATHS: Set[str] = {
        "/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico",
        "/api/v1/auth/login", "/api/v1/auth/refresh",
    }

    EXCLUDE_PREFIXES: Set[str] = {"/static/"}

    async def process_request(self, request: Request, call_next) -> Response:
        """Bearer 토큰 추출 → UserContext 생성 → request.state에 저장"""
        request.state.current_user = None

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # "Bearer " 이후
            try:
                payload = verify_token(token)
                if payload.token_type == "access":
                    request.state.current_user = UserContext(
                        user_id=int(payload.sub),
                        login_id=payload.login_id,
                        display_name=payload.display_name,
                        tenant_id=payload.tenant_id,
                        is_superuser=payload.is_superuser,
                        scope_type=payload.scope_type,
                        roles=payload.roles,
                        permissions=payload.permissions,
                    )
            except Exception:
                # Phase 3a: 토큰 검증 실패해도 차단하지 않음
                pass

        return await call_next(request)
```

### 5.3 선택적 모드 동작

```
요청에 Authorization 헤더 있음:
  Bearer 토큰 유효 → request.state.current_user = UserContext(...)
  Bearer 토큰 무효 → request.state.current_user = None (차단 안함)

요청에 Authorization 헤더 없음:
  → request.state.current_user = None (차단 안함)

제외 경로:
  → middleware 자체를 건너뜀 (BaseMiddleware.should_skip)
```

### 5.4 middleware/__init__.py 수정

```python
from app.middleware.auth import AuthMiddleware

__all__ = [
    "BaseMiddleware",
    "LoggingMiddleware",
    "HistoryMiddleware",
    "AuthMiddleware",
]
```

---

## 6. Step 4: main.py 수정

### 6.1 변경 내용

```python
# import 추가
from app.api.routes import auth
from app.middleware import AuthMiddleware

# 미들웨어 등록 순서 변경 (역순 실행)
app.add_middleware(HistoryMiddleware)     # 4. 이력 저장
app.add_middleware(AuthMiddleware)        # 3. 인증 검증 ← 추가
app.add_middleware(LoggingMiddleware)     # 2. 로깅 + request_id
app.add_middleware(CORSMiddleware, ...)   # 1. CORS

# 라우터 등록 추가
app.include_router(auth.router)          # ← 추가
```

### 6.2 미들웨어 실행 순서 (최종)

```
요청 순서: CORSMiddleware → LoggingMiddleware → AuthMiddleware → HistoryMiddleware → Handler
응답 순서: Handler → HistoryMiddleware → AuthMiddleware → LoggingMiddleware → CORSMiddleware

역할:
  CORS       → 브라우저 Same-Origin 정책 처리
  Logging    → request_id 생성 + 요청/응답 로깅
  Auth       → Bearer 토큰 → UserContext (선택적 모드)
  History    → API 이력 DB 저장
  Handler    → 실제 API 로직
```

---

## 7. 검증 체크리스트

### 7.1 단위 검증 (tests/test_auth.py)

- [ ] `auth_service.authenticate` — 올바른 비밀번호 → 성공
- [ ] `auth_service.authenticate` — 틀린 비밀번호 → UNAUTHORIZED
- [ ] `auth_service.authenticate` — 존재하지 않는 ID → UNAUTHORIZED
- [ ] `auth_service.create_session` — TokenResponse 형식 확인
- [ ] `auth_service.get_user_with_permissions` — roles/permissions 포함 확인
- [ ] `auth_service.refresh_access_token` — 유효한 Refresh Token → 새 Access Token
- [ ] `auth_service.change_password` — 비밀번호 변경 후 새 비밀번호로 로그인 성공

### 7.2 통합 검증 (curl)

```bash
# 1. 로그인
curl -X POST http://localhost:19090/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login_id": "admin", "password": "admin123!"}'

# 2. 내 정보 조회
curl http://localhost:19090/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 3. 토큰 갱신
curl -X POST http://localhost:19090/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# 4. 로그아웃
curl -X POST http://localhost:19090/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

### 7.3 기존 API 하위호환 확인

```bash
# 기존 API가 토큰 없이도 정상 동작하는지 확인
curl -X POST http://localhost:19090/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "재택근무 정책", "mode": "rag"}'
```

---

## 8. 다음 단계 (Phase 4 Preview)

Phase 4에서는 **사용자/역할/테넌트 관리 API (CRUD)**를 구현합니다:
- 사용자 CRUD (admin:users 권한 필요)
- 역할 CRUD (admin:roles 권한 필요)
- 테넌트 CRUD (admin:tenants 권한 필요)
- 기존 API에 권한 적용 (require_permission 의존성 사용)
