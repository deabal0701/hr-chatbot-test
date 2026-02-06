# 사용자 및 권한 관리 시스템 설계서

> **문서 버전**: 1.0
> **작성일**: 2026-02-06
> **상태**: Draft

---

## 1. 개요

### 1.1 목적

MUREUM 시스템에 사용자 인증 및 권한 관리 기능을 추가하여, 사용자 역할에 따른 데이터 접근 제어를 구현합니다. 특히 NL2SQL 실행 시 사용자 권한에 따라 자동으로 데이터 필터 조건이 주입되어 Row-Level Security를 보장합니다.

### 1.2 핵심 요구사항

| 요구사항 | 설명 |
|----------|------|
| 로그인/인증 | JWT 기반 토큰 인증 |
| 역할 기반 접근 제어 (RBAC) | 역할별 권한 관리 |
| 확장 가능한 권한 | 신규 역할/권한 동적 추가 |
| NL2SQL 데이터 필터 | 권한에 따른 SQL 조건 자동 주입 |

### 1.3 권한 계층 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                        권한 계층 구조                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [시스템 관리자]       전체 NL2SQL, 모든 데이터, 시스템 설정         │
│        │              scope_type: GLOBAL                            │
│        ▼                                                            │
│  [테넌트 총괄 관리자]  해당 테넌트 데이터만                          │
│        │              scope_type: TENANT                           │
│        │              SQL 조건: WHERE tenant_id = ?                │
│        ▼                                                            │
│  [일반 사용자]         본인 데이터만                                 │
│                       scope_type: USER                              │
│                       SQL 조건: WHERE user_id = ? AND tenant_id = ?│
│                                                                     │
│  [확장 가능]           신규 역할 추가 가능                           │
│                       예: 부서 관리자, 감사자, 읽기 전용 사용자 등   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 데이터베이스 설계

### 2.1 ERD (Entity Relationship Diagram)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  tb_tenant   │       │   tb_user    │       │   tb_role    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ tenant_id(PK)│◄──┐   │ user_id(PK)  │◄──┐   │ role_id(PK)  │◄──┐
│ tenant_code  │   │   │ username     │   │   │ role_code    │   │
│ tenant_name  │   ├───│ tenant_id(FK)│   │   │ role_name    │   │
│ is_active    │   │   │ password_hash│   │   │ scope_type   │   │
│ metadata     │   │   │ is_superuser │   │   │ is_system    │   │
└──────────────┘   │   └──────────────┘   │   └──────────────┘   │
       ▲           │          ▲           │          ▲           │
       │           │          │           │          │           │
       │           │   ┌──────┴───────────┴───┐      │           │
       │           │   │   tb_user_role       │      │           │
       │           │   ├──────────────────────┤      │           │
       │           │   │ user_id(PK,FK)───────┘      │           │
       │           │   │ role_id(PK,FK)──────────────┘           │
       │           └───│ tenant_id(PK,FK)                        │
       │               │ granted_by(FK)                          │
       │               └──────────────────────┘                  │
       │                                                         │
       │               ┌──────────────────┐                      │
       │               │tb_role_permission│                      │
       │               ├──────────────────┤                      │
       │               │ role_id(PK,FK)───┼──────────────────────┘
       │               │ permission_id(FK)│
       │               └────────┬─────────┘
       │                        │
       │                        ▼
       │               ┌──────────────────┐
       │               │  tb_permission   │
       │               ├──────────────────┤
       │               │ permission_id(PK)│
       │               │ permission_code  │
       │               │ category         │
       │               └──────────────────┘
       │
       │               ┌──────────────────┐
       │               │  tb_data_filter  │
       │               ├──────────────────┤
       └───────────────│ role_id(FK)      │───► tb_role
                       │ target_table     │
                       │ filter_column    │
                       │ filter_type      │
                       └──────────────────┘

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

#### 2.2.2 tb_user (사용자)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| user_id | BIGSERIAL | PK | 사용자 고유 ID |
| username | VARCHAR(100) | UK, NOT NULL | 로그인 ID |
| email | VARCHAR(255) | UK, NOT NULL | 이메일 |
| password_hash | VARCHAR(255) | NOT NULL | 비밀번호 해시 (bcrypt) |
| display_name | VARCHAR(100) | NULL | 표시 이름 |
| tenant_id | BIGINT | FK | 소속 테넌트 ID |
| is_active | BOOLEAN | DEFAULT true | 활성화 여부 |
| is_superuser | BOOLEAN | DEFAULT false | 시스템 관리자 플래그 |
| last_login_at | TIMESTAMPTZ | NULL | 마지막 로그인 일시 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 수정일시 |

