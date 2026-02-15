# 사용자/역할/권한 관리 시스템 설계서

> **문서 버전**: 3.0
> **작성일**: 2026-02-15
> **상태**: 구현 완료 (NL2SQL 권한 필터 제외)

---

## 1. 개요

### 1.1 핵심 설계 원칙

```
tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가"  (기능 접근)
tb_role.role_code = "어디까지 볼 수 있는가"       (데이터 범위)

같은 메뉴 권한이라도 role_code에 따라 보이는 데이터가 다름
예: 사용자 관리 Read + TENANT → 자기 테넌트 사용자만
    사용자 관리 Read + GLOBAL → 전체 사용자
```

### 1.2 권한 계층 구조

| 구분 | 시스템 관리자 | 테넌트 관리자 | 일반 사용자 |
|------|:---:|:---:|:---:|
| `role_code` | GLOBAL | TENANT | USER |
| `landing_page` | /admin/dashboard | /admin/dashboard | /chat |
| `is_superuser` | true | false | false |
| `tenant_id` | GLOBAL 테넌트 | 소속 테넌트 | 소속 테넌트 |
| 메뉴 접근 | 전체 | 제한적 | 채팅만 |
| 데이터 범위 | 전체 | 테넌트 내 | 본인만 |

---

## 2. 데이터베이스 설계

### 2.1 ERD

```
                    ┌──────────────────────┐
                    │     tb_tenant        │
                    ├──────────────────────┤
                    │ tenant_id (PK)       │
                    │ tenant_code (UK)     │
                    │ tenant_name          │
                    │ is_active            │
                    │ is_system            │
                    │ metadata (JSONB)     │
                    └──────────┬───────────┘
                               │ 1:N
┌───────────────┐  N ┌─────────┴────────────┐ N:1  ┌────────────────────────┐
│   tb_menu     │◄───│      tb_user         │─────►│      tb_role           │
├───────────────┤    ├──────────────────────┤      ├────────────────────────┤
│ menu_id (PK)  │    │ user_id (PK)         │      │ role_id (PK)           │
│ parent_menu_id│    │ login_id (UK)        │      │ role_code (UK)         │
│ menu_code(UK) │    │ email (UK)           │      │ role_name              │
│ menu_name     │    │ password_hash        │      │ landing_page           │
│ menu_type     │    │ display_name         │      │ is_system              │
│ menu_path     │    │ tenant_id (FK)       │      │ sort_order             │
│ api_pattern   │    │ role_id (FK)         │      └────────────────────────┘
│ icon          │    │ is_superuser         │
│ sort_order    │    │ is_active            │
│ depth         │    └──────────┬───────────┘
│ is_active     │               │ 1
└───────┬───────┘               │
        │ 1                     │ N
        │ N  ┌──────────────────┴──────┐     ┌───────────────────────┐
        └───►│    tb_user_menu         │     │   tb_user_session     │
             │  (유일한 권한 체크 테이블) │     ├───────────────────────┤
             ├─────────────────────────┤     │ session_id (PK, UUID) │
             │ user_id (PK, FK)        │     │ user_id (FK CASCADE)  │
             │ menu_id (PK, FK)        │     │ refresh_token         │
             │ can_create              │     │ expires_at            │
             │ can_read                │     └───────────────────────┘
             │ can_update              │
             │ can_delete              │
             │ can_export              │
             │ granted_by (FK SET NULL)│
             └─────────────────────────┘
```

### 2.2 테이블 명세

#### tb_tenant

| 컬럼 | 타입 | 설명 |
|------|------|------|
| tenant_id | BIGSERIAL PK | 테넌트 ID |
| tenant_code | VARCHAR(50) UK | 테넌트 코드 |
| tenant_name | VARCHAR(200) | 테넌트명 |
| is_active | BOOLEAN DEFAULT true | 활성화 여부 |
| **is_system** | **BOOLEAN DEFAULT false** | **시스템 테넌트 (삭제/비활성화 불가)** |
| metadata | JSONB | 추가 정보 (현재 미사용) |

> GLOBAL 테넌트: `is_system = true`, 삭제 및 비활성화 차단

#### tb_role

