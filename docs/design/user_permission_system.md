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

### 1.3 핵심 설계 원칙 — 두 축 분리

```
┌─────────────────────────────────────────────────────────────────────┐
│  permission = "기능 접근 여부"  (무엇을 할 수 있는가)                │
│  scope_type = "데이터 범위"    (어디까지 볼 수 있는가)               │
│                                                                     │
│  같은 permission이라도 scope_type에 따라 보이는 데이터가 다름        │
│  예: admin:users + GLOBAL → 전체 사용자 관리                        │
│      admin:users + TENANT → 자기 테넌트 사용자만 관리               │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 권한 계층 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        권한 계층 구조                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [시스템 관리자]         모든 데이터, 모든 기능, 시스템 설정/테넌트 관리     │
│        │                scope_type: GLOBAL | 권한: 9개 전부                 │
│        │                관리 화면: 전체 메뉴                                │
│        ▼                                                                    │
│  [테넌트 총괄 관리자]    해당 테넌트 데이터 + 테넌트 내 사용자 관리         │
│        │                scope_type: TENANT | 권한: 6개                      │
│        │                관리 화면: 문서, 사용자, 이력 (테넌트 범위)          │
│        │                SQL 조건: WHERE tenant_id = ?                       │
│        ▼                                                                    │
│  [일반 사용자]           본인 데이터만, 관리 기능 없음                       │
│                         scope_type: USER | 권한: 3개                        │
│                         관리 화면: 접근 불가                                │
│                         SQL 조건: WHERE tenant_id = ? AND emp_id = ?        │
│                                                                             │
│  [확장 가능]             코드 변경 없이 DB만으로 신규 역할 추가 가능         │
│                         예: 테넌트 부관리자, 부서 관리자, 감사자 등          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5 역할별 기능/데이터 범위 비교

| 구분 | 시스템 관리자 | 테넌트 관리자 | 일반 사용자 |
|------|:---:|:---:|:---:|
| `is_superuser` | `true` | `false` | `false` |
| `tenant_id` | `NULL` | 소속 테넌트 | 소속 테넌트 |
| `scope_type` | `GLOBAL` | `TENANT` | `USER` |
| **기능 권한** | 9개 전부 | 6개 | 3개 |
| NL2SQL 실행 | O | O (테넌트 데이터) | O (본인 데이터) |
| RAG 문서 검색 | O | O | O |
| 문서 조회 | O | O | O |
| 문서 등록/수정 | O | O | X |
| 문서 삭제 | O | O (테넌트 내) | X |
| 사용자 관리 | O (전체) | O (테넌트 내) | X |
| 시스템 설정 | O | X | X |
| 테넌트 관리 | O | X | X |
| **관리 화면 접근** | 전체 메뉴 | 문서/사용자/이력 | 접근 불가 |
| **NL2SQL 필터** | 없음 (전체) | `tenant_id = ?` | `tenant_id = ? AND emp_id = ?` |

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

> **`is_superuser` 설계 의도**:
> - **역할**: RBAC 시스템의 **비상 복구 안전장치** (Django의 is_superuser, PostgreSQL의 superuser와 동일한 패턴)
> - **정상 흐름**: 모든 권한 판별은 **RBAC (Role → Permission)** 만 사용. `is_superuser` 직접 체크하지 않음
> - **비상 시나리오**: SYSTEM_ADMIN 역할의 권한이 실수로 삭제되었을 때, `is_superuser=true`인 사용자는 시스템 접근 유지
> - **서비스 코드 원칙**: `if current_user.is_superuser or current_user.scope_type == "GLOBAL"` 형태로만 사용 (scope 판별 보조)
> - **운영 규칙**: `is_superuser=true`는 최소 1명의 관리자에게만 부여. 남용 금지

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
| SYSTEM_ADMIN | 시스템 관리자 | GLOBAL | 전체 시스템 관리 권한 (9개 permission) |
| TENANT_ADMIN | 테넌트 총괄 관리자 | TENANT | 테넌트 내 데이터 + 사용자 관리 (6개 permission) |
| USER | 일반 사용자 | USER | 본인 데이터만, 관리 기능 없음 (3개 permission) |

#### 2.2.4 tb_permission (권한)

| 컬럼명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| permission_id | BIGSERIAL | PK | 권한 고유 ID |
| permission_code | VARCHAR(100) | UK, NOT NULL | 권한 코드 |
| permission_name | VARCHAR(200) | NOT NULL | 권한명 |
| category | VARCHAR(50) | NOT NULL | 카테고리 (nl2sql, rag, admin, document) |
| description | TEXT | NULL | 설명 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 생성일시 |

> **원칙**: permission은 "기능 접근 여부"만 결정. 실제 데이터 범위는 `scope_type`으로 서비스 레이어에서 제한.
> 예: `admin:users` 보유 + `scope_type=TENANT` → 자기 테넌트 사용자만 관리 가능

**기본 권한**:

| permission_code | permission_name | category | 비고 |
|-----------------|-----------------|----------|------|
| nl2sql:execute | NL2SQL 실행 | nl2sql | |
| nl2sql:view_all | NL2SQL 전체 데이터 조회 | nl2sql | GLOBAL만 |
| rag:search | RAG 문서 검색 | rag | |
| document:read | 문서 조회 | document | |
| document:write | 문서 등록/수정 | document | |
| document:delete | 문서 삭제 | document | |
| admin:settings | 시스템 설정 관리 | admin | GLOBAL만 |
| admin:users | 사용자 관리 | admin | scope_type으로 범위 제한 |
| admin:tenants | 테넌트 관리 | admin | GLOBAL만 |

**역할별 권한 매핑**:

| permission | SYSTEM_ADMIN | TENANT_ADMIN | USER |
|------------|:---:|:---:|:---:|
| nl2sql:execute | O | O | O |
| nl2sql:view_all | O | | |
| rag:search | O | O | O |
| document:read | O | O | O |
| document:write | O | O | |
| document:delete | O | O | |
| admin:settings | O | | |
| admin:users | O (전체) | O (테넌트 내) | |
| admin:tenants | O | | |

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

> **`tenant_id` 정합성 규칙**:
> - `tb_user_role.tenant_id`는 `tb_user.tenant_id`와 **일치하거나 NULL(전역 역할)** 이어야 함
> - `tb_user.tenant_id` = 사용자의 **소속 테넌트** (identity), `tb_user_role.tenant_id` = 역할 부여의 **컨텍스트**
> - SYSTEM_ADMIN 부여 시: `tb_user_role.tenant_id = NULL` (전역)
> - TENANT_ADMIN/USER 부여 시: `tb_user_role.tenant_id = tb_user.tenant_id` (소속 테넌트)
> - **다른 테넌트 교차 부여 금지** — 서비스 레이어에서 검증 (MUREUM은 1사용자=1테넌트 모델)

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

### 4.5 서비스 레이어 scope_type 제한 원칙

> NL2SQL 뿐 아니라, **모든 CRUD 서비스**에서 scope_type 기반 데이터 범위 제한을 적용합니다.
> permission은 "기능 접근 여부", scope_type은 "데이터 범위"를 결정하는 **두 축 분리 원칙**.

**사용자 관리 예시** (`user_service.py`):

```python
def list_users(self, current_user: UserContext):
    """scope_type에 따라 조회 범위 자동 제한"""
    if current_user.is_superuser or current_user.scope_type == "GLOBAL":
        return query("SELECT * FROM tb_user")                           # 전체
    elif current_user.scope_type == "TENANT":
        return query("SELECT * FROM tb_user WHERE tenant_id = %s",
                      [current_user.tenant_id])                         # 테넌트 내
    else:
        return query("SELECT * FROM tb_user WHERE user_id = %s",
                      [current_user.user_id])                           # 본인만

