# 사용자 및 메뉴 기반 권한 관리 시스템 설계서

> **문서 버전**: 2.1
> **작성일**: 2026-02-06
> **수정일**: 2026-02-14
> **상태**: ✅ 구현 완료 (Phase 1~4, 6), ⚠️ 부분 구현 (Phase 5)
> **변경 사유**: permission 코드 기반 → 메뉴 기반 권한 관리 체계로 전면 전환
> **현행화 일자**: 2026-02-14 — 실제 구현 코드 기반으로 문서 현행화

---

## 1. 개요

### 1.1 목적

MUREUM 시스템에 사용자 인증 및 **메뉴 기반 권한 관리** 기능을 구현합니다. 기존 permission 코드 방식(`nl2sql:execute`, `admin:users` 등)을 폐기하고, 관리자가 **메뉴 트리를 보면서 직관적으로 CRUD 권한을 설정**할 수 있는 체계로 전환합니다.

### 1.2 핵심 요구사항

| 요구사항 | 설명 |
|----------|------|
| 로그인/인증 | JWT 기반 토큰 인증 |
| 메뉴 기반 권한 | 메뉴 트리 + 사용자별 CRUD 권한 |
| 역할 (1:N) | 사용자는 정확히 하나의 역할에 소속 |
| NL2SQL 데이터 필터 | scope_type 기반 SQL 조건 자동 주입 |

### 1.3 v1.0 → v2.0 변경 요약

| 구분 | v1.0 (permission 기반) | v2.0 (메뉴 기반) |
|------|:---:|:---:|
| 권한 단위 | `permission_code` (코드) | **`tb_menu` (메뉴)** |
| 사용자-역할 | M:N (`tb_user_role`) | **1:N** (`tb_user.role_id` FK) |
| 권한 매핑 | `tb_role_permission` | **`tb_user_menu`** (사용자별 직접) |
| 데이터 필터 | `tb_data_filter` 테이블 | **`tb_role.scope_type`** → 코드에서 유도 |
| 관리 UI | permission 코드 체크박스 | **메뉴 트리 + CRUD 체크박스** |
| 제거 테이블 | - | `tb_permission`, `tb_role_permission`, `tb_user_role`, `tb_data_filter` |

### 1.4 설계 원칙

```
┌─────────────────────────────────────────────────────────────────────┐
│  tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가"  (기능 접근)      │
│  tb_role.scope_type = "어디까지 볼 수 있는가"      (데이터 범위)     │
│                                                                     │
│  같은 메뉴 권한이라도 scope_type에 따라 보이는 데이터가 다름         │
│  예: 사용자 관리 메뉴 Read 권한 + TENANT → 자기 테넌트 사용자만     │
│      사용자 관리 메뉴 Read 권한 + GLOBAL → 전체 사용자              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.5 권한 계층 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        권한 계층 구조                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [시스템 관리자]         모든 메뉴 접근, 전체 CRUD, 전체 데이터             │
│        │                scope_type: GLOBAL | 메뉴: 전체                     │
│        │                landing_page: /admin/dashboard                      │
│        ▼                                                                    │
│  [테넌트 관리자]         제한된 메뉴, 테넌트 내 데이터                      │
│        │                scope_type: TENANT | 메뉴: 일부                     │
│        │                landing_page: /admin/dashboard                      │
│        │                NL2SQL 조건: WHERE tenant_id = ?                    │
│        ▼                                                                    │
│  [일반 사용자]           채팅 메뉴만, 본인 데이터                           │
│                         scope_type: USER | 메뉴: 채팅만                     │
│                         landing_page: /chat                                 │
│                         NL2SQL 조건: WHERE tenant_id = ? AND emp_id = ?    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.6 역할별 메뉴/데이터 범위 비교

| 구분 | 시스템 관리자 | 테넌트 관리자 | 일반 사용자 |
|------|:---:|:---:|:---:|
| `role_code` | SYSTEM_ADMIN | TENANT_ADMIN | USER |
| `scope_type` | GLOBAL | TENANT | USER |
| `landing_page` | /admin/dashboard | /admin/dashboard | /chat |
| `is_superuser` | true | false | false |
| `tenant_id` | NULL | 소속 테넌트 | 소속 테넌트 |
| **메뉴 접근** | 전체 (10개+) | 일부 (6개) | 채팅만 (1개) |
| **CRUD 범위** | 전체 CRUDE | 제한적 CRU | Read만 |
| **NL2SQL 필터** | 없음 (전체) | `tenant_id = ?` | `tenant_id = ? AND emp_id = ?` |

---

## 2. 데이터베이스 설계

### 2.1 ERD (Entity Relationship Diagram)

```
                    ┌──────────────────────┐
                    │     tb_tenant        │
                    ├──────────────────────┤
                    │ tenant_id (PK)       │
                    │ tenant_code (UK)     │
                    │ tenant_name          │
                    │ is_active            │
                    │ metadata (JSONB)     │
                    └──────────┬───────────┘
                               │ 1
                               │
                               │ N
