# Phase 1 구현 가이드: DB 테이블 + Pydantic 모델

> **문서 버전**: 1.0
> **작성일**: 2026-02-12
> **상위 문서**: `docs/design/user_permission_system.md`
> **목적**: Phase 1(기반 구축)의 실제 구현 절차를 코드 레벨에서 상세 설명

---

## 목차

1. [Phase 1 개요](#1-phase-1-개요)
2. [Step 1: DDL 실행 — 데이터베이스 테이블 생성](#2-step-1-ddl-실행)
3. [Step 2: `app/models/auth.py` — 인증 모델](#3-step-2-appmodelsauthpy)
4. [Step 3: `app/models/user.py` — 사용자/역할/권한 모델](#4-step-3-appmodelsuserpy)
5. [Step 4: `app/models/tenant.py` — 테넌트 모델](#5-step-4-appmodelstenantpy)
6. [Step 5: `app/config.py` 수정 — JWT 추가 설정](#6-step-5-appconfigpy-수정)
7. [검증 체크리스트](#7-검증-체크리스트)
8. [다음 단계 (Phase 2 Preview)](#8-다음-단계)

---

## 1. Phase 1 개요

### 1.1 무엇을 하는가

Phase 1은 **모든 후속 Phase의 기반**이 되는 데이터 구조를 확립하는 단계입니다.

```
Phase 1 산출물:
  [DB]  8개 테이블 + 초기 데이터
  [NEW] app/models/auth.py      ← 인증 요청/응답 모델
  [NEW] app/models/user.py      ← 사용자/역할/권한 모델
  [NEW] app/models/tenant.py    ← 테넌트 모델
  [MOD] app/config.py           ← JWT 추가 설정 필드
```

### 1.2 왜 필요한가

| 산출물 | 사용처 | 없으면 어떻게 되는가 |
|--------|--------|---------------------|
| DB 테이블 | Phase 2~6 전체 | 사용자/역할/권한 데이터를 저장할 곳이 없음 |
| Pydantic 모델 | API 요청/응답 직렬화, 타입 검증 | FastAPI 엔드포인트가 데이터 구조를 모름 |
| config.py 확장 | JWT 토큰 만료 시간 등 설정 | Phase 2에서 JWT 모듈이 설정값을 읽지 못함 |

### 1.3 구현 순서 (의존 관계)

```
Step 1: DDL 실행          → 테이블이 있어야 데이터를 넣을 수 있음
Step 2: auth.py 생성      → 인증 모델 (다른 모델에 의존하지 않음)
Step 3: user.py 생성      → 사용자/역할 모델 (auth.py의 UserInfo 참조)
Step 4: tenant.py 생성    → 테넌트 모델 (독립적)
Step 5: config.py 수정    → 추가 설정 필드 (독립적, Step 2~4와 병렬 가능)
```

### 1.4 기존 프로젝트 패턴 요약

Phase 1 코드를 작성하기 전에, 기존 MUREUM 프로젝트에서 사용하는 Pydantic 모델 패턴을 이해해야 합니다.

**기존 모델 파일 구조** (`app/models/` 디렉토리):
```
app/models/
├── __init__.py       ← 빈 파일 (CLAUDE.md 규칙)
├── agent.py          ← Agent 요청/응답
├── search.py         ← 검색 요청/응답
├── documents.py      ← 문서 CRUD
├── history.py        ← API 이력
├── rag.py            ← RAG 관련
├── settings.py       ← 설정
├── codes.py          ← 코드 관리
├── common.py         ← 공통
├── sse.py            ← SSE 이벤트
├── auth.py           ← [NEW] Phase 1에서 생성
├── user.py           ← [NEW] Phase 1에서 생성
└── tenant.py         ← [NEW] Phase 1에서 생성
```

**기존 코드에서 확인한 Pydantic 패턴**:

```python
# 1. 기본 import 패턴
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 2. 모든 필드에 Field()로 description 명시
query: str = Field(..., min_length=1, description="검색 질의")

# 3. Optional 필드는 None 기본값
session_id: Optional[str] = Field(None, description="세션 ID")

# 4. model_config로 API 문서 예시 제공
model_config = {
    "json_schema_extra": {
        "example": { ... }
    }
}

# 5. 상속 패턴: Base → Create/Update/Response
class UserBase(BaseModel): ...
class UserCreate(UserBase): ...
class UserResponse(UserBase): ...

# 6. __init__.py는 빈 파일 (import 문 작성하지 않음)
```

---

## 2. Step 1: DDL 실행

### 2.1 실행 대상 파일

```
파일 위치: docs/sql/tb_user_permission.sql
실행 대상: PostgreSQL (hermesdb)
접속 정보: postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb
```

### 2.2 실행 방법

**방법 A: psql 명령줄**
```bash
# Conda 환경 활성화
conda activate penv3.13-nlq

# psql로 DDL 실행
psql "postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb" -f docs/sql/tb_user_permission.sql
```

**방법 B: DBeaver/pgAdmin 등 GUI 도구**
1. `docs/sql/tb_user_permission.sql` 파일 전체를 복사
2. SQL 편집기에 붙여넣기
3. 전체 실행 (F5 또는 Ctrl+Enter)

### 2.3 DDL이 생성하는 것

#### 테이블 8개

| # | 테이블명 | 용도 | 핵심 컬럼 |
|---|---------|------|----------|
| 1 | `tb_tenant` | 테넌트(고객사) | `tenant_code` — NL2SQL WHERE 조건에 사용 |
| 2 | `tb_user` | 사용자 계정 | `password_hash` (bcrypt), `is_superuser` (비상 안전장치) |
| 3 | `tb_role` | 역할 정의 | `scope_type` — GLOBAL/TENANT/USER (데이터 범위) |
| 4 | `tb_permission` | 권한 정의 | `permission_code` — `category:action` 형식 |
| 5 | `tb_role_permission` | 역할↔권한 N:M 매핑 | 복합 PK (role_id, permission_id) |
| 6 | `tb_user_role` | 사용자↔역할 매핑 | 복합 PK + `tenant_id` (컨텍스트) |
| 7 | `tb_data_filter` | 데이터 접근 필터 | NL2SQL WHERE 자동 주입 규칙 |
| 8 | `tb_user_session` | JWT 세션 | `refresh_token` 저장 |

#### 초기 데이터

| 데이터 | 내용 |
|--------|------|
| 역할 3개 | SYSTEM_ADMIN (GLOBAL/9권한), TENANT_ADMIN (TENANT/6권한), USER (USER/3권한) |
| 권한 9개 | nl2sql:execute, nl2sql:view_all, rag:search, document:read/write/delete, admin:settings/users/tenants |
| 테넌트 2개 | SYSTEM (내부), DEMO (테스트) |
| 관리자 1명 | admin / admin123! (bcrypt 해시) |
| 데이터 필터 4개 | TENANT_ADMIN→employee/tb_user, USER→employee/tb_user |

### 2.4 실행 후 검증 쿼리

DDL 실행 후 아래 쿼리로 정상 생성을 확인합니다.

```sql
-- 1) 테이블 존재 확인
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'tb_%'
ORDER BY table_name;
-- 결과: tb_data_filter, tb_permission, tb_role, tb_role_permission,
--       tb_tenant, tb_user, tb_user_role, tb_user_session (8개)

-- 2) 역할 확인
SELECT role_code, role_name, scope_type FROM tb_role ORDER BY sort_order;
-- 결과: SYSTEM_ADMIN/GLOBAL, TENANT_ADMIN/TENANT, USER/USER

-- 3) 권한 확인
SELECT permission_code, category FROM tb_permission ORDER BY category, permission_code;
-- 결과: 9개 권한

-- 4) 역할-권한 매핑 확인
SELECT r.role_code, COUNT(*) as permission_count
FROM tb_role_permission rp
JOIN tb_role r ON rp.role_id = r.role_id
GROUP BY r.role_code ORDER BY r.role_code;
-- 결과: SYSTEM_ADMIN=9, TENANT_ADMIN=6, USER=3

-- 5) 관리자 계정 확인
SELECT login_id, display_name, is_superuser FROM tb_user;
-- 결과: admin, 시스템 관리자, true

-- 6) 데이터 필터 확인
SELECT r.role_code, df.target_table, df.filter_column, df.filter_type
FROM tb_data_filter df
JOIN tb_role r ON df.role_id = r.role_id
ORDER BY r.role_code, df.target_table;
-- 결과: TENANT_ADMIN→employee(TENANT), TENANT_ADMIN→tb_user(TENANT),
--       USER→employee(USER), USER→tb_user(USER)

```

### 2.5 DDL 핵심 설계 원칙 (참고)

```
permission = "기능 접근 여부"  (무엇을 할 수 있는가)
scope_type = "데이터 범위"    (어디까지 볼 수 있는가)

예: admin:users 권한 + scope_type=TENANT → 자기 테넌트 사용자만 관리
    admin:users 권한 + scope_type=GLOBAL → 전체 사용자 관리
```

---

## 3. Step 2: `app/models/auth.py`

### 3.1 파일 위치와 목적

```
파일 경로: app/models/auth.py
목적: 인증(Authentication) 관련 요청/응답 데이터 구조 정의
사용처: Phase 3의 인증 API (POST /api/v1/auth/login 등)에서 사용
```

### 3.2 이 파일이 필요한 이유

| 클래스 | 사용처 | 없으면 어떻게 되는가 |
|--------|--------|---------------------|
| `LoginRequest` | `POST /auth/login` 요청 바디 | 클라이언트가 보내는 login_id/password를 검증할 수 없음 |
| `TokenResponse` | 로그인 성공 응답 | access_token 등을 구조화하여 반환할 수 없음 |
| `UserInfo` | TokenResponse 내부의 사용자 정보 | 로그인 응답에 사용자 정보를 포함할 수 없음 |
| `UserContext` | 인증 미들웨어가 생성하는 현재 사용자 객체 | 모든 API에서 현재 사용자를 알 수 없음 |
| `RefreshRequest` | `POST /auth/refresh` 요청 바디 | 토큰 갱신 요청을 파싱할 수 없음 |
| `PasswordChangeRequest` | `PUT /auth/me/password` 요청 바디 | 비밀번호 변경 요청을 검증할 수 없음 |

### 3.3 전체 소스코드

```python
"""
인증(Authentication) 스키마

위치: app/models/auth.py
로그인, 토큰, 사용자 컨텍스트 관련 모델
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 로그인 요청/응답
# ===================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    password: str = Field(..., min_length=1, description="비밀번호")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "admin",
                "password": "admin123!"
            }
        }
    }


class UserInfo(BaseModel):
    """로그인 응답에 포함되는 사용자 정보 (JWT payload의 일부)"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")


class TokenResponse(BaseModel):
    """로그인 성공 응답 (JWT 토큰 + 사용자 정보)"""
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")
    user: UserInfo = Field(..., description="사용자 정보")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 1800,
                "user": {
                    "user_id": 1,
                    "login_id": "admin",
                    "display_name": "시스템 관리자",
                    "tenant_id": None,
                    "scope_type": "GLOBAL",
                    "roles": ["SYSTEM_ADMIN"],
                    "permissions": ["nl2sql:execute", "admin:settings"]
                }
            }
        }
    }


# ===================================
# 토큰 갱신
# ===================================

class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., min_length=1, description="Refresh Token")


# ===================================
# 비밀번호 변경
# ===================================

class PasswordChangeRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., min_length=1, description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호 (8자 이상)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """새 비밀번호 복잡도 검증"""
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "oldPassword1!",
                "new_password": "newPassword2!"
            }
        }
    }


# ===================================
# 사용자 컨텍스트 (인증 미들웨어 → API 핸들러)
# ===================================

class UserContext(BaseModel):
    """
    인증된 사용자 컨텍스트

    인증 미들웨어가 JWT를 검증한 후 생성하여 request.state.current_user에 저장.
    모든 API 핸들러에서 현재 사용자 정보를 참조할 때 사용.
    """
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    scope_type: str = Field(default="USER", description="데이터 범위 (GLOBAL, TENANT, USER)")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")

    def has_permission(self, permission_code: str) -> bool:
        """특정 권한 보유 여부 확인"""
        if self.is_superuser:
            return True
        return permission_code in self.permissions

    def has_any_permission(self, *permission_codes: str) -> bool:
        """주어진 권한 중 하나라도 보유하는지 확인 (OR 조건)"""
        if self.is_superuser:
            return True
        return any(p in self.permissions for p in permission_codes)

    def has_all_permissions(self, *permission_codes: str) -> bool:
        """주어진 권한을 모두 보유하는지 확인 (AND 조건)"""
        if self.is_superuser:
            return True
        return all(p in self.permissions for p in permission_codes)

    @property
    def is_global(self) -> bool:
        """GLOBAL scope 여부 (전체 데이터 접근)"""
        return self.is_superuser or self.scope_type == "GLOBAL"

    @property
    def is_tenant_scope(self) -> bool:
        """TENANT scope 여부"""
        return self.scope_type == "TENANT"

    @property
    def is_user_scope(self) -> bool:
        """USER scope 여부"""
        return self.scope_type == "USER"
```

### 3.4 코드 상세 설명

#### 3.4.1 import 문

```python
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
```

| import | 설명 |
|--------|------|
| `List` | `List[str]`처럼 리스트 타입 힌트에 사용. Python 3.9+에서는 `list[str]`도 가능하지만, 기존 프로젝트 패턴에 맞춰 `typing.List` 사용 |
| `Optional` | `Optional[str]`은 `str | None`과 동일. 값이 없을 수 있는 필드에 사용 |
| `BaseModel` | Pydantic의 기본 모델 클래스. 모든 모델이 이 클래스를 상속 |
| `Field` | 필드 메타데이터 정의. `...`은 필수, `None`은 선택, `default=값`은 기본값 |
| `field_validator` | Pydantic v2의 필드 검증 데코레이터. 특정 필드에 커스텀 검증 로직 추가 |

#### 3.4.2 LoginRequest

```python
class LoginRequest(BaseModel):
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    password: str = Field(..., min_length=1, description="비밀번호")
```

- `Field(...)`: `...`은 Python의 `Ellipsis` 객체. Pydantic에서 **필수 필드**를 의미
- `min_length=1`: 빈 문자열 방지. `""` 전송 시 422 Validation Error 반환
- `max_length=100`: DB의 `tb_user.login_id VARCHAR(100)`과 일치
- **DB 매핑**: `login_id` → `tb_user.login_id`, `password` → bcrypt로 해싱 후 `tb_user.password_hash`와 비교

#### 3.4.3 UserInfo (JWT 페이로드 → 프론트엔드)

```python
class UserInfo(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")
```

- `default_factory=list`: 기본값으로 **새 리스트 인스턴스**를 생성. `default=[]`를 쓰면 모든 인스턴스가 같은 리스트를 공유하는 **mutable default 버그** 발생
- `scope_type`: `tb_role.scope_type`에서 가져온 값. GLOBAL/TENANT/USER 중 하나
- `roles`, `permissions`: DB에서 5-테이블 JOIN으로 조회한 결과
  ```
  tb_user → tb_user_role → tb_role → tb_role_permission → tb_permission
  ```

#### 3.4.4 TokenResponse (로그인 성공 응답)

```python
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Access Token")
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")
    user: UserInfo = Field(..., description="사용자 정보")
```

- `user: UserInfo`: 다른 Pydantic 모델을 필드 타입으로 사용 (중첩 모델). JSON으로 직렬화 시 자동으로 중첩 객체가 됨
- `expires_in`: 초 단위. `config.py`의 `access_token_expire_minutes * 60`으로 계산

**응답 JSON 구조**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "user_id": 1,
    "login_id": "admin",
    "scope_type": "GLOBAL",
    "roles": ["SYSTEM_ADMIN"],
    "permissions": ["nl2sql:execute", "admin:settings", ...]
  }
}
```

#### 3.4.5 PasswordChangeRequest (비밀번호 검증)

```python
@field_validator("new_password")
@classmethod
def validate_new_password(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("비밀번호는 8자 이상이어야 합니다")
    has_upper = any(c.isupper() for c in v)
    has_lower = any(c.islower() for c in v)
    has_digit = any(c.isdigit() for c in v)
    if not (has_upper and has_lower and has_digit):
        raise ValueError("비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다")
    return v
```

- `@field_validator("new_password")`: `new_password` 필드에만 적용되는 검증 함수
- `@classmethod`: Pydantic v2에서 `field_validator`는 반드시 클래스 메서드여야 함 (`cls` 파라미터 필수)
- `v: str`: 검증 대상 값. Pydantic이 자동으로 전달
- `raise ValueError(...)`: 검증 실패 시 FastAPI가 자동으로 `422 Unprocessable Entity` 반환
- `return v`: 검증 통과 시 반드시 값을 반환해야 함 (변환도 가능)
- `any(c.isupper() for c in v)`: 제너레이터 표현식. 문자열의 각 문자를 순회하며 조건 충족 시 True 반환

#### 3.4.6 UserContext (핵심 — 인증 미들웨어의 산출물)

```python
class UserContext(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    scope_type: str = Field(default="USER", description="데이터 범위")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")

    def has_permission(self, permission_code: str) -> bool:
        if self.is_superuser:
            return True
        return permission_code in self.permissions
```

**UserContext가 가장 중요한 이유**:

Phase 3 이후 **모든 API 핸들러**에서 이 객체를 사용합니다:

```python
# Phase 3: 인증 미들웨어가 생성
# middleware/auth.py (미래 구현)
request.state.current_user = UserContext(
    user_id=1,
    login_id="admin",
    scope_type="GLOBAL",
    permissions=["nl2sql:execute", "admin:settings", ...]
)

# Phase 4: API 핸들러에서 사용
# routes/users.py (미래 구현)
@router.get("/")
async def list_users(current_user: UserContext = Depends(get_current_user)):
    if current_user.has_permission("admin:users"):
        if current_user.is_global:
            return get_all_users()
        elif current_user.is_tenant_scope:
            return get_tenant_users(current_user.tenant_id)
```

**메서드 설명**:

| 메서드 | 용도 | 예시 |
|--------|------|------|
| `has_permission(code)` | 특정 권한 보유 확인 | `user.has_permission("admin:settings")` |
| `has_any_permission(*codes)` | 하나라도 있으면 True | `user.has_any_permission("document:write", "document:delete")` |
| `has_all_permissions(*codes)` | 모두 있어야 True | `user.has_all_permissions("nl2sql:execute", "nl2sql:view_all")` |

**프로퍼티 설명**:

| 프로퍼티 | 반환값 | 용도 |
|---------|--------|------|
| `is_global` | `bool` | GLOBAL scope 또는 superuser인지 (데이터 필터 skip) |
| `is_tenant_scope` | `bool` | TENANT scope인지 (테넌트 필터 적용) |
| `is_user_scope` | `bool` | USER scope인지 (사용자 필터 적용) |

```python
@property
def is_global(self) -> bool:
    return self.is_superuser or self.scope_type == "GLOBAL"
```

- `@property`: 메서드를 속성처럼 호출 가능 (`user.is_global` — 괄호 없이 사용)
- `self.is_superuser or ...`: superuser는 RBAC 비상 안전장치이므로 항상 GLOBAL처럼 동작

---

## 4. Step 3: `app/models/user.py`

### 4.1 파일 위치와 목적

```
파일 경로: app/models/user.py
목적: 사용자, 역할, 권한 CRUD 작업의 데이터 구조 정의
사용처: Phase 4의 관리 API (/api/v1/users, /api/v1/roles 등)에서 사용
```

### 4.2 이 파일이 필요한 이유

| 클래스 그룹 | 사용처 | 없으면 어떻게 되는가 |
|------------|--------|---------------------|
| UserBase/Create/Update/Response | 사용자 CRUD API | 사용자 생성/수정 요청을 검증할 수 없음 |
| RoleBase/Create/Update/Response | 역할 관리 API | 역할 생성/수정 데이터를 구조화할 수 없음 |
| PermissionResponse | 권한 조회 API | 권한 목록을 반환할 수 없음 |
| UserRoleAssign | 역할 할당 API | 사용자에게 역할을 부여하는 요청을 파싱할 수 없음 |
| DataFilterResponse | 필터 조회 API | 데이터 필터 정보를 반환할 수 없음 |

### 4.3 전체 소스코드

```python
"""
사용자/역할/권한 관리 스키마

위치: app/models/user.py
사용자 CRUD, 역할 관리, 권한 조회 관련 모델
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 사용자 (User)
# ===================================

class UserBase(BaseModel):
    """사용자 기본 필드 (Create/Update의 공통 부모)"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    email: str = Field(..., max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """이메일 형식 간단 검증"""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v.lower().strip()


class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")
    is_active: bool = Field(default=True, description="활성화 여부")
    role_ids: List[int] = Field(default_factory=list, description="부여할 역할 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "user01",
                "email": "user01@company.com",
                "display_name": "홍길동",
                "password": "Password1!",
                "tenant_id": 2,
                "is_active": True,
                "role_ids": [3]
            }
        }
    }


class UserUpdate(BaseModel):
    """사용자 수정 요청 (모든 필드 Optional — 부분 수정 지원)"""
    email: Optional[str] = Field(None, max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("올바른 이메일 형식이 아닙니다")
            return v.lower().strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "display_name": "홍길동 (수정)",
                "is_active": True
            }
        }
    }


class RoleSimple(BaseModel):
    """역할 간략 정보 (UserResponse에 포함용)"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    scope_type: str = Field(..., description="데이터 범위")


class UserResponse(BaseModel):
    """사용자 상세 응답"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    email: str = Field(..., description="이메일")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    tenant_name: Optional[str] = Field(None, description="소속 테넌트명")
    is_active: bool = Field(..., description="활성화 여부")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 일시")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    roles: List[RoleSimple] = Field(default_factory=list, description="보유 역할 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "login_id": "admin",
                "email": "admin@system.local",
                "display_name": "시스템 관리자",
                "tenant_id": None,
                "tenant_name": None,
                "is_active": True,
                "is_superuser": True,
                "last_login_at": "2026-02-12T10:00:00+09:00",
                "created_at": "2026-02-06T09:00:00+09:00",
                "updated_at": "2026-02-06T09:00:00+09:00",
                "roles": [
                    {"role_id": 1, "role_code": "SYSTEM_ADMIN", "role_name": "시스템 관리자", "scope_type": "GLOBAL"}
                ]
            }
        }
    }


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    total: int = Field(..., description="전체 사용자 수")
    items: List[UserResponse] = Field(default_factory=list, description="사용자 목록")
    limit: int = Field(..., description="요청된 limit")
    offset: int = Field(..., description="요청된 offset")


# ===================================
# 역할 (Role)
# ===================================

class RoleBase(BaseModel):
    """역할 기본 필드"""
    role_code: str = Field(..., min_length=1, max_length=50, description="역할 코드")
    role_name: str = Field(..., min_length=1, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        valid = ["GLOBAL", "TENANT", "USER"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class RoleCreate(RoleBase):
    """역할 생성 요청"""
    permission_ids: List[int] = Field(default_factory=list, description="부여할 권한 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_code": "DEPT_ADMIN",
                "role_name": "부서 관리자",
                "description": "부서 내 데이터만 접근",
                "scope_type": "TENANT",
                "permission_ids": [1, 3, 4]
            }
        }
    }


class RoleUpdate(BaseModel):
    """역할 수정 요청 (모든 필드 Optional)"""
    role_name: Optional[str] = Field(None, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: Optional[str] = Field(None, description="데이터 범위")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ["GLOBAL", "TENANT", "USER"]
            v = v.upper()
            if v not in valid:
                raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class PermissionSimple(BaseModel):
    """권한 간략 정보 (RoleResponse에 포함용)"""
    permission_id: int = Field(..., description="권한 ID")
    permission_code: str = Field(..., description="권한 코드")
    permission_name: str = Field(..., description="권한명")
    category: str = Field(..., description="카테고리")


class RoleResponse(BaseModel):
    """역할 상세 응답"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위")
    is_system: bool = Field(..., description="시스템 기본 역할 여부")
    sort_order: int = Field(0, description="정렬 순서")
    created_at: datetime = Field(..., description="생성일시")
    permissions: List[PermissionSimple] = Field(default_factory=list, description="보유 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_id": 1,
                "role_code": "SYSTEM_ADMIN",
                "role_name": "시스템 관리자",
                "description": "전체 시스템 관리 권한",
                "scope_type": "GLOBAL",
                "is_system": True,
                "sort_order": 1,
                "created_at": "2026-02-06T09:00:00+09:00",
                "permissions": [
                    {"permission_id": 1, "permission_code": "nl2sql:execute", "permission_name": "NL2SQL 실행", "category": "nl2sql"}
                ]
            }
        }
    }


class RoleListResponse(BaseModel):
    """역할 목록 응답"""
    total: int = Field(..., description="전체 역할 수")
    items: List[RoleResponse] = Field(default_factory=list, description="역할 목록")


# ===================================
# 권한 (Permission)
# ===================================

class PermissionResponse(BaseModel):
    """권한 응답"""
    permission_id: int = Field(..., description="권한 ID")
    permission_code: str = Field(..., description="권한 코드")
    permission_name: str = Field(..., description="권한명")
    category: str = Field(..., description="카테고리")
    description: Optional[str] = Field(None, description="설명")
    is_system: bool = Field(default=False, description="시스템 기본 권한 여부")


# ===================================
# 역할 할당
# ===================================

class UserRoleAssign(BaseModel):
    """사용자에게 역할 할당 요청"""
    role_ids: List[int] = Field(..., min_length=1, description="할당할 역할 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_ids": [2, 3]
            }
        }
    }


class RolePermissionAssign(BaseModel):
    """역할에 권한 할당 요청"""
    permission_ids: List[int] = Field(..., min_length=1, description="할당할 권한 ID 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "permission_ids": [1, 3, 4, 5]
            }
        }
    }


# ===================================
# 데이터 필터
# ===================================

class DataFilterResponse(BaseModel):
    """데이터 필터 응답"""
    filter_id: int = Field(..., description="필터 ID")
    role_id: int = Field(..., description="역할 ID")
    target_table: str = Field(..., description="대상 테이블")
    filter_column: str = Field(..., description="필터 컬럼")
    filter_type: str = Field(..., description="필터 유형 (TENANT, USER, CUSTOM)")
    filter_sql: Optional[str] = Field(None, description="커스텀 SQL 조건")
    is_active: bool = Field(default=True, description="활성화 여부")
```

### 4.4 코드 상세 설명

#### 4.4.1 상속 패턴 — Base/Create/Update/Response

이 파일의 핵심 패턴은 **상속을 통한 필드 재사용**입니다:

```
UserBase (공통 필드: login_id, email, display_name, tenant_id)
  ├── UserCreate (상속 + password, is_active, role_ids 추가)
  └── (UserUpdate는 별도 — 모든 필드 Optional이므로)

UserResponse (별도 정의 — DB 조회 결과에 맞춤)
```

**왜 UserUpdate는 UserBase를 상속하지 않는가?**

```python
# UserBase는 login_id이 필수 (Field(...))
# UserUpdate에서 login_id을 Optional로 바꿀 수 없음
# Pydantic에서 상속 시 필수→Optional 변경이 불가능하므로 별도 클래스로 정의
class UserUpdate(BaseModel):  # UserBase가 아닌 BaseModel 상속
    email: Optional[str] = Field(None, ...)  # 모든 필드 Optional
```

**왜 UserResponse는 UserBase를 상속하지 않는가?**

```python
# UserBase에는 email, login_id이 필수로 정의됨
# UserResponse에는 user_id, is_active, created_at 등 추가 필드가 많고,
# DB에서 읽는 결과이므로 별도 클래스가 더 명확
class UserResponse(BaseModel):
    user_id: int = Field(...)     # DB PK (UserBase에 없음)
    roles: List[RoleSimple] = ... # JOIN 결과 (UserBase에 없음)
```

#### 4.4.2 UserCreate — 사용자 생성 요청

```python
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")
    is_active: bool = Field(default=True, description="활성화 여부")
    role_ids: List[int] = Field(default_factory=list, description="부여할 역할 ID 목록")
```

- `UserBase`를 상속하므로 `login_id`, `email`, `display_name`, `tenant_id` 필드가 자동 포함
- `password`: 생성 시에만 필요 (조회/수정에서는 사용하지 않음)
- `role_ids`: 사용자 생성과 동시에 역할 할당. 빈 리스트면 역할 없이 생성
- **DB 처리 흐름** (Phase 4에서 구현):
  ```
  1. UserCreate 모델 검증 → 422 또는 통과
  2. password → bcrypt 해싱 → tb_user.password_hash에 저장
  3. login_id, email 등 → tb_user INSERT
  4. role_ids → tb_user_role에 각각 INSERT
  ```

#### 4.4.3 UserUpdate — 부분 수정 (Partial Update)

```python
class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, ...)
    display_name: Optional[str] = Field(None, ...)
