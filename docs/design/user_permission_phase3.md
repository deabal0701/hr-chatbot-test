# Phase 3 구현 가이드: 인증 API + 인증 미들웨어 (v2.0)

> **문서 버전**: 2.1
> **작성일**: 2026-02-13
> **수정일**: 2026-02-14
> **상태**: ✅ 구현 완료
> **현행화**: 2026-02-14 (실제 구현 코드 기반 상태 반영)
> **상위 문서**: `docs/design/user_permission_system.md` (v2.1)
> **선행 조건**: Phase 1 (DB + Models v2.0), Phase 2 (Core Security v2.0) 완료
> **목적**: 인증 API + 인증 미들웨어를 v2.0 메뉴 기반 권한 체계에 맞게 구현

---

## 목차

1. [Phase 3 개요](#1-phase-3-개요)
2. [현행 상태 분석 (v1.0 → v2.0 갭)](#2-현행-상태-분석)
3. [Step 1: `auth_service.py` v2.0 마이그레이션](#3-step-1-auth_servicepy)
4. [Step 2: `routes/auth.py` v2.0 마이그레이션](#4-step-2-routesauthpy)
5. [Step 3: `middleware/auth.py` v2.0 마이그레이션](#5-step-3-middlewareauthpy)
6. [Step 4: `main.py` 확인](#6-step-4-mainpy-확인)
7. [검증 체크리스트](#7-검증-체크리스트)
8. [다음 단계 (Phase 4 Preview)](#8-다음-단계)

---

## 1. Phase 3 개요

### 1.1 무엇을 하는가

Phase 3은 **로그인/로그아웃/토큰갱신** 기능을 v2.0 메뉴 기반 권한 체계에 맞게 마이그레이션합니다.
현행 코드는 v1.0 (permission 코드 기반)으로 동작 중이며, v2.0 (메뉴 기반)으로 전환해야 합니다.

```
Phase 3 산출물:
  [MOD] app/api/services/auth_service.py    ← 쿼리 전면 재작성 (★ 핵심 변경)
  [MOD] app/api/routes/auth.py              ← UserInfo 생성 변경 (menus 포함)
  [MOD] app/middleware/auth.py              ← UserContext 생성 변경 (role_code 단일)
  [OK]  app/main.py                         ← 이미 등록 완료 (변경 불필요)
```

### 1.2 v1.0 → v2.0 핵심 변경 사항

| 구분 | v1.0 (현행 코드) | v2.0 (목표) |
|------|:---:|:---:|
| 역할 | `roles: List[str]` (M:N) | `role_code: str` (1:N) |
| 권한 | `permissions: List[str]` (코드) | `menus: List[MenuPermission]` (메뉴 CRUD) |
| 역할 조회 쿼리 | `tb_user_role` + `tb_role_permission` + `tb_permission` JOIN | `tb_user.role_id` → `tb_role` 직접 JOIN |
| 메뉴 권한 조회 | 없음 | `tb_user_menu` + `tb_menu` JOIN |
| UserInfo | `roles`, `role_names`, `permissions` | `role_code`, `landing_page`, `menus` |
| UserContext | `roles`, `permissions`, `has_permission()` | `role_code`, `scope_type` (DB 조회로 대체) |
| JWT payload | `roles`, `permissions` 배열 | `role_code` 단일 |

### 1.3 선행 완료 확인

Phase 3 시작 전 아래 Phase 1~2 산출물이 v2.0으로 완료되어야 합니다:

| 선행 산출물 | 확인 항목 |
|------------|----------|
| Phase 1: DB 테이블 | `tb_user.role_id` FK 존재, `tb_user_menu` 존재, v1.0 테이블(`tb_user_role`, `tb_role_permission`, `tb_permission`) 삭제 |
| Phase 1: `models/auth.py` | `UserInfo.role_code`, `UserInfo.menus`, `UserContext.role_code` (v2.0) |
| Phase 1: `models/menu.py` | `MenuPermission` 클래스 존재 |
| Phase 2: `jwt.py` | `TokenPayload.role_code: str` (단일, `roles` 리스트 제거) |
| Phase 2: `dependencies.py` | `UserContext(role_code=...)` 생성 |
| Phase 2: `permission.py` | `require_menu_permission(menu_code, action)` 구현 |

### 1.4 요청 흐름 (v2.0)

```
1. POST /api/v1/auth/login
   → auth_service.authenticate(login_id, password)
     → tb_user 조회 → 잠금 확인 → 비밀번호 검증
   → auth_service.create_session(user_id, ip, user_agent)
     → get_user_with_permissions(user_id)
       → tb_user JOIN tb_role → role_code, scope_type, landing_page
       → tb_user_menu JOIN tb_menu → menus[{menu_code, can_create, ...}]
     → tb_user_session INSERT
     → JWT Access Token (role_code, scope_type) + Refresh Token (session_id)
   → TokenResponse 반환 (user.menus 포함)

2. GET /api/v1/auth/me (Authorization: Bearer <access_token>)
   → AuthMiddleware: Bearer 토큰 → verify_token → UserContext(role_code=...)
   → request.state.current_user에 저장
   → Depends(get_current_active_user) → UserContext 반환
   → auth_service.get_user_with_permissions() → 최신 권한 + 메뉴 반환

3. POST /api/v1/auth/refresh (Access Token 만료 후)
   → auth_service.refresh_access_token(refresh_token)
     → JWT verify (token_type=refresh)
     → tb_user_session에서 refresh_token 확인
     → get_user_with_permissions → 최신 role_code, menus 로드
     → 새 Access Token (최신 role_code 반영)
   → TokenResponse 반환

4. POST /api/v1/auth/logout
   → auth_service.logout(user_id)
     → tb_user_session DELETE (해당 사용자 전체 세션)
```

### 1.5 설계 결정

```
┌─────────────────────────────────────────────────────────────────────┐
│  Q: 인증 미들웨어를 "필수 모드"로 전환할까?                           │
│  A: 아니요. "선택적 모드(Phase 3a)"를 유지합니다.                    │
│                                                                      │
│     이유: 기존 API (search, agent, rag 등)가 토큰 없이 동작 중이며,  │
│     프론트엔드 인증 완료(Phase 5) 전까지 하위호환 유지 필요.          │
│                                                                      │
│     Phase 3a: 토큰 있으면 검증, 없으면 anonymous로 통과              │
│     Phase 5+: 프론트엔드 인증 완료 후 "필수 모드"로 전환              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Q: JWT에 메뉴 권한을 포함할까?                                      │
│  A: 아니요. JWT에는 role_code, scope_type만 포함합니다.              │
│                                                                      │
│     이유: 메뉴 권한은 사용자별로 커스터마이즈 가능 (role 기본값과      │
│     다를 수 있음). JWT에 넣으면 토큰이 비대해지고, 권한 변경 시      │
│     토큰 만료까지 반영 불가.                                         │
│                                                                      │
│     메뉴 권한 사용 시점:                                             │
│     - 로그인 응답: menus 배열로 프론트엔드에 전달                    │
│     - API 권한 체크: require_menu_permission()이 DB 직접 조회        │
│     - /me 조회: DB에서 최신 메뉴 목록 반환                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Q: 권한 변경이 실시간 반영되는가?                                    │
│  A: Access Token 만료(30분) 후 Refresh 시점에 반영됩니다.            │
│                                                                      │
│     - Access Token 검증은 JWT 페이로드만 사용 (DB 조회 없음)         │
│     - 관리자가 사용자 권한 변경 시:                                   │
│       현재 Access Token은 이전 role_code 유지 (최대 30분)            │
│       → Access Token 만료 → Refresh → 최신 role_code 로드           │
│     - /me 엔드포인트는 항상 DB에서 최신 정보 반환                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 현행 상태 분석

### 2.1 파일별 현행 상태

| # | 파일 | 현재 버전 | 상태 | 비고 |
|---|------|-----------|------|------|
| 1 | `app/api/services/auth_service.py` | v2.0 | ✅ 구현 완료 | `tb_user.role_id` + `tb_user_menu` 기반 쿼리 재작성 완료 |
| 2 | `app/api/routes/auth.py` | v2.0 | ✅ 구현 완료 | `UserInfo(role_code=..., menus=...)` 전환 완료 |
| 3 | `app/middleware/auth.py` | v2.0 | ✅ 구현 완료 | `UserContext(role_code=..., scope_type=...)` 전환 완료 |
| 4 | `app/main.py` | v2.0 | ✅ 완료 | 미들웨어 + 라우터 이미 등록 |

### 2.2 auth_service.py — 현행 v1.0 문제점

현행 `get_user_with_permissions()` 메서드가 참조하는 테이블:

```sql
-- 현행 (v1.0): v2.0 DDL에서 삭제된 테이블을 JOIN (실행 불가)
SELECT DISTINCT r.role_code, r.role_name, r.scope_type, p.permission_code
FROM tb_user_role ur                          -- ← v2.0에서 삭제됨
JOIN tb_role r ON ur.role_id = r.role_id
LEFT JOIN tb_role_permission rp ON ...        -- ← v2.0에서 삭제됨
LEFT JOIN tb_permission p ON ...              -- ← v2.0에서 삭제됨
WHERE ur.user_id = %s
```

v2.0 DDL 적용 후 위 쿼리는 `relation "tb_user_role" does not exist` 에러 발생.

### 2.3 auth_service.py — v2.0 쿼리 변경 방향

```sql
-- v2.0: tb_user.role_id FK로 역할 직접 JOIN
SELECT u.user_id, u.login_id, u.display_name, u.tenant_id, u.is_superuser,
       r.role_code, r.role_name, r.scope_type, r.landing_page
FROM tb_user u
JOIN tb_role r ON r.role_id = u.role_id
WHERE u.user_id = %s

-- v2.0: 메뉴 권한 별도 조회
SELECT m.menu_code, m.menu_name, m.menu_path, m.menu_type, m.icon,
       m.depth, m.sort_order, pm.menu_code AS parent_menu_code,
       um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export
FROM tb_user_menu um
JOIN tb_menu m ON m.menu_id = um.menu_id
LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id
WHERE um.user_id = %s AND m.is_active = true
ORDER BY m.depth, m.sort_order
```

### 2.4 TokenResponse — v1.0 vs v2.0 비교

```json
// v1.0 (현행)
{
  "user": {
    "user_id": 1,
    "login_id": "admin",
    "scope_type": "GLOBAL",
    "roles": ["SYSTEM_ADMIN"],
    "role_names": ["시스템 관리자"],
    "permissions": ["nl2sql:execute", "admin:settings"]
  }
}

// v2.0 (목표)
{
  "user": {
    "user_id": 1,
    "login_id": "admin",
    "role_code": "SYSTEM_ADMIN",
    "scope_type": "GLOBAL",
    "landing_page": "/admin/dashboard",
    "menus": [
      {
        "menu_code": "DASHBOARD",
        "menu_name": "대시보드",
        "menu_path": "/admin/dashboard",
        "menu_type": "PAGE",
        "icon": "dashboard",
        "depth": 1,
        "sort_order": 1,
        "can_create": false,
        "can_read": true,
        "can_update": false,
        "can_delete": false,
        "can_export": false
      }
    ]
  }
}
```

---

## 3. Step 1: auth_service.py

### 3.1 변경 요약

| 메서드 | 변경 내용 |
|--------|----------|
| `authenticate()` | 변경 없음 (tb_user 직접 조회) |
| `_handle_login_failure()` | 변경 없음 |
| `create_session()` | JWT 토큰 데이터에 `role_code` 단일, `roles`/`role_names`/`permissions` 제거, `UserInfo` 생성 변경 |
| `refresh_access_token()` | 동일하게 JWT 토큰 데이터 + `UserInfo` 생성 변경 |
| `logout()` | 변경 없음 |
| `get_user_with_permissions()` | ★ **전면 재작성** — v2.0 쿼리 |
| `change_password()` | 변경 없음 |

### 3.2 v2.0 전체 소스코드

```python
"""인증 서비스

위치: app/api/services/auth_service.py
로그인, 세션 관리, 토큰 갱신, 비밀번호 변경 비즈니스 로직
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.config import settings
from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security.password import hash_password, verify_password
from app.models.auth import MenuPermission, TokenResponse, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


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
                cur.execute("UPDATE tb_user SET locked_until = NULL, login_fail_count = 0 WHERE user_id = %s", (user["user_id"],))

        # 비밀번호 검증
        if not verify_password(password, user["password_hash"]):
            self._handle_login_failure(user["user_id"], user["login_fail_count"], request_id, login_id)
            raise APIException(ErrorCode.UNAUTHORIZED, "아이디 또는 비밀번호가 올바르지 않습니다")

        # 로그인 성공 → 실패 횟수 초기화 + last_login_at 갱신
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("UPDATE tb_user SET login_fail_count = 0, locked_until = NULL, last_login_at = NOW() WHERE user_id = %s", (user["user_id"],))

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
            cur.execute("UPDATE tb_user SET login_fail_count = %s, locked_until = %s WHERE user_id = %s", (new_count, locked_until, user_id))

    def create_session(self, user_id: int, ip: str, user_agent: str, request_id: str = "") -> TokenResponse:
        """세션 생성 — 권한 조회 + tb_user_session INSERT + 토큰 발급"""
        user_info = self.get_user_with_permissions(user_id, request_id)

        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)

        # JWT 토큰 데이터 구성 (v2.0: role_code 단일, permissions 제거)
        token_data = {
            "sub": str(user_id),
            "login_id": user_info["login_id"],
            "display_name": user_info["display_name"],
            "tenant_id": user_info["tenant_id"],
            "role_code": user_info["role_code"],
            "scope_type": user_info["scope_type"],
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
                role_code=user_info["role_code"],
                scope_type=user_info["scope_type"],
                landing_page=user_info["landing_page"],
                menus=user_info["menus"],
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
                "SELECT user_id, expires_at FROM tb_user_session WHERE session_id = %s AND refresh_token = %s",
                (session_id, refresh_token),
            )
            session = cur.fetchone()

        if not session:
            log_step(logger, request_id, "AUTH", "3", "REFRESH", "세션 없음 또는 토큰 불일치", session_id=session_id[:8] if session_id else "none")
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 세션입니다")

        # 3. 세션 만료 확인
        if datetime.now(timezone.utc) > session["expires_at"]:
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
            "role_code": user_info["role_code"],
            "scope_type": user_info["scope_type"],
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
                role_code=user_info["role_code"],
                scope_type=user_info["scope_type"],
                landing_page=user_info["landing_page"],
                menus=user_info["menus"],
            ),
        )

    def logout(self, user_id: int, request_id: str = "") -> bool:
        """로그아웃 — 해당 사용자의 모든 세션 삭제"""
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_user_session WHERE user_id = %s", (user_id,))
            deleted = cur.rowcount > 0

        log_step(logger, request_id, "AUTH", "4", "LOGOUT", "로그아웃", user_id=user_id, deleted=deleted)
        return deleted

    def get_user_with_permissions(self, user_id: int, request_id: str = "") -> Dict[str, Any]:
        """
        사용자 정보 + 역할 + 메뉴 권한 일괄 조회 (v2.0)

        v2.0 변경:
        - tb_user.role_id FK로 역할 직접 JOIN (tb_user_role M:N 제거)
        - tb_user_menu + tb_menu JOIN으로 메뉴 CRUD 권한 조회 (tb_role_permission 제거)
        - 반환값에 role_code(단일), landing_page, menus(MenuPermission 리스트) 포함
        """
        # 1. 사용자 + 역할 조회 (tb_user.role_id → tb_role 직접 JOIN)
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id, "
                "u.is_superuser, u.is_active, "
                "r.role_code, r.role_name, r.scope_type, r.landing_page "
                "FROM tb_user u "
                "JOIN tb_role r ON r.role_id = u.role_id "
                "WHERE u.user_id = %s",
                (user_id,),
            )
            user_row = cur.fetchone()

        if not user_row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

        user = dict(user_row)
        if not user["is_active"]:
            raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

        # 2. 메뉴 권한 조회 (tb_user_menu + tb_menu JOIN)
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT m.menu_code, m.menu_name, m.menu_path, m.menu_type, m.icon, "
                "m.depth, m.sort_order, pm.menu_code AS parent_menu_code, "
                "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export "
                "FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id "
                "WHERE um.user_id = %s AND m.is_active = true "
                "ORDER BY m.depth, m.sort_order",
                (user_id,),
            )
            menu_rows = cur.fetchall()

        menus = [
            MenuPermission(
                menu_code=row["menu_code"],
                menu_name=row["menu_name"],
                menu_path=row["menu_path"],
                menu_type=row["menu_type"],
                icon=row["icon"],
                parent_menu_code=row["parent_menu_code"],
                depth=row["depth"],
                sort_order=row["sort_order"],
                can_create=row["can_create"],
                can_read=row["can_read"],
                can_update=row["can_update"],
                can_delete=row["can_delete"],
                can_export=row["can_export"],
            )
            for row in menu_rows
        ]

        user["menus"] = menus

        log_step(logger, request_id, "AUTH", "2", "PERMISSION", "권한 조회 완료", user_id=user_id, role=user["role_code"], menus=len(menus), scope=user["scope_type"])
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
            cur.execute("UPDATE tb_user SET password_hash = %s, updated_at = NOW() WHERE user_id = %s", (new_hash, user_id))

        log_step(logger, request_id, "AUTH", "5", "PASSWORD", "비밀번호 변경 완료", user_id=user_id)
        return True


# 싱글톤 인스턴스
auth_service = AuthService()
```

### 3.3 v1.0 → v2.0 핵심 변경 상세

#### 3.3.1 get_user_with_permissions() — 쿼리 전면 재작성

```
v1.0 (제거):
  tb_user_role ur → tb_role r → tb_role_permission rp → tb_permission p
  → roles: Set[str], permissions: Set[str], max_scope 계산

v2.0 (신규):
  쿼리 1: tb_user u JOIN tb_role r → role_code, scope_type, landing_page (단일 역할)
  쿼리 2: tb_user_menu um JOIN tb_menu m → menus 리스트 (MenuPermission 객체)

변경 이유:
  - tb_user_role, tb_role_permission, tb_permission 테이블이 v2.0 DDL에서 삭제됨
  - 사용자:역할 = 1:N (tb_user.role_id FK 직접 보유)
  - 권한 = 메뉴별 CRUD (tb_user_menu 유일한 권한 테이블)
```

#### 3.3.2 create_session() / refresh_access_token() — JWT 데이터 변경

```python
# v1.0 (제거)
token_data = {
    "roles": user_info["roles"],           # List[str] → 제거
    "role_names": user_info["role_names"], # List[str] → 제거
    "permissions": user_info["permissions"], # List[str] → 제거
}

# v2.0 (신규)
token_data = {
    "role_code": user_info["role_code"],   # str (단일 역할)
    # menus는 JWT에 포함하지 않음 (로그인 응답으로만 전달)
}
```

#### 3.3.3 UserInfo 생성 변경

```python
# v1.0 (제거)
UserInfo(
    roles=user_info["roles"],
    role_names=user_info["role_names"],
    permissions=user_info["permissions"],
)

# v2.0 (신규)
UserInfo(
    role_code=user_info["role_code"],
    landing_page=user_info["landing_page"],
    menus=user_info["menus"],  # List[MenuPermission]
)
```

---

## 4. Step 2: routes/auth.py

### 4.1 변경 요약

| 엔드포인트 | 변경 내용 |
|------------|----------|
| `POST /login` | 변경 없음 (auth_service가 v2.0 TokenResponse 반환) |
| `POST /logout` | 변경 없음 |
| `POST /refresh` | 변경 없음 (auth_service가 v2.0 TokenResponse 반환) |
| `GET /me` | UserInfo 생성 변경 (role_code, landing_page, menus) |
| `PUT /me/password` | 변경 없음 |

### 4.2 v2.0 전체 소스코드

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
from app.models.auth import LoginRequest, RefreshRequest, PasswordChangeRequest, UserContext, UserInfo
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """로그인 — JWT 토큰 발급 + 메뉴 권한 목록"""
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
    """Access Token 갱신 (최신 역할/메뉴 권한 반영)"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    token_response = auth_service.refresh_access_token(body.refresh_token, request_id)
    return success_response(token_response.model_dump())


@router.get("/me")
async def get_me(request: Request, current_user: UserContext = Depends(get_current_active_user)):
    """현재 사용자 정보 + 메뉴 권한 조회 (DB 최신 데이터)"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    user_data = auth_service.get_user_with_permissions(current_user.user_id, request_id)
    user_info = UserInfo(
        user_id=user_data["user_id"],
        login_id=user_data["login_id"],
        display_name=user_data["display_name"],
        tenant_id=user_data["tenant_id"],
        role_code=user_data["role_code"],
        scope_type=user_data["scope_type"],
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
```

### 4.3 엔드포인트별 인증 요구사항

| Endpoint | 인증 | Depends 사용 | 비고 |
|----------|------|-------------|------|
| `POST /login` | 불필요 | - | 비밀번호로 인증 |
| `POST /logout` | 필수 | `get_current_active_user` | |
| `POST /refresh` | 불필요 | - | Refresh Token을 body로 수신 |
| `GET /me` | 필수 | `get_current_active_user` | DB 최신 데이터 반환 |
| `PUT /me/password` | 필수 | `get_current_active_user` | |

### 4.4 GET /me 변경 상세

```python
# v1.0 (제거)
user_info = UserInfo(
    roles=user_data["roles"],           # List[str] → 제거
    role_names=user_data["role_names"], # List[str] → 제거
    permissions=user_data["permissions"], # List[str] → 제거
)

# v2.0 (신규)
user_info = UserInfo(
    role_code=user_data["role_code"],     # str (단일 역할)
    landing_page=user_data["landing_page"], # str (랜딩 페이지)
    menus=user_data["menus"],              # List[MenuPermission]
)
```

---

## 5. Step 3: middleware/auth.py

### 5.1 변경 요약

- `UserContext` 생성 시 `roles`/`permissions` → `role_code` 단일로 변경
- 선택적 모드(Phase 3a) 유지 (변경 없음)

### 5.2 v2.0 전체 소스코드

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
    """인증 미들웨어 (선택적 모드 — Phase 3a)"""

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
            token = auth_header[7:]
            try:
                payload = verify_token(token)
                if payload.token_type == "access":
                    request.state.current_user = UserContext(
                        user_id=int(payload.sub),
                        login_id=payload.login_id,
                        display_name=payload.display_name,
                        tenant_id=payload.tenant_id,
                        is_superuser=payload.is_superuser,
                        role_code=payload.role_code,
                        scope_type=payload.scope_type,
                    )
            except Exception:
                # Phase 3a: 토큰 검증 실패해도 차단하지 않음
                pass

        return await call_next(request)
```

### 5.3 v1.0 → v2.0 변경 상세

```python
# v1.0 (제거)
request.state.current_user = UserContext(
    ...,
    roles=payload.roles,           # List[str] → 제거
    permissions=payload.permissions, # List[str] → 제거
)

# v2.0 (신규)
request.state.current_user = UserContext(
    ...,
    role_code=payload.role_code,  # str (단일 역할)
    scope_type=payload.scope_type,
    # menus는 JWT에 포함되지 않음 → DB 조회로 처리
)
```

### 5.4 선택적 모드 동작 (변경 없음)

```
요청에 Authorization 헤더 있음:
  Bearer 토큰 유효 → request.state.current_user = UserContext(role_code=...)
  Bearer 토큰 무효 → request.state.current_user = None (차단 안함)

요청에 Authorization 헤더 없음:
  → request.state.current_user = None (차단 안함)

제외 경로:
  → middleware 자체를 건너뜀 (BaseMiddleware.should_skip)
```

---

## 6. Step 4: main.py 확인

### 6.1 현행 상태 — 변경 불필요

`app/main.py`는 이미 v2.0 구조로 되어 있어 변경이 필요 없습니다:

```python
# 이미 등록됨 — 변경 불필요
from app.middleware import LoggingMiddleware, HistoryMiddleware, AuthMiddleware

app.add_middleware(HistoryMiddleware)
app.add_middleware(AuthMiddleware)       # ← 이미 등록
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)          # ← 이미 등록
```

### 6.2 미들웨어 실행 순서 (최종)

```
요청 순서: CORSMiddleware → LoggingMiddleware → AuthMiddleware → HistoryMiddleware → Handler
응답 순서: Handler → HistoryMiddleware → AuthMiddleware → LoggingMiddleware → CORSMiddleware

역할:
  CORS       → 브라우저 Same-Origin 정책 처리
  Logging    → request_id 생성 + 요청/응답 로깅
  Auth       → Bearer 토큰 → UserContext(role_code, scope_type) (선택적 모드)
  History    → API 이력 DB 저장
  Handler    → 실제 API 로직
```

---

## 7. 검증 체크리스트

### 7.1 단위 검증 항목

- [x] `auth_service.authenticate()` — 올바른 비밀번호 → 성공
- [x] `auth_service.authenticate()` — 틀린 비밀번호 → UNAUTHORIZED
- [x] `auth_service.authenticate()` — 존재하지 않는 ID → UNAUTHORIZED
- [x] `auth_service.authenticate()` — 비활성 계정 → UNAUTHORIZED
- [x] `auth_service.authenticate()` — 5회 실패 → ACCOUNT_LOCKED
- [x] `auth_service.authenticate()` — 잠금 해제 시간 경과 후 → 잠금 자동 해제
- [x] `auth_service.create_session()` — TokenResponse에 `user.role_code` (단일 문자열) 포함 확인
- [x] `auth_service.create_session()` — TokenResponse에 `user.menus` (List[MenuPermission]) 포함 확인
- [x] `auth_service.create_session()` — TokenResponse에 `user.landing_page` 포함 확인
- [x] `auth_service.get_user_with_permissions()` — `role_code`, `scope_type`, `landing_page` 반환 확인
- [x] `auth_service.get_user_with_permissions()` — `menus` 리스트에 `can_create`~`can_export` CRUD 포함 확인
- [x] `auth_service.get_user_with_permissions()` — admin 사용자 → 메뉴 14개 확인
- [x] `auth_service.get_user_with_permissions()` — user01 사용자 → 메뉴 4개 확인
- [x] `auth_service.refresh_access_token()` — 유효한 Refresh Token → 새 Access Token
- [x] `auth_service.refresh_access_token()` — 만료된 Refresh Token → SESSION_EXPIRED
- [x] `auth_service.change_password()` — 변경 후 새 비밀번호로 로그인 성공

### 7.2 통합 검증 (curl)

```bash
# 1. 로그인 — role_code, landing_page, menus 포함 확인
curl -X POST http://localhost:19090/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login_id": "admin", "password": "admin123!"}'

# 응답 확인 포인트:
# - user.role_code = "SYSTEM_ADMIN" (단일 문자열, 배열 아님)
# - user.landing_page = "/admin/dashboard"
# - user.menus = [{menu_code: "DASHBOARD", can_read: true, ...}, ...]
# - user.menus 개수 = 14 (admin 계정)
# - roles, role_names, permissions 필드 없음

# 2. 내 정보 조회 — 최신 메뉴 권한
curl http://localhost:19090/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 3. 토큰 갱신 — 최신 role_code/menus 반영
curl -X POST http://localhost:19090/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'

# 4. 로그아웃
curl -X POST http://localhost:19090/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"

# 5. 비밀번호 변경
curl -X PUT http://localhost:19090/api/v1/auth/me/password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "admin123!", "new_password": "NewAdmin1!"}'
```

### 7.3 기존 API 하위호환 확인

```bash
# 인증 미들웨어 선택적 모드 확인 — 토큰 없이 기존 API 정상 동작
curl -X POST http://localhost:19090/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "재택근무 정책", "mode": "rag"}'

# Agent API도 토큰 없이 동작 확인
curl -X POST http://localhost:19090/api/v1/agent/search \
  -H "Content-Type: application/json" \
  -d '{"question": "2024년 입사자는 몇 명이야?"}'
```

### 7.4 계정별 메뉴 수 확인

| 계정 | 역할 | 예상 메뉴 수 | 확인 |
|------|------|:---:|:---:|
| admin | SYSTEM_ADMIN | 14 | [ ] |
| tenant_admin | TENANT_ADMIN | 9 | [ ] |
| user01 | USER | 4 | [ ] |

---

## 8. 다음 단계

### 8.1 Phase 4 Preview: 관리 API (CRUD)

Phase 4에서는 **사용자/역할/메뉴/테넌트 관리 API**를 v2.0으로 마이그레이션합니다:

| 작업 | 설명 |
|------|------|
| `user_service.py` | 사용자 CRUD + `tb_user_menu` 메뉴 권한 할당 (v1.0 → v2.0) |
| `role_service.py` | 역할 CRUD (v1.0 `tb_role_permission` 제거) |
| `menu_service.py` | ★ 신규: 메뉴 트리 CRUD |
| `tenant_service.py` | 이미 v2.0 완료 |
| `routes/users.py` | `require_permission` → `require_menu_permission` 전환 |
| `routes/roles.py` | 권한 할당 API 제거, 메뉴 트리 연동 |
| `routes/menus.py` | ★ 신규: 메뉴 관리 API |

### 8.2 Phase 의존 관계

```
Phase 1: DB 테이블 + Pydantic 모델 (v2.0)
    │
    ▼
Phase 2: Core Security (JWT, Dependencies, Permission v2.0)
    │
    ▼
Phase 3: Auth API + Auth Middleware (v2.0)     ← 현재 문서
    │
    ├───────────────────────┐
    ▼                       ▼
Phase 4:                Phase 5:
관리 API (CRUD)         NL2SQL 필터 +
+ 메뉴 관리             프론트엔드
```

---

## 부록 A: v1.0에서 제거되는 코드

### auth_service.py에서 제거

| 위치 | 제거 코드 | 대체 |
|------|----------|------|
| `get_user_with_permissions()` | `tb_user_role` JOIN | `tb_user.role_id` → `tb_role` 직접 JOIN |
| `get_user_with_permissions()` | `tb_role_permission` JOIN | 삭제 (메뉴 권한은 `tb_user_menu`) |
| `get_user_with_permissions()` | `tb_permission` JOIN | 삭제 |
| `get_user_with_permissions()` | `roles: Set[str]`, `role_names: Set[str]` | `role_code: str` (단일) |
| `get_user_with_permissions()` | `permissions: Set[str]` | `menus: List[MenuPermission]` |
| `get_user_with_permissions()` | `_SCOPE_PRIORITY` 기반 max_scope 계산 | 불필요 (역할이 1개이므로 scope_type 직접 사용) |
| `create_session()` | `token_data["roles"]`, `["role_names"]`, `["permissions"]` | `token_data["role_code"]` |
| `create_session()` | `UserInfo(roles=..., role_names=..., permissions=...)` | `UserInfo(role_code=..., landing_page=..., menus=...)` |
| `refresh_access_token()` | 동일 변경 | 동일 변경 |

### middleware/auth.py에서 제거

| 위치 | 제거 코드 | 대체 |
|------|----------|------|
| `process_request()` | `UserContext(roles=..., permissions=...)` | `UserContext(role_code=..., scope_type=...)` |

### routes/auth.py에서 제거

| 위치 | 제거 코드 | 대체 |
|------|----------|------|
| `get_me()` | `UserInfo(roles=..., role_names=..., permissions=...)` | `UserInfo(role_code=..., landing_page=..., menus=...)` |

## 부록 B: 파일별 import 변경

### auth_service.py

```python
# v1.0 (변경 전)
from app.models.auth import TokenResponse, UserInfo

# v2.0 (변경 후) — MenuPermission 추가
from app.models.auth import MenuPermission, TokenResponse, UserInfo
```

### middleware/auth.py

```python
# 변경 없음 (UserContext import 유지, 내부 필드만 변경)
from app.models.auth import UserContext
```

### routes/auth.py

```python
# 변경 없음 (import 동일, UserInfo 생성 필드만 변경)
from app.models.auth import LoginRequest, RefreshRequest, PasswordChangeRequest, UserContext, UserInfo
```
