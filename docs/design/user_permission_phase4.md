# Phase 4 구현 가이드: 사용자/역할/테넌트 관리 API (CRUD)

> **문서 버전**: 1.0
> **작성일**: 2026-02-12
> **상위 문서**: `docs/design/user_permission_system.md`
> **선행 조건**: Phase 3 완료 (인증 API + 인증 미들웨어)
> **목적**: Phase 4(관리 API 18개 + 기존 API 권한 적용)의 실제 구현 절차를 코드 레벨에서 상세 설명

---

## 목차

1. [Phase 4 개요](#1-phase-4-개요)
2. [Step 1: `user_service.py` — 사용자 관리 서비스](#2-step-1-user_service)
3. [Step 2: `role_service.py` — 역할 관리 서비스](#3-step-2-role_service)
4. [Step 3: `tenant_service.py` — 테넌트 관리 서비스](#4-step-3-tenant_service)
5. [Step 4: `users.py` (routes) — 사용자 관리 API](#5-step-4-users-routes)
6. [Step 5: `roles.py` (routes) — 역할 관리 API](#6-step-5-roles-routes)
7. [Step 6: `tenants.py` (routes) — 테넌트 관리 API](#7-step-6-tenants-routes)
8. [Step 7: 기존 API 권한 적용](#8-step-7-기존-api-권한-적용)
9. [Step 8: `main.py` 수정 — 라우터 등록](#9-step-8-main-수정)
10. [검증 체크리스트](#10-검증-체크리스트)
11. [다음 단계 (Phase 5 Preview)](#11-다음-단계)

---

## 1. Phase 4 개요

### 1.1 무엇을 하는가

Phase 4는 관리자가 **사용자, 역할, 테넌트를 CRUD 관리**할 수 있는 API 18개를 구현하고, **기존 API에 권한 검사를 적용**합니다.

```
Phase 4 산출물:
  [NEW] app/api/services/user_service.py     ← 사용자 관리 비즈니스 로직
  [NEW] app/api/services/role_service.py     ← 역할 관리 비즈니스 로직
  [NEW] app/api/services/tenant_service.py   ← 테넌트 관리 비즈니스 로직
  [NEW] app/api/routes/users.py              ← 사용자 관리 API (7개 엔드포인트)
  [NEW] app/api/routes/roles.py              ← 역할 관리 API (6개 엔드포인트)
  [NEW] app/api/routes/tenants.py            ← 테넌트 관리 API (5개 엔드포인트)
  [MOD] app/main.py                          ← 라우터 등록 (3개 추가)
```

### 1.2 핵심 설계 원칙

```
┌──────────────────────────────────────────────────────────────────────┐
│  permission = "기능 접근 여부" (무엇을 할 수 있는가)                    │
│  scope_type = "데이터 범위"   (어디까지 볼 수 있는가)                  │
│                                                                       │
│  두 축 분리:                                                          │
│    admin:users 권한 + GLOBAL scope → 전체 사용자 관리                 │
│    admin:users 권한 + TENANT scope → 자기 테넌트 사용자만 관리         │
│    admin:users 권한 없음           → 사용자 관리 불가                  │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 역할별 접근 범위 요약

| 역할 | scope_type | 사용자 관리 | 역할 관리 | 테넌트 관리 | 설정 관리 |
|------|-----------|------------|----------|------------|----------|
| SYSTEM_ADMIN | GLOBAL | 전체 | O | O | O |
| TENANT_ADMIN | TENANT | 자기 테넌트 내 | X | X | X |
| USER | USER | 본인만 | X | X | X |

### 1.4 의존 관계

```
Phase 2 (Core Security)
  ├── permission.py   → require_permission(), require_any_permission()
  ├── dependencies.py → get_current_active_user(), get_optional_user()
  └── password.py     → hash_password()

Phase 3 (인증)
  ├── auth_service.py → get_user_with_permissions() (참조용)
  └── middleware/auth.py → request.state.current_user

Phase 4 (이번 구현)
  ├── user_service.py   → 사용자 CRUD + scope 제한
  ├── role_service.py   → 역할 CRUD + 권한 할당
  ├── tenant_service.py → 테넌트 CRUD
  ├── routes/users.py   → require_permission("admin:users")
  ├── routes/roles.py   → require_permission("admin:users")
  └── routes/tenants.py → require_permission("admin:tenants")
```

---

## 2. Step 1: `user_service.py` — 사용자 관리 서비스

> **파일**: `app/api/services/user_service.py`
> **의존성**: db_manager, password.py, errors, logger
> **모델**: `app/models/user.py` (UserCreate, UserUpdate, UserResponse 등)

### 2.1 클래스 구조

```python
class UserService:
    """사용자 관리 비즈니스 로직"""

    def list_users(self, current_user, limit, offset, tenant_id_filter, is_active_filter) -> dict
    def get_user(self, user_id, current_user) -> dict
    def create_user(self, data: UserCreate, current_user) -> dict
    def update_user(self, user_id, data: UserUpdate, current_user) -> dict
    def delete_user(self, user_id, current_user) -> bool
    def assign_roles(self, user_id, role_ids, current_user) -> list
    def get_user_permissions(self, user_id, current_user) -> dict

    # 내부 헬퍼
    def _check_scope_access(self, target_user_id_or_tenant_id, current_user) -> None
    def _apply_scope_filter(self, base_sql, current_user) -> (str, list)

user_service = UserService()
```

### 2.2 scope_type 제한 로직

**모든 메서드에서 공통으로 적용**:

```python
def _check_scope_access(self, target_tenant_id: int, current_user: UserContext) -> None:
    """scope_type에 따른 접근 범위 검증"""
    # GLOBAL: 제한 없음
    if current_user.scope_type == "GLOBAL":
        return

    # TENANT: 자기 테넌트만
    if current_user.scope_type == "TENANT":
        if target_tenant_id != current_user.tenant_id:
            raise APIException(ErrorCode.FORBIDDEN, "다른 테넌트의 데이터에 접근할 수 없습니다")
        return

    # USER: 본인만 (사용자 관리 권한이 없으므로 여기 도달 안함)
    raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")
```

### 2.3 메서드별 상세

#### `list_users(current_user, limit, offset, tenant_id_filter, is_active_filter)`

```sql
-- 기본 쿼리
SELECT u.user_id, u.login_id, u.email, u.display_name, u.tenant_id,
       t.tenant_name, u.is_active, u.is_superuser,
       u.last_login_at, u.created_at, u.updated_at
FROM tb_user u
LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id
WHERE 1=1

-- scope_type별 추가 조건:
-- GLOBAL  → 추가 조건 없음 (전체 사용자)
-- TENANT  → AND u.tenant_id = {current_user.tenant_id}

-- 필터 조건 (선택):
-- AND u.tenant_id = {tenant_id_filter}  (GLOBAL만 사용 가능)
-- AND u.is_active = {is_active_filter}

ORDER BY u.created_at DESC
LIMIT {limit} OFFSET {offset}
```

- **총 건수 (total)**: 같은 조건으로 `SELECT COUNT(*)` 별도 실행
- **역할 목록**: 각 user의 roles는 별도 JOIN 쿼리 또는 서브쿼리로 조회
- **반환**: `{"total": N, "items": [UserResponse, ...]}`

#### `get_user(user_id, current_user)`

```sql
SELECT u.*, t.tenant_name
FROM tb_user u
LEFT JOIN tb_tenant t ON u.tenant_id = t.tenant_id
WHERE u.user_id = %s
```

- scope 검증: `_check_scope_access(user.tenant_id, current_user)`
- 역할 목록 조회:
```sql
SELECT r.role_id, r.role_code, r.role_name, r.scope_type
FROM tb_user_role ur
JOIN tb_role r ON ur.role_id = r.role_id
WHERE ur.user_id = %s
```

#### `create_user(data: UserCreate, current_user)`

1. 중복 검사: `login_id`, `email` UNIQUE 제약 → `DUPLICATE_ERROR`
2. **TENANT scope 강제**: `current_user.scope_type == "TENANT"` → `data.tenant_id = current_user.tenant_id`
3. 비밀번호 해시: `hash_password(data.password)`
4. INSERT:
```sql
INSERT INTO tb_user (login_id, email, password_hash, display_name, tenant_id, is_active)
VALUES (%s, %s, %s, %s, %s, %s)
RETURNING user_id
```
5. 역할 할당: `data.role_ids`가 있으면 `tb_user_role` INSERT
6. 반환: 생성된 UserResponse

#### `update_user(user_id, data: UserUpdate, current_user)`

1. 대상 사용자 조회 → 없으면 `NOT_FOUND`
2. scope 검증: `_check_scope_access(user.tenant_id, current_user)`
3. **superuser 보호**: `is_superuser=True`인 사용자는 다른 관리자가 수정 불가 (본인만 가능)
4. 동적 UPDATE (변경된 필드만):
```sql
UPDATE tb_user SET email=%s, display_name=%s, ... , updated_at=NOW()
WHERE user_id = %s
```

#### `delete_user(user_id, current_user)`

1. 대상 사용자 조회 → scope 검증
2. **superuser 보호**: superuser 삭제 불가
3. **자기 자신 삭제 불가**: `current_user.user_id == user_id` → 에러
4. 삭제 (CASCADE로 tb_user_role, tb_user_session 자동 삭제):
```sql
DELETE FROM tb_user WHERE user_id = %s
```

#### `assign_roles(user_id, role_ids, current_user)`

1. **GLOBAL만 가능**: `current_user.scope_type != "GLOBAL"` → `FORBIDDEN`
2. role_ids 유효성 검사: 존재하는 역할인지 확인
3. 기존 역할 전체 삭제 후 새로 할당 (replace 방식):
```sql
DELETE FROM tb_user_role WHERE user_id = %s;
INSERT INTO tb_user_role (user_id, role_id, tenant_id, granted_by)
VALUES (%s, %s, %s, %s)
```
4. `tenant_id`: 대상 사용자의 tenant_id 또는 NULL (GLOBAL 역할)

#### `get_user_permissions(user_id, current_user)`

1. scope 검증 또는 본인 확인
2. auth_service.get_user_with_permissions 재활용:
```python
from app.api.services.auth_service import auth_service
return auth_service.get_user_with_permissions(user_id, request_id)
```

---

## 3. Step 2: `role_service.py` — 역할 관리 서비스

> **파일**: `app/api/services/role_service.py`
> **의존성**: db_manager, errors, logger
> **모델**: `app/models/user.py` (RoleCreate, RoleUpdate, RoleResponse 등)

### 3.1 클래스 구조

```python
class RoleService:
    """역할 관리 비즈니스 로직"""

    def list_roles(self, request_id) -> dict
    def get_role(self, role_id, request_id) -> dict
    def create_role(self, data: RoleCreate, current_user, request_id) -> dict
    def update_role(self, role_id, data: RoleUpdate, current_user, request_id) -> dict
    def delete_role(self, role_id, current_user, request_id) -> bool
    def assign_permissions(self, role_id, permission_ids, current_user, request_id) -> list

role_service = RoleService()
```

### 3.2 메서드별 상세

#### `list_roles(request_id)`

```sql
SELECT r.role_id, r.role_code, r.role_name, r.description,
       r.scope_type, r.is_system, r.sort_order, r.created_at
FROM tb_role r
ORDER BY r.sort_order, r.role_id
```

- 각 역할의 권한 목록은 별도 조회:
```sql
SELECT p.permission_id, p.permission_code, p.permission_name, p.category
FROM tb_role_permission rp
JOIN tb_permission p ON rp.permission_id = p.permission_id
WHERE rp.role_id = %s
```

#### `get_role(role_id, request_id)`

```sql
SELECT r.*,
  (SELECT COUNT(*) FROM tb_user_role ur WHERE ur.role_id = r.role_id) as user_count
FROM tb_role r
WHERE r.role_id = %s
```

+ 권한 목록 조회 (list_roles와 동일한 쿼리)

#### `create_role(data: RoleCreate, current_user, request_id)`

1. 중복 검사: `role_code` UNIQUE → `DUPLICATE_ERROR`
2. INSERT:
```sql
INSERT INTO tb_role (role_code, role_name, description, scope_type, sort_order)
VALUES (%s, %s, %s, %s, %s)
RETURNING role_id
```
3. 권한 할당: `data.permission_ids`가 있으면 `tb_role_permission` INSERT

#### `update_role(role_id, data: RoleUpdate, current_user, request_id)`

1. 대상 역할 조회 → 없으면 `NOT_FOUND`
2. **시스템 역할 보호**: `is_system=True`인 역할의 `role_code`, `scope_type` 변경 불가
3. 동적 UPDATE

#### `delete_role(role_id, current_user, request_id)`

1. 대상 역할 조회
2. **시스템 역할 삭제 불가**: `is_system=True` → `BAD_REQUEST`
3. **사용 중 역할 삭제 불가**: `tb_user_role`에 참조 있으면 → `BAD_REQUEST`
4. DELETE (CASCADE로 tb_role_permission 자동 삭제)

#### `assign_permissions(role_id, permission_ids, current_user, request_id)`

1. 역할 존재 확인
2. **시스템 역할의 기본 권한 보호**: `is_system=True`인 역할도 권한 변경 허용 (단, 관리자만)
3. permission_ids 유효성: 존재하는 권한인지 확인
4. replace 방식:
```sql
DELETE FROM tb_role_permission WHERE role_id = %s;
INSERT INTO tb_role_permission (role_id, permission_id)
VALUES (%s, %s)
```

---

## 4. Step 3: `tenant_service.py` — 테넌트 관리 서비스

> **파일**: `app/api/services/tenant_service.py`
> **의존성**: db_manager, errors, logger
> **모델**: `app/models/tenant.py` (TenantCreate, TenantUpdate, TenantResponse 등)

### 4.1 클래스 구조

```python
class TenantService:
    """테넌트 관리 비즈니스 로직"""

    def list_tenants(self, request_id) -> dict
    def get_tenant(self, tenant_id, request_id) -> dict
    def create_tenant(self, data: TenantCreate, current_user, request_id) -> dict
    def update_tenant(self, tenant_id, data: TenantUpdate, current_user, request_id) -> dict
    def delete_tenant(self, tenant_id, current_user, request_id) -> bool

tenant_service = TenantService()
```

### 4.2 메서드별 상세

#### `list_tenants(request_id)`

```sql
SELECT t.tenant_id, t.tenant_code, t.tenant_name, t.is_active,
       t.metadata, t.created_at, t.updated_at,
       (SELECT COUNT(*) FROM tb_user u WHERE u.tenant_id = t.tenant_id) as user_count
FROM tb_tenant t
ORDER BY t.tenant_id
```

#### `get_tenant(tenant_id, request_id)`

동일 쿼리 + `WHERE t.tenant_id = %s`

#### `create_tenant(data: TenantCreate, current_user, request_id)`

1. 중복 검사: `tenant_code` UNIQUE → `DUPLICATE_ERROR`
2. INSERT:
```sql
INSERT INTO tb_tenant (tenant_code, tenant_name, is_active, metadata)
VALUES (%s, %s, %s, %s::jsonb)
RETURNING tenant_id
```

#### `update_tenant(tenant_id, data: TenantUpdate, current_user, request_id)`

1. 대상 테넌트 조회 → 없으면 `NOT_FOUND`
2. 동적 UPDATE (변경 필드만)

#### `delete_tenant(tenant_id, current_user, request_id)`

1. 대상 테넌트 조회
2. **소속 사용자 존재 시 삭제 불가**: `tb_user.tenant_id`로 사용자 존재 확인 → `BAD_REQUEST`
3. 소프트 삭제 (is_active=false) 또는 하드 삭제 선택
   - 권장: `UPDATE tb_tenant SET is_active = false` (비활성화)
   - 사용자가 없는 경우에만 하드 삭제 가능

---

## 5. Step 4: `users.py` (routes) — 사용자 관리 API

> **파일**: `app/api/routes/users.py`
> **prefix**: `/api/v1/users`
> **의존성**: user_service, require_permission, get_current_active_user

### 5.1 엔드포인트 정의

```python
from fastapi import APIRouter, Depends, Query, Request, status
from app.api.services.user_service import user_service
from app.core.security.permission import require_permission
from app.core.security.dependencies import get_current_active_user
from app.core.errors import success_response
from app.models.auth import UserContext
from app.models.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserRoleAssign, PermissionResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])
```

| Method | Path | Depends | 설명 |
|--------|------|---------|------|
| GET | `/` | `require_permission("admin:users")` | 사용자 목록 |
| POST | `/` | `require_permission("admin:users")` | 사용자 생성 |
| GET | `/{user_id}` | `get_current_active_user` | 사용자 상세 (본인 또는 admin:users) |
| PUT | `/{user_id}` | `require_permission("admin:users")` | 사용자 수정 |
| DELETE | `/{user_id}` | `require_permission("admin:users")` | 사용자 삭제 |
| PUT | `/{user_id}/roles` | `require_permission("admin:users")` | 역할 할당 (GLOBAL만) |
| GET | `/{user_id}/permissions` | `get_current_active_user` | 권한 조회 (본인 또는 admin:users) |

### 5.2 본인 조회 허용 로직

`GET /{user_id}`와 `GET /{user_id}/permissions`는 **본인이면 권한 없이도 조회 가능**:

```python
@router.get("/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
    current_user: UserContext = Depends(get_current_active_user),
):
    # 본인이 아니면 admin:users 권한 필요
    if current_user.user_id != user_id:
        if not current_user.has_permission("admin:users"):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")

    request_id = getattr(request.state, "request_id", "")
    result = user_service.get_user(user_id, current_user, request_id)
    return success_response(result)
```

### 5.3 Query Parameters

**GET /users** (목록):
```
?limit=20          (기본값 20, 최대 100)
&offset=0          (기본값 0)
&tenant_id=2       (테넌트 필터 — GLOBAL만 사용 가능)
&is_active=true    (활성화 필터)
```

---

## 6. Step 5: `roles.py` (routes) — 역할 관리 API

> **파일**: `app/api/routes/roles.py`
> **prefix**: `/api/v1/roles`
> **권한**: 모든 엔드포인트에 `require_permission("admin:users")` 적용

### 6.1 엔드포인트 정의

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 역할 목록 (전체 권한 포함) |
| POST | `/` | 역할 생성 |
| GET | `/{role_id}` | 역할 상세 (권한 포함) |
| PUT | `/{role_id}` | 역할 수정 |
| DELETE | `/{role_id}` | 역할 삭제 (시스템 역할 불가) |
| PUT | `/{role_id}/permissions` | 권한 할당 |

### 6.2 추가 엔드포인트: 권한 목록

역할에 권한을 할당하려면 **사용 가능한 권한 목록**이 필요합니다:

```python
@router.get("/permissions")
async def list_permissions(
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """사용 가능한 권한 목록 조회"""
    # SELECT * FROM tb_permission ORDER BY category, permission_id
```

> **주의**: `/permissions`는 고정 경로이므로 `/{role_id}` 파라미터 경로보다 **위에** 배치해야 합니다.

---

## 7. Step 6: `tenants.py` (routes) — 테넌트 관리 API

> **파일**: `app/api/routes/tenants.py`
> **prefix**: `/api/v1/tenants`
> **권한**: 모든 엔드포인트에 `require_permission("admin:tenants")` 적용

### 7.1 엔드포인트 정의

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 테넌트 목록 |
| POST | `/` | 테넌트 생성 |
| GET | `/{tenant_id}` | 테넌트 상세 |
| PUT | `/{tenant_id}` | 테넌트 수정 |
| DELETE | `/{tenant_id}` | 테넌트 삭제 (비활성화) |

> **참고**: 테넌트 관리는 `admin:tenants` 권한이 필요하며, 이 권한은 SYSTEM_ADMIN만 보유합니다.

---

## 8. Step 7: 기존 API 권한 적용

> Phase 4에서는 기존 API에 권한 의존성을 추가합니다.
> **중요**: Phase 3a(선택적 모드)를 유지하면서 `get_optional_user`를 사용하여 하위호환성 보장

### 8.1 적용 대상 및 방법

| 기존 라우트 파일 | 적용 방법 | 권한 |
|-----------------|----------|------|
| `search.py` | `get_optional_user` 추가 | 인증 선택적 (Phase 3a 유지) |
| `agent.py` | `get_optional_user` 추가 | 인증 선택적 (Phase 3a 유지) |
| `documents.py` | `require_permission` 추가 | `document:read`, `document:write`, `document:delete` |
| `settings.py` | `require_permission` 추가 | `admin:settings` |
| `codes.py` | `require_permission` 추가 | `admin:settings` |
| `history.py` | `get_optional_user` 추가 | 인증 선택적 (Phase 3a 유지) |

### 8.2 적용 패턴

**패턴 A — 필수 권한** (documents, settings, codes):

```python
from app.core.security.permission import require_permission

@router.post("")
async def save_document(
    doc: DocumentSaveRequest,
    current_user: UserContext = Depends(require_permission("document:write")),
):
    # current_user 사용 가능 (scope 제한 등)
    ...
```

**패턴 B — 선택적 인증** (search, agent, history):

```python
from app.core.security.dependencies import get_optional_user

@router.post("/search")
async def search(
    search_request: SearchRequest,
    request: Request,
    current_user: Optional[UserContext] = Depends(get_optional_user),
):
    # current_user가 None이면 anonymous 사용자
    # current_user가 있으면 인증된 사용자 (향후 scope 제한에 활용)
    ...
```

### 8.3 documents.py 권한 매핑

| 엔드포인트 | 현재 | 변경 후 |
|-----------|------|--------|
| `POST /` (저장) | 인증 없음 | `require_permission("document:write")` |
| `GET /` (목록) | 인증 없음 | `require_permission("document:read")` |
| `GET /{doc_id}` (상세) | 인증 없음 | `require_permission("document:read")` |
| `PUT /{doc_id}` (수정) | 인증 없음 | `require_permission("document:write")` |
| `DELETE /{doc_id}` (삭제) | 인증 없음 | `require_permission("document:delete")` |
| `POST /bulk-delete` | 인증 없음 | `require_permission("document:delete")` |
| `POST /embedding/execute` | 인증 없음 | `require_permission("document:write")` |
| `POST /embedding/preview` | 인증 없음 | `require_permission("document:read")` |

### 8.4 settings.py / codes.py 권한 매핑

모든 엔드포인트에 `require_permission("admin:settings")` 적용.

---

## 9. Step 8: `main.py` 수정 — 라우터 등록

```python
# import 추가
from app.api.routes import users, roles, tenants

# 라우터 등록 (기존 라우터 아래에 추가)
app.include_router(users.router)      # 사용자 관리 API
app.include_router(roles.router)      # 역할 관리 API
app.include_router(tenants.router)    # 테넌트 관리 API
```

### 9.1 api_info() 엔드포인트 업데이트

`/api/v1/info` 응답에 새 엔드포인트 정보 추가:

```python
"users": {
    "GET /api/v1/users": "사용자 목록 조회",
    "POST /api/v1/users": "사용자 생성",
    "GET /api/v1/users/{user_id}": "사용자 상세 조회",
    "PUT /api/v1/users/{user_id}": "사용자 수정",
    "DELETE /api/v1/users/{user_id}": "사용자 삭제",
    "PUT /api/v1/users/{user_id}/roles": "역할 할당",
    "GET /api/v1/users/{user_id}/permissions": "권한 조회",
},
"roles": {
    "GET /api/v1/roles": "역할 목록",
    "POST /api/v1/roles": "역할 생성",
    "GET /api/v1/roles/permissions": "사용 가능한 권한 목록",
    "GET /api/v1/roles/{role_id}": "역할 상세",
    "PUT /api/v1/roles/{role_id}": "역할 수정",
    "DELETE /api/v1/roles/{role_id}": "역할 삭제",
    "PUT /api/v1/roles/{role_id}/permissions": "권한 할당",
},
"tenants": {
    "GET /api/v1/tenants": "테넌트 목록",
    "POST /api/v1/tenants": "테넌트 생성",
    "GET /api/v1/tenants/{tenant_id}": "테넌트 상세",
    "PUT /api/v1/tenants/{tenant_id}": "테넌트 수정",
    "DELETE /api/v1/tenants/{tenant_id}": "테넌트 삭제",
},
```

---

## 10. 검증 체크리스트

### 10.1 사용자 관리

- [ ] 사용자 목록 조회 (GLOBAL: 전체, TENANT: 자기 테넌트만)
- [ ] 사용자 생성 (TENANT scope → 자기 테넌트로 강제)
- [ ] 사용자 상세 조회 (본인 또는 admin:users 권한)
- [ ] 사용자 수정 (scope 범위 내)
- [ ] 사용자 삭제 (superuser 삭제 불가, 본인 삭제 불가)
- [ ] 역할 할당 (GLOBAL만 가능)
- [ ] 권한 조회 (본인 또는 admin:users 권한)

### 10.2 역할 관리

- [ ] 역할 목록 조회 (권한 포함)
- [ ] 역할 생성
- [ ] 역할 상세 조회
- [ ] 역할 수정 (시스템 역할 code/scope 변경 불가)
- [ ] 역할 삭제 (시스템 역할 불가, 사용 중 불가)
- [ ] 권한 할당
- [ ] 사용 가능한 권한 목록 조회

### 10.3 테넌트 관리

- [ ] 테넌트 목록 조회
- [ ] 테넌트 생성
- [ ] 테넌트 상세 조회
- [ ] 테넌트 수정
- [ ] 테넌트 삭제 (소속 사용자 있으면 불가)

### 10.4 기존 API 권한

- [ ] documents.py — 권한 없으면 401/403
- [ ] settings.py — admin:settings 없으면 403
- [ ] codes.py — admin:settings 없으면 403
- [ ] search.py / agent.py — 토큰 없이도 동작 (Phase 3a 유지)

### 10.5 통합 시나리오

- [ ] SYSTEM_ADMIN → 모든 관리 API 정상 동작
- [ ] TENANT_ADMIN → 사용자 관리 시 자기 테넌트만 조회/생성
- [ ] TENANT_ADMIN → 역할/테넌트/설정 관리 → 403 Forbidden
- [ ] USER → 본인 정보만 조회 가능
- [ ] 미인증 사용자 → 관리 API 401 Unauthorized

---

## 11. 다음 단계 (Phase 5 Preview)

Phase 5는 **NL2SQL 권한 필터 주입 (Row-Level Security)** 입니다:

```
Phase 5 산출물:
  [MOD] app/core/database/sql_executor.py   ← inject_permission_filter()
  [MOD] app/graphs/nl2sql/nodes.py          ← execute_sql_node 수정
  [MOD] app/graphs/agent/tools/sql_tool.py  ← 필터 적용
  [MOD] app/middleware/history.py            ← UserContext에서 읽기
```

**핵심**: 사용자의 scope_type에 따라 NL2SQL이 생성한 SQL에 자동으로 WHERE 조건(tenant_id, emp_id)을 추가하여, TENANT는 자기 테넌트 데이터만, USER는 본인 데이터만 조회되도록 합니다.

---

## 구현 순서 요약

| Step | 파일 | 유형 | 설명 |
|------|------|------|------|
| 1 | `app/api/services/user_service.py` | NEW | 사용자 관리 서비스 |
| 2 | `app/api/services/role_service.py` | NEW | 역할 관리 서비스 |
| 3 | `app/api/services/tenant_service.py` | NEW | 테넌트 관리 서비스 |
| 4 | `app/api/routes/users.py` | NEW | 사용자 관리 API (7개) |
| 5 | `app/api/routes/roles.py` | NEW | 역할 관리 API (7개, 권한목록 포함) |
| 6 | `app/api/routes/tenants.py` | NEW | 테넌트 관리 API (5개) |
| 7 | `app/api/routes/documents.py` | MOD | 권한 적용 |
| 8 | `app/api/routes/settings.py` | MOD | 권한 적용 |
| 9 | `app/api/routes/codes.py` | MOD | 권한 적용 |
| 10 | `app/main.py` | MOD | 라우터 등록 |
| 11 | `tests/test_phase4.py` | NEW | 검증 테스트 |