def create_user(self, current_user: UserContext, new_user: UserCreate):
    """테넌트 관리자는 자기 테넌트에만 사용자 생성 가능"""
    if current_user.scope_type == "TENANT":
        new_user.tenant_id = current_user.tenant_id  # 강제로 자기 테넌트 설정
```

**문서 관리 예시** (`document_service.py`):

```python
def list_documents(self, current_user: UserContext):
    if current_user.scope_type == "GLOBAL":
        return query("SELECT * FROM tb_docs")                           # 전체
    elif current_user.scope_type == "TENANT":
        return query("SELECT * FROM tb_docs WHERE tenant_id = %s",
                      [current_user.tenant_id])                         # 테넌트 내
```

**적용 대상 서비스 목록**:

| 서비스 | GLOBAL | TENANT | USER |
|--------|--------|--------|------|
| user_service | 전체 사용자 | 테넌트 사용자 | 본인만 |
| document_service | 전체 문서 | 테넌트 문서 | (해당 없음) |
| history_service | 전체 이력 | 테넌트 이력 | 본인 이력 |
| NL2SQL (sql_executor) | 필터 없음 | `tenant_id = ?` | `tenant_id = ? AND emp_id = ?` |

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

---

## 11. 순차 개발 계획 (Implementation Roadmap)

> **작성일**: 2026-02-12
> **목적**: 현재 프로젝트 상태를 분석하여 사용자/권한/테넌트 시스템을 단계적으로 구현하기 위한 순차 개발 계획

### 11.1 현재 상태 분석

#### 준비 완료 항목

| 구분 | 상태 | 비고 |
|------|------|------|
| 설계 문서 | ✅ 완료 | 본 문서 (user_permission_system.md) |
| DDL 스크립트 | ✅ 완료 | `docs/sql/tb_user_permission.sql` (8개 테이블 + 초기 데이터 + 유틸 함수) |
| Python 의존성 | ✅ 설치됨 | `python-jose[cryptography]`, `passlib[bcrypt]` (requirements.txt) |
| JWT 설정 필드 | ✅ 존재 | `app/config.py` — `secret_key`, `algorithm`, `access_token_expire_minutes` |
| 멀티테넌트 컬럼 | ✅ 존재 | 기존 테이블(`tb_api_history`, `tb_docs` 등)에 `tenant_id` 컬럼 이미 포함 |
| 프론트엔드 가드 | ⚠️ placeholder | `frontend/src/router/index.js` — `beforeEach` 주석 처리 상태 |
| History 미들웨어 | ⚠️ 부분 준비 | `X-Tenant-ID`, `X-User-ID` 헤더 읽기만 구현 (검증 없음) |

#### 미구현 항목

| 구분 | 파일 | 상태 |
|------|------|------|
| DB 테이블 | `tb_tenant`, `tb_user`, `tb_role` 등 8개 | ❌ 미생성 |
| Backend 보안 모듈 | `app/core/security/*` | ❌ 디렉토리 자체 없음 |
| 인증 미들웨어 | `app/middleware/auth.py` | ❌ 미생성 |
| 인증 API | `app/api/routes/auth.py` | ❌ 미생성 |
| 관리 API | `users.py`, `roles.py`, `tenants.py` | ❌ 미생성 |
| 인증 서비스 | `auth_service.py`, `user_service.py` 등 | ❌ 미생성 |
| Pydantic 모델 | `user.py`, `auth.py`, `tenant.py` | ❌ 미생성 |
| NL2SQL 필터 주입 | `sql_executor.inject_permission_filter()` | ❌ 미구현 |
| Frontend 로그인 | `LoginView.vue`, `auth.js` 등 | ❌ 미생성 |

---

### 11.2 Phase별 상세 계획

#### Phase 1: 기반 구축 — DB 테이블 + Pydantic 모델

> **목적**: 모든 후속 작업의 기반이 되는 데이터 구조 확립
> **선행 조건**: 없음 (최초 단계)
> **산출물**: DB 테이블 8개 + Pydantic 모델 3개

##### 1-1. DB 테이블 생성

```
실행 대상: docs/sql/tb_user_permission.sql
```

| 테이블 | 설명 | 비고 |
|--------|------|------|
| `tb_tenant` | 테넌트(고객사) | `tenant_code`로 NL2SQL 조건 매핑 |
| `tb_user` | 사용자 계정 | bcrypt 해시, 로그인 실패 잠금 |
| `tb_role` | 역할 정의 | SYSTEM_ADMIN, TENANT_ADMIN, USER |
| `tb_permission` | 권한 정의 | `nl2sql:execute`, `rag:search` 등 |
| `tb_role_permission` | 역할-권한 매핑 | N:M 관계 |
| `tb_user_role` | 사용자-역할 매핑 | 테넌트별 역할 부여 가능 |
| `tb_data_filter` | 데이터 접근 필터 | NL2SQL WHERE 자동 주입 규칙 |
| `tb_user_session` | JWT 세션 | Refresh Token 저장 |

**초기 데이터**:
- 기본 역할 3개 (SYSTEM_ADMIN, TENANT_ADMIN, USER)
- 기본 권한 9개 (nl2sql, rag, document, admin 카테고리)
- 역할-권한 매핑
- 기본 테넌트 2개 (SYSTEM, DEMO)
- 관리자 계정 1개 (admin / admin123!)
- 데이터 필터 설정 (employee 테이블)
- 유틸리티 함수 3개 (`fn_get_user_permissions`, `fn_get_user_data_filters`, `fn_cleanup_expired_sessions`)

##### 1-2. Pydantic 모델 생성

**`app/models/auth.py`** — 인증 요청/응답:
```python
# LoginRequest: username, password
# TokenResponse: access_token, refresh_token, token_type, expires_in, user
# RefreshRequest: refresh_token
# PasswordChangeRequest: current_password, new_password
# UserContext: user_id, username, tenant_id, scope_type, roles, permissions
```

**`app/models/user.py`** — 사용자/역할/권한:
```python
# UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse
# RoleBase, RoleCreate, RoleUpdate, RoleResponse
# PermissionBase, PermissionResponse
# UserRoleAssign: role_id, tenant_id
# DataFilterResponse: filter_id, role_id, target_table, filter_column, filter_type
```

**`app/models/tenant.py`** — 테넌트:
```python
# TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
```

##### 1-3. 완료 검증

- [ ] 모든 테이블 생성 확인 (`\dt tb_*`)
- [ ] 초기 데이터 정상 INSERT 확인
- [ ] Pydantic 모델 import 정상 확인

---

#### Phase 2: Core Security 모듈 (JWT + 비밀번호 + 의존성)

> **목적**: 인증/인가의 핵심 유틸리티 구현
> **선행 조건**: Phase 1 (Pydantic 모델)
> **산출물**: `app/core/security/` 모듈 4개

##### 2-1. 파일 구조

```
app/core/security/
├── __init__.py              # 빈 파일
├── jwt.py                   # JWT 토큰 생성/검증
├── password.py              # 비밀번호 해싱/검증
├── dependencies.py          # FastAPI 의존성 주입 (get_current_user)
└── permission.py            # 권한 검사 데코레이터
```

##### 2-2. 각 파일 역할

**`jwt.py`**:
| 함수 | 설명 |
|------|------|
| `create_access_token(data, expires_delta)` | Access Token 생성 (기본 30분) |
| `create_refresh_token(data, expires_delta)` | Refresh Token 생성 (기본 7일) |
| `verify_token(token)` → `TokenPayload` | 토큰 검증 및 페이로드 반환 |

**`password.py`**:
| 함수 | 설명 |
|------|------|
| `hash_password(plain)` → `str` | bcrypt 해싱 (cost=12) |
| `verify_password(plain, hashed)` → `bool` | 비밀번호 검증 |

**`dependencies.py`**:
| 함수 | 설명 |
|------|------|
| `get_current_user(token)` → `UserContext` | Bearer 토큰에서 사용자 추출 (FastAPI Depends) |
| `get_current_active_user(user)` → `UserContext` | 활성 사용자 검증 |
| `get_optional_user(token)` → `Optional[UserContext]` | 인증 선택적 엔드포인트용 |

**`permission.py`**:
| 함수 | 설명 |
|------|------|
| `require_permission(*perms)` | 권한 검사 데코레이터 (`Depends`로 사용) |
| `require_any_permission(*perms)` | OR 조건 권한 검사 |
| `require_superuser()` | 시스템 관리자 전용 |

##### 2-3. config.py 확장

```python
# 추가 필드
jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh Token 만료(일)")
password_min_length: int = Field(default=8, description="최소 비밀번호 길이")
login_max_fail_count: int = Field(default=5, description="로그인 실패 허용 횟수")
login_lock_minutes: int = Field(default=30, description="계정 잠금 시간(분)")
```

##### 2-4. 완료 검증

- [ ] JWT 토큰 생성/검증 단위 테스트
- [ ] 비밀번호 해싱/검증 단위 테스트
- [ ] `get_current_user` 의존성 동작 확인

---

#### Phase 3: 인증 API + 인증 미들웨어

> **목적**: 로그인/로그아웃/토큰갱신 기능 구현 — 시스템 접근의 첫 관문
> **선행 조건**: Phase 2 (security 모듈)
> **산출물**: 인증 API 5개 + 인증 미들웨어

##### 3-1. 인증 서비스 (`app/api/services/auth_service.py`)

| 메서드 | 설명 |
|--------|------|
| `authenticate(username, password)` | 비밀번호 검증 + 실패 횟수 관리 + 계정 잠금 |
| `create_session(user_id, ip, user_agent)` | DB 세션 생성 + 토큰 발급 |
| `refresh_access_token(refresh_token)` | Refresh Token 검증 → 새 Access Token |
| `logout(session_id)` | 세션 삭제 (토큰 무효화) |
| `get_user_with_permissions(user_id)` | 사용자 + 역할 + 권한 일괄 조회 |
| `change_password(user_id, old, new)` | 비밀번호 변경 |

##### 3-2. 인증 라우트 (`app/api/routes/auth.py`)

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/v1/auth/login` | No | 로그인 (JWT 발급) |
| POST | `/api/v1/auth/logout` | Yes | 로그아웃 (세션 삭제) |
| POST | `/api/v1/auth/refresh` | No* | Access Token 갱신 (*Refresh Token 필요) |
| GET | `/api/v1/auth/me` | Yes | 현재 사용자 정보 조회 |
| PUT | `/api/v1/auth/me/password` | Yes | 비밀번호 변경 |

##### 3-3. 인증 미들웨어 (`app/middleware/auth.py`)

```
요청 처리 흐름:
1. Authorization 헤더에서 Bearer 토큰 추출
2. JWT 검증 → UserContext 생성
3. request.state.current_user에 저장
4. 인증 불필요 경로는 skip (PUBLIC_PATHS)
```

**인증 제외 경로 (PUBLIC_PATHS)**:
```python
PUBLIC_PATHS = {
    "/", "/health", "/docs", "/redoc", "/openapi.json",
    "/api/v1/auth/login", "/api/v1/auth/refresh",
}
PUBLIC_PREFIXES = {
    "/static/",
}
```

##### 3-4. main.py 수정

```python
# 미들웨어 등록 순서 (역순 실행)
app.add_middleware(HistoryMiddleware)     # 4. 이력 저장
app.add_middleware(AuthMiddleware)        # 3. 인증 검증 ← 추가
app.add_middleware(LoggingMiddleware)     # 2. 로깅 + request_id
app.add_middleware(CORSMiddleware, ...)   # 1. CORS

# 라우터 등록
app.include_router(auth.router)          # ← 추가
```

##### 3-5. 하위호환 전략

> **중요**: 인증 미들웨어 도입 시 기존 API가 즉시 깨지지 않도록 단계적 적용

```
Phase 3a: 인증 미들웨어를 "선택적 모드"로 도입
  → 토큰이 있으면 검증, 없으면 anonymous 사용자로 통과
  → 기존 클라이언트는 변경 없이 동작

Phase 3b: 프론트엔드 인증 완료 후 (Phase 6 이후)
  → "필수 모드"로 전환
  → 토큰 없으면 401 반환
```

##### 3-6. 완료 검증

- [ ] 로그인 → 토큰 발급 정상
- [ ] 토큰으로 `/auth/me` 호출 정상
- [ ] 만료된 토큰 → 401 반환
- [ ] Refresh Token으로 갱신 정상
- [ ] 로그아웃 → 세션 삭제 확인
- [ ] 잘못된 비밀번호 5회 → 계정 잠금

---

#### Phase 4: 사용자/역할/테넌트 관리 API (CRUD)

> **목적**: 관리자가 사용자, 역할, 테넌트를 관리할 수 있는 API
> **선행 조건**: Phase 3 (인증 API + 미들웨어)
> **산출물**: 관리 API 18개 + 기존 API 권한 적용
> **핵심 원칙**: permission은 기능 접근, scope_type은 데이터 범위 (섹션 4.5 참조)

##### 4-1. 사용자 관리

**서비스**: `app/api/services/user_service.py`
**라우트**: `app/api/routes/users.py` — prefix: `/api/v1/users`

> **scope_type 제한**: `admin:users` 권한이 있어도 scope_type에 따라 데이터 범위 제한
> - GLOBAL → 전체 사용자 관리
> - TENANT → 자기 테넌트 사용자만 (생성 시 자기 테넌트로 강제)
> - USER → 본인 정보만 조회/수정

| Method | Endpoint | 필요 권한 | scope 제한 | 설명 |
|--------|----------|-----------|------------|------|
| GET | `/` | `admin:users` | GLOBAL: 전체, TENANT: 테넌트 내 | 사용자 목록 |
| POST | `/` | `admin:users` | TENANT: 자기 테넌트로 강제 | 사용자 생성 |
| GET | `/{user_id}` | `admin:users` 또는 본인 | scope 범위 내 | 사용자 상세 |
| PUT | `/{user_id}` | `admin:users` | scope 범위 내 | 사용자 수정 |
| DELETE | `/{user_id}` | `admin:users` | scope 범위 내 | 사용자 삭제 |
| PUT | `/{user_id}/roles` | `admin:users` | GLOBAL만 가능 | 역할 할당 |
| GET | `/{user_id}/permissions` | `admin:users` 또는 본인 | scope 범위 내 | 권한 조회 |

##### 4-2. 역할 관리

**서비스**: `app/api/services/role_service.py`
**라우트**: `app/api/routes/roles.py` — prefix: `/api/v1/roles`

| Method | Endpoint | 필요 권한 | 설명 |
|--------|----------|-----------|------|
| GET | `/` | `admin:users` | 역할 목록 |
| POST | `/` | `admin:users` | 역할 생성 |
| GET | `/{role_id}` | `admin:users` | 역할 상세 (권한 포함) |
| PUT | `/{role_id}` | `admin:users` | 역할 수정 |
| DELETE | `/{role_id}` | `admin:users` | 역할 삭제 (시스템 역할 불가) |
| PUT | `/{role_id}/permissions` | `admin:users` | 권한 할당 |

##### 4-3. 테넌트 관리

**서비스**: `app/api/services/tenant_service.py`
**라우트**: `app/api/routes/tenants.py` — prefix: `/api/v1/tenants`

| Method | Endpoint | 필요 권한 | 설명 |
|--------|----------|-----------|------|
| GET | `/` | `admin:tenants` | 테넌트 목록 |
| POST | `/` | `admin:tenants` | 테넌트 생성 |
| GET | `/{tenant_id}` | `admin:tenants` | 테넌트 상세 |
| PUT | `/{tenant_id}` | `admin:tenants` | 테넌트 수정 |
| DELETE | `/{tenant_id}` | `admin:tenants` | 테넌트 삭제 (비활성화) |

##### 4-4. 기존 API에 권한 + scope 적용

| 기존 라우트 | 적용할 권한 | scope_type 제한 |
|-------------|------------|-----------------|
| `agent.py` — Agent 검색 | 인증만 | NL2SQL 필터로 데이터 제한 |
| `search.py` — RAG/NL2SQL | `rag:search` 또는 `nl2sql:execute` | NL2SQL 필터로 데이터 제한 |
| `documents.py` — 문서 관리 | `document:read`, `document:write`, `document:delete` | GLOBAL: 전체, TENANT: 테넌트 문서 |
| `settings.py` — 시스템 설정 | `admin:settings` | GLOBAL만 접근 가능 |
| `codes.py` — 코드 관리 | `admin:settings` | GLOBAL만 접근 가능 |
| `history.py` — 이력 조회 | 인증 사용자 | GLOBAL: 전체, TENANT: 테넌트 이력, USER: 본인 이력 |

##### 4-5. 완료 검증

- [ ] 사용자 CRUD 정상 동작
- [ ] 역할 할당/해제 정상
- [ ] 권한 없는 사용자 → 403 Forbidden
- [ ] 시스템 역할 삭제 시도 → 400 Bad Request
- [ ] 기존 API에 권한 검사 정상 적용
- [ ] TENANT_ADMIN이 사용자 관리 시 자기 테넌트 사용자만 조회됨
- [ ] TENANT_ADMIN이 사용자 생성 시 자기 테넌트로 강제 설정됨
- [ ] TENANT_ADMIN이 설정/테넌트 관리 접근 시 403

---

#### Phase 5: NL2SQL 권한 필터 주입 (Row-Level Security)

> **목적**: 사용자 권한에 따라 NL2SQL이 생성한 SQL에 자동으로 WHERE 조건 추가
> **선행 조건**: Phase 3 (인증 — UserContext 필요)
> **산출물**: SQL 필터 주입 로직 + 기존 노드 수정
> **비고**: Phase 4와 병렬 진행 가능

##### 5-1. SQL 필터 주입 (`app/core/database/sql_executor.py`)

```python
def inject_permission_filter(self, sql: str, user_context: UserContext) -> str:
    """
    사용자 권한(scope_type)에 따라 SQL에 WHERE 조건 자동 주입

    scope_type별 동작:
    - GLOBAL  → 변경 없음 (전체 데이터)
    - TENANT  → WHERE tenant_id = {user_context.tenant_id} 추가
    - USER    → WHERE tenant_id = {tenant_id} AND emp_id = {user_id} 추가
    """
```

**내부 처리 흐름**:
```
1. GLOBAL → return sql (변경 없음)
2. tb_data_filter에서 해당 역할의 필터 조건 조회
3. sqlparse로 SQL에서 테이블명 추출
4. 각 테이블에 대해 필터 조건(WHERE/AND) 추가
5. 파라미터 바인딩으로 SQL Injection 방지
```

##### 5-2. NL2SQL 노드 수정 (`app/graphs/nl2sql/nodes.py`)

| 노드 | 수정 내용 |
|------|----------|
| `execute_sql_node` | SQL 실행 전 `inject_permission_filter()` 호출 |

```python
# execute_sql_node 수정 (개념)
user_context = state.get("user_context")  # 미들웨어에서 전달받은 사용자 정보
if user_context:
    sql = sql_executor.inject_permission_filter(sql, user_context)
result = sql_executor.execute(sql)
```

##### 5-3. Agent SQL Tool 수정 (`app/graphs/agent/tools/sql_tool.py`)

| 수정 대상 | 수정 내용 |
|-----------|----------|
| `query_database_tool` | Tool 실행 시 UserContext를 받아 필터 적용 |

##### 5-4. History 미들웨어 수정 (`app/middleware/history.py`)

```python
# 변경 전 (헤더에서 직접 읽기 — 위변조 가능)
tenant_id = request.headers.get("X-Tenant-ID")
user_id = request.headers.get("X-User-ID")

# 변경 후 (인증된 UserContext에서 읽기)
current_user = getattr(request.state, "current_user", None)
tenant_id = current_user.tenant_id if current_user else None
user_id = current_user.user_id if current_user else None
```

##### 5-5. 필터 적용 예시

```
원본 질문: "2024년 입사자 목록 보여줘"

LLM 생성 SQL:
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01'

[시스템 관리자 (GLOBAL)] → 변경 없음
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01'

[테넌트 관리자 (TENANT, tenant_id=5)] → tenant_id 조건 추가
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01' AND tenant_id = 5

[일반 사용자 (USER, tenant_id=5, user_id=123)] → tenant_id + emp_id 조건 추가
  SELECT emp_name, hire_date FROM employee WHERE hire_date >= '2024-01-01' AND tenant_id = 5 AND emp_id = 123
```

##### 5-6. 완료 검증

- [ ] GLOBAL 사용자 → 필터 없이 전체 데이터 조회
- [ ] TENANT 사용자 → 해당 테넌트 데이터만 조회
- [ ] USER 사용자 → 본인 데이터만 조회
- [ ] JOIN 쿼리에서도 필터 정상 적용
- [ ] 파라미터 바인딩으로 SQL Injection 차단 확인

---

#### Phase 6: 프론트엔드 인증 통합

> **목적**: 로그인 UI, 인증 상태 관리, 관리자 화면 구현
> **선행 조건**: Phase 3 (인증 API), Phase 4 (관리 API)
> **산출물**: 로그인 화면 + Auth 모듈 + 관리 화면 3개

##### 6-1. 인증 인프라

| 파일 | 설명 |
|------|------|
| `frontend/src/api/auth.js` | 인증 API 클라이언트 (login, logout, refresh, me) |
| `frontend/src/store/modules/auth.js` | Vuex 인증 상태 (token, user, isAuthenticated) |
| `frontend/src/api/index.js` (수정) | Axios 인터셉터에 Authorization 헤더 자동 추가, 401 시 토큰 갱신 |

##### 6-2. 로그인 화면

| 파일 | 설명 |
|------|------|
| `frontend/src/views/LoginView.vue` | 로그인 폼 (username, password, remember me) |

**기능**:
- 로그인 폼 (유효성 검사 포함)
- 로그인 실패 시 에러 메시지 표시
- 계정 잠금 시 잠금 해제 시간 안내
- 로그인 성공 시 `/chat` 또는 이전 페이지로 리다이렉트

##### 6-3. 라우터 가드 활성화 (권한 기반)

| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/router/index.js` | `beforeEach` 가드 활성화 — 미인증 시 `/login`으로 리다이렉트, **권한 기반** 관리자 접근 제어 |

> **핵심 변경**: 기존 `roles.includes('SYSTEM_ADMIN')` 하드코딩 → `permissions` 기반 판별.
> TENANT_ADMIN도 `admin:users` 권한을 가지므로 관리자 화면 접근 가능.

```javascript
router.beforeEach((to, from, next) => {
  const authStore = store.state.auth
  const isAuthenticated = !!authStore.accessToken

  if (to.path === '/login') {
    // 이미 로그인된 경우 메인으로
    isAuthenticated ? next('/chat') : next()
  } else if (!isAuthenticated) {
    // 미인증 → 로그인 페이지
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin) {
    // ── 권한 기반 관리자 접근 제어 ──
    // admin:* 권한이 하나라도 있으면 관리자 화면 접근 허용
    const permissions = authStore.user?.permissions || []
    const hasAdminAccess = permissions.some(p => p.startsWith('admin:'))
    hasAdminAccess ? next() : next('/chat')
  } else {
    next()
  }
})
```

##### 6-4. 관리자 화면

| 파일 | 설명 |
|------|------|
| `frontend/src/views/admin/UsersView.vue` | 사용자 목록/생성/수정/삭제, 역할 할당 |
| `frontend/src/views/admin/RolesView.vue` | 역할 목록/생성/수정, 권한 할당 |
| `frontend/src/views/admin/TenantsView.vue` | 테넌트 목록/생성/수정/삭제 |

##### 6-5. 사이드바/헤더 수정 (권한 기반 메뉴 제어)

| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/components/layout/AppSidebar.vue` | **권한(permission) 기반** 메뉴 표시/숨김 |
| `frontend/src/components/layout/AppHeader.vue` | 사용자 정보 표시, 로그아웃 버튼 |
| `frontend/src/components/user/UserChatLayout.vue` | 사용자명 표시 |

> **핵심 원칙**: 메뉴 표시 여부는 `role`이 아닌 `permission`으로 판별한다.
> 역할이 추가되어도 프론트엔드 코드 변경 없이 DB에서 권한만 부여하면 메뉴가 자동으로 보인다.

```javascript
// AppSidebar.vue — 메뉴 필터링 예시
const adminMenus = computed(() => {
  const perms = authStore.user?.permissions || []
  const hasPermission = (code) => perms.includes(code)

  return [
    // 모든 admin:* 권한자에게 표시
    { path: '/admin/chat',      title: '자연어 검색',  show: true },
    // document:read 이상이면 표시
    { path: '/admin/documents', title: '지식문서 관리', show: hasPermission('document:read') },
    // admin:users 권한자에게만 표시 (SYSTEM_ADMIN, TENANT_ADMIN)
    { path: '/admin/users',     title: '사용자 관리',   show: hasPermission('admin:users') },
    // admin:roles 권한은 SYSTEM_ADMIN만 보유 → 시스템 관리자만 표시
    { path: '/admin/roles',     title: '역할 관리',     show: hasPermission('admin:roles') },
    // admin:tenants 권한은 SYSTEM_ADMIN만 보유
    { path: '/admin/tenants',   title: '테넌트 관리',   show: hasPermission('admin:tenants') },
    { path: '/admin/settings',  title: '시스템 설정',   show: hasPermission('admin:settings') },
    { path: '/admin/codes',     title: '코드 관리',     show: hasPermission('admin:settings') },
    { path: '/admin/history',   title: '검색 이력',     show: hasPermission('admin:settings') },
  ].filter(menu => menu.show)
})
```

**역할별 보이는 메뉴 비교**:

| 메뉴 | SYSTEM_ADMIN | TENANT_ADMIN | USER |
|------|:---:|:---:|:---:|
| 자연어 검색 | O | O | - |
| 지식문서 관리 | O | O | - |
| 사용자 관리 | O | O (테넌트 내) | - |
| 역할 관리 | O | - | - |
| 테넌트 관리 | O | - | - |
| 시스템 설정 | O | - | - |
| 코드 관리 | O | - | - |
| 검색 이력 | O | - | - |

##### 6-6. 라우터에 관리 화면 추가

```javascript
// admin children에 추가
{ path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/UsersView.vue'), meta: { title: '사용자 관리' } },
{ path: 'roles', name: 'AdminRoles', component: () => import('@/views/admin/RolesView.vue'), meta: { title: '역할 관리' } },
{ path: 'tenants', name: 'AdminTenants', component: () => import('@/views/admin/TenantsView.vue'), meta: { title: '테넌트 관리' } },
```

##### 6-7. 완료 검증

- [ ] 로그인 → 토큰 저장 → 페이지 이동 정상
- [ ] 미인증 접근 → 로그인 페이지 리다이렉트
- [ ] 토큰 만료 → 자동 갱신 → 요청 재시도
- [ ] 로그아웃 → 토큰 삭제 → 로그인 페이지
- [ ] 관리자 화면에서 사용자/역할/테넌트 CRUD 정상
- [ ] 권한 없는 메뉴 숨김 처리 정상
- [ ] **SYSTEM_ADMIN → /admin 접근 시 모든 메뉴 표시**
- [ ] **TENANT_ADMIN → /admin 접근 허용, 사용자 관리/문서 관리만 표시**
- [ ] **TENANT_ADMIN → 역할 관리/테넌트 관리/시스템 설정 메뉴 숨김 확인**
- [ ] **USER → /admin 접근 시 /chat으로 리다이렉트**
- [ ] **DB에 새 역할 추가 후 → 프론트엔드 코드 변경 없이 메뉴 자동 표시 확인**

---

### 11.3 Phase 의존 관계

```
Phase 1: DB 테이블 + Pydantic 모델
    │
    ▼
Phase 2: Core Security (JWT, Password, Dependencies)
    │
    ▼
Phase 3: Auth API (Login/Logout/Refresh) + Auth Middleware
    │
    ├───────────────────────┐
    ▼                       ▼
Phase 4:                Phase 5:
User/Role/Tenant        NL2SQL Filter
CRUD API                Injection
(관리 기능)              (Row-Level Security)
    │                       │
    └───────────┬───────────┘
                ▼
           Phase 6:
           Frontend
           (Login UI, Router Guard, Admin UI)
```

> **Phase 4와 5는 독립적**이므로 병렬 진행 가능.
> 단, 둘 다 **Phase 3 완료가 전제 조건**.

---

### 11.4 Phase별 생성 파일 요약

```
Phase 1 (기반):
  [DB]  docs/sql/tb_user_permission.sql 실행
  [NEW] app/models/auth.py
  [NEW] app/models/user.py
  [NEW] app/models/tenant.py

Phase 2 (보안 코어):
  [NEW] app/core/security/__init__.py
  [NEW] app/core/security/jwt.py
  [NEW] app/core/security/password.py
  [NEW] app/core/security/dependencies.py
  [NEW] app/core/security/permission.py
  [MOD] app/config.py                          ← JWT 설정 확장

Phase 3 (인증 API):
  [NEW] app/api/services/auth_service.py
  [NEW] app/api/routes/auth.py
  [NEW] app/middleware/auth.py
  [MOD] app/main.py                            ← 미들웨어 + 라우터 등록

Phase 4 (관리 API):
  [NEW] app/api/services/user_service.py
  [NEW] app/api/services/role_service.py
  [NEW] app/api/services/tenant_service.py
  [NEW] app/api/routes/users.py
  [NEW] app/api/routes/roles.py
  [NEW] app/api/routes/tenants.py
  [MOD] app/api/routes/agent.py                ← 권한 적용
  [MOD] app/api/routes/search.py               ← 권한 적용
  [MOD] app/api/routes/documents.py            ← 권한 적용
  [MOD] app/api/routes/settings.py             ← 권한 적용

Phase 5 (NL2SQL 필터):
  [MOD] app/core/database/sql_executor.py      ← inject_permission_filter()
  [MOD] app/graphs/nl2sql/nodes.py             ← execute_sql_node 수정
  [MOD] app/graphs/agent/tools/sql_tool.py     ← 필터 적용
  [MOD] app/middleware/history.py              ← UserContext에서 읽기

Phase 6 (프론트엔드):
  [NEW] frontend/src/views/LoginView.vue
  [NEW] frontend/src/api/auth.js
  [NEW] frontend/src/store/modules/auth.js
  [NEW] frontend/src/views/admin/UsersView.vue
  [NEW] frontend/src/views/admin/RolesView.vue
  [NEW] frontend/src/views/admin/TenantsView.vue
  [MOD] frontend/src/api/index.js              ← 인터셉터 수정
  [MOD] frontend/src/router/index.js           ← 가드 활성화 + 라우트 추가
  [MOD] frontend/src/components/layout/AppSidebar.vue  ← 권한별 메뉴
  [MOD] frontend/src/components/layout/AppHeader.vue   ← 사용자 정보 표시
```

**총계**: 신규 파일 17개 + 수정 파일 12개

---

### 11.5 환경 설정 변경 사항

#### `.env` 파일 추가 항목

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

#### `requirements.txt` (변경 없음)

`python-jose[cryptography]`와 `passlib[bcrypt]`가 이미 포함되어 있으므로 추가 의존성 불필요.

---

### 11.6 주의사항

1. **하위호환**: Phase 3에서 인증 미들웨어를 "선택적 모드"로 도입하여 기존 클라이언트 영향 최소화. Phase 6 완료 후 "필수 모드"로 전환
2. **admin 초기 비밀번호**: DDL의 bcrypt 해시는 예시용. 실배포 시 애플리케이션에서 동적 생성 필요
3. **테스트**: 각 Phase 완료 시점에 해당 Phase의 검증 체크리스트 수행
4. **보안**: `SECRET_KEY`는 프로덕션에서 반드시 강력한 랜덤 값 사용. `.env`에 저장하고 git에 포함하지 않을 것
5. **마이그레이션**: 기존 `tb_api_history`의 `tenant_id`, `user_id` 값은 인증 도입 전까지 NULL. 인증 후 자동으로 채워짐
