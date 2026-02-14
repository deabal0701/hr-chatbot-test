# Phase 2 구현 가이드: Core Security 모듈 (JWT + 비밀번호 + 의존성) v2.0

> **문서 버전**: 2.2
> **작성일**: 2026-02-12
> **수정일**: 2026-02-14
> **상태**: ✅ 구현 완료
> **현행화**: 2026-02-14 (실제 구현 코드 기반 상태 반영)
> **상위 문서**: `docs/design/user_permission_system.md` (v2.1)
> **선행 조건**: Phase 1 완료 (DB 테이블 DDL + Pydantic 모델 v2.0 마이그레이션)
> **목적**: Phase 2(Core Security 모듈)의 v1.0 → v2.0 마이그레이션 절차를 코드 레벨에서 상세 설명

---

## 목차

1. [Phase 2 개요](#1-phase-2-개요)
2. [현행 코드 상태 분석](#2-현행-코드-상태-분석)
3. [Step 1: `app/core/security/password.py` — 비밀번호 해싱 (완료)](#3-step-1-password)
4. [Step 2: `app/core/security/jwt.py` — JWT 토큰 관리 (v1.0→v2.0)](#4-step-2-jwt)
5. [Step 3: `app/core/security/dependencies.py` — FastAPI 의존성 주입 (v1.0→v2.0)](#5-step-3-dependencies)
6. [Step 4: `app/core/security/permission.py` — 권한 검사 (v1.0→v2.0)](#6-step-4-permission)
7. [검증 체크리스트](#7-검증-체크리스트)
8. [다음 단계 (Phase 3 Preview)](#8-다음-단계)

---

## 1. Phase 2 개요

### 1.1 무엇을 하는가

Phase 2는 인증/인가의 **핵심 유틸리티**를 v2.0으로 마이그레이션하는 단계입니다.

```
Phase 2 산출물:
  [OK]  app/core/security/__init__.py       ← 빈 파일 (이미 존재)
  [OK]  app/core/security/password.py       ← bcrypt 해싱/검증 (이미 v2.0 완료)
  [MOD] app/core/security/jwt.py            ← TokenPayload: roles/permissions → role_code
  [MOD] app/core/security/dependencies.py   ← UserContext 생성: roles/permissions 제거
  [MOD] app/core/security/permission.py     ← require_permission → require_menu_permission (★ 핵심)
```

### 1.2 v1.0 → v2.0 핵심 변경 요약

| 모듈 | v1.0 (현행) | v2.0 (목표) | 변경 이유 |
|------|------------|------------|----------|
| `password.py` | bcrypt 직접 사용 | **변경 없음** ✅ | 비밀번호 처리는 권한 체계와 무관 |
| `jwt.py` | `roles: List[str]`, `permissions: List[str]` | `role_code: str` | M:N → 1:N 전환, permission 코드 폐기 |
| `dependencies.py` | `UserContext(roles=..., permissions=...)` | `UserContext(role_code=...)` | auth.py 모델 변경 연쇄 |
| `permission.py` | `require_permission("admin:users")` → `has_all_permissions()` | `require_menu_permission("USER_MGMT", "read")` → **DB 조회** | 메뉴 기반 권한 체크 전환 (★) |

### 1.3 핵심 설계 결정

```
v1.0 설계:
┌──────────────────────────────────────────────────────────────────┐
│  get_current_user = JWT 페이로드의 roles/permissions로 권한 체크  │
│  모든 권한 정보가 JWT에 포함 → DB 조회 없이 체크 가능             │
│  단점: 권한 변경 시 Access Token 만료까지 반영 안 됨 (최대 30분)  │
└──────────────────────────────────────────────────────────────────┘

v2.0 설계:
┌──────────────────────────────────────────────────────────────────┐
│  get_current_user = JWT에서 role_code + scope_type만 추출         │
│                                                                   │
│  메뉴 CRUD 권한은 require_menu_permission()에서 DB 실시간 조회    │
│  → 관리자가 권한 변경하면 즉시 반영 (DB 기반)                     │
│                                                                   │
│  장점: 권한 변경 즉시 반영, 메뉴 단위 세밀한 CRUD 제어            │
│  단점: 보호된 API 호출 시 DB 1회 조회 필요                        │
│        → 캐시 도입으로 해소 가능 (Phase 5)                        │
└──────────────────────────────────────────────────────────────────┘
```

### 1.4 파일 간 의존 관계

```
password.py         (standalone — bcrypt만 사용)
                     ↑ 없음
jwt.py              → app.config (settings)
                    → app.core.errors (APIException, ErrorCode)
                     ↑
dependencies.py     → jwt.py (verify_token)
                    → app.models.auth (UserContext)  ← Phase 1에서 v2.0으로 변경됨
                    → app.core.errors (APIException, ErrorCode)
                     ↑
permission.py       → dependencies.py (get_current_active_user)
                    → app.models.auth (UserContext)
                    → app.core.errors (APIException, ErrorCode)
                    → app.core.database.connection (db_manager)  ← ★ v2.0 신규 의존

※ 순환 import 없음
```

### 1.5 Phase 1에서 사용하는 항목

| Phase 1 산출물 | Phase 2에서 사용하는 곳 | 비고 |
|---------------|----------------------|------|
| `UserContext` (app/models/auth.py) | dependencies.py, permission.py | v2.0: `role_code` 단일, `permissions` 제거 |
| `settings.secret_key` (app/config.py) | jwt.py | 변경 없음 |
| `settings.algorithm` | jwt.py | 변경 없음 |
| `settings.access_token_expire_minutes` | jwt.py | 변경 없음 |
| `settings.jwt_refresh_token_expire_days` | jwt.py | 변경 없음 |
| `ErrorCode.UNAUTHORIZED` (app/core/errors/) | jwt.py, dependencies.py | 변경 없음 |
| `ErrorCode.FORBIDDEN` | permission.py | 변경 없음 |
| `db_manager` (app/core/database/) | permission.py | ★ v2.0 신규 — 메뉴 권한 DB 조회 |

---

## 2. 현행 코드 상태 분석

### 2.1 파일별 현행 상태

| # | 파일 | 현재 버전 | 상태 | 비고 |
|---|------|-----------|------|------|
| 1 | `app/core/security/__init__.py` | — | ✅ 완료 | 빈 파일, 변경 없음 |
| 2 | `app/core/security/password.py` | v2.0 | ✅ 완료 | bcrypt 직접 사용, 변경 없음 |
| 3 | `app/core/security/jwt.py` | v2.0 | ✅ 구현 완료 | `role_code` 기반 토큰 페이로드 전환 완료 |
| 4 | `app/core/security/dependencies.py` | v2.0 | ✅ 구현 완료 | `UserContext` v2.0 생성부 구현 완료 |
| 5 | `app/core/security/permission.py` | v2.0 | ✅ 구현 완료 | 메뉴 기반 권한 체크 (DB 조회) 구현 완료 |

### 2.2 현행 v1.0 코드의 문제점

#### jwt.py — permission 코드 배열 포함 (v1.0)

```python
# 현행 (v1.0): roles/permissions 리스트 보유
class TokenPayload(BaseModel):
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")
```

**문제**: `tb_permission`, `tb_role_permission` 테이블이 v2.0 DDL에서 삭제되어 permissions 배열을 채울 수 없음. roles도 M:N에서 1:N으로 변경되어 배열이 아닌 단일 값이어야 함.

#### dependencies.py — v1.0 UserContext 생성 (v1.0)

```python
# 현행 (v1.0): roles/permissions 매핑
return UserContext(
    ...,
    roles=payload.roles,           # ← v2.0 UserContext에 없는 필드
    permissions=payload.permissions, # ← v2.0 UserContext에 없는 필드
)
```

**문제**: Phase 1에서 `UserContext`가 v2.0으로 변경되면(`roles`/`permissions` 제거, `role_code` 추가), 이 코드가 즉시 런타임 에러 발생.

#### permission.py — permission 코드 기반 체크 (v1.0)

```python
# 현행 (v1.0): permission 코드로 권한 체크
def require_permission(*required_permissions: str):
    if not current_user.has_all_permissions(*required_permissions):
        raise APIException(ErrorCode.FORBIDDEN, ...)

def require_any_permission(*required_permissions: str):
    if not current_user.has_any_permission(*required_permissions):
        raise APIException(ErrorCode.FORBIDDEN, ...)
```

**문제**: v2.0 `UserContext`에서 `has_all_permissions()`, `has_any_permission()` 메서드가 제거되어 호출 불가. `tb_permission` 테이블도 삭제되어 permission 코드 자체가 존재하지 않음.

### 2.3 v1.0 → v2.0 변경 요약

| 구분 | v1.0 (현행) | v2.0 (목표) |
|------|:---:|:---:|
| JWT payload 권한 | `roles: ["SYSTEM_ADMIN"]`, `permissions: ["admin:users"]` | `role_code: "SYSTEM_ADMIN"` (단일) |
| UserContext 생성 | `roles=payload.roles, permissions=payload.permissions` | `role_code=payload.role_code` |
| 권한 체크 방식 | `has_all_permissions("admin:users")` (JWT에서 체크) | `require_menu_permission("USER_MGMT", "read")` (**DB 조회**) |
| 권한 체크 대상 | permission 코드 문자열 | 메뉴 코드 + CRUD 액션 |
| superuser bypass | `UserContext.has_permission()` 내부 | `require_menu_permission()` 내부 |

---

## 3. Step 1: `app/core/security/password.py`

### 3.1 현행 상태

**이미 v2.0 완료. 변경 불필요.** ✅

비밀번호 해싱/검증은 권한 체계와 무관하므로, v1.0 → v2.0 전환에 영향이 없습니다.

### 3.2 현행 소스코드

```python
"""
비밀번호 해싱 및 검증 유틸리티

위치: app/core/security/password.py
bcrypt 알고리즘을 사용한 비밀번호 처리
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """비밀번호를 bcrypt로 해싱 (cost factor = 12)"""
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시 비교"""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
```

### 3.3 코드 설명

- **bcrypt 직접 사용**: passlib은 bcrypt 5.x와 호환성 문제가 있어(`AttributeError: module 'bcrypt' has no attribute '__about__'`) bcrypt 라이브러리를 직접 사용
- **cost factor 12**: `bcrypt.gensalt(rounds=12)` → 2^12 = 4096 라운드. 보안과 성능의 균형점
- **반환값**: `$2b$12$...` 형태의 60자 문자열 (salt 22자 + hash 31자 포함)
- **같은 비밀번호라도 매번 다른 해시 생성** (salt가 다르므로)

### 3.4 사용처

```
사용자 생성 (Phase 4):
  password (UserCreate) → hash_password() → tb_user.password_hash

로그인 (Phase 3):
  password (LoginRequest) + tb_user.password_hash → verify_password() → True/False
```

---

## 4. Step 2: `app/core/security/jwt.py`

### 4.1 현행 상태와 변경 사유

| 구분 | 현행 (v1.0) | 목표 (v2.0) | 변경 이유 |
|------|------------|------------|----------|
| `TokenPayload.roles` | `List[str]` | **제거** | M:N → 1:N 전환 |
| `TokenPayload.permissions` | `List[str]` | **제거** | `tb_permission` 테이블 삭제 |
| (없음) | — | `role_code: str` 추가 | 단일 역할 코드 |
| `create_access_token` | `roles`, `permissions` 포함 | `role_code` 포함 | payload 구조 변경 |
| `create_refresh_token` | 변경 없음 | 변경 없음 | minimal payload 유지 |
| `verify_token` | 변경 없음 | 변경 없음 | Pydantic이 자동 처리 |

### 4.2 v2.0 전체 소스코드

```python
"""
JWT 토큰 생성 및 검증 유틸리티

위치: app/core/security/jwt.py
python-jose를 사용한 Access/Refresh Token 관리
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings
from app.core.errors import APIException, ErrorCode


# ===================================
# JWT 페이로드 모델 (내부 전용)
# ===================================

class TokenPayload(BaseModel):
    """JWT 토큰 디코딩 결과 (v2.0 - 메뉴 기반)"""
    sub: str = Field(..., description="Subject (user_id 문자열)")
    login_id: str = Field(default="", description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="테넌트 ID")
    role_code: str = Field(default="USER", description="역할 코드 (SYSTEM_ADMIN, TENANT_ADMIN, USER)")
    scope_type: str = Field(default="USER", description="데이터 범위")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    exp: Optional[int] = Field(None, description="만료 시간 (Unix timestamp)")
    iat: Optional[int] = Field(None, description="발급 시간 (Unix timestamp)")
    token_type: str = Field(default="access", description="토큰 타입 (access, refresh)")
    session_id: Optional[str] = Field(None, description="세션 ID (refresh token only)")


# ===================================
# 토큰 생성
# ===================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Access Token 생성"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": now, "token_type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Refresh Token 생성 (minimal payload: sub + session_id)"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))
    to_encode.update({"exp": expire, "iat": now, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


# ===================================
# 토큰 검증
# ===================================

def verify_token(token: str) -> TokenPayload:
    """JWT 토큰 검증 및 페이로드 반환"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str = payload.get("sub")
        if sub is None:
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
        return TokenPayload(**payload)
    except JWTError:
        raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
```

### 4.3 v1.0 → v2.0 핵심 변경 포인트

#### 4.3.1 TokenPayload 변경 (diff)

```diff
 class TokenPayload(BaseModel):
-    """JWT 토큰 디코딩 결과"""
+    """JWT 토큰 디코딩 결과 (v2.0 - 메뉴 기반)"""
     sub: str = Field(..., description="Subject (user_id 문자열)")
     login_id: str = Field(default="", description="로그인 ID")
     display_name: Optional[str] = Field(None, description="표시 이름")
     tenant_id: Optional[int] = Field(None, description="테넌트 ID")
-    scope_type: str = Field(default="USER", description="데이터 범위")
-    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
-    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")
+    role_code: str = Field(default="USER", description="역할 코드 (SYSTEM_ADMIN, TENANT_ADMIN, USER)")
+    scope_type: str = Field(default="USER", description="데이터 범위")
     is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
```

- `roles: List[str]` → **제거**: 사용자당 역할이 하나이므로 `role_code: str`로 대체
- `permissions: List[str]` → **제거**: permission 코드 체계가 메뉴 기반으로 전환, JWT에 포함하지 않음
- `role_code: str` → **추가**: 단일 역할 코드 (SYSTEM_ADMIN, TENANT_ADMIN, USER)

#### 4.3.2 import 변경

```diff
-from typing import List, Optional
+from typing import Optional
```

- `List` import 제거: `roles`/`permissions` 필드가 없으므로 더 이상 필요 없음

#### 4.3.3 create_access_token/create_refresh_token/verify_token

이 세 함수는 **코드 변경 없음**. `data` dict를 받아서 그대로 인코딩하므로, 호출자(Phase 3 auth_service.py)가 전달하는 데이터가 바뀌면 자동으로 반영됨.

### 4.4 Phase 3에서의 호출 예시

```python
# auth_service.py (Phase 3에서 v2.0으로 변경)
access_token = create_access_token({
    "sub": str(user_id),
    "login_id": user_info["login_id"],
    "display_name": user_info["display_name"],
    "tenant_id": user_info["tenant_id"],
    "role_code": user_info["role_code"],         # ★ v2.0: 단일 역할 코드
    "scope_type": user_info["scope_type"],
    "is_superuser": user_info["is_superuser"],
    # roles, permissions → 제거됨
})

# Refresh Token은 변경 없음 (minimal payload)
refresh_token = create_refresh_token({
    "sub": str(user_id),
    "session_id": session_id,
})
```

---

## 5. Step 3: `app/core/security/dependencies.py`

### 5.1 현행 상태와 변경 사유

| 함수 | 현행 (v1.0) | 목표 (v2.0) | 변경 이유 |
|------|------------|------------|----------|
| `get_current_user` | `UserContext(roles=..., permissions=...)` | `UserContext(role_code=...)` | Phase 1 `UserContext` v2.0 연쇄 |
| `get_current_active_user` | pass-through | **변경 없음** | |
| `get_optional_user` | `UserContext(roles=..., permissions=...)` | `UserContext(role_code=...)` | Phase 1 `UserContext` v2.0 연쇄 |

### 5.2 v2.0 전체 소스코드

```python
"""
FastAPI 인증 의존성 주입

위치: app/core/security/dependencies.py
HTTP 요청의 Bearer 토큰에서 UserContext를 추출하는 Depends 함수
"""
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import APIException, ErrorCode
from app.core.security.jwt import verify_token
from app.models.auth import UserContext


# Bearer 토큰 추출기
_bearer_scheme = HTTPBearer(auto_error=True)
_bearer_scheme_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserContext:
    """Bearer 토큰에서 현재 사용자 추출 (필수 인증)"""
    payload = verify_token(credentials.credentials)

    if payload.token_type != "access":
        raise APIException(ErrorCode.UNAUTHORIZED, "Access Token이 필요합니다")

    return UserContext(
        user_id=int(payload.sub),
        login_id=payload.login_id,
        display_name=payload.display_name,
        tenant_id=payload.tenant_id,
        is_superuser=payload.is_superuser,
        role_code=payload.role_code,
        scope_type=payload.scope_type,
    )


async def get_current_active_user(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    """활성 사용자 검증"""
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme_optional),
) -> Optional[UserContext]:
    """선택적 인증 (토큰 없으면 None, 유효하지 않아도 None)"""
    if credentials is None:
        return None
    try:
        payload = verify_token(credentials.credentials)
        if payload.token_type != "access":
            return None
        return UserContext(
            user_id=int(payload.sub),
            login_id=payload.login_id,
            display_name=payload.display_name,
            tenant_id=payload.tenant_id,
            is_superuser=payload.is_superuser,
            role_code=payload.role_code,
            scope_type=payload.scope_type,
        )
    except Exception:
        return None
```

### 5.3 v1.0 → v2.0 핵심 변경 포인트

#### 5.3.1 get_current_user 변경 (diff)

```diff
     return UserContext(
         user_id=int(payload.sub),
         login_id=payload.login_id,
         display_name=payload.display_name,
         tenant_id=payload.tenant_id,
         is_superuser=payload.is_superuser,
+        role_code=payload.role_code,
         scope_type=payload.scope_type,
-        roles=payload.roles,
-        permissions=payload.permissions,
     )
```

- `roles=payload.roles` → **제거**: v2.0 `UserContext`에 `roles` 필드 없음
- `permissions=payload.permissions` → **제거**: v2.0 `UserContext`에 `permissions` 필드 없음
- `role_code=payload.role_code` → **추가**: v2.0 `UserContext`에 추가된 단일 역할 코드

#### 5.3.2 get_optional_user 변경

`get_current_user`와 동일한 변경 적용 (`roles`/`permissions` → `role_code`).

#### 5.3.3 get_current_active_user

**변경 없음**. pass-through 함수이므로 UserContext 구조 변경의 영향을 받지 않음.

### 5.4 코드 상세 설명

#### HTTPBearer — FastAPI 보안 스키마

```python
_bearer_scheme = HTTPBearer(auto_error=True)
_bearer_scheme_optional = HTTPBearer(auto_error=False)
```

- **`auto_error=True`**: 토큰이 없으면 FastAPI가 자동으로 403 반환
- **`auto_error=False`**: 토큰이 없어도 `None` 반환 (선택적 인증)
- **OpenAPI 문서**: Swagger UI에 "Authorize" 버튼 자동 생성

#### Depends 실행 흐름

```
1. 클라이언트 요청: GET /api/v1/auth/me (Authorization: Bearer eyJ...)
2. FastAPI → _bearer_scheme → credentials 추출
3. FastAPI → get_current_user(credentials) → verify_token() → TokenPayload
4. TokenPayload → UserContext(role_code="SYSTEM_ADMIN", scope_type="GLOBAL")
5. FastAPI → get_current_active_user(current_user) → UserContext 반환
6. 핸들러 실행
```

---

## 6. Step 4: `app/core/security/permission.py`

### 6.1 현행 상태와 변경 사유

| 함수 | 현행 (v1.0) | 목표 (v2.0) | 변경 이유 |
|------|------------|------------|----------|
| `require_permission()` | `has_all_permissions()` 코드 기반 | **제거** | `has_all_permissions()` 메서드 삭제 |
| `require_any_permission()` | `has_any_permission()` 코드 기반 | **제거** | `has_any_permission()` 메서드 삭제 |
| `require_superuser()` | superuser 체크 | **유지** (변경 없음) | superuser bypass는 v2.0에서도 동일 |
| (없음) | — | `require_menu_permission()` ★ 신규 | 메뉴 + CRUD 기반 DB 조회 권한 체크 |

**이 파일이 Phase 2의 가장 큰 변경점**입니다. permission 코드 기반에서 메뉴 기반으로 완전히 전환됩니다.

### 6.2 v2.0 전체 소스코드

```python
"""
권한 검사 의존성 팩토리 (v2.0 - 메뉴 기반)

위치: app/core/security/permission.py
메뉴 코드 + CRUD 액션 기반 권한 검사 (DB 실시간 조회)
"""
from fastapi import Depends

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext


def require_menu_permission(menu_code: str, action: str = "read"):
    """
    메뉴 기반 권한 검사 의존성 팩토리

    Args:
        menu_code: 메뉴 코드 (예: "USER_MGMT", "DASHBOARD", "NL2SQL")
        action: CRUD 액션 (create, read, update, delete, export)

    Usage:
        @router.get("/users")
        async def list_users(
            current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
        ): ...

        @router.post("/users")
        async def create_user(
            current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "create")),
        ): ...
    """
    valid_actions = ("create", "read", "update", "delete", "export")
    if action not in valid_actions:
        raise ValueError(f"action은 {valid_actions} 중 하나여야 합니다: {action}")

    async def permission_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        # superuser bypass
        if current_user.is_superuser:
            return current_user

        # DB에서 메뉴 권한 조회
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT can_create, can_read, can_update, can_delete, can_export "
                "FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true",
                (current_user.user_id, menu_code),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"메뉴 권한 없음: {menu_code}")

        if not row[f"can_{action}"]:
            raise APIException(ErrorCode.FORBIDDEN, "해당 작업 권한이 없습니다", detail=f"메뉴: {menu_code}, 필요 권한: {action}")

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
```

### 6.3 v1.0 → v2.0 핵심 변경 포인트

#### 6.3.1 제거된 함수

| v1.0 함수 | 제거 이유 |
|-----------|----------|
| `require_permission(*required_permissions)` | `has_all_permissions()` 메서드 삭제, permission 코드 체계 폐기 |
| `require_any_permission(*required_permissions)` | `has_any_permission()` 메서드 삭제 |

#### 6.3.2 신규 함수: `require_menu_permission()`

**v2.0의 핵심 함수**입니다. 기존 permission 코드 체크를 완전히 대체합니다.

```python
# v1.0 → v2.0 사용 변경
# Before (v1.0):
Depends(require_permission("admin:users"))     # permission 코드 기반
Depends(require_any_permission("admin:users", "admin:settings"))

# After (v2.0):
Depends(require_menu_permission("USER_MGMT", "read"))    # 메뉴 코드 + CRUD 액션
Depends(require_menu_permission("USER_MGMT", "create"))
Depends(require_menu_permission("SETTINGS", "update"))
```

#### 6.3.3 DB 조회 쿼리

```sql
SELECT can_create, can_read, can_update, can_delete, can_export
FROM tb_user_menu um
JOIN tb_menu m ON m.menu_id = um.menu_id
WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true
```

- `tb_user_menu`과 `tb_menu`을 JOIN하여 해당 사용자의 메뉴 CRUD 권한 조회
- `is_active = true`: 비활성 메뉴는 권한이 있더라도 접근 불가
- 결과가 없으면 → "접근 권한이 없습니다" (메뉴 자체에 접근 불가)
- 결과가 있지만 `can_{action}`이 false → "해당 작업 권한이 없습니다" (메뉴 접근 가능하나 특정 CRUD 불가)

#### 6.3.4 superuser bypass

```python
if current_user.is_superuser:
    return current_user
```

- v1.0에서는 `UserContext.has_permission()` 내부에서 superuser 체크
- v2.0에서는 `require_menu_permission()` 내부에서 직접 체크
- superuser는 DB 조회 없이 즉시 통과

#### 6.3.5 신규 import

```diff
+from app.core.database.connection import db_manager
```

- v1.0에서는 DB 접근 없이 JWT payload만으로 권한 체크
- v2.0에서는 `tb_user_menu` 테이블에서 실시간 권한 조회 → `db_manager` import 필요

### 6.4 Phase 4에서의 사용 예시

```python
# app/api/routes/users.py (Phase 4에서 v2.0으로 변경)

from app.core.security.permission import require_menu_permission, require_superuser

# 사용자 목록 조회 — USER_MGMT 메뉴 read 권한 필요
@router.get("")
async def list_users(
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
): ...

# 사용자 생성 — USER_MGMT 메뉴 create 권한 필요
@router.post("")
async def create_user(
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "create")),
): ...

# 사용자 수정 — USER_MGMT 메뉴 update 권한 필요
@router.put("/{user_id}")
async def update_user(
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "update")),
): ...

# 사용자 삭제 — USER_MGMT 메뉴 delete 권한 필요
@router.delete("/{user_id}")
async def delete_user(
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "delete")),
): ...

# 메뉴 관리 — MENU_MGMT 메뉴 (SYSTEM_ADMIN만 접근 가능하도록 DDL에서 설정)
@router.get("/menus")
async def list_menus(
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "read")),
): ...

# 시스템 관리자 전용 기능 (메뉴 기반이 아닌 경우)
@router.delete("/system/cache")
async def clear_system_cache(
    current_user: UserContext = Depends(require_superuser()),
): ...
```

### 6.5 메뉴 코드 → 라우트 매핑 참고

| 메뉴 코드 | 라우트 | 설명 |
|-----------|--------|------|
| `DASHBOARD` | `/api/admin/v1/dashboard` | 대시보드 |
| `CHAT` | `/api/admin/v1/agent` | AI 채팅 |
| `NL2SQL` | `/api/v1/nl2sql` | NL2SQL 실행 |
| `RAG` | `/api/v1/rag` | RAG 검색 |
| `DOC_MGMT` | `/api/admin/v1/documents` | 문서 관리 |
| `HISTORY` | `/api/admin/v1/history` | 이력 조회 |
| `USER_MGMT` | `/api/admin/v1/users` | 사용자 관리 |
| `ROLE_MGMT` | `/api/admin/v1/roles` | 역할 관리 |
| `TENANT_MGMT` | `/api/admin/v1/tenants` | 테넌트 관리 |
| `MENU_MGMT` | `/api/admin/v1/menus` | 메뉴 관리 |
| `SETTINGS` | `/api/admin/v1/settings` | 설정 관리 |
| `CODE_MGMT` | `/api/admin/v1/codes` | 코드 관리 |

---

## 7. 검증 체크리스트

### 7.1 파일 존재 및 버전 확인

- [x] `app/core/security/__init__.py` 존재 (빈 파일)
- [x] `app/core/security/password.py` 존재 (v2.0 완료, 변경 없음)
- [x] `app/core/security/jwt.py` 존재 (v2.0으로 변경 완료)
- [x] `app/core/security/dependencies.py` 존재 (v2.0으로 변경 완료)
- [x] `app/core/security/permission.py` 존재 (v2.0으로 재작성 완료)

### 7.2 Python import 테스트

```python
# Conda 환경 활성화 후 실행
conda activate penv3.13-nlq

# 1. password.py import (변경 없음)
from app.core.security.password import hash_password, verify_password
hashed = hash_password("admin123!")
print(f"Hash: {hashed}")
print(f"Verify correct: {verify_password('admin123!', hashed)}")  # True
print(f"Verify wrong: {verify_password('wrong', hashed)}")        # False

# 2. jwt.py import (v2.0)
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token, TokenPayload
token = create_access_token({
    "sub": "1",
    "login_id": "admin",
    "tenant_id": None,
    "role_code": "SYSTEM_ADMIN",          # ★ v2.0: 단일 역할 코드
    "scope_type": "GLOBAL",
    "is_superuser": True,
    # roles, permissions → 제거됨
})
print(f"Token: {token[:50]}...")
payload = verify_token(token)
print(f"sub={payload.sub}, type={payload.token_type}, role_code={payload.role_code}")

# 3. dependencies.py import
from app.core.security.dependencies import get_current_user, get_current_active_user, get_optional_user
print("dependencies.py import OK")

# 4. permission.py import (v2.0)
from app.core.security.permission import require_menu_permission, require_superuser
checker = require_menu_permission("USER_MGMT", "read")
print(f"require_menu_permission returns: {type(checker).__name__}")  # function

# v1.0 잔존 확인 (이것들이 ImportError 나면 정상)
# from app.core.security.permission import require_permission      → ImportError ✅
# from app.core.security.permission import require_any_permission  → ImportError ✅

# 5. 통합 테스트: JWT → UserContext (v2.0)
from app.models.auth import UserContext
user_ctx = UserContext(
    user_id=int(payload.sub),
    login_id=payload.login_id,
    role_code=payload.role_code,          # ★ v2.0
    scope_type=payload.scope_type,
    is_superuser=payload.is_superuser,
    # roles, permissions → 없음
)
print(f"role_code: {user_ctx.role_code}")    # SYSTEM_ADMIN
print(f"is_global: {user_ctx.is_global}")    # True
print(f"scope_type: {user_ctx.scope_type}")  # GLOBAL

# 6. v1.0 잔존 필드 확인 (AttributeError 나면 정상)
# print(user_ctx.roles)            → AttributeError ✅
# print(user_ctx.permissions)      → AttributeError ✅
# print(user_ctx.has_permission)   → AttributeError ✅
```

### 7.3 검증 항목 요약

| 항목 | 검증 방법 | 기대 결과 |
|------|----------|----------|
| password 해싱 | `hash_password("test")` | `$2b$12$...` 형태 문자열 |
| password 검증 | `verify_password("test", hashed)` | True |
| 틀린 password | `verify_password("wrong", hashed)` | False |
| salt 동작 | 같은 입력 2회 해싱 | 서로 다른 해시 |
| access token 생성 | `create_access_token({...})` | JWT 문자열 |
| token 검증 | `verify_token(token)` | TokenPayload 객체 |
| **role_code 포함** | `payload.role_code` | `"SYSTEM_ADMIN"` |
| **roles 필드 없음** | `hasattr(payload, 'roles')` | `False` |
| **permissions 필드 없음** | `hasattr(payload, 'permissions')` | `False` |
| 만료 토큰 | 만료된 토큰으로 verify_token | APIException(UNAUTHORIZED) |
| 변조 토큰 | 변경된 토큰으로 verify_token | APIException(UNAUTHORIZED) |
| token_type 구분 | access vs refresh | 각각 다른 token_type 포함 |
| dependencies import | 3개 함수 import | 오류 없음 |
| **permission import** | `require_menu_permission`, `require_superuser` | 오류 없음 |
| **v1.0 permission 제거** | `require_permission`, `require_any_permission` import | ImportError |
| 팩토리 반환 타입 | `require_menu_permission("USER_MGMT", "read")` | callable(function) |
| **잘못된 action** | `require_menu_permission("X", "invalid")` | ValueError 발생 |

---

## 8. 다음 단계 (Phase 3 Preview)

Phase 2 완료 후 **Phase 3: 인증 서비스 + 인증 API v2.0 마이그레이션**을 진행합니다.

### 8.1 Phase 3에서 수정할 파일

```
[MOD] app/api/services/auth_service.py   ← 쿼리 전면 재작성 (★ 가장 큰 변경)
[MOD] app/api/routes/auth.py             ← UserInfo(role_code=..., menus=...) 생성
```

### 8.2 auth_service.py 주요 변경 (Preview)

```python
# 현행 (v1.0): tb_user_role, tb_role_permission, tb_permission JOIN
cur.execute(
    "SELECT DISTINCT r.role_code, r.role_name, r.scope_type, p.permission_code "
    "FROM tb_user_role ur "
    "JOIN tb_role r ON ur.role_id = r.role_id "
    "LEFT JOIN tb_role_permission rp ON r.role_id = rp.role_id "
    "LEFT JOIN tb_permission p ON rp.permission_id = p.permission_id "
    "WHERE ur.user_id = %s", (user_id,))

# 목표 (v2.0): tb_user.role_id → tb_role 직접 JOIN + tb_user_menu 별도 조회
cur.execute(
    "SELECT u.user_id, u.login_id, u.display_name, u.tenant_id, u.is_superuser, "
    "r.role_code, r.role_name, r.scope_type, r.landing_page "
    "FROM tb_user u "
    "JOIN tb_role r ON r.role_id = u.role_id "
    "WHERE u.user_id = %s", (user_id,))

# 메뉴 권한 별도 조회 (로그인 응답용)
cur.execute(
    "SELECT m.menu_code, m.menu_name, m.menu_path, m.menu_type, m.icon, "
    "m.depth, m.sort_order, pm.menu_code AS parent_menu_code, "
    "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export "
    "FROM tb_user_menu um "
    "JOIN tb_menu m ON m.menu_id = um.menu_id "
    "LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id "
    "WHERE um.user_id = %s AND m.is_active = true "
    "ORDER BY m.depth, m.sort_order", (user_id,))
```

### 8.3 Phase 의존 관계 (전체)

```
Phase 1: DB 테이블 + Pydantic 모델 (v2.0)
    │
    ▼
Phase 2: Core Security (JWT, Dependencies, Permission v2.0)  ← 현재 문서
    │
    ▼
Phase 3: Auth Service + Auth API (v2.0 모델 + 쿼리 재작성)
    │
    ├───────────────────────┐
    ▼                       ▼
Phase 4:                Phase 5:
관리 API (CRUD)         NL2SQL 필터 +
+ 메뉴 관리             프론트엔드
```

---

## 부록 A: JWT 토큰 구조 참고

### A.1 Access Token 페이로드 예시 (v2.0)

```json
{
  "sub": "1",
  "login_id": "admin",
  "display_name": "시스템 관리자",
  "tenant_id": null,
  "role_code": "SYSTEM_ADMIN",
  "scope_type": "GLOBAL",
  "is_superuser": true,
  "exp": 1739350800,
  "iat": 1739349000,
  "token_type": "access"
}
```

**v1.0과의 차이**:
```diff
 {
   "sub": "1",
   "login_id": "admin",
-  "scope_type": "GLOBAL",
-  "roles": ["SYSTEM_ADMIN"],
-  "permissions": ["nl2sql:execute", "nl2sql:view_all", "rag:search", "document:read", ...],
+  "role_code": "SYSTEM_ADMIN",
+  "scope_type": "GLOBAL",
   "is_superuser": true,
   ...
 }
```

- `roles` 배열 → `role_code` 단일 문자열 (1:N 전환)
- `permissions` 배열 → **완전 제거** (메뉴 기반 DB 조회로 대체)
- JWT payload 크기가 크게 감소 (permissions 배열이 없어짐)

### A.2 Refresh Token 페이로드 예시 (변경 없음)

```json
{
  "sub": "1",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "exp": 1739953800,
  "iat": 1739349000,
  "token_type": "refresh"
}
```

Refresh Token은 minimal payload이므로 v1.0 → v2.0 변경 없음.

---

## 부록 B: v1.0에서 제거된 항목

### B.1 jwt.py

| v1.0 필드/타입 | 제거 이유 |
|---------------|----------|
| `TokenPayload.roles: List[str]` | `role_code: str`로 대체 (1:N) |
| `TokenPayload.permissions: List[str]` | 메뉴 기반 DB 조회로 대체 |
| `from typing import List` | `List` 사용처 없음 |

### B.2 dependencies.py

| v1.0 코드 | 제거 이유 |
|-----------|----------|
| `roles=payload.roles` | v2.0 UserContext에 `roles` 필드 없음 |
| `permissions=payload.permissions` | v2.0 UserContext에 `permissions` 필드 없음 |

### B.3 permission.py

| v1.0 함수 | 제거 이유 |
|-----------|----------|
| `require_permission(*required_permissions)` | `has_all_permissions()` 메서드 삭제 |
| `require_any_permission(*required_permissions)` | `has_any_permission()` 메서드 삭제 |

---

## 부록 C: 기존 프로젝트 패턴과의 일관성

### C.1 __init__.py 정책

| 모듈 | 형태 | 이유 |
|------|------|------|
| `app/core/security/__init__.py` | **빈 파일** | CLAUDE.md 규칙 준수 |
| `app/core/errors/__init__.py` | import 있음 | 예외 (에러 처리는 프로젝트 전반에서 빈번하게 import) |

### C.2 에러 처리 패턴

```python
# v2.0에서도 동일 패턴 유지:
raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail="메뉴 권한 없음: USER_MGMT")
```

### C.3 Settings 접근 패턴

```python
# 변경 없음:
from app.config import settings
key = settings.secret_key
algo = settings.algorithm
```

### C.4 DB 접근 패턴 (★ Phase 2 신규)

```python
# permission.py에서 신규 사용:
from app.core.database.connection import db_manager

with db_manager.get_cursor() as cur:
    cur.execute("SELECT ... FROM tb_user_menu um JOIN tb_menu m ...", (user_id, menu_code))
    row = cur.fetchone()
```

기존 서비스 레이어(`auth_service.py`, `user_service.py`)에서 사용하는 동일한 DB 접근 패턴을 security 모듈에서도 사용합니다.