| 컬럼 | 타입 | 설명 |
|------|------|------|
| role_id | BIGSERIAL PK | 역할 ID |
| role_code | VARCHAR(50) UK | GLOBAL / TENANT / USER |
| role_name | VARCHAR(100) | 역할명 |
| landing_page | VARCHAR(200) | 로그인 후 이동 경로 |
| is_system | BOOLEAN DEFAULT false | 시스템 역할 (삭제 불가) |
| sort_order | INT DEFAULT 0 | 정렬 (1=GLOBAL, 2=TENANT, 3=USER) |

> `sort_order`가 역할 계층을 결정: 낮을수록 상위

#### tb_user

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | BIGSERIAL PK | 사용자 ID |
| login_id | VARCHAR(100) UK | 로그인 ID |
| email | VARCHAR(255) UK | 이메일 |
| password_hash | VARCHAR(255) | bcrypt 해시 |
| display_name | VARCHAR(100) | 표시 이름 |
| tenant_id | BIGINT FK | 소속 테넌트 |
| role_id | BIGINT FK NOT NULL | 역할 (1:N) |
| is_superuser | BOOLEAN DEFAULT false | RBAC 비상 우회 |
| is_active | BOOLEAN DEFAULT true | 활성화 여부 |

> `is_superuser`: 역할/메뉴 설정이 꼬였을 때 비상 접근 보장 (Django와 동일 패턴)

#### tb_menu

| 컬럼 | 타입 | 설명 |
|------|------|------|
| menu_id | BIGSERIAL PK | 메뉴 ID |
| parent_menu_id | BIGINT FK(self) | 상위 메뉴 (NULL=루트) |
| menu_code | VARCHAR(50) UK | 메뉴 코드 (예: USER_MGMT) |
| menu_name | VARCHAR(100) | 표시명 |
| menu_type | VARCHAR(20) | DIRECTORY / PAGE / API |
| menu_path | VARCHAR(200) | 프론트엔드 경로 |
| api_pattern | VARCHAR(200) | API 경로 패턴 |
| depth | INT DEFAULT 0 | 트리 깊이 (0=루트) |
| sort_order | INT | 정렬 순서 |
| is_active | BOOLEAN DEFAULT true | 활성 여부 |

#### tb_user_menu (핵심 권한 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | BIGINT PK, FK CASCADE | 사용자 삭제 시 자동 삭제 |
| menu_id | BIGINT PK, FK | 메뉴 ID |
| can_create | BOOLEAN DEFAULT false | 등록 |
| can_read | BOOLEAN DEFAULT true | 조회 |
| can_update | BOOLEAN DEFAULT false | 수정 |
| can_delete | BOOLEAN DEFAULT false | 삭제 |
| can_export | BOOLEAN DEFAULT false | 내보내기 |
| granted_by | BIGINT FK SET NULL | 부여자 (삭제 시 NULL) |

### 2.3 기본 메뉴 트리

```
[DIR] ADMIN (관리자)
  ├── [PAGE] DASHBOARD        /admin/dashboard
  ├── [PAGE] CHAT             /admin/chat
  ├── [PAGE] DOCUMENTS        /admin/documents
  ├── [PAGE] USER_MGMT        /admin/users
  ├── [PAGE] MENU_MGMT        /admin/menus
  ├── [PAGE] ROLE_MGMT        /admin/roles
  ├── [PAGE] TENANT_MGMT      /admin/tenants
  ├── [PAGE] SETTINGS         /admin/settings
  ├── [PAGE] CODES            /admin/codes
  └── [PAGE] HISTORY          /admin/history
[DIR] USER_AREA (사용자)
  └── [PAGE] USER_CHAT        /chat
[DIR] API_ACCESS (API)
  ├── [API] AGENT_API         /api/v1/agent
  ├── [API] RAG_API           /api/v1/rag
  └── [API] NL2SQL_API        /api/v1/nl2sql
```

### 2.4 역할별 기본 메뉴 권한

| 메뉴 | GLOBAL | TENANT | USER |
|------|:---:|:---:|:---:|
| 대시보드 | CRUDE | R | - |
| AI 채팅 | CR | CR | - |
| 문서 관리 | CRUDE | CRUDE | - |
| 사용자 관리 | CRUDE | CRU | - |
| 메뉴/권한 관리 | CRUDE | - | - |
| 역할 관리 | CRUDE | - | - |
| 테넌트 관리 | CRUDE | - | - |
| 시스템 설정 | RU | - | - |
| 코드 관리 | CRUD | - | - |
| 검색 이력 | RE | RE | - |
| 채팅 | CR | CR | CR |
| API (Agent/RAG/NL2SQL) | CR | CR | CR |