```

모든 필드가 `Optional`이므로 **보내는 필드만 수정**됩니다:

```json
// 이메일만 수정하고 싶을 때
{ "email": "new@company.com" }

// 활성화만 변경하고 싶을 때
{ "is_active": false }

// 빈 객체 → 아무것도 수정하지 않음
{}
```

서비스 레이어에서 `model.model_dump(exclude_unset=True)`로 실제 전송된 필드만 추출합니다:

```python
# Phase 4에서 구현할 패턴 (미리보기)
data = update_request.model_dump(exclude_unset=True)
# { "email": "new@company.com" }  ← 전송된 필드만 포함
```

#### 4.4.4 RoleSimple vs RoleResponse

```python
class RoleSimple(BaseModel):     # 간략 (UserResponse 내부)
    role_id: int
    role_code: str
    role_name: str
    scope_type: str

class RoleResponse(BaseModel):   # 상세 (역할 관리 API 응답)
    role_id: int
    role_code: str
    role_name: str
    scope_type: str
    is_system: bool
    permissions: List[PermissionSimple]  # 보유 권한 목록
    created_at: datetime
```

같은 `tb_role` 테이블에서 읽지만 용도에 따라 반환 필드가 다릅니다:
- `RoleSimple`: 사용자 상세 조회 시 "이 사용자의 역할" 간략 표시
- `RoleResponse`: 역할 관리 화면에서 상세 정보 + 권한 목록 표시

#### 4.4.5 field_validator — scope_type 검증

```python
@field_validator("scope_type")
@classmethod
def validate_scope_type(cls, v: str) -> str:
    valid = ["GLOBAL", "TENANT", "USER"]
    v = v.upper()                    # 소문자 입력도 허용 ("tenant" → "TENANT")
    if v not in valid:
        raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
    return v                         # 변환된 대문자를 반환