┌───────────────┐  N ┌─────────┴────────────┐ N    1 ┌────────────────────────┐
│   tb_menu     │◄───│      tb_user         │───────►│      tb_role           │
├───────────────┤    ├──────────────────────┤        ├────────────────────────┤
│ menu_id (PK)  │    │ user_id (PK)         │        │ role_id (PK)           │
│ parent_menu_id│    │ login_id (UK)        │        │ role_code (UK)         │
│   (FK,self)   │    │ email (UK)           │        │ role_name              │
│ menu_code(UK) │    │ password_hash        │        │ scope_type             │
│ menu_name     │    │ display_name         │        │ landing_page           │
│ menu_type     │    │ tenant_id (FK)       │        │ is_system              │
│ menu_path     │    │ role_id (FK,NOT NULL) │       │ description            │
│ api_pattern   │    │ is_superuser         │        │ sort_order             │
│ icon          │    │ is_active            │        └────────────────────────┘
│ sort_order    │    │ last_login_at        │
│ depth         │    │ login_fail_count     │
│ is_active     │    │ locked_until         │
│ description   │    └──────────┬───────────┘
└───────┬───────┘               │ 1
        │ 1                     │
        │                       │ N
        │ N  ┌──────────────────┴──────┐
        └───►│    tb_user_menu         │
             │  ★ 유일한 권한 체크 테이블 │
             ├─────────────────────────┤     ┌───────────────────────┐
             │ user_id (PK, FK)        │     │   tb_user_session     │
             │ menu_id (PK, FK)        │     ├───────────────────────┤
             │ can_create              │     │ session_id (PK, UUID) │
             │ can_read                │     │ user_id (FK)          │
             │ can_update              │     │ refresh_token         │
             │ can_delete              │     │ ip_address            │
             │ can_export              │     │ user_agent            │
             │ granted_at              │     │ expires_at            │
             │ granted_by (FK)         │     └───────────────────────┘
             └─────────────────────────┘

※ 화살표 방향: FK가 있는 테이블 → PK가 있는 테이블 (자식 → 부모)
```

### 2.2 테이블 명세

#### 2.2.1 tb_tenant (테넌트)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| tenant_id | BIGSERIAL | PK | 테넌트 고유 ID |
| tenant_code | VARCHAR(50) | UK, NOT NULL | 테넌트 코드 (NL2SQL 조건용) |
| tenant_name | VARCHAR(200) | NOT NULL | 테넌트명 |
| is_active | BOOLEAN | DEFAULT true | 활성화 여부 |
| metadata | JSONB | NULL | 추가 정보 (업종, 계약정보 등) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 수정일시 |

#### 2.2.2 tb_role (역할)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| role_id | BIGSERIAL | PK | 역할 고유 ID |
| role_code | VARCHAR(50) | UK, NOT NULL | 역할 코드 |
| role_name | VARCHAR(100) | NOT NULL | 역할명 |
| description | TEXT | NULL | 설명 |
| scope_type | VARCHAR(20) | NOT NULL | 데이터 범위 (GLOBAL, TENANT, USER) |
| landing_page | VARCHAR(200) | NOT NULL | 로그인 후 랜딩 페이지 |
| is_system | BOOLEAN | DEFAULT false | 시스템 기본 역할 (삭제 불가) |
| sort_order | INT | DEFAULT 0 | 정렬 순서 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 수정일시 |

> **scope_type 역할**: NL2SQL 실행 시 데이터 필터 범위를 결정합니다.
> 서비스 레이어에서 `scope_type`을 읽어 WHERE 조건을 코드로 주입합니다.
> - GLOBAL → 필터 없음
> - TENANT → `WHERE tenant_id = ?`
> - USER → `WHERE tenant_id = ? AND emp_id = ?`

**기본 역할**:

| role_code | role_name | scope_type | landing_page |
|-----------|-----------|------------|--------------|
| SYSTEM_ADMIN | 시스템 관리자 | GLOBAL | /admin/dashboard |
| TENANT_ADMIN | 테넌트 관리자 | TENANT | /admin/dashboard |
| USER | 일반 사용자 | USER | /chat |

#### 2.2.3 tb_user (사용자)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| user_id | BIGSERIAL | PK | 사용자 고유 ID |
| login_id | VARCHAR(100) | UK, NOT NULL | 로그인 ID |
| email | VARCHAR(255) | UK, NOT NULL | 이메일 |
| password_hash | VARCHAR(255) | NOT NULL | 비밀번호 해시 (bcrypt) |
| display_name | VARCHAR(100) | NULL | 표시 이름 |
| tenant_id | BIGINT | FK, NULL | 소속 테넌트 ID (시스템 관리자는 NULL) |
| role_id | BIGINT | FK, NOT NULL | 역할 ID (**사용자는 하나의 역할에 소속**) |
| is_active | BOOLEAN | DEFAULT true | 활성화 여부 |
| is_superuser | BOOLEAN | DEFAULT false | 시스템 관리자 비상 안전장치 |
| last_login_at | TIMESTAMPTZ | NULL | 마지막 로그인 일시 |
| login_fail_count | INT | DEFAULT 0 | 로그인 실패 횟수 |
| locked_until | TIMESTAMPTZ | NULL | 계정 잠금 해제 시간 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 수정일시 |

> **v2.0 변경**: `tb_user_role` M:N 테이블 삭제, `role_id` FK를 직접 보유 (1:N).
> 사용자는 정확히 하나의 역할에 소속됩니다.

> **`is_superuser` 설계 의도**:
> - RBAC 비상 복구 안전장치 (Django, PostgreSQL과 동일 패턴)
> - 정상 흐름은 `tb_user_menu`만 사용. `is_superuser` 직접 체크하지 않음
> - 비상 시나리오: 역할/메뉴 설정이 꼬였을 때 `is_superuser=true`인 사용자는 접근 유지
> - 운영 규칙: 최소 1명에게만 부여

#### 2.2.4 tb_menu (메뉴)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| menu_id | BIGSERIAL | PK | 메뉴 고유 ID |
| parent_menu_id | BIGINT | FK(self), NULL | 상위 메뉴 ID (NULL = 루트) |
| menu_code | VARCHAR(50) | UK, NOT NULL | 메뉴 코드 |
| menu_name | VARCHAR(100) | NOT NULL | 메뉴 표시명 |
| menu_type | VARCHAR(20) | NOT NULL | `DIRECTORY` / `PAGE` / `API` |
| menu_path | VARCHAR(200) | NULL | 프론트엔드 URL 경로 |
| api_pattern | VARCHAR(200) | NULL | 연결 API 경로 패턴 |
| icon | VARCHAR(50) | NULL | 아이콘 클래스 |
| sort_order | INT | DEFAULT 0 | 정렬 순서 |
| depth | INT | DEFAULT 0 | 트리 깊이 (0=루트) |
| is_active | BOOLEAN | DEFAULT true | 활성 여부 |
| description | TEXT | NULL | 설명 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 수정일시 |

> **menu_type 설명**:
> - `DIRECTORY`: 하위 메뉴를 가진 폴더 (클릭 불가, 트리 구조용)
> - `PAGE`: 실제 화면 페이지 (프론트엔드 라우트)
> - `API`: API 접근 제어용 (화면 없이 API 패턴만)

**기본 메뉴 트리**:

```
ROOT
├── [DIR] ADMIN (관리자)                          depth=0
│   ├── [PAGE] DASHBOARD        /admin/dashboard   depth=1  대시보드
│   ├── [PAGE] CHAT             /admin/chat         depth=1  자연어 검색
│   ├── [PAGE] DOCUMENTS        /admin/documents    depth=1  문서 관리
│   ├── [PAGE] USER_MGMT        /admin/users        depth=1  사용자 관리
│   ├── [PAGE] MENU_MGMT        /admin/menus        depth=1  메뉴/권한 관리
│   ├── [PAGE] ROLE_MGMT        /admin/roles        depth=1  역할 관리
│   ├── [PAGE] TENANT_MGMT      /admin/tenants      depth=1  테넌트 관리
│   ├── [PAGE] SETTINGS         /admin/settings     depth=1  시스템 설정
│   ├── [PAGE] CODES            /admin/codes        depth=1  코드 관리
│   └── [PAGE] HISTORY          /admin/history      depth=1  검색 이력
├── [DIR] USER_AREA (사용자)                       depth=0
│   └── [PAGE] USER_CHAT        /chat               depth=1  채팅
└── [DIR] API_ACCESS (API 접근)                    depth=0
    ├── [API] AGENT_API         /api/v1/agent       depth=1  Agent API
    ├── [API] RAG_API           /api/v1/rag         depth=1  RAG API
    └── [API] NL2SQL_API        /api/v1/nl2sql      depth=1  NL2SQL API