**인덱스**:
- `idx_user_tenant` ON (tenant_id)
- `idx_user_active` ON (is_active)

#### 2.2.3 tb_role (역할)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| role_id | BIGSERIAL | PK | 역할 고유 ID |
| role_code | VARCHAR(50) | UK, NOT NULL | 역할 코드 |
| role_name | VARCHAR(100) | NOT NULL | 역할명 |
| description | TEXT | NULL | 설명 |
| scope_type | VARCHAR(20) | NOT NULL | 권한 범위 (GLOBAL, TENANT, USER) |
| is_system | BOOLEAN | DEFAULT false | 시스템 기본 역할 (삭제 불가) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

**기본 역할**:

| role_code | role_name | scope_type | 설명 |
|-----------|-----------|------------|------|
| SYSTEM_ADMIN | 시스템 관리자 | GLOBAL | 전체 시스템 관리 권한 |
| TENANT_ADMIN | 테넌트 총괄 관리자 | TENANT | 해당 테넌트 내 전체 데이터 접근 |
| USER | 일반 사용자 | USER | 본인 데이터만 접근 |

#### 2.2.4 tb_permission (권한)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| permission_id | BIGSERIAL | PK | 권한 고유 ID |
| permission_code | VARCHAR(100) | UK, NOT NULL | 권한 코드 |
| permission_name | VARCHAR(200) | NOT NULL | 권한명 |
| category | VARCHAR(50) | NOT NULL | 카테고리 (nl2sql, rag, admin 등) |
| description | TEXT | NULL | 설명 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

**기본 권한**:

| permission_code | permission_name | category |
|-----------------|-----------------|----------|
| nl2sql:execute | NL2SQL 실행 | nl2sql |
| nl2sql:view_all | NL2SQL 전체 데이터 조회 | nl2sql |
| rag:search | RAG 문서 검색 | rag |
| admin:settings | 시스템 설정 관리 | admin |
| admin:users | 사용자 관리 | admin |
| document:read | 문서 조회 | document |
| document:write | 문서 등록/수정 | document |

#### 2.2.5 tb_role_permission (역할-권한 매핑)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| role_id | BIGINT | PK, FK | 역할 ID |
| permission_id | BIGINT | PK, FK | 권한 ID |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

#### 2.2.6 tb_user_role (사용자-역할 매핑)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| user_id | BIGINT | PK, FK | 사용자 ID |
| role_id | BIGINT | PK, FK | 역할 ID |
| tenant_id | BIGINT | PK, FK | 테넌트 ID (NULL이면 전역 역할) |
| granted_at | TIMESTAMPTZ | DEFAULT NOW() | 부여일시 |
| granted_by | BIGINT | FK | 부여자 ID |

#### 2.2.7 tb_data_filter (데이터 접근 필터)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| filter_id | BIGSERIAL | PK | 필터 고유 ID |
| role_id | BIGINT | FK | 역할 ID |
| target_table | VARCHAR(100) | NOT NULL | 적용 대상 테이블 |
| filter_column | VARCHAR(100) | NOT NULL | 필터 컬럼명 |
| filter_type | VARCHAR(20) | NOT NULL | 필터 유형 (TENANT, USER, CUSTOM) |
| filter_sql | TEXT | NULL | 커스텀 SQL 조건 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