> C=Create, R=Read, U=Update, D=Delete, E=Export

### 2.5 FK CASCADE 동작

사용자 삭제 시:

| 테이블 | FK 동작 | 결과 |
|--------|---------|------|
| tb_user_menu (user_id) | CASCADE | 메뉴 권한 자동 삭제 |
| tb_user_menu (granted_by) | SET NULL | 부여자 정보만 NULL |
| tb_user_session | CASCADE | 세션 자동 삭제 |
| tb_api_history | FK 없음 | 이력 보존 (고아 레코드) |

---

## 3. 인증 시스템

### 3.1 JWT 인증 흐름

```
POST /api/v1/auth/login → 비밀번호 검증(bcrypt) → JWT 발급
  ├── Access Token (30분) - user_id, role_code, tenant_id 포함
  └── Refresh Token (7일) - session_id 포함, DB 저장

API 요청 → Authorization: Bearer <token> → 미들웨어 검증
  → request.state.current_user에 UserContext 저장
```

### 3.2 인증 API

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | /api/v1/auth/login | 로그인 (메뉴 목록 포함) | No |
| POST | /api/v1/auth/logout | 로그아웃 | Yes |
| POST | /api/v1/auth/refresh | 토큰 갱신 | No |
| GET | /api/v1/auth/me | 현재 사용자 정보 | Yes |
| PUT | /api/v1/auth/me/password | 비밀번호 변경 | Yes |

### 3.3 비밀번호 정책

- 최소 8자, 영문 대/소문자 + 숫자 필수
- bcrypt 해싱 (cost factor 12)
- 로그인 실패 5회 → 30분 계정 잠금

---

## 4. 메뉴 기반 권한 체크

### 4.1 권한 체크 메커니즘

```python
# app/core/security/permission.py
def require_menu_permission(menu_code: str, action: str):
    """FastAPI Depends로 사용"""
    async def checker(current_user = Depends(get_current_active_user)):
        if current_user.is_superuser:
            return current_user  # 비상 우회
        # tb_user_menu JOIN tb_menu에서 can_{action} 확인
        # 권한 없으면 403 FORBIDDEN
    return checker

# 라우트에서 사용
@router.post("")
async def create_user(
    current_user = Depends(require_menu_permission("USER_MGMT", "create"))
):
```

### 4.2 HTTP 메서드 → CRUD 매핑

| HTTP | action | 필드 |
|------|--------|------|
| POST | create | can_create |
| GET | read | can_read |
| PUT | update | can_update |
| DELETE | delete | can_delete |
| GET /export | export | can_export |

---

## 5. 보안 보호 메커니즘

### 5.1 시스템 리소스 보호

| 대상 | 보호 필드 | 보호 내용 |
|------|----------|----------|
| GLOBAL 테넌트 | `tb_tenant.is_system` | 삭제/비활성화 불가 |
| 기본 역할 (GLOBAL/TENANT/USER) | `tb_role.is_system` | 삭제 불가 |
| 슈퍼유저 | `tb_user.is_superuser` | 타인이 수정/삭제 불가 |

### 5.2 역할 권한 상승 방지

```
tb_role.sort_order 기준: 낮을수록 상위 (GLOBAL=1 > TENANT=2 > USER=3)

규칙: 자신보다 상위 역할은 할당할 수 없다
  - TENANT 관리자 → sort_order >= 자신의 역할만 할당 가능
  - GLOBAL 관리자 → 모든 역할 할당 가능
  - 새 역할 추가 시 sort_order만 설정하면 자동 적용 (하드코딩 없음)
```

**적용 위치**:
- `get_role_options()`: 드롭다운에서 상위 역할 제외
- `create_user()`: 백엔드 검증
- `update_user()`: 백엔드 검증

### 5.3 역할-테넌트 조합 검증

```
규칙: 역할과 테넌트의 논리적 조합만 허용

  GLOBAL 역할  → 시스템 테넌트(is_system=true) 자동 설정, 일반 테넌트 불가
  TENANT 역할  → tenant_id 필수, 시스템 테넌트 불가
  USER 역할    → tenant_id 필수, 시스템 테넌트 불가

금지 조합 예시:
  × GLOBAL + 일반 테넌트 → 시스템 테넌트로 자동 보정
  × TENANT + 시스템 테넌트 → BAD_REQUEST 에러
  × USER + 테넌트 미선택 → BAD_REQUEST 에러
```