```

#### 2.2.5 tb_user_menu (사용자-메뉴 권한)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| user_id | BIGINT | PK, FK | 사용자 ID |
| menu_id | BIGINT | PK, FK | 메뉴 ID |
| can_create | BOOLEAN | DEFAULT false | 등록 권한 |
| can_read | BOOLEAN | DEFAULT true | 조회 권한 |
| can_update | BOOLEAN | DEFAULT false | 수정 권한 |
| can_delete | BOOLEAN | DEFAULT false | 삭제 권한 |
| can_export | BOOLEAN | DEFAULT false | 내보내기 권한 |
| granted_at | TIMESTAMPTZ | DEFAULT NOW() | 부여일시 |
| granted_by | BIGINT | FK, NULL | 부여자 ID |

> **핵심**: 이 테이블이 **유일한 런타임 권한 체크 테이블**입니다.
> 프론트엔드 메뉴 렌더링과 백엔드 API 권한 체크 모두 이 테이블만 조회합니다.

**역할별 기본 메뉴 할당 (사용자 생성 시 복사)**:

| 메뉴 | SYSTEM_ADMIN | TENANT_ADMIN | USER |
|------|:---:|:---:|:---:|
| 대시보드 | CRUDE | R | - |
| 자연어 검색 | CR | CR | - |
| 문서 관리 | CRUDE | CRUDE | - |
| 사용자 관리 | CRUDE | CRU | - |
| 메뉴/권한 관리 | CRUDE | - | - |
| 역할 관리 | CRUDE | - | - |
| 테넌트 관리 | CRUDE | - | - |
| 시스템 설정 | RU | - | - |
| 코드 관리 | CRUD | - | - |
| 검색 이력 | RE | RE | - |
| 채팅 | CR | CR | CR |
| Agent API | CR | CR | CR |
| RAG API | CR | CR | CR |
| NL2SQL API | CR | CR | CR |

> C=Create, R=Read, U=Update, D=Delete, E=Export

#### 2.2.6 tb_user_session (사용자 세션)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| session_id | UUID | PK | 세션 ID |
| user_id | BIGINT | FK | 사용자 ID |
| refresh_token | VARCHAR(500) | NULL | 리프레시 토큰 |
| ip_address | VARCHAR(50) | NULL | 접속 IP |
| user_agent | TEXT | NULL | 브라우저 정보 |
| expires_at | TIMESTAMPTZ | NOT NULL | 만료일시 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

### 2.3 제거된 테이블 (v1.0 대비)

| 제거 테이블 | 대체 방안 |
|-------------|----------|
| `tb_permission` | `tb_menu`로 대체 (메뉴 자체가 권한 단위) |
| `tb_role_permission` | `tb_user_menu`로 대체 (사용자별 직접 권한) |
| `tb_user_role` | `tb_user.role_id` FK로 대체 (1:N) |
| `tb_data_filter` | `tb_role.scope_type` + 서비스 레이어 코드로 대체 |

---

## 3. 인증 시스템

### 3.1 인증 흐름 (JWT 기반)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        인증 흐름                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 로그인 요청                                                       │
│     POST /api/v1/auth/login                                          │
│     { "login_id": "user@company.com", "password": "..." }            │
│                         │                                            │
│                         ▼                                            │
│  2. 비밀번호 검증 (bcrypt)                                            │
│     → 역할/메뉴 권한 로드                                             │
│                         │                                            │
│                         ▼                                            │
│  3. JWT 토큰 발급                                                     │
│     {                                                                │
│       "access_token": "eyJ...",   // 유효기간: 30분                  │
│       "refresh_token": "eyJ...",  // 유효기간: 7일                   │
│       "token_type": "Bearer",                                        │
│       "expires_in": 1800,                                            │
│       "user": {                                                      │
│         "user_id": 1,                                                │
│         "login_id": "user@company.com",                              │
│         "tenant_id": 5,                                             │
│         "role_code": "TENANT_ADMIN",                                │
│         "scope_type": "TENANT",                                     │
│         "landing_page": "/admin/dashboard",                         │
│         "menus": [                                                   │
│           {"menu_code":"DASHBOARD","menu_name":"대시보드",            │
│            "menu_path":"/admin/dashboard","icon":"dashboard",        │
│            "can_create":false,"can_read":true,...},                  │
│           ...                                                        │
│         ]                                                            │
│       }                                                              │
│     }                                                                │
│                         │                                            │
│                         ▼                                            │
│  4. API 요청 시 헤더 포함                                             │
│     Authorization: Bearer <access_token>                             │
│                         │                                            │
│                         ▼                                            │
│  5. 인증 미들웨어에서 토큰 검증                                       │
│     → request.state.current_user에 사용자 정보 저장                   │
│     → 메뉴 권한 부족 시 403 Forbidden 반환                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 JWT 토큰 구조

**Access Token Payload**:
```json
{
  "sub": "user_id",
  "login_id": "user@company.com",
  "tenant_id": 5,
  "role_code": "TENANT_ADMIN",
  "scope_type": "TENANT",
  "is_superuser": false,
  "exp": 1707264000,
  "iat": 1707263100
}
```

> **v2.0 변경**: `permissions` 배열 대신 `role_code`와 `scope_type`만 포함.
> 메뉴 권한은 JWT에 포함하지 않고, 필요시 DB 조회 또는 로그인 응답의 `menus` 배열 사용.

**Refresh Token Payload**:
```json
{
  "sub": "user_id",
  "session_id": "uuid",
  "exp": 1707868800,
  "iat": 1707263100
}
```

### 3.3 토큰 갱신 프로세스

```
┌─────────────────────────────────────────────────────────────┐
│  Access Token 만료 시                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 클라이언트: 401 Unauthorized 수신                        │
│                         │                                   │
│                         ▼                                   │
│  2. POST /api/v1/auth/refresh                               │
│     { "refresh_token": "eyJ..." }                           │
│                         │                                   │
│                         ▼                                   │
│  3. 서버: Refresh Token 검증                                 │
│     → tb_user_session 확인                                  │
│     → 새로운 Access Token 발급                              │
│                         │                                   │
│                         ▼                                   │
│  4. 응답                                                    │
│     { "access_token": "새로운 토큰", "expires_in": 1800 }   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 메뉴 기반 권한 체크