#### 2.2.8 tb_user_session (사용자 세션)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| session_id | UUID | PK | 세션 ID |
| user_id | BIGINT | FK | 사용자 ID |
| refresh_token | VARCHAR(500) | NULL | 리프레시 토큰 |
| ip_address | VARCHAR(50) | NULL | 접속 IP |
| user_agent | TEXT | NULL | 브라우저 정보 |
| expires_at | TIMESTAMPTZ | NOT NULL | 만료일시 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

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
│     { "username": "user@company.com", "password": "..." }            │
│                         │                                            │
│                         ▼                                            │
│  2. 비밀번호 검증 (bcrypt)                                            │
│     → 역할/권한 로드                                                  │
│                         │                                            │
│                         ▼                                            │
│  3. JWT 토큰 발급                                                     │
│     {                                                                │
│       "access_token": "eyJ...",   // 유효기간: 15분                  │
│       "refresh_token": "eyJ...",  // 유효기간: 7일                   │
│       "token_type": "Bearer",                                        │
│       "expires_in": 900,                                             │
│       "user": {                                                      │
│         "user_id": 1,                                                │
│         "username": "user@company.com",                              │
│         "tenant_id": 5,                                             │
│         "roles": ["TENANT_ADMIN"],                                  │
│         "permissions": ["nl2sql:execute", "rag:search"]              │
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
│     → 권한 부족 시 403 Forbidden 반환                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 JWT 토큰 구조

**Access Token Payload**:
```json
{
  "sub": "user_id",
  "username": "user@company.com",
  "tenant_id": 5,
  "scope_type": "TENANT",
  "roles": ["TENANT_ADMIN"],
  "permissions": ["nl2sql:execute", "rag:search"],
  "exp": 1707264000,
  "iat": 1707263100
}
```

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
│     { "access_token": "새로운 토큰", "expires_in": 900 }    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. NL2SQL 권한 조건 주입

### 4.1 개요

NL2SQL 실행 시 사용자 권한(scope_type)에 따라 SQL WHERE 절에 조건이 자동으로 추가됩니다.

### 4.2 권한별 SQL 필터 규칙

| scope_type | 적용 조건 | 예시 |
|------------|----------|------|
| GLOBAL | 없음 (전체 데이터) | `SELECT * FROM employee` |
| TENANT | `tenant_id = ?` | `SELECT * FROM employee WHERE tenant_id = 5` |
| USER | `tenant_id = ? AND user_id = ?` | `SELECT * FROM employee WHERE tenant_id = 5 AND emp_id = 123` |

### 4.3 SQL 필터 주입 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NL2SQL 권한 필터 주입 흐름                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 사용자 질문: "2024년 입사자 목록 보여줘"                          │
│                         │                                           │
│                         ▼                                           │
│  2. LLM이 SQL 생성 (원본)                                            │
│     SELECT emp_name, hire_date FROM employee                        │
│     WHERE hire_date >= '2024-01-01'                                 │
│                         │                                           │
│                         ▼                                           │
│  3. 권한 필터 주입 (sql_executor.inject_permission_filter)          │
│                                                                     │
│     [시스템 관리자] → 변경 없음                                      │
│                                                                     │
│     [테넌트 관리자 (tenant_id=5)]                                   │
│     SELECT emp_name, hire_date FROM employee                        │
│     WHERE hire_date >= '2024-01-01'                                 │
│       AND tenant_id = 5                                            │
│                                                                     │
│     [일반 사용자 (user_id=123, tenant_id=5)]                        │
│     SELECT emp_name, hire_date FROM employee                        │
│     WHERE hire_date >= '2024-01-01'                                 │
│       AND tenant_id = 5 AND emp_id = 123                           │
│                         │                                           │
│                         ▼                                           │
│  4. SQL 실행 및 결과 반환                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 구현 상세

**SQLExecutorService 확장** (`app/core/database/sql_executor.py`):

```python
def inject_permission_filter(
    self,
    sql: str,
    user_context: UserContext
) -> str:
    """
    사용자 권한에 따라 SQL에 조건 자동 주입

    Args:
        sql: 원본 SQL
        user_context: 사용자 컨텍스트 (user_id, tenant_id, scope_type, role_id)

    Returns:
        필터가 적용된 SQL
    """
    # GLOBAL 권한은 필터 없음
    if user_context.scope_type == "GLOBAL":
        return sql

    # tb_data_filter에서 해당 역할의 필터 조건 조회
    filters = self._get_data_filters(user_context.role_id)

    # SQL에서 테이블명 추출
    table_names = self._extract_table_names(sql)

    # 각 테이블에 대해 필터 조건 추가
    for table_name in table_names:
        if table_name in filters:
            filter_config = filters[table_name]
            sql = self._add_where_condition(
                sql=sql,
                table_name=table_name,
                filter_config=filter_config,
                user_context=user_context
            )

    return sql
```

---

## 5. API 설계

### 5.1 인증 API (`/api/v1/auth`)

| Method | Endpoint | Description | 인증 필요 |
|--------|----------|-------------|-----------|
| POST | `/login` | 로그인 (JWT 발급) | No |
| POST | `/logout` | 로그아웃 (토큰 무효화) | Yes |
| POST | `/refresh` | Access Token 갱신 | No (Refresh Token) |
| GET | `/me` | 현재 사용자 정보 | Yes |
| PUT | `/me/password` | 비밀번호 변경 | Yes |

#### 로그인 요청/응답 예시

**Request**:
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin@company.com",
  "password": "password123"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "user_id": 1,
      "username": "admin@company.com",
      "display_name": "관리자",
      "tenant_id": null,
      "roles": ["SYSTEM_ADMIN"],
      "permissions": ["nl2sql:execute", "nl2sql:view_all", "admin:settings", "admin:users"]
    }
  },
  "error": null
}
```

**Response (Failure)**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "아이디 또는 비밀번호가 올바르지 않습니다",
    "detail": null
  }
}
```