**적용 위치**:
- **백엔드**: `_validate_role_tenant()` - create_user, update_user에서 호출
- **프론트엔드**: `handleRoleChange()` - GLOBAL 선택 시 시스템 테넌트 자동 설정 & 비활성화, TENANT/USER 선택 시 시스템 테넌트 제외

### 5.4 메뉴 권한 상승 방지

```
규칙: 자신이 보유하지 않은 메뉴는 할당할 수 없다
  - TENANT 관리자 → 본인의 tb_user_menu에 있는 메뉴만 할당 가능
  - GLOBAL 관리자 → 모든 메뉴 할당 가능
```

**적용 위치**:
- `get_menu_options()`: `assignable` 플래그로 UI에서 비활성화
- `assign_menus()`: 백엔드 검증 (unauthorized_ids 체크)
- `create_user()`: 메뉴 할당 시 동일 검증

### 5.5 사용자 삭제 보호

- 슈퍼유저 삭제 불가
- 자기 자신 삭제 불가
- 테넌트 범위 검증 (`_check_scope_access`)

---

## 6. API 구조

### 6.1 사용자 관리 API (`/api/admin/v1/users`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/options/roles` | 역할 드롭다운 (상위 역할 필터링) | USER_MGMT:read |
| GET | `/options/tenants` | 테넌트 드롭다운 (자기 테넌트만) | USER_MGMT:read |
| GET | `/options/menus` | 메뉴 체크박스 (assignable 플래그) | USER_MGMT:read |
| GET | `` | 사용자 목록 | USER_MGMT:read |
| POST | `` | 사용자 생성 + 메뉴 권한 | USER_MGMT:create |
| GET | `/{user_id}` | 사용자 상세 | USER_MGMT:read |
| PUT | `/{user_id}` | 사용자 수정 | USER_MGMT:update |
| DELETE | `/{user_id}` | 사용자 삭제 | USER_MGMT:delete |
| GET | `/{user_id}/menus` | 메뉴 권한 조회 | USER_MGMT:read |
| PUT | `/{user_id}/menus` | 메뉴 권한 할당 | USER_MGMT:update |

> `/options/*` 엔드포인트: USER_MGMT 권한으로 접근 (MENU_MGMT와 분리)

### 6.2 역할 관리 API (`/api/admin/v1/roles`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `` | 역할 목록 | ROLE_MGMT:read |
| POST | `` | 역할 생성 | ROLE_MGMT:create |
| GET | `/default-menus/{role_code}` | 역할 기본 메뉴 | ROLE_MGMT:read |
| GET | `/{role_id}` | 역할 상세 | ROLE_MGMT:read |
| PUT | `/{role_id}` | 역할 수정 | ROLE_MGMT:update |
| DELETE | `/{role_id}` | 역할 삭제 (is_system 불가) | ROLE_MGMT:delete |

### 6.3 메뉴 관리 API (`/api/admin/v1/menus`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `` | 메뉴 트리 | MENU_MGMT:read |
| POST | `` | 메뉴 추가 | MENU_MGMT:create |
| PUT | `/reorder` | 순서 변경 | MENU_MGMT:update |
| GET | `/{menu_id}` | 메뉴 상세 | MENU_MGMT:read |
| PUT | `/{menu_id}` | 메뉴 수정 | MENU_MGMT:update |
| DELETE | `/{menu_id}` | 메뉴 삭제 | MENU_MGMT:delete |

### 6.4 테넌트 관리 API (`/api/admin/v1/tenants`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `` | 테넌트 목록 | TENANT_MGMT:read |
| POST | `` | 테넌트 생성 | TENANT_MGMT:create |
| GET | `/{tenant_id}` | 테넌트 상세 | TENANT_MGMT:read |
| PUT | `/{tenant_id}` | 테넌트 수정 | TENANT_MGMT:update |
| DELETE | `/{tenant_id}` | 테넌트 삭제 (is_system 불가) | TENANT_MGMT:delete |

---

## 7. 프론트엔드

### 7.1 인증 상태 관리 (Vuex)

```javascript
// store/modules/auth.js
getters: {
  hasMenuPermission: (menuCode, action) => { /* user.menus 배열에서 확인 */ },
  canAccessAdmin: () => { /* menus.length > 0 */ },
  accessibleMenus: () => { /* menu_type=PAGE && can_read 필터 */ },
}
// localStorage: mureum_access_token, mureum_refresh_token, mureum_user
```