### 4.1 권한 체크 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                    메뉴 기반 권한 체크 흐름                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. API 요청: POST /api/admin/v1/users                             │
│                         │                                           │
│                         ▼                                           │
│  2. JWT에서 user_id 추출                                             │
│                         │                                           │
│                         ▼                                           │
│  3. tb_user_menu에서 해당 메뉴 권한 조회                              │
│     SELECT can_create, can_read, can_update, can_delete, can_export │
│     FROM tb_user_menu um                                            │
│     JOIN tb_menu m ON m.menu_id = um.menu_id                        │
│     WHERE um.user_id = ? AND m.menu_code = 'USER_MGMT'             │
│                         │                                           │
│                         ▼                                           │
│  4. HTTP 메서드 → CRUD 매핑                                          │
│     POST   → can_create 확인                                        │
│     GET    → can_read 확인                                          │
│     PUT    → can_update 확인                                        │
│     DELETE → can_delete 확인                                        │
│                         │                                           │
│                         ▼                                           │
│  5. 권한 있음 → scope_type으로 데이터 범위 필터                       │
│     권한 없음 → 403 Forbidden                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 구현 예시

```python
# 권한 검사 의존성 (FastAPI Depends)
def require_menu_permission(menu_code: str, action: str):
    """
    menu_code: 메뉴 코드 (예: 'USER_MGMT')
    action: 'create' | 'read' | 'update' | 'delete' | 'export'
    """
    async def checker(current_user: UserContext = Depends(get_current_user)):
        if current_user.is_superuser:
            return current_user

        query = """
            SELECT can_create, can_read, can_update, can_delete, can_export
            FROM tb_user_menu um
            JOIN tb_menu m ON m.menu_id = um.menu_id
            WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true
        """
        row = db.fetch_one(query, [current_user.user_id, menu_code])
        if not row or not row[f"can_{action}"]:
            raise HTTPException(status_code=403, detail="권한 없음")
        return current_user
    return checker

# 라우트에서 사용
@router.get("/")
async def list_users(
    current_user = Depends(require_menu_permission("USER_MGMT", "read"))
):
    ...
```