### 5.2 사용자 관리 API (`/api/v1/users`)

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 사용자 목록 | admin:users |
| POST | `/` | 사용자 생성 | admin:users |
| GET | `/{user_id}` | 사용자 상세 | admin:users 또는 본인 |
| PUT | `/{user_id}` | 사용자 수정 | admin:users |
| DELETE | `/{user_id}` | 사용자 삭제 | admin:users |
| PUT | `/{user_id}/roles` | 역할 할당 | admin:users |
| GET | `/{user_id}/permissions` | 사용자 권한 조회 | admin:users 또는 본인 |

### 5.3 역할 관리 API (`/api/v1/roles`)

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 역할 목록 | admin:users |
| POST | `/` | 역할 생성 | admin:users |
| GET | `/{role_id}` | 역할 상세 | admin:users |
| PUT | `/{role_id}` | 역할 수정 | admin:users |
| DELETE | `/{role_id}` | 역할 삭제 | admin:users |
| PUT | `/{role_id}/permissions` | 역할에 권한 할당 | admin:users |

### 5.4 권한 관리 API (`/api/v1/permissions`)

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 권한 목록 | admin:users |
| POST | `/` | 권한 생성 | admin:users |

### 5.5 테넌트 관리 API (`/api/v1/tenants`)

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 테넌트 목록 | admin:users |
| POST | `/` | 테넌트 생성 | admin:users |
| GET | `/{tenant_id}` | 테넌트 상세 | admin:users |
| PUT | `/{tenant_id}` | 테넌트 수정 | admin:users |
| DELETE | `/{tenant_id}` | 테넌트 삭제 | admin:users |

---

## 6. 파일 구조

### 6.1 추가될 파일 목록

```
app/
├── api/
│   ├── routes/
│   │   ├── auth.py                  # 인증 API 엔드포인트
│   │   ├── users.py                 # 사용자 관리 API
│   │   ├── roles.py                 # 역할 관리 API
│   │   └── tenants.py               # 테넌트 관리 API
│   └── services/
│       ├── auth_service.py          # 인증 비즈니스 로직
│       ├── user_service.py          # 사용자 CRUD
│       ├── role_service.py          # 역할/권한 관리
│       └── tenant_service.py        # 테넌트 관리
├── core/
│   └── security/
│       ├── __init__.py
│       ├── jwt.py                   # JWT 생성/검증 유틸
│       ├── password.py              # 비밀번호 해싱 (bcrypt)
│       ├── permission.py            # 권한 검사 데코레이터
│       └── dependencies.py          # FastAPI 의존성 (get_current_user 등)
├── middleware/
│   └── auth.py                      # 인증 미들웨어
├── models/
│   ├── user.py                      # User, Role, Permission Pydantic 모델
│   ├── auth.py                      # LoginRequest, TokenResponse 등
│   └── tenant.py                    # Tenant Pydantic 모델
└── config.py                        # JWT 설정 추가 (SECRET_KEY, ALGORITHM 등)

docs/
└── sql/
    └── tb_user_permission.sql       # 사용자/권한 테이블 DDL

frontend/src/
├── views/
│   ├── LoginView.vue                # 로그인 페이지
│   └── admin/
│       ├── UsersView.vue            # 사용자 관리
│       ├── RolesView.vue            # 역할 관리
│       └── TenantsView.vue          # 테넌트 관리
├── store/
│   └── modules/
│       └── auth.js                  # 인증 상태 관리
└── api/
    └── auth.js                      # 인증 API 클라이언트
```

