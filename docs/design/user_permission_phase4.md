# Phase 4 구현 가이드: 관리 API (메뉴 기반 CRUD)

> **문서 버전**: 2.0
> **작성일**: 2026-02-13
> **상위 문서**: `docs/design/user_permission_system.md` (v2.0)
> **선행 조건**: Phase 3 완료 (인증 API + 인증 미들웨어)
> **목적**: v2.0 메뉴 기반 권한 체계에 맞춰 사용자/역할/메뉴/테넌트 관리 API를 구현

---

## 목차

1. [Phase 4 개요](#1-phase-4-개요)
2. [v1.0 → v2.0 마이그레이션 요약](#2-v10--v20-마이그레이션-요약)
3. [Step 1: Pydantic 모델 수정](#3-step-1-pydantic-모델-수정)
4. [Step 2: 권한 검사 변경 — `require_menu_permission`](#4-step-2-권한-검사-변경)
5. [Step 3: `user_service.py` — 사용자 관리 서비스](#5-step-3-user_service)
6. [Step 4: `role_service.py` — 역할 관리 서비스](#6-step-4-role_service)
7. [Step 5: `menu_service.py` — 메뉴 관리 서비스 (신규)](#7-step-5-menu_service)
8. [Step 6: `tenant_service.py` — 테넌트 관리 서비스](#8-step-6-tenant_service)
9. [Step 7: API 라우트 구현](#9-step-7-api-라우트-구현)
10. [Step 8: 기존 API 권한 적용](#10-step-8-기존-api-권한-적용)
11. [Step 9: `auth_service.py` 수정](#11-step-9-auth_service-수정)
12. [Step 10: `main.py` 수정](#12-step-10-main-수정)
13. [검증 체크리스트](#13-검증-체크리스트)
14. [다음 단계 (Phase 5 Preview)](#14-다음-단계)

---

## 1. Phase 4 개요

### 1.1 무엇을 하는가

Phase 4는 v2.0 **메뉴 기반 권한 체계**에 맞춰 관리 API를 구현합니다.
v1.0에서 사용하던 permission 코드 방식을 완전히 폐기하고, `tb_user_menu` 기반 CRUD 권한 체크로 전환합니다.

```
Phase 4 산출물:
  [MOD] app/models/user.py                  ← v2.0 모델 전환 (role_id 1:N, 메뉴 권한)
  [NEW] app/models/menu.py                  ← 메뉴 관리 Pydantic 모델
  [MOD] app/models/auth.py                  ← UserContext에 menus 추가, permissions 제거
  [MOD] app/core/security/permission.py     ← require_menu_permission() 추가
  [MOD] app/api/services/user_service.py    ← tb_user.role_id + tb_user_menu 기반
  [MOD] app/api/services/role_service.py    ← 단순화 (tb_permission/tb_role_permission 제거)
  [NEW] app/api/services/menu_service.py    ← 메뉴 트리 CRUD (신규)
  [MOD] app/api/services/tenant_service.py  ← 변경 없음 (유지)
  [MOD] app/api/services/auth_service.py    ← 메뉴 권한 로드 방식 변경
  [MOD] app/api/routes/users.py             ← require_menu_permission 적용
  [MOD] app/api/routes/roles.py             ← 단순화 (권한 할당 제거)
  [NEW] app/api/routes/menus.py             ← 메뉴 관리 API (신규)
  [MOD] app/api/routes/tenants.py           ← require_menu_permission 적용
  [MOD] app/main.py                         ← menus 라우터 등록
```

### 1.2 핵심 설계 원칙 (v2.0)

```
┌──────────────────────────────────────────────────────────────────────┐
│  v2.0 권한 체크 = tb_user_menu 단일 테이블                            │
│                                                                       │
│  기능 접근: tb_user_menu의 CRUD 플래그 (can_create/read/update/delete) │
│  데이터 범위: tb_role.scope_type (GLOBAL/TENANT/USER)                 │
│  역할: tb_user.role_id FK (1:N, 사용자는 정확히 1개 역할)             │
│                                                                       │
│  예시:                                                                │
│    USER_MGMT 메뉴 + can_read=true + scope_type=TENANT                │
│    → 사용자 관리 조회 가능 + 자기 테넌트 사용자만 표시                 │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 역할별 접근 범위

| 역할 | scope_type | 사용자 관리 | 역할 관리 | 메뉴 관리 | 테넌트 관리 | 설정 관리 |
|------|-----------|:-----------:|:---------:|:---------:|:----------:|:---------:|
| SYSTEM_ADMIN | GLOBAL | 전체 (CRUDE) | O (CRUDE) | O (CRUDE) | O (CRUDE) | O (RU) |
| TENANT_ADMIN | TENANT | 자기 테넌트 (CRU) | - | - | - | - |
| USER | USER | 본인만 (R) | - | - | - | - |

### 1.4 의존 관계

```
Phase 2 (Core Security)
  ├── jwt.py           → 토큰 생성/검증
  ├── password.py      → 비밀번호 해싱
  └── dependencies.py  → get_current_active_user()

Phase 3 (인증)
  ├── auth_service.py  → get_user_with_menus() (v2.0 변경)
  └── middleware/auth.py → request.state.current_user

Phase 4 (이번 구현)
  ├── permission.py    → require_menu_permission(menu_code, action) [v2.0 추가]
  ├── user_service.py  → 사용자 CRUD + 메뉴 권한 할당
  ├── role_service.py  → 역할 CRUD (단순화)
  ├── menu_service.py  → 메뉴 트리 CRUD [신규]
  ├── tenant_service.py → 테넌트 CRUD
  ├── routes/users.py  → require_menu_permission("USER_MGMT", action)
  ├── routes/roles.py  → require_menu_permission("ROLE_MGMT", action)
  ├── routes/menus.py  → require_menu_permission("MENU_MGMT", action) [신규]
  └── routes/tenants.py → require_menu_permission("TENANT_MGMT", action)
```

---

## 2. v1.0 → v2.0 마이그레이션 요약

### 2.1 제거 대상 (v1.0 잔재)

| 구분 | v1.0 (제거) | v2.0 (대체) |
|------|:---:|:---:|
| 권한 단위 | `tb_permission` (코드) | `tb_menu` + `tb_user_menu` (메뉴 CRUD) |
| 역할-권한 | `tb_role_permission` | 사용하지 않음 (메뉴 권한은 사용자에 직접 할당) |
| 사용자-역할 | `tb_user_role` (M:N) | `tb_user.role_id` FK (1:N) |
| 데이터 필터 | `tb_data_filter` | `tb_role.scope_type` → 코드 유도 |
| 권한 체크 | `require_permission("admin:users")` | `require_menu_permission("USER_MGMT", "read")` |
| JWT 페이로드 | `permissions: [...]` 배열 | 불포함 (필요시 DB 조회) |
| 로그인 응답 | `permissions: [...]` | `menus: [{menu_code, can_create, ...}]` |

### 2.2 코드 변경 포인트

**삭제할 코드**:
- `user_service.py`: `tb_user_role` INSERT/DELETE 관련 로직
- `role_service.py`: `tb_role_permission`, `tb_permission` 관련 전체 로직
- `models/user.py`: `PermissionSimple`, `RolePermissionAssign`, `DataFilterResponse`
- `auth_service.py`: `tb_user_role` JOIN, `tb_role_permission` JOIN, `permissions` 수집

**추가할 코드**:
- `user_service.py`: `tb_user_menu` INSERT/DELETE, `tb_user.role_id` UPDATE
- `menu_service.py`: `tb_menu` CRUD (신규)
- `models/menu.py`: 메뉴 관련 Pydantic 모델 (신규)
- `permission.py`: `require_menu_permission()` 함수 (신규)
- `auth_service.py`: `tb_user_menu` + `tb_menu` JOIN으로 메뉴 권한 로드

---

## 3. Step 1: Pydantic 모델 수정

### 3.1 `app/models/auth.py` 수정

**변경**: `UserInfo`에서 `permissions` 제거, `menus` 추가. `UserContext`에 메뉴 권한 체크 메서드 추가.

```python
# ===================================
# 메뉴 권한 정보 (로그인 응답 포함용)
# ===================================

class MenuPermission(BaseModel):
    """메뉴별 CRUD 권한 (로그인 응답, 사이드바 렌더링용)"""
    menu_code: str
    menu_name: str
    menu_path: Optional[str] = None
    menu_type: str          # DIRECTORY, PAGE, API
    icon: Optional[str] = None
    parent_menu_code: Optional[str] = None
    depth: int = 0
    sort_order: int = 0
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False
    can_export: bool = False


class UserInfo(BaseModel):
    """로그인 응답에 포함되는 사용자 정보"""
    user_id: int
    login_id: str
    display_name: Optional[str] = None
    tenant_id: Optional[int] = None
    role_code: str                       # 단일 역할 코드
    scope_type: str                      # GLOBAL, TENANT, USER
    landing_page: str = "/chat"          # 로그인 후 랜딩 페이지
    menus: List[MenuPermission] = []     # 메뉴별 CRUD 권한


class UserContext(BaseModel):
    """인증된 사용자 컨텍스트 (JWT → request.state.current_user)"""
    user_id: int
    login_id: str
    display_name: Optional[str] = None
    tenant_id: Optional[int] = None
    is_superuser: bool = False
    role_code: str = "USER"
    scope_type: str = "USER"
    landing_page: str = "/chat"

    def has_menu_permission(self, menu_code: str, action: str) -> bool:
        """메뉴 CRUD 권한 체크 (DB 조회 없이 → permission.py에서 DB 조회)"""
        if self.is_superuser:
            return True
        return False  # 기본 False — 실제 체크는 permission.py에서 DB 조회

    @property
    def is_global(self) -> bool:
        return self.is_superuser or self.scope_type == "GLOBAL"

    @property
    def is_tenant_scope(self) -> bool:
        return self.scope_type == "TENANT"

    @property
    def is_user_scope(self) -> bool:
        return self.scope_type == "USER"
```

> **변경 요약**:
> - `UserInfo`: `roles`, `role_names`, `permissions` → `role_code`, `landing_page`, `menus`
> - `UserContext`: `roles`, `permissions` → `role_code`, `landing_page`
> - `has_permission()`, `has_any_permission()`, `has_all_permissions()` → 제거 (메뉴 권한은 DB 조회)

### 3.2 `app/models/user.py` 수정

**변경**: 역할은 1:N(`role_id`), 메뉴 권한 할당 모델 추가.

```python
# ===================================
# 사용자 (User)
# ===================================

class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8)
    is_active: bool = Field(default=True)
    role_id: int = Field(..., description="역할 ID (필수, 1:N)")
    menu_permissions: List[MenuPermissionItem] = Field(
        default_factory=list,
        description="메뉴별 CRUD 권한 목록"
    )


class MenuPermissionItem(BaseModel):
    """메뉴 권한 할당 항목 (사용자 생성/수정 시)"""
    menu_id: int
    can_create: bool = False
    can_read: bool = True
    can_update: bool = False
    can_delete: bool = False
    can_export: bool = False


class UserRoleChange(BaseModel):
    """사용자 역할 변경 요청 (1:N → 단일 role_id)"""
    role_id: int = Field(..., description="변경할 역할 ID")


class UserMenuAssign(BaseModel):
    """사용자 메뉴 권한 일괄 할당 요청 (replace 방식)"""
    menu_permissions: List[MenuPermissionItem] = Field(
        ..., min_length=1,
        description="메뉴별 CRUD 권한 목록"
    )


class UserResponse(BaseModel):
    """사용자 상세 응답"""
    user_id: int
    login_id: str
    email: str
    display_name: Optional[str] = None
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    is_active: bool
    is_superuser: bool = False
    role_id: int                          # v2.0: 단일 역할 ID
    role_code: str                        # 역할 코드
    role_name: str                        # 역할 표시명
    scope_type: str                       # 데이터 범위
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
```

**제거 대상**:
- `RolePermissionAssign` → 삭제 (역할에 permission 할당 개념 폐기)
- `PermissionSimple` → 삭제 (tb_permission 테이블 없음)
- `PermissionResponse` → 삭제
- `DataFilterResponse` → 삭제 (tb_data_filter 테이블 없음)
- `UserRoleAssign.role_ids: List[int]` → `UserRoleChange.role_id: int` (단일)

### 3.3 `app/models/menu.py` 신규 생성

```python
"""
메뉴 관리 스키마

위치: app/models/menu.py
메뉴 트리 CRUD 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class MenuCreate(BaseModel):
    """메뉴 생성 요청"""
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID (NULL=루트)")
    menu_code: str = Field(..., min_length=1, max_length=50, description="메뉴 코드")
    menu_name: str = Field(..., min_length=1, max_length=100, description="메뉴 표시명")
    menu_type: str = Field(..., description="DIRECTORY / PAGE / API")
    menu_path: Optional[str] = Field(None, max_length=200, description="프론트엔드 URL")
    api_pattern: Optional[str] = Field(None, max_length=200, description="API 경로 패턴")
    icon: Optional[str] = Field(None, max_length=50, description="아이콘 클래스")
    sort_order: int = Field(default=0, description="정렬 순서")
    description: Optional[str] = Field(None, description="설명")

    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: str) -> str:
        v = v.upper()
        if v not in ("DIRECTORY", "PAGE", "API"):
            raise ValueError("menu_type은 DIRECTORY, PAGE, API 중 하나여야 합니다")
        return v

    @field_validator("menu_code")
    @classmethod
    def validate_menu_code(cls, v: str) -> str:
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("menu_code는 영문, 숫자, 언더스코어만 사용 가능합니다")
        return v


class MenuUpdate(BaseModel):
    """메뉴 수정 요청 (모든 필드 Optional)"""
    menu_name: Optional[str] = Field(None, max_length=100)
    menu_path: Optional[str] = Field(None, max_length=200)
    api_pattern: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class MenuResponse(BaseModel):
    """메뉴 응답"""
    menu_id: int
    parent_menu_id: Optional[int] = None
    menu_code: str
    menu_name: str
    menu_type: str
    menu_path: Optional[str] = None
    api_pattern: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    depth: int = 0
    is_active: bool = True
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    children: List["MenuResponse"] = Field(default_factory=list, description="하위 메뉴")


class MenuTreeResponse(BaseModel):
    """메뉴 트리 응답 (루트 목록)"""
    total: int
    items: List[MenuResponse]
```

---

## 4. Step 2: 권한 검사 변경

### 4.1 `app/core/security/permission.py` 수정

**v1.0**: `require_permission("admin:users")` → JWT `permissions` 배열에서 코드 매칭
**v2.0**: `require_menu_permission("USER_MGMT", "read")` → **DB `tb_user_menu` 조회**

```python
"""
권한 검사 의존성 팩토리 (v2.0 메뉴 기반)

위치: app/core/security/permission.py
"""
from fastapi import Depends

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext


def require_menu_permission(menu_code: str, action: str = "read"):
    """
    메뉴 기반 권한 검사 의존성 (v2.0)

    Args:
        menu_code: 메뉴 코드 (예: 'USER_MGMT', 'DOCUMENTS')
        action: 'create' | 'read' | 'update' | 'delete' | 'export'

    Usage:
        @router.get("")
        async def list_users(
            current_user = Depends(require_menu_permission("USER_MGMT", "read"))
        ):
    """
    async def checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        # superuser는 무조건 통과
        if current_user.is_superuser:
            return current_user

        # DB에서 메뉴 권한 조회
        column = f"can_{action}"
        with db_manager.get_cursor() as cur:
            cur.execute(
                f"SELECT {column} FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true",
                (current_user.user_id, menu_code),
            )
            row = cur.fetchone()

        if not row or not row[column]:
            raise APIException(
                ErrorCode.FORBIDDEN,
                "접근 권한이 없습니다",
                detail=f"필요 권한: {menu_code}:{action}"
            )
        return current_user

    return checker


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

> **핵심 변경**: `require_permission()` → `require_menu_permission()`
> - v1.0: JWT 페이로드의 `permissions` 배열에서 매칭 (DB 조회 없음)
> - v2.0: 매 요청마다 `tb_user_menu` DB 조회 (실시간 권한 변경 반영)

### 4.2 HTTP 메서드 → CRUD 액션 매핑

| HTTP Method | action 파라미터 | `tb_user_menu` 컬럼 |
|:-----------:|:---------------:|:-------------------:|
| POST | `create` | `can_create` |
| GET | `read` | `can_read` |
| PUT | `update` | `can_update` |
| DELETE | `delete` | `can_delete` |
| GET (Excel) | `export` | `can_export` |

---

## 5. Step 3: `user_service.py` — 사용자 관리 서비스

> **파일**: `app/api/services/user_service.py`
> **주요 변경**: `tb_user_role` → `tb_user.role_id`, 메뉴 권한 할당 추가

### 5.1 클래스 구조

```python
class UserService:
    """사용자 관리 비즈니스 로직 (v2.0 메뉴 기반)"""

    # === 사용자 CRUD ===
    def list_users(self, current_user, request_id, limit, offset, ...) -> dict
    def get_user(self, user_id, current_user, request_id) -> dict
    def create_user(self, data, current_user, request_id) -> dict
    def update_user(self, user_id, data, current_user, request_id) -> dict
    def delete_user(self, user_id, current_user, request_id) -> bool

    # === 메뉴 권한 관리 ===
    def get_user_menus(self, user_id, current_user, request_id) -> list
    def assign_user_menus(self, user_id, menu_permissions, current_user, request_id) -> list

    # === 내부 헬퍼 ===
    def _check_scope_access(self, target_tenant_id, current_user) -> None
    def _get_user_role(self, user_id) -> dict   # 단일 역할 조회
    def _get_user_menu_permissions(self, user_id) -> list  # 메뉴 권한 목록
```

### 5.2 create_user — 사용자 생성

```python
def create_user(self, data: dict, current_user: UserContext, request_id: str = "") -> dict:
    """사용자 생성 (v2.0: role_id + 메뉴 권한)"""
    tenant_id = data.get("tenant_id")
    if current_user.scope_type == "TENANT":
        tenant_id = current_user.tenant_id

    role_id = data["role_id"]  # 필수 (단일 역할)
    password_hashed = hash_password(data["password"])

    try:
        with db_manager.get_cursor(commit=True) as cur:
            # 1. tb_user INSERT (role_id FK 포함)
            cur.execute(
                "INSERT INTO tb_user (login_id, email, password_hash, display_name, "
                "tenant_id, role_id, is_active) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id",
                (data["login_id"], data["email"], password_hashed,
                 data.get("display_name"), tenant_id, role_id,
                 data.get("is_active", True)),
            )
            new_user_id = cur.fetchone()["user_id"]

            # 2. tb_user_menu INSERT (메뉴 권한 할당)
            for perm in data.get("menu_permissions", []):
                cur.execute(
                    "INSERT INTO tb_user_menu "
                    "(user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (new_user_id, perm["menu_id"],
                     perm.get("can_create", False),
                     perm.get("can_read", True),
                     perm.get("can_update", False),
                     perm.get("can_delete", False),
                     perm.get("can_export", False),
                     current_user.user_id),
                )
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 로그인 ID 또는 이메일입니다")
        raise

    log_step(logger, request_id, "USER", "3", "CREATE", "사용자 생성", user_id=new_user_id)
    return self.get_user(new_user_id, current_user, request_id)
```

### 5.3 get_user — 사용자 상세 조회

```python
def get_user(self, user_id: int, current_user: UserContext, request_id: str = "") -> dict:
    """사용자 상세 조회 (v2.0: 역할 + 메뉴 권한 포함)"""
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT u.user_id, u.login_id, u.email, u.display_name, "
            "u.tenant_id, t.tenant_name, u.role_id, "
            "r.role_code, r.role_name, r.scope_type, "
            "u.is_active, u.is_superuser, u.last_login_at, u.created_at, u.updated_at "
            "FROM tb_user u "
            "LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id "
            "JOIN tb_role r ON u.role_id = r.role_id "
            "WHERE u.user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()

    if not row:
        raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

    user = dict(row)

    if current_user.user_id != user_id:
        self._check_scope_access(user["tenant_id"], current_user)

    log_step(logger, request_id, "USER", "2", "GET", "사용자 상세 조회", user_id=user_id)
    return user
```

> **v1.0 대비 변경점**:
> - `_get_user_roles()` 제거 → `tb_role` JOIN으로 직접 조회
> - `user["roles"]` (목록) → `user["role_id"]`, `user["role_code"]`, `user["role_name"]` (단일)
> - `tb_user_role` 조회 → 불필요

### 5.4 get_user_menus — 사용자 메뉴 권한 조회

```python
def get_user_menus(self, user_id: int, current_user: UserContext, request_id: str = "") -> list:
    """사용자의 메뉴별 CRUD 권한 목록"""
    if current_user.user_id != user_id:
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")
        self._check_scope_access(row["tenant_id"], current_user)

    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT m.menu_id, m.menu_code, m.menu_name, m.menu_type, "
            "m.menu_path, m.icon, m.depth, m.sort_order, "
            "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export "
            "FROM tb_user_menu um "
            "JOIN tb_menu m ON m.menu_id = um.menu_id "
            "WHERE um.user_id = %s AND m.is_active = true "
            "ORDER BY m.depth, m.sort_order",
            (user_id,),
        )
        return [dict(row) for row in cur.fetchall()]
```

### 5.5 assign_user_menus — 메뉴 권한 할당

```python
def assign_user_menus(self, user_id: int, menu_permissions: list, current_user: UserContext, request_id: str = "") -> list:
    """사용자 메뉴 권한 일괄 할당 (replace 방식: 전체 삭제 후 재할당)"""
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT user_id, tenant_id FROM tb_user WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
    if not user:
        raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

    self._check_scope_access(user["tenant_id"], current_user)

    with db_manager.get_cursor(commit=True) as cur:
        # 기존 메뉴 권한 전체 삭제
        cur.execute("DELETE FROM tb_user_menu WHERE user_id = %s", (user_id,))

        # 새 메뉴 권한 INSERT
        for perm in menu_permissions:
            cur.execute(
                "INSERT INTO tb_user_menu "
                "(user_id, menu_id, can_create, can_read, can_update, can_delete, can_export, granted_by) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, perm["menu_id"],
                 perm.get("can_create", False),
                 perm.get("can_read", True),
                 perm.get("can_update", False),
                 perm.get("can_delete", False),
                 perm.get("can_export", False),
                 current_user.user_id),
            )

    log_step(logger, request_id, "USER", "6", "ASSIGN_MENUS", "메뉴 권한 할당", user_id=user_id, menus=len(menu_permissions))
    return self.get_user_menus(user_id, current_user, request_id)
```

### 5.6 update_user — 사용자 수정 (role_id 변경 포함)

```python
def update_user(self, user_id: int, data: dict, current_user: UserContext, request_id: str = "") -> dict:
    """사용자 수정 (v2.0: role_id 직접 변경)"""
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT user_id, tenant_id, is_superuser FROM tb_user WHERE user_id = %s", (user_id,))
        existing = cur.fetchone()
    if not existing:
        raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

    self._check_scope_access(existing["tenant_id"], current_user)

    if existing["is_superuser"] and current_user.user_id != user_id:
        raise APIException(ErrorCode.FORBIDDEN, "슈퍼유저는 본인만 수정할 수 있습니다")

    # 동적 UPDATE (role_id 포함)
    fields = []
    params: list = []
    for key in ("email", "display_name", "tenant_id", "is_active", "role_id"):
        if key in data and data[key] is not None:
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
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 이메일입니다")
        if "foreign key" in str(e).lower() or "violates" in str(e).lower():
            raise APIException(ErrorCode.BAD_REQUEST, "존재하지 않는 역할 ID입니다")
        raise

    log_step(logger, request_id, "USER", "4", "UPDATE", "사용자 수정", user_id=user_id)
    return self.get_user(user_id, current_user, request_id)
```

---

## 6. Step 4: `role_service.py` — 역할 관리 서비스

> **파일**: `app/api/services/role_service.py`
> **주요 변경**: `tb_permission`, `tb_role_permission` 관련 로직 전면 삭제. 단순 CRUD만 제공.

### 6.1 클래스 구조

```python
class RoleService:
    """역할 관리 비즈니스 로직 (v2.0 단순화)"""

    def list_roles(self, request_id) -> dict
    def get_role(self, role_id, request_id) -> dict
    def create_role(self, data, current_user, request_id) -> dict
    def update_role(self, role_id, data, current_user, request_id) -> dict
    def delete_role(self, role_id, current_user, request_id) -> bool
    def get_default_menus(self, role_code, request_id) -> list  # 역할별 기본 메뉴 목록

role_service = RoleService()
```

> **v1.0 대비 제거된 메서드**:
> - `assign_permissions()` → 삭제 (역할에 permission 할당 개념 없음)
> - `list_permissions()` → 삭제 (tb_permission 테이블 없음)
> - `_get_role_permissions()` → 삭제

### 6.2 list_roles

```python
def list_roles(self, request_id: str = "") -> dict:
    """역할 목록 조회"""
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT r.role_id, r.role_code, r.role_name, r.description, "
            "r.scope_type, r.landing_page, r.is_system, r.sort_order, r.created_at, "
            "(SELECT COUNT(*) FROM tb_user u WHERE u.role_id = r.role_id) as user_count "
            "FROM tb_role r ORDER BY r.sort_order, r.role_id"
        )
        rows = cur.fetchall()

    items = [dict(row) for row in rows]
    log_step(logger, request_id, "ROLE", "1", "LIST", "역할 목록 조회", total=len(items))
    return {"total": len(items), "items": items}
```

> **변경점**:
> - 각 역할의 `permissions` 목록 조회 삭제
> - `user_count`를 `tb_user.role_id` 카운트로 변경 (기존 `tb_user_role` 카운트 아님)

### 6.3 get_role

```python
def get_role(self, role_id: int, request_id: str = "") -> dict:
    """역할 상세 조회 (사용자 수 포함)"""
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT r.role_id, r.role_code, r.role_name, r.description, "
            "r.scope_type, r.landing_page, r.is_system, r.sort_order, r.created_at, "
            "(SELECT COUNT(*) FROM tb_user u WHERE u.role_id = r.role_id) as user_count "
            "FROM tb_role r WHERE r.role_id = %s",
            (role_id,),
        )
        row = cur.fetchone()

    if not row:
        raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")

    log_step(logger, request_id, "ROLE", "2", "GET", "역할 상세 조회", role_id=role_id)
    return dict(row)
```

### 6.4 create_role

```python
def create_role(self, data: dict, current_user: UserContext, request_id: str = "") -> dict:
    """역할 생성 (v2.0: landing_page 포함)"""
    try:
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tb_role (role_code, role_name, description, scope_type, landing_page, sort_order) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING role_id",
                (data["role_code"], data["role_name"], data.get("description"),
                 data["scope_type"], data.get("landing_page", "/chat"),
                 data.get("sort_order", 0)),
            )
            new_role_id = cur.fetchone()["role_id"]
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 역할 코드입니다")
        raise

    log_step(logger, request_id, "ROLE", "3", "CREATE", "역할 생성", role_id=new_role_id)
    return self.get_role(new_role_id, request_id)
```

### 6.5 delete_role

```python
def delete_role(self, role_id: int, current_user: UserContext, request_id: str = "") -> bool:
    """역할 삭제"""
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT role_id, is_system, role_code FROM tb_role WHERE role_id = %s", (role_id,))
        existing = cur.fetchone()
    if not existing:
        raise APIException(ErrorCode.NOT_FOUND, "역할을 찾을 수 없습니다")
    if existing["is_system"]:
        raise APIException(ErrorCode.BAD_REQUEST, "시스템 기본 역할은 삭제할 수 없습니다")

    # v2.0: tb_user.role_id로 사용 중 확인
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE role_id = %s", (role_id,))
        if cur.fetchone()["cnt"] > 0:
            raise APIException(ErrorCode.BAD_REQUEST, "사용 중인 역할은 삭제할 수 없습니다")

    with db_manager.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM tb_role WHERE role_id = %s", (role_id,))

    log_step(logger, request_id, "ROLE", "5", "DELETE", "역할 삭제", role_id=role_id)
    return True
```

### 6.6 get_default_menus — 역할별 기본 메뉴 목록

사용자 생성 시, 선택한 역할에 따라 기본 메뉴 권한을 자동 체크하기 위한 메서드입니다.

```python
# 역할 코드별 기본 메뉴 템플릿 (하드코딩 또는 DB 테이블로 관리)
_DEFAULT_MENUS = {
    "SYSTEM_ADMIN": {
        # 모든 PAGE/API 메뉴에 전체 CRUD
        "__all_pages__": {"can_create": True, "can_read": True, "can_update": True, "can_delete": True, "can_export": True},
    },
    "TENANT_ADMIN": {
        "DASHBOARD": {"can_read": True},
        "CHAT":      {"can_create": True, "can_read": True},
        "DOCUMENTS": {"can_create": True, "can_read": True, "can_update": True, "can_delete": True, "can_export": True},
        "USER_MGMT": {"can_create": True, "can_read": True, "can_update": True},
        "HISTORY":   {"can_read": True, "can_export": True},
        "USER_CHAT": {"can_create": True, "can_read": True},
        "AGENT_API": {"can_create": True, "can_read": True},
        "RAG_API":   {"can_create": True, "can_read": True},
        "NL2SQL_API":{"can_create": True, "can_read": True},
    },
    "USER": {
        "USER_CHAT": {"can_create": True, "can_read": True},
        "AGENT_API": {"can_create": True, "can_read": True},
        "RAG_API":   {"can_create": True, "can_read": True},
        "NL2SQL_API":{"can_create": True, "can_read": True},
    },
}

def get_default_menus(self, role_code: str, request_id: str = "") -> list:
    """역할별 기본 메뉴 권한 목록 (UI에서 사용자 생성 시 자동 체크용)"""
    template = _DEFAULT_MENUS.get(role_code, {})

    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT menu_id, menu_code, menu_name, menu_type, menu_path, icon, depth, sort_order "
            "FROM tb_menu WHERE is_active = true AND menu_type IN ('PAGE', 'API') "
            "ORDER BY depth, sort_order"
        )
        menus = [dict(row) for row in cur.fetchall()]

    result = []
    for menu in menus:
        defaults = template.get(menu["menu_code"], template.get("__all_pages__", {}))
        result.append({
            **menu,
            "can_create": defaults.get("can_create", False),
            "can_read":   defaults.get("can_read", False),
            "can_update": defaults.get("can_update", False),
            "can_delete": defaults.get("can_delete", False),
            "can_export": defaults.get("can_export", False),
            "checked":    bool(defaults),  # UI에서 체크박스 표시용
        })

    return result
```

---

## 7. Step 5: `menu_service.py` — 메뉴 관리 서비스 (신규)

> **파일**: `app/api/services/menu_service.py` (신규 생성)
> **역할**: 메뉴 트리 CRUD

### 7.1 클래스 구조

```python
class MenuService:
    """메뉴 관리 비즈니스 로직"""

    def get_menu_tree(self, request_id) -> dict
    def get_menu(self, menu_id, request_id) -> dict
    def create_menu(self, data, current_user, request_id) -> dict
    def update_menu(self, menu_id, data, current_user, request_id) -> dict
    def delete_menu(self, menu_id, current_user, request_id) -> bool

menu_service = MenuService()
```

### 7.2 get_menu_tree — 메뉴 트리 조회

```python
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

    # 플랫 리스트 → 트리 구조 변환
    menu_map = {row["menu_id"]: {**row, "children": []} for row in rows}
    root_items = []

    for row in rows:
        parent_id = row["parent_menu_id"]
        if parent_id and parent_id in menu_map:
            menu_map[parent_id]["children"].append(menu_map[row["menu_id"]])
        else:
            root_items.append(menu_map[row["menu_id"]])

    log_step(logger, request_id, "MENU", "1", "TREE", "메뉴 트리 조회", total=len(rows))
    return {"total": len(rows), "items": root_items}
```

### 7.3 create_menu

```python
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
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 메뉴 코드입니다")
        raise

    log_step(logger, request_id, "MENU", "2", "CREATE", "메뉴 생성", menu_id=new_id)
    return self.get_menu(new_id, request_id)
```

### 7.4 delete_menu

```python
def delete_menu(self, menu_id: int, current_user: UserContext, request_id: str = "") -> bool:
    """메뉴 삭제 (하위 메뉴 있으면 불가)"""
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT menu_id, menu_code FROM tb_menu WHERE menu_id = %s", (menu_id,))
        existing = cur.fetchone()
    if not existing:
        raise APIException(ErrorCode.NOT_FOUND, "메뉴를 찾을 수 없습니다")

    # 하위 메뉴 존재 확인
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM tb_menu WHERE parent_menu_id = %s", (menu_id,))
        if cur.fetchone()["cnt"] > 0:
            raise APIException(ErrorCode.BAD_REQUEST, "하위 메뉴가 있어 삭제할 수 없습니다. 하위 메뉴를 먼저 삭제하세요")

    # tb_user_menu CASCADE 삭제됨
    with db_manager.get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM tb_menu WHERE menu_id = %s", (menu_id,))

    log_step(logger, request_id, "MENU", "4", "DELETE", "메뉴 삭제", menu_id=menu_id)
    return True
```

---

## 8. Step 6: `tenant_service.py` — 테넌트 관리 서비스

> **파일**: `app/api/services/tenant_service.py`
> **변경**: 없음 (v1.0과 동일). 현재 구현 유지.

테넌트 관리는 메뉴/권한 체계 변경의 영향을 받지 않습니다.
`require_menu_permission("TENANT_MGMT", action)` 적용만 라우트에서 변경합니다.

---

## 9. Step 7: API 라우트 구현

### 9.1 사용자 관리 API (`/api/admin/v1/users`)

> **파일**: `app/api/routes/users.py`

| Method | Path | Depends | 설명 |
|--------|------|---------|------|
| GET | `/` | `require_menu_permission("USER_MGMT", "read")` | 사용자 목록 |
| POST | `/` | `require_menu_permission("USER_MGMT", "create")` | 사용자 생성 |
| GET | `/{user_id}` | `get_current_active_user` | 사용자 상세 (본인 허용) |
| PUT | `/{user_id}` | `require_menu_permission("USER_MGMT", "update")` | 사용자 수정 |
| DELETE | `/{user_id}` | `require_menu_permission("USER_MGMT", "delete")` | 사용자 삭제 |
| GET | `/{user_id}/menus` | `get_current_active_user` | 사용자 메뉴 권한 조회 |
| PUT | `/{user_id}/menus` | `require_menu_permission("USER_MGMT", "update")` | 메뉴 권한 할당 |

```python
from app.core.security.permission import require_menu_permission

router = APIRouter(prefix="/api/admin/v1/users", tags=["admin-users"])


@router.get("")
async def list_users(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "read")),
):
    """사용자 목록 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.list_users(current_user, request_id, limit, offset, tenant_id, is_active, keyword)
    return success_response(result)


@router.post("")
async def create_user(
    data: UserCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "create")),
):
    """사용자 생성 (역할 + 메뉴 권한 포함)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.create_user(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{user_id}/menus")
async def get_user_menus(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(get_current_active_user),
):
    """사용자 메뉴 권한 조회 (본인 또는 USER_MGMT:read)"""
    if current_user.user_id != user_id:
        # DB에서 직접 권한 체크
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT can_read FROM tb_user_menu um "
                "JOIN tb_menu m ON m.menu_id = um.menu_id "
                "WHERE um.user_id = %s AND m.menu_code = 'USER_MGMT'",
                (current_user.user_id,),
            )
            row = cur.fetchone()
        if not current_user.is_superuser and (not row or not row["can_read"]):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user_menus(user_id, current_user, request_id)
    return success_response(result)


@router.put("/{user_id}/menus")
async def assign_user_menus(
    user_id: int,
    data: UserMenuAssign,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("USER_MGMT", "update")),
):
    """사용자 메뉴 권한 할당 (replace 방식)"""
    request_id = getattr(request.state, "request_id", "")
    result = user_service.assign_user_menus(
        user_id, [p.model_dump() for p in data.menu_permissions], current_user, request_id)
    return success_response(result)
```

> **v1.0 대비 변경점**:
> - `require_permission("admin:users")` → `require_menu_permission("USER_MGMT", "read"/"create"/"update"/"delete")`
> - `PUT /{user_id}/roles` (역할 목록 할당) → 삭제 (역할은 `PUT /{user_id}` 본문의 `role_id`로 변경)
> - `GET /{user_id}/permissions` → `GET /{user_id}/menus` (메뉴 권한 조회)
> - `PUT /{user_id}/menus` 추가 (메뉴 권한 할당)

### 9.2 역할 관리 API (`/api/admin/v1/roles`)

> **파일**: `app/api/routes/roles.py`

| Method | Path | Depends | 설명 |
|--------|------|---------|------|
| GET | `/default-menus/{role_code}` | `require_menu_permission("ROLE_MGMT", "read")` | 역할별 기본 메뉴 |
| GET | `/` | `require_menu_permission("ROLE_MGMT", "read")` | 역할 목록 |
| POST | `/` | `require_menu_permission("ROLE_MGMT", "create")` | 역할 생성 |
| GET | `/{role_id}` | `require_menu_permission("ROLE_MGMT", "read")` | 역할 상세 |
| PUT | `/{role_id}` | `require_menu_permission("ROLE_MGMT", "update")` | 역할 수정 |
| DELETE | `/{role_id}` | `require_menu_permission("ROLE_MGMT", "delete")` | 역할 삭제 |

```python
router = APIRouter(prefix="/api/admin/v1/roles", tags=["admin-roles"])


# 고정 경로를 파라미터 경로보다 먼저 배치
@router.get("/default-menus/{role_code}")
async def get_default_menus(
    role_code: str,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("ROLE_MGMT", "read")),
):
    """역할별 기본 메뉴 권한 목록 (사용자 생성 시 자동 체크용)"""
    request_id = getattr(request.state, "request_id", "")
    result = role_service.get_default_menus(role_code.upper(), request_id)
    return success_response(result)


@router.get("")
async def list_roles(request: Request, current_user = Depends(require_menu_permission("ROLE_MGMT", "read"))):
    """역할 목록 조회"""
    ...


@router.post("")
async def create_role(data: RoleCreate, request: Request, current_user = Depends(require_menu_permission("ROLE_MGMT", "create"))):
    """역할 생성"""
    ...
```

> **v1.0 대비 변경점**:
> - `GET /permissions` → 삭제 (tb_permission 없음)
> - `PUT /{role_id}/permissions` → 삭제 (역할-권한 할당 개념 없음)
> - `GET /default-menus/{role_code}` 추가 (역할별 기본 메뉴 템플릿)
> - `require_permission("admin:users")` → `require_menu_permission("ROLE_MGMT", action)`

### 9.3 메뉴 관리 API (`/api/admin/v1/menus`) — 신규

> **파일**: `app/api/routes/menus.py` (신규 생성)

| Method | Path | Depends | 설명 |
|--------|------|---------|------|
| GET | `/` | `require_menu_permission("MENU_MGMT", "read")` | 메뉴 트리 조회 |
| POST | `/` | `require_menu_permission("MENU_MGMT", "create")` | 메뉴 추가 |
| GET | `/{menu_id}` | `require_menu_permission("MENU_MGMT", "read")` | 메뉴 상세 |
| PUT | `/{menu_id}` | `require_menu_permission("MENU_MGMT", "update")` | 메뉴 수정 |
| DELETE | `/{menu_id}` | `require_menu_permission("MENU_MGMT", "delete")` | 메뉴 삭제 |

```python
"""메뉴 관리 API 라우터

위치: app/api/routes/menus.py
메뉴 트리 CRUD (MENU_MGMT 권한 필요)
"""
from fastapi import APIRouter, Depends, Request

from app.api.services.menu_service import menu_service
from app.core.errors import success_response
from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
from app.models.menu import MenuCreate, MenuUpdate

router = APIRouter(prefix="/api/admin/v1/menus", tags=["admin-menus"])


@router.get("")
async def get_menu_tree(
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "read")),
):
    """메뉴 트리 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.get_menu_tree(request_id)
    return success_response(result)


@router.post("")
async def create_menu(
    data: MenuCreate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "create")),
):
    """메뉴 추가"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.create_menu(data.model_dump(), current_user, request_id)
    return success_response(result)


@router.get("/{menu_id}")
async def get_menu(
    menu_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "read")),
):
    """메뉴 상세 조회"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.get_menu(menu_id, request_id)
    return success_response(result)


@router.put("/{menu_id}")
async def update_menu(
    menu_id: int,
    data: MenuUpdate,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "update")),
):
    """메뉴 수정"""
    request_id = getattr(request.state, "request_id", "")
    result = menu_service.update_menu(menu_id, data.model_dump(exclude_none=True), current_user, request_id)
    return success_response(result)


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: int,
    request: Request,
    current_user: UserContext = Depends(require_menu_permission("MENU_MGMT", "delete")),
):
    """메뉴 삭제 (하위 메뉴 존재 시 불가)"""
    request_id = getattr(request.state, "request_id", "")
    menu_service.delete_menu(menu_id, current_user, request_id)
    return success_response({"message": "메뉴가 삭제되었습니다"})
```

### 9.4 테넌트 관리 API (`/api/admin/v1/tenants`)

> **파일**: `app/api/routes/tenants.py`
> **변경**: `require_permission("admin:tenants")` → `require_menu_permission("TENANT_MGMT", action)`

| Method | Path | Depends | 설명 |
|--------|------|---------|------|
| GET | `/` | `require_menu_permission("TENANT_MGMT", "read")` | 테넌트 목록 |
| POST | `/` | `require_menu_permission("TENANT_MGMT", "create")` | 테넌트 생성 |
| GET | `/{tenant_id}` | `require_menu_permission("TENANT_MGMT", "read")` | 테넌트 상세 |
| PUT | `/{tenant_id}` | `require_menu_permission("TENANT_MGMT", "update")` | 테넌트 수정 |
| DELETE | `/{tenant_id}` | `require_menu_permission("TENANT_MGMT", "delete")` | 테넌트 삭제 |

---

## 10. Step 8: 기존 API 권한 적용

### 10.1 적용 대상 및 방법

| 기존 라우트 | 메뉴 코드 | 적용 방법 |
|------------|-----------|----------|
| `documents.py` | `DOCUMENTS` | `require_menu_permission("DOCUMENTS", action)` |
| `settings.py` | `SETTINGS` | `require_menu_permission("SETTINGS", action)` |
| `codes.py` | `CODES` | `require_menu_permission("CODES", action)` |
| `history.py` | `HISTORY` | `require_menu_permission("HISTORY", "read")` |
| `search.py` | - | `get_optional_user` (인증 선택적 — Phase 3a 유지) |
| `agent.py` | - | `get_optional_user` (인증 선택적 — Phase 3a 유지) |

### 10.2 documents.py 권한 매핑

| 엔드포인트 | v2.0 Depends |
|-----------|-------------|
| `POST /` (저장) | `require_menu_permission("DOCUMENTS", "create")` |
| `GET /` (목록) | `require_menu_permission("DOCUMENTS", "read")` |
| `GET /{doc_id}` (상세) | `require_menu_permission("DOCUMENTS", "read")` |
| `PUT /{doc_id}` (수정) | `require_menu_permission("DOCUMENTS", "update")` |
| `DELETE /{doc_id}` (삭제) | `require_menu_permission("DOCUMENTS", "delete")` |
| `POST /bulk-delete` | `require_menu_permission("DOCUMENTS", "delete")` |
| `POST /embedding/execute` | `require_menu_permission("DOCUMENTS", "create")` |

### 10.3 settings.py / codes.py 권한 매핑

| 엔드포인트 | v2.0 Depends |
|-----------|-------------|
| `GET /` (조회) | `require_menu_permission("SETTINGS"/"CODES", "read")` |
| `PUT /` (수정) | `require_menu_permission("SETTINGS"/"CODES", "update")` |

---

## 11. Step 9: `auth_service.py` 수정

> **파일**: `app/api/services/auth_service.py`
> **주요 변경**: `get_user_with_permissions()` → `get_user_with_menus()` (메뉴 기반 권한 로드)

### 11.1 get_user_with_menus (기존 get_user_with_permissions 대체)

```python
def get_user_with_menus(self, user_id: int, request_id: str = "") -> dict:
    """사용자 정보 + 역할 + 메뉴 권한 일괄 조회 (v2.0)"""
    # 1. 사용자 + 역할 조회 (1:N JOIN)
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT u.user_id, u.login_id, u.email, u.display_name, "
            "u.tenant_id, u.is_superuser, u.is_active, "
            "r.role_code, r.scope_type, r.landing_page "
            "FROM tb_user u "
            "JOIN tb_role r ON u.role_id = r.role_id "
            "WHERE u.user_id = %s",
            (user_id,),
        )
        user_row = cur.fetchone()

    if not user_row:
        raise APIException(ErrorCode.NOT_FOUND, "사용자를 찾을 수 없습니다")

    user = dict(user_row)
    if not user["is_active"]:
        raise APIException(ErrorCode.UNAUTHORIZED, "비활성화된 계정입니다")

    # 2. 메뉴 권한 조회
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT m.menu_code, m.menu_name, m.menu_type, m.menu_path, "
            "m.icon, m.depth, m.sort_order, "
            "pm.menu_code AS parent_menu_code, "
            "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export "
            "FROM tb_user_menu um "
            "JOIN tb_menu m ON m.menu_id = um.menu_id "
            "LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id "
            "WHERE um.user_id = %s AND m.is_active = true "
            "ORDER BY m.depth, m.sort_order",
            (user_id,),
        )
        menus = [dict(row) for row in cur.fetchall()]

    user["menus"] = menus

    log_step(logger, request_id, "AUTH", "2", "PERMISSION", "메뉴 권한 조회", user_id=user_id, scope=user["scope_type"], menus=len(menus))
    return user
```

### 11.2 create_session 수정

```python
def create_session(self, user_id: int, ip: str, user_agent: str, request_id: str = "") -> TokenResponse:
    """세션 생성 (v2.0: 메뉴 권한 포함)"""
    user_info = self.get_user_with_menus(user_id, request_id)  # 변경

    # JWT 토큰 데이터 (v2.0: permissions → role_code + scope_type)
    token_data = {
        "sub": str(user_id),
        "login_id": user_info["login_id"],
        "display_name": user_info["display_name"],
        "tenant_id": user_info["tenant_id"],
        "role_code": user_info["role_code"],       # v2.0
        "scope_type": user_info["scope_type"],
        "landing_page": user_info["landing_page"],  # v2.0
        "is_superuser": user_info["is_superuser"],
    }
    # ... 나머지 동일

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
            role_code=user_info["role_code"],       # v2.0
            scope_type=user_info["scope_type"],
            landing_page=user_info["landing_page"],  # v2.0
            menus=user_info["menus"],                # v2.0: 메뉴 권한 목록
        ),
    )
```

### 11.3 JWT 페이로드 변경

| 필드 | v1.0 | v2.0 |
|------|------|------|
| `roles` | `["SYSTEM_ADMIN"]` | **제거** |
| `permissions` | `["admin:users", ...]` | **제거** |
| `role_code` | - | `"SYSTEM_ADMIN"` (추가) |
| `scope_type` | 유지 | 유지 |
| `landing_page` | - | `"/admin/dashboard"` (추가) |

> **메뉴 권한은 JWT에 포함하지 않음**.
> - 로그인 응답의 `menus` 배열에만 포함 (프론트엔드 사이드바 렌더링용)
> - 백엔드 권한 체크는 매 요청 시 DB 조회 (`require_menu_permission`)

---

## 12. Step 10: `main.py` 수정

```python
# import 추가
from app.api.routes import auth, documents, search, agent, codes, history, export
from app.api.routes import users, roles, tenants, menus  # menus 추가
from app.api.routes import settings as settings_router

# 라우터 등록
app.include_router(auth.router)
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(settings_router.router)
app.include_router(codes.router, prefix="/api/admin/v1")
app.include_router(agent.router)
app.include_router(history.router)
app.include_router(export.router)
app.include_router(users.router)      # /api/admin/v1/users
app.include_router(roles.router)      # /api/admin/v1/roles
app.include_router(menus.router)      # /api/admin/v1/menus  ← 추가
app.include_router(tenants.router)    # /api/admin/v1/tenants
```

---

## 13. 검증 체크리스트

### 13.1 사용자 관리

- [ ] 사용자 목록 조회 (GLOBAL: 전체, TENANT: 자기 테넌트)
- [ ] 사용자 생성 (role_id 필수, menu_permissions 포함)
- [ ] 사용자 상세 조회 (역할 정보 JOIN, 본인 허용)
- [ ] 사용자 수정 (role_id 변경 가능)
- [ ] 사용자 삭제 (superuser/자기 자신 불가)
- [ ] 메뉴 권한 조회 (`GET /users/{id}/menus`)
- [ ] 메뉴 권한 할당 (`PUT /users/{id}/menus` — replace 방식)

### 13.2 역할 관리

- [ ] 역할 목록 조회 (user_count 포함, permissions 없음)
- [ ] 역할 생성 (landing_page 포함)
- [ ] 역할 상세 조회
- [ ] 역할 수정 (시스템 역할 scope_type 변경 불가)
- [ ] 역할 삭제 (시스템 역할/사용 중 불가)
- [ ] 기본 메뉴 목록 (`GET /roles/default-menus/{role_code}`)

### 13.3 메뉴 관리

- [ ] 메뉴 트리 조회 (계층 구조 응답)
- [ ] 메뉴 생성 (depth 자동 계산)
- [ ] 메뉴 상세 조회
- [ ] 메뉴 수정
- [ ] 메뉴 삭제 (하위 메뉴 존재 시 불가)

### 13.4 테넌트 관리

- [ ] 테넌트 목록 조회 (user_count 포함)
- [ ] 테넌트 생성 (metadata JSONB)
- [ ] 테넌트 상세 조회
- [ ] 테넌트 수정
- [ ] 테넌트 삭제 (사용자 있으면 비활성화)

### 13.5 권한 체크

- [ ] `require_menu_permission` 정상 동작 (DB 조회)
- [ ] superuser는 모든 메뉴 접근 허용
- [ ] 권한 없는 메뉴 접근 시 403 Forbidden
- [ ] documents.py — DOCUMENTS 메뉴 권한 체크
- [ ] settings.py — SETTINGS 메뉴 권한 체크
- [ ] search.py / agent.py — 토큰 없이 동작 (Phase 3a 유지)

### 13.6 통합 시나리오

- [ ] SYSTEM_ADMIN → 모든 관리 API 정상
- [ ] TENANT_ADMIN → USER_MGMT 메뉴 CRU 가능, D 불가
- [ ] TENANT_ADMIN → ROLE_MGMT, MENU_MGMT, TENANT_MGMT → 403
- [ ] USER → USER_CHAT, API만 접근 가능, 관리 메뉴 → 403
- [ ] 역할 선택 → 기본 메뉴 자동 로드 → 관리자 커스터마이즈 → 저장

---

## 14. 다음 단계 (Phase 5 Preview)

Phase 5는 **NL2SQL 권한 필터 + 프론트엔드** 입니다:

```
Phase 5 산출물:
  [MOD] app/core/database/sql_executor.py   ← inject_permission_filter() (scope_type 기반)
  [MOD] app/graphs/nl2sql/nodes.py          ← execute_sql_node에 UserContext 전달
  [MOD] app/graphs/agent/tools/sql_tool.py  ← scope 필터 적용
  [NEW] frontend/src/views/LoginView.vue    ← 로그인 화면
  [MOD] frontend/src/components/layout/AppSidebar.vue ← 동적 메뉴 렌더링
  [NEW] frontend/src/views/admin/UsersView.vue    ← 사용자 관리 (메뉴 권한 할당 포함)
  [NEW] frontend/src/views/admin/MenusView.vue    ← 메뉴/권한 관리
  [NEW] frontend/src/views/admin/RolesView.vue    ← 역할 관리
  [NEW] frontend/src/views/admin/TenantsView.vue  ← 테넌트 관리
```

---

## 구현 순서 요약

| Step | 파일 | 유형 | 설명 |
|:----:|------|:----:|------|
| 1 | `app/models/auth.py` | MOD | UserInfo/UserContext v2.0 전환 |
| 1 | `app/models/user.py` | MOD | role_id 1:N, 메뉴 권한 모델 |
| 1 | `app/models/menu.py` | NEW | 메뉴 관리 Pydantic 모델 |
| 2 | `app/core/security/permission.py` | MOD | require_menu_permission 추가 |
| 3 | `app/api/services/user_service.py` | MOD | role_id + tb_user_menu 기반 |
| 4 | `app/api/services/role_service.py` | MOD | 단순화 (permission 제거) |
| 5 | `app/api/services/menu_service.py` | NEW | 메뉴 트리 CRUD |
| 6 | `app/api/services/tenant_service.py` | - | 변경 없음 |
| 7 | `app/api/routes/users.py` | MOD | require_menu_permission + menus API |
| 7 | `app/api/routes/roles.py` | MOD | 단순화 + default-menus |
| 7 | `app/api/routes/menus.py` | NEW | 메뉴 관리 API |
| 7 | `app/api/routes/tenants.py` | MOD | require_menu_permission |
| 8 | 기존 라우트 (documents, settings, codes) | MOD | require_menu_permission |
| 9 | `app/api/services/auth_service.py` | MOD | get_user_with_menus |
| 10 | `app/main.py` | MOD | menus 라우터 등록 |