```

- DB의 `tb_role.scope_type`이 `VARCHAR(20)`이고 실제 값은 대문자로 저장됨
- API 호출 시 소문자로 입력해도 자동 변환하여 일관성 유지
- 잘못된 값 입력 시: `422 Unprocessable Entity` + `"scope_type은 ['GLOBAL', 'TENANT', 'USER'] 중 하나여야 합니다"`

#### 4.4.6 UserRoleAssign — 역할 할당

```python
class UserRoleAssign(BaseModel):
    role_ids: List[int] = Field(..., min_length=1, description="할당할 역할 ID 목록")
```

- `min_length=1`: 빈 리스트 방지. 최소 1개 역할 필요
- **DB 처리 흐름** (Phase 4):
  ```
  1. 기존 tb_user_role에서 해당 사용자 역할 삭제
  2. role_ids 각각에 대해 tb_user_role INSERT
  3. tenant_id 정합성 검증 (서비스 레이어)
  ```

#### 4.4.7 DataFilterResponse — NL2SQL 필터 조회

```python
class DataFilterResponse(BaseModel):
    filter_id: int = Field(...)
    target_table: str = Field(...)       # "employee", "tb_user" 등
    filter_column: str = Field(...)      # "tenant_id", "emp_id" 등
    filter_type: str = Field(...)        # "TENANT", "USER", "CUSTOM"
    filter_sql: Optional[str] = Field(None, description="커스텀 SQL 조건")