### 6.2 설정 추가 항목 (`app/config.py`)

```python
# JWT 설정
jwt_secret_key: str = Field(default="your-secret-key", description="JWT 시크릿 키")
jwt_algorithm: str = Field(default="HS256", description="JWT 알고리즘")
jwt_access_token_expire_minutes: int = Field(default=15, description="Access Token 만료 시간(분)")
jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh Token 만료 시간(일)")

# 비밀번호 정책
password_min_length: int = Field(default=8, description="최소 비밀번호 길이")
```

---

## 7. 구현 계획

### 7.1 Phase 1: 기반 구축 (1주)

| 작업 | 설명 |
|------|------|
| DB 테이블 생성 | DDL 스크립트 작성 및 실행 |
| 기본 데이터 입력 | 기본 역할, 권한, 관리자 계정 |
| Pydantic 모델 정의 | User, Role, Permission 모델 |

### 7.2 Phase 2: 인증 구현 (1주)

| 작업 | 설명 |
|------|------|
| JWT 모듈 구현 | 토큰 생성/검증 |
| 비밀번호 해싱 | bcrypt 유틸 |
| 로그인/로그아웃 API | /auth/* 엔드포인트 |
| 인증 미들웨어 | 토큰 검증 미들웨어 |

### 7.3 Phase 3: 권한 적용 (1주)

| 작업 | 설명 |
|------|------|
| 권한 검사 데코레이터 | @require_permission |
| NL2SQL 필터 주입 | sql_executor 확장 |
| 기존 API 권한 적용 | 모든 API에 권한 검사 추가 |

### 7.4 Phase 4: 관리 기능 (1주)

| 작업 | 설명 |
|------|------|
| 사용자 관리 API | CRUD |
| 역할/권한 관리 API | CRUD |
| 테넌트 관리 API | CRUD |

### 7.5 Phase 5: 프론트엔드 (1주)

| 작업 | 설명 |
|------|------|
| 로그인 화면 | LoginView.vue |
| 인증 상태 관리 | Vuex auth 모듈 |
| 관리자 화면 | Users, Roles, Companies 뷰 |

---

## 8. 보안 고려사항

### 8.1 비밀번호 정책

- 최소 8자 이상
- 영문 대/소문자, 숫자, 특수문자 조합 권장
- bcrypt 해싱 (cost factor: 12)
- 비밀번호 히스토리 관리 (선택)

### 8.2 토큰 보안

- Access Token: 짧은 유효기간 (15분)
- Refresh Token: DB 저장, 단일 세션 정책 가능
- HTTPS 필수
- HttpOnly 쿠키 옵션 (XSS 방지)

### 8.3 SQL Injection 방지

- 권한 필터 주입 시 파라미터 바인딩 사용
- 기존 SQL 검증 로직 유지

### 8.4 감사 로그

- 로그인/로그아웃 기록
- 권한 변경 이력
- 민감 데이터 접근 로그

---

## 9. 확장 가능성

### 9.1 신규 역할 추가

```sql
-- 예: 부서 관리자 역할 추가
INSERT INTO tb_role (role_code, role_name, scope_type, description)
VALUES ('DEPT_ADMIN', '부서 관리자', 'CUSTOM', '부서 내 데이터만 접근');

-- 권한 매핑
INSERT INTO tb_role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM tb_role r, tb_permission p
WHERE r.role_code = 'DEPT_ADMIN'
AND p.permission_code IN ('nl2sql:execute', 'rag:search');

-- 데이터 필터 설정
INSERT INTO tb_data_filter (role_id, target_table, filter_column, filter_type)
SELECT r.role_id, 'employee', 'department_id', 'CUSTOM'
FROM tb_role r WHERE r.role_code = 'DEPT_ADMIN';
```

### 9.2 OAuth/SSO 연동

- SAML 2.0 지원
- OIDC (OpenID Connect) 지원
- 기업 AD/LDAP 연동

### 9.3 다중 테넌트 지원

- 테넌트별 DB 스키마 분리
- 테넌트별 설정 관리

---

## 10. 참고 자료

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