---

## 5. NL2SQL 권한 조건 주입

> ⚠️ **현행 상태 (2026-02-14)**: 이 섹션은 **설계 사양**입니다. `inject_permission_filter` 메서드는 아직 구현되지 않았습니다.
> 현재 SQL 실행 시 기본 보안(위험 키워드 차단, SELECT 전용, 타임아웃)만 적용됩니다.
> scope_type 기반 WHERE 자동 주입은 Phase 5 구현 시 추가 예정입니다.

### 5.1 scope_type 기반 필터 (코드 레벨) — 설계 사양

> **v2.0 변경**: `tb_data_filter` 테이블 삭제.
> `scope_type`만으로 서비스 레이어에서 WHERE 조건을 유도합니다.

```python
# app/core/database/sql_executor.py
def inject_permission_filter(self, sql: str, user_context: UserContext) -> str:
    """scope_type 기반 SQL WHERE 조건 자동 주입"""

    if user_context.scope_type == "GLOBAL":
        return sql  # 전체 데이터

    if user_context.scope_type == "TENANT":
        # 테넌트 필터
        return self._add_where(sql, f"tenant_id = {user_context.tenant_id}")

    if user_context.scope_type == "USER":
        # 테넌트 + 사용자 필터
        return self._add_where(sql,
            f"tenant_id = {user_context.tenant_id} AND emp_id = {user_context.user_id}")

    return sql
```

### 5.2 필터 적용 예시

```
원본 질문: "2024년 입사자 목록 보여줘"

LLM 생성 SQL:
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01'

[시스템 관리자 (GLOBAL)] → 변경 없음
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01'

[테넌트 관리자 (TENANT, tenant_id=5)] → tenant_id 조건 추가
  SELECT emp_name, hire_date FROM employee
  WHERE hire_date >= '2024-01-01' AND tenant_id = 5

[일반 사용자 (USER, tenant_id=5, user_id=123)] → tenant_id + emp_id 조건 추가
  SELECT emp_name, hire_date FROM employee
  WHERE hire_date >= '2024-01-01' AND tenant_id = 5 AND emp_id = 123
```

### 5.3 서비스 레이어 scope_type 제한

| 서비스 | GLOBAL | TENANT | USER |
|--------|--------|--------|------|
| user_service | 전체 사용자 | 테넌트 사용자 | 본인만 |
| document_service | 전체 문서 | 테넌트 문서 | (해당 없음) |
| history_service | 전체 이력 | 테넌트 이력 | 본인 이력 |
| NL2SQL (sql_executor) | 필터 없음 | `tenant_id = ?` | `tenant_id = ? AND emp_id = ?` |

---

## 6. 사용자 생성 워크플로우

### 6.1 관리자 UI에서 사용자 생성

```
┌───────────────────────────────────────────────────────────┐
│  사용자 생성 화면                                           │
│                                                           │
│  ① 기본 정보 입력                                          │
│     - 로그인 ID, 이메일, 이름, 비밀번호                     │
│                                                           │
│  ② 테넌트 선택                                             │
│                                                           │
│  ③ 역할 선택 (SYSTEM_ADMIN / TENANT_ADMIN / USER)          │
│     → 선택 시 해당 역할의 기본 메뉴가 자동 체크됨            │
│                                                           │
│  ④ 메뉴 권한 설정 (체크박스 테이블)                          │
│  ┌─────────────────────────────────────────────┐          │
│  │ 메뉴              │  C  │  R  │  U  │  D  │ E │        │
│  ├───────────────────┼─────┼─────┼─────┼─────┼───┤        │
│  │ ☑ 대시보드        │  □  │  ☑  │  □  │  □  │ □ │        │
│  │ ☑ 자연어 검색     │  ☑  │  ☑  │  □  │  □  │ □ │        │
│  │ ☑ 문서 관리       │  ☑  │  ☑  │  ☑  │  ☑  │ ☑ │        │
│  │ ☑ 사용자 관리     │  ☑  │  ☑  │  ☑  │  □  │ □ │        │
│  │ □ 메뉴/권한 관리  │  □  │  □  │  □  │  □  │ □ │        │
│  │ □ 역할 관리       │  □  │  □  │  □  │  □  │ □ │        │
│  │ □ 테넌트 관리     │  □  │  □  │  □  │  □  │ □ │        │
│  │ □ 시스템 설정     │  □  │  □  │  □  │  □  │ □ │        │
│  │ ☑ 검색 이력       │  □  │  ☑  │  □  │  □  │ ☑ │        │
│  │ ☑ 채팅            │  ☑  │  ☑  │  □  │  □  │ □ │        │
│  └─────────────────────────────────────────────┘          │
│     ※ 역할 선택 시 기본값 자동 체크, 관리자가 개별 조정 가능  │
│                                                           │
│                    [저장]                                   │
└───────────────────────────────────────────────────────────┘
```

### 6.2 서비스 로직