```

- `tb_data_filter` 테이블의 조회 결과를 반환
- Phase 5에서 NL2SQL이 이 정보를 읽어 SQL WHERE 조건을 자동 주입

---

## 5. Step 4: `app/models/tenant.py`

### 5.1 파일 위치와 목적

```
파일 경로: app/models/tenant.py
목적: 테넌트(고객사) CRUD 작업의 데이터 구조 정의
사용처: Phase 4의 테넌트 관리 API (/api/v1/tenants)에서 사용
```

### 5.2 이 파일이 필요한 이유

| 클래스 | 사용처 | 없으면 어떻게 되는가 |
|--------|--------|---------------------|
| `TenantCreate` | `POST /api/v1/tenants` 요청 바디 | 테넌트 생성 요청을 검증할 수 없음 |
| `TenantUpdate` | `PUT /api/v1/tenants/{id}` 요청 바디 | 테넌트 수정 데이터를 파싱할 수 없음 |
| `TenantResponse` | 테넌트 조회 응답 | 테넌트 정보를 구조화하여 반환할 수 없음 |
| `TenantListResponse` | 테넌트 목록 응답 | 페이징된 목록을 반환할 수 없음 |

### 5.3 전체 소스코드

```python
"""
테넌트(고객사) 관리 스키마

위치: app/models/tenant.py
테넌트 CRUD 관련 모델
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 테넌트 (Tenant)
# ===================================

class TenantBase(BaseModel):
    """테넌트 기본 필드"""
    tenant_code: str = Field(..., min_length=1, max_length=50, description="테넌트 코드")
    tenant_name: str = Field(..., min_length=1, max_length=200, description="테넌트명")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보 (업종, 계약정보 등)")

    @field_validator("tenant_code")
    @classmethod
    def validate_tenant_code(cls, v: str) -> str:
        """테넌트 코드: 영문 대문자 + 숫자 + 언더스코어만 허용"""
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("테넌트 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
        return v


class TenantCreate(TenantBase):
    """테넌트 생성 요청"""
    is_active: bool = Field(default=True, description="활성화 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_code": "COMPANY_A",
                "tenant_name": "A 주식회사",
                "metadata": {"industry": "IT", "contract_type": "enterprise"},
                "is_active": True
            }
        }
    }


class TenantUpdate(BaseModel):
    """테넌트 수정 요청 (모든 필드 Optional)"""
    tenant_name: Optional[str] = Field(None, max_length=200, description="테넌트명")
    is_active: Optional[bool] = Field(None, description="활성화 여부")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_name": "A 주식회사 (수정)",
                "metadata": {"industry": "IT", "contract_type": "premium"}
            }
        }
    }


class TenantResponse(BaseModel):
    """테넌트 상세 응답"""
    tenant_id: int = Field(..., description="테넌트 ID")
    tenant_code: str = Field(..., description="테넌트 코드")
    tenant_name: str = Field(..., description="테넌트명")
    is_active: bool = Field(..., description="활성화 여부")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보")
    user_count: int = Field(default=0, description="소속 사용자 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_id": 1,
                "tenant_code": "SYSTEM",
                "tenant_name": "시스템",
                "is_active": True,
                "metadata": {"type": "internal"},
                "user_count": 1,
                "created_at": "2026-02-06T09:00:00+09:00",
                "updated_at": "2026-02-06T09:00:00+09:00"
            }
        }
    }


class TenantListResponse(BaseModel):
    """테넌트 목록 응답"""
    total: int = Field(..., description="전체 테넌트 수")
    items: List[TenantResponse] = Field(default_factory=list, description="테넌트 목록")
```

### 5.4 코드 상세 설명

#### 5.4.1 TenantBase — tenant_code 검증

```python
@field_validator("tenant_code")
@classmethod
def validate_tenant_code(cls, v: str) -> str:
    v = v.upper().strip()
    if not all(c.isalnum() or c == "_" for c in v):
        raise ValueError("테넌트 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
    return v
```

- `v.upper().strip()`: 소문자 입력 자동 변환, 앞뒤 공백 제거
- `all(... for c in v)`: 모든 문자가 조건을 만족하는지 확인
- `c.isalnum()`: 알파벳 또는 숫자인지 (`A-Z`, `0-9`)
- `c == "_"`: 언더스코어 허용
- **이유**: `tenant_code`는 NL2SQL WHERE 조건에서 사용되므로 (`WHERE tenant_code = 'COMPANY_A'`) 특수문자가 들어가면 SQL injection 위험

#### 5.4.2 TenantResponse — user_count 필드

```python
class TenantResponse(BaseModel):
    user_count: int = Field(default=0, description="소속 사용자 수")
```

- `tb_tenant` 테이블에는 `user_count` 컬럼이 없음
- 서비스 레이어에서 `tb_user`를 COUNT하여 계산한 값을 채워줌
- **DB 쿼리 패턴** (Phase 4에서 구현):
  ```sql
  SELECT t.*, COUNT(u.user_id) as user_count
  FROM tb_tenant t
  LEFT JOIN tb_user u ON t.tenant_id = u.tenant_id
  GROUP BY t.tenant_id
  ```

#### 5.4.3 metadata — JSONB 매핑

```python
metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보 (업종, 계약정보 등)")
```

- `Dict[str, Any]`: 키가 문자열, 값이 임의 타입인 딕셔너리
- DB의 `tb_tenant.metadata JSONB`와 매핑
- JSONB는 PostgreSQL의 바이너리 JSON 타입. 인덱싱과 검색이 가능
- **사용 예시**: 업종, 계약 유형, 연락처 등 구조가 유동적인 정보 저장
  ```json
  {"industry": "IT", "contract_type": "enterprise", "contact_email": "admin@company.com"}
  ```

---

## 6. Step 5: `app/config.py` 수정

### 6.1 수정 목적

기존 `app/config.py`에 JWT 관련 추가 설정 필드를 넣어 Phase 2에서 사용할 수 있게 준비합니다.

### 6.2 기존 필드 (이미 존재)

```python
# Security (현재 config.py에 이미 있음)
secret_key: str = Field(..., description="JWT 시크릿 키")
algorithm: str = Field(default="HS256", description="JWT 알고리즘")
access_token_expire_minutes: int = Field(default=30, description="액세스 토큰 만료 시간(분)")
```

### 6.3 추가할 필드

`app/config.py`의 `Settings` 클래스에 아래 필드를 추가합니다.

**추가 위치**: 기존 `# Security` 섹션의 `access_token_expire_minutes` 아래

```python
    # Security (기존 3개 필드 아래에 추가)
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh Token 만료 시간(일)")
    password_min_length: int = Field(default=8, description="최소 비밀번호 길이")
    login_max_fail_count: int = Field(default=5, description="로그인 실패 허용 횟수")
    login_lock_minutes: int = Field(default=30, description="계정 잠금 시간(분)")
```

### 6.4 각 필드 설명

| 필드 | 타입 | 기본값 | 사용처 (Phase 2~3) |
|------|------|--------|-------------------|
| `jwt_refresh_token_expire_days` | `int` | 7 | `security/jwt.py`에서 Refresh Token 만료 시간 계산 |
| `password_min_length` | `int` | 8 | `security/password.py`에서 비밀번호 길이 검증 |
| `login_max_fail_count` | `int` | 5 | `auth_service.py`에서 로그인 실패 횟수 초과 시 계정 잠금 |
| `login_lock_minutes` | `int` | 30 | `auth_service.py`에서 계정 잠금 해제 시간 계산 |

### 6.5 .env 파일에 추가할 항목

```bash
# JWT Authentication (기존 SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES 아래에 추가)
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
LOGIN_MAX_FAIL_COUNT=5
LOGIN_LOCK_MINUTES=30
```

> **참고**: Pydantic Settings에서 `case_sensitive=False`이므로 환경변수명은 대소문자 무관.
> `jwt_refresh_token_expire_days` ↔ `JWT_REFRESH_TOKEN_EXPIRE_DAYS` 자동 매핑.

---

## 7. 검증 체크리스트

Phase 1 완료 후 아래 항목을 확인합니다.

### 7.1 DB 검증

- [ ] 8개 테이블 모두 생성 확인 (`information_schema.tables`)
- [ ] 3개 역할 정상 INSERT 확인 (`SELECT * FROM tb_role`)
- [ ] 9개 권한 정상 INSERT 확인 (`SELECT * FROM tb_permission`)
- [ ] 역할-권한 매핑 확인 (SYSTEM_ADMIN=9, TENANT_ADMIN=6, USER=3)
- [ ] 관리자 계정 존재 확인 (`SELECT * FROM tb_user WHERE login_id='admin'`)
- [ ] 데이터 필터 4개 확인 (`SELECT * FROM tb_data_filter`)

### 7.2 Pydantic 모델 검증

Python 인터프리터에서 import 테스트:

```python
# Conda 환경 활성화 후 실행
conda activate penv3.13-nlq
python

# 1. auth.py import
from app.models.auth import (
    LoginRequest, TokenResponse, UserInfo, UserContext,
    RefreshRequest, PasswordChangeRequest
)

# 2. user.py import
from app.models.user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleBase, RoleCreate, RoleUpdate, RoleResponse, RoleListResponse,
    PermissionResponse, PermissionSimple, RoleSimple,
    UserRoleAssign, RolePermissionAssign, DataFilterResponse
)

# 3. tenant.py import
from app.models.tenant import (
    TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
)

# 4. 인스턴스 생성 테스트
login = LoginRequest(login_id="admin", password="admin123!")
print(login.model_dump())
# {'login_id': 'admin', 'password': 'admin123!'}

user_ctx = UserContext(
    user_id=1, login_id="admin", scope_type="GLOBAL",
    is_superuser=True, permissions=["admin:settings", "nl2sql:execute"]
)
print(user_ctx.has_permission("admin:settings"))  # True
print(user_ctx.is_global)                          # True

# 5. 검증 테스트
try:
    LoginRequest(login_id="", password="test")  # min_length=1 위반
except Exception as e:
    print(f"예상된 검증 오류: {e}")

try:
    PasswordChangeRequest(current_password="old", new_password="short")  # 8자 미만
except Exception as e:
    print(f"예상된 검증 오류: {e}")

# 6. config.py 확인
from app.config import settings
print(f"Refresh Token 만료: {settings.jwt_refresh_token_expire_days}일")
print(f"비밀번호 최소 길이: {settings.password_min_length}")
print(f"로그인 실패 허용: {settings.login_max_fail_count}회")
print(f"계정 잠금 시간: {settings.login_lock_minutes}분")
```

### 7.3 최종 확인

- [ ] `app/models/__init__.py`는 빈 파일 유지 (CLAUDE.md 규칙)
- [ ] 기존 API 정상 동작 (새 파일 추가만 했으므로 기존 기능 영향 없음)
- [ ] `.env` 파일에 새 환경변수 추가됨

---

## 8. 다음 단계

Phase 1 완료 후 **Phase 2: Core Security 모듈**을 진행합니다.

Phase 2에서 생성할 파일:
```
app/core/security/
├── __init__.py              # 빈 파일
├── jwt.py                   # JWT 토큰 생성/검증 (python-jose 사용)
├── password.py              # bcrypt 해싱/검증 (passlib 사용)
├── dependencies.py          # FastAPI Depends (get_current_user)
└── permission.py            # 권한 검사 데코레이터 (require_permission)
```

Phase 2는 Phase 1의 Pydantic 모델(`UserContext`, `TokenResponse` 등)을 import하여 사용합니다:
```python
# Phase 2의 jwt.py에서 Phase 1 모델 사용
from app.models.auth import UserContext, TokenResponse
```

---

## 부록 A: DB 테이블 ↔ Pydantic 모델 매핑

| DB 테이블 | Create 모델 | Response 모델 | 비고 |
|-----------|------------|--------------|------|
| `tb_tenant` | `TenantCreate` | `TenantResponse` | `user_count`는 JOIN으로 계산 |
| `tb_user` | `UserCreate` | `UserResponse` | `password` → `password_hash` (bcrypt) |
| `tb_role` | `RoleCreate` | `RoleResponse` | `permissions` 포함 |
| `tb_permission` | — | `PermissionResponse` | 읽기 전용 (시스템 기본 데이터) |
| `tb_role_permission` | `RolePermissionAssign` | `RoleResponse.permissions` | 매핑 테이블 |
| `tb_user_role` | `UserRoleAssign` | `UserResponse.roles` | 매핑 테이블 |
| `tb_data_filter` | — | `DataFilterResponse` | Phase 5에서 사용 |
| `tb_user_session` | — | — | 내부 전용 (API 노출 안 함) |

## 부록 B: Pydantic v2 문법 참조

### Field 사용법

```python
# 필수 필드 (값을 보내지 않으면 422 에러)
name: str = Field(..., description="이름")

# 선택 필드 (보내지 않으면 None)
nickname: Optional[str] = Field(None, description="별명")

# 기본값이 있는 필드
is_active: bool = Field(default=True, description="활성화")

# 리스트 기본값 (default_factory 사용)
items: List[str] = Field(default_factory=list, description="항목 목록")
# ⚠️ default=[] 사용 금지 — mutable default 공유 버그 발생

# 검증 포함
age: int = Field(..., ge=0, le=200, description="나이")
# ge=0: greater than or equal (0 이상)
# le=200: less than or equal (200 이하)

# 문자열 길이 제한
code: str = Field(..., min_length=1, max_length=50, description="코드")
```

### field_validator

```python
from pydantic import field_validator

class MyModel(BaseModel):
    status: str

    @field_validator("status")        # 대상 필드명
    @classmethod                       # 반드시 클래스메서드
    def validate_status(cls, v: str) -> str:  # cls는 클래스, v는 값
        if v not in ["active", "inactive"]:
            raise ValueError("status는 active 또는 inactive여야 합니다")
        return v                       # 반드시 값 반환 (변환 가능)
```

### model_config

```python
class MyModel(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {                # FastAPI /docs에서 표시되는 예시
                "field1": "value1",
                "field2": 42
            }
        }
    }
```

### model_dump (직렬화)

```python
model = UserUpdate(email="new@test.com")

# 모든 필드 포함 (None 포함)
model.model_dump()
# {'email': 'new@test.com', 'display_name': None, 'tenant_id': None, 'is_active': None}

# 전송된 필드만 추출 (Partial Update에 필수)
model.model_dump(exclude_unset=True)
# {'email': 'new@test.com'}
```

### @property

```python
class UserContext(BaseModel):
    scope_type: str
    is_superuser: bool

    @property                           # 메서드를 속성처럼 사용
    def is_global(self) -> bool:
        return self.is_superuser or self.scope_type == "GLOBAL"

# 사용
user = UserContext(scope_type="GLOBAL", is_superuser=False, ...)
print(user.is_global)   # True  ← 괄호 없이 호출
```
