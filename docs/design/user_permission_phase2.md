# Phase 2 구현 가이드: Core Security 모듈 (JWT + 비밀번호 + 의존성)

> **문서 버전**: 1.0
> **작성일**: 2026-02-12
> **상위 문서**: `docs/design/user_permission_system.md`
> **선행 조건**: Phase 1 완료 (DB 테이블 DDL + Pydantic 모델)
> **목적**: Phase 2(Core Security 모듈)의 실제 구현 절차를 코드 레벨에서 상세 설명

---

## 목차

1. [Phase 2 개요](#1-phase-2-개요)
2. [Step 1: `app/core/security/password.py` — 비밀번호 해싱](#2-step-1-password)
3. [Step 2: `app/core/security/jwt.py` — JWT 토큰 관리](#3-step-2-jwt)
4. [Step 3: `app/core/security/dependencies.py` — FastAPI 의존성 주입](#4-step-3-dependencies)
5. [Step 4: `app/core/security/permission.py` — 권한 검사](#5-step-4-permission)
6. [검증 체크리스트](#6-검증-체크리스트)
7. [다음 단계 (Phase 3 Preview)](#7-다음-단계)

---

## 1. Phase 2 개요

### 1.1 무엇을 하는가

Phase 2는 인증/인가의 **핵심 유틸리티**를 구현하는 단계입니다.

```
Phase 2 산출물:
  [NEW] app/core/security/__init__.py       ← 빈 파일
  [NEW] app/core/security/password.py       ← bcrypt 해싱/검증
  [NEW] app/core/security/jwt.py            ← JWT 토큰 생성/검증
  [NEW] app/core/security/dependencies.py   ← FastAPI Depends (get_current_user)
  [NEW] app/core/security/permission.py     ← 권한 검사 의존성 팩토리
```

### 1.2 왜 필요한가

| 모듈 | 없으면 어떻게 되는가 |
|------|---------------------|
| `password.py` | 비밀번호를 평문으로 저장하거나 매번 해싱 코드를 중복 작성해야 함 |
| `jwt.py` | 로그인 성공 후 상태를 유지할 수 없음 (세션 쿠키 방식은 SPA에 부적합) |
| `dependencies.py` | 모든 API 핸들러에서 직접 토큰을 파싱해야 함 → 코드 중복 |
| `permission.py` | 권한 검사를 각 핸들러마다 if문으로 작성해야 함 → 누락 위험 |

### 1.3 핵심 설계 결정

```
┌─────────────────────────────────────────────────────────────────────┐
│  get_current_user = JWT 페이로드만으로 UserContext 생성              │
│                                                                     │
│  JWT payload에 roles, permissions, scope_type이 포함되어 있으므로   │
│  매 요청마다 DB를 조회할 필요 없음                                   │
│                                                                     │
│  장점: 성능 (DB round-trip 없음), 무상태(stateless)                 │
│  단점: 권한 변경 시 최대 30분 지연 (Access Token 만료까지)           │
│        → Refresh 시점에 DB에서 최신 권한을 다시 로드                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 파일 간 의존 관계

```
password.py         (standalone — passlib만 사용)
                     ↑ 없음
jwt.py              → app.config (settings)
                    → app.core.errors (APIException, ErrorCode)
                     ↑
dependencies.py     → jwt.py (verify_token)
                    → app.models.auth (UserContext)
                    → app.core.errors (APIException, ErrorCode)
                     ↑
permission.py       → dependencies.py (get_current_active_user)
                    → app.models.auth (UserContext)
                    → app.core.errors (APIException, ErrorCode)

※ 순환 import 없음
```

### 1.5 Phase 1에서 사용하는 항목

| Phase 1 산출물 | Phase 2에서 사용하는 곳 |
|---------------|----------------------|
| `UserContext` (app/models/auth.py) | dependencies.py, permission.py |
| `settings.secret_key` (app/config.py) | jwt.py |
| `settings.algorithm` | jwt.py |
| `settings.access_token_expire_minutes` | jwt.py |
| `settings.jwt_refresh_token_expire_days` | jwt.py |
| `ErrorCode.UNAUTHORIZED` (app/core/errors/) | jwt.py, dependencies.py |
| `ErrorCode.FORBIDDEN` | permission.py |

---

## 2. Step 1: `app/core/security/password.py`

### 2.1 이 파일의 역할

```
목적: 비밀번호의 안전한 해싱(저장)과 검증(로그인)
사용처:
  - Phase 3의 auth_service.py: 로그인 시 verify_password()
  - Phase 4의 user_service.py: 사용자 생성 시 hash_password()
의존성: bcrypt (requirements.txt에 이미 존재)
비고: passlib은 bcrypt 5.x와 호환 문제가 있어 bcrypt를 직접 사용
```

### 2.2 전체 소스코드

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

### 2.3 코드 상세 설명

#### 2.3.1 bcrypt 직접 사용

```python
import bcrypt
```

- **passlib 대신 bcrypt 직접 사용**: passlib은 bcrypt 5.x와 호환성 문제가 있음 (`AttributeError: module 'bcrypt' has no attribute '__about__'`)
- bcrypt 라이브러리를 직접 사용하면 버전 호환 문제 없이 안정적으로 동작
- `bcrypt.gensalt(rounds=12)`: cost factor 12 (2^12 = 4096 라운드)
- `bcrypt.hashpw()`: salt + password → hash
- `bcrypt.checkpw()`: password + hash → True/False

#### 2.3.2 hash_password

```python
def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")
```

- `encode("utf-8")` / `decode("utf-8")`: bcrypt는 bytes로 동작하므로 str ↔ bytes 변환 필요
- `bcrypt.gensalt(rounds=12)`: 랜덤 salt 생성. rounds=12는 보안과 성능의 균형점
- `bcrypt.hashpw()`: 내부적으로 salt를 포함하여 해시 수행
- 반환값: `$2b$12$...` 형태의 60자 문자열
  - `$2b$`: bcrypt 알고리즘 식별자
  - `12$`: cost factor (2^12 = 4096 라운드)
  - 나머지: salt(22자) + hash(31자)
- **같은 비밀번호라도 매번 다른 해시 생성** (salt가 다르므로)

#### 2.3.3 verify_password

```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- `pwd_context.verify()`: 해시에서 salt를 추출하여 평문을 동일하게 해싱 후 비교
- 반환: `True` (일치) 또는 `False` (불일치)
- **예외를 발생시키지 않음** — 호출자(auth_service)가 False일 때 적절한 에러 반환 결정

#### 2.3.4 DB 매핑

```
사용자 생성 (Phase 4):
  password (UserCreate) → hash_password() → tb_user.password_hash

로그인 (Phase 3):
  password (LoginRequest) + tb_user.password_hash → verify_password() → True/False
```

---

## 3. Step 2: `app/core/security/jwt.py`

### 3.1 이 파일의 역할

```
목적: JWT 토큰의 생성(인코딩)과 검증(디코딩)
사용처:
  - Phase 3의 auth_service.py: 로그인 성공 시 create_access_token(), create_refresh_token()
  - Phase 2의 dependencies.py: 매 요청마다 verify_token()
의존성: python-jose[cryptography] (requirements.txt에 이미 존재)
```

### 3.2 이 파일이 필요한 이유

| 함수/클래스 | 사용처 | 없으면 어떻게 되는가 |
|-------------|--------|---------------------|
| `TokenPayload` | `verify_token()` 반환값 | JWT 디코딩 결과를 dict로 다뤄야 하며 타입 안전성 없음 |
| `create_access_token()` | Phase 3 auth_service | 토큰 생성 로직을 서비스마다 중복 작성 |
| `create_refresh_token()` | Phase 3 auth_service | Refresh Token의 minimal payload 규칙 관리 불가 |
| `verify_token()` | dependencies.py | 토큰 검증 + 에러 처리를 매번 작성 |

### 3.3 전체 소스코드

```python
"""
JWT 토큰 생성 및 검증 유틸리티

위치: app/core/security/jwt.py
python-jose를 사용한 Access/Refresh Token 관리
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings
from app.core.errors import APIException, ErrorCode


# ===================================
# JWT 페이로드 모델 (내부 전용)
# ===================================

class TokenPayload(BaseModel):
    """JWT 토큰 디코딩 결과"""
    sub: str = Field(..., description="Subject (user_id 문자열)")
    login_id: str = Field(default="", description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="테넌트 ID")
    scope_type: str = Field(default="USER", description="데이터 범위")
    roles: List[str] = Field(default_factory=list, description="역할 코드 목록")
    permissions: List[str] = Field(default_factory=list, description="권한 코드 목록")
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

### 3.4 코드 상세 설명

#### 3.4.1 TokenPayload — JWT 내부 모델

```python
class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject (user_id 문자열)")
    token_type: str = Field(default="access", description="토큰 타입 (access, refresh)")
    session_id: Optional[str] = Field(None, description="세션 ID (refresh token only)")
```

- **JWT 표준**: `sub` (subject), `exp` (expiration), `iat` (issued at)은 RFC 7519 표준 클레임
- **`sub`가 문자열인 이유**: JWT 표준은 `sub`을 문자열로 정의. `user_id`(int)를 `str(user_id)`로 변환하여 저장
- **`token_type`**: Access Token과 Refresh Token을 구분. Refresh Token을 Access Token 대신 사용하는 공격 방지
- **`session_id`**: Refresh Token에만 포함. `tb_user_session.session_id`와 매핑하여 개별 세션 관리
- **app/models/auth.py의 UserInfo와 차이**: `TokenPayload`는 JWT 내부 표현(sub 문자열, exp/iat 포함), `UserInfo`는 API 응답용(user_id 정수, 만료 정보 없음)

#### 3.4.2 create_access_token — Access Token 생성

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "iat": now, "token_type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

- **`data.copy()`**: 원본 dict 변경 방지 (exp, iat 추가 시 원본이 오염되면 안 됨)
- **`datetime.now(timezone.utc)`**: JWT 타임스탬프는 항상 UTC. DB는 Asia/Seoul이지만 토큰은 UTC 기준
- **`settings.access_token_expire_minutes`**: .env의 `ACCESS_TOKEN_EXPIRE_MINUTES=30`에서 로드
- **`jwt.encode()`**: python-jose 함수. payload dict → JWT 문자열 (Header.Payload.Signature)
- **`settings.secret_key`**: .env의 `SECRET_KEY`. 이 키가 유출되면 모든 토큰을 위조할 수 있으므로 프로덕션에서 강력한 랜덤값 사용 필수

**Phase 3에서의 호출 예시**:
```python
# auth_service.py (Phase 3에서 구현)
access_token = create_access_token({
    "sub": str(user.user_id),
    "login_id": user.login_id,
    "display_name": user.display_name,
    "tenant_id": user.tenant_id,
    "scope_type": role.scope_type,  # DB에서 조회한 최고 권한 역할의 scope_type
    "roles": ["SYSTEM_ADMIN"],       # DB에서 조회한 역할 코드 목록
    "permissions": ["nl2sql:execute", "admin:settings"],  # DB에서 조회
    "is_superuser": user.is_superuser,
})
```

#### 3.4.3 create_refresh_token — Refresh Token 생성

```python
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))
    to_encode.update({"exp": expire, "iat": now, "token_type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

- **Minimal payload**: Refresh Token에는 `sub`(user_id)와 `session_id`만 포함
- **roles/permissions 미포함**: Refresh로 새 Access Token 발급 시 DB에서 **최신 권한을 다시 조회**하므로, Refresh Token에 권한 정보를 넣을 필요 없음
- **`token_type: "refresh"`**: Access Token으로 사용하는 것을 방지

**Phase 3에서의 호출 예시**:
```python
# auth_service.py (Phase 3에서 구현)
session_id = str(uuid.uuid4())
refresh_token = create_refresh_token({
    "sub": str(user.user_id),
    "session_id": session_id,
})
# tb_user_session에 session_id, refresh_token, expires_at 저장
```

#### 3.4.4 verify_token — 토큰 검증

```python
def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str = payload.get("sub")
        if sub is None:
            raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
        return TokenPayload(**payload)
    except JWTError:
        raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
```

- **`jwt.decode()`**: 서명 검증 + 만료 시간 검증을 자동 수행
  - 서명 불일치 → `JWTError` 발생
  - `exp` 만료 → `ExpiredSignatureError` (JWTError의 하위 클래스) 발생
- **`algorithms=[settings.algorithm]`**: 리스트로 전달 (보안: algorithm confusion attack 방지)
- **`sub` 검증**: JWT 표준에서 sub는 필수는 아니지만, 이 시스템에서는 user_id를 담으므로 필수로 검증
- **`TokenPayload(**payload)`**: dict를 Pydantic 모델로 변환. 누락된 필드는 기본값 사용
- **에러 메시지 통일**: 만료, 변조, 형식 오류 모두 같은 메시지 반환 (보안: 공격자에게 구체적 원인을 알려주지 않음)

#### 3.4.5 python-jose vs PyJWT

```python
# python-jose (이 프로젝트에서 사용)
from jose import jwt, JWTError
jwt.encode(payload, key, algorithm="HS256")
jwt.decode(token, key, algorithms=["HS256"])

# PyJWT (다른 라이브러리 — 사용하지 않음)
import jwt
jwt.encode(payload, key, algorithm="HS256")
jwt.decode(token, key, algorithms=["HS256"])
```

- 두 라이브러리의 API가 거의 동일하지만, **import 경로가 다름**: `from jose import jwt` vs `import jwt`
- requirements.txt에 `python-jose[cryptography]`가 명시되어 있으므로 jose 사용

---

## 4. Step 3: `app/core/security/dependencies.py`

### 4.1 이 파일의 역할

```
목적: HTTP 요청에서 JWT를 추출하여 UserContext로 변환하는 FastAPI 의존성
사용처:
  - Phase 4의 라우트 핸들러: Depends(get_current_user)
  - Phase 3의 인증 미들웨어: get_optional_user()로 선택적 인증
특징: 프로젝트 최초의 FastAPI Depends 사용
```

### 4.2 이 파일이 필요한 이유

| 함수 | 사용처 | 없으면 어떻게 되는가 |
|------|--------|---------------------|
| `get_current_user` | Phase 4 API 핸들러 | 모든 핸들러에서 직접 Authorization 헤더 파싱 필요 |
| `get_current_active_user` | permission.py | 비활성 사용자 체크를 각 핸들러에서 개별 구현 |
| `get_optional_user` | Phase 3 인증 미들웨어 (선택적 모드) | 기존 API가 인증 도입 시 즉시 깨짐 |

### 4.3 전체 소스코드

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
        scope_type=payload.scope_type,
        roles=payload.roles,
        permissions=payload.permissions,
    )


async def get_current_active_user(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    """활성 사용자 검증 (Phase 3에서 확장 예정)"""
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
            scope_type=payload.scope_type,
            roles=payload.roles,
            permissions=payload.permissions,
        )
    except Exception:
        return None
```

### 4.4 코드 상세 설명

#### 4.4.1 HTTPBearer — FastAPI 보안 스키마

```python
_bearer_scheme = HTTPBearer(auto_error=True)
_bearer_scheme_optional = HTTPBearer(auto_error=False)
```

- **`HTTPBearer`**: FastAPI의 내장 보안 스키마. `Authorization: Bearer <token>` 헤더에서 토큰을 자동 추출
- **`auto_error=True`**: 토큰이 없으면 FastAPI가 자동으로 403 반환. 우리 코드까지 도달하지 않음
- **`auto_error=False`**: 토큰이 없어도 `None`을 반환하고 우리 코드에서 처리 가능 (선택적 인증)
- **OpenAPI 문서**: `HTTPBearer`를 사용하면 Swagger UI에 "Authorize" 버튼이 자동 생성되어 토큰 입력 가능

**왜 `OAuth2PasswordBearer`를 쓰지 않는가?**:
```python
# OAuth2PasswordBearer — 사용하지 않음
# 이유: OAuth2 password flow에 특화, /token 엔드포인트를 OpenAPI에 노출
# HTTPBearer가 순수 JWT Bearer 인증에 더 적합
```

#### 4.4.2 get_current_user — 핵심 인증 함수

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> UserContext:
```

- **`async def`**: FastAPI의 Depends 체인에서 비동기 함수를 지원하기 위해 async로 선언. 현재 DB 접근이 없어 실제로 await하는 것은 없지만, Phase 3 확장 시 async DB 조회 가능
- **`Depends(_bearer_scheme)`**: FastAPI가 요청의 Authorization 헤더에서 Bearer 토큰을 자동 추출하여 `credentials` 파라미터에 주입
- **`credentials.credentials`**: `HTTPAuthorizationCredentials` 객체의 `.credentials` 속성이 실제 토큰 문자열

```python
    payload = verify_token(credentials.credentials)

    if payload.token_type != "access":
        raise APIException(ErrorCode.UNAUTHORIZED, "Access Token이 필요합니다")
```

- **token_type 검증**: Refresh Token이 Access Token 대신 사용되는 것을 방지
- **보안 원칙**: Access Token은 짧은 수명(30분) + 풍부한 payload, Refresh Token은 긴 수명(7일) + 최소 payload

```python
    return UserContext(
        user_id=int(payload.sub),    # 문자열 → 정수 변환
        login_id=payload.login_id,
        ...
    )
```

- **`int(payload.sub)`**: JWT의 sub는 문자열(RFC 표준), UserContext의 user_id는 정수
- **DB 조회 없음**: JWT payload의 모든 필드를 직접 UserContext에 매핑

#### 4.4.3 get_current_active_user — 활성 사용자 검증

```python
async def get_current_active_user(
    current_user: UserContext = Depends(get_current_user),
) -> UserContext:
    return current_user
```

- **Depends 체인**: `get_current_active_user`는 `get_current_user`에 의존
  ```
  HTTP 요청 → HTTPBearer(토큰 추출) → get_current_user(검증) → get_current_active_user(활성 확인)
  ```
- **Phase 2에서는 pass-through**: 현재는 추가 검증 없이 바로 반환
- **Phase 3에서 확장**: 비활성 계정, 잠금 계정 등의 추가 검증을 여기에 구현 예정

#### 4.4.4 get_optional_user — 선택적 인증

```python
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme_optional),
) -> Optional[UserContext]:
    if credentials is None:
        return None       # 토큰 없음 → anonymous
    try:
        ...
        return UserContext(...)
    except Exception:
        return None       # 토큰 유효하지 않음 → anonymous
```

- **왜 필요한가**: Phase 3에서 인증 미들웨어를 "선택적 모드"로 도입할 때 사용
  ```
  Phase 3a (선택적 모드): 토큰 있으면 검증, 없으면 anonymous → 기존 클라이언트 영향 없음
  Phase 3b (필수 모드):   토큰 없으면 401 → 프론트엔드 인증 완료 후 전환
  ```
- **try-except**: 유효하지 않은 토큰이라도 예외를 던지지 않고 None 반환 (graceful degradation)

#### 4.4.5 FastAPI Depends 패턴 설명

```python
# Phase 4에서의 사용 예시 (라우트 핸들러):

from app.core.security.dependencies import get_current_user

@router.get("/me")
async def get_my_info(
    current_user: UserContext = Depends(get_current_user)
):
    # current_user가 자동으로 주입됨
    # Authorization: Bearer <token> 헤더가 없으면 401 자동 반환
    return success_response(current_user.model_dump())
```

**Depends 실행 흐름**:
```
1. 클라이언트가 요청: GET /api/v1/auth/me (Authorization: Bearer eyJ...)
2. FastAPI가 _bearer_scheme 실행 → credentials 추출
3. FastAPI가 get_current_user(credentials) 호출 → UserContext 반환
4. FastAPI가 get_my_info(current_user=UserContext) 호출
5. 핸들러 로직 실행
```

---

## 5. Step 4: `app/core/security/permission.py`

### 5.1 이 파일의 역할

```
목적: 권한 검사를 Depends로 제공하는 의존성 팩토리
사용처: Phase 4의 관리 API에서 엔드포인트별 권한 제어
패턴: "의존성 팩토리" — 함수가 callable을 반환하고, 반환된 callable이 Depends에서 사용됨
```

### 5.2 전체 소스코드

```python
"""
권한 검사 의존성 팩토리

위치: app/core/security/permission.py
FastAPI Depends로 사용하는 권한 검사 함수 생성기
"""
from fastapi import Depends

from app.core.errors import APIException, ErrorCode
from app.core.security.dependencies import get_current_active_user
from app.models.auth import UserContext


def require_permission(*required_permissions: str):
    """권한 검사 의존성 (AND 조건 — 모든 권한 필요)"""

    async def permission_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not current_user.has_all_permissions(*required_permissions):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"필요 권한: {', '.join(required_permissions)}")
        return current_user

    return permission_checker


def require_any_permission(*required_permissions: str):
    """권한 검사 의존성 (OR 조건 — 하나라도 있으면 통과)"""

    async def permission_checker(
        current_user: UserContext = Depends(get_current_active_user),
    ) -> UserContext:
        if not current_user.has_any_permission(*required_permissions):
            raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail=f"필요 권한 중 하나: {', '.join(required_permissions)}")
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

### 5.3 코드 상세 설명

#### 5.3.1 의존성 팩토리 패턴

```python
def require_permission(*required_permissions: str):      # 팩토리 함수
    async def permission_checker(...) -> UserContext:      # 내부 함수 (실제 검사)
        ...
    return permission_checker                              # callable 반환
```

**왜 이 패턴이 필요한가?**:

```python
# 문제: Depends에 인자를 전달할 수 없음
@router.get("/users")
async def list_users(
    user: UserContext = Depends(check_permission("admin:users"))  # ← 인자 전달 필요
):
    ...

# 해결: 팩토리 함수가 인자를 받고, Depends 가능한 callable을 반환
require_permission("admin:users")
# → permission_checker 함수 반환
# → Depends(permission_checker) 로 사용 가능
```

**실행 흐름**:
```
1. Python이 라우터 데코레이터 처리 시:
   require_permission("admin:users") 호출 → permission_checker 함수 반환

2. HTTP 요청 수신 시:
   Depends(permission_checker) → get_current_active_user() → get_current_user() → HTTPBearer
   → UserContext 생성 → 권한 검사 → 통과 또는 403

3. 핸들러 실행:
   current_user 파라미터에 검증된 UserContext 주입
```

#### 5.3.2 UserContext 메서드 활용

```python
if not current_user.has_all_permissions(*required_permissions):
    raise APIException(ErrorCode.FORBIDDEN, ...)
```

- **`has_all_permissions()`**: Phase 1에서 구현한 UserContext 메서드. `is_superuser=True`이면 항상 True 반환
- **`has_any_permission()`**: OR 조건. 하나라도 있으면 True
- **superuser bypass**: `has_permission()`, `has_any_permission()`, `has_all_permissions()` 모두 내부에서 `if self.is_superuser: return True` 처리

#### 5.3.3 Phase 4에서의 사용 예시

```python
# app/api/routes/users.py (Phase 4에서 구현)

from app.core.security.permission import require_permission, require_superuser

@router.get("/")
async def list_users(
    current_user: UserContext = Depends(require_permission("admin:users")),
):
    """사용자 목록 조회 — admin:users 권한 필요"""
    # SYSTEM_ADMIN: 전체 사용자
    # TENANT_ADMIN: 자기 테넌트 사용자 (scope_type으로 서비스에서 제한)
    ...

@router.put("/{user_id}/roles")
async def assign_roles(
    user_id: int,
    current_user: UserContext = Depends(require_superuser()),
):
    """역할 할당 — 시스템 관리자만 가능"""
    ...

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: UserContext = Depends(require_any_permission("admin:users", "admin:settings")),
):
    """사용자 상세 — admin:users 또는 admin:settings 중 하나만 있으면 접근 가능"""
    ...
```

---

## 6. 검증 체크리스트

### 6.1 파일 존재 확인

- [ ] `app/core/security/__init__.py` 존재 (빈 파일)
- [ ] `app/core/security/password.py` 존재
- [ ] `app/core/security/jwt.py` 존재
- [ ] `app/core/security/dependencies.py` 존재
- [ ] `app/core/security/permission.py` 존재

### 6.2 Python import 테스트

```python
# Conda 환경 활성화 후 실행
conda activate penv3.13-nlq

# 1. password.py import
from app.core.security.password import hash_password, verify_password
hashed = hash_password("admin123!")
print(f"Hash: {hashed}")
print(f"Verify correct: {verify_password('admin123!', hashed)}")  # True
print(f"Verify wrong: {verify_password('wrong', hashed)}")        # False

# 2. jwt.py import
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token, TokenPayload
token = create_access_token({
    "sub": "1",
    "login_id": "admin",
    "tenant_id": None,
    "scope_type": "GLOBAL",
    "roles": ["SYSTEM_ADMIN"],
    "permissions": ["admin:settings", "nl2sql:execute"],
    "is_superuser": True,
})
print(f"Token: {token[:50]}...")
payload = verify_token(token)
print(f"sub={payload.sub}, type={payload.token_type}, permissions={payload.permissions}")

# 3. dependencies.py import
from app.core.security.dependencies import get_current_user, get_current_active_user, get_optional_user
print("dependencies.py import OK")

# 4. permission.py import
from app.core.security.permission import require_permission, require_any_permission, require_superuser
checker = require_permission("admin:users")
print(f"require_permission returns: {type(checker).__name__}")  # function

# 5. 통합 테스트: JWT → UserContext
from app.models.auth import UserContext
user_ctx = UserContext(
    user_id=int(payload.sub),
    login_id=payload.login_id,
    scope_type=payload.scope_type,
    is_superuser=payload.is_superuser,
    roles=payload.roles,
    permissions=payload.permissions,
)
print(f"has admin:settings: {user_ctx.has_permission('admin:settings')}")  # True
print(f"is_global: {user_ctx.is_global}")  # True
```

### 6.3 검증 항목 요약

| 항목 | 검증 방법 | 기대 결과 |
|------|----------|----------|
| password 해싱 | `hash_password("test")` | `$2b$12$...` 형태 문자열 |
| password 검증 | `verify_password("test", hashed)` | True |
| 틀린 password | `verify_password("wrong", hashed)` | False |
| salt 동작 | 같은 입력 2회 해싱 | 서로 다른 해시 |
| access token 생성 | `create_access_token({...})` | JWT 문자열 |
| token 검증 | `verify_token(token)` | TokenPayload 객체 |
| 만료 토큰 | 만료된 토큰으로 verify_token | APIException(UNAUTHORIZED) |
| 변조 토큰 | 변경된 토큰으로 verify_token | APIException(UNAUTHORIZED) |
| token_type 구분 | access vs refresh | 각각 다른 token_type 포함 |
| dependencies import | 3개 함수 import | 오류 없음 |
| permission import | 3개 팩토리 import | 오류 없음 |
| 팩토리 반환 타입 | `require_permission(...)` | callable(function) |

---

## 7. 다음 단계 (Phase 3 Preview)

Phase 2 완료 후 **Phase 3: 인증 API + 인증 미들웨어**를 진행합니다.

Phase 3에서 생성할 파일:
```
app/api/services/auth_service.py   ← 인증 비즈니스 로직 (DB 접근)
app/api/routes/auth.py             ← 인증 API 엔드포인트 (5개)
app/middleware/auth.py             ← 인증 미들웨어 (선택적 모드)
[MOD] app/main.py                  ← 미들웨어 + 라우터 등록
```

Phase 3는 Phase 2의 모듈을 import하여 사용합니다:
```python
# Phase 3의 auth_service.py에서 Phase 2 모듈 사용
from app.core.security.password import hash_password, verify_password
from app.core.security.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security.dependencies import get_current_user, get_optional_user
```

---

## 부록 A: 기존 프로젝트 패턴과의 일관성

### A.1 __init__.py 정책

| 모듈 | 형태 | 이유 |
|------|------|------|
| `app/core/security/__init__.py` | **빈 파일** | CLAUDE.md 규칙 준수 |
| `app/core/errors/__init__.py` | import 있음 | 예외 (에러 처리는 프로젝트 전반에서 빈번하게 import) |

### A.2 에러 처리 패턴

```python
# 기존 프로젝트 패턴 (app/core/errors/handlers.py):
raise APIException(ErrorCode.UNAUTHORIZED, "인증이 필요합니다")
raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다")

# Phase 2에서 동일 패턴 사용:
raise APIException(ErrorCode.UNAUTHORIZED, "유효하지 않은 토큰입니다")
raise APIException(ErrorCode.FORBIDDEN, "접근 권한이 없습니다", detail="필요 권한: admin:users")
```

### A.3 Settings 접근 패턴

```python
# 기존 패턴:
from app.config import settings
value = settings.database_url

# Phase 2 동일 패턴:
from app.config import settings
key = settings.secret_key
algo = settings.algorithm
```

## 부록 B: JWT 토큰 구조 참고

### Access Token 페이로드 예시

```json
{
  "sub": "1",
  "login_id": "admin",
  "display_name": "시스템 관리자",
  "tenant_id": null,
  "scope_type": "GLOBAL",
  "roles": ["SYSTEM_ADMIN"],
  "permissions": ["nl2sql:execute", "nl2sql:view_all", "rag:search", "document:read", "document:write", "document:delete", "admin:settings", "admin:users", "admin:tenants"],
  "is_superuser": true,
  "exp": 1739350800,
  "iat": 1739349000,
  "token_type": "access"
}
```

### Refresh Token 페이로드 예시

```json
{
  "sub": "1",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "exp": 1739953800,
  "iat": 1739349000,
  "token_type": "refresh"
}
```