```python
class UserService:
    def create_user(self, user_data, role_id, menu_permissions):
        """
        user_data: 사용자 기본 정보
        role_id: 역할 ID
        menu_permissions: [{"menu_id": 1, "can_create": false, "can_read": true, ...}, ...]
        """
        # 1. tb_user INSERT
        user = self._insert_user(user_data, role_id)

        # 2. tb_user_menu INSERT (관리자가 설정한 메뉴 권한)
        for perm in menu_permissions:
            self._insert_user_menu(
                user_id=user.user_id,
                menu_id=perm["menu_id"],
                can_create=perm.get("can_create", False),
                can_read=perm.get("can_read", True),
                can_update=perm.get("can_update", False),
                can_delete=perm.get("can_delete", False),
                can_export=perm.get("can_export", False),
                granted_by=current_user.user_id,
            )

        return user
```

### 6.3 역할 변경 시

```
사용자의 역할을 TENANT_ADMIN → SYSTEM_ADMIN으로 변경:
  ① tb_user.role_id 업데이트
  ② 관리자가 메뉴 권한 재설정 (UI에서 SYSTEM_ADMIN 기본값 자동 체크)
  ③ tb_user_menu DELETE → 새 메뉴 권한 INSERT
```

---

## 7. 프론트엔드 메뉴 렌더링

### 7.1 로그인 응답으로 메뉴 목록 수신

```javascript
// 로그인 성공 응답
{
  user: {
    user_id: 5,
    login_id: "tenant_admin@demo.com",
    role_code: "TENANT_ADMIN",
    scope_type: "TENANT",
    landing_page: "/admin/dashboard",
    menus: [
      {
        menu_code: "DASHBOARD",
        menu_name: "대시보드",
        menu_path: "/admin/dashboard",
        menu_type: "PAGE",
        icon: "dashboard",
        parent_menu_code: "ADMIN",
        depth: 1,
        sort_order: 1,
        can_create: false,
        can_read: true,
        can_update: false,
        can_delete: false,
        can_export: false
      },
      ...
    ]
  }
}
```

### 7.2 사이드바 동적 생성

```javascript
// AppSidebar.vue — 메뉴 목록을 DB에서 받아 동적 생성
const sidebarMenus = computed(() => {
  const menus = authStore.user?.menus || []
  return menus
    .filter(m => m.menu_type === 'PAGE' && m.can_read)
    .sort((a, b) => a.sort_order - b.sort_order)
    .map(m => ({
      path: m.menu_path,
      title: m.menu_name,
      icon: m.icon,
      permissions: {
        canCreate: m.can_create,
        canRead: m.can_read,
        canUpdate: m.can_update,
        canDelete: m.can_delete,
        canExport: m.can_export,
      }
    }))
})
```

> **핵심**: 프론트엔드 코드에 메뉴 목록을 하드코딩하지 않음.
> DB에서 메뉴를 추가/삭제하면 프론트엔드 코드 변경 없이 메뉴가 자동으로 나타남/사라짐.

---

## 8. API 설계

### 8.1 인증 API (`/api/v1/auth`)

| Method | Endpoint | Description | 인증 필요 |
|--------|----------|-------------|-----------|
| POST | `/login` | 로그인 (JWT 발급 + 메뉴 목록) | No |
| POST | `/logout` | 로그아웃 (토큰 무효화) | Yes |
| POST | `/refresh` | Access Token 갱신 | No (Refresh Token) |
| GET | `/me` | 현재 사용자 정보 + 메뉴 목록 | Yes |
| PUT | `/me/password` | 비밀번호 변경 | Yes |

### 8.2 사용자 관리 API (`/api/admin/v1/users`)

| Method | Endpoint | Description | 필요 메뉴 권한 |
|--------|----------|-------------|---------------|
| GET | `/` | 사용자 목록 | USER_MGMT:read |
| POST | `/` | 사용자 생성 (+ 메뉴 권한) | USER_MGMT:create |
| GET | `/{user_id}` | 사용자 상세 | USER_MGMT:read |
| PUT | `/{user_id}` | 사용자 수정 | USER_MGMT:update |
| DELETE | `/{user_id}` | 사용자 삭제 | USER_MGMT:delete |
| GET | `/{user_id}/menus` | 사용자 메뉴 권한 조회 | USER_MGMT:read |
| PUT | `/{user_id}/menus` | 사용자 메뉴 권한 수정 | USER_MGMT:update |

### 8.3 역할 관리 API (`/api/admin/v1/roles`)

| Method | Endpoint | Description | 필요 메뉴 권한 |
|--------|----------|-------------|---------------|
| GET | `/` | 역할 목록 | ROLE_MGMT:read |
| POST | `/` | 역할 생성 | ROLE_MGMT:create |
| GET | `/{role_id}` | 역할 상세 | ROLE_MGMT:read |
| PUT | `/{role_id}` | 역할 수정 | ROLE_MGMT:update |
| DELETE | `/{role_id}` | 역할 삭제 (시스템 역할 불가) | ROLE_MGMT:delete |

### 8.4 메뉴 관리 API (`/api/admin/v1/menus`)

| Method | Endpoint | Description | 필요 메뉴 권한 |
|--------|----------|-------------|---------------|
| GET | `/` | 메뉴 트리 조회 | MENU_MGMT:read |
| POST | `/` | 메뉴 추가 | MENU_MGMT:create |
| PUT | `/{menu_id}` | 메뉴 수정 | MENU_MGMT:update |
| DELETE | `/{menu_id}` | 메뉴 삭제 | MENU_MGMT:delete |

### 8.5 테넌트 관리 API (`/api/admin/v1/tenants`)