### 7.2 사이드바 동적 메뉴

로그인 응답의 `menus[]` 배열로 사이드바를 동적 생성. 하드코딩 없음.

```javascript
const sidebarMenus = user.menus
  .filter(m => m.menu_type === 'PAGE' && m.can_read)
  .sort((a, b) => a.sort_order - b.sort_order)
```

### 7.3 라우터 가드

```javascript
// router/index.js
router.beforeEach → 토큰 없으면 /login
  → canAccessAdmin 체크 → 메뉴 경로 매칭
  → 권한 없으면 403 또는 landing_page로 리디렉트
```

---

## 8. 파일 구조

### 8.1 백엔드

```
app/core/security/
  ├── jwt.py            # JWT 생성/검증
  ├── password.py       # bcrypt 해싱
  ├── dependencies.py   # get_current_user, get_current_active_user
  ├── permission.py     # require_menu_permission, require_superuser
  └── tenant_context.py # 테넌트 컨텍스트

app/api/routes/
  ├── auth.py           # 인증 (login/logout/refresh/me/password)
  ├── users.py          # 사용자 CRUD + options + 메뉴 권한
  ├── roles.py          # 역할 CRUD + default-menus
  ├── menus.py          # 메뉴 트리 CRUD + reorder
  └── tenants.py        # 테넌트 CRUD

app/api/services/
  ├── auth_service.py   # 인증 로직 (로그인, 토큰, 세션)
  ├── user_service.py   # 사용자 CRUD + 권한 상승 방지
  ├── role_service.py   # 역할 CRUD + 기본 메뉴
  ├── menu_service.py   # 메뉴 트리 CRUD
  └── tenant_service.py # 테넌트 CRUD + is_system 보호

app/models/
  ├── auth.py           # LoginRequest, UserContext, TokenResponse
  ├── user.py           # UserCreate/Update/Response, RoleCreate/Update
  ├── menu.py           # MenuCreate/Update, UserMenuPermission/Assign
  ├── tenant.py         # TenantCreate/Update/Response
  └── role.py           # (user.py에 포함)
```

### 8.2 프론트엔드

```
frontend/src/
  ├── api/
  │   ├── auth.js       # 인증 API
  │   ├── users.js      # 사용자 + options API
  │   ├── roles.js      # 역할 API
  │   ├── menus.js      # 메뉴 API
  │   └── tenants.js    # 테넌트 API
  ├── store/modules/
  │   └── auth.js       # 인증 상태 + hasMenuPermission
  └── views/admin/
      ├── UsersView.vue    # 사용자 관리 (메뉴 권한 할당 포함)
      ├── RolesView.vue    # 역할 관리
      ├── MenusView.vue    # 메뉴 트리 관리
      └── TenantsView.vue  # 테넌트 관리
```

---

## 9. 환경 설정

```bash
# .env
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
LOGIN_MAX_FAIL_COUNT=5
LOGIN_LOCK_MINUTES=30
```

---

## 10. 미구현 사항

### 10.1 NL2SQL 권한 필터 (Phase 5)

role_code 기반 SQL WHERE 조건 자동 주입 미구현:

```
GLOBAL → 필터 없음
TENANT → WHERE tenant_id = ?
USER   → WHERE tenant_id = ? AND emp_id = ?
```

**필요 작업**:
- `sql_executor.py`에 `inject_permission_filter()` 구현
- NL2SQL 그래프에 UserContext 전달
- `prompt_build_node`에 scope 정보 포함
- 비즈니스 DB에 tenant_id 컬럼 추가

### 10.2 향후 개선 가능 사항

| 항목 | 설명 | 우선순위 |
|------|------|----------|
| 사용자 soft delete | 물리 삭제 → is_active=false 전환 | 중 |
| tb_api_history FK | user_id FK 추가 (SET NULL) | 낮 |
| ~~역할 계층 DB화~~ | ~~ROLE_HIERARCHY 하드코딩 → sort_order 활용~~ | **구현 완료** |
| 테넌트별 설정 격리 | tb_app_settings에 tenant_id 필터 | 중 |
| 테넌트별 문서 격리 | tb_docs에 tenant_id 필터 | 중 |

---

## 11. SQL DDL 참조

- DB 생성 스크립트: `docs/sql/tb_user_permission.sql`
- 전체 DB 스크립트: `docs/sql/psql-hermes_db.sql`
- 마이그레이션: `docs/sql/migration_role_scope.sql`