| Method | Endpoint | Description | 필요 메뉴 권한 |
|--------|----------|-------------|---------------|
| GET | `/` | 테넌트 목록 | TENANT_MGMT:read |
| POST | `/` | 테넌트 생성 | TENANT_MGMT:create |
| GET | `/{tenant_id}` | 테넌트 상세 | TENANT_MGMT:read |
| PUT | `/{tenant_id}` | 테넌트 수정 | TENANT_MGMT:update |
| DELETE | `/{tenant_id}` | 테넌트 삭제 | TENANT_MGMT:delete |

---

## 9. 파일 구조

### 9.1 파일 목록

```
app/
├── api/
│   ├── routes/
│   │   ├── auth.py                  # 인증 API (로그인/로그아웃/토큰갱신)
│   │   ├── users.py                 # 사용자 관리 API
│   │   ├── roles.py                 # 역할 관리 API
│   │   ├── menus.py                 # 메뉴 관리 API (★ 신규)
│   │   └── tenants.py               # 테넌트 관리 API
│   └── services/
│       ├── auth_service.py          # 인증 비즈니스 로직
│       ├── user_service.py          # 사용자 CRUD + 메뉴 권한 할당
│       ├── role_service.py          # 역할 관리
│       ├── menu_service.py          # 메뉴 관리 (★ 신규)
│       └── tenant_service.py        # 테넌트 관리
├── core/
│   └── security/
│       ├── __init__.py
│       ├── jwt.py                   # JWT 생성/검증 유틸
│       ├── password.py              # 비밀번호 해싱 (bcrypt)
│       ├── permission.py            # 메뉴 권한 검사 (require_menu_permission)
│       └── dependencies.py          # FastAPI 의존성 (get_current_user 등)
├── middleware/
│   └── auth.py                      # 인증 미들웨어
├── models/
│   ├── user.py                      # User, Role Pydantic 모델
│   ├── auth.py                      # LoginRequest, TokenResponse 등
│   ├── menu.py                      # Menu, UserMenu Pydantic 모델 (★ 신규)
│   └── tenant.py                    # Tenant Pydantic 모델
└── config.py                        # JWT 설정 추가

docs/
└── sql/
    └── tb_user_permission.sql       # DDL + 초기 데이터

frontend/src/
├── views/
│   ├── LoginView.vue                # 로그인 페이지
│   └── admin/
│       ├── UsersView.vue            # 사용자 관리 (메뉴 권한 할당 포함)
│       ├── MenusView.vue            # 메뉴/권한 관리 (★ 신규)
│       ├── RolesView.vue            # 역할 관리
│       └── TenantsView.vue          # 테넌트 관리
├── store/modules/
│   └── auth.js                      # 인증 상태 관리
└── api/
    ├── auth.js                      # 인증 API 클라이언트
    ├── users.js                     # 사용자 API
    ├── menus.js                     # 메뉴 API (★ 신규)
    └── tenants.js                   # 테넌트 API
```

---

## 10. 구현 계획

### 10.1 Phase 1: 기반 구축 — DB 테이블 + Pydantic 모델 ✅ 구현 완료

> **목적**: 데이터 구조 확립
> **산출물**: DB 테이블 6개 + Pydantic 모델
> **상태**: ✅ 구현 완료
> **구현 파일**: `docs/sql/tb_user_permission.sql`, `app/models/auth.py`, `app/models/user.py`, `app/models/menu.py`, `app/models/tenant.py`

| 작업 | 설명 | 상태 |
|------|------|------|
| DB 테이블 생성 | `tb_user_permission.sql` 실행 | ✅ |
| 초기 데이터 | 역할 3개, 메뉴 14개, 관리자 계정, 관리자 메뉴 권한 | ✅ |
| Pydantic 모델 | auth.py, user.py, menu.py, tenant.py | ✅ |

### 10.2 Phase 2: Core Security 모듈 ✅ 구현 완료

> **목적**: 인증/인가 핵심 유틸리티
> **선행**: Phase 1
> **상태**: ✅ 구현 완료
> **구현 파일**: `app/core/security/jwt.py`, `app/core/security/password.py`, `app/core/security/dependencies.py`, `app/core/security/permission.py`

| 작업 | 설명 | 상태 |
|------|------|------|
| jwt.py | JWT 생성/검증 (TokenPayload에 role_code, scope_type 포함) | ✅ |
| password.py | bcrypt 직접 사용 (cost factor 12) | ✅ |
| dependencies.py | get_current_user, get_optional_user (FastAPI Depends) | ✅ |
| permission.py | require_menu_permission (메뉴 권한 체크, DB 조회) | ✅ |
| config.py 확장 | JWT 설정 필드 추가 | ✅ |

### 10.3 Phase 3: 인증 API + 미들웨어 ✅ 구현 완료

> **목적**: 로그인/로그아웃/토큰갱신
> **선행**: Phase 2
> **상태**: ✅ 구현 완료
> **구현 파일**: `app/api/services/auth_service.py`, `app/api/routes/auth.py`, `app/middleware/auth.py`

| 작업 | 설명 | 상태 |
|------|------|------|
| auth_service.py | 인증 + 재귀 CTE로 메뉴 트리 로드 | ✅ |
| auth.py (route) | 인증 API 5개 (login, logout, refresh, me, password) | ✅ |
| auth.py (middleware) | JWT 검증 미들웨어 (선택적 인증 모드) | ✅ |
| main.py 수정 | 미들웨어 + 라우터 등록 | ✅ |

### 10.4 Phase 4: 관리 API (CRUD) ✅ 구현 완료

> **목적**: 사용자/역할/메뉴/테넌트 관리
> **선행**: Phase 3
> **상태**: ✅ 구현 완료
> **구현 파일**: `app/api/services/user_service.py`, `app/api/services/menu_service.py`, `app/api/services/role_service.py`, `app/api/services/tenant_service.py`, `app/api/routes/users.py`, `app/api/routes/menus.py`, `app/api/routes/roles.py`, `app/api/routes/tenants.py`

| 작업 | 설명 | 상태 |
|------|------|------|
| user_service.py | 사용자 CRUD + tb_user_menu 메뉴 권한 할당 | ✅ |
| menu_service.py | 메뉴 트리 CRUD + 순서 변경 | ✅ |
| role_service.py | 역할 CRUD | ✅ |
| tenant_service.py | 테넌트 CRUD | ✅ |
| 기존 API 권한 적용 | 라우트에 require_menu_permission 적용 | ✅ |

### 10.5 Phase 5: NL2SQL 데이터 필터 ⚠️ 부분 구현

> **목적**: scope_type 기반 NL2SQL 데이터 필터링
> **선행**: Phase 3, 4
> **상태**: ⚠️ 부분 구현 — SQL 인젝션 보호는 존재하나 scope 기반 WHERE 주입 미구현

| 작업 | 설명 | 상태 |
|------|------|------|
| sql_executor 확장 | scope_type 기반 WHERE 주입 (`inject_permission_filter`) | ❌ 미구현 |
| NL2SQL 노드에 UserContext 전달 | NL2SQL 그래프에서 사용자 컨텍스트 활용 | ❌ 미구현 |
| prompt_build_node scope 반영 | LLM 프롬프트에 scope 정보 포함 | ❌ 미구현 |
| SQL 인젝션 보호 | DROP/DELETE 등 위험 키워드 차단, SELECT only | ✅ 기존 구현 |

> **비고**: SQL 실행 시 기본 보안(위험 키워드 차단, SELECT 전용, 타임아웃)은 구현되어 있으나,
> scope_type에 따른 자동 WHERE 조건 주입(`inject_permission_filter`)은 미구현 상태입니다.

### 10.6 Phase 6: 프론트엔드 ✅ 구현 완료

> **목적**: 인증 UI + 메뉴 기반 권한 프론트엔드
> **선행**: Phase 3, 4
> **상태**: ✅ 구현 완료
> **구현 파일**: `frontend/src/store/modules/auth.js`, `frontend/src/views/LoginView.vue`, `frontend/src/components/layout/AppSidebar.vue`, `frontend/src/router/index.js`, `frontend/src/views/admin/UsersView.vue`, `frontend/src/api/auth.js`, `frontend/src/api/users.js`

| 작업 | 설명 | 상태 |
|------|------|------|
| auth.js (store) | Vuex 인증 상태 관리, menus 기반, hasMenuPermission getter | ✅ |
| LoginView.vue | 로그인 화면 + landing_page 리디렉트 | ✅ |
| AppSidebar.vue | 메뉴 목록 동적 생성 (auth/menus 기반) | ✅ |
| router/index.js | 메뉴 기반 라우트 가드 | ✅ |
| UsersView.vue | 사용자 관리 + 메뉴 권한 할당 UI | ✅ |
| auth.js (API) | 인증 API 클라이언트 | ✅ |
| users.js (API) | 사용자 API 클라이언트 | ✅ |

### 10.7 Phase 의존 관계 및 구현 현황

```
Phase 1: DB 테이블 + Pydantic 모델              ✅ 구현 완료
    │
    ▼
Phase 2: Core Security (JWT, Password, Deps)    ✅ 구현 완료
    │
    ▼
Phase 3: Auth API + Auth Middleware              ✅ 구현 완료
    │
    ├───────────────────────┐
    ▼                       ▼
Phase 4:                Phase 5:
관리 API (CRUD)          NL2SQL 필터
✅ 구현 완료              ⚠️ 부분 구현
    │
    ▼
Phase 6:
프론트엔드
✅ 구현 완료
```

---

## 11. 보안 고려사항

### 11.1 비밀번호 정책

- 최소 8자 이상
- 영문 대/소문자, 숫자, 특수문자 조합 권장
- bcrypt 해싱 (cost factor: 12)

### 11.2 토큰 보안

- Access Token: 짧은 유효기간 (30분)
- Refresh Token: DB 저장, 세션 기반 관리
- HTTPS 필수

### 11.3 계정 보호

- 로그인 실패 5회 → 30분 계정 잠금
- is_superuser 보호 (삭제 불가, 본인만 수정)

---

## 12. 환경 설정

### 12.1 `.env` 추가 항목

```bash
# JWT Authentication
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
PASSWORD_MIN_LENGTH=8
LOGIN_MAX_FAIL_COUNT=5
LOGIN_LOCK_MINUTES=30
```

### 12.2 `config.py` 추가 필드

```python
secret_key: str = Field(default="your-secret-key")
algorithm: str = Field(default="HS256")
access_token_expire_minutes: int = Field(default=30)
jwt_refresh_token_expire_days: int = Field(default=7)
password_min_length: int = Field(default=8)
login_max_fail_count: int = Field(default=5)
login_lock_minutes: int = Field(default=30)
```

---

## 13. 참고 자료

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
